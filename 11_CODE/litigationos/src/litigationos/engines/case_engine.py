"""Case management engine — CRUD operations for litigation cases.

Provides structured access to case records stored in
``litigation_context.db``, including lane assignment, status tracking,
and summary generation.

Usage::

    from litigationos.engines.case_engine import CaseEngine

    engine = CaseEngine()
    case = engine.get_case(case_id=1)
    cases = engine.list_cases(lane="A")
"""

from __future__ import annotations

import logging
import sqlite3
from datetime import datetime
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

CASE_LANES: dict[str, str] = {
    "A": "Watson custody",
    "B": "Shady Oaks housing",
    "C": "Convergence (cross-lane)",
    "D": "PPO / Protection Orders",
    "E": "Judicial Misconduct / JTC",
    "F": "Appellate (COA/MSC)",
}


# -- Models -------------------------------------------------------------------


class CaseRecord(BaseModel):
    """A single litigation case record."""

    case_id: Optional[int] = None
    case_number: str = ""
    title: str = ""
    court: str = ""
    lane: str = ""
    status: str = "active"
    filed_date: Optional[str] = None
    description: Optional[str] = None
    parties: list[str] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=datetime.now)

    model_config = ConfigDict(from_attributes=True)


class CaseSummary(BaseModel):
    """Lightweight summary of a case for dashboards."""

    case_id: Optional[int] = None
    case_number: str = ""
    title: str = ""
    lane: str = ""
    status: str = ""
    filing_count: int = 0
    evidence_count: int = 0
    next_deadline: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# -- Engine -------------------------------------------------------------------


class CaseEngine:
    """Case management engine for LitigationOS.

    Parameters
    ----------
    db_path : str | Path, optional
        Path to ``litigation_context.db``.
    """

    def __init__(self, db_path: str | Path | None = None) -> None:
        self._db_path = Path(db_path) if db_path else _DEFAULT_DB_PATH
        logger.info("CaseEngine initialized — db=%s", self._db_path)

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

    def get_case(self, case_id: int) -> CaseRecord:
        """Retrieve a single case by its primary key."""
        record = CaseRecord(case_id=case_id)
        if not self._db_path.exists():
            return record
        conn = self._connect(self._db_path)
        try:
            if not self._table_exists(conn, "cases"):
                return record
            cols = [r[1] for r in conn.execute("PRAGMA table_info(cases)").fetchall()]
            row = conn.execute("SELECT * FROM cases WHERE rowid = ?", (case_id,)).fetchone()
            if row:
                if "case_number" in cols:
                    record.case_number = str(row["case_number"])
                if "title" in cols:
                    record.title = str(row["title"])
                if "court" in cols:
                    record.court = str(row["court"])
                if "lane" in cols:
                    record.lane = str(row["lane"])
                if "status" in cols:
                    record.status = str(row["status"])
        finally:
            conn.close()
        return record

    def list_cases(self, lane: str | None = None, status: str | None = None) -> list[CaseRecord]:
        """List cases with optional lane / status filters."""
        results: list[CaseRecord] = []
        if not self._db_path.exists():
            return results
        conn = self._connect(self._db_path)
        try:
            if not self._table_exists(conn, "cases"):
                return results
            query = "SELECT rowid, * FROM cases WHERE 1=1"
            params: list[Any] = []
            cols = [r[1] for r in conn.execute("PRAGMA table_info(cases)").fetchall()]
            if lane and "lane" in cols:
                query += " AND lane = ?"
                params.append(lane)
            if status and "status" in cols:
                query += " AND status = ?"
                params.append(status)
            for row in conn.execute(query, params).fetchall():
                rec = CaseRecord(case_id=row["rowid"])
                if "case_number" in cols:
                    rec.case_number = str(row["case_number"])
                if "title" in cols:
                    rec.title = str(row["title"])
                if "lane" in cols:
                    rec.lane = str(row["lane"])
                if "status" in cols:
                    rec.status = str(row["status"])
                results.append(rec)
        finally:
            conn.close()
        return results

    def update_case_status(self, case_id: int, status: str) -> bool:
        """Update the status of a case.  Returns ``True`` on success."""
        if not self._db_path.exists():
            return False
        conn = self._connect(self._db_path)
        try:
            if not self._table_exists(conn, "cases"):
                return False
            cols = [r[1] for r in conn.execute("PRAGMA table_info(cases)").fetchall()]
            if "status" not in cols:
                return False
            conn.execute("UPDATE cases SET status = ? WHERE rowid = ?", (status, case_id))
            conn.commit()
            return True
        finally:
            conn.close()

    def get_case_summary(self, case_id: int) -> CaseSummary:
        """Build a lightweight summary for a single case."""
        case = self.get_case(case_id)
        return CaseSummary(
            case_id=case.case_id,
            case_number=case.case_number,
            title=case.title,
            lane=case.lane,
            status=case.status,
        )
