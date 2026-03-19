#!/usr/bin/env python3
"""
MBP LitigationOS -- Deadline Monitor Skill
============================================
Calendar and alert system for litigation deadlines.
Checks deadlines table on every invocation and warns about upcoming/overdue items.

JSON-RPC methods: check_deadlines, add_deadline, update_deadline, deadline_report

Usage:
    from skills.deadline_monitor import DeadlineMonitor
    m = DeadlineMonitor()
    result = m.check_deadlines()

CLI:
    python deadline_monitor.py check
    python deadline_monitor.py add --case 2024-001507-DC --title "Response Due" --due 2026-04-15 --authority "MCR 2.119"
    python deadline_monitor.py update --id 5 --status completed
    python deadline_monitor.py report
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(
    0,
    str(
        Path(__file__).resolve().parent.parent
        if "skills" in str(Path(__file__))
        else Path(__file__).resolve().parent
    ),
)
try:
    from cycle_method import cycle_json, cycle_print
except ImportError:
    cycle_json = lambda obj, **kw: print(json.dumps(obj, default=str, indent=2))
    cycle_print = print

DB_PATH = os.environ.get(
    "LITIGATION_DB_PATH",
    r"C:\Users\andre\LitigationOS\litigation_context.db",
)

# ── Separation tracker ───────────────────────────────────────────────
SEPARATION_START = datetime(2025, 8, 8)

# ── Known critical deadlines (fallback if DB table empty) ────────────
KNOWN_DEADLINES = [
    {
        "case_id": "366810",
        "title": "COA Appellant Brief Due",
        "due_date_iso": "2026-04-15",
        "basis": "MCR 7.212(A)(1) — appellant brief due within 56 days of claim",
        "authority": "MCR 7.212(A)(1)",
        "risk": "JURISDICTIONAL — failure = dismissal",
        "lane": "F",
    },
    {
        "case_id": "2023-5907-PP",
        "title": "PPO Renewal/Challenge Deadline",
        "due_date_iso": "2026-06-01",
        "basis": "MCL 600.2950(1) — PPO duration and renewal",
        "authority": "MCL 600.2950",
        "risk": "HIGH — affects custody proceedings",
        "lane": "D",
    },
    {
        "case_id": "JTC-2026",
        "title": "JTC Complaint Follow-Up",
        "due_date_iso": "2026-05-01",
        "basis": "Follow up on filed JTC complaint for status",
        "authority": "MCR 9.220",
        "risk": "MEDIUM — independent track",
        "lane": "E",
    },
    {
        "case_id": "2024-001507-DC",
        "title": "ONGOING: Parent-Child Separation",
        "due_date_iso": None,
        "basis": f"567+ days since Aug 8, 2025 — constitutional violation ongoing",
        "authority": "XIV Amendment; Troxel v Granville, 530 US 57 (2000)",
        "risk": "EMERGENCY — fundamental right being violated daily",
        "lane": "A",
    },
]


# ── DeadlineMonitor ──────────────────────────────────────────────────

class DeadlineMonitor:
    """Monitors and manages litigation deadlines with auto-alerts."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    def _get_conn(self, readonly: bool = True) -> Optional[sqlite3.Connection]:
        try:
            conn = sqlite3.connect(self.db_path, timeout=30)
            conn.execute("PRAGMA journal_mode=WAL")
            if readonly:
                conn.execute("PRAGMA query_only=ON")
            conn.row_factory = sqlite3.Row
            return conn
        except Exception:
            return None

    def _get_write_conn(self) -> Optional[sqlite3.Connection]:
        return self._get_conn(readonly=False)

    def _ensure_table(self, conn: sqlite3.Connection) -> bool:
        """Ensure deadlines table exists with expected schema."""
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS deadlines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    case_id TEXT,
                    title TEXT NOT NULL,
                    due_date_iso TEXT,
                    basis TEXT,
                    authority TEXT,
                    risk TEXT DEFAULT 'MEDIUM',
                    lane TEXT,
                    status TEXT DEFAULT 'active',
                    created_at TEXT DEFAULT (datetime('now')),
                    updated_at TEXT DEFAULT (datetime('now')),
                    notes TEXT
                )
            """)
            conn.commit()
            return True
        except Exception:
            return False

    def _categorize_deadline(self, due_date_iso: Optional[str]) -> Dict[str, Any]:
        """Categorize a deadline by urgency."""
        if not due_date_iso:
            return {"category": "ONGOING", "days_remaining": None, "alert_level": "EMERGENCY"}

        try:
            due = datetime.strptime(due_date_iso, "%Y-%m-%d")
        except ValueError:
            try:
                due = datetime.fromisoformat(due_date_iso)
            except ValueError:
                return {"category": "UNKNOWN", "days_remaining": None, "alert_level": "INFO"}

        now = datetime.now()
        delta = (due - now).days

        if delta < 0:
            return {"category": "OVERDUE", "days_remaining": delta, "alert_level": "CRITICAL"}
        elif delta <= 7:
            return {"category": "CRITICAL", "days_remaining": delta, "alert_level": "CRITICAL"}
        elif delta <= 30:
            return {"category": "UPCOMING", "days_remaining": delta, "alert_level": "WARNING"}
        else:
            return {"category": "FUTURE", "days_remaining": delta, "alert_level": "INFO"}

    def _separation_days(self) -> int:
        """Calculate days of parent-child separation since Aug 8, 2025."""
        return (datetime.now() - SEPARATION_START).days

    def check_deadlines(self) -> Dict[str, Any]:
        """Query deadlines table and return categorized results.

        Categories:
            OVERDUE — past due_date_iso
            CRITICAL — within 7 days
            UPCOMING — within 30 days
            FUTURE — beyond 30 days
            ONGOING — no end date (e.g., separation)

        Returns:
            Structured report with all deadlines categorized.
        """
        overdue = []
        critical = []
        upcoming = []
        future = []
        ongoing = []

        db_deadlines = []
        conn = self._get_conn()
        if conn:
            try:
                rows = conn.execute(
                    "SELECT * FROM deadlines WHERE status != 'completed' "
                    "ORDER BY due_date_iso ASC NULLS LAST"
                ).fetchall()
                db_deadlines = [dict(r) for r in rows]
            except Exception:
                # Table might not exist yet — use known deadlines
                pass
            finally:
                conn.close()

        # Merge with known deadlines if DB is empty
        all_deadlines = db_deadlines if db_deadlines else KNOWN_DEADLINES

        for dl in all_deadlines:
            due = dl.get("due_date_iso")
            cat = self._categorize_deadline(due)
            entry = {
                "id": dl.get("id"),
                "case_id": dl.get("case_id", ""),
                "title": dl.get("title", ""),
                "due_date": due,
                "basis": dl.get("basis", ""),
                "authority": dl.get("authority", ""),
                "risk": dl.get("risk", "MEDIUM"),
                "lane": dl.get("lane", ""),
                "status": dl.get("status", "active"),
                "days_remaining": cat["days_remaining"],
                "alert_level": cat["alert_level"],
            }

            if cat["category"] == "OVERDUE":
                overdue.append(entry)
            elif cat["category"] == "CRITICAL":
                critical.append(entry)
            elif cat["category"] == "UPCOMING":
                upcoming.append(entry)
            elif cat["category"] == "ONGOING":
                ongoing.append(entry)
            else:
                future.append(entry)

        # Always include separation alert
        sep_days = self._separation_days()
        sep_entry = {
            "id": None,
            "case_id": "2024-001507-DC",
            "title": f"EMERGENCY: Parent-Child Separation — Day {sep_days}",
            "due_date": None,
            "basis": f"{sep_days} days since Aug 8, 2025 — constitutional violation ongoing",
            "authority": "XIV Amendment; Troxel v Granville, 530 US 57 (2000); MCL 722.27a",
            "risk": "EMERGENCY — fundamental right being violated daily",
            "lane": "A",
            "status": "active",
            "days_remaining": None,
            "alert_level": "EMERGENCY",
        }
        # Avoid duplicate if already in ongoing
        if not any(e.get("title", "").startswith("ONGOING: Parent-Child") or
                    e.get("title", "").startswith("EMERGENCY: Parent-Child")
                    for e in ongoing):
            ongoing.insert(0, sep_entry)

        total = len(overdue) + len(critical) + len(upcoming) + len(future) + len(ongoing)
        alerts = len(overdue) + len(critical) + len(ongoing)

        return {
            "status": "ALERT" if alerts > 0 else "OK",
            "summary": {
                "total_active": total,
                "overdue": len(overdue),
                "critical": len(critical),
                "upcoming": len(upcoming),
                "future": len(future),
                "ongoing": len(ongoing),
                "separation_days": sep_days,
            },
            "overdue": overdue,
            "critical": critical,
            "upcoming": upcoming,
            "future": future,
            "ongoing": ongoing,
            "checked_at": datetime.now().isoformat(),
        }

    def add_deadline(
        self,
        case_id: str,
        title: str,
        due_date: str,
        basis: str = "",
        authority: str = "",
        risk: str = "MEDIUM",
        lane: str = "",
        notes: str = "",
    ) -> Dict[str, Any]:
        """Insert a new deadline into the deadlines table.

        Args:
            case_id: Case number (e.g., '2024-001507-DC')
            title: Descriptive title of the deadline
            due_date: ISO date string (YYYY-MM-DD)
            basis: Legal basis for the deadline
            authority: Court rule citation
            risk: Risk level (LOW/MEDIUM/HIGH/CRITICAL/JURISDICTIONAL)
            lane: Case lane (A-G)
            notes: Additional notes

        Returns:
            Confirmation with inserted deadline info.
        """
        conn = self._get_write_conn()
        if not conn:
            return {"error": "Cannot connect to database", "success": False}

        self._ensure_table(conn)

        try:
            cursor = conn.execute(
                """INSERT INTO deadlines
                   (case_id, title, due_date_iso, basis, authority, risk, lane, status, notes)
                   VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?)""",
                (case_id, title, due_date, basis, authority, risk, lane, notes),
            )
            conn.commit()
            new_id = cursor.lastrowid

            cat = self._categorize_deadline(due_date)
            conn.close()

            return {
                "success": True,
                "id": new_id,
                "case_id": case_id,
                "title": title,
                "due_date": due_date,
                "category": cat["category"],
                "days_remaining": cat["days_remaining"],
                "alert_level": cat["alert_level"],
            }
        except Exception as e:
            conn.close()
            return {"error": str(e), "success": False}

    def update_deadline(
        self,
        deadline_id: int,
        status: str = "completed",
        notes: str = "",
    ) -> Dict[str, Any]:
        """Update a deadline's status.

        Args:
            deadline_id: ID of the deadline to update
            status: New status (active/completed/waived/extended)
            notes: Additional notes about the update

        Returns:
            Confirmation with updated deadline info.
        """
        valid_statuses = ("active", "completed", "waived", "extended", "missed")
        if status not in valid_statuses:
            return {
                "error": f"Invalid status '{status}'. Valid: {', '.join(valid_statuses)}",
                "success": False,
            }

        conn = self._get_write_conn()
        if not conn:
            return {"error": "Cannot connect to database", "success": False}

        try:
            update_fields = "status = ?, updated_at = datetime('now')"
            params: list = [status]
            if notes:
                update_fields += ", notes = COALESCE(notes, '') || ? "
                params.append(f"\n[{datetime.now().strftime('%Y-%m-%d')}] {notes}")
            params.append(deadline_id)

            conn.execute(
                f"UPDATE deadlines SET {update_fields} WHERE id = ?",
                params,
            )
            conn.commit()

            row = conn.execute(
                "SELECT * FROM deadlines WHERE id = ?", (deadline_id,)
            ).fetchone()
            conn.close()

            if row:
                return {
                    "success": True,
                    "id": deadline_id,
                    "title": row["title"],
                    "status": status,
                    "updated_at": datetime.now().isoformat(),
                }
            return {"error": f"Deadline {deadline_id} not found", "success": False}
        except Exception as e:
            conn.close()
            return {"error": str(e), "success": False}

    def deadline_report(self) -> Dict[str, Any]:
        """Generate a formatted deadline report with days remaining.

        Returns:
            Comprehensive report with all deadlines, status, and alerts.
        """
        data = self.check_deadlines()
        sep_days = self._separation_days()

        lines = []
        lines.append("=" * 72)
        lines.append("  LITIGATION DEADLINE REPORT")
        lines.append(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append(f"  Parent-Child Separation: DAY {sep_days}")
        lines.append("=" * 72)

        def _format_section(title: str, items: list, icon: str):
            if not items:
                return
            lines.append("")
            lines.append(f"  {icon} {title} ({len(items)})")
            lines.append("  " + "-" * 60)
            for item in items:
                days = item.get("days_remaining")
                if days is not None and days < 0:
                    days_str = f"OVERDUE by {abs(days)} days"
                elif days is not None:
                    days_str = f"{days} days remaining"
                else:
                    days_str = "ONGOING"
                lines.append(f"    [{item.get('lane', '?')}] {item['title']}")
                lines.append(f"        Due: {item.get('due_date', 'N/A')} — {days_str}")
                lines.append(f"        Authority: {item.get('authority', 'N/A')}")
                lines.append(f"        Risk: {item.get('risk', 'N/A')}")
                lines.append("")

        _format_section("ONGOING EMERGENCIES", data.get("ongoing", []), "🚨")
        _format_section("OVERDUE", data.get("overdue", []), "❌")
        _format_section("CRITICAL (≤7 days)", data.get("critical", []), "⚠️")
        _format_section("UPCOMING (≤30 days)", data.get("upcoming", []), "📅")
        _format_section("FUTURE (>30 days)", data.get("future", []), "📋")

        lines.append("")
        lines.append("=" * 72)
        s = data.get("summary", {})
        lines.append(f"  TOTALS: {s.get('total_active', 0)} active | "
                      f"{s.get('overdue', 0)} overdue | "
                      f"{s.get('critical', 0)} critical | "
                      f"{s.get('ongoing', 0)} ongoing")
        lines.append("=" * 72)

        report_text = "\n".join(lines)

        return {
            "report": report_text,
            "data": data,
            "separation_days": sep_days,
            "generated_at": datetime.now().isoformat(),
        }


# ── Module-level convenience functions (for JSON-RPC dispatch) ───────

_monitor = None

def _get_monitor() -> DeadlineMonitor:
    global _monitor
    if _monitor is None:
        _monitor = DeadlineMonitor()
    return _monitor

def check_deadlines() -> Dict[str, Any]:
    """JSON-RPC: check_deadlines — Query and categorize all active deadlines."""
    return _get_monitor().check_deadlines()

def add_deadline(
    case_id: str,
    title: str,
    due_date: str,
    basis: str = "",
    authority: str = "",
    risk: str = "MEDIUM",
    lane: str = "",
    notes: str = "",
) -> Dict[str, Any]:
    """JSON-RPC: add_deadline — Insert a new deadline."""
    return _get_monitor().add_deadline(case_id, title, due_date, basis, authority, risk, lane, notes)

def update_deadline(deadline_id: int, status: str = "completed", notes: str = "") -> Dict[str, Any]:
    """JSON-RPC: update_deadline — Update a deadline's status."""
    return _get_monitor().update_deadline(deadline_id, status, notes)

