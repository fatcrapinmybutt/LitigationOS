#!/usr/bin/env python3
"""
db_lock_manager.py — Tier-2 SQLite Connection Manager for LitigationOS
======================================================================
Provides managed_db() context manager with:
- 3-connection semaphore (EAGAIN prevention)
- WAL mode, busy_timeout=60s, 32MB cache
- Read-only mode support
- Health checking and WAL enforcement

Usage:
    from db_lock_manager import managed_db, check_db_health, ensure_wal_mode

    with managed_db("path/to/db.db") as conn:
        rows = conn.execute("SELECT * FROM table").fetchall()
"""

import sqlite3
import threading
import os
from contextlib import contextmanager
from pathlib import Path

_semaphore = threading.Semaphore(3)  # Max 3 concurrent connections
_active_count = 0
_count_lock = threading.Lock()


@contextmanager
def managed_db(db_path, readonly=False):
    """Context manager for safe SQLite access with concurrency control.

    Args:
        db_path: Path to the SQLite database file.
        readonly: If True, sets PRAGMA query_only = ON.

    Yields:
        sqlite3.Connection with Row factory and optimized PRAGMAs.
    """
    global _active_count
    _semaphore.acquire()
    with _count_lock:
        _active_count += 1
    conn = None
    try:
        conn = sqlite3.connect(str(db_path), timeout=60)
        conn.execute("PRAGMA busy_timeout = 60000")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA cache_size = -32000")
        conn.execute("PRAGMA temp_store = MEMORY")
        conn.execute("PRAGMA synchronous = NORMAL")
        if readonly:
            conn.execute("PRAGMA query_only = ON")
        conn.row_factory = sqlite3.Row
        yield conn
        if not readonly:
            conn.commit()
    except Exception:
        if conn and not readonly:
            try:
                conn.rollback()
            except Exception:
                pass
        raise
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass
        with _count_lock:
            _active_count -= 1
        _semaphore.release()


def get_connection_count():
    """Return the number of currently active managed connections."""
    with _count_lock:
        return _active_count


def check_db_health(db_path):
    """Run PRAGMA integrity_check on a database.

    Args:
        db_path: Path to the SQLite database file.

    Returns:
        dict with keys: path, size_bytes, status ('ok', 'corrupt', 'empty', 'missing', 'error'),
              table_count, and detail.
    """
    db_path = str(db_path)
    result = {"path": db_path, "size_bytes": 0, "status": "unknown", "table_count": 0, "detail": ""}

    if not os.path.exists(db_path):
        result["status"] = "missing"
        result["detail"] = "File does not exist"
        return result

    size = os.path.getsize(db_path)
    result["size_bytes"] = size

    if size == 0:
        result["status"] = "empty"
        result["detail"] = "0 bytes — needs rebuild"
        return result

    try:
        conn = sqlite3.connect(db_path, timeout=10)
        conn.execute("PRAGMA busy_timeout = 10000")

        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
        table_count = conn.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
        ).fetchone()[0]

        conn.close()

        result["table_count"] = table_count
        if integrity == "ok":
            result["status"] = "ok"
            result["detail"] = f"Integrity OK, {table_count} tables"
        else:
            result["status"] = "corrupt"
            result["detail"] = integrity[:200]
    except Exception as e:
        result["status"] = "error"
        result["detail"] = str(e)[:200]

    return result


def ensure_wal_mode(db_path):
    """Ensure a database is using WAL journal mode.

    Args:
        db_path: Path to the SQLite database file.

    Returns:
        True if WAL mode is active after the call, False otherwise.
    """
    try:
        conn = sqlite3.connect(str(db_path), timeout=10)
        conn.execute("PRAGMA busy_timeout = 10000")
        mode = conn.execute("PRAGMA journal_mode = WAL").fetchone()[0]
        conn.close()
        return mode.lower() == "wal"
    except Exception:
        return False


if __name__ == "__main__":
    import sys
    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace', closefd=False)

    print("db_lock_manager.py — LitigationOS Tier-2 Connection Manager")
    print(f"  Semaphore slots: 3")
    print(f"  Active connections: {get_connection_count()}")

    if len(sys.argv) > 1:
        path = sys.argv[1]
        print(f"\nHealth check: {path}")
        result = check_db_health(path)
        for k, v in result.items():
            print(f"  {k}: {v}")
