#!/usr/bin/env python3
"""
_authority_merge.py  –  Merge authority_master.db → litigation_context.db
────────────────────────────────────────────────────────────────────────
• Copies every regular table from authority_master.db into litigation_context.db
  with an "auth_" prefix (e.g. rules → auth_rules).
• Rebuilds FTS5 virtual tables (auth_rules_fts, auth_passages_fts) on the target.
• Ingests MASTER_CITATIONS.csv into master_citations table in the target.
• Uses WAL mode + large cache on both connections.
• Batch inserts (executemany, 5 000-row chunks).  Never crashes.
"""
from __future__ import annotations

import csv
import os
import sqlite3
import sys
import time
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────
SOURCE_DB = Path(r"C:\Users\andre\LitigationOS\03_LEGAL_AUTHORITIES\authority_master.db")
TARGET_DB = Path(r"C:\Users\andre\litigation_context.db")
CSV_PATH  = Path(r"C:\Users\andre\LitigationOS\03_LEGAL_AUTHORITIES\case_citations\MASTER_CITATIONS.csv")

BATCH_SIZE = 5_000

# Tables to copy as regular tables (skip FTS shadow tables and sqlite internals)
SKIP_PREFIXES = ("passages_fts_", "rules_fts_", "sqlite_")
SKIP_EXACT    = {"passages_fts", "rules_fts"}  # FTS5 virtual tables – rebuild instead


def _pragma_tune(conn: sqlite3.Connection) -> None:
    """Apply WAL mode and generous cache to a connection."""
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-65536")
    conn.execute("PRAGMA synchronous=NORMAL")


def _table_list(conn: sqlite3.Connection) -> list[str]:
    """Return list of user-created table names."""
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    return [r[0] for r in cur.fetchall()]


def _create_table_like(
    src: sqlite3.Connection,
    dst: sqlite3.Connection,
    src_table: str,
    dst_table: str,
) -> list[str]:
    """
    Create *dst_table* in *dst* with the same columns as *src_table* in *src*.
    Returns the ordered list of column names.
    """
    info = src.execute(f'PRAGMA table_info("{src_table}")').fetchall()
    col_names = [row[1] for row in info]
    col_defs = []
    for row in info:
        # row: (cid, name, type, notnull, default_value, pk)
        parts = [f'"{row[1]}" {row[2]}']
        if row[5]:  # primary key
            parts.append("PRIMARY KEY")
        if row[3]:  # NOT NULL
            parts.append("NOT NULL")
        if row[4] is not None:
            parts.append(f"DEFAULT {row[4]}")
        col_defs.append(" ".join(parts))
    ddl = f'CREATE TABLE IF NOT EXISTS "{dst_table}" ({", ".join(col_defs)})'
    dst.execute(ddl)
    return col_names


def _copy_table(
    src: sqlite3.Connection,
    dst: sqlite3.Connection,
    src_table: str,
    dst_table: str,
) -> int:
    """Copy all rows from src_table to dst_table in batches. Returns row count."""
    cols = _create_table_like(src, dst, src_table, dst_table)
    placeholders = ", ".join(["?"] * len(cols))
    insert_sql = f'INSERT OR IGNORE INTO "{dst_table}" VALUES ({placeholders})'
    cursor = src.execute(f'SELECT * FROM "{src_table}"')
    total = 0
    while True:
        batch = cursor.fetchmany(BATCH_SIZE)
        if not batch:
            break
        dst.executemany(insert_sql, batch)
        total += len(batch)
    dst.commit()
    return total


def _rebuild_fts(dst: sqlite3.Connection) -> None:
    """Create FTS5 virtual tables on the copied auth_ data tables."""
    # auth_rules_fts → index on auth_rules
    try:
        dst.execute("DROP TABLE IF EXISTS auth_rules_fts")
        dst.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS auth_rules_fts
            USING fts5(
                id, rule_number, title, full_text, summary,
                content='auth_rules',
                content_rowid='rowid'
            )
        """)
        dst.execute("""
            INSERT INTO auth_rules_fts(auth_rules_fts) VALUES('rebuild')
        """)
        dst.commit()
        cnt = dst.execute("SELECT COUNT(*) FROM auth_rules_fts").fetchone()[0]
        print(f"  ✓ auth_rules_fts rebuilt ({cnt:,} rows)")
    except Exception as exc:
        print(f"  ⚠ auth_rules_fts rebuild failed: {exc}")

    # auth_passages_fts → index on auth_authority_passages
    try:
        dst.execute("DROP TABLE IF EXISTS auth_passages_fts")
        dst.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS auth_passages_fts
            USING fts5(
                rule_id, passage_text, section,
                content='auth_authority_passages',
                content_rowid='rowid'
            )
        """)
        dst.execute("""
            INSERT INTO auth_passages_fts(auth_passages_fts) VALUES('rebuild')
        """)
        dst.commit()
        cnt = dst.execute("SELECT COUNT(*) FROM auth_passages_fts").fetchone()[0]
        print(f"  ✓ auth_passages_fts rebuilt ({cnt:,} rows)")
    except Exception as exc:
        print(f"  ⚠ auth_passages_fts rebuild failed: {exc}")


