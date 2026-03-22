"""Evidence management engine — catalog, link, and assess evidence.

Manages evidence records from the ``evidence_quotes`` table in
``litigation_context.db``.  Supports lane-aware filtering, claim linkage,
strength assessment, and gap analysis.

Usage::

    from litigationos.engines.evidence import EvidenceEngine

    engine = EvidenceEngine()
    items = engine.list_evidence(lane="A")
    gaps = engine.get_gaps(vehicle_name="custody_motion")
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

EVIDENCE_STRENGTH = ("strong", "moderate", "weak", "unverified")


# -- Models -------------------------------------------------------------------


class EvidenceItem(BaseModel):
    """A single evidence record."""

    evidence_id: Optional[int] = None
    quote: str = ""
    source_file: Optional[str] = None
    claim_id: Optional[int] = None
    vehicle_name: Optional[str] = None
    lane: Optional[str] = None
    strength: str = "unverified"
    date_captured: Optional[str] = None
    category: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class EvidenceGap(BaseModel):
    """An identified gap in evidentiary coverage."""

    claim_id: Optional[int] = None
    vehicle_name: Optional[str] = None
    gap_description: str = ""
    severity: str = "medium"
    recommendation: str = ""

    model_config = ConfigDict(from_attributes=True)


class StrengthAssessment(BaseModel):
    """Overall evidence strength for a claim or vehicle."""

    target: str = ""
    total_items: int = 0
    strong: int = 0
    moderate: int = 0
    weak: int = 0
    unverified: int = 0
    overall_score: float = 0.0

    model_config = ConfigDict(from_attributes=True)


# -- Engine -------------------------------------------------------------------


class EvidenceEngine:
    """Evidence management and gap analysis engine.

    Parameters
    ----------
    db_path : str | Path, optional
        Path to ``litigation_context.db``.
    """

    def __init__(self, db_path: str | Path | None = None) -> None:
        self._db_path = Path(db_path) if db_path else _DEFAULT_DB_PATH
        logger.info("EvidenceEngine initialized — db=%s", self._db_path)

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

    def _row_to_evidence(self, row: sqlite3.Row, cols: Sequence[str]) -> EvidenceItem:
        return EvidenceItem(
            evidence_id=int(row["rowid"]) if "rowid" in cols else None,
            quote=str(row["quote"]) if "quote" in cols else "",
            source_file=str(row["source_file"]) if "source_file" in cols else None,
            claim_id=int(row["claim_id"]) if "claim_id" in cols and row["claim_id"] else None,
            vehicle_name=str(row["vehicle_name"]) if "vehicle_name" in cols else None,
            lane=str(row["lane"]) if "lane" in cols else None,
        )

    def get_evidence(self, evidence_id: int) -> EvidenceItem:
        """Retrieve a single evidence item by primary key."""
        result = EvidenceItem(evidence_id=evidence_id)
        if not self._db_path.exists():
            return result
        conn = self._connect(self._db_path)
        try:
            if not self._table_exists(conn, "evidence_quotes"):
                return result
            cols = [r[1] for r in conn.execute("PRAGMA table_info(evidence_quotes)").fetchall()]
            cols_with_rowid = ["rowid", *cols]
            row = conn.execute(
                "SELECT rowid, * FROM evidence_quotes WHERE rowid = ?", (evidence_id,)
            ).fetchone()
            if row:
                result = self._row_to_evidence(row, cols_with_rowid)
        finally:
            conn.close()
        return result

    def list_evidence(
        self,
        lane: str | None = None,
        vehicle_name: str | None = None,
        limit: int = 100,
    ) -> list[EvidenceItem]:
        """List evidence items with optional lane / vehicle filters."""
        results: list[EvidenceItem] = []
        if not self._db_path.exists():
            return results
        conn = self._connect(self._db_path)
        try:
            if not self._table_exists(conn, "evidence_quotes"):
                return results
            cols = [r[1] for r in conn.execute("PRAGMA table_info(evidence_quotes)").fetchall()]
            cols_with_rowid = ["rowid", *cols]
            query = "SELECT rowid, * FROM evidence_quotes WHERE 1=1"
            params: list[Any] = []
            if lane and "lane" in cols:
                query += " AND lane = ?"
                params.append(lane)
            if vehicle_name and "vehicle_name" in cols:
                query += " AND vehicle_name = ?"
                params.append(vehicle_name)
            query += " LIMIT ?"
            params.append(limit)
            for row in conn.execute(query, params).fetchall():
                results.append(self._row_to_evidence(row, cols_with_rowid))
        finally:
            conn.close()
        return results

    def link_to_claim(self, evidence_id: int, claim_id: int) -> bool:
        """Link an evidence item to a claim.  Returns ``True`` on success."""
        if not self._db_path.exists():
            return False
        conn = self._connect(self._db_path)
        try:
            if not self._table_exists(conn, "evidence_quotes"):
                return False
            cols = [r[1] for r in conn.execute("PRAGMA table_info(evidence_quotes)").fetchall()]
            if "claim_id" not in cols:
                return False
            conn.execute(
                "UPDATE evidence_quotes SET claim_id = ? WHERE rowid = ?",
                (claim_id, evidence_id),
            )
            conn.commit()
            return True
        finally:
            conn.close()

    def assess_strength(self, vehicle_name: str | None = None) -> StrengthAssessment:
        """Assess evidentiary strength for a vehicle or overall."""
        items = self.list_evidence(vehicle_name=vehicle_name, limit=10000)
        assessment = StrengthAssessment(
            target=vehicle_name or "all",
            total_items=len(items),
        )
        for item in items:
            if item.strength == "strong":
                assessment.strong += 1
            elif item.strength == "moderate":
                assessment.moderate += 1
            elif item.strength == "weak":
                assessment.weak += 1
            else:
                assessment.unverified += 1
        if assessment.total_items > 0:
            assessment.overall_score = (
                (assessment.strong * 1.0 + assessment.moderate * 0.6 + assessment.weak * 0.2)
                / assessment.total_items
            )
        return assessment

    def get_gaps(self, vehicle_name: str | None = None) -> list[EvidenceGap]:
        """Identify evidentiary gaps for a filing vehicle."""
        gaps: list[EvidenceGap] = []
        if not self._db_path.exists():
            return gaps
        conn = self._connect(self._db_path)
        try:
            if not self._table_exists(conn, "claims"):
                return gaps
            cols = [r[1] for r in conn.execute("PRAGMA table_info(claims)").fetchall()]
            query = "SELECT * FROM claims"
            params: list[Any] = []
            if vehicle_name and "vehicle_name" in cols:
                query += " WHERE vehicle_name = ?"
                params.append(vehicle_name)
            for claim_row in conn.execute(query, params).fetchall():
                cid_col = next((c for c in cols if c in ("claim_id", "id", "rowid")), None)
                if not cid_col:
                    continue
                cid = claim_row[cid_col]
                if self._table_exists(conn, "evidence_quotes"):
                    eq_cols = [r[1] for r in conn.execute("PRAGMA table_info(evidence_quotes)").fetchall()]
                    if "claim_id" in eq_cols:
                        cnt = conn.execute(
                            "SELECT COUNT(*) FROM evidence_quotes WHERE claim_id = ?", (cid,)
                        ).fetchone()[0]
                        if cnt == 0:
                            gaps.append(EvidenceGap(
                                claim_id=int(cid),
                                vehicle_name=vehicle_name,
                                gap_description=f"No evidence linked to claim {cid}",
                                severity="high",
                                recommendation="Search evidence corpus for supporting quotes",
                            ))
        finally:
            conn.close()
        return gaps
