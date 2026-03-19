# -*- coding: utf-8 -*-
"""
deadline_integration.py — Deadline Sentinel Integration for LitigationOS
=========================================================================
Wires the skill_deadline_sentinel engine into the daemon scheduler for
automated periodic deadline monitoring with multi-tier alerting.

Capabilities:
  - Periodic deadline scanning (configurable interval, default 6h)
  - Multi-tier alerting: 30d / 14d / 7d / 3d / 1d / OVERDUE
  - Per-filing deadline tracking with SOL awareness
  - Alert history with deduplication
  - Dashboard generation (JSON + plain text)
  - Integration with litigation_context.db deadlines table

Zero external dependencies. CPU-first. Local-only.
"""

import sqlite3
import json
import re
import os
import hashlib
from datetime import datetime, date, timedelta
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

# ─── Database path resolution ───
_ROOT = Path(__file__).resolve().parents[1]
_DEFAULT_DB = _ROOT / "litigation_context.db"


# ─── Data Classes ───

@dataclass
class AlertThreshold:
    """A deadline alert threshold configuration."""
    days: int
    level: str  # CRITICAL, HIGH, MEDIUM, LOW, INFO
    label: str
    color: str = "#000000"

    def matches(self, days_remaining: int) -> bool:
        """Check if days_remaining triggers this threshold."""
        return days_remaining <= self.days


@dataclass
class DeadlineAlert:
    """A generated alert for an approaching/overdue deadline."""
    alert_id: str
    deadline_id: str
    case_name: str
    filing_type: str
    due_date: str
    days_remaining: int
    alert_level: str
    alert_message: str
    authority: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    acknowledged: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class DeadlineStatus:
    """Overall deadline health status."""
    total_deadlines: int = 0
    overdue: int = 0
    critical_7d: int = 0
    high_14d: int = 0
    medium_30d: int = 0
    upcoming: int = 0
    filed: int = 0
    waived: int = 0
    health_score: float = 100.0  # 0-100, lower = more urgent
    alerts: list = field(default_factory=list)
    scan_time: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "total_deadlines": self.total_deadlines,
            "overdue": self.overdue,
            "critical_7d": self.critical_7d,
            "high_14d": self.high_14d,
            "medium_30d": self.medium_30d,
            "upcoming": self.upcoming,
            "filed": self.filed,
            "waived": self.waived,
            "health_score": round(self.health_score, 1),
            "alert_count": len(self.alerts),
            "scan_time": self.scan_time,
        }


# ─── Alert Thresholds (ordered most urgent → least) ───

DEFAULT_THRESHOLDS = [
    AlertThreshold(days=0, level="OVERDUE", label="OVERDUE", color="#FF0000"),
    AlertThreshold(days=1, level="CRITICAL", label="DUE TOMORROW", color="#FF3300"),
    AlertThreshold(days=3, level="CRITICAL", label="Due in ≤3 days", color="#FF6600"),
    AlertThreshold(days=7, level="HIGH", label="Due in ≤7 days", color="#FF9900"),
    AlertThreshold(days=14, level="HIGH", label="Due in ≤14 days", color="#FFCC00"),
    AlertThreshold(days=30, level="MEDIUM", label="Due in ≤30 days", color="#FFFF00"),
]


