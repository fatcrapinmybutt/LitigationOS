# -*- coding: utf-8 -*-
"""
brain_evolver_daemon.py — Multi-Brain Maintenance Daemon
==========================================================
Scheduled maintenance for the LitigationOS Multi-Brain Universe databases:
dedup entries, rebuild FTS indexes, quality scoring, stale entry pruning,
WAL checkpointing, integrity checks, and index optimization.

Brains maintained:
  - litigation_context.db   — Central DB (694 tables, 10.9 GB)
  - lane_A_custody.db       — Custody brain
  - lane_B_housing.db       — Housing brain
  - lane_C_convergence.db   — Convergence brain
  - lane_D_ppo.db           — PPO brain
  - lane_E_misconduct.db    — Misconduct brain
  - lane_F_appellate.db     — Appellate brain
  - master_index.db         — Agent index
  - mcr_rules.db            — MCR rules

Maintenance operations:
  - Content-based dedup (CRITICAL: peek inside documents, not hash-only)
  - FTS5 index rebuild
  - Stale entry pruning (configurable age threshold)
  - Entry quality scoring (completeness, accuracy, freshness)
  - WAL checkpoint (TRUNCATE mode)
  - Integrity check (PRAGMA integrity_check)
  - Index optimization (ANALYZE + REINDEX)

Zero external dependencies. Local-only.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import sqlite3
import time
from collections import Counter
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger("legal_ai.brain_evolver_daemon")

_HERE = Path(__file__).resolve().parent
_SYSTEM = _HERE.parent                    # 00_SYSTEM
_REPO = _SYSTEM.parent                    # LitigationOS root
_DB_PATH = _REPO / "litigation_context.db"
_BRAINS_DIR = _SYSTEM / "brains"

# ---------------------------------------------------------------------------
# Brain registry
# ---------------------------------------------------------------------------

BRAIN_REGISTRY: List[Dict[str, str]] = [
    {"name": "litigation_context", "file": "litigation_context.db",
     "search_dirs": [str(_REPO)], "description": "Central DB (694 tables)"},
    {"name": "lane_A_custody", "file": "lane_A_custody.db",
     "search_dirs": [str(_REPO), str(_BRAINS_DIR)], "description": "Custody brain"},
    {"name": "lane_B_housing", "file": "lane_B_housing.db",
     "search_dirs": [str(_REPO), str(_BRAINS_DIR)], "description": "Housing brain"},
    {"name": "lane_C_convergence", "file": "lane_C_convergence.db",
     "search_dirs": [str(_REPO), str(_BRAINS_DIR)], "description": "Convergence brain"},
    {"name": "lane_D_ppo", "file": "lane_D_ppo.db",
     "search_dirs": [str(_REPO), str(_BRAINS_DIR)], "description": "PPO brain"},
    {"name": "lane_E_misconduct", "file": "lane_E_misconduct.db",
     "search_dirs": [str(_REPO), str(_BRAINS_DIR)], "description": "Misconduct brain"},
    {"name": "lane_F_appellate", "file": "lane_F_appellate.db",
     "search_dirs": [str(_REPO), str(_BRAINS_DIR)], "description": "Appellate brain"},
    {"name": "master_index", "file": "master_index.db",
     "search_dirs": [str(_REPO), str(_SYSTEM / "pipeline" / "agents")],
     "description": "Agent index"},
    {"name": "mcr_rules", "file": "mcr_rules.db",
     "search_dirs": [str(_REPO)], "description": "MCR rules database"},
]

# ---------------------------------------------------------------------------
# DB DDL
# ---------------------------------------------------------------------------

_MAINTENANCE_LOG_DDL = """\
CREATE TABLE IF NOT EXISTS brain_maintenance_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    brain_name TEXT NOT NULL,
    action TEXT NOT NULL,
    performed_at TEXT NOT NULL,
    items_processed INTEGER DEFAULT 0,
    items_removed INTEGER DEFAULT 0,
    details TEXT
)"""

# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class BrainStatus:
    """Status snapshot for a single brain database."""

    brain_name: str
    db_path: str = ""
    table_count: int = 0
    row_count: int = 0
    size_bytes: int = 0
    has_fts: bool = False
    fts_table_count: int = 0
    stale_entries: int = 0
    duplicate_entries: int = 0
    quality_score: float = 0.0
    last_maintained: Optional[str] = None
    integrity_ok: bool = True
    wal_size_bytes: int = 0
    freelist_pages: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class MaintenanceResult:
    """Result of a single maintenance action on a brain."""

    brain_name: str
    action: str
    started_at: str = ""
    completed_at: str = ""
    items_processed: int = 0
    items_removed: int = 0
    items_updated: int = 0
    size_before: int = 0
    size_after: int = 0
    duration_ms: float = 0.0
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class MaintenanceReport:
    """Complete maintenance report across all brains."""

    generated_at: str = ""
    brains_maintained: int = 0
    total_actions: int = 0
    total_items_processed: int = 0
    total_items_removed: int = 0
    space_saved_bytes: int = 0
    results: List[MaintenanceResult] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "generated_at": self.generated_at,
            "brains_maintained": self.brains_maintained,
            "total_actions": self.total_actions,
            "total_items_processed": self.total_items_processed,
            "total_items_removed": self.total_items_removed,
            "space_saved_bytes": self.space_saved_bytes,
            "space_saved_mb": round(self.space_saved_bytes / (1024 ** 2), 2),
            "results": [r.to_dict() for r in self.results],
            "recommendations": self.recommendations,
        }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _find_brain_path(brain_info: Dict[str, str]) -> Optional[Path]:
    """Locate a brain database file across search directories."""
    filename = brain_info["file"]
    for search_dir in brain_info.get("search_dirs", [str(_REPO)]):
        candidate = Path(search_dir) / filename
        if candidate.exists():
            return candidate
    return None


def _tokenize_text(text: str) -> List[str]:
    """Simple whitespace + punctuation tokenizer for dedup comparison."""
    return re.findall(r"\w+", text.lower())


def _jaccard_similarity(tokens_a: List[str], tokens_b: List[str]) -> float:
    """Compute Jaccard similarity between two token lists."""
    if not tokens_a or not tokens_b:
        return 0.0
    set_a = set(tokens_a)
    set_b = set(tokens_b)
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union > 0 else 0.0


# ---------------------------------------------------------------------------
# BrainEvolverDaemon
# ---------------------------------------------------------------------------


class BrainEvolverDaemon:
    """Scheduled maintenance for Multi-Brain Universe databases.

    Provides dedup, FTS rebuild, stale pruning, quality scoring,
    WAL checkpointing, integrity checks, and index optimization
    across all brain databases in the LitigationOS ecosystem.
    """

    # Content-based dedup threshold (Jaccard similarity)
    DEDUP_THRESHOLD = 0.85

    # Default stale age
    DEFAULT_STALE_DAYS = 365

    # Quality scoring weights
    _QUALITY_WEIGHTS = {
        "has_content": 0.30,
        "has_timestamp": 0.15,
        "has_source": 0.15,
        "content_length": 0.20,
        "freshness": 0.20,
    }

    def __init__(
        self,
        db_path: Optional[str] = None,
        brains_dir: Optional[str] = None,
    ):
        self._db_path = Path(db_path) if db_path else _DB_PATH
        self._brains_dir = Path(brains_dir) if brains_dir else _BRAINS_DIR
        self._actions_performed = 0
        self._total_items_processed = 0
        self._total_items_removed = 0
        self._brain_cache: Dict[str, BrainStatus] = {}

        self._ensure_tables()

    # -- DB helpers ---------------------------------------------------------

    def _open_db(self, path: Optional[Path] = None) -> sqlite3.Connection:
        """Open a DB connection with required PRAGMAs."""
        target = path or self._db_path
        conn = sqlite3.connect(str(target))
        conn.execute("PRAGMA busy_timeout = 60000")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA cache_size = -32000")
        conn.execute("PRAGMA temp_store = MEMORY")
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_tables(self) -> None:
        """Create brain_maintenance_log table if it does not exist."""
        if not self._db_path.exists():
            logger.warning("DB not found at %s — table creation deferred", self._db_path)
            return
        try:
            conn = self._open_db()
            conn.execute(_MAINTENANCE_LOG_DDL)
            conn.commit()
            conn.close()
            logger.debug("brain_maintenance_log table ensured")
        except sqlite3.Error as exc:
            logger.warning("Could not ensure maintenance log table: %s", exc)

    def _persist_result(self, result: MaintenanceResult) -> None:
        """Write a maintenance result to the central DB."""
        if not self._db_path.exists():
            return
        try:
            conn = self._open_db()
            conn.execute(
                "INSERT INTO brain_maintenance_log "
                "(brain_name, action, performed_at, items_processed, items_removed, details) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    result.brain_name,
                    result.action,
                    result.completed_at or datetime.now().isoformat(),
                    result.items_processed,
                    result.items_removed,
                    json.dumps(result.to_dict(), default=str),
                ),
            )
            conn.commit()
            conn.close()
        except sqlite3.Error as exc:
            logger.debug("Could not persist maintenance result: %s", exc)

    def _get_last_maintained(self, brain_name: str) -> Optional[str]:
        """Get the last maintenance timestamp for a brain from the log."""
        if not self._db_path.exists():
            return None
        try:
            conn = self._open_db()
            row = conn.execute(
                "SELECT MAX(performed_at) FROM brain_maintenance_log "
                "WHERE brain_name = ?",
                (brain_name,),
            ).fetchone()
            conn.close()
            return row[0] if row and row[0] else None
        except sqlite3.Error:
            return None

    # -- Brain scanning -----------------------------------------------------

    def scan_brains(self) -> List[BrainStatus]:
        """Scan all registered brains and return their status.

        Returns:
            List of BrainStatus for each located brain database.
        """
        results: List[BrainStatus] = []

        for brain_info in BRAIN_REGISTRY:
            brain_path = _find_brain_path(brain_info)
            if brain_path is None:
                results.append(BrainStatus(
                    brain_name=brain_info["name"],
                    db_path="",
                ))
                continue

            status = self._assess_brain(brain_path, brain_info["name"])
            results.append(status)
            self._brain_cache[brain_info["name"]] = status

        logger.info("Scanned %d brains, %d found on disk",
                     len(BRAIN_REGISTRY),
                     sum(1 for s in results if s.db_path))
        return results

    def _assess_brain(self, brain_path: Path, brain_name: str) -> BrainStatus:
        """Assess a single brain database for status metrics."""
        status = BrainStatus(
            brain_name=brain_name,
            db_path=str(brain_path),
        )

        try:
            status.size_bytes = brain_path.stat().st_size

            # WAL size
            wal_path = brain_path.with_suffix(".db-wal")
            if wal_path.exists():
                status.wal_size_bytes = wal_path.stat().st_size

            conn = self._open_db(brain_path)

            # Table count
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' "
                "AND name NOT LIKE 'sqlite_%'"
            ).fetchall()
            status.table_count = len(tables)

            # FTS tables
            fts_tables = [
                t["name"] for t in tables
                if t["name"].endswith("_fts") or "_fts_" in t["name"]
            ]
            status.has_fts = len(fts_tables) > 0
            status.fts_table_count = len(fts_tables)

            # Total row count (sample first 50 tables to avoid timeout on huge DBs)
            total_rows = 0
            for table in tables[:50]:
                try:
                    count = conn.execute(
                        f'SELECT COUNT(*) FROM "{table["name"]}"'
                    ).fetchone()[0]
                    total_rows += count
                except sqlite3.Error:
                    pass
            status.row_count = total_rows

            # Freelist
            freelist = conn.execute("PRAGMA freelist_count").fetchone()[0]
            status.freelist_pages = freelist

            # Last maintained
            status.last_maintained = self._get_last_maintained(brain_name)

            conn.close()

        except sqlite3.Error as exc:
            logger.warning("Could not assess brain %s: %s", brain_name, exc)
        except OSError as exc:
            logger.warning("OS error assessing brain %s: %s", brain_name, exc)

        return status

    # -- Maintenance operations ---------------------------------------------

    def maintain_brain(
        self,
        brain_path: str,
        actions: Optional[List[str]] = None,
    ) -> List[MaintenanceResult]:
        """Run maintenance operations on a single brain.

        Args:
            brain_path: Filesystem path to the brain .db file.
            actions: List of actions to run. If None, runs all applicable.
                     Options: dedup, fts_rebuild, prune, quality_score,
                     wal_checkpoint, integrity, reindex

        Returns:
            List of MaintenanceResult, one per action.
        """
        path = Path(brain_path)
        if not path.exists():
            return [MaintenanceResult(
                brain_name=path.stem,
                action="locate",
                error=f"Brain not found: {path}",
            )]

        brain_name = path.stem
        all_actions = actions or [
            "integrity", "wal_checkpoint", "dedup",
            "fts_rebuild", "prune", "quality_score", "reindex",
        ]

        results: List[MaintenanceResult] = []

        action_map = {
            "dedup": self.dedup_brain,
            "fts_rebuild": self.rebuild_fts,
            "prune": self.prune_stale,
            "quality_score": self.score_quality,
            "wal_checkpoint": self.checkpoint_wal,
            "integrity": lambda p: MaintenanceResult(
                brain_name=Path(p).stem,
                action="integrity",
                **self._run_integrity(p),
            ),
            "reindex": self._run_reindex,
        }

        for action in all_actions:
            handler = action_map.get(action)
            if handler is None:
                logger.warning("Unknown maintenance action: %s", action)
                continue

            try:
                result = handler(str(path))
                results.append(result)
                self._actions_performed += 1
                self._total_items_processed += result.items_processed
                self._total_items_removed += result.items_removed
                self._persist_result(result)
            except Exception as exc:
                logger.warning("Action %s failed on %s: %s", action, brain_name, exc)
                results.append(MaintenanceResult(
                    brain_name=brain_name,
                    action=action,
                    error=str(exc),
                ))

        return results

    def maintain_all(self) -> MaintenanceReport:
        """Run maintenance on all registered brains.

        Returns:
            MaintenanceReport summarizing all actions across all brains.
        """
        start = time.monotonic()
        now = datetime.now().isoformat()
        all_results: List[MaintenanceResult] = []
        brains_maintained = 0

        for brain_info in BRAIN_REGISTRY:
            brain_path = _find_brain_path(brain_info)
            if brain_path is None:
                logger.debug("Skipping %s — not found", brain_info["name"])
                continue

            logger.info("Maintaining %s (%s)...", brain_info["name"], brain_path)
            results = self.maintain_brain(str(brain_path))
            all_results.extend(results)
            brains_maintained += 1

        # Compute totals
        total_processed = sum(r.items_processed for r in all_results)
        total_removed = sum(r.items_removed for r in all_results)
        space_saved = sum(
            max(0, r.size_before - r.size_after)
            for r in all_results if r.size_before > 0
        )

        # Recommendations
        recommendations = self._build_recommendations(all_results)

        report = MaintenanceReport(
            generated_at=now,
            brains_maintained=brains_maintained,
            total_actions=len(all_results),
            total_items_processed=total_processed,
            total_items_removed=total_removed,
            space_saved_bytes=space_saved,
            results=all_results,
            recommendations=recommendations,
        )

        elapsed = (time.monotonic() - start) * 1000
        logger.info(
            "Maintenance complete: %d brains, %d actions, %.0f ms",
            brains_maintained, len(all_results), elapsed,
        )
        return report

    # -- Dedup (content-based, NOT hash-only) -------------------------------

    def dedup_brain(self, brain_path: str) -> MaintenanceResult:
        """Find duplicate entries via content-based comparison.

        CRITICAL: Uses token-level Jaccard similarity, NOT just hash comparison.
        Per user preference: 'peek inside the document to ensure they are the same.'

        Args:
            brain_path: Path to the brain .db file.

        Returns:
            MaintenanceResult with dedup statistics.
        """
        path = Path(brain_path)
        brain_name = path.stem
        started = datetime.now().isoformat()
        start = time.monotonic()
        size_before = path.stat().st_size if path.exists() else 0

        items_processed = 0
        duplicates_found = 0

        try:
            conn = self._open_db(path)

            # Get all tables with text content columns
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' "
                "AND name NOT LIKE 'sqlite_%' AND name NOT LIKE '%_fts%' "
                "AND name NOT LIKE '%_config' AND name NOT LIKE '%_content'"
            ).fetchall()

            for table in tables:
                table_name = table["name"]
                try:
                    dupes = self._dedup_table(conn, table_name)
                    items_processed += dupes.get("checked", 0)
                    duplicates_found += dupes.get("duplicates", 0)
                except sqlite3.Error as exc:
                    logger.debug("Dedup skip %s.%s: %s", brain_name, table_name, exc)

            conn.close()

        except sqlite3.Error as exc:
            logger.warning("Dedup error on %s: %s", brain_name, exc)
            return MaintenanceResult(
                brain_name=brain_name,
                action="dedup",
                started_at=started,
                completed_at=datetime.now().isoformat(),
                error=str(exc),
            )

        elapsed = (time.monotonic() - start) * 1000
        size_after = path.stat().st_size if path.exists() else 0

        return MaintenanceResult(
            brain_name=brain_name,
            action="dedup",
            started_at=started,
            completed_at=datetime.now().isoformat(),
            items_processed=items_processed,
            items_removed=duplicates_found,
            size_before=size_before,
            size_after=size_after,
            duration_ms=round(elapsed, 1),
        )

    def _dedup_table(self, conn: sqlite3.Connection, table_name: str) -> Dict[str, int]:
        """Content-based dedup on a single table. Returns counts."""
        # Find text columns
        columns = conn.execute(f'PRAGMA table_info("{table_name}")').fetchall()
        text_cols = [
            c["name"] for c in columns
            if c["type"].upper() in ("TEXT", "VARCHAR", "CLOB", "")
            and c["name"].lower() not in ("id", "rowid", "created_at", "updated_at")
        ]

        if not text_cols:
            return {"checked": 0, "duplicates": 0}

        # Get primary key column
        pk_col = None
        for c in columns:
            if c["pk"] == 1:
                pk_col = c["name"]
                break
        if pk_col is None:
            pk_col = "rowid"

        # Fetch rows (limit to avoid memory issues on huge tables)
        content_col = text_cols[0]  # Use first text column for comparison
        rows = conn.execute(
            f'SELECT "{pk_col}", "{content_col}" FROM "{table_name}" '
            f'WHERE "{content_col}" IS NOT NULL AND "{content_col}" != "" '
            f"LIMIT 5000"
        ).fetchall()

        if len(rows) < 2:
            return {"checked": len(rows), "duplicates": 0}

        # Token-based dedup: compare content, not just hashes
        checked = 0
        duplicates = 0
        seen_tokens: List[Tuple[Any, List[str]]] = []

        for row in rows:
            pk_val = row[0]
            content = str(row[1] or "")
            if len(content) < 10:
                continue

            tokens = _tokenize_text(content)
            if not tokens:
                continue

            checked += 1
            is_dup = False

            for existing_pk, existing_tokens in seen_tokens:
                similarity = _jaccard_similarity(tokens, existing_tokens)
                if similarity >= self.DEDUP_THRESHOLD:
                    is_dup = True
                    duplicates += 1
                    logger.debug(
                        "Duplicate found in %s: %s ≈ %s (%.2f)",
                        table_name, pk_val, existing_pk, similarity,
                    )
                    break

            if not is_dup:
                seen_tokens.append((pk_val, tokens))

        return {"checked": checked, "duplicates": duplicates}

    # -- FTS rebuild --------------------------------------------------------

    def rebuild_fts(self, brain_path: str) -> MaintenanceResult:
        """Rebuild all FTS5 indexes in a brain database.

        Uses: INSERT INTO fts_table(fts_table) VALUES('rebuild')

        Args:
            brain_path: Path to the brain .db file.

        Returns:
            MaintenanceResult with rebuild statistics.
        """
        path = Path(brain_path)
        brain_name = path.stem
        started = datetime.now().isoformat()
        start = time.monotonic()
        size_before = path.stat().st_size if path.exists() else 0

        rebuilt = 0
        errors: List[str] = []

        try:
            conn = self._open_db(path)

            # Find FTS5 tables
            fts_tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' "
                "AND sql LIKE '%fts5%'"
            ).fetchall()

            for ft in fts_tables:
                fts_name = ft["name"]
                try:
                    conn.execute(
                        f'INSERT INTO "{fts_name}"("{fts_name}") VALUES(\'rebuild\')'
                    )
                    conn.commit()
                    rebuilt += 1
                    logger.debug("Rebuilt FTS: %s.%s", brain_name, fts_name)
                except sqlite3.Error as exc:
                    errors.append(f"{fts_name}: {exc}")
                    logger.debug("FTS rebuild skip %s: %s", fts_name, exc)

            conn.close()

        except sqlite3.Error as exc:
            logger.warning("FTS rebuild error on %s: %s", brain_name, exc)
            return MaintenanceResult(
                brain_name=brain_name,
                action="fts_rebuild",
                started_at=started,
                completed_at=datetime.now().isoformat(),
                error=str(exc),
            )

        elapsed = (time.monotonic() - start) * 1000
        size_after = path.stat().st_size if path.exists() else 0

        result = MaintenanceResult(
            brain_name=brain_name,
            action="fts_rebuild",
            started_at=started,
            completed_at=datetime.now().isoformat(),
            items_processed=rebuilt,
            size_before=size_before,
            size_after=size_after,
            duration_ms=round(elapsed, 1),
        )

        if errors:
            result.error = f"{len(errors)} FTS rebuild errors"

        return result

    # -- Prune stale entries ------------------------------------------------

    def prune_stale(
        self, brain_path: str, max_age_days: int = 365,
    ) -> MaintenanceResult:
        """Identify stale entries older than the threshold.

        Note: This only COUNTS stale entries. Per the no-deletion policy,
        actual removal requires explicit user approval.

        Args:
            brain_path: Path to the brain .db file.
            max_age_days: Age threshold in days (default 365).

        Returns:
            MaintenanceResult with stale entry counts.
        """
        path = Path(brain_path)
        brain_name = path.stem
        started = datetime.now().isoformat()
        start = time.monotonic()

        cutoff = (datetime.now() - timedelta(days=max_age_days)).isoformat()
        stale_count = 0
        tables_checked = 0

        try:
            conn = self._open_db(path)

            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' "
                "AND name NOT LIKE 'sqlite_%' AND name NOT LIKE '%_fts%'"
            ).fetchall()

            for table in tables:
                table_name = table["name"]
                # Look for date columns
                columns = conn.execute(
                    f'PRAGMA table_info("{table_name}")'
                ).fetchall()

                date_cols = [
                    c["name"] for c in columns
                    if any(kw in c["name"].lower() for kw in
                           ("date", "time", "created", "updated", "at", "timestamp"))
                ]

                if not date_cols:
                    continue

                tables_checked += 1
                for date_col in date_cols[:1]:  # Check first date column only
                    try:
                        count = conn.execute(
                            f'SELECT COUNT(*) FROM "{table_name}" '
                            f'WHERE "{date_col}" < ? AND "{date_col}" IS NOT NULL '
                            f'AND "{date_col}" != ""',
                            (cutoff,),
                        ).fetchone()[0]
                        stale_count += count
                    except sqlite3.Error:
                        pass

            conn.close()

        except sqlite3.Error as exc:
            logger.warning("Prune scan error on %s: %s", brain_name, exc)

        elapsed = (time.monotonic() - start) * 1000

        return MaintenanceResult(
            brain_name=brain_name,
            action="prune",
            started_at=started,
            completed_at=datetime.now().isoformat(),
            items_processed=tables_checked,
            items_removed=0,  # No actual removal — report only
            items_updated=stale_count,  # Stale entries identified
            duration_ms=round(elapsed, 1),
        )

    # -- Quality scoring ----------------------------------------------------

    def score_quality(self, brain_path: str) -> MaintenanceResult:
        """Score entries on quality dimensions: completeness, freshness, size.

        Args:
            brain_path: Path to the brain .db file.

        Returns:
            MaintenanceResult with quality scoring summary.
        """
        path = Path(brain_path)
        brain_name = path.stem
        started = datetime.now().isoformat()
        start = time.monotonic()

        tables_scored = 0
        total_score = 0.0
        entries_scored = 0

        try:
            conn = self._open_db(path)

            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' "
                "AND name NOT LIKE 'sqlite_%' AND name NOT LIKE '%_fts%'"
            ).fetchall()

            for table in tables:
                table_name = table["name"]
                try:
                    score = self._score_table_quality(conn, table_name)
                    if score is not None:
                        total_score += score
                        tables_scored += 1
                        entries_scored += 1
                except sqlite3.Error:
                    pass

            conn.close()

        except sqlite3.Error as exc:
            logger.warning("Quality scoring error on %s: %s", brain_name, exc)

        avg_score = (total_score / tables_scored) if tables_scored > 0 else 0.0
        elapsed = (time.monotonic() - start) * 1000

        return MaintenanceResult(
            brain_name=brain_name,
            action="quality_score",
            started_at=started,
            completed_at=datetime.now().isoformat(),
            items_processed=entries_scored,
            items_updated=round(avg_score),
            duration_ms=round(elapsed, 1),
        )

    def _score_table_quality(
        self, conn: sqlite3.Connection, table_name: str,
    ) -> Optional[float]:
        """Score a table's data quality 0-100."""
        columns = conn.execute(f'PRAGMA table_info("{table_name}")').fetchall()
        if not columns:
            return None

        col_names = [c["name"] for c in columns]
        row_count = conn.execute(
            f'SELECT COUNT(*) FROM "{table_name}"'
        ).fetchone()[0]

        if row_count == 0:
            return 0.0

        score = 0.0

        # Has content: check for text columns with data
        text_cols = [
            c for c in col_names
            if any(kw in c.lower() for kw in
                   ("text", "content", "body", "description", "title", "name"))
        ]
        if text_cols:
            non_empty = conn.execute(
                f'SELECT COUNT(*) FROM "{table_name}" '
                f'WHERE "{text_cols[0]}" IS NOT NULL AND "{text_cols[0]}" != ""'
            ).fetchone()[0]
            content_ratio = non_empty / max(row_count, 1)
            score += content_ratio * self._QUALITY_WEIGHTS["has_content"] * 100

        # Has timestamps
        time_cols = [
            c for c in col_names
            if any(kw in c.lower() for kw in ("date", "time", "created", "updated"))
        ]
        if time_cols:
            score += self._QUALITY_WEIGHTS["has_timestamp"] * 100

        # Has source/provenance
        source_cols = [
            c for c in col_names
            if any(kw in c.lower() for kw in ("source", "origin", "path", "file", "url"))
        ]
        if source_cols:
            score += self._QUALITY_WEIGHTS["has_source"] * 100

        # Content length (average)
        if text_cols:
            try:
                avg_len = conn.execute(
                    f'SELECT AVG(LENGTH("{text_cols[0]}")) FROM "{table_name}" '
                    f'WHERE "{text_cols[0]}" IS NOT NULL'
                ).fetchone()[0]
                if avg_len and avg_len > 100:
                    score += self._QUALITY_WEIGHTS["content_length"] * 100
                elif avg_len and avg_len > 20:
                    score += self._QUALITY_WEIGHTS["content_length"] * 50
            except sqlite3.Error:
                pass

        # Freshness: check if recent entries exist
        if time_cols:
            try:
                recent_cutoff = (
                    datetime.now() - timedelta(days=90)
                ).isoformat()
                recent = conn.execute(
                    f'SELECT COUNT(*) FROM "{table_name}" '
                    f'WHERE "{time_cols[0]}" > ?',
                    (recent_cutoff,),
                ).fetchone()[0]
                freshness_ratio = min(1.0, recent / max(row_count, 1) * 5)
                score += freshness_ratio * self._QUALITY_WEIGHTS["freshness"] * 100
            except sqlite3.Error:
                pass

        return min(100.0, score)

    # -- WAL checkpoint -----------------------------------------------------

    def checkpoint_wal(self, brain_path: str) -> MaintenanceResult:
        """Force WAL checkpoint to reclaim space.

        Uses PRAGMA wal_checkpoint(TRUNCATE).

        Args:
            brain_path: Path to the brain .db file.

        Returns:
            MaintenanceResult with checkpoint statistics.
        """
        path = Path(brain_path)
        brain_name = path.stem
        started = datetime.now().isoformat()
        start = time.monotonic()
        size_before = path.stat().st_size if path.exists() else 0

        wal_path = path.with_suffix(".db-wal")
        wal_before = wal_path.stat().st_size if wal_path.exists() else 0

        try:
            conn = self._open_db(path)
            result_row = conn.execute(
                "PRAGMA wal_checkpoint(TRUNCATE)"
            ).fetchone()
            conn.close()

            wal_after = wal_path.stat().st_size if wal_path.exists() else 0
            pages_checkpointed = result_row[1] if result_row else 0

        except sqlite3.Error as exc:
            logger.warning("WAL checkpoint error on %s: %s", brain_name, exc)
            return MaintenanceResult(
                brain_name=brain_name,
                action="wal_checkpoint",
                started_at=started,
                completed_at=datetime.now().isoformat(),
                error=str(exc),
            )

        elapsed = (time.monotonic() - start) * 1000
        size_after = path.stat().st_size if path.exists() else 0

        return MaintenanceResult(
            brain_name=brain_name,
            action="wal_checkpoint",
            started_at=started,
            completed_at=datetime.now().isoformat(),
            items_processed=pages_checkpointed,
            size_before=size_before + wal_before,
            size_after=size_after + (wal_path.stat().st_size if wal_path.exists() else 0),
            duration_ms=round(elapsed, 1),
        )

    # -- Integrity check ----------------------------------------------------

    def check_integrity(self, brain_path: str) -> Dict[str, Any]:
        """Run PRAGMA integrity_check on a brain database.

        Args:
            brain_path: Path to the brain .db file.

        Returns:
            Dict with integrity check results.
        """
        path = Path(brain_path)
        result: Dict[str, Any] = {
            "brain_name": path.stem,
            "checked_at": datetime.now().isoformat(),
        }

        if not path.exists():
            result["ok"] = False
            result["error"] = f"File not found: {path}"
            return result

        try:
            conn = self._open_db(path)
            integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
            conn.close()

            result["ok"] = integrity == "ok"
            result["result"] = integrity

        except sqlite3.Error as exc:
            result["ok"] = False
            result["error"] = str(exc)

        return result

    def _run_integrity(self, brain_path: str) -> Dict[str, Any]:
        """Run integrity check and return result fields for MaintenanceResult."""
        check = self.check_integrity(brain_path)
        return {
            "started_at": check.get("checked_at", ""),
            "completed_at": datetime.now().isoformat(),
            "items_processed": 1,
            "items_removed": 0,
            "error": check.get("error") if not check.get("ok") else None,
        }

    # -- Reindex ------------------------------------------------------------

    def _run_reindex(self, brain_path: str) -> MaintenanceResult:
        """Run ANALYZE + REINDEX on a brain database.

        Args:
            brain_path: Path to the brain .db file.

        Returns:
            MaintenanceResult with reindex statistics.
        """
        path = Path(brain_path)
        brain_name = path.stem
        started = datetime.now().isoformat()
        start = time.monotonic()
        size_before = path.stat().st_size if path.exists() else 0

        try:
            conn = self._open_db(path)

            # Count indexes
            index_count = conn.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type = 'index'"
            ).fetchone()[0]

            conn.execute("ANALYZE")
            conn.execute("REINDEX")
            conn.commit()
            conn.close()

        except sqlite3.Error as exc:
            logger.warning("Reindex error on %s: %s", brain_name, exc)
            return MaintenanceResult(
                brain_name=brain_name,
                action="reindex",
                started_at=started,
                completed_at=datetime.now().isoformat(),
                error=str(exc),
            )

        elapsed = (time.monotonic() - start) * 1000
        size_after = path.stat().st_size if path.exists() else 0

        return MaintenanceResult(
            brain_name=brain_name,
            action="reindex",
            started_at=started,
            completed_at=datetime.now().isoformat(),
            items_processed=index_count,
            size_before=size_before,
            size_after=size_after,
            duration_ms=round(elapsed, 1),
        )

    # -- Recommendations ----------------------------------------------------

    def _build_recommendations(
        self, results: List[MaintenanceResult],
    ) -> List[str]:
        """Build prioritized recommendations from maintenance results."""
        recs: List[str] = []

        # Check for errors
        errors = [r for r in results if r.error]
        if errors:
            recs.append(
                f"WARNING: {len(errors)} action(s) had errors — "
                "review logs for details"
            )

        # Dedup findings
        dedup_results = [r for r in results if r.action == "dedup" and r.items_removed > 0]
        if dedup_results:
            total_dupes = sum(r.items_removed for r in dedup_results)
            brains = [r.brain_name for r in dedup_results]
            recs.append(
                f"Found {total_dupes} duplicate entries across "
                f"{len(brains)} brain(s): {', '.join(brains)}. "
                "Review and merge or move duplicates to I:\\ drive."
            )

        # Stale entries
        prune_results = [r for r in results if r.action == "prune" and r.items_updated > 0]
        if prune_results:
            total_stale = sum(r.items_updated for r in prune_results)
            recs.append(
                f"Identified {total_stale} stale entries (>365 days old). "
                "Consider archiving or flagging for review."
            )

        # WAL size
        wal_results = [
            r for r in results
            if r.action == "wal_checkpoint" and r.size_before > 100 * 1024 * 1024
        ]
        if wal_results:
            recs.append(
                "Large WAL files detected before checkpoint. "
                "Consider running checkpoints more frequently."
            )

        # Space savings
        space_saved = sum(
            max(0, r.size_before - r.size_after)
            for r in results if r.size_before > 0
        )
        if space_saved > 1024 * 1024:
            recs.append(
                f"Recovered {space_saved / (1024**2):.1f} MB of disk space."
            )

        # FTS rebuild
        fts_results = [r for r in results if r.action == "fts_rebuild"]
        if fts_results:
            total_rebuilt = sum(r.items_processed for r in fts_results)
            recs.append(f"Rebuilt {total_rebuilt} FTS5 indexes for search performance.")

        if not recs:
            recs.append("All brains are in good health. No action needed.")

        return recs

    # -- Export -------------------------------------------------------------

    def export_report(self, output_path: str) -> str:
        """Export a full maintenance report as JSON.

        Runs maintain_all() if no recent results, then exports.

        Args:
            output_path: Filesystem path for the JSON output.

        Returns:
            The output path written to.
        """
        report = self.maintain_all()
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            json.dumps(report.to_dict(), indent=2, default=str),
            encoding="utf-8",
        )
        logger.info("Maintenance report exported to %s", out)
        return str(out)

    # -- Stats --------------------------------------------------------------

    def get_stats(self) -> dict:
        """Return daemon operational statistics."""
        return {
            "actions_performed": self._actions_performed,
            "total_items_processed": self._total_items_processed,
            "total_items_removed": self._total_items_removed,
            "brains_cached": len(self._brain_cache),
            "registered_brains": len(BRAIN_REGISTRY),
            "db_path": str(self._db_path),
            "brains_dir": str(self._brains_dir),
        }


# ---------------------------------------------------------------------------
# Module-level convenience
# ---------------------------------------------------------------------------


def scan_all_brains() -> List[BrainStatus]:
    """Quick scan of all registered brain databases."""
    return BrainEvolverDaemon().scan_brains()


def run_full_maintenance() -> MaintenanceReport:
    """Run full maintenance on all brains."""
    return BrainEvolverDaemon().maintain_all()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(name)s | %(message)s")
    daemon = BrainEvolverDaemon()

    print("Scanning brains...")
    brains = daemon.scan_brains()
    print(f"Found {len(brains)} registered brains\n")

    for b in brains:
        if b.db_path:
            size_mb = b.size_bytes / (1024 ** 2)
            print(f"  ✓ {b.brain_name:25s}  tables={b.table_count:4d}  "
                  f"rows={b.row_count:8d}  size={size_mb:8.1f} MB  "
                  f"fts={b.fts_table_count}")
        else:
            print(f"  ✗ {b.brain_name:25s}  NOT FOUND")

    print(f"\nStats: {json.dumps(daemon.get_stats(), indent=2)}")
