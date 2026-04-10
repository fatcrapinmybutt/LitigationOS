#!/usr/bin/env python3
"""
Delta999 Citation Agent — Legal citation validator and authority finder.

Validates legal citations against michigan_rules_extracted and authority_chains_v2,
finds supporting authority for legal claims, and checks citation accuracy across
filings to prevent hallucinated or incorrect citations.

CLI:
    python delta999_citation_agent.py --action validate --text "MCR 2.119(A) requires..."
    python delta999_citation_agent.py --action find_authority --claim "judicial bias"
    python delta999_citation_agent.py --action check_accuracy
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
AGENT_NAME = 'delta999_citation_agent'

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


# ── Citation extraction regex ────────────────────────────────────────────────

# Matches MCR X.XXX, MCL XXX.XX, MRE XXX, case citations (Name v Name, NNN Mich XXX)
CITATION_PATTERNS = [
    (r'MCR\s+\d+\.\d+(?:\([A-Za-z0-9]+\))*', 'MCR'),
    (r'MCL\s+\d+\.\d+[a-z]?(?:\([A-Za-z0-9]+\))*', 'MCL'),
    (r'MRE\s+\d+(?:\([a-z]\)(?:\(\d+\))?)?', 'MRE'),
    (r'\d+\s+Mich\s+(?:App\s+)?\d+', 'CASE_MICH'),
    (r'\d+\s+NW\s*2d\s+\d+', 'CASE_NW2D'),
    (r'\d+\s+US\s+\d+', 'CASE_US'),
    (r'\d+\s+USC\s+§?\s*\d+', 'STATUTE_FED'),
]


def extract_citations(text: str) -> list:
    """Extract all legal citations from text using regex patterns."""
    found = []
    for pattern, cite_type in CITATION_PATTERNS:
        for match in re.finditer(pattern, text):
            found.append({
                'citation': match.group(0).strip(),
                'type': cite_type,
                'position': match.start(),
            })
    return found


# ── Citation Agent class ─────────────────────────────────────────────────────

class CitationAgent:
    """Legal citation validator that cross-references all citations against
    the litigation database to prevent hallucinated or inaccurate cites.

    Searches michigan_rules_extracted for MCR/MCL/MRE text,
    authority_chains_v2 for citation provenance, and master_citations
    for the full citation universe.
    """

    def validate_citations(self, text: str) -> dict:
        """Validate every legal citation found in the provided text.

        Extracts citations via regex, then verifies each against
        michigan_rules_extracted and authority_chains_v2. Returns a
        per-citation validation status: VERIFIED, UNVERIFIED, or INVALID.
        """
        citations = extract_citations(text)
        if not citations:
            return {'text_length': len(text), 'citations_found': 0, 'results': [],
                    'summary': 'No legal citations detected in text.'}

        conn = get_conn()
        results = []

        for cite_info in citations:
            cite = cite_info['citation']
            cite_type = cite_info['type']
            status = 'UNVERIFIED'
            db_match = None

            # Check michigan_rules_extracted for MCR/MCL/MRE
            if cite_type in ('MCR', 'MCL', 'MRE'):
                try:
                    rows = conn.execute(
                        "SELECT rule_number, rule_title, full_text "
                        "FROM michigan_rules_extracted "
                        "WHERE rule_number LIKE ? LIMIT 3",
                        (f'%{cite}%',)
                    ).fetchall()
                    if rows:
                        status = 'VERIFIED'
                        db_match = {
                            'table': 'michigan_rules_extracted',
                            'rule_number': rows[0]['rule_number'],
                            'rule_title': rows[0]['rule_title'],
                            'text_preview': str(rows[0]['full_text'])[:200] if rows[0]['full_text'] else '',
                        }
                except Exception:
                    pass

            # Check authority_chains_v2 for all citation types
            if status == 'UNVERIFIED':
                try:
                    rows = conn.execute(
                        "SELECT citation, authority_type, context, confidence "
                        "FROM authority_chains_v2 "
                        "WHERE citation LIKE ? LIMIT 5",
                        (f'%{cite}%',)
                    ).fetchall()
                    if rows:
                        status = 'VERIFIED'
                        db_match = {
                            'table': 'authority_chains_v2',
                            'citation': rows[0]['citation'],
                            'authority_type': rows[0]['authority_type'],
                            'confidence': rows[0]['confidence'],
                        }
                except Exception:
                    pass

            # Check master_citations as final fallback
            if status == 'UNVERIFIED':
                try:
                    rows = conn.execute(
                        "SELECT citation, citation_type, source_context "
                        "FROM master_citations "
                        "WHERE citation LIKE ? LIMIT 3",
                        (f'%{cite}%',)
                    ).fetchall()
                    if rows:
                        status = 'VERIFIED'
                        db_match = {
                            'table': 'master_citations',
                            'citation': rows[0]['citation'],
                            'citation_type': rows[0]['citation_type'],
                        }
                except Exception:
                    pass

            results.append({
                'citation': cite,
                'type': cite_type,
                'status': status,
                'db_match': db_match,
            })

        conn.close()

        verified = sum(1 for r in results if r['status'] == 'VERIFIED')
        unverified = sum(1 for r in results if r['status'] == 'UNVERIFIED')

        output = {
            'text_length': len(text),
            'citations_found': len(citations),
            'verified': verified,
            'unverified': unverified,
            'accuracy_pct': round(verified / len(results) * 100, 1) if results else 0,
            'results': results,
        }
        log_activity(f'validate_citations:{len(citations)}found', json.dumps(output, default=str)[:2000])
        return output

    def find_supporting_authority(self, claim: str) -> dict:
        """Find legal authorities that support a specific legal claim.

        Searches authority_chains_v2 for matching authorities,
        michigan_rules_extracted for applicable rules, and master_citations
        for additional supporting case law.
        """
        conn = get_conn()
        safe_claim = sanitize_fts5(claim)

        # 1. Search authority_chains_v2
        authorities = []
        try:
            rows = conn.execute(
                "SELECT citation, authority_type, context, confidence "
                "FROM authority_chains_v2 "
                "WHERE context LIKE ? OR citation LIKE ? "
                "ORDER BY confidence DESC LIMIT 25",
                (f'%{claim}%', f'%{claim}%')
            ).fetchall()
            authorities = [dict(r) for r in rows]
        except Exception:
            pass

        # 2. Search michigan_rules_extracted
        rules = []
        try:
            rows = conn.execute(
                "SELECT rule_number, rule_title, full_text "
                "FROM michigan_rules_extracted "
                "WHERE full_text LIKE ? OR rule_title LIKE ? "
                "LIMIT 15",
                (f'%{claim}%', f'%{claim}%')
            ).fetchall()
            rules = [dict(r) for r in rows]
        except Exception:
            pass

        # 3. Search master_citations for supporting case law
        case_law = []
        try:
            rows = conn.execute(
                "SELECT citation, citation_type, source_context "
                "FROM master_citations "
                "WHERE source_context LIKE ? "
                "LIMIT 20",
                (f'%{claim}%',)
            ).fetchall()
            case_law = [dict(r) for r in rows]
        except Exception:
            pass

        # 4. LLM synthesis of strongest authorities
        try:
            synthesis = llm_ask(
                f"Find the strongest legal authorities supporting the claim: '{claim}'\n\n"
                f"Authorities found ({len(authorities)}):\n"
                f"{json.dumps(authorities[:10], default=str)[:1000]}\n\n"
                f"Rules found ({len(rules)}):\n"
                f"{json.dumps([{'num': r['rule_number'], 'title': r['rule_title']} for r in rules[:5]], default=str)[:500]}\n\n"
                f"Case law ({len(case_law)}):\n"
                f"{json.dumps(case_law[:5], default=str)[:500]}\n\n"
                f"Rank the top 5 strongest authorities and explain why each supports the claim.",
                system_prompt=(
                    "You are a Michigan legal authority specialist. Rules:\n"
                    "1. Rank authorities by relevance and binding weight\n"
                    "2. Distinguish mandatory from persuasive authority\n"
                    "3. Only cite authorities present in the provided context — mark others UNVERIFIED\n"
                    "4. Use 'L.D.W.' for the minor child — never spell out the full name\n"
                    "5. Note if any authority has been overruled or distinguished"
                )
            )
        except Exception as e:
            synthesis = f"LLM unavailable: {e}"

        conn.close()

        result = {
            'claim': claim,
            'authorities_found': len(authorities),
            'rules_found': len(rules),
            'case_law_found': len(case_law),
            'top_authorities': authorities[:10],
            'applicable_rules': [{'number': r['rule_number'], 'title': r['rule_title']} for r in rules],
            'synthesis': synthesis,
        }
        log_activity(f'find_authority:{claim[:60]}', json.dumps(result, default=str)[:2000])
        return result

    def check_citation_accuracy(self) -> dict:
        """Audit citation accuracy across the entire authority database.

        Cross-references authority_chains_v2 against michigan_rules_extracted
        to identify citations that reference non-existent rules, incorrect
        rule numbers, or known hallucination patterns.
        """
        conn = get_conn()

        # Known hallucination patterns to flag
        hallucination_patterns = [
            ('MCL 722.27c', 'MCL 722.27c does not exist — correct cite is MCL 722.23(j)'),
            ('Jane Berry', 'Jane Berry is a hallucinated entity — never existed'),
            ('Patricia Berry', 'Patricia Berry is a hallucinated entity — never existed'),
        ]

        # 1. Count total authorities
        total_authorities = 0
        try:
            total_authorities = conn.execute(
                "SELECT COUNT(DISTINCT citation) FROM authority_chains_v2"
            ).fetchone()[0]
        except Exception:
            pass

        # 2. Count total rules
        total_rules = 0
        try:
            total_rules = conn.execute(
                "SELECT COUNT(*) FROM michigan_rules_extracted"
            ).fetchone()[0]
        except Exception:
            pass

        # 3. Check for hallucination patterns in authority_chains_v2
        flagged = []
        for pattern, reason in hallucination_patterns:
            try:
                rows = conn.execute(
                    "SELECT citation, context FROM authority_chains_v2 "
                    "WHERE citation LIKE ? OR context LIKE ? LIMIT 10",
                    (f'%{pattern}%', f'%{pattern}%')
                ).fetchall()
                for r in rows:
                    flagged.append({
                        'citation': r['citation'],
                        'pattern': pattern,
                        'reason': reason,
                        'severity': 'CRITICAL',
                    })
            except Exception:
                pass

        # 4. Sample MCR citations and verify they exist in rules table
        mcr_audit = []
        try:
            rows = conn.execute(
                "SELECT DISTINCT citation FROM authority_chains_v2 "
                "WHERE citation LIKE 'MCR%' LIMIT 50"
            ).fetchall()
            for r in rows:
                cite = r['citation']
                match = conn.execute(
                    "SELECT rule_number FROM michigan_rules_extracted "
                    "WHERE rule_number LIKE ? LIMIT 1",
                    (f'%{cite}%',)
                ).fetchone()
                mcr_audit.append({
                    'citation': cite,
                    'exists_in_rules': match is not None,
                })
        except Exception:
            pass

        verified_mcr = sum(1 for a in mcr_audit if a['exists_in_rules'])

        conn.close()

        result = {
            'total_authorities': total_authorities,
            'total_rules': total_rules,
            'hallucinations_flagged': len(flagged),
            'flagged_items': flagged,
            'mcr_audit_sample': len(mcr_audit),
            'mcr_verified': verified_mcr,
            'mcr_accuracy_pct': round(verified_mcr / len(mcr_audit) * 100, 1) if mcr_audit else 0,
        }
        log_activity('check_citation_accuracy', json.dumps(result, default=str)[:2000])
        return result


# ── Module-level convenience functions ───────────────────────────────────────

_agent = CitationAgent()

def validate_citations(text: str) -> dict:
    return _agent.validate_citations(text)

def find_supporting_authority(claim: str) -> dict:
    return _agent.find_supporting_authority(claim)

def search_authority(topic: str) -> dict:
    """Alias used by orchestrator pipeline."""
    return _agent.find_supporting_authority(topic)

def check_citation_accuracy() -> dict:
    return _agent.check_citation_accuracy()


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Delta999 Citation Agent — Legal Citation Validator')
    parser.add_argument('--action', required=True,
                        choices=['validate', 'find_authority', 'check_accuracy'],
                        help='Action to perform')
    parser.add_argument('--text', type=str, help='Text to validate citations in')
    parser.add_argument('--claim', type=str, help='Legal claim to find authority for')
    args = parser.parse_args()

    if args.action == 'validate':
        if not args.text:
            parser.error('--text required for validate')
        result = validate_citations(args.text)
    elif args.action == 'find_authority':
        if not args.claim:
            parser.error('--claim required for find_authority')
        result = find_supporting_authority(args.claim)
    elif args.action == 'check_accuracy':
        result = check_citation_accuracy()
    else:
        parser.print_help()
        return

    print(json.dumps(result, indent=2, default=str))


if __name__ == '__main__':
    main()
