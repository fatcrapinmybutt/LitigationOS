"""Filing workflow engine — CRUD, validation, and readiness scoring.

Manages the filing lifecycle from the ``filing_readiness`` table in
``litigation_context.db``.  Provides readiness scores, validation checks,
and status tracking.

Usage::

    from litigationos.engines.filing import FilingEngine

    engine = FilingEngine()
    filings = engine.list_filings(status="ready")
    score = engine.get_readiness_score(filing_id=1)
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

FILING_STATUSES = (
    "draft", "review", "qa_pass", "qa_fail", "ready", "filed", "served",
)


# -- Models -------------------------------------------------------------------


class Filing(BaseModel):
    """A filing record from the readiness pipeline."""

    filing_id: Optional[int] = None
    vehicle_name: str = ""
    status: str = "draft"
    lane: Optional[str] = None
    court: Optional[str] = None
    case_number: Optional[str] = None
    filing_type: Optional[str] = None
    readiness_score: float = 0.0
    last_updated: datetime = Field(default_factory=datetime.now)

    model_config = ConfigDict(from_attributes=True)


class ValidationResult(BaseModel):
    """Result of validating a filing for court submission."""

    filing_id: Optional[int] = None
    is_valid: bool = False
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    checks_passed: int = 0
    checks_total: int = 0

    model_config = ConfigDict(from_attributes=True)


class ReadinessScore(BaseModel):
    """Readiness assessment for a single filing."""

    filing_id: Optional[int] = None
    vehicle_name: str = ""
    score: float = 0.0
    missing_items: list[str] = Field(default_factory=list)
    blocking_issues: list[str] = Field(default_factory=list)
    ready_to_file: bool = False

    model_config = ConfigDict(from_attributes=True)


# -- Engine -------------------------------------------------------------------


class FilingEngine:
    """Filing workflow and readiness engine.

    Parameters
    ----------
    db_path : str | Path, optional
        Path to ``litigation_context.db``.
    """

    def __init__(self, db_path: str | Path | None = None) -> None:
        self._db_path = Path(db_path) if db_path else _DEFAULT_DB_PATH
        logger.info("FilingEngine initialized — db=%s", self._db_path)

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

    def _row_to_filing(self, row: sqlite3.Row, cols: Sequence[str]) -> Filing:
        return Filing(
            filing_id=int(row["rowid"]) if "rowid" in cols else None,
            vehicle_name=str(row["vehicle_name"]) if "vehicle_name" in cols else "",
            status=str(row["status"]) if "status" in cols else "draft",
            lane=str(row["lane"]) if "lane" in cols else None,
            court=str(row["court"]) if "court" in cols else None,
            case_number=str(row["case_number"]) if "case_number" in cols else None,
        )

    def get_filing(self, filing_id: int) -> Filing:
        """Retrieve a single filing by primary key."""
        result = Filing(filing_id=filing_id)
        if not self._db_path.exists():
            return result
        conn = self._connect(self._db_path)
        try:
            if not self._table_exists(conn, "filing_readiness"):
                return result
            cols = [r[1] for r in conn.execute("PRAGMA table_info(filing_readiness)").fetchall()]
            cols_with_rowid = ["rowid", *cols]
            row = conn.execute(
                "SELECT rowid, * FROM filing_readiness WHERE rowid = ?", (filing_id,)
            ).fetchone()
            if row:
                result = self._row_to_filing(row, cols_with_rowid)
        finally:
            conn.close()
        return result

    def list_filings(self, status: str | None = None, limit: int = 100) -> list[Filing]:
        """List filings with optional *status* filter."""
        results: list[Filing] = []
        if not self._db_path.exists():
            return results
        conn = self._connect(self._db_path)
        try:
            if not self._table_exists(conn, "filing_readiness"):
                return results
            cols = [r[1] for r in conn.execute("PRAGMA table_info(filing_readiness)").fetchall()]
            cols_with_rowid = ["rowid", *cols]
            query = "SELECT rowid, * FROM filing_readiness"
            params: list[Any] = []
            if status and "status" in cols:
                query += " WHERE status = ?"
                params.append(status)
            query += " LIMIT ?"
            params.append(limit)
            for row in conn.execute(query, params).fetchall():
                results.append(self._row_to_filing(row, cols_with_rowid))
        finally:
            conn.close()
        return results

    def validate_filing(self, filing_id: int) -> ValidationResult:
        """Run validation checks on a filing."""
        vr = ValidationResult(filing_id=filing_id)
        filing = self.get_filing(filing_id)
        checks = [
            ("vehicle_name", bool(filing.vehicle_name)),
            ("status_valid", filing.status in FILING_STATUSES),
        ]
        vr.checks_total = len(checks)
        for name, passed in checks:
            if passed:
                vr.checks_passed += 1
            else:
                vr.errors.append(f"Check failed: {name}")
        vr.is_valid = vr.checks_passed == vr.checks_total
        return vr

    def get_readiness_score(self, filing_id: int) -> ReadinessScore:
        """Compute a readiness score for a filing."""
        filing = self.get_filing(filing_id)
        score = ReadinessScore(
            filing_id=filing_id,
            vehicle_name=filing.vehicle_name,
        )
        points = 0.0
        total = 3.0
        if filing.vehicle_name:
            points += 1.0
        else:
            score.missing_items.append("vehicle_name")
        if filing.status in ("qa_pass", "ready", "filed", "served"):
            points += 1.0
        else:
            score.missing_items.append(f"status={filing.status} (needs qa_pass+)")
        if filing.case_number:
            points += 1.0
        else:
            score.missing_items.append("case_number")
        score.score = round(points / total, 2) if total > 0 else 0.0
        score.ready_to_file = score.score >= 0.9
        return score
