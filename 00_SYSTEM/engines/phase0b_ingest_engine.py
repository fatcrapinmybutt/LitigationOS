#!/usr/bin/env python3
"""
phase0b_ingest_engine.py — Multi-source structured data ingestion into litigation_context.db
Ingests CSV/TSV/JSON/JSONL/SQLite from PERMAFIX R12-R14, MI Warchest, DocForge V18,
HYPERVISOR CYCLE0011, CYCLEPACK NO_LIMIT_FULL, and MEEK234 KNOWLEDGE_ALL.
"""

import csv
import json
import os
import re
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# ── Configuration ────────────────────────────────────────────────────────────
DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"
BATCH_SIZE = 10_000
BATCH_SIZE_JSONL = 5_000

csv.field_size_limit(2**31 - 1)  # handle huge fields


# ── Helpers ──────────────────────────────────────────────────────────────────

def fmt_size(n):
    """Human-readable file size."""
    for u in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.2f} {u}"
        n /= 1024
    return f"{n:.2f} TB"


def open_file(path):
    """Open text file with encoding fallback."""
    for enc in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            f = open(path, "r", encoding=enc, newline="")
            f.read(4096)
            f.seek(0)
            return f
        except (UnicodeDecodeError, UnicodeError):
            continue
    return open(path, "r", encoding="latin-1", errors="replace", newline="")


def detect_delimiter(path):
    """Sniff CSV delimiter from first few lines."""
    with open_file(path) as f:
        sample = f.read(8192)
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",\t|;")
        return dialect.delimiter
    except csv.Error:
        if "\t" in sample:
            return "\t"
        return ","


def sanitize_col(name):
    """Make a column name SQLite-safe."""
    name = re.sub(r"[^\w]", "_", name.strip()).strip("_")
    if not name or name[0].isdigit():
        name = "col_" + name
    return name.lower()


def sanitize_table(name):
    """Make a table name SQLite-safe."""
    return re.sub(r"[^\w]", "_", name.strip()).strip("_").lower()


def find_files(base_dir, patterns, extensions=(".csv", ".tsv", ".json", ".jsonl")):
    """Find files matching any pattern (case-insensitive substring) under base_dir."""
    results = {}
    if not os.path.isdir(base_dir):
        return results
    for root, _, files in os.walk(base_dir):
        for fn in files:
            fn_low = fn.lower()
            ext = os.path.splitext(fn_low)[1]
            if ext not in extensions:
                continue
            for pat in patterns:
                if pat.lower() in fn_low:
                    if pat not in results:
                        results[pat] = os.path.join(root, fn)
                    break
    return results


def find_sqlite_files(base_dir):
    """Recursively find .sqlite, .sqlite3, .db files."""
    hits = []
    if not os.path.isdir(base_dir):
        return hits
    for root, _, files in os.walk(base_dir):
        for fn in files:
            if fn.lower().endswith((".sqlite", ".sqlite3", ".db")):
                hits.append(os.path.join(root, fn))
    return hits


def find_text_file(base_dir, pattern, extensions=(".csv", ".tsv", ".txt", ".md")):
    """Find a single text file matching pattern."""
    if not os.path.isdir(base_dir):
        return None
    for root, _, files in os.walk(base_dir):
        for fn in files:
            fn_low = fn.lower()
            ext = os.path.splitext(fn_low)[1]
            if ext in extensions and pattern.lower() in fn_low:
                # Prefer CSV/TSV over TXT/MD
                return os.path.join(root, fn)
    return None


# ── Ingest functions ─────────────────────────────────────────────────────────

