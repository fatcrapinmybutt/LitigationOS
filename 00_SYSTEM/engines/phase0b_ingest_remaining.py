#!/usr/bin/env python3
"""
phase0b_ingest_remaining.py
Ingests remaining structured data into litigation_context.db:
  1. MI Warchest Pinnacle v5  (SQLite → mi_warchest_*)
  2. MI Warchest v1           (SQLite → mi_warchest_v1_*)
  3. Authority Store 2        (SQLite → authority_store_*)
  4. Superpin Pack MAX        (text files → superpin_reference_docs + FTS5)
  5. MI Superpin Atlas        (text files → mi_atlas_docs + FTS5)
  6. Gemini Masterpack v01    (text files → gemini_masterpack_docs + FTS5)
  7. authority_shards JSONL   (JSONL → authority_shards + FTS5) — if readable
"""

import sqlite3
import os
import json
import re
import time
import glob as globmod
import traceback

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"

# ── helpers ─────────────────────────────────────────────────────────
def log(msg):
    print(f"[phase0b] {msg}")

def get_table_count(conn):
    return conn.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
    ).fetchone()[0]

def drop_tables_with_prefix(conn, prefix):
    """Drop all tables whose name starts with prefix."""
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE ?",
        (prefix + "%",),
    ).fetchall()
    for (tname,) in tables:
        log(f"  DROP TABLE [{tname}]")
        conn.execute(f"DROP TABLE IF EXISTS [{tname}]")
    conn.commit()
    return len(tables)

