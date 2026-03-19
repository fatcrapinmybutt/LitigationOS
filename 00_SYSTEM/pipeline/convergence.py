import sys; sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')
"""
CONVERGENCE ENGINE — Pipeline Stabilisation Detector
=====================================================
Tracks metrics across pipeline runs and determines when the system
has stabilised (no new evidence being discovered).  Implements both
statistical and heuristic stopping criteria.

Usage:
    from convergence import ConvergenceEngine

    engine = ConvergenceEngine()
    result = engine.run_convergence_loop(my_pipeline_fn)
    print(result)

CLI (dry-run):
    python convergence.py
"""

import hashlib
import json
import os
import sqlite3
import traceback
from datetime import datetime
from pathlib import Path

# ── Failsafe (must be first) ───────────────────────────────────────
try:
    from failsafe import safe_call, never_crash
except ImportError:
    def safe_call(fn, *a, timeout_s=30, fallback=None, **kw):
        try:
            return fn(*a, **kw)
        except Exception:
            return fallback
    def never_crash(fallback=None):
        def d(f):
            import functools
            @functools.wraps(f)
            def w(*a, **kw):
                try:
                    return f(*a, **kw)
                except Exception:
                    return fallback
            return w
        return d

# ── Config imports ──────────────────────────────────────────────────
try:
    from config import LITIGOS_ROOT
except ImportError:
    LITIGOS_ROOT = Path(r"C:\Users\andre\LitigationOS")

DB_PATH = str(LITIGOS_ROOT / "litigation_context.db")
INSTRUCTIONS_PATH = LITIGOS_ROOT / "00_SYSTEM" / "COPILOT_INSTRUCTIONS_ENHANCED.md"


