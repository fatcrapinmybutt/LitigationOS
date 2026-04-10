"""
Filing Engine Triggers — Auto-Activation System
=================================================

Scans for conditions that should trigger autonomous filing preparation:
  1. Deadline proximity (configurable window)
  2. EGCP readiness threshold crossed
  3. New court order detected (creates response deadline)
  4. Manual invocation
"""

import sqlite3
import json
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field, asdict


@dataclass
class Trigger:
    """A detected trigger condition."""
    trigger_type: str          # deadline | readiness | order | manual
    filing_id: str             # Filing lane/ID
    urgency: str               # critical | high | medium | low
    days_remaining: Optional[int] = None
    readiness_score: Optional[float] = None
    description: str = ""
    rule_authority: str = ""
    recommended_action: str = ""


@dataclass
class TriggerConfig:
    """Configuration for trigger thresholds."""
    deadline_critical_days: int = 7
    deadline_high_days: int = 14
    deadline_medium_days: int = 30
    readiness_threshold: float = 65.0
    auto_activate: bool = False   # True = auto-start pipeline
    scan_interval_minutes: int = 60
    separation_date: Optional[date] = None  # Last contact date for custody separation trigger


class TriggerScanner:
    """Scans case state for filing activation triggers."""

    def __init__(self, db_path: Optional[str] = None,
                 config: Optional[TriggerConfig] = None):
        self.config = config or TriggerConfig()
        self._db_path = db_path
        self._db = None

    def _get_db(self) -> sqlite3.Connection:
        """Lazy database connection. Uses shared module when available."""
        if self._db is None:
            if self._db_path:
                self._db = sqlite3.connect(self._db_path)
            else:
                # Try shared module first, fall back to manual path
                try:
                    import sys as _sys
                    _sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
                    from shared import get_root, DB_REGISTRY
                    root = get_root()
                    db_rel = DB_REGISTRY.get("litigation", "litigation_context.db")
                    self._db = sqlite3.connect(str(root / db_rel))
                except Exception:
                    root = Path(__file__).resolve().parent.parent.parent.parent
                    self._db = sqlite3.connect(str(root / "litigation_context.db"))
            self._db.row_factory = sqlite3.Row
            self._db.execute("PRAGMA busy_timeout=60000")
            self._db.execute("PRAGMA journal_mode=WAL")
            self._db.execute("PRAGMA cache_size=-32000")
        return self._db

    def scan_all(self) -> list:
        """Run all trigger scans. Returns sorted list of Trigger objects."""
        triggers = []
        triggers.extend(self.scan_deadlines())
        triggers.extend(self.scan_readiness())

        # Sort: critical first, then by days remaining
        priority = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        triggers.sort(key=lambda t: (priority.get(t.urgency, 9),
                                     t.days_remaining or 999))
        return triggers

    def scan_deadlines(self) -> list:
        """Check for approaching deadlines across all lanes."""
        triggers = []
        db = self._get_db()
        today = date.today()

        # Check deadlines table
        try:
            rows = db.execute("""
                SELECT * FROM deadlines
                WHERE status IN ('PENDING', 'pending', 'active')
                ORDER BY deadline_date ASC
            """).fetchall()
        except sqlite3.OperationalError:
            # Table may not exist — return empty
            return triggers

        for row in rows:
            try:
                deadline_str = row["deadline_date"]
                if not deadline_str:
                    continue
                deadline_date = date.fromisoformat(deadline_str[:10])
                days_left = (deadline_date - today).days

                if days_left < 0:
                    urgency = "critical"
                    desc = f"OVERDUE by {abs(days_left)} days"
                elif days_left <= self.config.deadline_critical_days:
                    urgency = "critical"
                    desc = f"{days_left} days remaining"
                elif days_left <= self.config.deadline_high_days:
                    urgency = "high"
                    desc = f"{days_left} days remaining"
                elif days_left <= self.config.deadline_medium_days:
                    urgency = "medium"
                    desc = f"{days_left} days remaining"
                else:
                    continue  # Outside scan window

                filing_id = row["filing_id"] if "filing_id" in row.keys() else "UNKNOWN"
                rule = row["rule"] if "rule" in row.keys() else ""

                triggers.append(Trigger(
                    trigger_type="deadline",
                    filing_id=filing_id,
                    urgency=urgency,
                    days_remaining=days_left,
                    description=f"Deadline: {desc} — {row.get('description', '')}",
                    rule_authority=rule,
                    recommended_action="Begin filing preparation" if days_left > 3
                                       else "URGENT: File immediately"
                ))
            except (ValueError, KeyError):
                continue

        return triggers

    def scan_readiness(self) -> list:
        """Check EGCP readiness scores for filings crossing threshold."""
        triggers = []
        db = self._get_db()

        # Try to read EGCP scores from filing_packages or similar table
        for table in ["filing_packages", "egcp_scores"]:
            try:
                rows = db.execute(f"""
                    SELECT * FROM {table}
                    WHERE readiness_score >= ?
                    ORDER BY readiness_score DESC
                """, (self.config.readiness_threshold,)).fetchall()

                for row in rows:
                    score = row["readiness_score"]
                    filing_id = row.get("filing_id", row.get("package_id", "UNKNOWN"))
                    triggers.append(Trigger(
                        trigger_type="readiness",
                        filing_id=filing_id,
                        urgency="high" if score >= 80 else "medium",
                        readiness_score=score,
                        description=f"EGCP score {score:.1f}/100 — filing ready",
                        recommended_action="Assemble and file"
                    ))
                break  # Found a working table
            except sqlite3.OperationalError:
                continue

        return triggers

    def scan_separation_urgency(self, last_contact: date = None) -> Optional[Trigger]:
        """Calculate separation urgency for child custody cases.

        Uses last_contact if provided, otherwise falls back to
        config.separation_date. Returns None if neither is set.
        """
        if last_contact is None:
            last_contact = self.config.separation_date
        if last_contact is None:
            import logging as _log
            _log.getLogger(__name__).debug(
                "scan_separation_urgency skipped — no separation_date configured"
            )
            return None
        days = (date.today() - last_contact).days
        months = days / 30.44

        if days > 180:
            urgency = "critical"
        elif days > 90:
            urgency = "high"
        elif days > 30:
            urgency = "medium"
        else:
            urgency = "low"

        return Trigger(
            trigger_type="separation",
            filing_id="CUSTODY",
            urgency=urgency,
            days_remaining=days,
            description=f"Parent-child separation: {days} days ({months:.1f} months)",
            rule_authority="US Const Amend XIV; Troxel v Granville",
            recommended_action="Emergency motion if not already filed"
        )

    def to_json(self, triggers: list) -> str:
        """Serialize triggers to JSON."""
        return json.dumps([asdict(t) for t in triggers], indent=2, default=str)

    def to_report(self, triggers: list) -> str:
        """Generate human-readable trigger report."""
        if not triggers:
            return "✅ No active triggers — all filings on schedule."

        lines = ["=" * 60,
                 "  FILING ENGINE — TRIGGER SCAN REPORT",
                 f"  Scanned: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                 "=" * 60, ""]

        icons = {"critical": "🔴", "high": "🟡", "medium": "🟢", "low": "⚪"}
        for t in triggers:
            icon = icons.get(t.urgency, "❓")
            lines.append(f"{icon} [{t.urgency.upper()}] {t.filing_id}")
            lines.append(f"   Type: {t.trigger_type}")
            lines.append(f"   {t.description}")
            if t.rule_authority:
                lines.append(f"   Authority: {t.rule_authority}")
            lines.append(f"   → {t.recommended_action}")
            lines.append("")

        summary = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for t in triggers:
            summary[t.urgency] = summary.get(t.urgency, 0) + 1

        lines.append("-" * 60)
        lines.append(f"  Summary: {summary['critical']} critical, "
                     f"{summary['high']} high, {summary['medium']} medium, "
                     f"{summary['low']} low")
        lines.append("=" * 60)
        return "\n".join(lines)

    def close(self):
        """Close database connection."""
        if self._db:
            self._db.close()
            self._db = None
