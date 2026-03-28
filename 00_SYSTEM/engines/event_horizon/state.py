"""
EVENT HORIZON Δ∞ — SQLite State Manager
========================================
Persists all engine state: manifests, routing decisions, moves,
quality scores, convergence metrics, and genetic memory.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import (
    Confidence,
    ConvergenceScore,
    ConvergenceState,
    MoveRecord,
    QualityGate,
    QualityResult,
    RoutingDecision,
    RoutingTier,
)

DEFAULT_DB = Path(__file__).parent / "event_horizon.db"


class StateDB:
    """SQLite-backed state manager for the EVENT HORIZON engine."""

    def __init__(self, db_path: Path = DEFAULT_DB):
        self.db_path = db_path
        self.conn = sqlite3.connect(str(db_path))
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self._init_schema()

    def _init_schema(self):
        """Create tables if they don't exist."""
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS runs (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                zone        TEXT NOT NULL,
                dry_run     INTEGER NOT NULL DEFAULT 1,
                started_at  TEXT NOT NULL,
                finished_at TEXT,
                status      TEXT DEFAULT 'running',
                stats_json  TEXT
            );

            CREATE TABLE IF NOT EXISTS file_manifests (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id       INTEGER NOT NULL REFERENCES runs(id),
                path         TEXT NOT NULL,
                name         TEXT NOT NULL,
                extension    TEXT,
                size_bytes   INTEGER,
                modified     TEXT,
                content_hash TEXT,
                is_protected INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS routing_decisions (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id      INTEGER NOT NULL REFERENCES runs(id),
                source      TEXT NOT NULL,
                destination TEXT NOT NULL,
                tier        TEXT NOT NULL,
                confidence  TEXT NOT NULL,
                score       REAL NOT NULL,
                reason      TEXT,
                signals     TEXT
            );

            CREATE TABLE IF NOT EXISTS move_log (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id       INTEGER NOT NULL REFERENCES runs(id),
                source       TEXT NOT NULL,
                destination  TEXT NOT NULL,
                timestamp    TEXT NOT NULL,
                success      INTEGER NOT NULL DEFAULT 1,
                error        TEXT,
                rollback_path TEXT
            );

            CREATE TABLE IF NOT EXISTS quality_scores (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id      INTEGER NOT NULL REFERENCES runs(id),
                gate        TEXT NOT NULL,
                passed      INTEGER NOT NULL,
                score       REAL NOT NULL,
                details     TEXT,
                violations  TEXT
            );

            CREATE TABLE IF NOT EXISTS convergence_metrics (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id         INTEGER NOT NULL REFERENCES runs(id),
                state          TEXT NOT NULL,
                score          REAL NOT NULL,
                files_sorted   INTEGER,
                files_total    INTEGER,
                root_files     INTEGER,
                bloated_zones  TEXT,
                cycle          INTEGER DEFAULT 1,
                measured_at    TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS genetic_memory (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern     TEXT NOT NULL,
                lesson      TEXT NOT NULL,
                source_run  INTEGER REFERENCES runs(id),
                created_at  TEXT NOT NULL,
                hit_count   INTEGER DEFAULT 0
            );

            CREATE INDEX IF NOT EXISTS idx_manifests_run ON file_manifests(run_id);
            CREATE INDEX IF NOT EXISTS idx_decisions_run ON routing_decisions(run_id);
            CREATE INDEX IF NOT EXISTS idx_moves_run ON move_log(run_id);
            CREATE INDEX IF NOT EXISTS idx_quality_run ON quality_scores(run_id);
        """)
        self.conn.commit()

    # -- Run management --
    def start_run(self, zone: str, dry_run: bool = True) -> int:
        cur = self.conn.execute(
            "INSERT INTO runs (zone, dry_run, started_at) VALUES (?, ?, ?)",
            (zone, int(dry_run), datetime.now().isoformat()),
        )
        self.conn.commit()
        return cur.lastrowid

    def finish_run(self, run_id: int, status: str = "completed", stats: dict = None):
        self.conn.execute(
            "UPDATE runs SET finished_at=?, status=?, stats_json=? WHERE id=?",
            (datetime.now().isoformat(), status, json.dumps(stats or {}), run_id),
        )
        self.conn.commit()

    # -- Manifests --
    def save_manifests(self, run_id: int, manifests: list):
        rows = [
            (run_id, str(m.path), m.name, m.extension, m.size_bytes,
             m.modified.isoformat() if m.modified else None,
             m.content_hash, int(m.is_protected))
            for m in manifests
        ]
        self.conn.executemany(
            "INSERT INTO file_manifests (run_id,path,name,extension,size_bytes,modified,content_hash,is_protected) "
            "VALUES (?,?,?,?,?,?,?,?)",
            rows,
        )
        self.conn.commit()

    # -- Routing decisions --
    def save_decisions(self, run_id: int, decisions: list[RoutingDecision]):
        rows = [
            (run_id, str(d.source), str(d.destination), d.tier.name,
             d.confidence.name, d.score, d.reason, json.dumps(d.signals))
            for d in decisions
        ]
        self.conn.executemany(
            "INSERT INTO routing_decisions (run_id,source,destination,tier,confidence,score,reason,signals) "
            "VALUES (?,?,?,?,?,?,?,?)",
            rows,
        )
        self.conn.commit()

    # -- Move log --
    def save_move(self, run_id: int, rec: MoveRecord):
        self.conn.execute(
            "INSERT INTO move_log (run_id,source,destination,timestamp,success,error,rollback_path) "
            "VALUES (?,?,?,?,?,?,?)",
            (run_id, str(rec.source), str(rec.destination),
             rec.timestamp.isoformat(), int(rec.success), rec.error,
             str(rec.rollback_path) if rec.rollback_path else None),
        )
        self.conn.commit()

    # -- Quality scores --
    def save_quality(self, run_id: int, report):
        """Save quality results. Accepts QualityReport or list[QualityResult]."""
        results = report.results if hasattr(report, 'results') else report
        rows = [
            (run_id, r.gate.value, int(r.passed), r.score, r.details,
             json.dumps(r.violations))
            for r in results
        ]
        self.conn.executemany(
            "INSERT INTO quality_scores (run_id,gate,passed,score,details,violations) "
            "VALUES (?,?,?,?,?,?)",
            rows,
        )
        self.conn.commit()

    # -- Convergence --
    def save_convergence(self, run_id: int, cs: ConvergenceScore):
        self.conn.execute(
            "INSERT INTO convergence_metrics "
            "(run_id,state,score,files_sorted,files_total,root_files,bloated_zones,cycle,measured_at) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (run_id, cs.state.value, cs.score, cs.files_sorted, cs.files_total,
             cs.root_files, json.dumps(cs.bloated_zones), cs.cycle,
             datetime.now().isoformat()),
        )
        self.conn.commit()

    # -- Genetic memory --
    def remember(self, pattern: str, lesson: str, run_id: int = None):
        self.conn.execute(
            "INSERT INTO genetic_memory (pattern, lesson, source_run, created_at) VALUES (?,?,?,?)",
            (pattern, lesson, run_id, datetime.now().isoformat()),
        )
        self.conn.commit()

    def recall(self, pattern: str) -> list[tuple[str, int]]:
        """Recall lessons matching a pattern. Returns (lesson, hit_count)."""
        rows = self.conn.execute(
            "SELECT lesson, hit_count FROM genetic_memory WHERE pattern LIKE ? ORDER BY hit_count DESC",
            (f"%{pattern}%",),
        ).fetchall()
        # Bump hit counts
        if rows:
            self.conn.execute(
                "UPDATE genetic_memory SET hit_count = hit_count + 1 WHERE pattern LIKE ?",
                (f"%{pattern}%",),
            )
            self.conn.commit()
        return rows

    # -- Statistics --
    def get_run_stats(self, run_id: int) -> dict:
        """Get aggregate stats for a run."""
        manifests = self.conn.execute(
            "SELECT COUNT(*) FROM file_manifests WHERE run_id=?", (run_id,)
        ).fetchone()[0]
        decisions = self.conn.execute(
            "SELECT COUNT(*) FROM routing_decisions WHERE run_id=?", (run_id,)
        ).fetchone()[0]
        moves = self.conn.execute(
            "SELECT COUNT(*), SUM(CASE WHEN success=1 THEN 1 ELSE 0 END) FROM move_log WHERE run_id=?",
            (run_id,),
        ).fetchone()
        return {
            "manifests": manifests,
            "decisions": decisions,
            "moves_total": moves[0] or 0,
            "moves_success": moves[1] or 0,
        }

    def close(self):
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
