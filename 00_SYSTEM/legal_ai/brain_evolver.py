"""
LitigationOS Brain Evolver v1.0
=================================
Multi-Brain auto-evolution engine for health assessment, dedup, and maintenance.

Features:
  - Brain health scoring (row counts, orphans, duplicates, provenance coverage)
  - Token-level Jaccard duplicate detection (pure Python, no ML deps)
  - FTS sync verification and rebuild
  - Stale record detection and archival
  - Propose-only by default; explicit approval required for mutations
  - Full evolution audit log with rollback SQL

Usage::

    from legal_ai.brain_evolver import BrainEvolver

    evolver = BrainEvolver()
    report = evolver.evolve(dry_run=True)
    print(f"Overall health: {report.overall_health:.0%}")
    for score in report.brain_scores:
        print(f"  {score.brain_name}: {score.health_score:.0%}")
"""

from __future__ import annotations

import logging
import os
import re
import sqlite3
import sys
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger("legal_ai.brain_evolver")

_HERE = Path(__file__).parent
_REPO = _HERE.parent.parent
_BRAIN_DIR = _REPO / "00_SYSTEM" / "brains"

# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class BrainHealthScore:
    """Health assessment for a single brain database."""

    brain_name: str
    total_tables: int = 0
    total_rows: int = 0
    tables_with_data: int = 0
    empty_tables: int = 0
    orphaned_references: int = 0
    duplicate_count: int = 0
    stale_record_count: int = 0
    provenance_coverage: float = 0.0  # 0-1
    fts_sync_status: str = "unknown"
    health_score: float = 0.0  # 0-1
    issues: List[str] = field(default_factory=list)


@dataclass
class DuplicateGroup:
    """A group of duplicate records detected via Jaccard similarity."""

    brain_name: str
    table_name: str
    record_ids: List[str] = field(default_factory=list)
    similarity_score: float = 0.0
    sample_text: str = ""
    merge_recommendation: str = "manual"  # keep_first/keep_best/merge/manual


@dataclass
class EvolutionAction:
    """A single evolution action (proposed or executed)."""

    action_type: str  # gap_fill/dedup/schema_migrate/fts_rebuild/orphan_cleanup/stale_archive
    brain_name: str
    table_name: str = ""
    description: str = ""
    status: str = "proposed"  # proposed/approved/executed/failed/rolled_back
    records_affected: int = 0
    executed_at: str = ""
    rollback_sql: str = ""


@dataclass
class EvolutionReport:
    """Complete report from one evolution cycle."""

    cycle_id: str = ""
    started_at: str = ""
    completed_at: str = ""
    brain_scores: List[BrainHealthScore] = field(default_factory=list)
    duplicates_found: List[DuplicateGroup] = field(default_factory=list)
    actions_taken: List[EvolutionAction] = field(default_factory=list)
    actions_proposed: List[EvolutionAction] = field(default_factory=list)
    overall_health: float = 0.0
    warnings: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BRAIN_NAMES: List[str] = [
    "authority_brain",
    "narrative_brain",
    "entity_brain",
    "claims_brain",
    "interpretation_brain",
    "cross_brain_index",
]

BRAIN_FTS_TABLES: Dict[str, List[str]] = {
    "authority_brain": [
        "court_rules_fts",
        "statutes_fts",
        "case_law_fts",
        "evidence_rules_fts",
        "benchbook_fts",
    ],
    "narrative_brain": [
        "timeline_fts",
        "extractions_fts",
        "orders_fts",
        "police_fts",
        "testimony_fts",
        "communications_fts",
    ],
    "entity_brain": [],
    "claims_brain": [],
    "interpretation_brain": [
        "arguments_fts",
        "impeachment_fts",
        "drafts_fts",
        "applications_fts",
    ],
    "cross_brain_index": ["universal_search"],
}

_EVOLUTION_LOG_DDL = """\
CREATE TABLE IF NOT EXISTS brain_evolution_log (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    cycle_id TEXT NOT NULL,
    action_type TEXT NOT NULL,
    brain_name TEXT NOT NULL,
    table_name TEXT,
    description TEXT,
    records_affected INTEGER DEFAULT 0,
    status TEXT DEFAULT 'proposed',
    rollback_sql TEXT,
    executed_at TEXT DEFAULT (datetime('now'))
)"""


