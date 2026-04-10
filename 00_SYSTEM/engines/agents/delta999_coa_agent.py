#!/usr/bin/env python3
"""
Delta999 COA Agent — Court of Appeals specialist for docket COA 366810.

Builds appellate brief components: issues presented, statement of facts,
and authority compilation for MCR 7.212 compliance. Queries Lane F evidence,
authority chains, and timeline events for the appeal of right.

CLI:
    python delta999_coa_agent.py --action issues
    python delta999_coa_agent.py --action facts
    python delta999_coa_agent.py --action authorities
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
AGENT_NAME = 'delta999_coa_agent'
COA_DOCKET = '366810'
CASE_NUMBER = '2024-001507-DC'

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


# ── COA Agent class ──────────────────────────────────────────────────────────

class COAAgent:
    """Court of Appeals specialist for docket COA 366810.

    Builds MCR 7.212-compliant appellate brief components by querying
    the litigation database for Lane F evidence, authority chains, and
    timeline events relevant to the appeal of right.
    """

    def __init__(self):
        self.docket = COA_DOCKET
        self.case_number = CASE_NUMBER

    def build_issues_presented(self) -> dict:
        """Build the Issues Presented section per MCR 7.212(C)(5).

        Queries evidence_quotes for Lane F appellate issues, timeline_events
        for procedural errors, and judicial_violations for misconduct patterns
        that form the basis of the appeal.
        """
        conn = get_conn()

        # 1. Gather appellate-lane evidence
        appellate_evidence, ev_method = _fts_search(
            conn, 'evidence_fts', 'evidence_quotes', 'quote_text',
            'appeal OR appellate OR COA OR "366810" OR "court of appeals"', limit=30
        )

        # 2. Gather judicial violations as potential appellate issues
        judicial_issues = []
        try:
            rows = conn.execute(
                "SELECT violation_type, description, severity, mcr_citation, date_observed "
                "FROM judicial_violations "
                "WHERE severity IN ('critical', 'high', 'CRITICAL', 'HIGH') "
                "ORDER BY date_observed DESC LIMIT 30"
            ).fetchall()
            judicial_issues = [dict(r) for r in rows]
        except Exception:
            pass

        # 3. Timeline events showing procedural errors
        procedural_errors = []
        try:
            rows = conn.execute(
                "SELECT event_date, event_type, description, source "
                "FROM timeline_events "
                "WHERE description LIKE '%ex parte%' "
                "   OR description LIKE '%due process%' "
                "   OR description LIKE '%denied%' "
                "   OR description LIKE '%suspended%' "
                "ORDER BY event_date DESC LIMIT 25"
            ).fetchall()
            procedural_errors = [dict(r) for r in rows]
        except Exception:
            pass

        # 4. Synthesize issues via LLM
        context = {
            'appellate_evidence_count': len(appellate_evidence),
            'judicial_issues_count': len(judicial_issues),
            'procedural_errors_count': len(procedural_errors),
            'sample_violations': [str(v)[:200] for v in judicial_issues[:5]],
            'sample_errors': [str(e)[:200] for e in procedural_errors[:5]],
        }
        try:
            synthesis = llm_ask(
                f"Build the 'Issues Presented' section for COA docket {self.docket}.\n"
                f"Appeal from 14th Circuit Case No. {self.case_number}.\n"
                f"Context: {json.dumps(context, default=str)[:1500]}\n\n"
                f"Format each issue as a yes/no question per MCR 7.212(C)(5).\n"
                f"Include the trial court's answer and the appellant's answer.",
                system_prompt=(
                    "You are a Michigan appellate brief drafter. Rules:\n"
                    "1. Each issue must be a concise yes/no question under MCR 7.212(C)(5)\n"
                    "2. Cite specific MCR/MCL for each issue\n"
                    "3. Use 'L.D.W.' for the minor child — never spell out the full name\n"
                    "4. Focus on preserved errors and constitutional violations\n"
                    "5. Only cite authorities present in the context — mark others UNVERIFIED"
                )
            )
        except Exception as e:
            synthesis = f"LLM unavailable: {e}"

        conn.close()

        result = {
            'docket': self.docket,
            'case_number': self.case_number,
            'appellate_evidence_found': len(appellate_evidence),
            'judicial_violations_found': len(judicial_issues),
            'procedural_errors_found': len(procedural_errors),
            'issues_presented': synthesis,
            'evidence_method': ev_method,
        }
        log_activity('build_issues_presented', json.dumps(result, default=str)[:2000])
        return result

    def gather_statement_of_facts(self) -> dict:
        """Gather the Statement of Facts per MCR 7.212(C)(6).

        Queries timeline_events for chronological case history and
        evidence_quotes for supporting factual assertions with page references.
        """
        conn = get_conn()

        # 1. Full timeline of key events
        timeline = []
        try:
            rows = conn.execute(
                "SELECT event_date, event_type, description, source "
                "FROM timeline_events "
                "WHERE event_date IS NOT NULL AND event_date != '' "
                "ORDER BY event_date ASC LIMIT 100"
            ).fetchall()
            timeline = [dict(r) for r in rows]
        except Exception:
            pass

        # 2. Key evidence quotes with source references
        key_quotes, q_method = _fts_search(
            conn, 'evidence_fts', 'evidence_quotes', 'quote_text',
            'custody OR parenting OR "ex parte" OR order OR suspended OR withholding',
            limit=40
        )

        # 3. Court orders and rulings
        orders = []
        try:
            rows = conn.execute(
                "SELECT event_date, description, source "
                "FROM timeline_events "
                "WHERE event_type LIKE '%order%' OR event_type LIKE '%ruling%' "
                "   OR description LIKE '%order%' OR description LIKE '%judgment%' "
                "ORDER BY event_date ASC LIMIT 30"
            ).fetchall()
            orders = [dict(r) for r in rows]
        except Exception:
            pass

        # 4. Synthesize statement of facts
        try:
            synthesis = llm_ask(
                f"Build a Statement of Facts for COA docket {self.docket}.\n"
                f"Timeline events: {len(timeline)} (earliest to latest)\n"
                f"Key evidence quotes: {len(key_quotes)}\n"
                f"Court orders: {len(orders)}\n"
                f"Sample timeline: {json.dumps(timeline[:10], default=str)[:1200]}\n"
                f"Sample orders: {json.dumps(orders[:5], default=str)[:600]}\n\n"
                f"Produce a chronological narrative citing record references.",
                system_prompt=(
                    "You are a Michigan appellate brief drafter. Rules:\n"
                    "1. Present facts chronologically per MCR 7.212(C)(6)\n"
                    "2. Cite lower court record for every factual assertion\n"
                    "3. Use 'L.D.W.' for the minor child — never spell out the full name\n"
                    "4. State facts neutrally but emphasize preserved errors\n"
                    "5. Only reference evidence and dates present in the provided context"
                )
            )
        except Exception as e:
            synthesis = f"LLM unavailable: {e}"

        conn.close()

        result = {
            'docket': self.docket,
            'timeline_events': len(timeline),
            'key_evidence_quotes': len(key_quotes),
            'court_orders': len(orders),
            'statement_of_facts': synthesis,
        }
        log_activity('gather_statement_of_facts', json.dumps(result, default=str)[:2000])
        return result

    def compile_authorities(self) -> dict:
        """Compile authority chain for the appellate brief per MCR 7.212(C)(7).

        Queries authority_chains_v2 for relevant case law and statutes,
        michigan_rules_extracted for MCR/MCL text, and master_citations
        for pin cites supporting appellate arguments.
        """
        conn = get_conn()

        # 1. Authority chains relevant to appeal
        authority_chains = []
        appellate_terms = [
            'appeal', 'MCR 7.212', 'MCR 7.204', 'MCR 7.205',
            'due process', 'custody', 'best interest', 'MCL 722.23',
            'ex parte', 'disqualification', 'MCR 2.003',
        ]
        for term in appellate_terms:
            try:
                rows = conn.execute(
                    "SELECT citation, authority_type, context, confidence "
                    "FROM authority_chains_v2 "
                    "WHERE citation LIKE ? OR context LIKE ? "
                    "LIMIT 10",
                    (f'%{term}%', f'%{term}%')
                ).fetchall()
                for r in rows:
                    entry = dict(r)
                    entry['search_term'] = term
                    authority_chains.append(entry)
            except Exception:
                pass

        # 2. Michigan court rules full text for key rules
        key_rules = []
        rule_cites = ['MCR 7.212', 'MCR 7.204', 'MCR 7.205', 'MCR 2.003',
                       'MCL 722.23', 'MCL 722.27', 'MCR 2.119']
        for cite in rule_cites:
            try:
                rows = conn.execute(
                    "SELECT rule_number, rule_title, full_text "
                    "FROM michigan_rules_extracted "
                    "WHERE rule_number LIKE ? LIMIT 3",
                    (f'%{cite}%',)
                ).fetchall()
                key_rules.extend([dict(r) for r in rows])
            except Exception:
                pass

        # 3. Master citations for supporting case law
        case_law = []
        try:
            rows = conn.execute(
                "SELECT citation, source_context, citation_type "
                "FROM master_citations "
                "WHERE citation_type LIKE '%case%' "
                "  AND (source_context LIKE '%custody%' "
                "       OR source_context LIKE '%appeal%' "
                "       OR source_context LIKE '%due process%') "
                "LIMIT 30"
            ).fetchall()
            case_law = [dict(r) for r in rows]
        except Exception:
            pass

        conn.close()

        # Deduplicate authority chains by citation
        seen_citations = set()
        deduped_authorities = []
        for a in authority_chains:
            cit = a.get('citation', '')
            if cit and cit not in seen_citations:
                seen_citations.add(cit)
                deduped_authorities.append(a)

        result = {
            'docket': self.docket,
            'authority_chains_found': len(deduped_authorities),
            'key_rules_found': len(key_rules),
            'case_law_found': len(case_law),
            'authorities': deduped_authorities[:50],
            'rules': key_rules,
            'case_law_sample': case_law[:20],
        }
        log_activity('compile_authorities', json.dumps(result, default=str)[:2000])
        return result


# ── Module-level convenience functions ───────────────────────────────────────

_agent = COAAgent()

def build_issues_presented():
    return _agent.build_issues_presented()

def gather_statement_of_facts():
    return _agent.gather_statement_of_facts()

def compile_authorities():
    return _agent.compile_authorities()


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Delta999 COA Agent — COA 366810 Specialist')
    parser.add_argument('--action', required=True,
                        choices=['issues', 'facts', 'authorities'],
                        help='Action to perform')
    args = parser.parse_args()

    if args.action == 'issues':
        result = build_issues_presented()
    elif args.action == 'facts':
        result = gather_statement_of_facts()
    elif args.action == 'authorities':
        result = compile_authorities()
    else:
        parser.print_help()
        return

    print(json.dumps(result, indent=2, default=str))


if __name__ == '__main__':
    main()
