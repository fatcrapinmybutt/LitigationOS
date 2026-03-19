"""
LitigationOS Safe DB Wrapper
============================
Import THIS instead of sqlite3 in all scripts.
Automatically uses the Shell Resilience Engine for:
- WAL mode (concurrent readers, no hangs)
- Timeout protection (10s max wait)
- Retry with backoff on lock contention
- Cycle Method for large outputs

Usage:
    from safe_db_wrapper import db, query, write, fts, health

    # Quick query
    rows = query("SELECT * FROM auth_rules LIMIT 5")

    # FTS search
    results = fts("evidence_quotes_fts", "Watson")

    # Write with auto-retry
    write("INSERT INTO my_table VALUES (?, ?)", ("a", "b"))

    # Context manager
    with db() as conn:
        conn.execute("SELECT ...")

    # Health check
    print(health())
"""
import logging
import sys
import os

logger = logging.getLogger(__name__)

# Add parent to path
_DIR = os.path.dirname(os.path.abspath(__file__))
_PARENT = os.path.dirname(_DIR)
if _PARENT not in sys.path:
    sys.path.insert(0, _PARENT)

from shell_resilience_engine import (
    safe_db as db,
    safe_query as query,
    safe_write as write,
    safe_write_many as write_many,
    safe_fts as fts,
    safe_shell as shell,
    db_health_check as health,
    enforce_wal_mode,
    wal_checkpoint,
    cycle_print,
    cycle_json,
    init,
    DB_PATH,
)

# Auto-init WAL on import
try:
    init()
except Exception as e:
    logger.warning(f"DB WAL init deferred (may be locked): {e}")

__all__ = [
    "db", "query", "write", "write_many", "fts", "shell", "health",
    "enforce_wal_mode", "wal_checkpoint", "cycle_print", "cycle_json",
    "init", "DB_PATH"
]