def deadline_report() -> Dict[str, Any]:
    """JSON-RPC: deadline_report — Generate formatted deadline report."""
    return _get_monitor().deadline_report()


# ── CLI ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Deadline Monitor — Calendar and Alert System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python deadline_monitor.py check
  python deadline_monitor.py report
  python deadline_monitor.py add --case 2024-001507-DC --title "Motion Response Due" --due 2026-04-20 --authority "MCR 2.119(C)(1)" --risk HIGH
  python deadline_monitor.py update --id 5 --status completed --notes "Filed on time"
        """,
    )
    sub = parser.add_subparsers(dest="command", help="Command to run")

    # check
    sub.add_parser("check", help="Check all active deadlines")

    # report
    sub.add_parser("report", help="Generate formatted deadline report")

    # add
    p_add = sub.add_parser("add", help="Add a new deadline")
    p_add.add_argument("--case", required=True, help="Case ID")
    p_add.add_argument("--title", required=True, help="Deadline title")
    p_add.add_argument("--due", required=True, help="Due date (YYYY-MM-DD)")
    p_add.add_argument("--basis", default="", help="Legal basis")
    p_add.add_argument("--authority", default="", help="Court rule citation")
    p_add.add_argument("--risk", default="MEDIUM",
                        choices=["LOW", "MEDIUM", "HIGH", "CRITICAL", "JURISDICTIONAL"],
                        help="Risk level")
    p_add.add_argument("--lane", default="", help="Case lane (A-G)")
    p_add.add_argument("--notes", default="", help="Additional notes")

    # update
    p_upd = sub.add_parser("update", help="Update a deadline status")
    p_upd.add_argument("--id", required=True, type=int, help="Deadline ID")
    p_upd.add_argument("--status", required=True,
                        choices=["active", "completed", "waived", "extended", "missed"],
                        help="New status")
    p_upd.add_argument("--notes", default="", help="Update notes")

    args = parser.parse_args()

    if args.command == "check":
        result = check_deadlines()
        cycle_json(result)
    elif args.command == "report":
        result = deadline_report()
        # Print the formatted report text directly
        print(result.get("report", ""))
    elif args.command == "add":
        result = add_deadline(
            case_id=args.case,
            title=args.title,
            due_date=args.due,
            basis=args.basis,
            authority=args.authority,
            risk=args.risk,
            lane=args.lane,
            notes=args.notes,
        )
        cycle_json(result)
    elif args.command == "update":
        result = update_deadline(
            deadline_id=args.id,
            status=args.status,
            notes=args.notes,
        )
        cycle_json(result)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
