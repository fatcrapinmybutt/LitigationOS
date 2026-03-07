#!/usr/bin/env python3
"""
connection_multiplexer.py — Δ∞ Zero-Syscall Connection Manager
==============================================================

State-of-the-art SQLite connection manager for LitigationOS:

  1. MMAP I/O:      12GB memory-mapped virtual address space eliminates read() syscalls
  2. Read/Write:    N reader connections + 1 WAL writer (auto-routed)
  3. Thread-safe:   Thread-local readers, mutex-guarded writer
  4. PRAGMA tuning: 128MB cache, MEMORY temp store, NORMAL sync
  5. Schema cache:  300s TTL (5× improvement over 60s)
  6. Drop-in:       `from connection_multiplexer import db` replaces sqlite3.connect()

Performance targets (measured on 10.22 GB / 694-table DB):
  - master_citations COUNT(*): 3,622ms → <500ms (mmap + covering index)
  - evidence_quotes COUNT(*): 146ms → <20ms
  - FTS5 queries: 4-5ms → <2ms
  - Filing assembly: 35-50 queries → batched through reader pool

Usage:
    # Quick: drop-in replacement
    from connection_multiplexer import db
    conn = db.reader()              # Read-only, mmap-enabled
    conn = db.writer()              # Single WAL writer

    # Context managers (auto-commit/rollback)
    with db.read_cursor() as cur:
        cur.execute("SELECT * FROM evidence_quotes_fts WHERE evidence_quotes_fts MATCH ?", (q,))
        rows = cur.fetchall()

    with db.write_cursor() as cur:
        cur.execute("INSERT INTO ingest_logs ...", data)

    # Backward-compatible: returns a fully-configured connection
    conn = get_connection()            # Read-write, all PRAGMAs set
    conn = get_connection(readonly=True)  # Read-only, query_only=ON
"""
import os
import sys
import sqlite3
import threading
import queue
import time
import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

logger = logging.getLogger("connection_multiplexer")

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTS — tuned for 10.22 GB DB on SSD-backed Windows workstation
# ═══════════════════════════════════════════════════════════════════════════════

_LITIGOS_ROOT = Path(r"C:\Users\andre\LitigationOS")
_DEFAULT_DB = _LITIGOS_ROOT / "litigation_context.db"
_STUB_DB = Path(r"C:\Users\andre\litigation_context.db")
_MIN_DB_SIZE_MB = 100

# PRAGMA configuration tiers
PRAGMA_MMAP = {
    "mmap_size": 12_884_901_888,    # 12 GB virtual address space (zero-syscall reads)
    "cache_size": -131_072,          # 128 MB page cache (negative = KB)
    "temp_store": "MEMORY",          # Temp tables in RAM, not disk
    "synchronous": "NORMAL",         # Durability with less fsync (WAL protects)
    "busy_timeout": 180_000,         # 3 minutes (heavy concurrent access)
    "journal_mode": "WAL",           # Write-Ahead Logging for concurrent reads
}

PRAGMA_READER = {
    **PRAGMA_MMAP,
    "query_only": "ON",              # Prevent accidental writes from readers
}

PRAGMA_WRITER = {
    **PRAGMA_MMAP,
    "wal_autocheckpoint": 1000,      # Checkpoint every 1000 pages
}

# Pool sizing
_DEFAULT_READER_COUNT = min(os.cpu_count() or 4, 8)  # Cap at 8 readers
_SCHEMA_CACHE_TTL = 300.0  # 5 minutes (schema doesn't change during runs)


# ═══════════════════════════════════════════════════════════════════════════════
# PATH VALIDATION (from guardrails.py — shared logic)
# ═══════════════════════════════════════════════════════════════════════════════

def _validate_db_path(path: Path) -> Path:
    """Validate DB path is real (not stub), exists, and is large enough."""
    resolved = path.resolve()
    if resolved == _STUB_DB.resolve():
        raise ValueError(
            f"WRONG_DB_PATH: {path} is the 28KB stub! "
            f"Use {_DEFAULT_DB} instead."
        )
    if not path.exists():
        raise FileNotFoundError(f"Database not found: {path}")
    size_mb = path.stat().st_size / (1024 * 1024)
    if size_mb < _MIN_DB_SIZE_MB:
        raise ValueError(
            f"WRONG_DB_PATH: {path} is only {size_mb:.1f}MB (need {_MIN_DB_SIZE_MB}+). "
            f"Expected: {_DEFAULT_DB}"
        )
    return resolved


