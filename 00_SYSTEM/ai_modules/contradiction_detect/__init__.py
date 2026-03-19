"""Contradiction Detection Engine for LitigationOS.

Local-only. Zero network. Scans litigation documents for contradictory
statements using TF-IDF similarity, entity comparison, and temporal analysis.

Usage::

    from contradiction_detect import ContradictionEngine

    engine = ContradictionEngine()
    report = engine.scan(lane="A")          # full scan on lane A
    report = engine.scan_documents([1, 5])  # targeted scan
    stats  = engine.get_stats()             # summary statistics
"""
from __future__ import annotations

import logging
import sqlite3
from typing import Optional

from . import config
from .statement_extractor import Statement, StatementExtractor
from .normalizer import NormalizedStatement, StatementNormalizer
from .comparator import Contradiction, ComparisonResult, StatementComparator
from .temporal_checker import TemporalAnomaly, TemporalChecker
from .scorer import ScoredContradiction, ContradictionScorer
from .report_generator import ContradictionReport

__all__ = [
    "ContradictionEngine",
    "Statement",
    "NormalizedStatement",
    "Contradiction",
    "ComparisonResult",
    "TemporalAnomaly",
    "ScoredContradiction",
    "ContradictionReport",
]

logger = logging.getLogger(__name__)