def ingest_csv(conn, table_name, file_path, batch_size=BATCH_SIZE):
    """Stream-ingest a CSV/TSV file into a SQLite table."""
    fsize = os.path.getsize(file_path)
    print(f"  → Ingesting {os.path.basename(file_path)} ({fmt_size(fsize)}) → [{table_name}]")

    delim = detect_delimiter(file_path)
    f = open_file(file_path)
    reader = csv.reader(f, delimiter=delim)

    # Read header
    try:
        raw_header = next(reader)
    except StopIteration:
        print(f"    ⚠ Empty file, skipping")
        f.close()
        return 0

    cols = [sanitize_col(c) for c in raw_header]
    # Deduplicate column names
    seen = {}
    for i, c in enumerate(cols):
        if c in seen:
            seen[c] += 1
            cols[i] = f"{c}_{seen[c]}"
        else:
            seen[c] = 0

    col_defs = ", ".join(f'"{c}" TEXT' for c in cols)
    conn.execute(f'DROP TABLE IF EXISTS "{table_name}"')
    conn.execute(f'CREATE TABLE "{table_name}" ({col_defs})')

    placeholders = ", ".join("?" * len(cols))
    insert_sql = f'INSERT INTO "{table_name}" VALUES ({placeholders})'

    total = 0
    batch = []
    ncols = len(cols)
    for row in reader:
        # Pad or trim to match header
        if len(row) < ncols:
            row.extend([""] * (ncols - len(row)))
        elif len(row) > ncols:
            row = row[:ncols]
        batch.append(row)
        if len(batch) >= batch_size:
            conn.executemany(insert_sql, batch)
            conn.commit()
            total += len(batch)
            print(f"    ... {total:,} rows", end="\r")
            batch.clear()

    if batch:
        conn.executemany(insert_sql, batch)
        conn.commit()
        total += len(batch)

    f.close()
    print(f"    ✓ {total:,} rows ingested                ")
    return total


def ingest_text_as_table(conn, table_name, file_path):
    """Store a text/markdown file as a table with line_num and line columns."""
    fsize = os.path.getsize(file_path)
    print(f"  → Ingesting text {os.path.basename(file_path)} ({fmt_size(fsize)}) → [{table_name}]")

    conn.execute(f'DROP TABLE IF EXISTS "{table_name}"')
    conn.execute(f'CREATE TABLE "{table_name}" (line_num INTEGER, line TEXT)')

    f = open_file(file_path)
    batch = []
    total = 0
    for i, line in enumerate(f, 1):
        batch.append((i, line.rstrip("\n\r")))
        if len(batch) >= BATCH_SIZE:
            conn.executemany(f'INSERT INTO "{table_name}" VALUES (?, ?)', batch)
            conn.commit()
            total += len(batch)
            batch.clear()
    if batch:
        conn.executemany(f'INSERT INTO "{table_name}" VALUES (?, ?)', batch)
        conn.commit()
        total += len(batch)
    f.close()
    print(f"    ✓ {total:,} lines ingested")
    return total


