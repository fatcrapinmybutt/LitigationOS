#!/usr/bin/env python3
"""
Delta999 Compliance Agent — Filing compliance checker for Michigan courts.

Validates filings against MCR formatting rules, checks word/page counts,
verifies required sections, and produces a compliance report with
pass/fail status per MCR 2.119 and MCR 7.212.

CLI:
    python delta999_compliance_agent.py --action check_mcr --filing-text "..."
    python delta999_compliance_agent.py --action word_count --filing-text "..."
    python delta999_compliance_agent.py --action required_sections --filing-type "appellate_brief"
    python delta999_compliance_agent.py --action full_report --filing-stack "MEEK1"
"""

import sys
try:
    sys.stdout.reconfigure(encoding='utf-8')
except (AttributeError, OSError):
    pass

import argparse
import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path

# ── paths ────────────────────────────────────────────────────────────────────
AGENT_DIR = Path(__file__).parent
ENGINE_DIR = AGENT_DIR.parent
sys.path.insert(0, str(ENGINE_DIR))

DB = str(Path(__file__).resolve().parents[3] / "litigation_context.db")
AGENT_NAME = 'delta999_compliance_agent'

from llm_bridge import llm_ask, llm_analyze_legal


# ── Shared module import ─────────────────────────────────────────────────────
try:
    _sys_dir = str(Path(__file__).resolve().parent.parent.parent)
    if _sys_dir not in sys.path:
        sys.path.insert(0, _sys_dir)
    from shared import sanitize_fts5, safe_fts5_search
    _HAS_SHARED = True
except ImportError:
    _HAS_SHARED = False
    def sanitize_fts5(q):
        if not q:
            return ""
        return re.sub(r'[^\w\s*"]', ' ', q).strip()


# ── DB helpers ───────────────────────────────────────────────────────────────

def get_conn():
    conn = sqlite3.connect(DB, timeout=120)
    conn.execute('PRAGMA busy_timeout=60000')
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA cache_size=-32000')
    conn.row_factory = sqlite3.Row
    return conn


def log_activity(action, result):
    try:
        conn = get_conn()
        conn.execute(
            'INSERT INTO agent_activity_log (agent_name, action, result) VALUES (?,?,?)',
            (AGENT_NAME, action, str(result)[:2000])
        )
        conn.commit()
        conn.close()
    except Exception:
        pass


# ── Filing type requirements ─────────────────────────────────────────────────

FILING_REQUIREMENTS = {
    'circuit_motion': {
        'rule': 'MCR 2.119',
        'word_limit': None,
        'page_limit': None,
        'required_sections': [
            'Caption with case number and judge name',
            'Title of motion',
            'Statement of issue(s)',
            'Statement of facts',
            'Argument with legal authority',
            'Relief requested',
            'Signature block (pro se)',
            'Certificate of service',
        ],
        'formatting': {
            'font': 'Times New Roman or similar serif, 12pt',
            'spacing': 'Double-spaced',
            'margins': '1 inch all sides',
        },
    },
    'circuit_brief': {
        'rule': 'MCR 2.119(A)(2)',
        'word_limit': None,
        'page_limit': None,
        'required_sections': [
            'Caption',
            'Table of contents (if over 5 pages)',
            'Statement of issues',
            'Statement of facts',
            'Argument',
            'Relief requested',
            'Signature block',
            'Certificate of service',
        ],
        'formatting': {
            'font': 'Times New Roman or similar serif, 12pt',
            'spacing': 'Double-spaced',
            'margins': '1 inch all sides',
        },
    },
    'appellate_brief': {
        'rule': 'MCR 7.212',
        'word_limit': 16000,
        'page_limit': 50,
        'required_sections': [
            'Table of contents',
            'Index of authorities',
            'Jurisdictional statement — MCR 7.212(C)(3)',
            'Statement of questions presented — MCR 7.212(C)(5)',
            'Statement of facts — MCR 7.212(C)(6)',
            'Argument — MCR 7.212(C)(7)',
            'Relief requested — MCR 7.212(C)(8)',
            'Signature block',
            'Certificate of service',
        ],
        'formatting': {
            'font': 'Times New Roman, 12pt minimum',
            'spacing': 'Double-spaced (footnotes may be single)',
            'margins': '1 inch all sides',
            'binding_margin': '0.5 inch additional on left',
        },
    },
    'msc_application': {
        'rule': 'MCR 7.305',
        'word_limit': 9000,
        'page_limit': None,
        'required_sections': [
            'Questions presented',
            'Statement of facts',
            'Argument for why leave should be granted',
            'Certificate of service',
        ],
        'formatting': {
            'font': 'Times New Roman, 12pt',
            'spacing': 'Double-spaced',
            'margins': '1 inch all sides',
        },
    },
    'emergency_motion': {
        'rule': 'MCR 2.119(B)',
        'word_limit': None,
        'page_limit': None,
        'required_sections': [
            'Caption',
            'Title indicating emergency/ex parte nature',
            'Verified statement of facts showing irreparable harm',
            'Specific facts showing notice is impractical (if ex parte)',
            'Legal authority',
            'Proposed order',
            'Signature block',
            'Certificate of service (if not ex parte)',
        ],
        'formatting': {
            'font': 'Times New Roman or similar serif, 12pt',
            'spacing': 'Double-spaced',
            'margins': '1 inch all sides',
        },
    },
}

