#!/usr/bin/env python3
"""
SESSION CONTINUITY ENGINE — LitigationOS Autonomous Execution
==============================================================
Tells every new Copilot session EXACTLY what happened, what's pending,
and what to do next. Queries 5 continuity tables in litigation_context.db:
  - pipeline_registry:  What pipelines exist and their status
  - master_todos:       Autonomous task queue with priorities/deadlines
  - filing_readiness:   Per-filing readiness scores and blockers
  - session_handoff:    What the last session accomplished + left behind
  - system_health_log:  Engine/service health

Usage:
    python session_continuity_engine.py              # Full report to stdout
    python session_continuity_engine.py --json       # JSON output
    python session_continuity_engine.py --next       # Just "what to do next"
    python session_continuity_engine.py --handoff    # Last session handoff
    python session_continuity_engine.py --update     # Update MSC/COA status after agent completion

Run this AFTER copilot_startup_hook.py in every session startup.
"""

import json
import os
import sqlite3
import sys
from datetime import datetime, date, timedelta
from pathlib import Path

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace', closefd=False)

DB_PATH = Path(r"C:\Users\andre\LitigationOS\litigation_context.db")
REPORT_PATH = Path(r"C:\Users\andre\LitigationOS\00_SYSTEM\CONTINUITY_REPORT.md")


def get_db():
    conn = sqlite3.connect(str(DB_PATH), timeout=30)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    conn.row_factory = sqlite3.Row
    return conn


def table_exists(conn, name):
    return conn.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone()[0] > 0


def urgency_emoji(days_left):
    if days_left is None:
        return "⚪"
    if days_left <= 3:
        return "🔴"
    if days_left <= 7:
        return "🟠"
    if days_left <= 14:
        return "🟡"
    return "🟢"


def days_until(deadline_str):
    if not deadline_str:
        return None
    try:
        dl = datetime.strptime(deadline_str[:10], "%Y-%m-%d").date()
        return (dl - date.today()).days
    except Exception:
        return None


