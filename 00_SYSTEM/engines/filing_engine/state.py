"""
Filing Engine State Machine
============================

Tracks each filing through pipeline phases with full audit trail.
Uses SQLite for persistent state — survives crashes, restarts, sessions.

Python 3.12+: Uses StrEnum for cleaner DB storage and match/case for
transition validation. Phases are strictly ordered — no skipping or
going backward without explicit FAILED transition.
"""

import logging
import sqlite3
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Optional

logger = logging.getLogger("filing_engine.state")


class Phase(StrEnum):
    """Filing pipeline phases (strictly ordered)."""
    TRIGGERED = "TRIGGERED"
    SCANNING = "SCANNING"
    VALIDATING = "VALIDATING"
    FORMATTING = "FORMATTING"
    ASSEMBLING = "ASSEMBLING"
    QA = "QA"
    OUTPUT = "OUTPUT"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"


class RunStatus(StrEnum):
    """Overall run status."""
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"
    DRY_RUN = "DRY_RUN"


# Phase ordering for progression checks (FAILED excluded — it's a terminal sink)
PHASE_ORDER = [Phase.TRIGGERED, Phase.SCANNING, Phase.VALIDATING,
               Phase.FORMATTING, Phase.ASSEMBLING, Phase.QA,
               Phase.OUTPUT, Phase.COMPLETE]

# Build index map for O(1) ordering lookups
_PHASE_INDEX = {phase: idx for idx, phase in enumerate(PHASE_ORDER)}


