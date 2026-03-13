"""
WAR ROOM DASHBOARD — LitigationOS
==================================
Real-time litigation status dashboard. Queries litigation_context.db
for separation days, deadlines, filing readiness, evidence strength,
damages estimates, and adversary threat models.

Usage:
    python war_room.py                    # Full dashboard
    python war_room.py --section deadlines  # Single section
    python war_room.py --json             # JSON output for automation
    python war_room.py --brief            # Compact summary

ScriptVault: dashboard/war_room.py | Version 1.0
"""
import sqlite3
import sys
import os
import json
from datetime import datetime, timedelta
from pathlib import Path

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

DB_PATH = Path(r"C:\Users\andre\LitigationOS\litigation_context.db")

PRAGMAS = """
PRAGMA busy_timeout = 180000;
PRAGMA journal_mode = WAL;
PRAGMA cache_size = -32000;
PRAGMA temp_store = MEMORY;
PRAGMA synchronous = NORMAL;
"""

def get_conn():
    conn = sqlite3.connect(str(DB_PATH), timeout=180)
    conn.row_factory = sqlite3.Row
    conn.executescript(PRAGMAS)
    return conn

def safe_query(conn, sql, params=(), default=None):
    try:
        return conn.execute(sql, params).fetchall()
    except Exception:
        return default if default is not None else []

def safe_scalar(conn, sql, params=(), default=0):
    try:
        row = conn.execute(sql, params).fetchone()
        return row[0] if row else default
    except Exception:
        return default

def render_separation(conn):
    days = safe_scalar(conn, "SELECT CAST(julianday('now') - julianday('2025-07-29') AS INTEGER)")
    weeks = days // 7
    months = days / 30.44
    print(f"""
{'='*65}
  SEPARATION CLOCK: {days} DAYS  ({weeks} weeks / {months:.1f} months)
  Last contact with L.D.W.: July 29, 2025
  Cause: Ex parte order - no hearing, no BIF analysis
{'='*65}""")

def render_deadlines(conn):
    print("\nACTIVE DEADLINES")
    print("-" * 65)
    rows = safe_query(conn, """
        SELECT deadline_id, title, due_date_iso, status, risk_if_missed
        FROM deadlines WHERE status != 'completed'
        ORDER BY due_date_iso ASC LIMIT 15
    """)
    today = datetime.now().strftime('%Y-%m-%d')
    for r in rows:
        try:
            dl_id = r['deadline_id']
            title = r['title']
            due = r['due_date_iso']
            status = r['status']
            risk = (r['risk_if_missed'] or '')[:40]
            flag = "OVERDUE" if (due and due < today) else "UPCOMING"
            print(f"  [{flag:>8s}] {dl_id}: {title}")
            print(f"             Due: {due} | Status: {status}")
            if risk:
                print(f"             Risk: {risk}")
        except Exception:
            pass
    print()

