#!/usr/bin/env python3
"""
THE MANBEARPIG x NEXUS — Copilot Startup Hook — EPOCH v11.0 OMEGA-SUPREME
===================================================================
Auto-generates a startup report when Copilot CLI launches.
Provides instant context: DB health, deadlines, filing status,
separation day count, system health, HF AI models, todo status,
drive state, NEXUS 85-system warmup, and past session recall.

Usage:
    python copilot_startup_hook.py              # Generate report to stdout
    python copilot_startup_hook.py --file       # Write to startup_report.md
    python copilot_startup_hook.py --json       # JSON output
    python copilot_startup_hook.py --warmup     # NEXUS warmup + HF models + report
"""

import json
import os
import sqlite3
import sys
from datetime import datetime, date
from pathlib import Path

# Force UTF-8 output
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace', closefd=False)

LITIGOS_ROOT = Path(r"C:\Users\andre\LitigationOS")
DB_PATH = LITIGOS_ROOT / "litigation_context.db"
REPORT_PATH = LITIGOS_ROOT / "00_SYSTEM" / "STARTUP_REPORT.md"
SESSION_STATE = LITIGOS_ROOT / "00_SYSTEM" / "MANBEARPIG_SESSION_STATE.md"

def get_db():
    try:
        conn = sqlite3.connect(str(DB_PATH), timeout=10)
        conn.execute("PRAGMA journal_mode=WAL")
        return conn
    except Exception as e:
        return None

def separation_days():
    sep_start = date(2025, 8, 8)
    today = date.today()
    return (today - sep_start).days

