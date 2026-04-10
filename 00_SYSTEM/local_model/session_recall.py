#!/usr/bin/env python3
"""
LitigationOS Session Recall v2.0
=================================
Discovers and indexes Copilot session history for cross-session continuity.
Queries the session_store database (if available) and local session artifacts.

Usage:
    python session_recall.py recent           # Last 5 sessions with summaries
    python session_recall.py search <query>   # Search session history
    python session_recall.py handoff          # Get last session handoff data
    python session_recall.py stats            # Session statistics
    python session_recall.py --json           # All output as JSON

This script queries:
    1. The Copilot CLI session_store (SQLite at ~/.copilot/session-state/)
    2. Local session_handoff table in litigation_context.db
    3. master_todos table for pending work items
    4. filing_readiness for current filing status
    5. convergence_domains for convergence health
"""

import sqlite3
import sys
import os
import json
from datetime import datetime, date
from pathlib import Path

# ── Constants ──────────────────────────────────────────────────────────────
REPO_ROOT = Path(r"C:\Users\andre\LitigationOS")
DB_PATH = REPO_ROOT / "litigation_context.db"
SESSION_STATE_DIR = Path.home() / ".copilot" / "session-state"
LAST_CONTACT = date(2025, 7, 29)


def get_db_connection() -> sqlite3.Connection:
    """Open litigation_context.db with mandatory PRAGMAs."""
    conn = sqlite3.connect(str(DB_PATH), timeout=60)
    conn.execute("PRAGMA busy_timeout = 60000")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA cache_size = -32000")
    conn.row_factory = sqlite3.Row
    return conn


def safe_query(conn: sqlite3.Connection, sql: str, params=()) -> list:
    """Execute a query safely, returning empty list on error."""
    try:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]
    except sqlite3.OperationalError:
        return []


def get_session_handoffs(conn: sqlite3.Connection, limit: int = 5) -> list:
    """Get recent session handoff records."""
    return safe_query(conn, """
        SELECT session_id, work_completed, work_pending, critical_state,
               handoff_notes, created_at
        FROM session_handoff
        ORDER BY created_at DESC
        LIMIT ?
    """, (limit,))


def get_master_todos(conn: sqlite3.Connection, status_filter: str = None) -> list:
    """Get master todos, optionally filtered by status."""
    if status_filter:
        return safe_query(conn, """
            SELECT id, title, description, status, progress, updated_at
            FROM master_todos
            WHERE status = ?
            ORDER BY updated_at DESC
        """, (status_filter,))
    return safe_query(conn, """
        SELECT id, title, description, status, progress, updated_at
        FROM master_todos
        ORDER BY
            CASE status WHEN 'IN_PROGRESS' THEN 1 WHEN 'PENDING' THEN 2
                        WHEN 'BLOCKED' THEN 3 ELSE 4 END,
            updated_at DESC
    """)


def get_filing_readiness(conn: sqlite3.Connection) -> list:
    """Get filing readiness data."""
    return safe_query(conn, """
        SELECT vehicle_name, lane, status, confidence_score, deadline_date
        FROM filing_readiness
        ORDER BY confidence_score DESC
    """)


def get_convergence_summary(conn: sqlite3.Connection) -> dict:
    """Get convergence domain status counts."""
    rows = safe_query(conn, """
        SELECT status, COUNT(*) as cnt
        FROM convergence_domains
        GROUP BY status
        ORDER BY cnt DESC
    """)
    return {r["status"]: r["cnt"] for r in rows}


def get_pipeline_status(conn: sqlite3.Connection) -> list:
    """Get pipeline phase statuses."""
    return safe_query(conn, """
        SELECT phase_id, phase_name, status, progress, updated_at
        FROM pipeline_registry
        ORDER BY phase_id
    """)


def get_system_health(conn: sqlite3.Connection) -> list:
    """Get recent system health log entries."""
    return safe_query(conn, """
        SELECT component, status, details, checked_at
        FROM system_health_log
        ORDER BY checked_at DESC
        LIMIT 10
    """)


def get_critical_facts(conn: sqlite3.Connection, limit: int = 10) -> list:
    """Get critical facts from the immutable facts table."""
    return safe_query(conn, """
        SELECT fact_id, category, fact_text, source, verified
        FROM critical_facts
        ORDER BY fact_id
        LIMIT ?
    """, (limit,))


