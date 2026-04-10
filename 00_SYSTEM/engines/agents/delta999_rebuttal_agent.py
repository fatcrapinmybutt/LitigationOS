#!/usr/bin/env python3
"""
Delta999 Rebuttal Agent — Adversary rebuttal builder and impeachment specialist.

Builds counter-arguments to adversary claims, finds contradictions in
adversary statements, and assembles impeachment packages from the
contradiction_map, impeachment_matrix, and evidence_quotes tables.

CLI:
    python delta999_rebuttal_agent.py --action rebut --claim "father is unfit"
    python delta999_rebuttal_agent.py --action contradictions --person "Emily Watson"
    python delta999_rebuttal_agent.py --action impeachment --target "Emily Watson"
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
AGENT_NAME = 'delta999_rebuttal_agent'

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


# ── Rebuttal Agent class ────────────────────────────────────────────────────

class RebuttalAgent:
    """Adversary rebuttal specialist that builds counter-arguments,
    finds contradictions, and assembles impeachment packages.

    Queries contradiction_map for documented inconsistencies,
    impeachment_matrix for cross-examination ammunition, and
    evidence_quotes for supporting evidence to rebut adversary claims.
    """

    def build_rebuttal(self, claim: str) -> dict:
        """Build a rebuttal to an adversary's claim.

        Searches evidence_quotes for facts that contradict the claim,
        contradiction_map for documented inconsistencies, and
        authority_chains_v2 for legal authority supporting the rebuttal.
        """
        conn = get_conn()

        # 1. Search evidence that contradicts the claim
        counter_evidence, ev_method = _fts_search(
            conn, 'evidence_fts', 'evidence_quotes', 'quote_text',
            claim, limit=30
        )

        # 2. Search contradiction_map for relevant contradictions
        contradictions = []
        try:
            rows = conn.execute(
                "SELECT person, statement_1, statement_2, source_1, source_2, "
                "       date_1, date_2, severity "
                "FROM contradiction_map "
                "WHERE statement_1 LIKE ? OR statement_2 LIKE ? "
                "   OR person LIKE ? "
                "ORDER BY severity DESC LIMIT 20",
                (f'%{claim}%', f'%{claim}%', f'%{claim}%')
            ).fetchall()
            contradictions = [dict(r) for r in rows]
        except Exception:
            pass

        # 3. Search authority for legal basis of rebuttal
        authorities = []
        try:
            rows = conn.execute(
                "SELECT citation, authority_type, context, confidence "
                "FROM authority_chains_v2 "
                "WHERE context LIKE ? "
                "ORDER BY confidence DESC LIMIT 15",
                (f'%{claim}%',)
            ).fetchall()
            authorities = [dict(r) for r in rows]
        except Exception:
            pass

        # 4. Search rebuttal_matrix for pre-built rebuttals
        existing_rebuttals = []
        try:
            rows = conn.execute(
                "SELECT * FROM rebuttal_matrix "
                "WHERE adversary_claim LIKE ? OR rebuttal_text LIKE ? "
                "LIMIT 10",
                (f'%{claim}%', f'%{claim}%')
            ).fetchall()
            existing_rebuttals = [dict(r) for r in rows]
        except Exception:
            pass

        # 5. LLM synthesis
        try:
            synthesis = llm_ask(
                f"Build a rebuttal to the adversary claim: '{claim}'\n\n"
                f"Counter-evidence found: {len(counter_evidence)}\n"
                f"Contradictions found: {len(contradictions)}\n"
                f"Authorities found: {len(authorities)}\n"
                f"Existing rebuttals: {len(existing_rebuttals)}\n\n"
                f"Sample contradictions: {json.dumps(contradictions[:3], default=str)[:800]}\n"
                f"Sample authorities: {json.dumps(authorities[:3], default=str)[:500]}\n\n"
                f"Build a structured rebuttal with: (1) factual counter-argument, "
                f"(2) contradictions that undermine the claim, (3) legal authority.",
                system_prompt=(
                    "You are a Michigan litigation rebuttal specialist. Rules:\n"
                    "1. Structure: Fact → Contradiction → Authority → Conclusion\n"
                    "2. Cite evidence with source references for each factual assertion\n"
                    "3. Use 'L.D.W.' for the minor child — never spell out the full name\n"
                    "4. Only cite authorities present in the context — mark others UNVERIFIED\n"
                    "5. Highlight the strongest contradictions that destroy credibility"
                )
            )
        except Exception as e:
            synthesis = f"LLM unavailable: {e}"

        conn.close()

        result = {
            'adversary_claim': claim,
            'counter_evidence_found': len(counter_evidence),
            'contradictions_found': len(contradictions),
            'authorities_found': len(authorities),
            'existing_rebuttals': len(existing_rebuttals),
            'rebuttal': synthesis,
            'evidence_method': ev_method,
        }
        log_activity(f'build_rebuttal:{claim[:60]}', json.dumps(result, default=str)[:2000])
        return result

    def find_contradictions(self, person: str) -> dict:
        """Find all documented contradictions for a specific person.

        Queries contradiction_map for prior inconsistent statements,
        timeline_events for date-based inconsistencies, and evidence_quotes
        for statements that conflict with each other.
        """
        conn = get_conn()

        # 1. Direct contradiction_map entries
        contradictions = []
        try:
            rows = conn.execute(
                "SELECT person, statement_1, statement_2, source_1, source_2, "
                "       date_1, date_2, severity "
                "FROM contradiction_map "
                "WHERE person LIKE ? "
                "ORDER BY severity DESC",
                (f'%{person}%',)
            ).fetchall()
            contradictions = [dict(r) for r in rows]
        except Exception:
            pass

        # 2. Timeline events for this person showing inconsistency
        timeline_entries = []
        try:
            rows = conn.execute(
                "SELECT event_date, event_type, description, source "
                "FROM timeline_events "
                "WHERE description LIKE ? "
                "ORDER BY event_date ASC LIMIT 40",
                (f'%{person}%',)
            ).fetchall()
            timeline_entries = [dict(r) for r in rows]
        except Exception:
            pass

        # 3. Evidence quotes from/about this person
        person_evidence, ev_method = _fts_search(
            conn, 'evidence_fts', 'evidence_quotes', 'quote_text',
            person, limit=30
        )

        # 4. Impeachment entries for this person
        impeachment = []
        try:
            rows = conn.execute(
                "SELECT target, contradiction_type, statement_a, statement_b, "
                "       source_a, source_b, mre_rule, severity "
                "FROM impeachment_matrix "
                "WHERE target LIKE ? "
                "ORDER BY severity DESC",
                (f'%{person}%',)
            ).fetchall()
            impeachment = [dict(r) for r in rows]
        except Exception:
            pass

        conn.close()

        result = {
            'person': person,
            'contradictions_found': len(contradictions),
            'timeline_entries': len(timeline_entries),
            'evidence_quotes': len(person_evidence),
            'impeachment_entries': len(impeachment),
            'contradictions': contradictions[:30],
            'impeachment_preview': impeachment[:10],
        }
        log_activity(f'find_contradictions:{person[:40]}', json.dumps(result, default=str)[:2000])
        return result

    def get_impeachment_ammo(self, target: str) -> dict:
        """Assemble a complete impeachment package for cross-examination.

        Queries impeachment_matrix for prior inconsistent statements with
        MRE rule references, contradiction_map for factual contradictions,
        and evidence_quotes for documentary proof supporting impeachment.
        """
        conn = get_conn()

        # 1. Impeachment matrix entries
        impeachment = []
        try:
            rows = conn.execute(
                "SELECT target, contradiction_type, statement_a, statement_b, "
                "       source_a, source_b, mre_rule, severity "
                "FROM impeachment_matrix "
                "WHERE target LIKE ? "
                "ORDER BY severity DESC",
                (f'%{target}%',)
            ).fetchall()
            impeachment = [dict(r) for r in rows]
        except Exception:
            pass

        # 2. Contradictions for this target
        contradictions = []
        try:
            rows = conn.execute(
                "SELECT person, statement_1, statement_2, source_1, source_2, "
                "       date_1, date_2, severity "
                "FROM contradiction_map "
                "WHERE person LIKE ? "
                "ORDER BY severity DESC LIMIT 30",
                (f'%{target}%',)
            ).fetchall()
            contradictions = [dict(r) for r in rows]
        except Exception:
            pass

        # 3. Evidence supporting impeachment (sworn statements, police reports)
        supporting_evidence, ev_method = _fts_search(
            conn, 'evidence_fts', 'evidence_quotes', 'quote_text',
            f'{target} OR sworn OR statement OR recant OR testified',
            limit=25
        )

        # 4. Police reports mentioning this target
        police_reports = []
        try:
            rows = conn.execute(
                "SELECT incident_number, date, narrative, officer "
                "FROM police_reports "
                "WHERE narrative LIKE ? LIMIT 15",
                (f'%{target}%',)
            ).fetchall()
            police_reports = [dict(r) for r in rows]
        except Exception:
            pass

        # 5. LLM cross-examination synthesis
        try:
            synthesis = llm_ask(
                f"Build a cross-examination impeachment package for: '{target}'\n\n"
                f"Impeachment entries: {len(impeachment)}\n"
                f"Contradictions: {len(contradictions)}\n"
                f"Supporting evidence: {len(supporting_evidence)}\n"
                f"Police reports: {len(police_reports)}\n\n"
                f"Sample impeachment: {json.dumps(impeachment[:3], default=str)[:800]}\n"
                f"Sample contradictions: {json.dumps(contradictions[:3], default=str)[:600]}\n\n"
                f"Create a cross-examination outline with: "
                f"(1) setup questions that lock in testimony, "
                f"(2) impeachment questions that expose contradictions, "
                f"(3) MRE rule for each impeachment line.",
                system_prompt=(
                    "You are a Michigan cross-examination specialist. Rules:\n"
                    "1. Use leading questions only (answerable yes/no)\n"
                    "2. Cite MRE 613 for prior inconsistent statements\n"
                    "3. Cite MRE 608/609 for character/conviction impeachment\n"
                    "4. Use 'L.D.W.' for the minor child — never spell out the full name\n"
                    "5. Only reference evidence and statements present in the context\n"
                    "6. Build from general (lock) → specific (impeach) → conclude (destroy)"
                )
            )
        except Exception as e:
            synthesis = f"LLM unavailable: {e}"

        conn.close()

        # Categorize impeachment by type
        by_type = {}
        for entry in impeachment:
            ctype = entry.get('contradiction_type', 'unknown')
            by_type.setdefault(ctype, []).append(entry)

        result = {
            'target': target,
            'impeachment_entries': len(impeachment),
            'contradictions': len(contradictions),
            'supporting_evidence': len(supporting_evidence),
            'police_reports': len(police_reports),
            'by_type': {k: len(v) for k, v in by_type.items()},
            'cross_examination_outline': synthesis,
            'evidence_method': ev_method,
        }
        log_activity(f'impeachment:{target[:40]}', json.dumps(result, default=str)[:2000])
        return result


# ── Module-level convenience functions ───────────────────────────────────────

_agent = RebuttalAgent()

def build_rebuttal(claim: str) -> dict:
    return _agent.build_rebuttal(claim)

def find_contradictions(person: str) -> dict:
    return _agent.find_contradictions(person)

def get_impeachment_ammo(target: str) -> dict:
    return _agent.get_impeachment_ammo(target)


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Delta999 Rebuttal Agent — Adversary Rebuttal Builder')
    parser.add_argument('--action', required=True,
                        choices=['rebut', 'contradictions', 'impeachment'],
                        help='Action to perform')
    parser.add_argument('--claim', type=str, help='Adversary claim to rebut')
    parser.add_argument('--person', type=str, help='Person to find contradictions for')
    parser.add_argument('--target', type=str, help='Impeachment target')
    args = parser.parse_args()

    if args.action == 'rebut':
        if not args.claim:
            parser.error('--claim required for rebut')
        result = build_rebuttal(args.claim)
    elif args.action == 'contradictions':
        if not args.person:
            parser.error('--person required for contradictions')
        result = find_contradictions(args.person)
    elif args.action == 'impeachment':
        if not args.target:
            parser.error('--target required for impeachment')
        result = get_impeachment_ammo(args.target)
    else:
        parser.print_help()
        return

    print(json.dumps(result, indent=2, default=str))


if __name__ == '__main__':
    main()
