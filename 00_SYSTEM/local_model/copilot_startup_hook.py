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

    # Engine availability (NOVEL, DARWIN, inference_engine)
    try:
        engines_status = {}
        engine_paths = {
            "novel": LITIGOS_ROOT / "00_SYSTEM" / "novel" / "novel_engine.py",
            "darwin": LITIGOS_ROOT / "00_SYSTEM" / "darwin" / "darwin_engine.py",
            "inference": LITIGOS_ROOT / "00_SYSTEM" / "local_model" / "inference_engine.py",
        }
        for name, path in engine_paths.items():
            engines_status[name] = path.exists()
        report["engines"] = engines_status
    except Exception:
        report["engines"] = {}

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

    # ── NOVEL + DARWIN Engine Status ──
    novel_info = {"available": False}
    novel_db_path = LITIGOS_ROOT / "00_SYSTEM" / "novel" / "novel.db"
    if novel_db_path.exists():
        novel_info["available"] = True
        novel_info["size_kb"] = os.path.getsize(str(novel_db_path)) // 1024
        try:
            nconn = sqlite3.connect(str(novel_db_path), timeout=5)
            nconn.execute("PRAGMA busy_timeout=5000")
            row = nconn.execute("""
                SELECT
                    (SELECT COUNT(*) FROM inventions) as total,
                    (SELECT COUNT(*) FROM inventions WHERE status='prototyped') as prototyped,
                    (SELECT COUNT(*) FROM inventions WHERE status='tested') as tested,
                    (SELECT COUNT(*) FROM inventions WHERE status='deployed') as deployed,
                    (SELECT COUNT(*) FROM gap_registry) as gaps,
                    (SELECT COUNT(*) FROM evolution_cycles) as cycles
            """).fetchone()
            novel_info["inventions"] = row[0] if row else 0
            novel_info["prototyped"] = row[1] if row else 0
            novel_info["tested"] = row[2] if row else 0
            novel_info["deployed"] = row[3] if row else 0
            novel_info["gaps"] = row[4] if row else 0
            novel_info["cycles"] = row[5] if row else 0
            # Best fitness
            best = nconn.execute(
                "SELECT MAX(fitness_score) FROM inventions WHERE status != 'archived'"
            ).fetchone()
            novel_info["best_fitness"] = round(best[0], 3) if best and best[0] else 0
            nconn.close()
        except Exception as e:
            novel_info["error"] = str(e)
    report["novel_engine"] = novel_info

    darwin_info = {"available": False}
    darwin_db_path = LITIGOS_ROOT / "00_SYSTEM" / "darwin" / "darwin.db"
    if darwin_db_path.exists():
        darwin_info["available"] = True
        darwin_info["size_kb"] = os.path.getsize(str(darwin_db_path)) // 1024
        try:
            dconn = sqlite3.connect(str(darwin_db_path), timeout=5)
            dconn.execute("PRAGMA busy_timeout=5000")
            row = dconn.execute("""
                SELECT
                    (SELECT COUNT(*) FROM genomes) as total,
                    (SELECT MAX(generation) FROM genomes) as max_gen,
                    (SELECT MAX(fitness) FROM genomes) as best_fitness
            """).fetchone()
            darwin_info["genomes"] = row[0] if row else 0
            darwin_info["max_generation"] = row[1] if row else 0
            darwin_info["best_fitness"] = round(row[2], 3) if row and row[2] else 0
            dconn.close()
        except Exception as e:
            darwin_info["error"] = str(e)
    report["darwin_engine"] = darwin_info

    # ── LEXICON + ORACLE Legal Intelligence ──
    lexicon_info = {"available": False}
    lexicon_db_path = LITIGOS_ROOT / "00_SYSTEM" / "databases" / "lexicon.db"
    if lexicon_db_path.exists():
        lexicon_info["available"] = True
        lexicon_info["size_kb"] = os.path.getsize(str(lexicon_db_path)) // 1024
        try:
            lconn = sqlite3.connect(str(lexicon_db_path), timeout=5)
            lconn.execute("PRAGMA busy_timeout=5000")
            row = lconn.execute("""
                SELECT
                    (SELECT COUNT(*) FROM legal_rules) as total_rules,
                    (SELECT COUNT(*) FROM legal_rules WHERE source='MCR') as mcr,
                    (SELECT COUNT(*) FROM legal_rules WHERE source='MCL') as mcl,
                    (SELECT COUNT(*) FROM legal_rules WHERE source='MRE') as mre,
                    (SELECT COUNT(*) FROM rule_cross_refs) as xrefs,
                    (SELECT COUNT(*) FROM filing_requirements) as filing_reqs,
                    (SELECT COUNT(*) FROM deadline_rules) as deadlines,
                    (SELECT COUNT(*) FROM evidence_rules) as evidence,
                    (SELECT COUNT(*) FROM canon_violations) as canons
            """).fetchone()
            if row:
                lexicon_info["total_rules"] = row[0]
                lexicon_info["mcr"] = row[1]
                lexicon_info["mcl"] = row[2]
                lexicon_info["mre"] = row[3]
                lexicon_info["cross_refs"] = row[4]
                lexicon_info["filing_reqs"] = row[5]
                lexicon_info["deadlines"] = row[6]
                lexicon_info["evidence_rules"] = row[7]
                lexicon_info["canon_violations"] = row[8]
            lconn.close()
        except Exception as e:
            lexicon_info["error"] = str(e)
    # Check ORACLE
    oracle_engine = LITIGOS_ROOT / "00_SYSTEM" / "engines" / "oracle" / "oracle_engine.py"
    lexicon_info["oracle_available"] = oracle_engine.exists()
    report["lexicon_oracle"] = lexicon_info

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

    # NOVEL + DARWIN Engines
    novel = report.get("novel_engine", {})
    darwin = report.get("darwin_engine", {})
    if novel.get("available") or darwin.get("available"):
        lines.append("## 🧬 Evolution Engines")
        if novel.get("available"):
            lines.append(f"### NOVEL v2 (Invention Factory)")
            lines.append(f"- **Status:** ✅ ACTIVE — {novel.get('size_kb', 0)}KB")
            lines.append(f"- **Inventions:** {novel.get('inventions', 0)} total "
                        f"({novel.get('prototyped', 0)} prototyped, "
                        f"{novel.get('tested', 0)} tested, "
                        f"{novel.get('deployed', 0)} deployed)")
            lines.append(f"- **Gaps tracked:** {novel.get('gaps', 0)}")
            lines.append(f"- **Evolution cycles:** {novel.get('cycles', 0)}")
            lines.append(f"- **Best fitness:** {novel.get('best_fitness', 0)}")
            lines.append(f"- **Commands:** `perceive` `scan` `compose` `evolve` `validate` `forge` `dashboard`")
            lines.append(f"- **Run:** `cd 00_SYSTEM/novel && python novel_engine.py <command>`")
        else:
            lines.append("- **NOVEL:** ❌ NOT INITIALIZED (run `python 00_SYSTEM/novel/novel_engine.py scan`)")
        lines.append("")
        if darwin.get("available"):
            lines.append(f"### DARWIN (Self-Evolving Agent Fleet)")
            lines.append(f"- **Status:** ✅ ACTIVE — {darwin.get('size_kb', 0)}KB")
            lines.append(f"- **Genomes:** {darwin.get('genomes', 0)} "
                        f"(max generation: {darwin.get('max_generation', 0)})")
            lines.append(f"- **Best fitness:** {darwin.get('best_fitness', 0)}")
            lines.append(f"- **Run:** `cd 00_SYSTEM/darwin && python darwin_engine.py evolve`")
        else:
            lines.append("- **DARWIN:** ❌ NOT INITIALIZED (run `python 00_SYSTEM/darwin/darwin_engine.py bootstrap`)")
        lines.append("")

    # LEXICON + ORACLE Legal Intelligence
    lex = report.get("lexicon_oracle", {})
    if lex.get("available"):
        lines.append("## ⚖️ Legal Intelligence Engines")
        lines.append(f"### LEXICON (Michigan Legal Authority Database)")
        lines.append(f"- **Status:** ✅ ACTIVE — {lex.get('size_kb', 0)}KB")
        lines.append(f"- **Total rules:** {lex.get('total_rules', 0)} "
                     f"(MCR:{lex.get('mcr', 0)} MCL:{lex.get('mcl', 0)} MRE:{lex.get('mre', 0)})")
        lines.append(f"- **Cross-references:** {lex.get('cross_refs', 0)}")
        lines.append(f"- **Filing requirements:** {lex.get('filing_reqs', 0)}")
        lines.append(f"- **Deadline rules:** {lex.get('deadlines', 0)}")
        lines.append(f"- **Evidence decision trees:** {lex.get('evidence_rules', 0)}")
        lines.append(f"- **Canon violations (JTC):** {lex.get('canon_violations', 0)}")
        lines.append(f"- **Run:** `cd 00_SYSTEM/engines/lexicon && python lexicon_engine.py ask \"your question\"`")
        lines.append("")
        if lex.get("oracle_available"):
            lines.append(f"### ORACLE (Rule Reasoning Engine)")
            lines.append(f"- **Status:** ✅ ACTIVE")
            lines.append(f"- **Capabilities:** roadmap, deadlines, checklists, forms, service, risks")
            lines.append(f"- **Run:** `cd 00_SYSTEM/engines/oracle && python oracle_engine.py roadmap <type> <court>`")
            lines.append(f"- **Deadlines:** `python oracle_engine.py deadlines motion_filing --date YYYY-MM-DD`")
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
    # Engine status
    engines = report.get("engines", {})
    if engines:
        lines.append("## AI Engines")
        for eng_name, available in engines.items():
            icon = "✅" if available else "❌"
            lines.append(f"- {icon} **{eng_name.upper()}**")
        lines.append("")

    hf_models = report.get("hf_models", [])
    if hf_models:
        lines.append("## HuggingFace AI Models")
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
    lines.append("- Run inference engine: `cd 00_SYSTEM/local_model && python inference_engine.py --benchmark`")
    lines.append("- Run NOVEL perceive: `cd 00_SYSTEM/novel && python novel_engine.py perceive`")
    lines.append("- Run NOVEL evolve: `cd 00_SYSTEM/novel && python novel_engine.py evolve`")
    lines.append("- Run DARWIN evolve: `cd 00_SYSTEM/darwin && python darwin_engine.py evolve`")
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