def _ingest_csv(dst: sqlite3.Connection, csv_path: Path) -> int:
    """Read MASTER_CITATIONS.csv and insert into master_citations table."""
    if not csv_path.exists():
        print(f"\n⚠ CSV not found: {csv_path}")
        return 0

    size_mb = csv_path.stat().st_size / (1024 * 1024)
    print(f"\n{'='*72}")
    print(f"Ingesting CSV: {csv_path} ({size_mb:.1f} MB)")

    with open(csv_path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f)
        headers = next(reader)
        headers_clean = [h.strip().lower().replace(" ", "_") for h in headers]

        # Create table
        col_defs = ", ".join([f'"{h}" TEXT' for h in headers_clean])
        dst.execute(f"CREATE TABLE IF NOT EXISTS master_citations ({col_defs})")

        placeholders = ", ".join(["?"] * len(headers_clean))
        insert_sql = f"INSERT INTO master_citations VALUES ({placeholders})"

        total = 0
        batch: list[tuple] = []
        for row in reader:
            # Pad/truncate row to match header count
            if len(row) < len(headers_clean):
                row.extend([""] * (len(headers_clean) - len(row)))
            elif len(row) > len(headers_clean):
                row = row[: len(headers_clean)]
            batch.append(tuple(row))
            if len(batch) >= BATCH_SIZE:
                dst.executemany(insert_sql, batch)
                total += len(batch)
                if total % 50_000 == 0:
                    print(f"  … {total:>10,} rows ingested")
                batch.clear()
        if batch:
            dst.executemany(insert_sql, batch)
            total += len(batch)
        dst.commit()

    print(f"  ✓ master_citations: {total:,} rows ingested")
    return total


# ── Main ───────────────────────────────────────────────────────────────
def main() -> None:
    print("=" * 72)
    print("AUTHORITY MERGE  –  authority_master.db → litigation_context.db")
    print("=" * 72)

    if not SOURCE_DB.exists():
        print(f"FATAL: Source DB not found: {SOURCE_DB}")
        sys.exit(1)
    if not TARGET_DB.exists():
        print(f"FATAL: Target DB not found: {TARGET_DB}")
        sys.exit(1)

    src = sqlite3.connect(str(SOURCE_DB))
    dst = sqlite3.connect(str(TARGET_DB))
    _pragma_tune(src)
    _pragma_tune(dst)

    tables = _table_list(src)
    tables_to_copy = [
        t for t in tables
        if t not in SKIP_EXACT
        and not any(t.startswith(p) for p in SKIP_PREFIXES)
    ]

    print(f"\nSource tables: {len(tables)} total, {len(tables_to_copy)} to copy")
    print(f"Skipping FTS shadow tables + sqlite internals + FTS virtual tables\n")

    results: dict[str, int] = {}

    for tbl in tables_to_copy:
        dst_name = f"auth_{tbl}"
        t0 = time.time()
        try:
            count = _copy_table(src, dst, tbl, dst_name)
            elapsed = time.time() - t0
            results[dst_name] = count
            print(f"  ✓ {tbl:30s} → {dst_name:40s}  {count:>10,} rows  ({elapsed:.1f}s)")
        except Exception as exc:
            results[dst_name] = -1
            print(f"  ✗ {tbl:30s} → {dst_name:40s}  ERROR: {exc}")

    # Rebuild FTS5 indexes on the target
    print(f"\nRebuilding FTS5 indexes …")
    _rebuild_fts(dst)

    # Ingest CSV
    csv_count = _ingest_csv(dst, CSV_PATH)
    if csv_count > 0:
        results["master_citations"] = csv_count

    # Summary
    print(f"\n{'='*72}")
    print("MERGE SUMMARY")
    print(f"{'='*72}")
    total_rows = 0
    for name, count in results.items():
        status = f"{count:>10,} rows" if count >= 0 else "     ERROR"
        print(f"  {name:45s} {status}")
        if count > 0:
            total_rows += count
    print(f"\n  TOTAL: {total_rows:,} rows across {len(results)} tables")
    print(f"{'='*72}")

    src.close()
    dst.close()
    print("Done.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"\nUNEXPECTED ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