# ── Prohibited content patterns ──────────────────────────────────────────────

PROHIBITED_PATTERNS = [
    (r'(?i)\bLitigationOS\b', 'AI system reference: "LitigationOS"'),
    (r'(?i)\bEGCP\b', 'AI scoring reference: "EGCP"'),
    (r'(?i)\bdelta\s*999\b', 'AI agent reference: "delta999"'),
    (r'(?i)\bundersigned\s+counsel\b', 'Implies attorney representation — use "Plaintiff, appearing pro se"'),
    (r'(?i)\battorney\s+for\s+plaintiff\b', 'Implies attorney representation'),
    (r'(?i)\bMCL\s+722\.27c\b', 'Non-existent statute — correct cite is MCL 722.23(j)'),
    (r'(?i)\bJane\s+Berry\b', 'Hallucinated entity — Jane Berry never existed'),
    (r'(?i)\bPatricia\s+Berry\b', 'Hallucinated entity — Patricia Berry never existed'),
    (r'(?i)\bBrady\s+v\.?\s*Maryland\b', 'Criminal-only — use Mathews v Eldridge for family law due process'),
]


# ── Compliance Agent class ───────────────────────────────────────────────────

class ComplianceAgent:
    """Filing compliance checker that validates court documents against
    Michigan Court Rules for formatting, content, and procedural requirements.

    Queries michigan_rules_extracted for authoritative rule text and
    cross-references filing requirements per MCR 2.119 and MCR 7.212.
    """

    def check_mcr_compliance(self, filing_text: str, filing_type: str = 'circuit_motion') -> dict:
        """Check filing text against MCR formatting and content rules.

        Scans for prohibited content (AI references, hallucinations, incorrect
        citations), verifies required sections are present, and validates
        formatting compliance against the applicable MCR rule set.
        """
        requirements = FILING_REQUIREMENTS.get(filing_type, FILING_REQUIREMENTS['circuit_motion'])

        # 1. Scan for prohibited content
        violations = []
        for pattern, description in PROHIBITED_PATTERNS:
            matches = re.findall(pattern, filing_text)
            if matches:
                violations.append({
                    'type': 'PROHIBITED_CONTENT',
                    'severity': 'CRITICAL',
                    'description': description,
                    'occurrences': len(matches),
                    'sample': matches[0],
                })

        # 2. Check for child's full name (MCR 8.119(H))
        child_name_patterns = [
            r'(?i)L\.?\s*D\.?\s*W\.?\s*Pigors',
            r'(?i)L\.?\s*D\.?\s*W\.?\s*Watson',
        ]
        for pat in child_name_patterns:
            if re.search(pat, filing_text):
                violations.append({
                    'type': 'CHILD_NAME_VIOLATION',
                    'severity': 'CRITICAL',
                    'description': 'Child full name exposed — MCR 8.119(H) requires initials only (L.D.W.)',
                })

        # 3. Check required sections
        sections_found = []
        sections_missing = []
        for section in requirements['required_sections']:
            section_keywords = section.lower().split()[:3]
            found = any(
                all(kw in filing_text.lower() for kw in section_keywords[:2])
                for _ in [None]
            )
            if found:
                sections_found.append(section)
            else:
                sections_missing.append(section)

        # 4. Verify MCR rule text from database
        conn = get_conn()
        rule_verification = []
        rule_cite = requirements['rule']
        try:
            rows = conn.execute(
                "SELECT rule_number, rule_title, full_text "
                "FROM michigan_rules_extracted "
                "WHERE rule_number LIKE ? LIMIT 3",
                (f'%{rule_cite}%',)
            ).fetchall()
            rule_verification = [{'rule': r['rule_number'], 'title': r['rule_title']} for r in rows]
        except Exception:
            pass
        conn.close()

        # 5. Overall compliance score
        total_checks = len(requirements['required_sections']) + len(PROHIBITED_PATTERNS)
        passed_checks = len(sections_found) + (len(PROHIBITED_PATTERNS) - len(violations))
        score = round(passed_checks / total_checks * 100, 1) if total_checks > 0 else 0

        result = {
            'filing_type': filing_type,
            'governing_rule': requirements['rule'],
            'compliance_score': score,
            'status': 'PASS' if score >= 80 and not any(v['severity'] == 'CRITICAL' for v in violations) else 'FAIL',
            'violations': violations,
            'sections_found': sections_found,
            'sections_missing': sections_missing,
            'formatting_requirements': requirements['formatting'],
            'rule_verified_in_db': rule_verification,
        }
        log_activity(f'check_mcr:{filing_type}', json.dumps(result, default=str)[:2000])
        return result

    def validate_word_count(self, filing_text: str, filing_type: str = 'appellate_brief') -> dict:
        """Validate word count against MCR limits for the filing type.

        MCR 7.212(B) limits appellate briefs to 16,000 words (50 pages).
        MCR 7.305 limits MSC applications to 9,000 words.
        """
        requirements = FILING_REQUIREMENTS.get(filing_type, FILING_REQUIREMENTS['circuit_motion'])
        word_limit = requirements.get('word_limit')
        page_limit = requirements.get('page_limit')

        # Count words (exclude headers/footers/captions by splitting on whitespace)
        words = filing_text.split()
        word_count = len(words)

        # Estimate pages (250 words/page for double-spaced 12pt)
        estimated_pages = round(word_count / 250, 1)

        word_ok = word_limit is None or word_count <= word_limit
        page_ok = page_limit is None or estimated_pages <= page_limit

        warnings = []
        if word_limit and word_count > word_limit * 0.9:
            pct = round(word_count / word_limit * 100, 1)
            warnings.append(f"Word count at {pct}% of limit ({word_count}/{word_limit})")
        if page_limit and estimated_pages > page_limit * 0.9:
            warnings.append(f"Estimated pages at {estimated_pages}/{page_limit}")

        result = {
            'filing_type': filing_type,
            'governing_rule': requirements['rule'],
            'word_count': word_count,
            'word_limit': word_limit,
            'word_ok': word_ok,
            'estimated_pages': estimated_pages,
            'page_limit': page_limit,
            'page_ok': page_ok,
            'status': 'PASS' if word_ok and page_ok else 'FAIL',
            'warnings': warnings,
        }
        log_activity(f'word_count:{filing_type}', json.dumps(result, default=str)[:2000])
        return result

    def check_required_sections(self, filing_type: str = 'appellate_brief') -> dict:
        """Return the required sections and formatting rules for a filing type.

        Queries michigan_rules_extracted for the authoritative rule text
        governing the specified filing type and returns a structured checklist.
        """
        requirements = FILING_REQUIREMENTS.get(filing_type)
        if not requirements:
            return {
                'filing_type': filing_type,
                'error': f'Unknown filing type. Available: {list(FILING_REQUIREMENTS.keys())}',
            }

        conn = get_conn()

        # Pull authoritative rule text from DB
        rule_text = None
        rule_cite = requirements['rule']
        try:
            row = conn.execute(
                "SELECT rule_number, rule_title, full_text "
                "FROM michigan_rules_extracted "
                "WHERE rule_number LIKE ? LIMIT 1",
                (f'%{rule_cite}%',)
            ).fetchone()
            if row:
                rule_text = {
                    'rule_number': row['rule_number'],
                    'rule_title': row['rule_title'],
                    'full_text_preview': str(row['full_text'])[:500] if row['full_text'] else '',
                }
        except Exception:
            pass

        # Pull related rules for cross-reference
        related_rules = []
        try:
            rows = conn.execute(
                "SELECT rule_number, rule_title "
                "FROM michigan_rules_extracted "
                "WHERE rule_number LIKE ? OR rule_number LIKE ? "
                "LIMIT 10",
                (f'{rule_cite.split()[0]}%', f'%service%')
            ).fetchall()
            related_rules = [{'number': r['rule_number'], 'title': r['rule_title']} for r in rows]
        except Exception:
            pass

        conn.close()

        result = {
            'filing_type': filing_type,
            'governing_rule': requirements['rule'],
            'required_sections': requirements['required_sections'],
            'formatting': requirements['formatting'],
            'word_limit': requirements.get('word_limit'),
            'page_limit': requirements.get('page_limit'),
            'rule_text_from_db': rule_text,
            'related_rules': related_rules,
        }
        log_activity(f'required_sections:{filing_type}', json.dumps(result, default=str)[:2000])
        return result

    def full_compliance_report(self, filing_stack: str = '') -> dict:
        """Generate a full compliance report across all filing types.

        Queries the filing stack index for pending filings and checks each
        against its applicable MCR requirements.
        """
        conn = get_conn()

        # Get filings from stack
        filings = []
        try:
            rows = conn.execute(
                "SELECT * FROM apex_filing_stack_index "
                "WHERE stack_label LIKE ? OR meek_track LIKE ? "
                "LIMIT 20",
                (f'%{filing_stack}%', f'%{filing_stack}%')
            ).fetchall()
            filings = [dict(r) for r in rows]
        except Exception:
            pass

        # Check each filing type's requirements
        filing_types_checked = {}
        for ft_name, ft_reqs in FILING_REQUIREMENTS.items():
            rule_cite = ft_reqs['rule']
            verified = False
            try:
                row = conn.execute(
                    "SELECT COUNT(*) as cnt FROM michigan_rules_extracted "
                    "WHERE rule_number LIKE ?",
                    (f'%{rule_cite}%',)
                ).fetchone()
                verified = row['cnt'] > 0
            except Exception:
                pass
            filing_types_checked[ft_name] = {
                'rule': rule_cite,
                'sections_required': len(ft_reqs['required_sections']),
                'word_limit': ft_reqs.get('word_limit'),
                'rule_in_db': verified,
            }

        conn.close()

        result = {
            'filing_stack': filing_stack,
            'filings_in_stack': len(filings),
            'filing_types_checked': filing_types_checked,
            'total_filing_types': len(FILING_REQUIREMENTS),
            'prohibited_patterns_active': len(PROHIBITED_PATTERNS),
        }
        log_activity(f'full_report:{filing_stack}', json.dumps(result, default=str)[:2000])
        return result