def scan_session_folders() -> list:
    """Scan ~/.copilot/session-state/ for session folders."""
    sessions = []
    if SESSION_STATE_DIR.exists():
        for d in sorted(SESSION_STATE_DIR.iterdir(), reverse=True):
            if d.is_dir() and len(d.name) > 20:  # UUID-like names
                plan_file = d / "plan.md"
                has_plan = plan_file.exists()
                plan_size = plan_file.stat().st_size if has_plan else 0

                checkpoints_dir = d / "checkpoints"
                checkpoint_count = 0
                if checkpoints_dir.exists():
                    checkpoint_count = len(list(checkpoints_dir.glob("*.md")))

                sessions.append({
                    "id": d.name,
                    "has_plan": has_plan,
                    "plan_size_kb": round(plan_size / 1024, 1),
                    "checkpoints": checkpoint_count,
                    "modified": datetime.fromtimestamp(d.stat().st_mtime).isoformat(),
                })
    return sessions


def format_recent(conn: sqlite3.Connection) -> str:
    """Format recent session context for human reading."""
    sep_days = (date.today() - LAST_CONTACT).days
    lines = []
    lines.append("# 📋 SESSION RECALL — LitigationOS")
    lines.append(f"**Date:** {date.today().isoformat()}")
    lines.append(f"**Separation from L.D.W.:** {sep_days} days ({round(sep_days/30.44, 1)} months)")
    lines.append("")

    # Session handoffs
    handoffs = get_session_handoffs(conn, 3)
    if handoffs:
        lines.append("## 🔄 RECENT SESSION HANDOFFS")
        lines.append("")
        for h in handoffs:
            lines.append(f"### Session: {h.get('session_id', 'unknown')}")
            lines.append(f"**Date:** {h.get('created_at', 'unknown')}")
            if h.get("work_completed"):
                lines.append(f"**Completed:** {h['work_completed'][:500]}")
            if h.get("work_pending"):
                lines.append(f"**Pending:** {h['work_pending'][:500]}")
            if h.get("handoff_notes"):
                lines.append(f"**Notes:** {h['handoff_notes'][:300]}")
            lines.append("")
    else:
        lines.append("## 🔄 SESSION HANDOFFS")
        lines.append("No session handoff records found in DB.")
        lines.append("")

    # Master todos (active work)
    todos = get_master_todos(conn)
    active = [t for t in todos if t.get("status") in ("IN_PROGRESS", "PENDING")]
    if active:
        lines.append("## 📝 ACTIVE WORK ITEMS")
        lines.append("")
        lines.append("| ID | Title | Status | Progress |")
        lines.append("|----|-------|--------|----------|")
        for t in active[:10]:
            lines.append(f"| {t.get('id', '?')} | {t.get('title', '?')} | {t.get('status', '?')} | {t.get('progress', '?')} |")
        lines.append("")

    # Filing readiness
    filings = get_filing_readiness(conn)
    if filings:
        lines.append("## 📁 FILING READINESS")
        lines.append("")
        lines.append("| Vehicle | Lane | Status | Score | Deadline |")
        lines.append("|---------|------|--------|-------|----------|")
        for f in filings[:10]:
            dl = f.get("deadline_date") or "—"
            lines.append(f"| {f['vehicle_name']} | {f['lane']} | {f['status']} | {f.get('confidence_score', 0)} | {dl} |")
        lines.append("")

    # Convergence
    conv = get_convergence_summary(conn)
    if conv:
        lines.append("## 🟢 CONVERGENCE STATUS")
        lines.append("")
        for status, cnt in conv.items():
            emoji = "🟢" if status == "GREEN" else "🟡" if status == "YELLOW" else "🔴"
            lines.append(f"- {emoji} **{status}**: {cnt} domains")
        lines.append("")

    # Session folders
    sessions = scan_session_folders()
    if sessions:
        lines.append(f"## 📂 COPILOT SESSIONS ({len(sessions)} found)")
        lines.append("")
        lines.append("| Session ID | Checkpoints | Plan Size | Last Modified |")
        lines.append("|-----------|-------------|-----------|---------------|")
        for s in sessions[:8]:
            sid = s["id"][:12] + "..."
            lines.append(f"| {sid} | {s['checkpoints']} | {s['plan_size_kb']} KB | {s['modified'][:16]} |")
        lines.append("")

    lines.append("---")
    lines.append(f"*Generated by session_recall.py at {datetime.now().isoformat()}*")
    return "\n".join(lines)


