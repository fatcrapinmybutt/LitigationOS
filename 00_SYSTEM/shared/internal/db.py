"""
Database connection factory for LitigationOS.

Provides get_db() — THE one way to open a database connection.
Every connection gets standard PRAGMAs applied automatically.

Replaces the pattern of hardcoding sqlite3.connect() + ad-hoc PRAGMAs
that was duplicated across 7+ modules with inconsistent settings.
"""

import os
import sqlite3
import time
import functools
import logging
from contextlib import contextmanager
from pathlib import Path

logger = logging.getLogger("litigationos.shared")


class LitigationDBError(Exception):
    """Raised for database configuration or connection errors."""
    pass


# ---------------------------------------------------------------------------
# Standard PRAGMAs — applied to EVERY connection
# ---------------------------------------------------------------------------
# These are the optimized settings for LitigationOS databases.
# Based on pipeline/connection_multiplexer.py Tier-1 PRAGMAs, tuned
# for the common case (read-heavy, WAL mode, large DB).

STANDARD_PRAGMAS: dict[str, int | str] = {
    "busy_timeout": 60000,       # 60 seconds (safe for concurrent reads)
    "journal_mode": "WAL",       # Write-ahead log (concurrent reads)
    "cache_size": -32000,        # 32 MB (negative = KB)
    "mmap_size": 268435456,      # 256 MB memory-mapped I/O
    "temp_store": 2,             # MEMORY (2 = memory)
    "synchronous": "NORMAL",     # Safe with WAL
}


def _apply_pragmas(conn: sqlite3.Connection) -> None:
    """Apply standard PRAGMAs to a connection."""
    for pragma, value in STANDARD_PRAGMAS.items():
        try:
            conn.execute(f"PRAGMA {pragma} = {value}")
        except sqlite3.OperationalError:
            pass  # Some PRAGMAs not supported on all SQLite versions


def get_db_path(name: str = "litigation") -> Path:
    """Resolve a database name to its filesystem path.

    Checks environment variable overrides first:
    - LITIGATION_DB_PATH for "litigation"
    - NEXUS_DB_PATH for "litigation" (legacy compat)
    - BRAIN_DIR + name.db for brain databases

    Then falls back to the DB_REGISTRY in config.py.

    Args:
        name: Logical database name (e.g., "litigation", "authority_brain").

    Returns:
        Absolute Path to the database file.

    Raises:
        LitigationDBError: If the database name is unknown.
    """
    from .config import DB_REGISTRY, get_root

    # Environment variable overrides (highest priority)
    if name == "litigation":
        env_path = os.environ.get("LITIGATION_DB_PATH") or os.environ.get("NEXUS_DB_PATH")
        if env_path:
            return Path(env_path)

    brain_dir_env = os.environ.get("BRAIN_DIR")
    if brain_dir_env and name.endswith("_brain"):
        return Path(brain_dir_env) / f"{name}.db"

    # Registry lookup
    if name not in DB_REGISTRY:
        raise LitigationDBError(
            f"Unknown database: '{name}'. "
            f"Known databases: {', '.join(sorted(DB_REGISTRY.keys()))}"
        )

    return get_root() / DB_REGISTRY[name]


def get_db(name: str = "litigation", readonly: bool = False) -> sqlite3.Connection:
    """Open a database connection with standard PRAGMAs.

    This is THE way to connect to any LitigationOS database.
    Every connection gets WAL mode, busy_timeout, cache, mmap, etc.

    Args:
        name: Logical database name (default: "litigation").
              See DB_REGISTRY in config.py for all known names.
        readonly: If True, set PRAGMA query_only = ON.

    Returns:
        sqlite3.Connection with row_factory=sqlite3.Row and standard PRAGMAs.

    Raises:
        LitigationDBError: If database name is unknown or file not found.
    """
    db_path = get_db_path(name)

    if not db_path.exists():
        raise LitigationDBError(
            f"Database file not found: {db_path}. "
            f"Ensure the file exists or set the appropriate environment variable."
        )

    try:
        conn = sqlite3.connect(str(db_path), timeout=60)
    except sqlite3.Error as e:
        raise LitigationDBError(f"Failed to connect to {name}: {e}") from e

    conn.row_factory = sqlite3.Row
    _apply_pragmas(conn)

    if readonly:
        try:
            conn.execute("PRAGMA query_only = ON")
        except sqlite3.OperationalError:
            pass

    return conn


_connection_pool: dict[str, sqlite3.Connection] = {}


@contextmanager
def db_connection(name: str = "litigation", readonly: bool = False, reuse: bool = False):
    """Context manager for database connections with automatic cleanup.

    Args:
        name: Database name.
        readonly: If True, open in read-only mode.
        reuse: If True, reuse cached connection (faster for repeated calls).

    Usage:
        with db_connection() as conn:
            rows = conn.execute("SELECT * FROM evidence_quotes LIMIT 10").fetchall()
    """
    if reuse and name in _connection_pool:
        conn = _connection_pool[name]
        try:
            conn.execute("SELECT 1")  # Verify connection is alive
            yield conn
            return
        except Exception:
            _connection_pool.pop(name, None)

    conn = get_db(name, readonly)
    try:
        if reuse:
            _connection_pool[name] = conn
        yield conn
    finally:
        if not reuse:
            try:
                conn.close()
            except Exception:
                pass


def close_pool():
    """Close all pooled connections. Call at shutdown."""
    for name, conn in _connection_pool.items():
        try:
            conn.close()
        except Exception:
            pass
    _connection_pool.clear()


@contextmanager
def db_transaction(conn):
    """Transaction context manager with automatic commit/rollback.

    Usage:
        with db_connection() as conn:
            with db_transaction(conn):
                conn.execute("INSERT INTO ...")
                conn.execute("UPDATE ...")
                # auto-commits on success, rolls back on exception
    """
    conn.execute("BEGIN")
    try:
        yield conn
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise


def retry_on_busy(max_retries: int = 3, base_delay: float = 1.0):
    """Decorator: retry on sqlite3.OperationalError with exponential backoff.

    Usage:
        @retry_on_busy(max_retries=3)
        def my_query():
            conn = get_db()
            return conn.execute("SELECT ...").fetchall()
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except sqlite3.OperationalError as e:
                    last_error = e
                    if "database is locked" in str(e) and attempt < max_retries:
                        delay = base_delay * (2 ** attempt)
                        logger.warning(
                            f"DB locked (attempt {attempt + 1}/{max_retries + 1}), "
                            f"retrying in {delay:.1f}s: {func.__name__}"
                        )
                        time.sleep(delay)
                    else:
                        raise
            raise last_error
        return wrapper
    return decorator


@contextmanager
def query_timer(label: str = "query"):
    """Context manager that logs query execution time.

    Usage:
        with query_timer("evidence search"):
            rows = conn.execute("SELECT ...").fetchall()
        # Logs: "evidence search completed in 0.045s"
    """
    start = time.perf_counter()
    yield
    elapsed = time.perf_counter() - start
    if elapsed > 0.1:
        logger.warning(f"SLOW {label}: {elapsed:.3f}s")
    else:
        logger.debug(f"{label}: {elapsed:.3f}s")


def get_db_readonly(name: str = "litigation"):
    """Convenience shortcut for read-only connections.

    Equivalent to get_db(name, readonly=True).
    """
    return get_db(name, readonly=True)
