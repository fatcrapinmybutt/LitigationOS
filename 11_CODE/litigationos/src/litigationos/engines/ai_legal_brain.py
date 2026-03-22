"""Legal AI reasoning engine — local-only case analysis and strategy.

Provides structured legal analysis using data from ``litigation_context.db``.
All reasoning is rule-based and local — no remote API calls.

Usage::

    from litigationos.engines.ai_legal_brain import LegalAIBrain

    brain = LegalAIBrain()
    result = brain.analyze_case(case_id=1)
    strategy = brain.generate_strategy(lane="A")
"""

from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass, field
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


# -- Models -------------------------------------------------------------------


class CaseAnalysis(BaseModel):
    """Result of analysing a case or claim."""

    case_id: Optional[int] = None
    lane: Optional[str] = None
    summary: str = ""
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    evidence_count: int = 0
    claim_count: int = 0
    risk_factors: list[str] = Field(default_factory=list)
    analyzed_at: datetime = Field(default_factory=datetime.now)

    model_config = ConfigDict(from_attributes=True)


class StrategyRecommendation(BaseModel):
    """A recommended litigation strategy."""

    strategy_name: str = ""
    description: str = ""
    priority: str = "normal"
    recommended_filings: list[str] = Field(default_factory=list)
    estimated_strength: float = 0.0

    model_config = ConfigDict(from_attributes=True)


class ClaimStrength(BaseModel):
    """Strength assessment for a single claim."""

    claim_id: Optional[int] = None
    claim_type: str = ""
    strength_score: float = 0.0
    supporting_evidence: int = 0
    gaps: list[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# -- Engine -------------------------------------------------------------------


class LegalAIBrain:
    """Local-only legal AI reasoning engine.

    Parameters
    ----------
    db_path : str | Path, optional
        Path to ``litigation_context.db``.  Defaults to the canonical
        repo-root location.
    """

    def __init__(self, db_path: str | Path | None = None) -> None:
        self._db_path = Path(db_path) if db_path else _DEFAULT_DB_PATH
        logger.info("LegalAIBrain initialized — db=%s", self._db_path)

    @staticmethod
    def _connect(db_path: Path) -> sqlite3.Connection:
        """Open a connection with LitigationOS-standard PRAGMAs."""
        conn = sqlite3.connect(str(db_path), timeout=120)
        for pragma in _SQLITE_PRAGMAS:
            conn.execute(pragma)
        conn.row_factory = sqlite3.Row
        return conn

    def analyze_case(self, case_id: int | None = None, lane: str | None = None) -> CaseAnalysis:
        """Analyse a case by *case_id* or *lane*, returning structured findings."""
        analysis = CaseAnalysis(case_id=case_id, lane=lane)
        if not self._db_path.exists():
            logger.warning("Database not found at %s", self._db_path)
            return analysis
        conn = self._connect(self._db_path)
        try:
            tables = {r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()}
            if "claims" in tables:
                rows = conn.execute("SELECT COUNT(*) FROM claims").fetchone()
                analysis.claim_count = rows[0] if rows else 0
            if "evidence_quotes" in tables:
                rows = conn.execute("SELECT COUNT(*) FROM evidence_quotes").fetchone()
                analysis.evidence_count = rows[0] if rows else 0
            analysis.summary = (
                f"Case analysis: {analysis.claim_count} claims, "
                f"{analysis.evidence_count} evidence items"
            )
        finally:
            conn.close()
        return analysis

    def generate_strategy(self, lane: str | None = None) -> list[StrategyRecommendation]:
        """Generate litigation strategy recommendations for a lane."""
        strategies: list[StrategyRecommendation] = []
        if not self._db_path.exists():
            return strategies
        conn = self._connect(self._db_path)
        try:
            tables = {r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()}
            if "filing_readiness" in tables:
                query = "SELECT vehicle_name, status FROM filing_readiness"
                params: list[Any] = []
                if lane:
                    query += " WHERE vehicle_name LIKE ?"
                    params.append(f"%{lane}%")
                for row in conn.execute(query, params).fetchall():
                    strategies.append(StrategyRecommendation(
                        strategy_name=str(row[0]),
                        description=f"Filing vehicle: {row[0]} — status: {row[1]}",
                        priority="high" if row[1] == "ready" else "normal",
                    ))
        finally:
            conn.close()
        return strategies

    def assess_claim_strength(self, claim_id: int | None = None) -> ClaimStrength:
        """Assess the evidentiary strength of a specific claim."""
        result = ClaimStrength(claim_id=claim_id)
        if not self._db_path.exists():
            return result
        conn = self._connect(self._db_path)
        try:
            tables = {r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()}
            if "evidence_quotes" in tables and claim_id is not None:
                cols = [r[1] for r in conn.execute("PRAGMA table_info(evidence_quotes)").fetchall()]
                if "claim_id" in cols:
                    row = conn.execute(
                        "SELECT COUNT(*) FROM evidence_quotes WHERE claim_id = ?",
                        (claim_id,),
                    ).fetchone()
                    result.supporting_evidence = row[0] if row else 0
                    result.strength_score = min(result.supporting_evidence / 10.0, 1.0)
        finally:
            conn.close()
        return result
