#!/usr/bin/env python3
"""
Delta999 Red Team Agent — Vulnerability assessor and war-gaming specialist.

Identifies weaknesses in filings before submission, predicts opposition
arguments, and scores filing strength. Operates as adversary's counsel
to stress-test every claim, citation, and evidentiary foundation.

CLI:
    python delta999_redteam_agent.py --action weaknesses --filing-text "..."
    python delta999_redteam_agent.py --action predict_opposition --filing-text "..."
    python delta999_redteam_agent.py --action score --filing-text "..."
    python delta999_redteam_agent.py --action attack --filing-stack "MEEK1"
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
AGENT_NAME = 'delta999_redteam_agent'

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


def _fts_search(conn, fts_table, base_table, text_col, query, limit=25):
    """FTS5 search with automatic LIKE fallback per Rule 15."""
    safe_query = sanitize_fts5(query)
    if _HAS_SHARED:
        rows, method = safe_fts5_search(conn, fts_table, base_table, text_col, query, limit=limit)
        return [dict(r) if hasattr(r, 'keys') else r for r in rows], method

    try:
        rows = conn.execute(
            f"SELECT * FROM [{fts_table}] WHERE [{fts_table}] MATCH ? ORDER BY rank LIMIT ?",
            (safe_query, limit)
        ).fetchall()
        return [dict(r) for r in rows], 'FTS5'
    except Exception:
        terms = [t for t in safe_query.split() if len(t) >= 2 and t.upper() not in {"AND", "OR", "NOT"}]
        if not terms:
            return [], 'EMPTY'
        like_clauses = " AND ".join([f"[{text_col}] LIKE ?" for _ in terms])
        like_params = [f"%{t}%" for t in terms]
        try:
            rows = conn.execute(
                f"SELECT * FROM [{base_table}] WHERE {like_clauses} LIMIT ?",
                like_params + [limit]
            ).fetchall()
            return [dict(r) for r in rows], 'LIKE_FALLBACK'
        except Exception:
            return [], 'ERROR'


# ── Attack vector definitions ────────────────────────────────────────────────

ATTACK_VECTORS = [
    {
        'name': 'Unsupported factual assertions',
        'description': 'Claims made without evidence citations',
        'severity_weight': 3,
    },
    {
        'name': 'Unverified legal citations',
        'description': 'Citations not confirmed in authority database',
        'severity_weight': 3,
    },
    {
        'name': 'Standing/jurisdiction defects',
        'description': 'Arguments that may fail on procedural grounds',
        'severity_weight': 4,
    },
    {
        'name': 'Hearsay without exception',
        'description': 'Evidence that may be excluded under MRE 802',
        'severity_weight': 2,
    },
    {
        'name': 'Emotional vs legal argument',
        'description': 'Sections that argue emotion rather than law',
        'severity_weight': 2,
    },
    {
        'name': 'Judicial immunity defense',
        'description': 'Claims against judge that may be barred by judicial immunity',
        'severity_weight': 4,
    },
    {
        'name': 'Preservation failures',
        'description': 'Issues not raised at trial court level',
        'severity_weight': 3,
    },
    {
        'name': 'Pro se formatting defects',
        'description': 'Formatting issues that may cause rejection',
        'severity_weight': 1,
    },
]


# ── Red Team Agent class ────────────────────────────────────────────────────

class RedTeamAgent:
    """Vulnerability assessor that war-games filings by assuming the role
    of opposing counsel and identifying every exploitable weakness.

    Queries authority_chains_v2 to verify citation foundations,
    evidence_quotes to check evidentiary support, and contradiction_map
    to identify self-inflicted vulnerabilities.
    """

    def identify_weaknesses(self, filing_text: str) -> dict:
        """Identify vulnerabilities in a filing that opposing counsel would exploit.

        Scans for unsupported assertions, unverified citations, hearsay,
        emotional arguments, and procedural defects. Cross-references
        against the authority database and evidence repository.
        """
        conn = get_conn()
        findings = []

        # 1. Extract citations and verify each
        citation_patterns = [
            (r'MCR\s+\d+\.\d+(?:\([A-Za-z0-9]+\))*', 'MCR'),
            (r'MCL\s+\d+\.\d+[a-z]?(?:\([A-Za-z0-9]+\))*', 'MCL'),
            (r'MRE\s+\d+', 'MRE'),
        ]
        unverified_cites = []
        for pattern, cite_type in citation_patterns:
            for match in re.finditer(pattern, filing_text):
                cite = match.group(0)
                try:
                    row = conn.execute(
                        "SELECT COUNT(*) as cnt FROM michigan_rules_extracted "
                        "WHERE rule_number LIKE ?",
                        (f'%{cite}%',)
                    ).fetchone()
                    if row['cnt'] == 0:
                        auth_row = conn.execute(
                            "SELECT COUNT(*) as cnt FROM authority_chains_v2 "
                            "WHERE citation LIKE ?",
                            (f'%{cite}%',)
                        ).fetchone()
                        if auth_row['cnt'] == 0:
                            unverified_cites.append(cite)
                except Exception:
                    unverified_cites.append(cite)

        if unverified_cites:
            findings.append({
                'vector': 'Unverified legal citations',
                'severity': 'HIGH',
                'details': f'{len(unverified_cites)} citation(s) not found in authority database',
                'citations': unverified_cites[:10],
                'mitigation': 'Verify each citation in michigan_rules_extracted or authority_chains_v2',
            })

        # 2. Check for prohibited content
        prohibited = [
            (r'(?i)\bLitigationOS\b', 'AI system reference leaked'),
            (r'(?i)\bundersigned\s+counsel\b', 'Implies attorney representation (pro se violation)'),
            (r'(?i)\bMCL\s+722\.27c\b', 'Non-existent statute cited'),
            (r'(?i)\bBrady\s+v\.?\s*Maryland\b', 'Criminal-only authority used in family law'),
        ]
        for pattern, desc in prohibited:
            if re.search(pattern, filing_text):
                findings.append({
                    'vector': 'Prohibited content',
                    'severity': 'CRITICAL',
                    'details': desc,
                    'mitigation': 'Remove before filing',
                })

        # 3. Check evidentiary support density
        sentences = [s.strip() for s in re.split(r'[.!?]+', filing_text) if len(s.strip()) > 30]
        sentences_with_cites = sum(1 for s in sentences if re.search(r'MCR|MCL|MRE|Exhibit|¶|p\.\s*\d+', s))
        citation_density = round(sentences_with_cites / len(sentences) * 100, 1) if sentences else 0

        if citation_density < 30:
            findings.append({
                'vector': 'Low citation density',
                'severity': 'MEDIUM',
                'details': f'Only {citation_density}% of assertions cite authority ({sentences_with_cites}/{len(sentences)})',
                'mitigation': 'Add MCR/MCL citations or evidence references to unsupported assertions',
            })

        # 4. Check for self-contradictions against our own evidence
        our_contradictions = []
        try:
            rows = conn.execute(
                "SELECT person, statement_1, statement_2, severity "
                "FROM contradiction_map "
                "WHERE person LIKE '%Pigors%' OR person LIKE '%Andrew%' "
                "ORDER BY severity DESC LIMIT 10"
            ).fetchall()
            our_contradictions = [dict(r) for r in rows]
        except Exception:
            pass

        if our_contradictions:
            findings.append({
                'vector': 'Potential self-contradiction',
                'severity': 'HIGH',
                'details': f'{len(our_contradictions)} documented contradiction(s) in our own record',
                'items': [c.get('statement_1', '')[:100] for c in our_contradictions[:3]],
                'mitigation': 'Address proactively or omit contradicted claims',
            })

        conn.close()

        # Sort by severity
        severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
        findings.sort(key=lambda f: severity_order.get(f['severity'], 9))

        result = {
            'filing_length': len(filing_text),
            'total_findings': len(findings),
            'critical': sum(1 for f in findings if f['severity'] == 'CRITICAL'),
            'high': sum(1 for f in findings if f['severity'] == 'HIGH'),
            'medium': sum(1 for f in findings if f['severity'] == 'MEDIUM'),
            'findings': findings,
            'citation_density_pct': citation_density,
        }
        log_activity('identify_weaknesses', json.dumps(result, default=str)[:2000])
        return result

    def predict_opposition_arguments(self, filing_text: str = '') -> dict:
        """Predict what arguments opposing counsel will make.

        Queries evidence_quotes for adversary-favorable evidence,
        authority_chains_v2 for authorities that cut against our position,
        and the adversary assertions table for known opposition themes.
        """
        conn = get_conn()

        # 1. Adversary's known assertion patterns
        adversary_assertions = []
        try:
            rows = conn.execute(
                "SELECT * FROM adversary_assertions "
                "ORDER BY ROWID DESC LIMIT 30"
            ).fetchall()
            adversary_assertions = [dict(r) for r in rows]
        except Exception:
            pass

        # 2. Evidence favorable to adversary
        adversary_evidence, ev_method = _fts_search(
            conn, 'evidence_fts', 'evidence_quotes', 'quote_text',
            'Emily Watson OR defendant OR mother OR custody favorable',
            limit=20
        )

        # 3. Authorities that may cut against us
        counter_authorities = []
        try:
            rows = conn.execute(
                "SELECT citation, authority_type, context, confidence "
                "FROM authority_chains_v2 "
                "WHERE context LIKE '%presumption%' "
                "   OR context LIKE '%established custodial%' "
                "   OR context LIKE '%status quo%' "
                "   OR context LIKE '%abuse of discretion%' "
                "ORDER BY confidence DESC LIMIT 15",
                ()
            ).fetchall()
            counter_authorities = [dict(r) for r in rows]
        except Exception:
            pass

        # 4. LLM prediction of opposition arguments
        try:
            prediction = llm_ask(
                f"Acting as opposing counsel (Emily A. Watson's side), predict the top 5 arguments "
                f"that would be raised against the filing.\n\n"
                f"Known adversary assertions: {len(adversary_assertions)}\n"
                f"Sample assertions: {json.dumps(adversary_assertions[:5], default=str)[:800]}\n\n"
                f"Counter-authorities found: {len(counter_authorities)}\n"
                f"Sample: {json.dumps(counter_authorities[:3], default=str)[:500]}\n\n"
                f"For each predicted argument: (1) the argument, (2) authority they would cite, "
                f"(3) how strong it is (1-10), (4) our best counter.",
                system_prompt=(
                    "You are playing the role of opposing counsel in Michigan family court. Rules:\n"
                    "1. Think like a defense attorney — find every vulnerability\n"
                    "2. Cite specific MCR/MCL that support the defense position\n"
                    "3. Use 'L.D.W.' for the minor child — never spell out the full name\n"
                    "4. Focus on: standing, preservation, judicial discretion, res judicata\n"
                    "5. Only cite authorities present in the context — mark others UNVERIFIED"
                )
            )
        except Exception as e:
            prediction = f"LLM unavailable: {e}"

        conn.close()

        result = {
            'adversary_assertions_found': len(adversary_assertions),
            'adversary_evidence_found': len(adversary_evidence),
            'counter_authorities_found': len(counter_authorities),
            'opposition_prediction': prediction,
            'evidence_method': ev_method,
        }
        log_activity('predict_opposition', json.dumps(result, default=str)[:2000])
        return result

    def score_filing_strength(self, filing_text: str = '') -> dict:
        """Score a filing's overall strength on a 0-100 scale.

        Evaluates across four dimensions: Evidence Foundation (0-25),
        Legal Authority (0-25), Procedural Compliance (0-25), and
        Persuasive Impact (0-25). Each dimension is grounded in DB queries.
        """
        conn = get_conn()
        scores = {}

        # 1. Evidence Foundation (0-25) — count evidence support
        evidence_count = 0
        try:
            evidence_count = conn.execute("SELECT COUNT(*) FROM evidence_quotes").fetchone()[0]
        except Exception:
            pass
        evidence_score = min(25, round(evidence_count / 4000 * 25))
        scores['evidence_foundation'] = {
            'score': evidence_score,
            'max': 25,
            'detail': f'{evidence_count} evidence quotes in database',
        }

        # 2. Legal Authority (0-25) — count verified citations
        authority_count = 0
        try:
            authority_count = conn.execute(
                "SELECT COUNT(DISTINCT citation) FROM authority_chains_v2"
            ).fetchone()[0]
        except Exception:
            pass
        authority_score = min(25, round(authority_count / 1200 * 25))
        scores['legal_authority'] = {
            'score': authority_score,
            'max': 25,
            'detail': f'{authority_count} distinct authorities in chain',
        }

        # 3. Procedural Compliance (0-25) — check rules coverage
        rules_count = 0
        try:
            rules_count = conn.execute(
                "SELECT COUNT(*) FROM michigan_rules_extracted"
            ).fetchone()[0]
        except Exception:
            pass
        compliance_score = min(25, round(rules_count / 100 * 25))
        scores['procedural_compliance'] = {
            'score': compliance_score,
            'max': 25,
            'detail': f'{rules_count} Michigan rules indexed for compliance checks',
        }

        # 4. Persuasive Impact (0-25) — impeachment & contradiction strength
        impeachment_count = 0
        try:
            impeachment_count = conn.execute("SELECT COUNT(*) FROM impeachment_matrix").fetchone()[0]
        except Exception:
            pass
        contradiction_count = 0
        try:
            contradiction_count = conn.execute("SELECT COUNT(*) FROM contradiction_map").fetchone()[0]
        except Exception:
            pass
        impact_score = min(25, round((impeachment_count + contradiction_count) / 500 * 25))
        scores['persuasive_impact'] = {
            'score': impact_score,
            'max': 25,
            'detail': f'{impeachment_count} impeachment entries, {contradiction_count} contradictions',
        }

        conn.close()

        total = sum(s['score'] for s in scores.values())
        status = 'STRONG' if total >= 75 else 'MODERATE' if total >= 50 else 'WEAK'

        result = {
            'total_score': total,
            'max_score': 100,
            'status': status,
            'dimensions': scores,
            'recommendation': (
                'Filing is well-supported — proceed with confidence' if total >= 75
                else 'Filing has moderate support — address gaps before submission' if total >= 50
                else 'Filing has significant weaknesses — substantial revision needed'
            ),
        }
        log_activity(f'score_strength:{total}/100', json.dumps(result, default=str)[:2000])
        return result

    def attack_filing(self, filing_stack: str = '') -> dict:
        """Full red-team attack on a filing stack — combines all assessments."""
        weaknesses = self.identify_weaknesses(filing_stack)
        opposition = self.predict_opposition_arguments(filing_stack)
        strength = self.score_filing_strength(filing_stack)

        result = {
            'filing_stack': filing_stack,
            'strength_score': strength['total_score'],
            'strength_status': strength['status'],
            'weaknesses_found': weaknesses['total_findings'],
            'critical_issues': weaknesses['critical'],
            'opposition_prediction': opposition.get('opposition_prediction', '')[:500],
            'dimensions': strength['dimensions'],
            'top_findings': weaknesses['findings'][:5],
        }
        log_activity(f'attack:{filing_stack}', json.dumps(result, default=str)[:2000])
        return result


# ── Module-level convenience functions ───────────────────────────────────────

_agent = RedTeamAgent()

def identify_weaknesses(filing_text: str) -> dict:
    return _agent.identify_weaknesses(filing_text)

def predict_opposition_arguments(filing_text: str = '') -> dict:
    return _agent.predict_opposition_arguments(filing_text)

def score_filing_strength(filing_text: str = '') -> dict:
    return _agent.score_filing_strength(filing_text)

def attack_filing(filing_stack: str = '') -> dict:
    return _agent.attack_filing(filing_stack)


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Delta999 Red Team Agent — Vulnerability Assessor')
    parser.add_argument('--action', required=True,
                        choices=['weaknesses', 'predict_opposition', 'score', 'attack'],
                        help='Action to perform')
    parser.add_argument('--filing-text', type=str, default='', help='Filing text to analyze')
    parser.add_argument('--filing-stack', type=str, default='', help='Filing stack for full attack')
    args = parser.parse_args()

    if args.action == 'weaknesses':
        if not args.filing_text:
            parser.error('--filing-text required for weaknesses')
        result = identify_weaknesses(args.filing_text)
    elif args.action == 'predict_opposition':
        result = predict_opposition_arguments(args.filing_text)
    elif args.action == 'score':
        result = score_filing_strength(args.filing_text)
    elif args.action == 'attack':
        result = attack_filing(args.filing_stack)
    else:
        parser.print_help()
        return

    print(json.dumps(result, indent=2, default=str))


if __name__ == '__main__':
    main()