class ContradictionEngine:
    """Orchestrates the full contradiction-detection pipeline.

    Pipeline stages:
    1. **Extract** — pull attributed statements from document text.
    2. **Normalize** — canonicalize text, extract keywords / entities / dates.
    3. **Compare** — pairwise contradiction detection via TF-IDF + entity diff.
    4. **Temporal check** — timeline anomaly scan.
    5. **Score** — assign severity, impeachment value, legal significance.
    6. **Report** — render markdown / JSON / HTML; persist to DB.
    """

    def __init__(self, db_path: Optional[str] = None) -> None:
        self._db_path = db_path or config.DB_PATH
        self._extractor = StatementExtractor()
        self._normalizer = StatementNormalizer()
        self._comparator = StatementComparator()
        self._temporal = TemporalChecker()
        self._scorer = ContradictionScorer()
        self._reporter = ContradictionReport()

    # ------------------------------------------------------------------
    # DB helpers
    # ------------------------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        """Open a connection with mandatory PRAGMAs."""
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        for pragma in config.DB_PRAGMAS:
            conn.execute(pragma)
        return conn

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def scan(
        self,
        source: str = "db",
        lane: Optional[str] = None,
        fmt: str = "markdown",
    ) -> str:
        """Full contradiction scan.

        Parameters
        ----------
        source:
            ``"db"`` reads from the central litigation DB.
        lane:
            Optional case lane filter (``"A"``, ``"B"``, etc.).
        fmt:
            Report format — ``"markdown"``, ``"json"``, ``"html"``.

        Returns
        -------
        str
            Formatted report.
        """
        logger.info("Starting full scan (source=%s, lane=%s)", source, lane)
        raw_statements = self._load_from_db(lane) if source == "db" else []

        if not raw_statements:
            logger.warning("No statements found — nothing to compare.")
            return self._reporter.generate([], fmt=fmt)

        normalized = [self._normalizer.normalize(s) for s in raw_statements]
        contradictions = self._comparator.find_contradictions(normalized)

        # Temporal anomalies → convert to contradictions
        anomalies = self._temporal.check_timeline(normalized)
        for anom in anomalies:
            if len(anom.statements_involved) >= 2:
                contradictions.append(Contradiction(
                    statement_a=anom.statements_involved[0],
                    statement_b=anom.statements_involved[1],
                    contradiction_type="TEMPORAL",
                    severity=anom.severity,
                    explanation=anom.description,
                ))

        scored = self._scorer.score_batch(contradictions)

        # Persist
        try:
            self._reporter.store_to_db(scored, lane=lane or "", db_path=self._db_path)
        except Exception:
            logger.exception("Failed to persist contradiction reports to DB")

        return self._reporter.generate(scored, fmt=fmt)

    def scan_documents(
        self,
        doc_ids: list[int],
        fmt: str = "markdown",
    ) -> str:
        """Targeted scan on specific document IDs."""
        logger.info("Targeted scan on doc_ids=%s", doc_ids)
        raw_statements = self._load_documents(doc_ids)
        if not raw_statements:
            return self._reporter.generate([], fmt=fmt)

        normalized = [self._normalizer.normalize(s) for s in raw_statements]
        contradictions = self._comparator.find_contradictions(normalized)
        anomalies = self._temporal.check_timeline(normalized)
        for anom in anomalies:
            if len(anom.statements_involved) >= 2:
                contradictions.append(Contradiction(
                    statement_a=anom.statements_involved[0],
                    statement_b=anom.statements_involved[1],
                    contradiction_type="TEMPORAL",
                    severity=anom.severity,
                    explanation=anom.description,
                ))

        scored = self._scorer.score_batch(contradictions)
        return self._reporter.generate(scored, fmt=fmt)

    def scan_text(
        self,
        texts: list[tuple[str, dict]],
        fmt: str = "markdown",
    ) -> str:
        """Scan raw text pairs ``(text, metadata_dict)`` without DB."""
        all_stmts: list[Statement] = []
        for text, meta in texts:
            all_stmts.extend(self._extractor.extract_statements(text, meta))

        normalized = [self._normalizer.normalize(s) for s in all_stmts]
        contradictions = self._comparator.find_contradictions(normalized)
        anomalies = self._temporal.check_timeline(normalized)
        for anom in anomalies:
            if len(anom.statements_involved) >= 2:
                contradictions.append(Contradiction(
                    statement_a=anom.statements_involved[0],
                    statement_b=anom.statements_involved[1],
                    contradiction_type="TEMPORAL",
                    severity=anom.severity,
                    explanation=anom.description,
                ))

        scored = self._scorer.score_batch(contradictions)
        return self._reporter.generate(scored, fmt=fmt)

    def get_stats(self) -> dict:
        """Return contradiction statistics from the DB."""
        conn = self._connect()
        try:
            # Ensure table exists
            conn.execute(
                "CREATE TABLE IF NOT EXISTS contradiction_reports "
                "(id INTEGER PRIMARY KEY AUTOINCREMENT, "
                " statement_a_source TEXT, statement_a_text TEXT, "
                " statement_a_date TEXT, statement_b_source TEXT, "
                " statement_b_text TEXT, statement_b_date TEXT, "
                " speaker TEXT, contradiction_type TEXT, severity TEXT, "
                " severity_score REAL, impeachment_value TEXT, lane TEXT, "
                " created_at TEXT DEFAULT (datetime('now')))"
            )
            row = conn.execute(
                "SELECT "
                "  (SELECT COUNT(*) FROM contradiction_reports) AS total, "
                "  (SELECT COUNT(*) FROM contradiction_reports WHERE severity='CRITICAL') AS critical, "
                "  (SELECT COUNT(*) FROM contradiction_reports WHERE severity='MAJOR') AS major, "
                "  (SELECT COUNT(*) FROM contradiction_reports WHERE severity='MINOR') AS minor, "
                "  (SELECT AVG(severity_score) FROM contradiction_reports) AS avg_score"
            ).fetchone()
            return {
                "total": row["total"],
                "critical": row["critical"],
                "major": row["major"],
                "minor": row["minor"],
                "avg_severity_score": round(row["avg_score"] or 0, 1),
            }
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # DB loaders
    # ------------------------------------------------------------------

    def _load_from_db(self, lane: Optional[str] = None) -> list[Statement]:
        """Load statements from the ``documents`` table."""
        conn = self._connect()
        try:
            # Check what columns actually exist
            cols = {
                r[1] for r in conn.execute("PRAGMA table_info(documents)").fetchall()
            }
            if "content" not in cols:
                logger.warning("documents table missing 'content' column — skipping DB load")
                return []

            query = "SELECT id, title, content FROM documents WHERE content IS NOT NULL AND content != ''"
            rows = conn.execute(query).fetchall()

            all_stmts: list[Statement] = []
            for row in rows:
                meta = {
                    "file_path": row["title"],
                    "page_number": 0,
                    "doc_id": row["id"],
                }
                stmts = self._extractor.extract_statements(row["content"] or "", meta)
                all_stmts.extend(stmts)

            logger.info("Loaded %d statements from %d documents", len(all_stmts), len(rows))
            return all_stmts
        except sqlite3.OperationalError as exc:
            logger.error("DB load error: %s", exc)
            return []
        finally:
            conn.close()

    def _load_documents(self, doc_ids: list[int]) -> list[Statement]:
        """Load statements from specific document IDs."""
        if not doc_ids:
            return []

        conn = self._connect()
        try:
            placeholders = ",".join("?" for _ in doc_ids)
            query = (
                f"SELECT id, title, content FROM documents "
                f"WHERE id IN ({placeholders}) AND content IS NOT NULL"
            )
            rows = conn.execute(query, doc_ids).fetchall()

            all_stmts: list[Statement] = []
            for row in rows:
                meta = {
                    "file_path": row["title"],
                    "page_number": 0,
                    "doc_id": row["id"],
                }
                stmts = self._extractor.extract_statements(row["content"] or "", meta)
                all_stmts.extend(stmts)

            return all_stmts
        except sqlite3.OperationalError as exc:
            logger.error("DB load error: %s", exc)
            return []
        finally:
            conn.close()
