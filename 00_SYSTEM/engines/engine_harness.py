"""
engine_harness.py - Universal engine execution harness for LitigationOS.

Wraps any engine with error handling, retry logic, DB savepoints,
disk/memory guards, checkpointing, logging, resume support, and WAL management.

Usage:
    from engine_harness import EngineHarness

    harness = EngineHarness("my_engine_name")

    @harness.run
    def main(conn, log):
        log.info("Processing...")
        conn.execute("INSERT INTO ...")
        harness.checkpoint("phase1")
        return {"rows": 1000}

CLI:
    python engine_harness.py --status
"""

import sqlite3
import os
import sys
import time
import shutil
import psutil
import logging
import traceback
import functools
import argparse
import importlib.util
from datetime import datetime, timezone

DEFAULT_DB = r"C:\Users\andre\LitigationOS\litigation_context.db"
MIN_DISK_GB = 2
WARN_RAM_GB = 2
WAL_THRESHOLD_MB = 100

LOG_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS engine_run_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    engine_name TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT,
    status TEXT NOT NULL DEFAULT 'running',
    error_message TEXT,
    rows_affected INTEGER,
    disk_before_gb REAL,
    disk_after_gb REAL,
    last_checkpoint TEXT
)
"""


def _free_disk_gb(drive="C:\\"):
    usage = shutil.disk_usage(drive)
    return round(usage.free / (1024 ** 3), 2)


def _free_ram_gb():
    mem = psutil.virtual_memory()
    return round(mem.available / (1024 ** 3), 2)


def _utcnow():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def _wal_size(db_path):
    wal_path = db_path + "-wal"
    if os.path.exists(wal_path):
        return os.path.getsize(wal_path) / (1024 ** 2)
    return 0


class EngineHarness:
    """Universal execution harness for LitigationOS engines."""

    def __init__(self, engine_name, db_path=DEFAULT_DB, retries=3, backoff_base=2):
        self.engine_name = engine_name
        self.db_path = db_path
        self.retries = retries
        self.backoff_base = backoff_base
        self._checkpoints = []
        self._run_id = None
        self._conn = None

        self.logger = logging.getLogger(f"harness.{engine_name}")
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stderr)
            handler.setFormatter(logging.Formatter(
                "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s"
            ))
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    # ── Log table management ─────────────────────────────────────────

    def _ensure_log_table(self, conn):
        conn.executescript(LOG_TABLE_DDL)

    def _insert_run(self, conn, disk_before):
        cur = conn.execute(
            "INSERT INTO engine_run_log (engine_name, start_time, status, disk_before_gb) "
            "VALUES (?, ?, 'running', ?)",
            (self.engine_name, _utcnow(), disk_before),
        )
        return cur.lastrowid

    def _update_run(self, conn, run_id, *, status, error_message=None,
                    rows_affected=None, disk_after=None, last_checkpoint=None):
        conn.execute(
            "UPDATE engine_run_log SET end_time=?, status=?, error_message=?, "
            "rows_affected=?, disk_after_gb=?, last_checkpoint=? WHERE id=?",
            (_utcnow(), status, error_message, rows_affected, disk_after,
             last_checkpoint, run_id),
        )
        conn.commit()

    # ── Guards ────────────────────────────────────────────────────────

    def _check_disk(self):
        free = _free_disk_gb()
        if free < MIN_DISK_GB:
            raise RuntimeError(
                f"Disk space guard: only {free} GB free on C: (minimum {MIN_DISK_GB} GB)"
            )
        self.logger.info("Disk guard OK: %.2f GB free", free)
        return free

    def _check_memory(self):
        free = _free_ram_gb()
        if free < WARN_RAM_GB:
            self.logger.warning("Memory guard: only %.2f GB RAM available", free)
        else:
            self.logger.info("Memory guard OK: %.2f GB free", free)
        return free

    # ── Checkpointing ─────────────────────────────────────────────────

    def checkpoint(self, name):
        """Create an intermediate savepoint inside the running engine."""
        if self._conn is None:
            raise RuntimeError("checkpoint() can only be called inside a harnessed run")
        sp_name = f"ckpt_{name}"
        self._conn.execute(f"RELEASE SAVEPOINT engine_main")
        self._conn.execute(f"SAVEPOINT engine_main")
        self._checkpoints.append(name)
        if self._run_id:
            self._conn.execute(
                "UPDATE engine_run_log SET last_checkpoint=? WHERE id=?",
                (name, self._run_id),
            )
            self._conn.commit()
            self._conn.execute("SAVEPOINT engine_main")
        self.logger.info("Checkpoint saved: %s", name)

    # ── Resume support ────────────────────────────────────────────────

    def get_last_checkpoint(self):
        """Return the last checkpoint name from the most recent crashed run, or None."""
        try:
            conn = sqlite3.connect(self.db_path)
            self._ensure_log_table(conn)
            row = conn.execute(
                "SELECT last_checkpoint FROM engine_run_log "
                "WHERE engine_name=? AND status='error' AND last_checkpoint IS NOT NULL "
                "ORDER BY id DESC LIMIT 1",
                (self.engine_name,),
            ).fetchone()
            conn.close()
            return row[0] if row else None
        except Exception:
            return None

    # ── WAL management ────────────────────────────────────────────────

    def _wal_checkpoint_if_needed(self, conn):
        wal_mb = _wal_size(self.db_path)
        if wal_mb > WAL_THRESHOLD_MB:
            self.logger.info("WAL is %.1f MB — running TRUNCATE checkpoint", wal_mb)
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        else:
            self.logger.info("WAL size OK: %.1f MB", wal_mb)

    # ── Core run decorator ────────────────────────────────────────────

    def run(self, func):
        """Decorator that wraps an engine function with full harness protections.

        The decorated function receives (conn, log) and may return a dict of metrics.
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return self._execute(func, *args, **kwargs)
        return wrapper

    def _execute(self, func, *args, **kwargs):
        last_err = None
        for attempt in range(1, self.retries + 1):
            try:
                return self._execute_once(func, attempt, *args, **kwargs)
            except Exception as exc:
                last_err = exc
                if attempt < self.retries:
                    wait = self.backoff_base ** attempt
                    self.logger.warning(
                        "Attempt %d/%d failed (%s). Retrying in %ds...",
                        attempt, self.retries, exc, wait,
                    )
                    time.sleep(wait)
                else:
                    self.logger.error(
                        "All %d attempts failed. Last error: %s", self.retries, exc
                    )
                    raise

    def _execute_once(self, func, attempt, *args, **kwargs):
        # Pre-flight guards
        disk_before = self._check_disk()
        self._check_memory()

        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        self._conn = conn
        self._checkpoints = []

        self._ensure_log_table(conn)
        run_id = self._insert_run(conn, disk_before)
        conn.commit()
        self._run_id = run_id

        self.logger.info(
            "Engine '%s' starting (attempt %d/%d, run_id=%d)",
            self.engine_name, attempt, self.retries, run_id,
        )

        try:
            conn.execute("SAVEPOINT engine_main")
            result = func(conn, self.logger, *args, **kwargs)
            conn.execute("RELEASE SAVEPOINT engine_main")

            rows = None
            if isinstance(result, dict):
                rows = result.get("rows") or result.get("rows_affected")

            disk_after = _free_disk_gb()
            self._update_run(
                conn, run_id, status="success",
                rows_affected=rows, disk_after=disk_after,
                last_checkpoint=self._checkpoints[-1] if self._checkpoints else None,
            )

            self._wal_checkpoint_if_needed(conn)
            self.logger.info("Engine '%s' completed successfully", self.engine_name)
            return result

        except Exception as exc:
            tb = traceback.format_exc()
            self.logger.error("Engine '%s' failed:\n%s", self.engine_name, tb)

            try:
                conn.execute("ROLLBACK TO SAVEPOINT engine_main")
                conn.execute("RELEASE SAVEPOINT engine_main")
            except Exception:
                pass

            disk_after = _free_disk_gb()
            try:
                self._update_run(
                    conn, run_id, status="error",
                    error_message=str(exc)[:2000], disk_after=disk_after,
                    last_checkpoint=self._checkpoints[-1] if self._checkpoints else None,
                )
            except Exception:
                pass

            raise
        finally:
            self._conn = None
            self._run_id = None
            try:
                conn.close()
            except Exception:
                pass

    # ── Wrap existing engine file ─────────────────────────────────────

    def wrap_existing(self, engine_path):
        """Import and execute an existing engine .py file under harness protection.

        The target file must define a function called `engine_main(conn, log)`.
        """
        spec = importlib.util.spec_from_file_location("wrapped_engine", engine_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        if not hasattr(mod, "engine_main"):
            raise AttributeError(
                f"{engine_path} must define an 'engine_main(conn, log)' function"
            )

        @self.run
        def _wrapped(conn, log):
            return mod.engine_main(conn, log)

        self.logger.info("Wrapping existing engine: %s", engine_path)
        return _wrapped()

    # ── CLI: --status ─────────────────────────────────────────────────

    @staticmethod
    def print_status(db_path=DEFAULT_DB, limit=20):
        """Print recent engine runs from the log table."""
        if not os.path.exists(db_path):
            print(f"Database not found: {db_path}")
            return

        conn = sqlite3.connect(db_path)
        try:
            # Check if table exists
            exists = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='engine_run_log'"
            ).fetchone()
            if not exists:
                print("engine_run_log table does not exist yet. No engines have been run.")
                conn.close()
                return

            rows = conn.execute(
                "SELECT id, engine_name, start_time, end_time, status, "
                "error_message, rows_affected, disk_before_gb, disk_after_gb, last_checkpoint "
                "FROM engine_run_log ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        finally:
            conn.close()

        if not rows:
            print("No engine runs recorded yet.")
            return

        print(f"\n{'='*100}")
        print(f"  LitigationOS Engine Run Log  (last {limit} runs)")
        print(f"{'='*100}")
        print(f"{'ID':>5}  {'Engine':<25} {'Status':<8} {'Start':<20} {'End':<20} {'Rows':>8}  {'Chkpt':<15}")
        print(f"{'-'*100}")
        for r in rows:
            rid, name, start, end, status, err, rows_aff, db, da, ckpt = r
            status_icon = {"success": "OK", "error": "FAIL", "running": "RUN"}.get(status, status)
            print(
                f"{rid:>5}  {(name or ''):<25} {status_icon:<8} "
                f"{(start or ''):<20} {(end or ''):<20} "
                f"{(rows_aff if rows_aff is not None else ''):>8}  {(ckpt or ''):<15}"
            )
            if err:
                print(f"       ERROR: {err[:80]}")
        print(f"{'='*100}\n")


# ── CLI entry point ───────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="LitigationOS Engine Harness")
    parser.add_argument("--status", action="store_true", help="Show recent engine runs")
    parser.add_argument("--db", default=DEFAULT_DB, help="Path to litigation_context.db")
    parser.add_argument("--limit", type=int, default=20, help="Number of recent runs to show")
    parser.add_argument("--wrap", type=str, help="Path to an engine .py file to run under harness")
    parser.add_argument("--engine-name", type=str, default=None, help="Engine name (used with --wrap)")
    args = parser.parse_args()

    if args.status:
        EngineHarness.print_status(db_path=args.db, limit=args.limit)
    elif args.wrap:
        name = args.engine_name or os.path.splitext(os.path.basename(args.wrap))[0]
        harness = EngineHarness(name, db_path=args.db)
        harness.wrap_existing(args.wrap)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