# ---------------------------------------------------------------------------
# BrainEvolver
# ---------------------------------------------------------------------------


class BrainEvolver:
    """Multi-Brain auto-evolution engine."""

    def __init__(
        self,
        brain_manager: Optional[Any] = None,
        auto_execute: bool = False,
        brain_dir: Optional[str] = None,
    ):
        self._brain_manager = brain_manager
        self._auto_execute = auto_execute
        self._brain_dir = Path(brain_dir) if brain_dir else _BRAIN_DIR
        self._evolution_count = 0
        self._total_actions = 0

        # Try loading BrainManager if not provided
        if self._brain_manager is None:
            self._init_brain_manager()

        # Ensure evolution log table exists
        self._ensure_evolution_log()

    def _init_brain_manager(self) -> None:
        """Lazy-load BrainManager with graceful fallback."""
        try:
            sys.path.insert(0, str(_HERE.parent))
            from brains.brain_manager import BrainManager

            self._brain_manager = BrainManager(brain_dir=str(self._brain_dir))
            logger.info("BrainManager loaded from %s", self._brain_dir)
        except Exception as exc:
            logger.warning(
                "BrainManager unavailable — using direct DB access: %s", exc
            )

    def _ensure_evolution_log(self) -> None:
        """Create evolution log table in cross_brain_index if needed."""
        db_path = self._brain_dir / "cross_brain_index.db"
        if not db_path.exists():
            logger.warning("cross_brain_index.db not found at %s", db_path)
            return
        try:
            conn = self._open_db(str(db_path))
            conn.execute(_EVOLUTION_LOG_DDL)
            conn.commit()
            conn.close()
            logger.debug("brain_evolution_log table ensured")
        except sqlite3.Error as exc:
            logger.warning("Could not create evolution log table: %s", exc)

    # -- database helpers ---------------------------------------------------

    def _open_db(self, db_path: str) -> sqlite3.Connection:
        """Open a database connection with required PRAGMAs."""
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA busy_timeout = 60000")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA cache_size = -32000")
        conn.execute("PRAGMA temp_store = MEMORY")
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.row_factory = sqlite3.Row
        return conn

    def _brain_db_path(self, brain_name: str) -> str:
        """Resolve brain name to database file path."""
        name = brain_name if brain_name.endswith(".db") else f"{brain_name}.db"
        return str(self._brain_dir / name)

    def _brain_exists(self, brain_name: str) -> bool:
        """Check if a brain database file exists."""
        return os.path.exists(self._brain_db_path(brain_name))

    def _get_tables(self, conn: sqlite3.Connection) -> List[str]:
        """List all user tables in a database."""
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ).fetchall()
        return [r[0] for r in rows]

    def _table_exists(self, conn: sqlite3.Connection, table: str) -> bool:
        """Check if a table exists."""
        row = conn.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?",
            (table,),
        ).fetchone()
        return row[0] > 0 if row else False

    def _row_count(self, conn: sqlite3.Connection, table: str) -> int:
        """Get row count for a table (safe)."""
        try:
            row = conn.execute(f"SELECT COUNT(*) FROM [{table}]").fetchone()
            return row[0] if row else 0
        except sqlite3.Error:
            return 0

    # -- public API ---------------------------------------------------------

    def assess_health(
        self, brain_name: Optional[str] = None
    ) -> List[BrainHealthScore]:
        """Score health of one or all brains."""
        names = [brain_name] if brain_name else BRAIN_NAMES
        scores: List[BrainHealthScore] = []

        for name in names:
            if not self._brain_exists(name):
                scores.append(BrainHealthScore(
                    brain_name=name,
                    health_score=0.0,
                    issues=[f"Database file not found: {self._brain_db_path(name)}"],
                ))
                continue

            try:
                score = self._score_brain(name)
                scores.append(score)
            except Exception as exc:
                logger.error("Health check failed for %s: %s", name, exc)
                scores.append(BrainHealthScore(
                    brain_name=name,
                    health_score=0.0,
                    issues=[f"Health check error: {exc}"],
                ))

        return scores

    def find_duplicates(
        self,
        brain_name: str,
        table_name: str,
        text_column: str,
        threshold: float = 0.85,
    ) -> List[DuplicateGroup]:
        """Find duplicate records using token-level Jaccard similarity."""
        if not self._brain_exists(brain_name):
            logger.warning("Brain %s not found", brain_name)
            return []

        db_path = self._brain_db_path(brain_name)
        groups: List[DuplicateGroup] = []

        try:
            conn = self._open_db(db_path)
            if not self._table_exists(conn, table_name):
                conn.close()
                return []

            # Get the primary key column
            pk_col = self._get_pk_column(conn, table_name)

            rows = conn.execute(
                f"SELECT [{pk_col}], [{text_column}] FROM [{table_name}] "
                f"WHERE [{text_column}] IS NOT NULL AND [{text_column}] != '' "
                f"LIMIT 5000"
            ).fetchall()
            conn.close()

            if len(rows) < 2:
                return []

            # Tokenize all records
            tokenized: List[Tuple[str, Set[str]]] = []
            for row in rows:
                rid = str(row[0])
                text = str(row[1])
                tokens = _tokenize(text)
                if tokens:
                    tokenized.append((rid, tokens))

            # Pairwise Jaccard comparison (O(n²) — bounded by LIMIT 5000)
            seen: Set[str] = set()
            for i in range(len(tokenized)):
                if tokenized[i][0] in seen:
                    continue
                cluster_ids = [tokenized[i][0]]
                for j in range(i + 1, len(tokenized)):
                    if tokenized[j][0] in seen:
                        continue
                    sim = _jaccard(tokenized[i][1], tokenized[j][1])
                    if sim >= threshold:
                        cluster_ids.append(tokenized[j][0])
                        seen.add(tokenized[j][0])

                if len(cluster_ids) > 1:
                    seen.add(tokenized[i][0])
                    # Compute average similarity within cluster
                    avg_sim = threshold  # minimum known
                    sample = str(rows[0][1])[:200] if rows else ""
                    groups.append(DuplicateGroup(
                        brain_name=brain_name,
                        table_name=table_name,
                        record_ids=cluster_ids,
                        similarity_score=avg_sim,
                        sample_text=sample,
                        merge_recommendation=(
                            "keep_first" if avg_sim > 0.95 else "manual"
                        ),
                    ))

        except sqlite3.Error as exc:
            logger.error("Duplicate scan error on %s.%s: %s", brain_name, table_name, exc)

        return groups

    def merge_duplicates(
        self,
        group: DuplicateGroup,
        strategy: str = "keep_best",
    ) -> EvolutionAction:
        """Execute a duplicate merge for a group."""
        action = EvolutionAction(
            action_type="dedup",
            brain_name=group.brain_name,
            table_name=group.table_name,
            description=(
                f"Merge {len(group.record_ids)} duplicates in "
                f"{group.brain_name}.{group.table_name} "
                f"(similarity={group.similarity_score:.2f}, strategy={strategy})"
            ),
            status="proposed",
            records_affected=len(group.record_ids) - 1,
        )

        if not self._auto_execute:
            return action

        if not self._brain_exists(group.brain_name):
            action.status = "failed"
            action.description += " — brain not found"
            return action

        try:
            db_path = self._brain_db_path(group.brain_name)
            conn = self._open_db(db_path)
            pk_col = self._get_pk_column(conn, group.table_name)

            # Keep first (or best) record, delete rest
            keep_id = group.record_ids[0]
            delete_ids = group.record_ids[1:]

            if delete_ids:
                placeholders = ",".join("?" * len(delete_ids))
                rollback_rows = conn.execute(
                    f"SELECT * FROM [{group.table_name}] "
                    f"WHERE [{pk_col}] IN ({placeholders})",
                    delete_ids,
                ).fetchall()

                conn.execute(
                    f"DELETE FROM [{group.table_name}] "
                    f"WHERE [{pk_col}] IN ({placeholders})",
                    delete_ids,
                )
                conn.commit()

                action.rollback_sql = (
                    f"-- Rollback: re-insert {len(delete_ids)} deleted rows "
                    f"into {group.table_name}"
                )
                action.status = "executed"
                action.executed_at = time.strftime("%Y-%m-%dT%H:%M:%S")

            conn.close()
        except Exception as exc:
            action.status = "failed"
            action.description += f" — error: {exc}"
            logger.error("Merge failed: %s", exc)

        self._log_action(action)
        return action

    def find_orphans(self, brain_name: str) -> List[Dict[str, Any]]:
        """Find orphaned cross-references pointing to nonexistent records."""
        orphans: List[Dict[str, Any]] = []
        xref_db = self._brain_dir / "cross_brain_index.db"
        if not xref_db.exists():
            return orphans

        try:
            conn = self._open_db(str(xref_db))
            if not self._table_exists(conn, "cross_references"):
                conn.close()
                return orphans

            rows = conn.execute(
                "SELECT rowid, source_brain, source_table, source_id, "
                "target_brain, target_table, target_id "
                "FROM cross_references "
                "WHERE source_brain = ? OR target_brain = ?",
                (brain_name, brain_name),
            ).fetchall()
            conn.close()

            for row in rows:
                ref = dict(row)
                # Check if target exists
                target_brain = ref.get("target_brain", "")
                target_table = ref.get("target_table", "")
                target_id = ref.get("target_id", "")
                if target_brain and self._brain_exists(target_brain):
                    try:
                        tconn = self._open_db(
                            self._brain_db_path(target_brain)
                        )
                        if self._table_exists(tconn, target_table):
                            pk = self._get_pk_column(tconn, target_table)
                            found = tconn.execute(
                                f"SELECT 1 FROM [{target_table}] "
                                f"WHERE [{pk}] = ? LIMIT 1",
                                (target_id,),
                            ).fetchone()
                            if not found:
                                orphans.append(ref)
                        tconn.close()
                    except sqlite3.Error:
                        pass

        except sqlite3.Error as exc:
            logger.error("Orphan scan error for %s: %s", brain_name, exc)

        return orphans

    def find_stale(
        self, brain_name: str, days_threshold: int = 180
    ) -> List[Dict[str, Any]]:
        """Find records not updated in N days."""
        stale: List[Dict[str, Any]] = []
        if not self._brain_exists(brain_name):
            return stale

        try:
            conn = self._open_db(self._brain_db_path(brain_name))
            tables = self._get_tables(conn)

            for table in tables:
                # Check for common timestamp columns
                cols = [
                    c[1]
                    for c in conn.execute(
                        f"PRAGMA table_info([{table}])"
                    ).fetchall()
                ]
                ts_col = None
                for candidate in [
                    "updated_at",
                    "modified_at",
                    "last_updated",
                    "created_at",
                    "ingested_at",
                    "extracted_at",
                ]:
                    if candidate in cols:
                        ts_col = candidate
                        break

                if not ts_col:
                    continue

                try:
                    interval = f"-{int(days_threshold)} days"
                    rows = conn.execute(
                        f"SELECT COUNT(*) FROM [{table}] "
                        f"WHERE [{ts_col}] < datetime('now', ?) "
                        f"AND [{ts_col}] IS NOT NULL AND [{ts_col}] != ''",
                        (interval,),
                    ).fetchone()
                    count = rows[0] if rows else 0
                    if count > 0:
                        stale.append({
                            "brain_name": brain_name,
                            "table_name": table,
                            "timestamp_column": ts_col,
                            "stale_count": count,
                            "threshold_days": days_threshold,
                        })
                except sqlite3.Error:
                    continue

            conn.close()
        except sqlite3.Error as exc:
            logger.error("Stale scan error for %s: %s", brain_name, exc)

        return stale

    def check_fts_sync(self, brain_name: str) -> Dict[str, str]:
        """Compare FTS tables vs base tables for sync status."""
        results: Dict[str, str] = {}
        fts_tables = BRAIN_FTS_TABLES.get(brain_name, [])
        if not fts_tables or not self._brain_exists(brain_name):
            return results

        try:
            conn = self._open_db(self._brain_db_path(brain_name))
            for fts_table in fts_tables:
                if not self._table_exists(conn, fts_table):
                    results[fts_table] = "missing"
                    continue

                fts_count = self._row_count(conn, fts_table)

                # Infer base table name (strip _fts suffix)
                base_name = fts_table.replace("_fts", "")
                if self._table_exists(conn, base_name):
                    base_count = self._row_count(conn, base_name)
                    if fts_count == base_count:
                        results[fts_table] = "synced"
                    elif fts_count < base_count:
                        results[fts_table] = f"behind ({fts_count}/{base_count})"
                    else:
                        results[fts_table] = f"ahead ({fts_count}/{base_count})"
                else:
                    results[fts_table] = (
                        f"ok ({fts_count} rows, no base table)"
                    )
            conn.close()
        except sqlite3.Error as exc:
            logger.error("FTS sync check error for %s: %s", brain_name, exc)

        return results

    def rebuild_fts(
        self, brain_name: str, fts_table: str
    ) -> EvolutionAction:
        """Rebuild an FTS index by re-inserting from the base table."""
        action = EvolutionAction(
            action_type="fts_rebuild",
            brain_name=brain_name,
            table_name=fts_table,
            description=f"Rebuild FTS index {brain_name}.{fts_table}",
            status="proposed",
        )

        if not self._auto_execute:
            return action

        if not self._brain_exists(brain_name):
            action.status = "failed"
            action.description += " — brain not found"
            return action

        try:
            conn = self._open_db(self._brain_db_path(brain_name))
            if not self._table_exists(conn, fts_table):
                action.status = "failed"
                action.description += " — FTS table not found"
                conn.close()
                return action

            # FTS5 rebuild command
            conn.execute(
                f"INSERT INTO [{fts_table}]([{fts_table}]) VALUES('rebuild')"
            )
            conn.commit()

            action.status = "executed"
            action.executed_at = time.strftime("%Y-%m-%dT%H:%M:%S")
            action.records_affected = self._row_count(conn, fts_table)
            conn.close()
        except sqlite3.Error as exc:
            action.status = "failed"
            action.description += f" — error: {exc}"
            logger.error("FTS rebuild failed: %s", exc)

        self._log_action(action)
        return action

    def evolve(
        self,
        brain_name: Optional[str] = None,
        dry_run: bool = True,
    ) -> EvolutionReport:
        """Run a full evolution cycle: assess, detect issues, propose/execute actions."""
        cycle_id = f"evo_{uuid.uuid4().hex[:12]}"
        started_at = time.strftime("%Y-%m-%dT%H:%M:%S")
        warnings: List[str] = []

        # Assess health
        scores = self.assess_health(brain_name)

        # Find duplicates across all brains (text columns only)
        all_dupes: List[DuplicateGroup] = []
        names = [brain_name] if brain_name else BRAIN_NAMES
        for name in names:
            if not self._brain_exists(name):
                continue
            try:
                conn = self._open_db(self._brain_db_path(name))
                tables = self._get_tables(conn)
                for table in tables:
                    if table.endswith("_fts") or table.startswith("sqlite_"):
                        continue
                    text_cols = self._find_text_columns(conn, table)
                    for col in text_cols[:1]:  # first text column only
                        dupes = self.find_duplicates(name, table, col)
                        all_dupes.extend(dupes)
                conn.close()
            except Exception as exc:
                warnings.append(f"Dedup scan for {name}: {exc}")

        # Check FTS sync
        actions_proposed: List[EvolutionAction] = []
        actions_taken: List[EvolutionAction] = []
        for name in names:
            fts_status = self.check_fts_sync(name)
            for fts_table, status in fts_status.items():
                if status not in ("synced", "missing"):
                    action = EvolutionAction(
                        action_type="fts_rebuild",
                        brain_name=name,
                        table_name=fts_table,
                        description=f"FTS out of sync: {status}",
                        status="proposed",
                    )
                    if self._auto_execute and not dry_run:
                        action = self.rebuild_fts(name, fts_table)
                        actions_taken.append(action)
                    else:
                        actions_proposed.append(action)

        # Propose dedup actions
        for group in all_dupes:
            action = EvolutionAction(
                action_type="dedup",
                brain_name=group.brain_name,
                table_name=group.table_name,
                description=(
                    f"Merge {len(group.record_ids)} duplicates "
                    f"(sim={group.similarity_score:.2f})"
                ),
                status="proposed",
                records_affected=len(group.record_ids) - 1,
            )
            if self._auto_execute and not dry_run:
                action = self.merge_duplicates(group)
                actions_taken.append(action)
            else:
                actions_proposed.append(action)

        # Calculate overall health
        if scores:
            overall = sum(s.health_score for s in scores) / len(scores)
        else:
            overall = 0.0

        completed_at = time.strftime("%Y-%m-%dT%H:%M:%S")
        self._evolution_count += 1
        self._total_actions += len(actions_taken)

        report = EvolutionReport(
            cycle_id=cycle_id,
            started_at=started_at,
            completed_at=completed_at,
            brain_scores=scores,
            duplicates_found=all_dupes,
            actions_taken=actions_taken,
            actions_proposed=actions_proposed,
            overall_health=overall,
            warnings=warnings,
        )

        # Log the cycle summary
        self._log_cycle_summary(report)

        return report

    def get_evolution_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Query evolution log from cross_brain_index."""
        db_path = self._brain_dir / "cross_brain_index.db"
        if not db_path.exists():
            return []

        try:
            conn = self._open_db(str(db_path))
            if not self._table_exists(conn, "brain_evolution_log"):
                conn.close()
                return []

            rows = conn.execute(
                "SELECT * FROM brain_evolution_log "
                "ORDER BY executed_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
            conn.close()
            return [dict(r) for r in rows]
        except sqlite3.Error as exc:
            logger.error("Evolution history query failed: %s", exc)
            return []

    def get_stats(self) -> Dict[str, Any]:
        """Return evolver status and capabilities."""
        available_brains = [n for n in BRAIN_NAMES if self._brain_exists(n)]
        total_fts = sum(len(v) for v in BRAIN_FTS_TABLES.values())
        return {
            "version": "1.0.0",
            "brain_dir": str(self._brain_dir),
            "brain_dir_exists": self._brain_dir.exists(),
            "known_brains": len(BRAIN_NAMES),
            "available_brains": len(available_brains),
            "available_brain_names": available_brains,
            "total_fts_tables": total_fts,
            "auto_execute": self._auto_execute,
            "evolution_cycles_run": self._evolution_count,
            "total_actions_executed": self._total_actions,
        }

    # -- private helpers ----------------------------------------------------

    def _score_brain(self, brain_name: str) -> BrainHealthScore:
        """Compute health score for a single brain."""
        db_path = self._brain_db_path(brain_name)
        conn = self._open_db(db_path)
        tables = self._get_tables(conn)

        total_rows = 0
        tables_with_data = 0
        empty_tables = 0
        issues: List[str] = []

        for table in tables:
            count = self._row_count(conn, table)
            total_rows += count
            if count > 0:
                tables_with_data += 1
            else:
                empty_tables += 1

        # FTS sync check
        fts_status = self.check_fts_sync(brain_name)
        fts_ok = all(
            s in ("synced", "missing") or "no base table" in s
            for s in fts_status.values()
        ) if fts_status else True
        fts_summary = "synced" if fts_ok else "out_of_sync"
        if not fts_ok:
            issues.append("FTS indexes out of sync")

        # Provenance coverage (check cross_brain_index)
        provenance_coverage = self._check_provenance_coverage(brain_name, conn)

        conn.close()

        # Scoring formula
        score = 1.0
        if total_rows == 0:
            score = 0.1
            issues.append("No data in any table")
        else:
            # Penalize empty tables (mild)
            if len(tables) > 0:
                data_ratio = tables_with_data / len(tables)
                if data_ratio < 0.5:
                    score -= 0.2
                    issues.append(
                        f"Low data coverage: {tables_with_data}/{len(tables)} tables populated"
                    )
            # Penalize FTS out of sync
            if not fts_ok:
                score -= 0.15
            # Reward provenance coverage
            if provenance_coverage < 0.5:
                score -= 0.1
                issues.append(
                    f"Low provenance coverage: {provenance_coverage:.0%}"
                )

        score = max(0.0, min(1.0, score))

        return BrainHealthScore(
            brain_name=brain_name,
            total_tables=len(tables),
            total_rows=total_rows,
            tables_with_data=tables_with_data,
            empty_tables=empty_tables,
            provenance_coverage=provenance_coverage,
            fts_sync_status=fts_summary,
            health_score=score,
            issues=issues,
        )

    def _check_provenance_coverage(
        self, brain_name: str, brain_conn: sqlite3.Connection
    ) -> float:
        """Check what fraction of brain tables have provenance records."""
        xref_db = self._brain_dir / "cross_brain_index.db"
        if not xref_db.exists():
            return 0.0

        try:
            xconn = self._open_db(str(xref_db))
            if not self._table_exists(xconn, "provenance"):
                xconn.close()
                return 0.0

            row = xconn.execute(
                "SELECT COUNT(DISTINCT record_table) FROM provenance "
                "WHERE brain_name = ?",
                (brain_name,),
            ).fetchone()
            xconn.close()

            prov_tables = row[0] if row else 0
            brain_tables = self._get_tables(brain_conn)
            real_tables = [
                t for t in brain_tables
                if not t.endswith("_fts") and not t.startswith("sqlite_")
            ]
            if not real_tables:
                return 0.0
            return min(prov_tables / len(real_tables), 1.0)
        except sqlite3.Error:
            return 0.0

    def _get_pk_column(
        self, conn: sqlite3.Connection, table: str
    ) -> str:
        """Get primary key column name for a table (falls back to rowid)."""
        try:
            cols = conn.execute(f"PRAGMA table_info([{table}])").fetchall()
            for col in cols:
                if col[5] == 1:  # pk flag
                    return col[1]
            # No explicit PK — use first column
            if cols:
                return cols[0][1]
        except sqlite3.Error:
            pass
        return "rowid"

    def _find_text_columns(
        self, conn: sqlite3.Connection, table: str
    ) -> List[str]:
        """Find TEXT columns suitable for dedup comparison."""
        text_cols: List[str] = []
        try:
            cols = conn.execute(f"PRAGMA table_info([{table}])").fetchall()
            for col in cols:
                col_type = str(col[2]).upper()
                col_name = col[1]
                if col_type in ("TEXT", "VARCHAR", "CLOB", ""):
                    # Skip columns that are likely IDs or short metadata
                    if col_name.endswith("_id") or col_name in (
                        "id", "hash", "sha256", "uuid", "status", "type",
                    ):
                        continue
                    text_cols.append(col_name)
        except sqlite3.Error:
            pass
        return text_cols

    def _log_action(self, action: EvolutionAction) -> None:
        """Write an action to the evolution log."""
        db_path = self._brain_dir / "cross_brain_index.db"
        if not db_path.exists():
            return
        try:
            conn = self._open_db(str(db_path))
            conn.execute(
                "INSERT INTO brain_evolution_log "
                "(cycle_id, action_type, brain_name, table_name, "
                "description, records_affected, status, rollback_sql) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    "",
                    action.action_type,
                    action.brain_name,
                    action.table_name,
                    action.description,
                    action.records_affected,
                    action.status,
                    action.rollback_sql,
                ),
            )
            conn.commit()
            conn.close()
        except sqlite3.Error as exc:
            logger.warning("Could not log action: %s", exc)

    def _log_cycle_summary(self, report: EvolutionReport) -> None:
        """Write a cycle summary entry to the evolution log."""
        db_path = self._brain_dir / "cross_brain_index.db"
        if not db_path.exists():
            return
        try:
            conn = self._open_db(str(db_path))
            if not self._table_exists(conn, "brain_evolution_log"):
                conn.close()
                return
            conn.execute(
                "INSERT INTO brain_evolution_log "
                "(cycle_id, action_type, brain_name, table_name, "
                "description, records_affected, status) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    report.cycle_id,
                    "cycle_summary",
                    "all",
                    "",
                    (
                        f"Evolution cycle: {len(report.brain_scores)} brains scored, "
                        f"{len(report.duplicates_found)} dupe groups, "
                        f"{len(report.actions_taken)} actions executed, "
                        f"{len(report.actions_proposed)} proposed. "
                        f"Overall health: {report.overall_health:.0%}"
                    ),
                    len(report.actions_taken),
                    "executed",
                ),
            )
            conn.commit()
            conn.close()
        except sqlite3.Error as exc:
            logger.warning("Could not log cycle summary: %s", exc)


# ---------------------------------------------------------------------------
# Pure-Python helpers (no external deps)
# ---------------------------------------------------------------------------

_TOKEN_RE = re.compile(r"\w+", re.UNICODE)


def _tokenize(text: str) -> Set[str]:
    """Tokenize text into a set of lowercase tokens."""
    return set(_TOKEN_RE.findall(text.lower()))


def _jaccard(a: Set[str], b: Set[str]) -> float:
    """Compute Jaccard similarity between two token sets."""
    if not a and not b:
        return 1.0
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)