def generate_report(conn):
    lines = []
    lines.append("# 🔄 SESSION CONTINUITY REPORT")
    lines.append(f"Generated: {datetime.now().isoformat()}")
    lines.append(f"Engine: session_continuity_engine.py v1.0")
    lines.append("")

    # ── SECTION 1: LAST SESSION HANDOFF ──
    lines.append("## 📋 LAST SESSION HANDOFF")
    if table_exists(conn, "session_handoff"):
        row = conn.execute(
            "SELECT * FROM session_handoff ORDER BY id DESC LIMIT 1"
        ).fetchone()
        if row:
            lines.append(f"- Session: `{row['session_id'][:12]}...`")
            lines.append(f"- Date: {row['session_date']}")
            try:
                completed = json.loads(row["work_completed"] or "[]")
                lines.append(f"- Completed: {len(completed)} items")
                for item in completed[:5]:
                    lines.append(f"  - ✅ {item}")
                if len(completed) > 5:
                    lines.append(f"  - ... and {len(completed)-5} more")
            except Exception:
                pass
            try:
                wip = json.loads(row["work_in_progress"] or "[]")
                if wip:
                    lines.append(f"- **Still In Progress:**")
                    for item in wip:
                        lines.append(f"  - 🔄 {item}")
            except Exception:
                pass
            try:
                blocked = json.loads(row["work_blocked"] or "[]")
                if blocked:
                    lines.append(f"- **Blocked:**")
                    for item in blocked:
                        lines.append(f"  - 🚫 {item}")
            except Exception:
                pass
            try:
                notes = json.loads(row["critical_notes"] or "[]")
                if notes:
                    lines.append(f"- **Critical Notes:**")
                    for note in notes:
                        lines.append(f"  - ⚠️ {note}")
            except Exception:
                pass
        else:
            lines.append("- No session handoff data found")
    else:
        lines.append("- ❌ session_handoff table missing — run continuity setup")
    lines.append("")

    # ── SECTION 2: URGENT DEADLINES ──
    lines.append("## 🚨 DEADLINE URGENCY")
    if table_exists(conn, "deadlines"):
        deadlines = conn.execute(
            "SELECT title, due_date, case_number, status FROM deadlines "
            "WHERE due_date >= date('now') ORDER BY due_date LIMIT 10"
        ).fetchall()
        if deadlines:
            for dl in deadlines:
                days = days_until(dl["due_date"])
                emoji = urgency_emoji(days)
                days_str = f"{days}d" if days is not None else "??"
                lines.append(
                    f"  {emoji} **{dl['title']}** — {dl['due_date']} "
                    f"({days_str}) [{dl['case_number'] or ''}]"
                )
        else:
            lines.append("  No upcoming deadlines")
    lines.append("")

    # ── SECTION 3: WHAT TO DO NEXT (priority-ordered) ──
    lines.append("## 🎯 WHAT TO DO NEXT (Priority Order)")
    if table_exists(conn, "master_todos"):
        todos = conn.execute(
            "SELECT id, title, description, status, priority, deadline, lane, category "
            "FROM master_todos WHERE status IN ('pending','in_progress','blocked') "
            "ORDER BY priority, id"
        ).fetchall()
        if todos:
            for t in todos:
                days = days_until(t["deadline"])
                emoji = urgency_emoji(days)
                status_icon = {"pending": "⏳", "in_progress": "🔄", "blocked": "🚫"}.get(
                    t["status"], "❓"
                )
                dl_str = f" [DUE: {t['deadline']}]" if t["deadline"] else ""
                lane_str = f" [Lane {t['lane']}]" if t["lane"] else ""
                lines.append(
                    f"  {emoji}{status_icon} **P{t['priority']}** {t['title']}{dl_str}{lane_str}"
                )
                if t["description"]:
                    desc_short = t["description"][:120]
                    lines.append(f"     → {desc_short}")
            lines.append("")
            lines.append(
                f"  **Summary:** {sum(1 for t in todos if t['status']=='pending')} pending, "
                f"{sum(1 for t in todos if t['status']=='in_progress')} in_progress, "
                f"{sum(1 for t in todos if t['status']=='blocked')} blocked"
            )
        else:
            lines.append("  All tasks complete! 🎉")
    else:
        lines.append("  ❌ master_todos table missing")
    lines.append("")

    # ── SECTION 4: PIPELINE STATUS ──
    lines.append("## 🔧 PIPELINE STATUS")
    if table_exists(conn, "pipeline_registry"):
        phases = conn.execute(
            "SELECT phase_id, phase_name, status, items_processed, items_total, "
            "error_message, script_path FROM pipeline_registry ORDER BY phase_number"
        ).fetchall()
        if phases:
            for p in phases:
                status_icon = {
                    "completed": "✅",
                    "running": "🔄",
                    "partial": "⚡",
                    "pending": "⏳",
                    "failed": "❌",
                    "blocked": "🚫",
                }.get(p["status"], "❓")
                total = p["items_total"] or 0
                proc = p["items_processed"] or 0
                pct = f" ({proc}/{total}, {proc*100//total if total else 0}%)" if total else ""
                lines.append(f"  {status_icon} **{p['phase_name']}** — {p['status']}{pct}")
                if p["error_message"]:
                    lines.append(f"     ⚠️ {p['error_message'][:100]}")
                if p["script_path"] and p["status"] in ("pending", "partial"):
                    lines.append(f"     📄 Script: `{p['script_path']}`")
    lines.append("")

    # ── SECTION 5: FILING READINESS ──
    lines.append("## 📄 FILING READINESS")
    if table_exists(conn, "filing_readiness"):
        filings = conn.execute(
            "SELECT vehicle_name, status, readiness_score, lane, deadline, blockers "
            "FROM filing_readiness ORDER BY readiness_score DESC"
        ).fetchall()
        if filings:
            for f in filings:
                days = days_until(f["deadline"])
                emoji = urgency_emoji(days)
                score = f["readiness_score"] or 0
                lines.append(
                    f"  {emoji} **{f['vehicle_name']}** — {f['status']} "
                    f"(score: {score}/100) [Lane {f['lane'] or '?'}]"
                )
                if f["blockers"]:
                    lines.append(f"     🚫 Blockers: {f['blockers']}")
        else:
            lines.append("  No filing readiness data — run filing audit")
    lines.append("")

    # ── SECTION 6: EXECUTION INSTRUCTIONS ──
    lines.append("## 🤖 AUTONOMOUS EXECUTION INSTRUCTIONS")
    lines.append("")
    lines.append("**For the Copilot agent reading this report:**")
    lines.append("")
    lines.append("1. **Check master_todos** — execute tasks in priority order (P1 first)")
    lines.append("2. **Resume partial pipelines** — any pipeline with status='partial' needs re-run")
    lines.append("3. **Unblock blocked tasks** — check dependencies, resolve blockers")
    lines.append("4. **Deadline-driven** — if any deadline is <3 days away, DROP everything else")
    lines.append("5. **Update status** — after completing any task:")
    lines.append("   ```sql")
    lines.append("   UPDATE master_todos SET status='done', completed_at=datetime('now'),")
    lines.append("     completed_by_session='<your_session_id>' WHERE id=<task_id>;")
    lines.append("   ```")
    lines.append("6. **Write session_handoff** before ending your session")
    lines.append("7. **Query these tables on startup:**")
    lines.append("   ```sql")
    lines.append("   SELECT * FROM master_todos WHERE status IN ('pending','in_progress','blocked') ORDER BY priority;")
    lines.append("   SELECT * FROM pipeline_registry WHERE status NOT IN ('completed') ORDER BY phase_number;")
    lines.append("   SELECT * FROM session_handoff ORDER BY id DESC LIMIT 1;")
    lines.append("   SELECT * FROM filing_readiness ORDER BY readiness_score ASC;")
    lines.append("   ```")
    lines.append("")

    # ── SECTION 7: CONTEXT TABLES REMINDER ──
    lines.append("## 🧠 PERMANENT CONTEXT TABLES (query these for intelligence)")
    context_tables = [
        ("narrative_context", "Case narrative elements by category/lane"),
        ("critical_facts", "Verified immutable facts (Berry nexus, perjury, etc.)"),
        ("police_reports", "7 weaponized police reports with critical quotes"),
        ("evidence_exhibits", "23 key exhibits with file paths and authentication"),
        ("false_allegations", "Emily's 7 false allegations with rebuttals"),
        ("json_harvest", "Harvested JSON files with MEEK lane tags"),
        ("json_atoms", "Evidence atoms extracted from JSON files"),
        ("ocr_master_xref", "4,061 OCR'd files cross-wired from J:\\ocr_master.db"),
    ]
    for tname, desc in context_tables:
        if table_exists(conn, tname):
            count = conn.execute(f"SELECT COUNT(*) FROM [{tname}]").fetchone()[0]
            lines.append(f"  - `{tname}`: {count} rows — {desc}")
        else:
            lines.append(f"  - ❌ `{tname}`: MISSING")
    lines.append("")

    return "\n".join(lines)


