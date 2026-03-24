#!/usr/bin/env python3
"""
connection_multiplexer.py — Tier-1 SQLite Connection Multiplexer for LitigationOS
==================================================================================
High-performance connection pool with:
- mmap_size = 12GB, cache_size = 128MB, busy_timeout = 180s
- Connection pool (max 5 connections)
- Read/write splitting
- Health monitoring

Usage:
    from connection_multiplexer import ConnectionMultiplexer

    mux = ConnectionMultiplexer("path/to/db.db")
    with mux.reader() as conn:
        rows = conn.execute("SELECT * FROM table").fetchall()
    with mux.writer() as conn:
        conn.execute("INSERT INTO table VALUES (?)", (val,))
    mux.close_all()
"""

import sqlite3
import threading
import time
import os
from contextlib import contextmanager
from pathlib import Path

# Tier-1 PRAGMAs — maximum performance for the central 10GB+ database
TIER1_PRAGMAS = {
    "busy_timeout": 180000,        # 180 seconds
    "journal_mode": "WAL",
    "cache_size": -131072,         # 128 MB (negative = KB)
    "mmap_size": 12884901888,      # 12 GB
    "temp_store": "MEMORY",
    "synchronous": "NORMAL",
    "wal_autocheckpoint": 1000,
    "page_size": 4096,
}


class ConnectionMultiplexer:
    """Tier-1 connection pool with read/write splitting and health monitoring."""

    def __init__(self, db_path, max_readers=4, max_writers=1):
        """Initialize the multiplexer.

        Args:
            db_path: Path to the SQLite database.
            max_readers: Maximum concurrent reader connections (default 4).
            max_writers: Maximum concurrent writer connections (default 1).
        """
        self.db_path = str(db_path)
        self.max_readers = max_readers
        self.max_writers = max_writers

        self._reader_sem = threading.Semaphore(max_readers)
        self._writer_sem = threading.Semaphore(max_writers)
        self._lock = threading.Lock()

        self._active_readers = 0
        self._active_writers = 0
        self._total_reads = 0
        self._total_writes = 0
        self._errors = 0
        self._created_at = time.time()

    def _create_connection(self, readonly=False):
        """Create a new connection with Tier-1 PRAGMAs."""
        conn = sqlite3.connect(self.db_path, timeout=180)

        for pragma, value in TIER1_PRAGMAS.items():
            try:
                conn.execute(f"PRAGMA {pragma} = {value}")
            except sqlite3.OperationalError:
                pass  # Some PRAGMAs may not be supported on all SQLite versions

        if readonly:
            try:
                conn.execute("PRAGMA query_only = ON")
            except sqlite3.OperationalError:
                pass

        conn.row_factory = sqlite3.Row
        return conn

    @contextmanager
    def reader(self):
        """Acquire a read-only connection from the pool.

        Yields:
            sqlite3.Connection configured for read-only access.
        """
        self._reader_sem.acquire()
        with self._lock:
            self._active_readers += 1
        conn = None
        try:
            conn = self._create_connection(readonly=True)
            yield conn
            with self._lock:
                self._total_reads += 1
        except Exception:
            with self._lock:
                self._errors += 1
            raise
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass
            with self._lock:
                self._active_readers -= 1
            self._reader_sem.release()

    @contextmanager
    def writer(self):
        """Acquire a read-write connection from the pool.

        Yields:
            sqlite3.Connection configured for read-write access.
            Auto-commits on success, rolls back on exception.
        """
        self._writer_sem.acquire()
        with self._lock:
            self._active_writers += 1
        conn = None
        try:
            conn = self._create_connection(readonly=False)
            yield conn
            conn.commit()
            with self._lock:
                self._total_writes += 1
        except Exception:
            if conn:
                try:
                    conn.rollback()
                except Exception:
                    pass
            with self._lock:
                self._errors += 1
            raise
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass
            with self._lock:
                self._active_writers -= 1
            self._writer_sem.release()

    def health(self):
        """Return health statistics for the multiplexer.

        Returns:
            dict with pool status, counters, and DB file info.
        """
        with self._lock:
            stats = {
                "db_path": self.db_path,
                "active_readers": self._active_readers,
                "active_writers": self._active_writers,
                "total_reads": self._total_reads,
                "total_writes": self._total_writes,
                "errors": self._errors,
                "uptime_seconds": round(time.time() - self._created_at, 1),
                "max_readers": self.max_readers,
                "max_writers": self.max_writers,
            }

        # DB file health
        try:
            stats["db_size_mb"] = round(os.path.getsize(self.db_path) / (1024 * 1024), 1)
            stats["db_exists"] = True
        except OSError:
            stats["db_size_mb"] = 0
            stats["db_exists"] = False

        # WAL file size
        wal_path = self.db_path + "-wal"
        try:
            stats["wal_size_mb"] = round(os.path.getsize(wal_path) / (1024 * 1024), 1)
        except OSError:
            stats["wal_size_mb"] = 0

        return stats

    def checkpoint(self):
        """Force a WAL checkpoint (TRUNCATE mode).

        Returns:
            Tuple of (busy_pages, log_pages, checkpointed_pages) or None on error.
        """
        try:
            conn = self._create_connection(readonly=False)
            result = conn.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()
            conn.close()
            return tuple(result) if result else None
        except Exception:
            return None

    def close_all(self):
        """Reset pool counters. Connections are per-context-manager so no pool to drain."""
        with self._lock:
            self._active_readers = 0
            self._active_writers = 0


if __name__ == "__main__":
    import sys
    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace', closefd=False)

    print("connection_multiplexer.py — LitigationOS Tier-1 Connection Multiplexer")
    print(f"  Tier-1 PRAGMAs:")
    for k, v in TIER1_PRAGMAS.items():
        print(f"    {k} = {v}")

    if len(sys.argv) > 1:
        db_path = sys.argv[1]
        print(f"\nCreating multiplexer for: {db_path}")
        mux = ConnectionMultiplexer(db_path)
        health = mux.health()
        for k, v in health.items():
            print(f"  {k}: {v}")
        mux.close_all()
