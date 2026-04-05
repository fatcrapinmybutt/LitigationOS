#!/usr/bin/env python3
"""
skill_landlord_tenant.py — Landlord/Tenant Claims Skill
Wired to: shadyoaks_claim_table (49), housing_violations (200), extracted_harms (Shady Oaks/Homes)
"""
import sys, os, sqlite3, json
from datetime import datetime

try:
    sys.stdout.reconfigure(encoding='utf-8')
except (AttributeError, OSError):
    pass
DB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'litigation_context.db')

def _conn():
    c = sqlite3.connect(DB, timeout=120)
    c.execute('PRAGMA busy_timeout=60000')
    c.execute('PRAGMA journal_mode=WAL')
    c.execute('PRAGMA cache_size=-32000')
    c.row_factory = sqlite3.Row
    return c

# ── Core Functions──────────────────────────────────────────────────

def get_all_claims():
    """Get all 49 Shady Oaks claims from shadyoaks_claim_table."""
    conn = _conn()
    rows = conn.execute("SELECT * FROM shadyoaks_claim_table ORDER BY cl_id").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_violations_by_type(violation_type=None):
    """Get housing violations, optionally filtered by type/code."""
    conn = _conn()
    if violation_type:
        rows = conn.execute(
            "SELECT * FROM housing_violations WHERE code_section LIKE ? OR description LIKE ? ORDER BY date_reported",
            (f'%{violation_type}%', f'%{violation_type}%')
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM housing_violations ORDER BY date_reported").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_damages_estimate():
    """Calculate damages estimate from extracted_harms for Shady Oaks / Homes of America."""
    conn = _conn()
    shady = conn.execute(
        "SELECT adversary, COUNT(*) as harm_count, GROUP_CONCAT(DISTINCT category) as categories "
        "FROM extracted_harms WHERE adversary LIKE '%shady%' OR adversary LIKE '%homes%' OR adversary LIKE '%Housing%' "
        "GROUP BY adversary"
    ).fetchall()

    summary = conn.execute(
        "SELECT * FROM adversary_harm_summary WHERE adversary LIKE '%Shady%' OR adversary LIKE '%Homes%' OR adversary LIKE '%Housing%'"
    ).fetchall()

    financial = conn.execute(
        "SELECT * FROM financial_damages_comprehensive WHERE description LIKE '%hous%' OR description LIKE '%rent%' OR description LIKE '%shady%'"
    ).fetchall()

    conn.close()
    return {
        'harm_by_adversary': [dict(r) for r in shady],
        'adversary_summaries': [dict(r) for r in summary],
        'financial_damages': [dict(r) for r in financial]
    }


def get_housing_evidence():
    """Get all housing-related evidence from extracted_harms."""
    conn = _conn()
    rows = conn.execute(
        "SELECT * FROM extracted_harms "
        "WHERE adversary LIKE '%shady%' OR adversary LIKE '%homes%' OR adversary LIKE '%Housing%' "
        "ORDER BY severity DESC LIMIT 200"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_filing_stack():
    """Get Shady Oaks filing stack from convergence tables."""
    conn = _conn()
    files = conn.execute(
        "SELECT * FROM convergence_filing_stacks WHERE stack_name LIKE '%SHADY%'"
    ).fetchall()
    status = conn.execute(
        "SELECT * FROM convergence_status WHERE stack_name LIKE '%SHADY%'"
    ).fetchall()
    conn.close()
    return {
        'files': [dict(r) for r in files],
        'status': [dict(r) for r in status]
    }


# ── Main ────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print("=" * 70)
    print("LANDLORD/TENANT CLAIMS SKILL — DB-WIRED")
    print("=" * 70)

    claims = get_all_claims()
    print(f"\n[CLAIMS] {len(claims)} Shady Oaks claims")
    for c in claims[:5]:
        print(f"  • {c['cl_id']}: {c['claim_type']} — {str(c['claim_text'])[:80]}...")

    violations = get_violations_by_type()
    print(f"\n[VIOLATIONS] {len(violations)} housing violations")
    code_counts = {}
    for v in violations:
        cs = v.get('code_section', 'Unknown')
        code_counts[cs] = code_counts.get(cs, 0) + 1
    for code, cnt in sorted(code_counts.items(), key=lambda x: -x[1])[:10]:
        print(f"  • {code}: {cnt} violations")

    damages = get_damages_estimate()
    print(f"\n[DAMAGES] Harm by adversary:")
    for h in damages['harm_by_adversary']:
        print(f"  • {h['adversary']}: {h['harm_count']} harms — categories: {str(h['categories'])[:80]}")

    stack = get_filing_stack()
    print(f"\n[FILING STACK] {len(stack['files'])} files in Shady Oaks stack")

    print("\n✅ Landlord/Tenant Skill operational")