class FilingState:
    """Persistent state machine for filing pipeline runs."""

    SCHEMA = """
    CREATE TABLE IF NOT EXISTS filing_runs (
        run_id INTEGER PRIMARY KEY AUTOINCREMENT,
        filing_id TEXT NOT NULL,
        case_number TEXT,
        court TEXT,
        phase TEXT NOT NULL DEFAULT 'TRIGGERED',
        status TEXT NOT NULL DEFAULT 'RUNNING',
        dry_run INTEGER NOT NULL DEFAULT 1,
        trigger_reason TEXT,
        started_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        finished_at TEXT,
        result_json TEXT,
        error_message TEXT
    );

    CREATE TABLE IF NOT EXISTS phase_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id INTEGER NOT NULL,
        phase TEXT NOT NULL,
        status TEXT NOT NULL,
        message TEXT,
        data_json TEXT,
        timestamp TEXT NOT NULL,
        duration_ms INTEGER,
        FOREIGN KEY(run_id) REFERENCES filing_runs(run_id)
    );

    CREATE TABLE IF NOT EXISTS component_inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id INTEGER NOT NULL,
        component_type TEXT NOT NULL,
        component_name TEXT NOT NULL,
        file_path TEXT,
        status TEXT DEFAULT 'pending',
        validation_notes TEXT,
        page_count INTEGER,
        created_at TEXT NOT NULL,
        FOREIGN KEY(run_id) REFERENCES filing_runs(run_id)
    );

    CREATE TABLE IF NOT EXISTS qa_findings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id INTEGER NOT NULL,
        check_name TEXT NOT NULL,
        passed INTEGER NOT NULL,
        severity TEXT DEFAULT 'warning',
        message TEXT,
        rule_authority TEXT,
        auto_fixable INTEGER DEFAULT 0,
        fixed INTEGER DEFAULT 0,
        timestamp TEXT NOT NULL,
        FOREIGN KEY(run_id) REFERENCES filing_runs(run_id)
    );

    CREATE INDEX IF NOT EXISTS idx_filing_runs_filing_id
        ON filing_runs(filing_id);
    CREATE INDEX IF NOT EXISTS idx_filing_runs_status
        ON filing_runs(status);
    CREATE INDEX IF NOT EXISTS idx_phase_log_run_id
        ON phase_log(run_id);
    CREATE INDEX IF NOT EXISTS idx_component_inventory_run_id
        ON component_inventory(run_id);
    CREATE INDEX IF NOT EXISTS idx_qa_findings_run_id
        ON qa_findings(run_id);
    """

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            engine_dir = Path(__file__).resolve().parent
            db_path = str(engine_dir / "filing_engine.db")
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA busy_timeout=60000")
        self.conn.execute("PRAGMA cache_size=-32000")
        self.conn.executescript(self.SCHEMA)
        self.conn.commit()

    def start_run(self, filing_id: str, case_number: str = "",
                  court: str = "", dry_run: bool = True,
                  trigger_reason: str = "manual") -> int:
        """Start a new filing pipeline run. Returns run_id."""
        now = datetime.now().isoformat()
        cursor = self.conn.execute("""
            INSERT INTO filing_runs
                (filing_id, case_number, court, phase, status, dry_run,
                 trigger_reason, started_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (filing_id, case_number, court, Phase.TRIGGERED.value,
              RunStatus.DRY_RUN.value if dry_run else RunStatus.RUNNING.value,
              1 if dry_run else 0, trigger_reason, now, now))
        self.conn.commit()
        run_id = cursor.lastrowid
        self._log_phase(run_id, Phase.TRIGGERED, "started",
                        f"Run initiated: {trigger_reason}")
        return run_id

    def advance_phase(self, run_id: int, phase: Phase,
                      message: str = "", data: str = None) -> None:
        """Move a run to the next phase with strict ordering validation.

        Enforces:
          - Forward-only transitions (no backward jumps)
          - No skipping phases (must follow PHASE_ORDER sequence)
          - FAILED is always allowed (terminal sink from any phase)
          - COMPLETE only from OUTPUT
        """
        # Get current phase
        row = self.conn.execute(
            "SELECT phase FROM filing_runs WHERE run_id = ?", (run_id,)
        ).fetchone()
        if not row:
            raise ValueError(f"Run {run_id} not found")

        current = Phase(row["phase"] if isinstance(row, sqlite3.Row) else row[0])

        # FAILED is always a valid transition (terminal sink)
        if phase == Phase.FAILED:
            self._do_advance(run_id, phase, message, data)
            return

        # Validate ordering using match/case for clarity
        match (current, phase):
            case (Phase.COMPLETE, _):
                raise ValueError(
                    f"Run {run_id}: cannot advance from COMPLETE to {phase.value}")
            case (Phase.FAILED, _):
                raise ValueError(
                    f"Run {run_id}: cannot advance from FAILED to {phase.value}")
            case _:
                # Check forward-only, sequential progression
                cur_idx = _PHASE_INDEX.get(current, -1)
                new_idx = _PHASE_INDEX.get(phase, -1)
                if new_idx <= cur_idx:
                    raise ValueError(
                        f"Run {run_id}: backward transition "
                        f"{current.value} → {phase.value} not allowed")
                if new_idx != cur_idx + 1:
                    skipped = [p.value for p in PHASE_ORDER[cur_idx + 1:new_idx]]
                    raise ValueError(
                        f"Run {run_id}: cannot skip phases "
                        f"{current.value} → {phase.value} "
                        f"(skips: {', '.join(skipped)})")

        self._do_advance(run_id, phase, message, data)

    def _do_advance(self, run_id: int, phase: Phase,
                    message: str = "", data: str = None) -> None:
        """Internal: perform the phase update + log."""
        now = datetime.now().isoformat()
        self.conn.execute("""
            UPDATE filing_runs SET phase = ?, updated_at = ? WHERE run_id = ?
        """, (phase.value, now, run_id))
        self.conn.commit()
        self._log_phase(run_id, phase, "started", message, data)
        logger.info(f"Run {run_id} advanced to {phase.value}: {message}")

    def complete_phase(self, run_id: int, phase: Phase,
                       message: str = "", duration_ms: int = 0,
                       data: str = None) -> None:
        """Mark a phase as completed."""
        self._log_phase(run_id, phase, "completed", message, data, duration_ms)

    def fail_run(self, run_id: int, phase: Phase,
                 error_message: str) -> None:
        """Mark a run as failed at a specific phase."""
        now = datetime.now().isoformat()
        self.conn.execute("""
            UPDATE filing_runs
            SET phase = ?, status = ?, updated_at = ?,
                finished_at = ?, error_message = ?
            WHERE run_id = ?
        """, (Phase.FAILED.value, RunStatus.FAILED.value, now, now,
              error_message, run_id))
        self.conn.commit()
        self._log_phase(run_id, phase, "failed", error_message)

    def finish_run(self, run_id: int, result_json: str = None) -> None:
        """Mark a run as successfully completed."""
        now = datetime.now().isoformat()
        self.conn.execute("""
            UPDATE filing_runs
            SET phase = ?, status = ?, updated_at = ?,
                finished_at = ?, result_json = ?
            WHERE run_id = ?
        """, (Phase.COMPLETE.value, RunStatus.COMPLETE.value, now, now,
              result_json, run_id))
        self.conn.commit()
        self._log_phase(run_id, Phase.COMPLETE, "completed",
                        "Filing pipeline complete")

    def add_component(self, run_id: int, component_type: str,
                      component_name: str, file_path: str = None) -> int:
        """Register a filing component (exhibit, COS, etc.)."""
        cursor = self.conn.execute("""
            INSERT INTO component_inventory
                (run_id, component_type, component_name, file_path, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (run_id, component_type, component_name, file_path,
              datetime.now().isoformat()))
        self.conn.commit()
        return cursor.lastrowid

    def add_qa_finding(self, run_id: int, check_name: str,
                       passed: bool, severity: str = "warning",
                       message: str = "", rule_authority: str = "",
                       auto_fixable: bool = False) -> int:
        """Record a QA check result."""
        cursor = self.conn.execute("""
            INSERT INTO qa_findings
                (run_id, check_name, passed, severity, message,
                 rule_authority, auto_fixable, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (run_id, check_name, 1 if passed else 0, severity,
              message, rule_authority, 1 if auto_fixable else 0,
              datetime.now().isoformat()))
        self.conn.commit()
        return cursor.lastrowid

    def get_run(self, run_id: int) -> Optional[dict]:
        """Get current state of a run."""
        row = self.conn.execute(
            "SELECT * FROM filing_runs WHERE run_id = ?", (run_id,)
        ).fetchone()
        return dict(row) if row else None

    def get_active_runs(self) -> list:
        """Get all currently running filing pipelines."""
        rows = self.conn.execute("""
            SELECT * FROM filing_runs
            WHERE status IN ('RUNNING', 'DRY_RUN')
            ORDER BY started_at DESC
        """).fetchall()
        return [dict(r) for r in rows]

    def get_run_history(self, filing_id: str = None, limit: int = 20) -> list:
        """Get run history, optionally filtered by filing_id."""
        if filing_id:
            rows = self.conn.execute("""
                SELECT * FROM filing_runs WHERE filing_id = ?
                ORDER BY started_at DESC LIMIT ?
            """, (filing_id, limit)).fetchall()
        else:
            rows = self.conn.execute("""
                SELECT * FROM filing_runs ORDER BY started_at DESC LIMIT ?
            """, (limit,)).fetchall()
        return [dict(r) for r in rows]

    def get_phase_log(self, run_id: int) -> list:
        """Get full phase log for a run."""
        rows = self.conn.execute("""
            SELECT * FROM phase_log WHERE run_id = ?
            ORDER BY timestamp ASC
        """, (run_id,)).fetchall()
        return [dict(r) for r in rows]

    def _log_phase(self, run_id: int, phase: Phase, status: str,
                   message: str = "", data: str = None,
                   duration_ms: int = 0) -> None:
        """Internal: log a phase event."""
        self.conn.execute("""
            INSERT INTO phase_log
                (run_id, phase, status, message, data_json, timestamp, duration_ms)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (run_id, phase.value, status, message, data,
              datetime.now().isoformat(), duration_ms))
        self.conn.commit()

    def close(self):
        """Close database connection."""
        self.conn.close()