def _ts() -> str:
    """Compact ISO timestamp for log lines."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _log(msg: str) -> None:
    print(f"[{_ts()}] [convergence] {msg}", flush=True)


# ────────────────────────────────────────────────────────────────────
#  ConvergenceEngine
# ────────────────────────────────────────────────────────────────────
class ConvergenceEngine:
    """Determines when the drive-ingestion pipeline has stabilised."""

    def __init__(self, db_path: str | None = None, max_iterations: int = 5,
                 epsilon: float = 0.001):
        """
        Parameters
        ----------
        db_path : str | None
            Path to litigation_context.db.  Falls back to the canonical location.
        max_iterations : int
            Maximum convergence runs before force-stop.
        epsilon : float
            Minimum improvement threshold (0.1 % default).
        """
        self.db_path = db_path or DB_PATH
        self.max_iterations = max_iterations
        self.epsilon = epsilon

    # ── DB helpers ──────────────────────────────────────────────────

    @never_crash(fallback=None)
    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=120)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA busy_timeout=120000")
        conn.row_factory = sqlite3.Row
        return conn

    @never_crash(fallback=None)
    def _ensure_table(self, conn: sqlite3.Connection) -> None:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ingest_logs (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id      TEXT    NOT NULL,
                phase       TEXT    NOT NULL DEFAULT 'convergence',
                status      TEXT    NOT NULL DEFAULT 'started',
                started_at  TEXT    NOT NULL,
                ended_at    TEXT,
                delta_json  TEXT,
                metrics_json TEXT
            )
        """)
        conn.commit()

    # ── Public API ──────────────────────────────────────────────────

    @never_crash(fallback="RUN_ERROR")
    def start_run(self) -> str:
        """Start a new convergence run.  Returns run_id ``RUN_YYYYMMDD_HHMMSS``."""
        run_id = f"RUN_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        conn = self._connect()
        if conn is None:
            _log("ERROR: cannot open DB — returning placeholder run_id")
            return run_id
        try:
            self._ensure_table(conn)
            conn.execute(
                "INSERT INTO ingest_logs (run_id, phase, status, started_at) "
                "VALUES (?, 'convergence', 'started', ?)",
                (run_id, _ts()),
            )
            conn.commit()
            _log(f"Started convergence run {run_id}")
        finally:
            conn.close()
        return run_id

    @never_crash(fallback={})
    def snapshot_metrics(self, run_id: str) -> dict:
        """Capture current DB state metrics for comparison."""
        conn = self._connect()
        if conn is None:
            _log("ERROR: cannot open DB for snapshot")
            return {}
        try:
            def _count(table: str, where: str = "") -> int:
                sql = f"SELECT count(*) FROM [{table}]"
                if where:
                    sql += f" WHERE {where}"
                try:
                    row = conn.execute(sql).fetchone()
                    return row[0] if row else 0
                except sqlite3.OperationalError:
                    return 0

            metrics = {
                "evidence_quotes_count": _count("evidence_quotes"),
                "authority_chains_count": _count("authority_chains"),
                "drive_files_count": _count("documents"),
                "file_atoms_count": _count("atoms") if self._table_exists(conn, "atoms") else 0,
                "gap_tickets_open": _count("gap_tickets", "status='open'")
                    if self._table_exists(conn, "gap_tickets") else 0,
                "claims_with_evidence": _count(
                    "claims",
                    "claim_id IN (SELECT DISTINCT claim_id FROM claim_evidence_links)"
                ) if self._table_exists(conn, "claim_evidence_links") else 0,
                "instruction_hash": self._instruction_hash(),
            }
            _log(f"[{run_id}] Snapshot: quotes={metrics['evidence_quotes_count']}, "
                 f"chains={metrics['authority_chains_count']}, "
                 f"files={metrics['drive_files_count']}, "
                 f"atoms={metrics['file_atoms_count']}")
            return metrics
        finally:
            conn.close()

    @never_crash(fallback={})
    def compute_delta(self, before: dict, after: dict) -> dict:
        """Compute the change between two snapshots."""
        if not before or not after:
            return {
                "new_quotes": 0, "new_atoms": 0, "new_files": 0,
                "gaps_delta": 0, "instruction_changed": False,
                "improvement_pct": 0.0,
            }

        new_quotes = after.get("evidence_quotes_count", 0) - before.get("evidence_quotes_count", 0)
        new_atoms = after.get("file_atoms_count", 0) - before.get("file_atoms_count", 0)
        new_files = after.get("drive_files_count", 0) - before.get("drive_files_count", 0)
        new_chains = after.get("authority_chains_count", 0) - before.get("authority_chains_count", 0)
        gaps_delta = before.get("gap_tickets_open", 0) - after.get("gap_tickets_open", 0)
        instruction_changed = (
            before.get("instruction_hash", "") != after.get("instruction_hash", "")
        )

        # Weighted composite improvement percentage
        # quotes(40%) + atoms(30%) + chains(20%) + gaps_closed(10%)
        denom_quotes = max(before.get("evidence_quotes_count", 1), 1)
        denom_atoms = max(before.get("file_atoms_count", 1), 1)
        denom_chains = max(before.get("authority_chains_count", 1), 1)
        denom_gaps = max(before.get("gap_tickets_open", 1), 1)

        improvement_pct = (
            0.40 * (new_quotes / denom_quotes)
            + 0.30 * (new_atoms / denom_atoms)
            + 0.20 * (new_chains / denom_chains)
            + 0.10 * (gaps_delta / denom_gaps)
        )

        delta = {
            "new_quotes": new_quotes,
            "new_atoms": new_atoms,
            "new_files": new_files,
            "gaps_delta": gaps_delta,
            "instruction_changed": instruction_changed,
            "improvement_pct": improvement_pct,
        }
        _log(f"Delta: +{new_quotes} quotes, +{new_atoms} atoms, "
             f"+{new_files} files, gaps Δ{gaps_delta}, "
             f"improvement={improvement_pct:.4%}")
        return delta

    @never_crash(fallback=(False, "ERROR"))
    def check_convergence(self, deltas: list[dict]) -> tuple[bool, str]:
        """
        Determine whether the pipeline has converged.

        Returns
        -------
        (converged, reason) where reason is one of:
            CONVERGED_ZERO_CHANGE, CONVERGED_STATISTICAL,
            FORCE_STOP, CONTINUE, ERROR
        """
        if not deltas:
            return False, "CONTINUE"

        latest = deltas[-1]

        # Rule 1: zero new evidence and instructions unchanged
        if (latest.get("new_quotes", 0) == 0
                and latest.get("new_atoms", 0) == 0
                and not latest.get("instruction_changed", False)):
            _log("Convergence: zero new quotes + atoms, instructions unchanged")
            return True, "CONVERGED_ZERO_CHANGE"

        # Rule 2: improvement below epsilon for 2 consecutive runs
        if len(deltas) >= 2:
            prev = deltas[-2]
            if (abs(latest.get("improvement_pct", 0.0)) < self.epsilon
                    and abs(prev.get("improvement_pct", 0.0)) < self.epsilon):
                _log(f"Convergence: improvement < {self.epsilon} for 2 consecutive runs")
                return True, "CONVERGED_STATISTICAL"

        # Rule 3: max iterations
        if len(deltas) >= self.max_iterations:
            _log(f"Force-stop: reached {self.max_iterations} iterations")
            return True, "FORCE_STOP"

        # Rule 4: continue
        return False, "CONTINUE"

    @never_crash(fallback=None)
    def end_run(self, run_id: str, status: str, delta: dict) -> None:
        """Record run completion in ingest_logs."""
        conn = self._connect()
        if conn is None:
            _log(f"ERROR: cannot open DB to end run {run_id}")
            return
        try:
            self._ensure_table(conn)
            conn.execute(
                "UPDATE ingest_logs SET status=?, ended_at=?, delta_json=? "
                "WHERE run_id=? AND phase='convergence'",
                (status, _ts(), json.dumps(delta, default=str), run_id),
            )
            conn.commit()
            _log(f"Ended run {run_id} — status={status}")
        finally:
            conn.close()

    @never_crash(fallback=[])
    def get_run_history(self) -> list[dict]:
        """Get all convergence run results, ordered by timestamp."""
        conn = self._connect()
        if conn is None:
            return []
        try:
            self._ensure_table(conn)
            rows = conn.execute(
                "SELECT run_id, phase, status, started_at, ended_at, delta_json, metrics_json "
                "FROM ingest_logs WHERE phase='convergence' ORDER BY started_at"
            ).fetchall()
            history = []
            for r in rows:
                entry = {
                    "run_id": r["run_id"],
                    "phase": r["phase"],
                    "status": r["status"],
                    "started_at": r["started_at"],
                    "ended_at": r["ended_at"],
                    "delta": json.loads(r["delta_json"]) if r["delta_json"] else {},
                    "metrics": json.loads(r["metrics_json"]) if r["metrics_json"] else {},
                }
                history.append(entry)
            return history
        finally:
            conn.close()

    @never_crash(fallback={"converged": False, "reason": "ERROR", "iterations": 0,
                           "total_new_quotes": 0, "total_new_atoms": 0, "run_history": []})
    def run_convergence_loop(self, pipeline_fn) -> dict:
        """
        Run ``pipeline_fn`` repeatedly until convergence.

        Parameters
        ----------
        pipeline_fn : callable(run_id) -> None
            Executes one full pipeline cycle.

        Returns
        -------
        dict with keys: converged, reason, iterations, total_new_quotes,
        total_new_atoms, run_history.
        """
        deltas: list[dict] = []
        run_records: list[dict] = []
        total_new_quotes = 0
        total_new_atoms = 0

        for iteration in range(1, self.max_iterations + 1):
            _log(f"=== Convergence iteration {iteration}/{self.max_iterations} ===")

            run_id = self.start_run()
            before = self.snapshot_metrics(run_id)

            # Execute the pipeline
            ok = safe_call(pipeline_fn, run_id, timeout_s=3600, fallback=None,
                           component="convergence_pipeline")
            if ok is None:
                _log(f"WARNING: pipeline_fn returned None / timed-out on iteration {iteration}")

            after = self.snapshot_metrics(run_id)
            delta = self.compute_delta(before, after)
            deltas.append(delta)

            total_new_quotes += delta.get("new_quotes", 0)
            total_new_atoms += delta.get("new_atoms", 0)

            converged, reason = self.check_convergence(deltas)

            status = reason if converged else "completed"
            self.end_run(run_id, status, delta)

            run_records.append({
                "run_id": run_id,
                "iteration": iteration,
                "delta": delta,
                "converged": converged,
                "reason": reason,
            })

            if converged:
                _log(f"Pipeline converged after {iteration} iteration(s): {reason}")
                break
        else:
            converged = True
            reason = "FORCE_STOP"
            _log(f"Pipeline force-stopped after {self.max_iterations} iterations")

        return {
            "converged": converged,
            "reason": reason,
            "iterations": len(run_records),
            "total_new_quotes": total_new_quotes,
            "total_new_atoms": total_new_atoms,
            "run_history": run_records,
        }

    # ── Helpers (private) ───────────────────────────────────────────

    @staticmethod
    def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
        try:
            row = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                (table,),
            ).fetchone()
            return row is not None
        except Exception:
            return False

    @staticmethod
    def _instruction_hash() -> str:
        """SHA-256 of COPILOT_INSTRUCTIONS_ENHANCED.md (or empty on error)."""
        try:
            data = INSTRUCTIONS_PATH.read_bytes()
            return hashlib.sha256(data).hexdigest()
        except Exception:
            return ""


# ────────────────────────────────────────────────────────────────────
#  CLI — dry-run convergence check
# ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    _log("Dry-run convergence check — snapshot only (no pipeline execution)")
    engine = ConvergenceEngine()
    run_id = engine.start_run()
    metrics = engine.snapshot_metrics(run_id)
    engine.end_run(run_id, "dry_run", {})

    _log("Current metrics:")
    for k, v in sorted(metrics.items()):
        _log(f"  {k}: {v}")

    history = engine.get_run_history()
    _log(f"Historical convergence runs: {len(history)}")
    for h in history[-5:]:
        _log(f"  {h['run_id']}  status={h['status']}  delta={h.get('delta', {})}")

    _log("Done.")