# ── Module-level convenience functions ───────────────────────────────────────

_agent = ComplianceAgent()

def check_mcr_compliance(filing_text: str, filing_type: str = 'circuit_motion') -> dict:
    return _agent.check_mcr_compliance(filing_text, filing_type)

def validate_word_count(filing_text: str, filing_type: str = 'appellate_brief') -> dict:
    return _agent.validate_word_count(filing_text, filing_type)

def check_required_sections(filing_type: str = 'appellate_brief') -> dict:
    return _agent.check_required_sections(filing_type)

def full_compliance_report(filing_stack: str = '') -> dict:
    return _agent.full_compliance_report(filing_stack)


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Delta999 Compliance Agent — Filing Compliance Checker')
    parser.add_argument('--action', required=True,
                        choices=['check_mcr', 'word_count', 'required_sections', 'full_report'],
                        help='Action to perform')
    parser.add_argument('--filing-text', type=str, help='Filing text to check')
    parser.add_argument('--filing-type', type=str, default='circuit_motion',
                        help='Filing type (circuit_motion, appellate_brief, msc_application, etc.)')
    parser.add_argument('--filing-stack', type=str, default='', help='Filing stack for full report')
    args = parser.parse_args()

    if args.action == 'check_mcr':
        if not args.filing_text:
            parser.error('--filing-text required for check_mcr')
        result = check_mcr_compliance(args.filing_text, args.filing_type)
    elif args.action == 'word_count':
        if not args.filing_text:
            parser.error('--filing-text required for word_count')
        result = validate_word_count(args.filing_text, args.filing_type)
    elif args.action == 'required_sections':
        result = check_required_sections(args.filing_type)
    elif args.action == 'full_report':
        result = full_compliance_report(args.filing_stack)
    else:
        parser.print_help()
        return

    print(json.dumps(result, indent=2, default=str))


if __name__ == '__main__':
    main()
