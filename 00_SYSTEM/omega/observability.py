#!/usr/bin/env python3
"""
LitigationOS Phase 10 CONVERGE — Full Observability Dashboard
System, revenue, case, and alert dashboards in a single pane of glass.
"""

import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import os
import json
import sqlite3
import shutil
import platform
from datetime import datetime, timedelta
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────
BASE_DIR = Path(r"C:\Users\andre\LitigationOS")
SYSTEM_DIR = BASE_DIR / "00_SYSTEM"
DB_PATH = Path(r"C:\Users\andre\litigation_context.db")
OMEGA_DIR = SYSTEM_DIR / "omega"
APPS_DIR = SYSTEM_DIR / "apps"

# ── Database Helper ────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def ensure_alert_tables(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS omega_alerts (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            alert_type  TEXT NOT NULL,
            severity    TEXT DEFAULT 'MEDIUM',
            threshold   TEXT,
            enabled     INTEGER DEFAULT 1,
            last_fired  TEXT,
            detail      TEXT,
            created_at  TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS omega_alert_history (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            alert_type  TEXT NOT NULL,
            severity    TEXT,
            message     TEXT,
            fired_at    TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.commit()


# ── Utility ────────────────────────────────────────────────────────────
def safe_query(conn, sql, default=None):
    """Execute a query, returning default on error."""
    try:
        return conn.execute(sql).fetchall()
    except Exception:
        return default if default is not None else []


def table_exists(conn, name):
    row = conn.execute(
        "SELECT COUNT(*) as c FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone()
    return row["c"] > 0


def table_row_count(conn, name):
    if not table_exists(conn, name):
        return None
    row = conn.execute(f'SELECT COUNT(*) as c FROM "{name}"').fetchone()
    return row["c"]


# ══════════════════════════════════════════════════════════════════════
#  1. SYSTEM DASHBOARD
# ══════════════════════════════════════════════════════════════════════
def system_dashboard(conn):
    print("\n┌─────────────────────────────────────────────────────────┐")
    print("│           📡  SYSTEM DASHBOARD                         │")
    print("└─────────────────────────────────────────────────────────┘")

    # Pipeline status
    pipeline_dir = SYSTEM_DIR / "pipeline"
    pipeline_scripts = sorted(pipeline_dir.glob("*.py")) if pipeline_dir.exists() else []
    print(f"\n  Pipeline scripts:   {len(pipeline_scripts)}")

    # DB size & growth
    db_size_mb = DB_PATH.stat().st_size / (1024 * 1024) if DB_PATH.exists() else 0
    print(f"  Database size:      {db_size_mb:,.1f} MB")

    # Table counts for key tables
    key_tables = [
        "omega_evolution_config", "omega_evolution_log", "omega_anomaly_log",
        "omega_alerts", "omega_revenue_projections", "omega_scores",
        "omega_documents", "omega_filings", "omega_agents",
    ]
    print("  Key tables:")
    for t in key_tables:
        count = table_row_count(conn, t)
        status = f"{count:,} rows" if count is not None else "—"
        print(f"    {t:<36} {status}")

    # Total tables
    all_tables = conn.execute(
        "SELECT COUNT(*) as c FROM sqlite_master WHERE type='table'"
    ).fetchone()
    print(f"  Total tables:       {all_tables['c']}")

    # Disk space
    total, used, free = shutil.disk_usage(str(BASE_DIR))
    print(f"\n  Disk total:         {total / (1024**3):,.1f} GB")
    print(f"  Disk used:          {used / (1024**3):,.1f} GB")
    print(f"  Disk free:          {free / (1024**3):,.1f} GB")
    pct = used / total * 100
    bar_len = 30
    filled = int(bar_len * pct / 100)
    bar = "█" * filled + "░" * (bar_len - filled)
    print(f"  Usage:              [{bar}] {pct:.1f}%")

    # Agent fleet health
    print("\n  Agent fleet:")
    agent_dir = SYSTEM_DIR / "agents"
    if agent_dir.exists():
        agents = list(agent_dir.glob("*.py"))
        print(f"    Agent scripts:    {len(agents)}")
        for a in agents[:8]:
            print(f"      • {a.name}")
        if len(agents) > 8:
            print(f"      … and {len(agents) - 8} more")
    else:
        print("    No agents directory found")

    # Recent errors
    recent_errors = safe_query(conn, """
        SELECT COUNT(*) as c FROM omega_evolution_log
        WHERE event_type = 'ERROR' AND created_at >= datetime('now', '-24 hours')
    """)
    err_count = recent_errors[0]["c"] if recent_errors else 0
    print(f"\n  Errors (24h):       {err_count}")
    print(f"  System:             {platform.system()} {platform.release()}")
    print(f"  Python:             {platform.python_version()}")


# ══════════════════════════════════════════════════════════════════════
#  2. REVENUE DASHBOARD
# ══════════════════════════════════════════════════════════════════════
def revenue_dashboard(conn):
    print("\n┌─────────────────────────────────────────────────────────┐")
    print("│           💰  REVENUE DASHBOARD                        │")
    print("└─────────────────────────────────────────────────────────┘")

    if not table_exists(conn, "omega_revenue_projections"):
        print("  ℹ️  omega_revenue_projections table not found")
        print("  Creating table for future use…")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS omega_revenue_projections (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                period      TEXT NOT NULL,
                mrr         REAL DEFAULT 0,
                arr         REAL DEFAULT 0,
                source      TEXT,
                notes       TEXT,
                created_at  TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.commit()
        print("  ✅ Table created — awaiting data")
        return

    rows = safe_query(conn, """
        SELECT period, mrr, arr, source
        FROM omega_revenue_projections
        ORDER BY period DESC LIMIT 12
    """)
    if not rows:
        print("  No revenue data yet")
        return

    print(f"\n  {'Period':<14} {'MRR':>12} {'ARR':>14} {'Source':<20}")
    print("  " + "─" * 62)
    for r in rows:
        mrr = f"${r['mrr']:,.2f}" if r['mrr'] else "—"
        arr = f"${r['arr']:,.2f}" if r['arr'] else "—"
        print(f"  {r['period']:<14} {mrr:>12} {arr:>14} {(r['source'] or ''):20}")


# ══════════════════════════════════════════════════════════════════════
#  3. CASE DASHBOARD
# ══════════════════════════════════════════════════════════════════════
def case_dashboard(conn):
    print("\n┌─────────────────────────────────────────────────────────┐")
    print("│           ⚖️   CASE DASHBOARD                           │")
    print("└─────────────────────────────────────────────────────────┘")

    # Separation days tracker
    config_row = safe_query(conn, """
        SELECT value FROM omega_evolution_config WHERE key = 'separation_date'
    """)
    if config_row:
        try:
            sep_date = datetime.fromisoformat(config_row[0]["value"])
            days = (datetime.now() - sep_date).days
            print(f"\n  Days since separation: {days}")
        except Exception:
            print("\n  Separation date:       not configured")
    else:
        print("\n  Separation date:       not configured")

    # Filing status per forum
    if table_exists(conn, "omega_filings"):
        filings = safe_query(conn, """
            SELECT forum, status, COUNT(*) as cnt
            FROM omega_filings
            GROUP BY forum, status
            ORDER BY forum, status
        """)
        if filings:
            print(f"\n  {'Forum':<24} {'Status':<16} {'Count':>6}")
            print("  " + "─" * 48)
            for f in filings:
                print(f"  {(f['forum'] or 'Unknown'):<24} {(f['status'] or '—'):<16} {f['cnt']:>6}")
        else:
            print("  No filing records yet")
    else:
        print("  ℹ️  omega_filings table not found")

    # OMEGA Score Trends
    if table_exists(conn, "omega_scores"):
        scores = safe_query(conn, """
            SELECT date(created_at) as day, 
                   ROUND(AVG(score), 2) as avg_score,
                   COUNT(*) as evaluations
            FROM omega_scores
            WHERE created_at >= datetime('now', '-30 days')
            GROUP BY day ORDER BY day DESC LIMIT 14
        """)
        if scores:
            print(f"\n  OMEGA Score Trends (last 14 days):")
            print(f"  {'Date':<14} {'Avg Score':>10} {'Evaluations':>13}")
            print("  " + "─" * 40)
            for s in scores:
                bar = "▓" * int((s["avg_score"] or 0) / 10)
                print(f"  {s['day']:<14} {s['avg_score']:>10} {s['evaluations']:>13}  {bar}")
        else:
            print("\n  No OMEGA score data in last 30 days")
    else:
        print("  ℹ️  omega_scores table not found")


# ══════════════════════════════════════════════════════════════════════
#  4. ALERT CONFIGURATION
# ══════════════════════════════════════════════════════════════════════
DEFAULT_ALERTS = [
    ("DISK_SPACE_LOW",       "HIGH",     "free_gb < 10",       "Disk free space below 10 GB"),
    ("AGENT_DOWN",           "CRITICAL", "errors_1h > 10",     "Agent failure spike — more than 10 errors/hour"),
    ("PAYMENT_FAILED",       "HIGH",     "stripe_status=fail",  "Payment processing failure detected"),
    ("DEADLINE_APPROACHING", "HIGH",     "days_remaining < 7",  "Court filing deadline within 7 days"),
    ("DB_GROWTH_SPIKE",      "MEDIUM",   "growth_mb > 50",     "Database grew more than 50 MB since last check"),
    ("OMEGA_SCORE_DROP",     "MEDIUM",   "score_delta < -10",  "OMEGA score dropped by 10+ points"),
]


def setup_alerts(conn):
    """Insert default alert configs if they don't exist."""
    ensure_alert_tables(conn)
    existing = {r["alert_type"] for r in safe_query(conn, "SELECT alert_type FROM omega_alerts")}
    inserted = 0
    for atype, severity, threshold, detail in DEFAULT_ALERTS:
        if atype not in existing:
            conn.execute(
                "INSERT INTO omega_alerts (alert_type, severity, threshold, detail) VALUES (?, ?, ?, ?)",
                (atype, severity, threshold, detail)
            )
            inserted += 1
    conn.commit()
    return inserted


def alert_dashboard(conn):
    print("\n┌─────────────────────────────────────────────────────────┐")
    print("│           🚨  ALERT CONFIGURATION                      │")
    print("└─────────────────────────────────────────────────────────┘")

    new_alerts = setup_alerts(conn)
    if new_alerts:
        print(f"\n  Inserted {new_alerts} new default alert rule(s)")

    alerts = safe_query(conn, "SELECT * FROM omega_alerts ORDER BY severity, alert_type")
    if not alerts:
        print("  No alerts configured")
        return

    sev_icons = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}
    print(f"\n  {'':2} {'Alert Type':<26} {'Sev':<10} {'Threshold':<22} {'Enabled'}")
    print("  " + "─" * 72)
    for a in alerts:
        icon = sev_icons.get(a["severity"], "⚪")
        enabled = "✓" if a["enabled"] else "✗"
        print(f"  {icon} {a['alert_type']:<26} {a['severity']:<10} {(a['threshold'] or '—'):<22} {enabled}")

    # Check live alerts
    print("\n  Live alert checks:")
    _check_disk_space()
    _check_recent_errors(conn)


def _check_disk_space():
    total, used, free = shutil.disk_usage(str(BASE_DIR))
    free_gb = free / (1024 ** 3)
    status = "🟢 OK" if free_gb > 10 else "🔴 LOW"
    print(f"    Disk free: {free_gb:,.1f} GB  {status}")


def _check_recent_errors(conn):
    rows = safe_query(conn, """
        SELECT COUNT(*) as c FROM omega_evolution_log
        WHERE event_type = 'ERROR' AND created_at >= datetime('now', '-1 hour')
    """)
    count = rows[0]["c"] if rows else 0
    status = "🟢 OK" if count <= 10 else "🔴 SPIKE"
    print(f"    Errors (1h): {count}  {status}")


# ══════════════════════════════════════════════════════════════════════
#  MAIN — Run and Print Full Observability Dashboard
# ══════════════════════════════════════════════════════════════════════
def main():
    print("=" * 72)
    print("  🔭 LitigationOS — Full Observability Dashboard  (Phase 10)")
    print(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 72)

    if not DB_PATH.exists():
        print(f"\n⚠️  Database not found at {DB_PATH}")
        print("   Creating minimal DB for dashboard schema…")
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
    else:
        conn = get_db()

    ensure_alert_tables(conn)

    system_dashboard(conn)
    revenue_dashboard(conn)
    case_dashboard(conn)
    alert_dashboard(conn)

    conn.close()
    print("\n" + "=" * 72)
    print("  🔭 Observability Dashboard — COMPLETE")
    print("=" * 72)


if __name__ == "__main__":
    main()
