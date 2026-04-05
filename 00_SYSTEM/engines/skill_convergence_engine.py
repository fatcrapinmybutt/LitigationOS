#!/usr/bin/env python3
"""
skill_convergence_engine.py — Convergence Engine Skill
Wired to: convergence_status (8), convergence_filing_stacks (51), convergence_evidence_map (27), convergence_cycles (116)
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

# ── Core Functions ──────────────────────────────────────────────────

def get_status():
    """Get convergence status for all 8 filing stacks."""
    conn = _conn()
    rows = conn.execute("SELECT * FROM convergence_status ORDER BY stack_name").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_stack(stack_name):
    """Get all files in a specific filing stack."""
    conn = _conn()
    files = conn.execute(
        "SELECT * FROM convergence_filing_stacks WHERE stack_name LIKE ? ORDER BY id",
        (f'%{stack_name}%',)
    ).fetchall()
    status = conn.execute(
        "SELECT * FROM convergence_status WHERE stack_name LIKE ?",
        (f'%{stack_name}%',)
    ).fetchone()
    evidence = conn.execute(
        "SELECT * FROM convergence_evidence_map WHERE stack_name LIKE ?",
        (f'%{stack_name}%',)
    ).fetchall()
    conn.close()
    return {
        'files': [dict(r) for r in files],
        'status': dict(status) if status else None,
        'evidence_map': [dict(r) for r in evidence]
    }


def get_all_stacks():
    """Get complete overview of all convergence filing stacks."""
    conn = _conn()
    stacks = conn.execute(
        "SELECT stack_name, COUNT(*) as file_count, GROUP_CONCAT(file_name, '; ') as files "
        "FROM convergence_filing_stacks GROUP BY stack_name"
    ).fetchall()
    statuses = conn.execute("SELECT * FROM convergence_status").fetchall()
    conn.close()
    status_map = {dict(s)['stack_name']: dict(s) for s in statuses}
    result = []
    for s in stacks:
        d = dict(s)
        d['status_info'] = status_map.get(d['stack_name'])
        result.append(d)
    return result


def get_convergence_cycles(limit=20):
    """Get recent convergence cycles."""
    conn = _conn()
    rows = conn.execute(
        "SELECT * FROM convergence_cycles ORDER BY rowid DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_evidence_map():
    """Get the full convergence evidence map."""
    conn = _conn()
    rows = conn.execute("SELECT * FROM convergence_evidence_map").fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Main ────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print("=" * 70)
    print("CONVERGENCE ENGINE SKILL — DB-WIRED")
    print("=" * 70)

    statuses = get_status()
    print(f"\n[STATUS] {len(statuses)} filing stacks:")
    for s in statuses:
        print(f"  • {s['stack_name']}: {s['status']} — {s['file_count']} files — {s['court_action']}")

    all_stacks = get_all_stacks()
    print(f"\n[STACKS] {len(all_stacks)} stacks with files:")
    for s in all_stacks:
        print(f"  • {s['stack_name']}: {s['file_count']} files")

    ev_map = get_evidence_map()
    print(f"\n[EVIDENCE MAP] {len(ev_map)} evidence mappings")

    cycles = get_convergence_cycles(5)
    print(f"\n[CYCLES] Last {len(cycles)} convergence cycles")

    print("\n✅ Convergence Engine Skill operational")
