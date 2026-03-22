"""Deadline tracking engine — urgency scoring and calendar management.

Tracks litigation deadlines from ``litigation_context.db``, computes
urgency scores, and surfaces upcoming events.

Usage::

    from litigationos.engines.deadline import DeadlineEngine

    engine = DeadlineEngine()
    deadlines = engine.get_deadlines(case_id=1)
    upcoming = engine.get_upcoming(days=14)
"""

from __future__ import annotations

import logging
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Optional, Sequence

from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)

# -- Constants ----------------------------------------------------------------

_DEFAULT_DB_PATH = Path(__file__).resolve().parents[5] / "litigation_context.db"

_SQLITE_PRAGMAS = (
    "PRAGMA busy_timeout=60000",
    "PRAGMA journal_mode=WAL",
    "PRAGMA cache_size=-32000",
    "PRAGMA temp_store=MEMORY",
    "PRAGMA synchronous=NORMAL",
)

_URGENCY_THRESHOLDS: dict[str, int] = {
    "critical": 3,
    "high": 7,
    "elevated": 14,
    "normal": 30,
}


# -- Models -------------------------------------------------------------------


class Deadline(BaseModel):
    """A single deadline record."""

    deadline_id: Optional[int] = None
    case_id: Optional[int] = None
    title: str = ""
    due_date: Optional[str] = None
    status: str = "pending"
    urgency: str = "normal"
    description: Optional[str] = None
    vehicle_name: Optional[str] = None
    rule_citation: Optional[str] = None
    days_remaining: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class UrgencyReport(BaseModel):
    """Urgency assessment across all active deadlines."""

    total_deadlines: int = 0
    critical: int = 0
    high: int = 0
    elevated: int = 0
    normal: int = 0
    overdue: int = 0
    next_deadline: Optional[Deadline] = None

    model_config = ConfigDict(from_attributes=True)


# -- Helpers ------------------------------------------------------------------


def _days_until(date_str: str | None) -> int | None:
    """Return days remaining until *date_str* (ISO-8601).  ``None`` on failure."""
    if not date_str:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            target = datetime.strptime(date_str[:19], fmt).date()
            return (target - date.today()).days
        except (ValueError, TypeError):
            continue
    return None


def _classify_urgency(days_remaining: int | None) -> str:
    if days_remaining is None:
        return "normal"
    if days_remaining < 0:
        return "overdue"
    for level, threshold in _URGENCY_THRESHOLDS.items():
        if days_remaining <= threshold:
            return level
    return "normal"


# -- Engine -------------------------------------------------------------------


class DeadlineEngine:
    """Deadline tracking and urgency-scoring engine.

    Parameters
    ----------
    db_path : str | Path, optional
        Path to ``litigation_context.db``.
    """

    def __init__(self, db_path: str | Path | None = None) -> None:
        self._db_path = Path(db_path) if db_path else _DEFAULT_DB_PATH
        logger.info("DeadlineEngine initialized — db=%s", self._db_path)

    @staticmethod
    def _connect(db_path: Path) -> sqlite3.Connection:
        conn = sqlite3.connect(str(db_path), timeout=120)
        for pragma in _SQLITE_PRAGMAS:
            conn.execute(pragma)
        conn.row_factory = sqlite3.Row
        return conn

    def _table_exists(self, conn: sqlite3.Connection, name: str) -> bool:
        row = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
        ).fetchone()
        return row is not None

    def _row_to_deadline(self, row: sqlite3.Row, cols: Sequence[str]) -> Deadline:
        """Map a DB row to a :class:`Deadline`."""
        due = str(row["due_date_iso"]) if "due_date_iso" in cols else (
            str(row["due_date"]) if "due_date" in cols else None
        )
        days = _days_until(due)
        return Deadline(
            deadline_id=int(row["rowid"]) if "rowid" in cols else None,
            title=str(row["title"]) if "title" in cols else "",
            due_date=due,
            status=str(row["status"]) if "status" in cols else "pending",
            urgency=_classify_urgency(days),
            vehicle_name=str(row["vehicle_name"]) if "vehicle_name" in cols else None,
            days_remaining=days,
        )

    def get_deadlines(self, case_id: int | None = None) -> list[Deadline]:
        """Return all deadlines, optionally filtered by *case_id*."""
        results: list[Deadline] = []
        if not self._db_path.exists():
            return results
        conn = self._connect(self._db_path)
        try:
            if not self._table_exists(conn, "deadlines"):
                return results
            cols = [r[1] for r in conn.execute("PRAGMA table_info(deadlines)").fetchall()]
            query = "SELECT rowid, * FROM deadlines"
            params: list[Any] = []
            if case_id is not None and "case_id" in cols:
                query += " WHERE case_id = ?"
                params.append(case_id)
            for row in conn.execute(query, params).fetchall():
                results.append(self._row_to_deadline(row, cols))
        finally:
            conn.close()
        return results

    def add_deadline(
        self,
        title: str,
        due_date: str,
        case_id: int | None = None,
        vehicle_name: str | None = None,
    ) -> Deadline:
        """Insert a new deadline and return it."""
        days = _days_until(due_date)
        dl = Deadline(
            title=title,
            due_date=due_date,
            case_id=case_id,
            vehicle_name=vehicle_name,
            urgency=_classify_urgency(days),
            days_remaining=days,
        )
        if not self._db_path.exists():
            return dl
        conn = self._connect(self._db_path)
        try:
            if not self._table_exists(conn, "deadlines"):
                return dl
            conn.execute(
                "INSERT INTO deadlines (title, due_date, case_id, vehicle_name, status) "
                "VALUES (?, ?, ?, ?, ?)",
                (title, due_date, case_id, vehicle_name, "pending"),
            )
            conn.commit()
        finally:
            conn.close()
        return dl

    def check_urgency(self) -> UrgencyReport:
        """Return an urgency report across all active deadlines."""
        deadlines = self.get_deadlines()
        report = UrgencyReport(total_deadlines=len(deadlines))
        for dl in deadlines:
            if dl.urgency == "overdue":
                report.overdue += 1
            elif dl.urgency == "critical":
                report.critical += 1
            elif dl.urgency == "high":
                report.high += 1
            elif dl.urgency == "elevated":
                report.elevated += 1
            else:
                report.normal += 1
        pending = [d for d in deadlines if d.due_date and d.days_remaining is not None and d.days_remaining >= 0]
        if pending:
            report.next_deadline = min(pending, key=lambda d: d.days_remaining or 999)
        return report

    def get_upcoming(self, days: int = 14) -> list[Deadline]:
        """Return deadlines due within the next *days* days."""
        all_dl = self.get_deadlines()
        return [
            d for d in all_dl
            if d.days_remaining is not None and 0 <= d.days_remaining <= days
        ]