def ingest_sqlite_source(conn, source_path, prefix):
    """Attach a SQLite source and copy all its tables with a prefix."""
    fsize = os.path.getsize(source_path)
    print(f"  → Attaching {os.path.basename(source_path)} ({fmt_size(fsize)})")

    alias = "src_" + prefix.rstrip("_")
    conn.execute(f'ATTACH DATABASE ? AS "{alias}"', (source_path,))

    tables = conn.execute(
        f"SELECT name FROM \"{alias}\".sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()

    results = []
    for (src_table,) in tables:
        if src_table.startswith("sqlite_"):
            continue
        dest_table = prefix + sanitize_table(src_table)
        try:
            cols_info = conn.execute(f'PRAGMA "{alias}".table_info("{src_table}")').fetchall()
            if not cols_info:
                continue

            conn.execute(f'DROP TABLE IF EXISTS main."{dest_table}"')

            # Get CREATE TABLE statement
            create_sql = conn.execute(
                f"SELECT sql FROM \"{alias}\".sqlite_master WHERE type='table' AND name=?",
                (src_table,)
            ).fetchone()[0]

            # Rewrite CREATE TABLE to use dest_table name in main schema
            create_sql = re.sub(
                r'CREATE\s+TABLE\s+("[^"]+"|[^\s(]+)',
                f'CREATE TABLE main."{dest_table}"',
                create_sql,
                count=1,
                flags=re.IGNORECASE,
            )
            conn.execute(create_sql)

            # Stream copy in batches
            total = 0
            col_names = [c[1] for c in cols_info]
            placeholders = ", ".join("?" * len(col_names))
            insert_sql = f'INSERT INTO main."{dest_table}" VALUES ({placeholders})'

            cursor = conn.execute(f'SELECT * FROM "{alias}"."{src_table}"')
            while True:
                rows = cursor.fetchmany(BATCH_SIZE)
                if not rows:
                    break
                conn.executemany(insert_sql, rows)
                conn.commit()
                total += len(rows)

            print(f"    ✓ {src_table} → {dest_table}: {total:,} rows")
            results.append((dest_table, total, source_path))
        except Exception as e:
            print(f"    ⚠ Error copying {src_table}: {e}")
            results.append((dest_table, 0, source_path))

    conn.execute(f'DETACH DATABASE "{alias}"')
    return results


def ingest_jsonl(conn, table_name, file_path, batch_size=BATCH_SIZE_JSONL):
    """Stream-ingest a JSONL file: first pass detects all keys, second pass inserts."""
    fsize = os.path.getsize(file_path)
    print(f"  → Ingesting {os.path.basename(file_path)} ({fmt_size(fsize)}) → [{table_name}]")

    # First pass: collect all keys
    all_keys = []
    key_set = set()
    with open_file(file_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if isinstance(obj, dict):
                    for k in obj.keys():
                        if k not in key_set:
                            key_set.add(k)
                            all_keys.append(k)
            except json.JSONDecodeError:
                continue

    if not all_keys:
        print(f"    ⚠ No valid JSON objects found, skipping")
        return 0

    cols = [sanitize_col(k) for k in all_keys]
    # Deduplicate
    seen = {}
    for i, c in enumerate(cols):
        if c in seen:
            seen[c] += 1
            cols[i] = f"{c}_{seen[c]}"
        else:
            seen[c] = 0

    col_defs = ", ".join(f'"{c}" TEXT' for c in cols)
    conn.execute(f'DROP TABLE IF EXISTS "{table_name}"')
    conn.execute(f'CREATE TABLE "{table_name}" ({col_defs})')

    placeholders = ", ".join("?" * len(cols))
    insert_sql = f'INSERT INTO "{table_name}" VALUES ({placeholders})'

    # Second pass: insert data
    total = 0
    batch = []
    with open_file(file_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(obj, dict):
                continue
            row = []
            for k in all_keys:
                val = obj.get(k)
                if val is None:
                    row.append(None)
                elif isinstance(val, (dict, list)):
                    row.append(json.dumps(val, ensure_ascii=False))
                else:
                    row.append(str(val))
            batch.append(row)
            if len(batch) >= batch_size:
                conn.executemany(insert_sql, batch)
                conn.commit()
                total += len(batch)
                print(f"    ... {total:,} rows", end="\r")
                batch.clear()

    if batch:
        conn.executemany(insert_sql, batch)
        conn.commit()
        total += len(batch)

    print(f"    ✓ {total:,} rows ingested                ")
    return total


# ── Log helper ───────────────────────────────────────────────────────────────

def log_result(conn, table_name, row_count, source_file, notes=""):
    """Append a row to the ingest log table."""
    conn.execute(
        'INSERT INTO phase0b_ingest_log (table_name, row_count, source_file, timestamp, notes) '
        'VALUES (?, ?, ?, ?, ?)',
        (table_name, row_count, source_file, datetime.now(timezone.utc).isoformat(), notes),
    )
    conn.commit()


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    t0 = time.time()
    total_rows = 0

    print("=" * 72)
    print("  PHASE 0B — MULTI-SOURCE INGEST ENGINE")
    print(f"  Target DB : {DB_PATH}")
    print(f"  Started   : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 72)

    if not os.path.isfile(DB_PATH):
        print(f"ERROR: Database not found at {DB_PATH}")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH, timeout=120)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=-64000")  # 64 MB cache

    # Create ingest log table
    conn.execute("DROP TABLE IF EXISTS phase0b_ingest_log")
    conn.execute(
        "CREATE TABLE phase0b_ingest_log ("
        "  id INTEGER PRIMARY KEY AUTOINCREMENT,"
        "  table_name TEXT,"
        "  row_count INTEGER,"
        "  source_file TEXT,"
        "  timestamp TEXT,"
        "  notes TEXT"
        ")"
    )
    conn.commit()

    # ── 1. PERMAFIX R12 ─────────────────────────────────────────────────────
    print("\n" + "─" * 72)
    print("  [1/8] PERMAFIX R12")
    print("─" * 72)
    r12_dir = r"F:\PERMAFIX9R12_MEEK234_PACK"
    r12_map = {
        "contradiction_map": "permafix_r12_contradiction_map",
        "quote_db":          "permafix_r12_quote_db",
        "operating_orders":  "permafix_r12_operating_orders",
        "doc_records":       "permafix_r12_doc_records",
    }
    if os.path.isdir(r12_dir):
        found = find_files(r12_dir, list(r12_map.keys()))
        for pat, table in r12_map.items():
            if pat in found:
                n = ingest_csv(conn, table, found[pat])
                log_result(conn, table, n, found[pat])
                total_rows += n
            else:
                print(f"  ⚠ No file matching '{pat}' found — skipped")
                log_result(conn, table, 0, "", f"NOT FOUND in {r12_dir}")
    else:
        print(f"  ⚠ Directory not found: {r12_dir}")

    # ── 2. PERMAFIX R13 ─────────────────────────────────────────────────────
    print("\n" + "─" * 72)
    print("  [2/8] PERMAFIX R13")
    print("─" * 72)
    r13_dir = r"F:\PERMAFIX9R13_20260214_203353_STACK"
    r13_map = {
        "case_catalog":     "permafix_r13_case_catalog",
        "quote_db":         "permafix_r13_quote_db",
        "contradiction":    "permafix_r13_contradiction_grid",
        "authority_anchor": "permafix_r13_authority_anchors",
    }
    if os.path.isdir(r13_dir):
        # CSV/TSV files
        found = find_files(r13_dir, list(r13_map.keys()))
        for pat, table in r13_map.items():
            if pat in found:
                n = ingest_csv(conn, table, found[pat])
                log_result(conn, table, n, found[pat])
                total_rows += n
            else:
                # Try as text file (.txt, .md)
                tf = find_text_file(r13_dir, pat, extensions=(".csv", ".tsv", ".txt", ".md"))
                if tf:
                    ext = os.path.splitext(tf)[1].lower()
                    if ext in (".csv", ".tsv"):
                        n = ingest_csv(conn, table, tf)
                    else:
                        n = ingest_text_as_table(conn, table, tf)
                    log_result(conn, table, n, tf)
                    total_rows += n
                else:
                    print(f"  ⚠ No file matching '{pat}' found — skipped")
                    log_result(conn, table, 0, "", f"NOT FOUND in {r13_dir}")
    else:
        print(f"  ⚠ Directory not found: {r13_dir}")

    # ── 3. PERMAFIX R14 ─────────────────────────────────────────────────────
    print("\n" + "─" * 72)
    print("  [3/8] PERMAFIX R14")
    print("─" * 72)
    r14_dir = r"F:\PERMAFIX9R14_RENEW_20260215_005131_STACK"
    r14_map = {
        "case_chronology":  "permafix_r14_case_chronology",
        "operating_orders": "permafix_r14_operating_orders",
        "quote_db":         "permafix_r14_quote_db",
    }
    if os.path.isdir(r14_dir):
        found = find_files(r14_dir, list(r14_map.keys()))
        for pat, table in r14_map.items():
            if pat in found:
                n = ingest_csv(conn, table, found[pat])
                log_result(conn, table, n, found[pat])
                total_rows += n
            else:
                tf = find_text_file(r14_dir, pat, extensions=(".csv", ".tsv", ".txt", ".md"))
                if tf:
                    ext = os.path.splitext(tf)[1].lower()
                    if ext in (".csv", ".tsv"):
                        n = ingest_csv(conn, table, tf)
                    else:
                        n = ingest_text_as_table(conn, table, tf)
                    log_result(conn, table, n, tf)
                    total_rows += n
                else:
                    print(f"  ⚠ No file matching '{pat}' found — skipped")
                    log_result(conn, table, 0, "", f"NOT FOUND in {r14_dir}")
    else:
        print(f"  ⚠ Directory not found: {r14_dir}")

    # ── 4. MI Warchest SQLite ────────────────────────────────────────────────
    print("\n" + "─" * 72)
    print("  [4/8] MI WARCHEST SQLite")
    print("─" * 72)
    mi_dir = r"F:\MI_WARCHEST_v2_Suite"
    if os.path.isdir(mi_dir):
        sqlite_files = find_sqlite_files(mi_dir)
        if sqlite_files:
            for sf in sqlite_files:
                results = ingest_sqlite_source(conn, sf, "mi_warchest_")
                for tbl, cnt, src in results:
                    log_result(conn, tbl, cnt, src)
                    total_rows += cnt
        else:
            print(f"  ⚠ No .sqlite/.sqlite3/.db file found under {mi_dir}")
            log_result(conn, "mi_warchest_*", 0, "", f"No SQLite DB found in {mi_dir}")
    else:
        print(f"  ⚠ Directory not found: {mi_dir}")

    # ── 5. DocForge V18 SQLite ───────────────────────────────────────────────
    print("\n" + "─" * 72)
    print("  [5/8] DOCFORGE V18 SQLite")
    print("─" * 72)
    df_dir = r"I:\LITIGATIONOS_MI_APPELLATE_DOCFORGE_MEEK1234_V18_BULKGRAFT_LINKLOCK"
    if os.path.isdir(df_dir):
        sqlite_files = find_sqlite_files(df_dir)
        if sqlite_files:
            for sf in sqlite_files:
                results = ingest_sqlite_source(conn, sf, "docforge_v18_")
                for tbl, cnt, src in results:
                    log_result(conn, tbl, cnt, src)
                    total_rows += cnt
        else:
            print(f"  ⚠ No .sqlite/.sqlite3/.db file found under {df_dir}")
            log_result(conn, "docforge_v18_*", 0, "", f"No SQLite DB found in {df_dir}")
    else:
        print(f"  ⚠ Directory not found: {df_dir}")

    # ── 6. HYPERVISOR CYCLE0011 ──────────────────────────────────────────────
    print("\n" + "─" * 72)
    print("  [6/8] HYPERVISOR CYCLE0011")
    print("─" * 72)
    hv_dir = r"I:\LitigationOS_CyclePack_HYPERVISOR_CYCLE0011"
    hv_map = {
        "accusation_index":    "hypervisor_c11_accusation_index",
        "claim_cluster":       "hypervisor_c11_claim_clusters",
        "rebuttal_microbrief": "hypervisor_c11_rebuttal_microbriefs",
        "nodes":               "hypervisor_c11_nodes",
        "edges":               "hypervisor_c11_edges",
    }
    if os.path.isdir(hv_dir):
        found = find_files(hv_dir, list(hv_map.keys()))
        for pat, table in hv_map.items():
            if pat in found:
                n = ingest_csv(conn, table, found[pat])
                log_result(conn, table, n, found[pat])
                total_rows += n
            else:
                # Try text files
                tf = find_text_file(hv_dir, pat, extensions=(".csv", ".tsv", ".txt", ".md"))
                if tf:
                    ext = os.path.splitext(tf)[1].lower()
                    if ext in (".csv", ".tsv"):
                        n = ingest_csv(conn, table, tf)
                    else:
                        n = ingest_text_as_table(conn, table, tf)
                    log_result(conn, table, n, tf)
                    total_rows += n
                else:
                    print(f"  ⚠ No file matching '{pat}' found — skipped")
                    log_result(conn, table, 0, "", f"NOT FOUND in {hv_dir}")
    else:
        print(f"  ⚠ Directory not found: {hv_dir}")

    # ── 7. CYCLEPACK NO_LIMIT_FULL ───────────────────────────────────────────
    print("\n" + "─" * 72)
    print("  [7/8] CYCLEPACK NO_LIMIT_FULL")
    print("─" * 72)
    cp_dir = r"I:\CYCLEPACK_20260215T010318Z_NO_LIMIT_FULL"
    cp_files = {
        "CHRONODB.csv":              "cyclepack_chronodb",
        "STATEMENT_INDEX.csv":       "cyclepack_statement_index",
        "EXHIBIT_MATRIX.csv":        "cyclepack_exhibit_matrix",
        "PARTY_MENTION_INDEX.csv":   "cyclepack_party_mention_index",
    }
    if os.path.isdir(cp_dir):
        for fn, table in cp_files.items():
            # Search for the file (may be in subdirectory)
            fpath = None
            for root, _, files in os.walk(cp_dir):
                if fn in files:
                    fpath = os.path.join(root, fn)
                    break
            if fpath:
                n = ingest_csv(conn, table, fpath, batch_size=BATCH_SIZE)
                log_result(conn, table, n, fpath)
                total_rows += n
            else:
                print(f"  ⚠ {fn} not found — skipped")
                log_result(conn, table, 0, "", f"NOT FOUND in {cp_dir}")
    else:
        print(f"  ⚠ Directory not found: {cp_dir}")

    # ── 8. MEEK234 KNOWLEDGE_ALL.jsonl ───────────────────────────────────────
    print("\n" + "─" * 72)
    print("  [8/8] MEEK234 KNOWLEDGE_ALL.jsonl")
    print("─" * 72)
    kall_path = r"C:\Users\andre\LitigationOS\00_SYSTEM\engines\meek234_fullstack\KNOWLEDGE_ALL.jsonl"
    if os.path.isfile(kall_path):
        n = ingest_jsonl(conn, "meek234_knowledge", kall_path, batch_size=BATCH_SIZE_JSONL)
        log_result(conn, "meek234_knowledge", n, kall_path)
        total_rows += n
    else:
        print(f"  ⚠ File not found: {kall_path}")
        log_result(conn, "meek234_knowledge", 0, "", "NOT FOUND")

    # ── Summary ──────────────────────────────────────────────────────────────
    elapsed = time.time() - t0
    print("\n" + "=" * 72)
    print("  INGEST COMPLETE — SUMMARY")
    print("=" * 72)

    rows = conn.execute(
        "SELECT table_name, row_count, source_file, notes FROM phase0b_ingest_log ORDER BY id"
    ).fetchall()
    print(f"  {'Table':<45} {'Rows':>10}  Source")
    print(f"  {'─'*45} {'─'*10}  {'─'*50}")
    for tbl, cnt, src, notes in rows:
        src_short = os.path.basename(src) if src else notes or "—"
        print(f"  {tbl:<45} {cnt:>10,}  {src_short}")

    total_tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()

    print(f"\n  Total rows ingested this run : {total_rows:,}")
    print(f"  Total tables in database     : {len(total_tables)}")
    print(f"  Elapsed time                 : {elapsed:.1f}s ({elapsed/60:.1f}m)")
    print(f"  Database size                : {fmt_size(os.path.getsize(DB_PATH))}")
    print("=" * 72)

    conn.close()


if __name__ == "__main__":
    main()