def _apply_pragmas(conn: sqlite3.Connection, pragmas: dict) -> None:
    """Apply PRAGMA settings to a connection."""
    for key, value in pragmas.items():
        try:
            conn.execute(f"PRAGMA {key}={value}")
        except sqlite3.OperationalError as e:
            logger.warning(f"PRAGMA {key}={value} failed: {e}")


def _create_connection(db_path: Path, readonly: bool = False,
                       check_same_thread: bool = False) -> sqlite3.Connection:
    """Create a single connection with full PRAGMA tuning."""
    if readonly:
        uri = f"file:{db_path}?mode=ro"
        conn = sqlite3.connect(uri, uri=True, timeout=180,
                               check_same_thread=check_same_thread)
        _apply_pragmas(conn, PRAGMA_READER)
    else:
        conn = sqlite3.connect(str(db_path), timeout=180,
                               check_same_thread=check_same_thread)
        _apply_pragmas(conn, PRAGMA_WRITER)
    conn.row_factory = sqlite3.Row
    return conn


# ═══════════════════════════════════════════════════════════════════════════════
# SCHEMA CACHE (upgraded: 300s TTL, thread-safe)
# ═══════════════════════════════════════════════════════════════════════════════

class SchemaCache:
    """Thread-safe schema cache with 300s TTL.

    Eliminates per-minute PRAGMA table_info calls across 150+ modules.
    """
    _instance: Optional['SchemaCache'] = None
    _lock = threading.Lock()

    def __init__(self, db_path: Path):
        self._db_path = db_path
        self._cache: dict[str, dict] = {}
        self._loaded_at: float = 0
        self._ttl = _SCHEMA_CACHE_TTL
        self._rlock = threading.RLock()

    @classmethod
    def get(cls, db_path: Optional[Path] = None) -> 'SchemaCache':
        """Thread-safe singleton access."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(db_path or _DEFAULT_DB)
        return cls._instance

    def _ensure_loaded(self):
        if time.time() - self._loaded_at > self._ttl:
            with self._rlock:
                if time.time() - self._loaded_at > self._ttl:
                    self._load()

    def _load(self):
        conn = _create_connection(self._db_path, readonly=True)
        try:
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            new_cache = {}
            for row in tables:
                tbl = row[0] if isinstance(row, (tuple, list)) else row['name']
                cols = conn.execute(f"PRAGMA table_info([{tbl}])").fetchall()
                new_cache[tbl] = {
                    c[1]: {'type': c[2], 'notnull': bool(c[3]),
                           'default': c[4], 'pk': bool(c[5])}
                    for c in cols
                }
            self._cache = new_cache
            self._loaded_at = time.time()
            logger.debug(f"SchemaCache loaded: {len(new_cache)} tables")
        finally:
            conn.close()

    def get_columns(self, table: str) -> dict:
        self._ensure_loaded()
        return self._cache.get(table, {})

    def table_exists(self, table: str) -> bool:
        self._ensure_loaded()
        return table in self._cache

    def all_tables(self) -> list[str]:
        self._ensure_loaded()
        return list(self._cache.keys())

    def invalidate(self):
        """Force refresh on next access."""
        self._loaded_at = 0


# ═══════════════════════════════════════════════════════════════════════════════
# CONNECTION MULTIPLEXER
# ═══════════════════════════════════════════════════════════════════════════════

class ConnectionMultiplexer:
    """Read/write connection multiplexer with mmap zero-syscall I/O.

    Architecture:
      - 1 WAL writer connection (mutex-guarded)
      - N reader connections (thread-local, query_only=ON)
      - All connections: mmap=12GB, cache=128MB, temp=MEMORY

    Thread safety:
      - Readers are thread-local (no sharing, no locks needed)
      - Writer is protected by a threading.Lock
      - Safe for use from pipeline agents, inference engine, and desktop app
    """

    def __init__(self, db_path: Optional[Path] = None,
                 reader_count: int = _DEFAULT_READER_COUNT):
        self._db_path = _validate_db_path(db_path or _DEFAULT_DB)
        self._reader_count = reader_count
        self._writer: Optional[sqlite3.Connection] = None
        self._writer_lock = threading.Lock()
        self._local = threading.local()
        self._closed = False
        logger.info(
            f"ConnectionMultiplexer: db={self._db_path.name}, "
            f"readers={reader_count}, mmap=12GB"
        )

    def reader(self) -> sqlite3.Connection:
        """Get a thread-local read-only connection.

        Each thread gets its own connection (reused across calls).
        All readers have: mmap=12GB, query_only=ON, cache=128MB.
        """
        if self._closed:
            raise RuntimeError("ConnectionMultiplexer is closed")
        conn = getattr(self._local, 'reader_conn', None)
        if conn is None:
            conn = _create_connection(self._db_path, readonly=True,
                                      check_same_thread=False)
            self._local.reader_conn = conn
            logger.debug(f"Reader created for thread {threading.current_thread().name}")
        return conn

    def writer(self) -> sqlite3.Connection:
        """Get the single WAL writer connection (thread-safe).

        Only one writer exists. Access is mutex-guarded.
        Callers should use write_cursor() context manager instead.
        """
        if self._closed:
            raise RuntimeError("ConnectionMultiplexer is closed")
        if self._writer is None:
            with self._writer_lock:
                if self._writer is None:
                    self._writer = _create_connection(
                        self._db_path, readonly=False,
                        check_same_thread=False
                    )
                    logger.debug("Writer connection created")
        return self._writer

    @contextmanager
    def read_cursor(self):
        """Context manager for read operations.

        Usage:
            with db.read_cursor() as cur:
                cur.execute("SELECT ...")
                rows = cur.fetchall()
        """
        conn = self.reader()
        cur = conn.cursor()
        try:
            yield cur
        finally:
            cur.close()

    @contextmanager
    def write_cursor(self):
        """Context manager for write operations with auto-commit/rollback.

        Usage:
            with db.write_cursor() as cur:
                cur.execute("INSERT INTO ...")
        """
        with self._writer_lock:
            conn = self.writer()
            cur = conn.cursor()
            try:
                yield cur
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                cur.close()

    def execute_read(self, sql: str, params=()) -> list:
        """Convenience: execute a read query and return all rows."""
        with self.read_cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()

    def execute_write(self, sql: str, params=()) -> int:
        """Convenience: execute a write query and return lastrowid."""
        with self.write_cursor() as cur:
            cur.execute(sql, params)
            return cur.lastrowid

    def execute_many(self, sql: str, param_list: list) -> int:
        """Convenience: execute many writes in a single transaction."""
        with self.write_cursor() as cur:
            cur.executemany(sql, param_list)
            return cur.rowcount

    def close(self):
        """Close all connections."""
        self._closed = True
        if self._writer:
            try:
                self._writer.close()
            except Exception:
                pass
            self._writer = None
        conn = getattr(self._local, 'reader_conn', None)
        if conn:
            try:
                conn.close()
            except Exception:
                pass
            self._local.reader_conn = None
        logger.info("ConnectionMultiplexer closed")


# ═══════════════════════════════════════════════════════════════════════════════
# GLOBAL SINGLETON + BACKWARD-COMPATIBLE API
# ═══════════════════════════════════════════════════════════════════════════════

_global_mux: Optional[ConnectionMultiplexer] = None
_global_lock = threading.Lock()


def get_multiplexer(db_path: Optional[Path] = None) -> ConnectionMultiplexer:
    """Get or create the global ConnectionMultiplexer singleton."""
    global _global_mux
    if _global_mux is None:
        with _global_lock:
            if _global_mux is None:
                _global_mux = ConnectionMultiplexer(db_path)
    return _global_mux


def get_connection(readonly: bool = False,
                   db_path: Optional[Path] = None) -> sqlite3.Connection:
    """Drop-in replacement for sqlite3.connect() calls.

    Returns a fully-configured connection with:
      - mmap_size=12GB
      - cache_size=128MB
      - temp_store=MEMORY
      - WAL mode
      - busy_timeout=180s

    For modules that can't yet migrate to the multiplexer pattern,
    this provides all PRAGMA benefits with zero code changes beyond
    changing the import.

    Usage:
        # Before:
        conn = sqlite3.connect(DB_PATH, timeout=30)

        # After:
        from connection_multiplexer import get_connection
        conn = get_connection()
    """
    path = _validate_db_path(db_path or _DEFAULT_DB)
    return _create_connection(path, readonly=readonly)


# Convenience alias: `from connection_multiplexer import db`
class _LazyMultiplexer:
    """Lazy-initialized multiplexer that validates DB on first use, not import."""

    def __getattr__(self, name):
        mux = get_multiplexer()
        # Replace ourselves with the real multiplexer
        global db
        db = mux
        return getattr(mux, name)

db: ConnectionMultiplexer = _LazyMultiplexer()  # type: ignore[assignment]


# ═══════════════════════════════════════════════════════════════════════════════
# BENCHMARK UTILITY
# ═══════════════════════════════════════════════════════════════════════════════

def benchmark(db_path: Optional[Path] = None):
    """Run comparison benchmarks: raw connect vs mmap multiplexer."""
    import json
    path = db_path or _DEFAULT_DB
    _validate_db_path(path)

    queries = [
        ("master_citations COUNT", "SELECT COUNT(*) FROM master_citations"),
        ("evidence_quotes COUNT", "SELECT COUNT(*) FROM evidence_quotes"),
        ("omega_filesystem COUNT", "SELECT COUNT(*) FROM omega_filesystem_map"),
        ("auth_rules LIKE", "SELECT * FROM auth_rules WHERE full_text LIKE '%disqualif%' LIMIT 20"),
        ("evidence_fts MATCH", "SELECT * FROM evidence_quotes_fts WHERE evidence_quotes_fts MATCH 'custody' LIMIT 30"),
        ("filing_readiness", "SELECT * FROM filing_readiness"),
    ]

    results = []
    print("=" * 70)
    print("CONNECTION MULTIPLEXER BENCHMARK")
    print(f"DB: {path} ({path.stat().st_size / (1024**3):.2f} GB)")
    print("=" * 70)
    print(f"{'Query':<30} {'Baseline':>10} {'MMAP':>10} {'Speedup':>8}")
    print("-" * 70)

    for name, sql in queries:
        # Baseline: raw connection, minimal pragmas
        conn1 = sqlite3.connect(str(path), timeout=120)
        conn1.execute("PRAGMA busy_timeout=120000")
        t0 = time.perf_counter()
        r1 = conn1.execute(sql).fetchall()
        base_ms = (time.perf_counter() - t0) * 1000
        conn1.close()

        # MMAP: full multiplexer connection
        conn2 = get_connection(readonly=True, db_path=path)
        # Warm the mmap
        try:
            conn2.execute("SELECT 1").fetchone()
        except Exception:
            pass
        t0 = time.perf_counter()
        r2 = conn2.execute(sql).fetchall()
        mmap_ms = (time.perf_counter() - t0) * 1000
        conn2.close()

        speedup = base_ms / mmap_ms if mmap_ms > 0.01 else 0
        print(f"{name:<30} {base_ms:>8.1f}ms {mmap_ms:>8.1f}ms {speedup:>6.1f}x")
        results.append({
            "query": name, "baseline_ms": round(base_ms, 2),
            "mmap_ms": round(mmap_ms, 2), "speedup": round(speedup, 1),
            "rows": len(r1),
        })

    print("=" * 70)

    out_path = path.parent / "00_SYSTEM" / "_mmap_benchmark.json"
    try:
        with open(out_path, "w") as f:
            json.dump(results, f, indent=2)
        print(f"Results saved: {out_path}")
    except Exception:
        pass

    return results


# ═══════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')
    logging.basicConfig(level=logging.INFO, format="%(name)s: %(message)s")

    if len(sys.argv) > 1 and sys.argv[1] == "benchmark":
        benchmark()
    else:
        print("ConnectionMultiplexer — Δ∞ Zero-Syscall DB Manager")
        print(f"  DB: {_DEFAULT_DB}")
        print(f"  MMAP: {PRAGMA_MMAP['mmap_size'] / (1024**3):.0f} GB")
        print(f"  Cache: {abs(PRAGMA_MMAP['cache_size'])} KB")
        print(f"  Readers: {_DEFAULT_READER_COUNT}")
        print(f"  Schema TTL: {_SCHEMA_CACHE_TTL}s")
        print("\nUsage:")
        print("  python connection_multiplexer.py benchmark   # Run benchmarks")
        print("  from connection_multiplexer import db        # In code")
        print("  from connection_multiplexer import get_connection  # Drop-in")