def format_search(conn: sqlite3.Connection, query: str) -> str:
    """Search across session artifacts for a query."""
    lines = []
    lines.append(f"# 🔍 SESSION SEARCH: '{query}'")
    lines.append("")

    # Search handoffs
    handoffs = safe_query(conn, """
        SELECT session_id, work_completed, work_pending, handoff_notes, created_at
        FROM session_handoff
        WHERE work_completed LIKE ? OR work_pending LIKE ? OR handoff_notes LIKE ?
        ORDER BY created_at DESC
        LIMIT 10
    """, (f"%{query}%", f"%{query}%", f"%{query}%"))

    if handoffs:
        lines.append(f"## Handoff Records ({len(handoffs)} matches)")
        for h in handoffs:
            lines.append(f"- **{h.get('created_at', '?')}** — {h.get('work_completed', '')[:200]}")
        lines.append("")

    # Search todos
    todos = safe_query(conn, """
        SELECT id, title, status, description
        FROM master_todos
        WHERE title LIKE ? OR description LIKE ?
        LIMIT 10
    """, (f"%{query}%", f"%{query}%"))

    if todos:
        lines.append(f"## Todos ({len(todos)} matches)")
        for t in todos:
            lines.append(f"- [{t.get('status', '?')}] {t.get('title', '?')}")
        lines.append("")

    if not handoffs and not todos:
        lines.append("No matches found in session data.")
        lines.append("")

    return "\n".join(lines)


def format_stats(conn: sqlite3.Connection) -> str:
    """Session statistics summary."""
    lines = []
    lines.append("# 📊 SESSION STATISTICS")
    lines.append("")

    sessions = scan_session_folders()
    total_checkpoints = sum(s["checkpoints"] for s in sessions)
    lines.append(f"- **Total sessions:** {len(sessions)}")
    lines.append(f"- **Total checkpoints:** {total_checkpoints}")
    lines.append(f"- **Sessions with plans:** {sum(1 for s in sessions if s['has_plan'])}")
    lines.append("")

    handoff_count = safe_query(conn, "SELECT COUNT(*) as cnt FROM session_handoff")
    if handoff_count:
        lines.append(f"- **Handoff records:** {handoff_count[0].get('cnt', 0)}")

    todo_stats = safe_query(conn, """
        SELECT status, COUNT(*) as cnt FROM master_todos GROUP BY status
    """)
    if todo_stats:
        lines.append("- **Todos:**")
        for t in todo_stats:
            lines.append(f"  - {t['status']}: {t['cnt']}")

    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print("Usage: python session_recall.py {recent|search <query>|handoff|stats} [--json]")
        sys.exit(1)

    command = sys.argv[1]
    use_json = "--json" in sys.argv

    conn = get_db_connection()
    try:
        if command == "recent":
            if use_json:
                data = {
                    "handoffs": get_session_handoffs(conn, 5),
                    "todos": get_master_todos(conn),
                    "filings": get_filing_readiness(conn),
                    "convergence": get_convergence_summary(conn),
                    "sessions": scan_session_folders()[:10],
                    "separation_days": (date.today() - LAST_CONTACT).days,
                }
                print(json.dumps(data, indent=2, default=str))
            else:
                print(format_recent(conn))

        elif command == "search" and len(sys.argv) > 2:
            query = " ".join(sys.argv[2:]).replace("--json", "").strip()
            if use_json:
                handoffs = safe_query(conn, """
                    SELECT * FROM session_handoff
                    WHERE work_completed LIKE ? OR work_pending LIKE ?
                    ORDER BY created_at DESC LIMIT 10
                """, (f"%{query}%", f"%{query}%"))
                print(json.dumps({"query": query, "results": handoffs}, indent=2, default=str))
            else:
                print(format_search(conn, query))

        elif command == "handoff":
            handoffs = get_session_handoffs(conn, 1)
            if use_json:
                print(json.dumps(handoffs, indent=2, default=str))
            elif handoffs:
                h = handoffs[0]
                print(f"Last Session: {h.get('session_id', 'unknown')}")
                print(f"Date: {h.get('created_at', 'unknown')}")
                print(f"Completed: {h.get('work_completed', 'N/A')}")
                print(f"Pending: {h.get('work_pending', 'N/A')}")
                print(f"Notes: {h.get('handoff_notes', 'N/A')}")
            else:
                print("No session handoff records found.")

        elif command == "stats":
            if use_json:
                sessions = scan_session_folders()
                print(json.dumps({
                    "sessions": len(sessions),
                    "checkpoints": sum(s["checkpoints"] for s in sessions),
                    "with_plans": sum(1 for s in sessions if s["has_plan"]),
                }, indent=2))
            else:
                print(format_stats(conn))

        else:
            print(f"Unknown command: {command}")
            print("Usage: python session_recall.py {recent|search <query>|handoff|stats} [--json]")
            sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