def get_next_actions(conn):
    """Return just the next actions for quick startup."""
    actions = []
    if table_exists(conn, "master_todos"):
        todos = conn.execute(
            "SELECT title, priority, deadline, lane, description "
            "FROM master_todos WHERE status='pending' ORDER BY priority LIMIT 5"
        ).fetchall()
        for t in todos:
            actions.append({
                "title": t["title"],
                "priority": t["priority"],
                "deadline": t["deadline"],
                "lane": t["lane"],
                "description": t["description"],
            })
    return actions


def update_todo(conn, todo_id, status, session_id=None):
    """Mark a todo as done/in_progress/blocked."""
    now = datetime.now().isoformat()
    if status == "done":
        conn.execute(
            "UPDATE master_todos SET status=?, completed_at=?, completed_by_session=? WHERE id=?",
            (status, now, session_id, todo_id),
        )
    elif status == "in_progress":
        conn.execute(
            "UPDATE master_todos SET status=?, started_at=? WHERE id=?",
            (status, now, todo_id),
        )
    else:
        conn.execute("UPDATE master_todos SET status=? WHERE id=?", (status, todo_id))
    conn.commit()


def update_pipeline(conn, phase_id, status, items_processed=None, error=None):
    """Update pipeline phase status."""
    now = datetime.now().isoformat()
    if items_processed is not None:
        conn.execute(
            "UPDATE pipeline_registry SET status=?, items_processed=?, "
            "updated_at=?, error_message=? WHERE phase_id=?",
            (status, items_processed, now, error, phase_id),
        )
    else:
        conn.execute(
            "UPDATE pipeline_registry SET status=?, updated_at=?, error_message=? WHERE phase_id=?",
            (status, now, error, phase_id),
        )
    conn.commit()


def write_handoff(conn, session_id, completed, in_progress, blocked, priorities, notes):
    """Write session handoff record."""
    conn.execute(
        """INSERT INTO session_handoff
        (session_id, work_completed, work_in_progress, work_blocked,
         next_priorities, critical_notes)
        VALUES (?, ?, ?, ?, ?, ?)""",
        (
            session_id,
            json.dumps(completed),
            json.dumps(in_progress),
            json.dumps(blocked),
            json.dumps(priorities),
            json.dumps(notes),
        ),
    )
    conn.commit()


def main():
    args = sys.argv[1:]
    conn = get_db()

    if "--json" in args:
        report = {
            "next_actions": get_next_actions(conn),
            "timestamp": datetime.now().isoformat(),
        }
        print(json.dumps(report, indent=2))
    elif "--next" in args:
        actions = get_next_actions(conn)
        print("=== NEXT ACTIONS ===")
        for a in actions:
            dl = f" [DUE: {a['deadline']}]" if a["deadline"] else ""
            print(f"  P{a['priority']}: {a['title']}{dl}")
            if a["description"]:
                print(f"    → {a['description'][:100]}")
    elif "--handoff" in args:
        if table_exists(conn, "session_handoff"):
            row = conn.execute(
                "SELECT * FROM session_handoff ORDER BY id DESC LIMIT 1"
            ).fetchone()
            if row:
                print(f"Session: {row['session_id']}")
                print(f"Date: {row['session_date']}")
                for field in [
                    "work_completed",
                    "work_in_progress",
                    "work_blocked",
                    "next_priorities",
                    "critical_notes",
                ]:
                    val = row[field]
                    if val:
                        try:
                            items = json.loads(val)
                            print(f"\n{field}:")
                            for item in items:
                                print(f"  - {item}")
                        except Exception:
                            print(f"\n{field}: {val}")
    else:
        report_text = generate_report(conn)
        print(report_text)
        # Also write to file
        try:
            with open(str(REPORT_PATH), "w", encoding="utf-8") as f:
                f.write(report_text)
            print(f"\n[Saved to {REPORT_PATH}]")
        except Exception as e:
            print(f"\n[Could not save: {e}]")

    conn.close()


if __name__ == "__main__":
    main()
