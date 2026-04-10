"""
adaptive_insert.py — Schema-introspecting DB inserter for LitigationOS.

NEVER hardcode column names. This module reads PRAGMA table_info() at runtime,
maps your dict keys to actual columns, warns on mismatches, and inserts only
what the table actually accepts. Zero column-name crashes, ever.

Usage:
    from shared.adaptive_insert import adaptive_insert, adaptive_insert_many, get_columns

    # Single row
    adaptive_insert(conn, "evidence_quotes", {
        "source_file": "police_report_204.pdf",
        "quote_text": "Emily stated nothing was physical",
        "category": "false_allegation",
        "lane": "A",
    })

    # Batch
    rows = [{"source_file": "...", "quote_text": "...", ...}, ...]
    adaptive_insert_many(conn, "evidence_quotes", rows)
"""

import sqlite3
import logging
from typing import Any
from functools import lru_cache

logger = logging.getLogger(__name__)

# Cache schema per (db_path, table) to avoid repeated PRAGMAs within one session
_schema_cache: dict[tuple[str, str], set[str]] = {}


def get_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    """Return the set of column names for a table. Cached per connection+table."""
    db_path = conn.execute("PRAGMA database_list").fetchone()[2] or "memory"
    key = (db_path, table)
    if key not in _schema_cache:
        rows = conn.execute(f"PRAGMA table_info([{table}])").fetchall()
        if not rows:
            raise ValueError(f"Table '{table}' does not exist or has no columns")
        _schema_cache[key] = {row[1] for row in rows}
    return _schema_cache[key]


def clear_cache():
    """Clear the schema cache (call after ALTER TABLE or schema changes)."""
    _schema_cache.clear()


def _filter_data(conn: sqlite3.Connection, table: str, data: dict[str, Any]) -> dict[str, Any]:
    """Filter a data dict to only keys that match actual table columns.
    Warns on dropped keys. Never crashes on mismatch."""
    columns = get_columns(conn, table)
    filtered = {}
    dropped = []
    for k, v in data.items():
        if k in columns:
            filtered[k] = v
        elif k != "id":  # silently skip auto-increment id
            dropped.append(k)
    if dropped:
        logger.warning("adaptive_insert: dropped keys not in %s schema: %s", table, dropped)
    return filtered


def adaptive_insert(
    conn: sqlite3.Connection,
    table: str,
    data: dict[str, Any],
    *,
    or_ignore: bool = True,
    or_replace: bool = False,
) -> int:
    """Insert a single row into `table`, mapping only keys that match real columns.

    Returns: lastrowid on success, -1 on failure (logged, not raised).
    """
    filtered = _filter_data(conn, table, data)
    if not filtered:
        logger.warning("adaptive_insert: no matching columns for %s — skipping", table)
        return -1

    cols = list(filtered.keys())
    vals = [filtered[c] for c in cols]
    placeholders = ", ".join(["?"] * len(cols))
    col_str = ", ".join(cols)

    conflict = ""
    if or_replace:
        conflict = "OR REPLACE"
    elif or_ignore:
        conflict = "OR IGNORE"

    sql = f"INSERT {conflict} INTO [{table}] ({col_str}) VALUES ({placeholders})"
    try:
        cur = conn.execute(sql, vals)
        return cur.lastrowid
    except sqlite3.Error as e:
        logger.error("adaptive_insert into %s failed: %s | SQL: %s", table, e, sql)
        return -1


def adaptive_insert_many(
    conn: sqlite3.Connection,
    table: str,
    rows: list[dict[str, Any]],
    *,
    or_ignore: bool = True,
    or_replace: bool = False,
    batch_size: int = 500,
) -> int:
    """Batch-insert multiple rows. All rows must have the same keys (first row's keys used).

    Returns: total rows inserted.
    """
    if not rows:
        return 0

    # Use first row to determine column mapping
    filtered_template = _filter_data(conn, table, rows[0])
    if not filtered_template:
        logger.warning("adaptive_insert_many: no matching columns for %s — skipping", table)
        return 0

    cols = list(filtered_template.keys())
    placeholders = ", ".join(["?"] * len(cols))
    col_str = ", ".join(cols)

    conflict = ""
    if or_replace:
        conflict = "OR REPLACE"
    elif or_ignore:
        conflict = "OR IGNORE"

    sql = f"INSERT {conflict} INTO [{table}] ({col_str}) VALUES ({placeholders})"

    total = 0
    for i in range(0, len(rows), batch_size):
        batch = rows[i : i + batch_size]
        values = []
        for row in batch:
            values.append(tuple(row.get(c) for c in cols))
        try:
            conn.executemany(sql, values)
            total += len(batch)
        except sqlite3.Error as e:
            logger.error("adaptive_insert_many batch %d failed: %s", i // batch_size, e)

    conn.commit()
    return total


def show_schema(conn: sqlite3.Connection, table: str) -> str:
    """Pretty-print a table's schema for debugging."""
    rows = conn.execute(f"PRAGMA table_info([{table}])").fetchall()
    lines = [f"=== {table} ({len(rows)} columns) ==="]
    for r in rows:
        cid, name, dtype, notnull, default, pk = r
        flags = []
        if pk:
            flags.append("PK")
        if notnull:
            flags.append("NOT NULL")
        if default is not None:
            flags.append(f"DEFAULT {default}")
        flag_str = f" ({', '.join(flags)})" if flags else ""
        lines.append(f"  {name}: {dtype}{flag_str}")
    return "\n".join(lines)


# Convenience: print all 4 core litigation tables
def show_core_schemas(conn: sqlite3.Connection) -> str:
    """Show schemas for evidence_quotes, timeline_events, impeachment_matrix, berry_mcneill_intelligence."""
    tables = ["evidence_quotes", "timeline_events", "impeachment_matrix", "berry_mcneill_intelligence"]
    return "\n\n".join(show_schema(conn, t) for t in tables)