def render_filing_readiness(conn):
    print("\nFILING READINESS (Top 15)")
    print("-" * 65)
    rows = safe_query(conn, """
        SELECT vehicle_name, total_score, gaps
        FROM filing_readiness ORDER BY total_score DESC LIMIT 15
    """)
    for r in rows:
        vn = r['vehicle_name']
        ts = r['total_score']
        bar = "#" * (ts // 5) + "." * (20 - ts // 5)
        gaps = (r['gaps'] or "None")[:57]
        print(f"  [{ts:3d}/100] {bar} {vn}")
        if gaps != "None":
            print(f"           Gaps: {gaps}")
    print()

def render_evidence_arsenal(conn):
    print("\nEVIDENCE ARSENAL")
    print("-" * 65)
    total = safe_scalar(conn, "SELECT COUNT(*) FROM evidence_consolidated")
    strong = safe_scalar(conn, "SELECT COUNT(*) FROM evidence_consolidated WHERE best_strength LIKE '%STRONG%'")
    print(f"  Total consolidated: {total:,} | Strong grade: {strong:,}")
    rows = safe_query(conn, """
        SELECT adversary, SUM(hit_count) as total_hits, COUNT(*) as claim_count
        FROM evidence_by_adversary
        GROUP BY adversary ORDER BY total_hits DESC
    """)
    if rows:
        print("  BY ADVERSARY:")
        for r in rows:
            print(f"    {r['adversary']}: {r['total_hits']:,} hits across {r['claim_count']} claims")
    print()

def render_tort_matrix(conn):
    print("\nTORT MATRIX (Sufficient Evidence)")
    print("-" * 65)
    rows = safe_query(conn, """
        SELECT tort_type, adversary, total_hits, evidence_sufficient
        FROM tort_evidence_matrix WHERE evidence_sufficient = 'STRONG' OR evidence_sufficient = 'SUFFICIENT'
        ORDER BY total_hits DESC LIMIT 20
    """)
    if not rows:
        rows = safe_query(conn, """
            SELECT tort_type, adversary, total_hits, evidence_sufficient
            FROM tort_evidence_matrix WHERE total_hits >= 10
            ORDER BY total_hits DESC LIMIT 20
        """)
    for r in rows:
        status = r['evidence_sufficient'] or 'UNKNOWN'
        print(f"  [{status:>10s}] {r['tort_type']} vs {r['adversary']}: {r['total_hits']:,} hits")
    sufficient = safe_scalar(conn, "SELECT COUNT(*) FROM tort_evidence_matrix WHERE evidence_sufficient IN ('STRONG','SUFFICIENT')")
    total_torts = safe_scalar(conn, "SELECT COUNT(*) FROM tort_evidence_matrix")
    print(f"\n  Actionable: {sufficient} / {total_torts} total tort claims")
    print()

def render_damages(conn):
    print("\nDAMAGES ESTIMATES")
    print("-" * 65)
    rows = safe_query(conn, """
        SELECT damage_category, adversary, low_estimate, high_estimate, quantification_basis
        FROM damages_expanded ORDER BY high_estimate DESC
    """)
    total_min = total_max = 0
    for r in rows:
        mn = r['low_estimate'] or 0
        mx = r['high_estimate'] or 0
        total_min += mn
        total_max += mx
        basis = (r['quantification_basis'] or '')[:40]
        print(f"  {r['damage_category']} ({r['adversary']}): ${mn:,.0f} - ${mx:,.0f}")
        if basis:
            print(f"    Basis: {basis}")
    print(f"\n  TOTAL: ${total_min:,.0f} - ${total_max:,.0f}")
    print()

def render_judicial_violations(conn):
    print("\nJUDICIAL VIOLATIONS")
    print("-" * 65)
    total = safe_scalar(conn, "SELECT COUNT(*) FROM judicial_violations")
    rows = safe_query(conn, """
        SELECT severity, COUNT(*) as cnt FROM judicial_violations
        GROUP BY severity ORDER BY cnt DESC
    """)
    print(f"  Total: {total:,}")
    for r in rows:
        print(f"    {str(r['severity']).upper()}: {r['cnt']:,}")
    chains = safe_scalar(conn, "SELECT COUNT(*) FROM authority_chains WHERE chain_complete = 1")
    chains_total = safe_scalar(conn, "SELECT COUNT(*) FROM authority_chains")
    print(f"  Authority chains: {chains}/{chains_total} complete")
    print()

def render_victory_strategy(conn):
    print("\nVICTORY STRATEGY")
    print("-" * 65)
    rows = safe_query(conn, """
        SELECT id, action_to_undo, filing_vehicle, evidence_strength, confidence
        FROM victory_strategy ORDER BY id
    """)
    for r in rows:
        print(f"  #{r['id']:2d} [{r['confidence'] or 'N/A'}] {r['action_to_undo']}")
        print(f"       Vehicle: {r['filing_vehicle']} | Evidence: {r['evidence_strength'] or 'N/A'}")
    print()

def render_clerk_ready(conn):
    print("\nCLERK-READY FILINGS")
    print("-" * 65)
    clerk_dir = Path(r"C:\Users\andre\LitigationOS\01_FILINGS\CLERK_READY")
    if clerk_dir.exists():
        for f in sorted(clerk_dir.glob("*.md")):
            print(f"  [READY] {f.name} ({f.stat().st_size / 1024:.1f} KB)")
    print()

def render_db_health(conn):
    print("\nDATABASE HEALTH")
    print("-" * 65)
    tc = safe_scalar(conn, "SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
    sz = os.path.getsize(str(DB_PATH)) / (1024 * 1024)
    print(f"  Tables: {tc} | Size: {sz:,.1f} MB")
    for t in ['evidence_consolidated', 'actionable_evidence', 'harvest_texts',
              'judicial_violations', 'docket_events', 'claims', 'deadlines',
              'authority_chains', 'victory_strategy', 'filing_readiness',
              'ppo_rescission_evidence', 'watson_family_conspiracy', 'damages_expanded']:
        cnt = safe_scalar(conn, f"SELECT COUNT(*) FROM [{t}]", default='N/A')
        label = f"{cnt:,}" if isinstance(cnt, int) else str(cnt)
        print(f"    {t}: {label}")
    print()

def render_all():
    conn = get_conn()
    print("=" * 65)
    print("  WAR ROOM DASHBOARD — Pigors v. Watson")
    print(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 65)
    render_separation(conn)
    render_deadlines(conn)
    render_filing_readiness(conn)
    render_evidence_arsenal(conn)
    render_tort_matrix(conn)
    render_damages(conn)
    render_judicial_violations(conn)
    render_victory_strategy(conn)
    render_clerk_ready(conn)
    render_db_health(conn)
    print("=" * 65)
    print("  END OF WAR ROOM REPORT")
    print("=" * 65)
    conn.close()

def render_brief():
    conn = get_conn()
    days = safe_scalar(conn, "SELECT CAST(julianday('now') - julianday('2025-07-29') AS INTEGER)")
    dl = safe_scalar(conn, "SELECT COUNT(*) FROM deadlines WHERE status != 'completed'")
    ev = safe_scalar(conn, "SELECT COUNT(*) FROM evidence_consolidated")
    viol = safe_scalar(conn, "SELECT COUNT(*) FROM judicial_violations")
    torts = safe_scalar(conn, "SELECT COUNT(*) FROM tort_evidence_matrix WHERE evidence_sufficient IN ('STRONG','SUFFICIENT')")
    filings = safe_scalar(conn, "SELECT COUNT(*) FROM filing_readiness WHERE total_score >= 70")
    print(f"WAR ROOM BRIEF | {datetime.now().strftime('%Y-%m-%d')}")
    print(f"  Separation: {days} days | Deadlines: {dl} active")
    print(f"  Evidence: {ev:,} consolidated | Violations: {viol:,}")
    print(f"  Torts ready: {torts} | Filings ready: {filings}")
    conn.close()

def render_json():
    conn = get_conn()
    data = {
        'generated': datetime.now().isoformat(),
        'separation_days': safe_scalar(conn, "SELECT CAST(julianday('now') - julianday('2025-07-29') AS INTEGER)"),
        'deadlines_active': safe_scalar(conn, "SELECT COUNT(*) FROM deadlines WHERE status != 'completed'"),
        'evidence_consolidated': safe_scalar(conn, "SELECT COUNT(*) FROM evidence_consolidated"),
        'judicial_violations': safe_scalar(conn, "SELECT COUNT(*) FROM judicial_violations"),
        'torts_sufficient': safe_scalar(conn, "SELECT COUNT(*) FROM tort_evidence_matrix WHERE evidence_sufficient IN ('STRONG','SUFFICIENT')"),
        'filings_ready': safe_scalar(conn, "SELECT COUNT(*) FROM filing_readiness WHERE total_score >= 70"),
        'authority_chains_complete': safe_scalar(conn, "SELECT COUNT(*) FROM authority_chains WHERE chain_complete = 1"),
    }
    conn.close()
    print(json.dumps(data, indent=2))

if __name__ == '__main__':
    args = sys.argv[1:]
    if '--json' in args:
        render_json()
    elif '--brief' in args:
        render_brief()
    elif '--section' in args:
        idx = args.index('--section')
        section = args[idx + 1] if idx + 1 < len(args) else 'all'
        conn = get_conn()
        sections = {
            'separation': render_separation, 'deadlines': render_deadlines,
            'filings': render_filing_readiness, 'evidence': render_evidence_arsenal,
            'torts': render_tort_matrix, 'damages': render_damages,
            'violations': render_judicial_violations, 'strategy': render_victory_strategy,
            'clerk': render_clerk_ready, 'db': render_db_health,
        }
        fn = sections.get(section)
        if fn:
            fn(conn)
        else:
            print(f"Unknown section: {section}. Available: {', '.join(sections.keys())}")
        conn.close()
    else:
        render_all()