def copy_sqlite_tables(conn, src_path, prefix, alias="src"):
    """Attach src_path, copy every user table with the given prefix.
    Skips FTS5 virtual tables and their shadow tables."""
    log(f"  Attaching {src_path} as [{alias}]")
    conn.execute(f"ATTACH DATABASE ? AS [{alias}]", (src_path,))

    # Get all regular tables (not virtual/FTS shadow tables)
    all_tables = conn.execute(
        f"SELECT name FROM [{alias}].sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()

    # Identify FTS5 virtual tables
    fts_tables = set()
    vtables = conn.execute(
        f"SELECT name FROM [{alias}].sqlite_master WHERE type='table' AND sql LIKE '%fts5%'"
    ).fetchall()
    for (vt,) in vtables:
        fts_tables.add(vt)
    # Also check for virtual tables via sqlite_master type='table' with fts in sql
    vtables2 = conn.execute(
        f"SELECT name, sql FROM [{alias}].sqlite_master WHERE type='table'"
    ).fetchall()
    for vt_name, vt_sql in vtables2:
        if vt_sql and "fts5" in vt_sql.lower():
            fts_tables.add(vt_name)

    # Build set of FTS shadow table names (e.g. tablename_content, _data, etc.)
    fts_shadow_names = set()
    for ft in fts_tables:
        for suffix in ["_config", "_content", "_data", "_docsize", "_idx", "_vocab"]:
            fts_shadow_names.add(ft + suffix)

    # Filter to only copyable tables
    tables = [(t,) for (t,) in all_tables if t not in fts_tables and t not in fts_shadow_names]
    skipped = [t for (t,) in all_tables if t in fts_tables or t in fts_shadow_names]
    log(f"  Found {len(all_tables)} tables in source ({len(tables)} copyable, {len(skipped)} FTS skipped)")
    if skipped:
        log(f"  Skipped FTS tables: {skipped}")

    total_rows = 0
    tables_created = 0
    for (tname,) in tables:
        dest = f"{prefix}{tname}"
        row_count = conn.execute(f"SELECT COUNT(*) FROM [{alias}].[{tname}]").fetchone()[0]

        # Get CREATE TABLE DDL and rewrite
        ddl = conn.execute(
            f"SELECT sql FROM [{alias}].sqlite_master WHERE type='table' AND name=?",
            (tname,),
        ).fetchone()[0]

        if ddl:
            # Replace original table name with prefixed name
            # Handle both CREATE TABLE name and CREATE TABLE "name"
            new_ddl = re.sub(
                r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?:\[.*?\]|\".*?\"|`.*?`|\S+)",
                f"CREATE TABLE IF NOT EXISTS [{dest}]",
                ddl,
                count=1,
                flags=re.IGNORECASE,
            )
            try:
                conn.execute(new_ddl)
            except sqlite3.OperationalError as e:
                log(f"    WARN creating [{dest}]: {e} — using fallback SELECT INTO")
                conn.execute(f"DROP TABLE IF EXISTS [{dest}]")
                conn.execute(
                    f"CREATE TABLE [{dest}] AS SELECT * FROM [{alias}].[{tname}] WHERE 0"
                )
        else:
            conn.execute(
                f"CREATE TABLE IF NOT EXISTS [{dest}] AS SELECT * FROM [{alias}].[{tname}] WHERE 0"
            )

        conn.execute(f"INSERT INTO [{dest}] SELECT * FROM [{alias}].[{tname}]")
        conn.commit()
        log(f"    [{dest}]: {row_count} rows")
        total_rows += row_count
        tables_created += 1

    conn.execute(f"DETACH DATABASE [{alias}]")
    return tables_created, total_rows


def extract_category(filename):
    """Extract category from filename patterns."""
    fn_upper = filename.upper()
    categories = [
        ("SYSTEM_PROMPT", "SYSTEM_PROMPT"),
        ("VEHICLE", "VEHICLE"),
        ("EVIDENCE", "EVIDENCE"),
        ("AUTHORITY", "AUTHORITY"),
        ("GATE", "GATE"),
        ("PIN", "PIN"),
        ("TIMELINE", "TIMELINE"),
        ("RULE", "RULE"),
        ("PROPOSITION", "PROPOSITION"),
        ("CITATION", "CITATION"),
        ("CLUSTER", "CLUSTER"),
        ("INDEX", "INDEX"),
        ("STRATEGY", "STRATEGY"),
        ("SKELETON", "SKELETON"),
        ("BRIEF", "BRIEF"),
        ("MOTION", "MOTION"),
        ("SUPERPIN", "SUPERPIN"),
        ("ATLAS", "ATLAS"),
        ("MASTER", "MASTER"),
        ("CONFIG", "CONFIG"),
        ("README", "README"),
        ("PROMPT", "PROMPT"),
    ]
    for pattern, cat in categories:
        if pattern in fn_upper:
            return cat
    return "GENERAL"


def ingest_text_files(conn, directory, table_name, fts_name, extensions=None):
    """Read text/md files from directory, store in table with FTS5 index."""
    if extensions is None:
        extensions = {".txt", ".md", ".json", ".jsonl", ".csv", ".py", ".yaml",
                      ".toml", ".html", ".rtf", ".sh", ".ps1", ".env"}

    conn.execute(f"DROP TABLE IF EXISTS [{table_name}]")
    conn.execute(f"""
        CREATE TABLE [{table_name}] (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            content TEXT,
            file_size INTEGER,
            category TEXT
        )
    """)

    # Drop FTS tables (main + shadow tables)
    for suffix in ["", "_config", "_content", "_data", "_docsize", "_idx"]:
        conn.execute(f"DROP TABLE IF EXISTS [{fts_name}{suffix}]")

    files = []
    for root, dirs, fnames in os.walk(directory):
        for fn in fnames:
            ext = os.path.splitext(fn)[1].lower()
            if ext in extensions:
                files.append(os.path.join(root, fn))

    log(f"  Found {len(files)} text files in {directory}")
    total_rows = 0
    for fpath in sorted(files):
        fname = os.path.basename(fpath)
        fsize = os.path.getsize(fpath)
        category = extract_category(fname)

        # Try multiple encodings
        content = None
        for enc in ["utf-8-sig", "utf-8", "cp1252", "latin-1"]:
            try:
                with open(fpath, "r", encoding=enc) as f:
                    content = f.read()
                break
            except (UnicodeDecodeError, UnicodeError):
                continue

        if content is None:
            log(f"    SKIP (unreadable): {fname}")
            continue

        conn.execute(
            f"INSERT INTO [{table_name}] (filename, content, file_size, category) VALUES (?, ?, ?, ?)",
            (fname, content, fsize, category),
        )
        total_rows += 1

    conn.commit()

    # Create FTS5 index
    conn.execute(f"""
        CREATE VIRTUAL TABLE IF NOT EXISTS [{fts_name}]
        USING fts5(content, filename, content=[{table_name}], content_rowid=id)
    """)
    conn.execute(f"""
        INSERT INTO [{fts_name}]([{fts_name}])
        VALUES('rebuild')
    """)
    conn.commit()
    log(f"  Created FTS5 index [{fts_name}] over {total_rows} documents")
    return total_rows


def ingest_authority_shards(conn):
    """Attempt to parse authority_shards JSONL files."""
    candidates = [
        r"G:\Legal\authority_shards_all.jsonl",
        r"G:\Legal\authority_shards_all(0).jsonl",
        r"G:\Legal\authority_shards_all(1).jsonl",
    ]

    # Find a readable JSONL file
    valid_file = None
    for fpath in candidates:
        if not os.path.exists(fpath):
            continue
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                line = f.readline().strip()
                if line and line.startswith("{"):
                    json.loads(line)
                    valid_file = fpath
                    break
        except Exception:
            continue

    if not valid_file:
        log("  No readable JSONL authority_shards file found — skipping")
        return 0

    log(f"  Parsing {valid_file}")
    conn.execute("DROP TABLE IF EXISTS [authority_shards]")

    # Read first line to get schema
    with open(valid_file, "r", encoding="utf-8") as f:
        first = json.loads(f.readline())
    cols = list(first.keys())

    col_defs = ", ".join(f"[{c}] TEXT" for c in cols)
    conn.execute(f"CREATE TABLE [authority_shards] (id INTEGER PRIMARY KEY AUTOINCREMENT, {col_defs})")

    placeholders = ", ".join(["?"] * len(cols))
    insert_sql = f"INSERT INTO [authority_shards] ({', '.join(f'[{c}]' for c in cols)}) VALUES ({placeholders})"

    count = 0
    with open(valid_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                vals = [str(obj.get(c, "")) if obj.get(c) is not None else None for c in cols]
                conn.execute(insert_sql, vals)
                count += 1
                if count % 5000 == 0:
                    conn.commit()
            except json.JSONDecodeError:
                continue

    conn.commit()

    # FTS5 if there's a text-heavy column
    text_cols = [c for c in cols if any(k in c.lower() for k in ["text", "content", "body", "snippet", "passage"])]
    if text_cols:
        fts_cols = ", ".join(text_cols)
        for suffix in ["", "_config", "_content", "_data", "_docsize", "_idx"]:
            conn.execute(f"DROP TABLE IF EXISTS [authority_shards_fts{suffix}]")
        conn.execute(f"""
            CREATE VIRTUAL TABLE [authority_shards_fts]
            USING fts5({fts_cols}, content=[authority_shards], content_rowid=id)
        """)
        conn.execute("INSERT INTO [authority_shards_fts]([authority_shards_fts]) VALUES('rebuild')")
        conn.commit()
        log(f"  Created FTS5 index on columns: {text_cols}")

    log(f"  authority_shards: {count} rows")
    return count


# ── main ────────────────────────────────────────────────────────────
def main():
    t0 = time.time()
    log(f"Opening {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=-64000")  # 64 MB cache

    initial_tables = get_table_count(conn)
    log(f"Initial table count: {initial_tables}")

    grand_total_rows = 0
    grand_total_tables = 0

    # ─── 1. MI Warchest Pinnacle v5 ────────────────────────────────
    log("\n═══ 1. MI Warchest Pinnacle v5 ═══")
    src = r"I:\out\mi_warchest_pinnacle_v5(1).sqlite"
    dropped = drop_tables_with_prefix(conn, "mi_warchest_")
    log(f"  Dropped {dropped} existing mi_warchest_* tables")
    tc, rc = copy_sqlite_tables(conn, src, "mi_warchest_", alias="warchest_v5")
    grand_total_tables += tc
    grand_total_rows += rc
    log(f"  Subtotal: {tc} tables, {rc} rows")

    # ─── 2. MI Warchest v1 ─────────────────────────────────────────
    log("\n═══ 2. MI Warchest v1 ═══")
    src = r"F:\MI_WARCHEST_BUILDER_v1_WITH_OUTPUT\out\mi_warchest.sqlite"
    dropped = drop_tables_with_prefix(conn, "mi_warchest_v1_")
    log(f"  Dropped {dropped} existing mi_warchest_v1_* tables")
    tc, rc = copy_sqlite_tables(conn, src, "mi_warchest_v1_", alias="warchest_v1")
    grand_total_tables += tc
    grand_total_rows += rc
    log(f"  Subtotal: {tc} tables, {rc} rows")

    # ─── 3. Authority Store 2 ──────────────────────────────────────
    log("\n═══ 3. Authority Store 2 ═══")
    src = r"G:\Legal\authority_store_2.sqlite"
    dropped = drop_tables_with_prefix(conn, "authority_store_")
    log(f"  Dropped {dropped} existing authority_store_* tables")
    tc, rc = copy_sqlite_tables(conn, src, "authority_store_", alias="auth_store")
    grand_total_tables += tc
    grand_total_rows += rc
    log(f"  Subtotal: {tc} tables, {rc} rows")

    # ─── 4. Superpin Pack MAX ──────────────────────────────────────
    log("\n═══ 4. Superpin Pack MAX ═══")
    d = r"F:\LitigationOS_Gemini_Superpin_Pack_v2026-02-13_MAX_2026-02-14_035616_REV4"
    drop_tables_with_prefix(conn, "superpin_reference_docs")
    drop_tables_with_prefix(conn, "superpin_reference_fts")
    rc = ingest_text_files(conn, d, "superpin_reference_docs", "superpin_reference_fts")
    grand_total_tables += 2  # table + FTS
    grand_total_rows += rc
    log(f"  Subtotal: 2 tables, {rc} rows")

    # ─── 5. MI Superpin Atlas ──────────────────────────────────────
    log("\n═══ 5. MI Superpin Atlas ═══")
    d = r"F:\MI_SUPERPIN_ATLAS_v2026-02-14"
    drop_tables_with_prefix(conn, "mi_atlas_docs")
    drop_tables_with_prefix(conn, "mi_atlas_fts")
    rc = ingest_text_files(conn, d, "mi_atlas_docs", "mi_atlas_fts")
    grand_total_tables += 2
    grand_total_rows += rc
    log(f"  Subtotal: 2 tables, {rc} rows")

    # ─── 6. Gemini Masterpack v01 ──────────────────────────────────
    log("\n═══ 6. Gemini Masterpack v01 ═══")
    d = r"F:\LITIGATIONOS_GEMINI_MASTERPACK_v2026-02-14_01"
    drop_tables_with_prefix(conn, "gemini_masterpack_docs")
    drop_tables_with_prefix(conn, "gemini_masterpack_fts")
    rc = ingest_text_files(conn, d, "gemini_masterpack_docs", "gemini_masterpack_fts")
    grand_total_tables += 2
    grand_total_rows += rc
    log(f"  Subtotal: 2 tables, {rc} rows")

    # ─── 7. Authority Shards JSONL ─────────────────────────────────
    log("\n═══ 7. Authority Shards JSONL ═══")
    rc = ingest_authority_shards(conn)
    if rc > 0:
        grand_total_tables += 1
        grand_total_rows += rc

    # ─── Summary ───────────────────────────────────────────────────
    final_tables = get_table_count(conn)
    elapsed = time.time() - t0

    log("\n" + "═" * 60)
    log("INGESTION COMPLETE")
    log(f"  Tables before: {initial_tables}")
    log(f"  Tables after:  {final_tables}")
    log(f"  New tables created: {final_tables - initial_tables}")
    log(f"  Total rows ingested this run: {grand_total_rows:,}")
    log(f"  Elapsed: {elapsed:.1f}s")
    log("═" * 60)

    conn.close()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"FATAL ERROR: {e}")
        traceback.print_exc()
        raise