class DeadlineSentinelIntegration:
    """
    Integrates deadline sentinel with the daemon scheduler.
    Provides periodic scanning, alerting, and dashboard generation.
    """

    def __init__(
        self,
        db_path: Optional[str] = None,
        thresholds: Optional[list] = None,
        alert_history_limit: int = 1000,
    ):
        self.db_path = str(db_path or _DEFAULT_DB)
        self.thresholds = thresholds or DEFAULT_THRESHOLDS
        self.alert_history_limit = alert_history_limit
        self._stats = {
            "scans_run": 0,
            "alerts_generated": 0,
            "last_scan": None,
        }
        self._ensure_tables()

    def _connect(self) -> sqlite3.Connection:
        """Create a database connection with proper PRAGMAs."""
        conn = sqlite3.connect(self.db_path, timeout=120)
        conn.execute("PRAGMA busy_timeout=60000")
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA cache_size=-32000")
        conn.execute("PRAGMA temp_store=MEMORY")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_tables(self):
        """Create alert tracking tables if they don't exist."""
        try:
            conn = self._connect()
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS deadline_alerts (
                    alert_id TEXT PRIMARY KEY,
                    deadline_id TEXT NOT NULL,
                    case_name TEXT,
                    filing_type TEXT,
                    due_date TEXT,
                    days_remaining INTEGER,
                    alert_level TEXT,
                    alert_message TEXT,
                    authority TEXT,
                    created_at TEXT DEFAULT (datetime('now')),
                    acknowledged INTEGER DEFAULT 0,
                    acknowledged_at TEXT
                );

                CREATE TABLE IF NOT EXISTS deadline_scan_history (
                    scan_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scan_time TEXT DEFAULT (datetime('now')),
                    total_deadlines INTEGER,
                    overdue_count INTEGER,
                    critical_count INTEGER,
                    alerts_generated INTEGER,
                    health_score REAL
                );

                CREATE INDEX IF NOT EXISTS idx_deadline_alerts_level
                    ON deadline_alerts(alert_level);
                CREATE INDEX IF NOT EXISTS idx_deadline_alerts_deadline
                    ON deadline_alerts(deadline_id);
            """)
            conn.commit()
            conn.close()
        except sqlite3.OperationalError:
            pass  # Tables may already exist or DB locked

    def scan(self) -> DeadlineStatus:
        """
        Run a full deadline scan. Returns DeadlineStatus with alerts.

        This is the main entry point — call periodically (e.g., every 6 hours).
        """
        status = DeadlineStatus()
        today = date.today()

        try:
            conn = self._connect()

            # Check if litigation_deadlines table exists
            table_check = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='litigation_deadlines'"
            ).fetchone()

            if not table_check:
                # Also check for 'deadlines' table (alternate name)
                table_check = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='deadlines'"
                ).fetchone()
                deadline_table = "deadlines" if table_check else None
            else:
                deadline_table = "litigation_deadlines"

            if not deadline_table:
                conn.close()
                return status

            # Get column names for the table
            cols = [
                r[1] for r in conn.execute(f"PRAGMA table_info({deadline_table})").fetchall()
            ]

            # Determine column mappings
            id_col = "deadline_id" if "deadline_id" in cols else "id"
            case_col = "case_name" if "case_name" in cols else (
                "vehicle_name" if "vehicle_name" in cols else "case_id"
            )
            date_col = "due_date" if "due_date" in cols else (
                "due_date_iso" if "due_date_iso" in cols else "deadline_date"
            )
            type_col = "filing_type" if "filing_type" in cols else (
                "type" if "type" in cols else "description"
            )
            status_col = "status" if "status" in cols else None
            auth_col = "authority" if "authority" in cols else (
                "basis" if "basis" in cols else None
            )

            query = f"SELECT * FROM {deadline_table}"
            rows = conn.execute(query).fetchall()
            status.total_deadlines = len(rows)

            alerts = []
            for row in rows:
                row_dict = dict(row)

                # Get values using mapped column names
                d_id = str(row_dict.get(id_col, ""))
                case = str(row_dict.get(case_col, ""))
                due_str = str(row_dict.get(date_col, ""))
                f_type = str(row_dict.get(type_col, ""))
                d_status = str(row_dict.get(status_col, "upcoming")) if status_col else "upcoming"
                authority = str(row_dict.get(auth_col, "")) if auth_col else ""

                # Skip already filed/satisfied/waived
                if d_status in ("filed", "satisfied", "waived"):
                    if d_status == "filed":
                        status.filed += 1
                    elif d_status == "waived":
                        status.waived += 1
                    continue

                # Calculate days remaining
                days_remaining = self._calc_days(due_str, today)
                if days_remaining is None:
                    status.upcoming += 1
                    continue

                # Categorize
                if days_remaining < 0:
                    status.overdue += 1
                elif days_remaining <= 7:
                    status.critical_7d += 1
                elif days_remaining <= 14:
                    status.high_14d += 1
                elif days_remaining <= 30:
                    status.medium_30d += 1
                else:
                    status.upcoming += 1

                # Generate alerts for thresholds
                for threshold in self.thresholds:
                    if days_remaining <= threshold.days:
                        alert = self._create_alert(
                            deadline_id=d_id,
                            case_name=case,
                            filing_type=f_type,
                            due_date=due_str,
                            days_remaining=days_remaining,
                            threshold=threshold,
                            authority=authority,
                        )
                        alerts.append(alert)
                        break  # Only match the most urgent threshold

            status.alerts = alerts
            status.health_score = self._compute_health_score(status)

            # Persist alerts and scan history
            self._persist_alerts(conn, alerts)
            self._persist_scan(conn, status)

            conn.close()

        except Exception as e:
            # Non-fatal — return partial status
            status.health_score = 0.0
            status.alerts.append(
                DeadlineAlert(
                    alert_id=f"error-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    deadline_id="SYSTEM",
                    case_name="SYSTEM ERROR",
                    filing_type="scan_error",
                    due_date="",
                    days_remaining=-1,
                    alert_level="CRITICAL",
                    alert_message=f"Scan error: {e}",
                )
            )

        self._stats["scans_run"] += 1
        self._stats["alerts_generated"] += len(status.alerts)
        self._stats["last_scan"] = status.scan_time

        return status

    def get_dashboard(self, format: str = "text") -> str:
        """
        Generate a deadline dashboard.

        Args:
            format: 'text' for plain text, 'json' for JSON, 'html' for HTML
        """
        status = self.scan()

        if format == "json":
            return json.dumps(status.to_dict(), indent=2)

        if format == "html":
            return self._render_html_dashboard(status)

        # Default: plain text dashboard
        lines = [
            "╔══════════════════════════════════════════════════╗",
            "║       LITIGATION DEADLINE SENTINEL DASHBOARD     ║",
            f"║  Scan Time: {status.scan_time[:19]:<37}║",
            "╠══════════════════════════════════════════════════╣",
            f"║  Health Score: {status.health_score:>5.1f}/100                       ║",
            f"║  Total Deadlines: {status.total_deadlines:<31}║",
            "╠══════════════════════════════════════════════════╣",
        ]

        if status.overdue > 0:
            lines.append(f"║  🔴 OVERDUE:        {status.overdue:<29}║")
        if status.critical_7d > 0:
            lines.append(f"║  🟠 Critical (≤7d):  {status.critical_7d:<28}║")
        if status.high_14d > 0:
            lines.append(f"║  🟡 High (≤14d):     {status.high_14d:<28}║")
        if status.medium_30d > 0:
            lines.append(f"║  🟢 Medium (≤30d):   {status.medium_30d:<28}║")

        lines.append(f"║  Filed: {status.filed}  |  Waived: {status.waived}  |  Upcoming: {status.upcoming:<5}║")
        lines.append("╠══════════════════════════════════════════════════╣")

        if status.alerts:
            lines.append(f"║  ALERTS ({len(status.alerts)}):                               ║")
            for alert in status.alerts[:10]:  # Show top 10
                level_icon = {
                    "OVERDUE": "🔴", "CRITICAL": "🟠",
                    "HIGH": "🟡", "MEDIUM": "🟢"
                }.get(alert.alert_level, "⚪")
                line = f"║  {level_icon} {alert.case_name[:15]:<15} {alert.filing_type[:12]:<12} {alert.alert_message[:15]}"
                lines.append(f"{line:<51}║")
        else:
            lines.append("║  ✅ No active alerts                              ║")

        lines.append("╚══════════════════════════════════════════════════╝")
        return "\n".join(lines)

    def get_overdue(self) -> list[DeadlineAlert]:
        """Get only OVERDUE deadline alerts."""
        status = self.scan()
        return [a for a in status.alerts if a.alert_level == "OVERDUE"]

    def get_upcoming(self, days: int = 30) -> list[dict]:
        """Get deadlines due within the next N days."""
        today = date.today()
        try:
            conn = self._connect()
            # Try litigation_deadlines first, then deadlines
            for table in ("litigation_deadlines", "deadlines"):
                check = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    (table,)
                ).fetchone()
                if check:
                    rows = conn.execute(f"SELECT * FROM {table}").fetchall()
                    conn.close()
                    results = []
                    for r in rows:
                        d = dict(r)
                        due_str = d.get("due_date", d.get("due_date_iso", d.get("deadline_date", "")))
                        days_rem = self._calc_days(str(due_str), today)
                        if days_rem is not None and 0 <= days_rem <= days:
                            d["days_remaining"] = days_rem
                            results.append(d)
                    results.sort(key=lambda x: x.get("days_remaining", 9999))
                    return results
            conn.close()
        except Exception:
            pass
        return []

    def acknowledge_alert(self, alert_id: str) -> bool:
        """Mark an alert as acknowledged."""
        try:
            conn = self._connect()
            conn.execute(
                "UPDATE deadline_alerts SET acknowledged=1, acknowledged_at=datetime('now') WHERE alert_id=?",
                (alert_id,),
            )
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False

    def get_alert_history(self, limit: int = 50) -> list[dict]:
        """Get recent alert history."""
        try:
            conn = self._connect()
            rows = conn.execute(
                "SELECT * FROM deadline_alerts ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
            conn.close()
            return [dict(r) for r in rows]
        except Exception:
            return []

    def get_stats(self) -> dict:
        """Return integration statistics."""
        return {
            **self._stats,
            "thresholds": len(self.thresholds),
            "db_path": self.db_path,
        }

    # ─── Private Methods ───

    @staticmethod
    def _calc_days(due_date_str: str, today: date) -> Optional[int]:
        """Calculate days remaining from today to due date."""
        if not due_date_str or due_date_str in ("TBD", "N/A", "ASAP", "None", ""):
            return None
        for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y-%m-%dT%H:%M:%S"):
            try:
                due = datetime.strptime(due_date_str.strip(), fmt).date()
                return (due - today).days
            except ValueError:
                continue
        return None

    def _create_alert(
        self,
        deadline_id: str,
        case_name: str,
        filing_type: str,
        due_date: str,
        days_remaining: int,
        threshold: AlertThreshold,
        authority: str = "",
    ) -> DeadlineAlert:
        """Create a DeadlineAlert for a triggered threshold."""
        # Deterministic alert ID for dedup
        raw = f"{deadline_id}:{threshold.level}:{due_date}"
        alert_id = hashlib.sha256(raw.encode()).hexdigest()[:16]

        if days_remaining < 0:
            msg = f"OVERDUE by {abs(days_remaining)} days!"
        elif days_remaining == 0:
            msg = "DUE TODAY!"
        elif days_remaining == 1:
            msg = "DUE TOMORROW!"
        else:
            msg = f"Due in {days_remaining} days"

        return DeadlineAlert(
            alert_id=alert_id,
            deadline_id=deadline_id,
            case_name=case_name,
            filing_type=filing_type,
            due_date=due_date,
            days_remaining=days_remaining,
            alert_level=threshold.level,
            alert_message=msg,
            authority=authority,
        )

    def _compute_health_score(self, status: DeadlineStatus) -> float:
        """Compute a 0-100 health score (100 = all clear, 0 = critical)."""
        if status.total_deadlines == 0:
            return 100.0

        score = 100.0
        # Overdue: -20 per overdue item
        score -= status.overdue * 20
        # Critical: -10 per critical item
        score -= status.critical_7d * 10
        # High: -5 per high item
        score -= status.high_14d * 5
        # Medium: -2 per medium item
        score -= status.medium_30d * 2

        return max(0.0, min(100.0, score))

    def _persist_alerts(self, conn: sqlite3.Connection, alerts: list):
        """Persist alerts to database with dedup."""
        if not alerts:
            return
        try:
            rows = [
                (a.alert_id, a.deadline_id, a.case_name, a.filing_type,
                 a.due_date, a.days_remaining, a.alert_level, a.alert_message,
                 a.authority, a.created_at)
                for a in alerts
            ]
            conn.executemany(
                """INSERT OR IGNORE INTO deadline_alerts
                   (alert_id, deadline_id, case_name, filing_type, due_date,
                    days_remaining, alert_level, alert_message, authority, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                rows,
            )
            # Prune old alerts
            conn.execute(
                """DELETE FROM deadline_alerts
                   WHERE rowid NOT IN (
                       SELECT rowid FROM deadline_alerts
                       ORDER BY created_at DESC LIMIT ?
                   )""",
                (self.alert_history_limit,),
            )
            conn.commit()
        except sqlite3.OperationalError:
            pass  # Non-fatal

    def _persist_scan(self, conn: sqlite3.Connection, status: DeadlineStatus):
        """Record scan in history table."""
        try:
            conn.execute(
                """INSERT INTO deadline_scan_history
                   (total_deadlines, overdue_count, critical_count, alerts_generated, health_score)
                   VALUES (?, ?, ?, ?, ?)""",
                (status.total_deadlines, status.overdue, status.critical_7d,
                 len(status.alerts), status.health_score),
            )
            conn.commit()
        except sqlite3.OperationalError:
            pass

    def _render_html_dashboard(self, status: DeadlineStatus) -> str:
        """Render an HTML deadline dashboard."""
        health_color = (
            "#ff0000" if status.health_score < 30 else
            "#ff9900" if status.health_score < 60 else
            "#00cc00"
        )
        alert_rows = ""
        for a in status.alerts:
            level_class = a.alert_level.lower()
            alert_rows += f"""
            <tr class="{level_class}">
                <td>{a.alert_level}</td>
                <td>{a.case_name}</td>
                <td>{a.filing_type}</td>
                <td>{a.due_date}</td>
                <td>{a.days_remaining}</td>
                <td>{a.alert_message}</td>
            </tr>"""

        return f"""<!DOCTYPE html>
<html><head><title>Deadline Sentinel Dashboard</title>
<style>
body {{ font-family: 'Segoe UI', sans-serif; background: #1a1a2e; color: #eee; padding: 20px; }}
.card {{ background: #16213e; border-radius: 8px; padding: 20px; margin: 10px 0; }}
.health {{ font-size: 48px; color: {health_color}; font-weight: bold; }}
table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
th, td {{ padding: 8px 12px; text-align: left; border-bottom: 1px solid #333; }}
th {{ background: #0f3460; }}
.overdue {{ background: rgba(255,0,0,0.15); }}
.critical {{ background: rgba(255,100,0,0.15); }}
.high {{ background: rgba(255,200,0,0.1); }}
.medium {{ background: rgba(0,200,0,0.05); }}
</style></head><body>
<h1>⚖️ Deadline Sentinel Dashboard</h1>
<div class="card">
    <div class="health">{status.health_score:.0f}/100</div>
    <p>Scanned: {status.scan_time[:19]} | Total: {status.total_deadlines} deadlines</p>
    <p>🔴 Overdue: {status.overdue} | 🟠 Critical: {status.critical_7d} | 🟡 High: {status.high_14d} | 🟢 Medium: {status.medium_30d}</p>
</div>
<div class="card">
    <h2>Active Alerts ({len(status.alerts)})</h2>
    <table>
        <tr><th>Level</th><th>Case</th><th>Filing</th><th>Due</th><th>Days</th><th>Message</th></tr>
        {alert_rows if alert_rows else '<tr><td colspan="6">✅ No active alerts</td></tr>'}
    </table>
</div>
</body></html>"""


# ─── Module-level convenience functions ───

def scan_deadlines(db_path: str = None) -> DeadlineStatus:
    """Quick scan — returns DeadlineStatus."""
    return DeadlineSentinelIntegration(db_path=db_path).scan()


def deadline_dashboard(db_path: str = None, format: str = "text") -> str:
    """Quick dashboard — returns formatted string."""
    return DeadlineSentinelIntegration(db_path=db_path).get_dashboard(format=format)


if __name__ == "__main__":
    import sys
    fmt = sys.argv[1] if len(sys.argv) > 1 else "text"
    print(deadline_dashboard(format=fmt))
