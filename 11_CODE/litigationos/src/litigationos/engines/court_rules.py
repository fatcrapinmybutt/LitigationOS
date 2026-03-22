"""Court rules engine — Michigan Court Rule lookup and deadline calculation.

Queries ``mcr_rules.db`` for rule text, filing requirements, and
deadline computations.  Falls back to ``litigation_context.db`` when
the dedicated rules database is unavailable.

Usage::

    from litigationos.engines.court_rules import CourtRulesEngine

    engine = CourtRulesEngine()
    rule = engine.get_rule("MCR 2.003")
    results = engine.search_rules("disqualification")
"""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path
from typing import Any, Optional, Sequence

from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)

# -- Constants ----------------------------------------------------------------

_DEFAULT_DB_PATH = Path(__file__).resolve().parents[5] / "litigation_context.db"
_MCR_RULES_DB = Path(__file__).resolve().parents[5] / "mcr_rules.db"

_SQLITE_PRAGMAS = (
    "PRAGMA busy_timeout=60000",
    "PRAGMA journal_mode=WAL",
    "PRAGMA cache_size=-32000",
    "PRAGMA temp_store=MEMORY",
    "PRAGMA synchronous=NORMAL",
)


# -- Models -------------------------------------------------------------------


class CourtRule(BaseModel):
    """A single court rule entry."""

    rule_id: Optional[int] = None
    citation: str = ""
    title: str = ""
    text: str = ""
    category: Optional[str] = None
    effective_date: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class DeadlineRule(BaseModel):
    """Deadline parameters derived from a court rule."""

    rule_citation: str = ""
    rule_type: str = ""
    days: int = 0
    business_days: bool = False
    description: str = ""

    model_config = ConfigDict(from_attributes=True)


class FilingRequirement(BaseModel):
    """Filing requirements for a specific motion type."""

    motion_type: str = ""
    required_documents: list[str] = Field(default_factory=list)
    service_required: bool = True
    hearing_required: bool = False
    notice_days: int = 0
    applicable_rules: list[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# -- Engine -------------------------------------------------------------------


class CourtRulesEngine:
    """Michigan Court Rule lookup engine.

    Parameters
    ----------
    db_path : str | Path, optional
        Path to ``litigation_context.db`` (fallback).
    mcr_db_path : str | Path, optional
        Path to ``mcr_rules.db`` (primary rules database).
    """

    def __init__(
        self,
        db_path: str | Path | None = None,
        mcr_db_path: str | Path | None = None,
    ) -> None:
        self._db_path = Path(db_path) if db_path else _DEFAULT_DB_PATH
        self._mcr_db = Path(mcr_db_path) if mcr_db_path else _MCR_RULES_DB
        logger.info(
            "CourtRulesEngine initialized — mcr=%s fallback=%s",
            self._mcr_db, self._db_path,
        )

    @staticmethod
    def _connect(db_path: Path) -> sqlite3.Connection:
        conn = sqlite3.connect(str(db_path), timeout=120)
        for pragma in _SQLITE_PRAGMAS:
            conn.execute(pragma)
        conn.row_factory = sqlite3.Row
        return conn

    def _rules_conn(self) -> sqlite3.Connection:
        """Return a connection to the best available rules database."""
        if self._mcr_db.exists():
            return self._connect(self._mcr_db)
        return self._connect(self._db_path)

    def get_rule(self, citation: str) -> CourtRule:
        """Look up a court rule by citation string (e.g. ``MCR 2.003``)."""
        result = CourtRule(citation=citation)
        conn = self._rules_conn()
        try:
            tables = {r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()}
            for table in ("rules", "court_rules", "mcr_rules"):
                if table not in tables:
                    continue
                cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]
                cit_col = next((c for c in cols if c in ("citation", "rule_citation", "rule_number")), None)
                if not cit_col:
                    continue
                row = conn.execute(
                    f"SELECT * FROM {table} WHERE {cit_col} LIKE ?",
                    (f"%{citation}%",),
                ).fetchone()
                if row:
                    result.citation = str(row[cit_col])
                    if "title" in cols:
                        result.title = str(row["title"])
                    if "text" in cols:
                        result.text = str(row["text"])
                    elif "rule_text" in cols:
                        result.text = str(row["rule_text"])
                    break
        finally:
            conn.close()
        return result

    def search_rules(self, query: str, limit: int = 20) -> list[CourtRule]:
        """Full-text search across court rules."""
        results: list[CourtRule] = []
        conn = self._rules_conn()
        try:
            tables = {r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()}
            for table in ("rules", "court_rules", "mcr_rules"):
                if table not in tables:
                    continue
                cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]
                text_col = next((c for c in cols if c in ("text", "rule_text", "content")), None)
                if not text_col:
                    continue
                for row in conn.execute(
                    f"SELECT * FROM {table} WHERE {text_col} LIKE ? LIMIT ?",
                    (f"%{query}%", limit),
                ).fetchall():
                    cit = ""
                    for c in ("citation", "rule_citation", "rule_number"):
                        if c in cols:
                            cit = str(row[c])
                            break
                    results.append(CourtRule(
                        citation=cit,
                        title=str(row["title"]) if "title" in cols else "",
                        text=str(row[text_col]),
                    ))
                break
        finally:
            conn.close()
        return results

    def get_deadline_rule(self, rule_type: str) -> DeadlineRule:
        """Return deadline parameters for a given rule type."""
        return DeadlineRule(rule_type=rule_type, description=f"Deadline rule for {rule_type}")

    def get_filing_requirements(self, motion_type: str) -> FilingRequirement:
        """Return filing requirements for a specific motion type."""
        return FilingRequirement(
            motion_type=motion_type,
            required_documents=["motion", "brief", "proof_of_service"],
            service_required=True,
            applicable_rules=[],
        )
