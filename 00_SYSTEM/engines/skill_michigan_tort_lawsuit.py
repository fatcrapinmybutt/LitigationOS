#!/usr/bin/env python3
"""
skill_michigan_tort_lawsuit.py — Michigan Tort Lawsuit Skill
Wired to: extracted_harms (26K), adversary_harm_summary (17), convergence_filing_stacks (51), tort_claims (10)
"""
import sys, os, sqlite3, json
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

DB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'litigation_context.db')

def _conn():
    c = sqlite3.connect(DB, timeout=120)
    c.execute('PRAGMA busy_timeout=60000')
    c.execute('PRAGMA journal_mode=WAL')
    c.row_factory = sqlite3.Row
    return c

# ── Core Functions ──────────────────────────────────────────────────

def get_tort_claims(adversary=None):
    """Get tort claims from extracted_harms + tort_claims, optionally filtered by adversary."""
    conn = _conn()
    results = {}
    if adversary:
        rows = conn.execute(
            "SELECT category, subcategory, description, date_ref, severity, constitutional_violation, mcr_violation, filing_stacks "
            "FROM extracted_harms WHERE adversary LIKE ? ORDER BY severity DESC",
            (f'%{adversary}%',)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT category, subcategory, description, date_ref, severity, constitutional_violation, mcr_violation, filing_stacks "
            "FROM extracted_harms ORDER BY severity DESC LIMIT 500"
        ).fetchall()
    results['extracted_harms'] = [dict(r) for r in rows]

    tort_rows = conn.execute(
        "SELECT tort_type, defendant, elements_met, evidence_refs, strength_score, chess_defense, chess_rebuttal, status "
        "FROM tort_claims"
    ).fetchall()
    results['tort_claims'] = [dict(r) for r in tort_rows]
    conn.close()
    return results


def calculate_damages(adversary):
    """Calculate damages summary for a specific adversary from adversary_harm_summary + damages tables."""
    conn = _conn()
    summary = conn.execute(
        "SELECT * FROM adversary_harm_summary WHERE adversary LIKE ?",
        (f'%{adversary}%',)
    ).fetchone()

    damages = conn.execute(
        "SELECT * FROM damages_calculations"
    ).fetchall()

    financial = conn.execute(
        "SELECT * FROM financial_damages_comprehensive WHERE description LIKE ? OR description LIKE ?",
        (f'%{adversary}%', f'%tort%')
    ).fetchall()

    conn.close()
    return {
        'adversary_summary': dict(summary) if summary else None,
        'damages_calculations': [dict(r) for r in damages],
        'financial_damages': [dict(r) for r in financial]
    }


def get_evidence_for_count(count_name):
    """Get evidence supporting a specific tort count (e.g., 'IIED', 'fraud', 'negligence')."""
    conn = _conn()
    harms = conn.execute(
        "SELECT * FROM extracted_harms WHERE category LIKE ? OR subcategory LIKE ? OR description LIKE ? ORDER BY severity DESC LIMIT 100",
        (f'%{count_name}%', f'%{count_name}%', f'%{count_name}%')
    ).fetchall()

    quotes = conn.execute(
        "SELECT * FROM evidence_quotes WHERE evidence_category LIKE ? OR quote_text LIKE ? OR legal_significance LIKE ? LIMIT 100",
        (f'%{count_name}%', f'%{count_name}%', f'%{count_name}%')
    ).fetchall()

    conn.close()
    return {
        'harms': [dict(r) for r in harms],
        'evidence_quotes': [dict(r) for r in quotes]
    }


def get_watson_tort_stack():
    """Get Watson tort filing stack from convergence_filing_stacks."""
    conn = _conn()
    rows = conn.execute(
        "SELECT * FROM convergence_filing_stacks WHERE stack_name LIKE '%WATSON%' OR stack_name LIKE '%TORT%'"
    ).fetchall()
    status = conn.execute(
        "SELECT * FROM convergence_status WHERE stack_name LIKE '%WATSON%' OR stack_name LIKE '%TORT%'"
    ).fetchall()
    conn.close()
    return {
        'files': [dict(r) for r in rows],
        'status': [dict(r) for r in status]
    }


def get_all_adversaries():
    """Get all adversaries with their harm summaries."""
    conn = _conn()
    rows = conn.execute("SELECT * FROM adversary_harm_summary ORDER BY harm_count DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Main ────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print("=" * 70)
    print("MICHIGAN TORT LAWSUIT SKILL — DB-WIRED")
    print("=" * 70)

    advs = get_all_adversaries()
    print(f"\n[ADVERSARIES] {len(advs)} adversaries in harm summary:")
    for a in advs:
        print(f"  • {a['adversary']}: {a['harm_count']} harms, {a['total_mentions']} mentions")

    watson_stack = get_watson_tort_stack()
    print(f"\n[WATSON TORT STACK] {len(watson_stack['files'])} files")
    for f in watson_stack['files']:
        print(f"  • {f['file_name']} — {f['doc_type']}")

    claims = get_tort_claims('Watson')
    print(f"\n[WATSON TORT CLAIMS] {len(claims['extracted_harms'])} harms, {len(claims['tort_claims'])} formal claims")

    for tc in claims['tort_claims']:
        print(f"  • {tc['tort_type']} vs {tc['defendant']} — strength {tc['strength_score']}")

    print("\n✅ Michigan Tort Lawsuit Skill operational")