def generate_report():
    """Generate comprehensive startup report."""
    report = {}
    report["timestamp"] = datetime.now().isoformat()
    report["engine"] = "THE-MANBEARPIG x NEXUS v11.0 OMEGA-SUPREME"
    report["separation_days"] = separation_days()

    # Drive free space
    try:
        import shutil
        drives = {}
        for d in ['C:\\', 'D:\\', 'F:\\', 'G:\\', 'H:\\', 'I:\\']:
            try:
                u = shutil.disk_usage(d)
                drives[d[0]] = {"free_gb": round(u.free/1024**3, 2), "total_gb": round(u.total/1024**3, 2)}
            except:
                pass
        report["drives"] = drives
    except:
        report["drives"] = {}

    conn = get_db()
    if not conn:
        report["db_status"] = "DISCONNECTED"
        return report

    report["db_status"] = "CONNECTED"

    # DB size
    try:
        db_size = os.path.getsize(str(DB_PATH))
        report["db_size_mb"] = round(db_size / (1024 * 1024), 1)
    except:
        report["db_size_mb"] = 0

    # Table count
    try:
        report["table_count"] = conn.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
        ).fetchone()[0]
    except:
        report["table_count"] = 0

    # Deadlines
    try:
        rows = conn.execute(
            "SELECT deadline_name, due_date_iso, case_id, status FROM deadlines "
            "WHERE due_date_iso >= date('now') ORDER BY due_date_iso LIMIT 15"
        ).fetchall()
        deadlines = []
        for r in rows:
            try:
                due = datetime.strptime(r[1], "%Y-%m-%d").date()
                days_left = (due - date.today()).days
                urgency = "🔴" if days_left <= 7 else "🟠" if days_left <= 14 else "🟡" if days_left <= 30 else "🟢"
                deadlines.append({
                    "name": r[0], "due": r[1], "case": r[2], "status": r[3],
                    "days_left": days_left, "urgency": urgency
                })
            except:
                pass
        report["deadlines"] = deadlines
    except:
        report["deadlines"] = []

    # Filing readiness
    try:
        rows = conn.execute(
            "SELECT vehicle_name, status, readiness_score FROM filing_readiness "
            "ORDER BY readiness_score DESC LIMIT 20"
        ).fetchall()
        report["filing_readiness"] = [
            {"vehicle": r[0], "status": r[1], "score": r[2]} for r in rows
        ]
    except:
        report["filing_readiness"] = []

    # Evidence counts
    report["evidence"] = {}
    for tbl, key in [("extracted_harms", "harms"), ("evidence_quotes", "quotes"),
                     ("impeachment_items", "impeachment"), ("judicial_violations", "violations"),
                     ("contradiction_map", "contradictions"), ("claims", "claims")]:
        try:
            cnt = conn.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
            report["evidence"][key] = cnt
        except:
            pass

    # System health
    try:
        rows = conn.execute(
            "SELECT engine_name, status, latency_ms FROM system_health_log ORDER BY rowid DESC LIMIT 10"
        ).fetchall()
        healthy = sum(1 for r in rows if r[1] == "HEALTHY")
        report["system_health"] = {
            "engines_checked": len(rows),
            "healthy": healthy,
            "status": "ALL HEALTHY" if healthy == len(rows) else f"{healthy}/{len(rows)} HEALTHY"
        }
    except:
        report["system_health"] = {"status": "UNKNOWN"}

    # Recent copilot sessions
    try:
        from session_recall import SessionRecall
        sr = SessionRecall()
        recent = sr.get_recent_sessions(limit=5)
        report["recent_sessions"] = recent.get("sessions", [])[:5]
        report["total_sessions"] = recent.get("total_discovered", 0)
        sr.close()
    except:
        report["recent_sessions"] = []
        report["total_sessions"] = 0

    # Todo status from master_todos
    try:
        rows = conn.execute(
            "SELECT status, COUNT(*) FROM master_todos GROUP BY status"
        ).fetchall()
        report["todos"] = {r[0]: r[1] for r in rows}
        report["todos"]["total"] = sum(r[1] for r in rows)
    except:
        report["todos"] = {}

    # HF model registry
    try:
        rows = conn.execute(
            "SELECT model_id, purpose, status FROM hf_model_registry"
        ).fetchall()
        report["hf_models"] = [{"id": r[0], "purpose": r[1], "status": r[2]} for r in rows]
    except:
        report["hf_models"] = []

    # HF Legal Engine availability
    hf_engine = LITIGOS_ROOT / "00_SYSTEM" / "local_model" / "hf_legal_engine.py"
    report["hf_engine_available"] = hf_engine.exists()

    # Jurisdiction databases
    jur_db_dir = LITIGOS_ROOT / "databases"
    court_forms_db = LITIGOS_ROOT / "court_forms.db"
    jur_info = {"databases": {}, "specialty_count": 0}
    jur_info["court_forms"] = f"✅ {os.path.getsize(str(court_forms_db)) // 1024}KB" if court_forms_db.exists() else "❌ NOT FOUND"
    if jur_db_dir.exists():
        import glob as globmod
        for db_file in sorted(globmod.glob(str(jur_db_dir / "*.db"))):
            db_name = os.path.basename(db_file)
            try:
                db_conn = sqlite3.connect(db_file, timeout=5)
                db_conn.execute("PRAGMA busy_timeout=5000")
                tbl_count = db_conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
                db_conn.close()
                jur_info["databases"][db_name] = {
                    "exists": True,
                    "size_kb": os.path.getsize(db_file) // 1024,
                    "tables": tbl_count
                }
                jur_info["specialty_count"] += 1
            except:
                jur_info["databases"][db_name] = {"exists": True, "size_kb": os.path.getsize(db_file) // 1024, "tables": 0}
    report["jurisdiction_dbs"] = jur_info

    conn.close()
    return report

def format_markdown(report):
    """Format report as readable markdown."""
    sep = report.get("separation_days", 0)
    lines = [
        f"# 🐻 THE MANBEARPIG — Startup Report",
        f"**Generated:** {report.get('timestamp', 'unknown')}",
        f"**Engine:** {report.get('engine', 'unknown')}",
        f"**Parent-Child Separation:** **{sep} DAYS** (since Aug 8, 2025)",
        "",
        f"## Database",
        f"- Status: {report.get('db_status', 'UNKNOWN')}",
        f"- Size: {report.get('db_size_mb', 0)} MB",
        f"- Tables: {report.get('table_count', 0)}",
        "",
    ]

    # Evidence
    ev = report.get("evidence", {})
    if ev:
        lines.append("## Evidence Arsenal")
        for k, v in ev.items():
            lines.append(f"- **{k}:** {v:,}")
        lines.append("")

    # Deadlines
    deadlines = report.get("deadlines", [])
    if deadlines:
        lines.append("## Upcoming Deadlines")
        lines.append("| Urgency | Deadline | Due | Days Left | Case | Status |")
        lines.append("|---------|----------|-----|-----------|------|--------|")
        for d in deadlines:
            lines.append(
                f"| {d.get('urgency', '?')} | {d.get('name', '?')} | {d.get('due', '?')} | "
                f"{d.get('days_left', '?')} | {d.get('case', '?')} | {d.get('status', '?')} |"
            )
        lines.append("")

    # Filing readiness
    filings = report.get("filing_readiness", [])
    if filings:
        lines.append("## Filing Readiness")
        lines.append("| Vehicle | Status | Score |")
        lines.append("|---------|--------|-------|")
        for f in filings[:15]:
            lines.append(f"| {f.get('vehicle', '?')} | {f.get('status', '?')} | {f.get('score', '?')} |")
        lines.append("")

    # System health
    health = report.get("system_health", {})
    lines.append(f"## System Health: {health.get('status', 'UNKNOWN')}")
    lines.append("")

    # Recent sessions
    sessions = report.get("recent_sessions", [])
    if sessions:
        lines.append(f"## Recent Copilot Sessions ({report.get('total_sessions', 0)} total)")
        for s in sessions:
            sid = s.get("session_id", "?")[:12]
            mod = s.get("last_modified", "?")
            plan = s.get("plan_summary", "No plan")
            lines.append(f"- `{sid}...` — {mod} — {plan}")
        lines.append("")

    # Jurisdiction Databases
    jur_dbs = report.get("jurisdiction_dbs", {})
    if jur_dbs:
        lines.append("## Jurisdiction Databases")
        lines.append(f"- **Court Forms DB:** {jur_dbs.get('court_forms', 'NOT FOUND')}")
        lines.append(f"- **Specialty DBs:** {jur_dbs.get('specialty_count', 0)} loaded")
        for db_name, db_info in jur_dbs.get("databases", {}).items():
            status_icon = "✅" if db_info.get("exists") else "❌"
            size = db_info.get("size_kb", 0)
            tables = db_info.get("tables", 0)
            lines.append(f"  - {status_icon} `{db_name}` — {size}KB, {tables} tables")
        lines.append("")

    lines.append("---")
    lines.append("*MANBEARPIG v11.0 OMEGA-SUPREME — Zero external API. Every assertion DB-grounded.*")
    lines.append("")

    # Drive state
    drives = report.get("drives", {})
    if drives:
        lines.append("## Drive State")
        lines.append("| Drive | Free GB | Total GB | Status |")
        lines.append("|-------|---------|----------|--------|")
        for d, info in sorted(drives.items()):
            free = info.get("free_gb", 0)
            total = info.get("total_gb", 0)
            status = "🔴 CRITICAL" if free < 2 else "🟠 LOW" if free < 5 else "🟢 OK"
            lines.append(f"| {d}: | {free} | {total} | {status} |")
        lines.append("")

    # Todo status
    todos = report.get("todos", {})
    if todos:
        lines.append("## Todo Tracker")
        lines.append(f"- **Total:** {todos.get('total', 0)}")
        lines.append(f"- ✅ Done: {todos.get('done', 0)}")
        lines.append(f"- 🔄 In Progress: {todos.get('in_progress', 0)}")
        lines.append(f"- ⏳ Pending: {todos.get('pending', 0)}")
        lines.append(f"- 🚫 Blocked: {todos.get('blocked', 0)}")
        lines.append("")

    # HF Models
    hf_models = report.get("hf_models", [])
    if hf_models:
        lines.append("## HuggingFace AI Models")
        lines.append(f"- **HF Legal Engine:** {'✅ READY' if report.get('hf_engine_available') else '❌ NOT FOUND'}")
        lines.append(f"- **Engine path:** `00_SYSTEM/local_model/hf_legal_engine.py`")
        for m in hf_models:
            status_icon = "✅" if m["status"] == "ready" else "❌"
            lines.append(f"- {status_icon} `{m['id']}` — {m['purpose']}")
        lines.append("")

    # Iron Rules reminder
    lines.append("## ⚠️ IRON RULES (PERMANENT)")
    lines.append("1. EXTREME DEPTH standard (8,348-violation thoroughness MINIMUM)")
    lines.append("2. Real court files = PDF ONLY (.md filings are AI-generated drafts)")
    lines.append("3. ASK PERMISSION before deleting anything")
    lines.append("4. Leave ALL Python files alone")
    lines.append("5. HASHING BANNED — use 5-Tier Convergence Dedup Engine")
    lines.append("6. Save to litigation_context.db before each new task")
    lines.append("")

    # Continuation pointer
    lines.append("## Resume Work")
    lines.append("- Read `CONTINUE_FROM_HERE.md` for full handoff context")
    lines.append("- Query: `SELECT * FROM master_todos WHERE status='pending' ORDER BY id LIMIT 20`")
    lines.append("- Run NEXUS benchmark: `python 00_SYSTEM/local_model/nexus_engine.py --benchmark`")
    lines.append("- Run NEXUS status: `python 00_SYSTEM/local_model/nexus_engine.py --status`")
    lines.append("- Run HF engine: `python 00_SYSTEM/local_model/hf_legal_engine.py --benchmark`")
    lines.append("")

    # NEXUS System Map
    lines.append("## NEXUS v2.0 OMEGA-SUPREME System Map")
    lines.append("**6 Core Brains:** MANBEARPIG | HF Legal AI | GGUF LLM | FRED CEPS | FRED MONOLITH | ALE")
    lines.append("**85 systems across 9 tiers | 53 skills | 22 agents | 40+ JSON-RPC routes**")
    lines.append("- T0: Security (4) | T1: Database (5) | T2: Retrieval (8) | T3: Classification (10)")
    lines.append("- T4: Reasoning (7) | T5: Analysis (12) | T6: Orchestration (7) | T7: Filing (9)")
    lines.append("- T8: Apps (10) | T9: Skills (53) + Agents (22)")
    lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    report = generate_report()

    if "--json" in sys.argv:
        print(json.dumps(report, indent=2, default=str))
    elif "--warmup" in sys.argv:
        # NEXUS 4-phase warmup + report
        try:
            sys.path.insert(0, str(Path(__file__).resolve().parent))
            from nexus_engine import NexusEngine
            nexus = NexusEngine()
            warmup_result = nexus.warmup()
            report["nexus_warmup"] = warmup_result
            print(f"NEXUS warmup: {warmup_result.get('total_loaded', 0)} engines loaded in {warmup_result.get('total_ms', 0)}ms")
        except Exception as e:
            print(f"NEXUS warmup error: {e}")
        md = format_markdown(report)
        REPORT_PATH.write_text(md, encoding="utf-8")
        print(f"Report written to {REPORT_PATH}")
        print(md)
    elif "--file" in sys.argv:
        md = format_markdown(report)
        REPORT_PATH.write_text(md, encoding="utf-8")
        print(f"Report written to {REPORT_PATH}")
        print(md)
    else:
        md = format_markdown(report)
        print(md)
