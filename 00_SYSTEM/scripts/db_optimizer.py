#!/usr/bin/env python3
"""
LitigationOS Database Optimizer — Schema Health, Index Coverage, FTS5, and Bloat Analysis.

Targets: litigation_context.db (~10 GB, 700+ tables)
Safety:  Read-only analysis + CREATE INDEX IF NOT EXISTS only. Never drops/alters tables.
Tier:    Standard (PRAGMA busy_timeout=60s, cache=32 MB, WAL mode)

Usage:
    python db_optimizer.py                          # default DB path
    python db_optimizer.py --db /path/to/db.sqlite  # custom DB path
    python db_optimizer.py --skip-indexes            # audit only, no index creation
    python db_optimizer.py --json                    # JSON output
"""
import sys
import os
import json
import time
import argparse
from pathlib import Path
from datetime import datetime

# UTF-8 stdout (Windows safety)
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

import sqlite3

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DEFAULT_DB = Path(__file__).resolve().parent.parent.parent / "litigation_context.db"

REQUIRED_PRAGMAS = {
    "busy_timeout": "60000",
    "journal_mode": "wal",
    "cache_size": "-32000",
    "temp_store": "2",       # 2 = MEMORY
    "synchronous": "1",      # 1 = NORMAL
}

# Composite indexes to create — each tuple: (index_name, table, columns)
# Column names verified against actual DB schema (2026-03-09)
COMPOSITE_INDEXES = [
    # --- Hot query pattern indexes (from copilot-instructions.md, corrected to real columns) ---
    ("idx_evidence_quotes_category_docid",      "evidence_quotes",       "evidence_category, document_id"),
    ("idx_evidence_quotes_source_type",         "evidence_quotes",       "source_type, evidence_category"),
    ("idx_authority_chains_vehicle_complete",    "authority_chains",      "filing_vehicle, chain_complete"),
    ("idx_authority_chains_type",               "authority_chains",      "authority_type, filing_vehicle"),
    ("idx_deadlines_case_status",               "deadlines",             "case_id, status"),
    ("idx_deadlines_due_status",                "deadlines",             "due_date_iso, status"),
    ("idx_documents_category",                  "documents",             "evidence_category"),
    ("idx_claims_classification_status",        "claims",                "classification, status"),
    ("idx_claims_actor",                        "claims",                "actor, classification"),
    ("idx_docket_events_case_date",             "docket_events",         "case_id, event_date_iso"),
    ("idx_docket_events_type",                  "docket_events",         "event_type, case_id"),
    ("idx_court_rules_chapter",                 "court_rules",           "chapter, rule"),
    # --- Large table indexes (tables > 100K rows without coverage) ---
    ("idx_master_citations_type",               "master_citations",      "cite_type, source_file"),
    ("idx_drive_manifest_ext_drive",            "drive_manifest",        "extension, drive"),
    ("idx_drive_manifest_category",             "drive_manifest",        "category, drive"),
    ("idx_omega_fs_ext_drive",                  "omega_filesystem_map",  "extension, drive"),
    ("idx_omega_fs_filetype",                   "omega_filesystem_map",  "file_type, drive"),
    ("idx_file_inventory_ext_class",            "file_inventory",        "extension, classification"),
    ("idx_file_inventory_ext_dup",              "file_inventory_external", "extension, drive"),
    ("idx_pages_docid",                         "pages",                 "document_id, page_number"),
    ("idx_auth_edges_source",                   "auth_authority_edges",  "source_id, edge_type"),
    ("idx_auth_edges_target",                   "auth_authority_edges",  "target_id, edge_type"),
    ("idx_evidence_dedup_canonical",            "evidence_dedup_map",    "canonical_id, is_canonical"),
    ("idx_master_file_index_ext_drive",         "master_file_index",     "extension, drive"),
    ("idx_master_file_index_category",          "master_file_index",     "category, is_duplicate"),
    ("idx_evidence_file_index_lane",            "evidence_file_index",   "lane, category"),
    ("idx_evidence_file_index_type",            "evidence_file_index",   "file_type, relevance_lane"),
    ("idx_chatgpt_convos_title",                "chatgpt_conversations", "conversation_id, message_role"),
    ("idx_chatgpt_intel_relevant",              "chatgpt_litigation_intel", "litigation_relevant, conversation_id"),
    ("idx_d_drive_catalog_ext",                 "d_drive_catalog",       "extension, category"),
    ("idx_scan_inventory_ext",                  "scan_inventory",        "file_ext, doc_type"),
    ("idx_file_atoms_lane_type",                "file_atoms",            "lane, atom_type"),
    ("idx_case_intel_hub_lane",                 "case_intelligence_hub", "lane, entity_type"),
    ("idx_extracted_harms_category",            "extracted_harms",       "category, severity"),
    ("idx_prosecution_timeline_date",           "prosecution_timeline",  "event_date, event_type"),
    ("idx_prosecution_timeline_type",           "prosecution_timeline",  "event_type, severity"),
]

BLOAT_THRESHOLD_PCT = 10  # recommend VACUUM if freelist > this % of total pages


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def connect(db_path: Path) -> sqlite3.Connection:
    """Open a connection with mandatory LitigationOS PRAGMAs."""
    conn = sqlite3.connect(str(db_path), timeout=120)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 60000")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA cache_size = -32000")
    conn.execute("PRAGMA temp_store = MEMORY")
    conn.execute("PRAGMA synchronous = NORMAL")
    return conn


def table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type IN ('table','view') AND name = ?",
        (table,),
    ).fetchone()
    return row is not None


def table_has_columns(conn: sqlite3.Connection, table: str, columns: list[str]) -> bool:
    """Check that *all* columns exist on the table."""
    try:
        info = conn.execute(f"PRAGMA table_info([{table}])").fetchall()
    except Exception:
        return False
    existing = {row["name"] for row in info}
    return all(c.strip() in existing for c in columns)


def safe_count(conn: sqlite3.Connection, table: str) -> int:
    """Return row count, handling virtual/corrupt tables gracefully."""
    try:
        row = conn.execute(f"SELECT COUNT(*) AS n FROM [{table}]").fetchone()
        return row["n"] if row else 0
    except Exception:
        return -1


def separator(char: str = "=", width: int = 76) -> str:
    return char * width


# ---------------------------------------------------------------------------
# 1. Schema Health Audit
# ---------------------------------------------------------------------------
def schema_health_audit(conn: sqlite3.Connection) -> dict:
    """Count tables, views, indexes, triggers; find hot tables & missing indexes."""
    master = conn.execute(
        "SELECT type, name, tbl_name, sql FROM sqlite_master ORDER BY type, name"
    ).fetchall()

    tables = [r for r in master if r["type"] == "table" and not r["name"].startswith("sqlite_")]
    views = [r for r in master if r["type"] == "view"]
    indexes = [r for r in master if r["type"] == "index" and not r["name"].startswith("sqlite_")]
    triggers = [r for r in master if r["type"] == "trigger"]

    # Identify tables (non-FTS shadow tables)
    real_tables = [t for t in tables if not any(
        t["name"].endswith(sfx) for sfx in ("_content", "_segments", "_segdir", "_stat",
                                              "_data", "_idx", "_config", "_docsize")
    )]

    # Row counts (batched for speed — sample first 300, then full for hot)
    row_counts: dict[str, int] = {}
    for t in real_tables:
        row_counts[t["name"]] = safe_count(conn, t["name"])

    hot_tables = {k: v for k, v in row_counts.items() if v > 100_000}

    # Tables with no user-created indexes
    indexed_tables = {r["tbl_name"] for r in indexes}
    tables_no_index = [t["name"] for t in real_tables if t["name"] not in indexed_tables]

    # Index coverage ratio
    total_real = len(real_tables)
    covered = len(indexed_tables & {t["name"] for t in real_tables})
    coverage_ratio = covered / total_real if total_real else 0

    return {
        "total_tables": len(tables),
        "total_views": len(views),
        "total_indexes": len(indexes),
        "total_triggers": len(triggers),
        "real_tables": len(real_tables),
        "row_counts": row_counts,
        "hot_tables": hot_tables,
        "tables_no_index": tables_no_index,
        "index_coverage_ratio": coverage_ratio,
    }


# ---------------------------------------------------------------------------
# 2. PRAGMA Settings Check
# ---------------------------------------------------------------------------
def check_pragmas(conn: sqlite3.Connection) -> dict:
    results = {}
    for pragma, expected in REQUIRED_PRAGMAS.items():
        try:
            row = conn.execute(f"PRAGMA {pragma}").fetchone()
            actual = str(row[0]).lower() if row else "N/A"
            results[pragma] = {"expected": expected, "actual": actual, "ok": actual == expected}
        except Exception as e:
            results[pragma] = {"expected": expected, "actual": str(e), "ok": False}
    return results


# ---------------------------------------------------------------------------
# 3. Add Missing Composite Indexes
# ---------------------------------------------------------------------------
def add_composite_indexes(conn: sqlite3.Connection, dry_run: bool = False) -> list[dict]:
    results = []
    for idx_name, table, cols in COMPOSITE_INDEXES:
        col_list = [c.strip() for c in cols.split(",")]
        entry = {"index": idx_name, "table": table, "columns": cols}

        if not table_exists(conn, table):
            entry["status"] = "SKIPPED — table does not exist"
            results.append(entry)
            continue

        if not table_has_columns(conn, table, col_list):
            entry["status"] = f"SKIPPED — missing column(s) in {table}"
            results.append(entry)
            continue

        # Check if index already exists
        existing = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='index' AND name=?", (idx_name,)
        ).fetchone()

        if existing:
            entry["status"] = "EXISTS — no action needed"
            results.append(entry)
            continue

        if dry_run:
            entry["status"] = "WOULD CREATE (dry run)"
            results.append(entry)
            continue

        try:
            sql = f"CREATE INDEX IF NOT EXISTS [{idx_name}] ON [{table}]({cols})"
            conn.execute(sql)
            conn.commit()
            entry["status"] = "CREATED"
        except Exception as e:
            entry["status"] = f"ERROR — {e}"
        results.append(entry)

    return results


# ---------------------------------------------------------------------------
# 4. FTS5 Health Check
# ---------------------------------------------------------------------------
def fts5_health_check(conn: sqlite3.Connection) -> list[dict]:
    fts_tables = conn.execute(
        "SELECT name, sql FROM sqlite_master WHERE type='table' AND sql LIKE '%fts5%'"
    ).fetchall()

    results = []
    for t in fts_tables:
        name = t["name"]
        count = safe_count(conn, name)
        results.append({"table": name, "row_count": count, "populated": count > 0})

    # Also check for search_index specifically (may be created via FTS5)
    if not any(r["table"] == "search_index" for r in results):
        if table_exists(conn, "search_index"):
            count = safe_count(conn, "search_index")
            results.append({
                "table": "search_index",
                "row_count": count,
                "populated": count > 0,
                "note": "found but not FTS5-created in sqlite_master",
            })

    return results


# ---------------------------------------------------------------------------
# 5. Bloat Analysis
# ---------------------------------------------------------------------------
def bloat_analysis(conn: sqlite3.Connection) -> dict:
    page_count = conn.execute("PRAGMA page_count").fetchone()[0]
    page_size = conn.execute("PRAGMA page_size").fetchone()[0]
    freelist = conn.execute("PRAGMA freelist_count").fetchone()[0]

    total_bytes = page_count * page_size
    free_bytes = freelist * page_size
    bloat_pct = (freelist / page_count * 100) if page_count else 0

    return {
        "page_count": page_count,
        "page_size": page_size,
        "total_bytes": total_bytes,
        "total_mb": round(total_bytes / (1024 * 1024), 2),
        "total_gb": round(total_bytes / (1024 * 1024 * 1024), 3),
        "freelist_pages": freelist,
        "free_mb": round(free_bytes / (1024 * 1024), 2),
        "bloat_pct": round(bloat_pct, 2),
        "vacuum_recommended": bloat_pct > BLOAT_THRESHOLD_PCT,
    }


# ---------------------------------------------------------------------------
# Report Printer
# ---------------------------------------------------------------------------
def print_report(health: dict, pragmas: dict, indexes: list, fts: list, bloat: dict):
    print(f"\n{separator('=')}")
    print(f"  LitigationOS Database Optimizer Report")
    print(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(separator("="))

    # --- Schema Summary ---
    print(f"\n{'[1] SCHEMA HEALTH AUDIT':^76}")
    print(separator("-"))
    print(f"  Total tables:     {health['total_tables']:>8,}")
    print(f"  Real tables:      {health['real_tables']:>8,}")
    print(f"  Views:            {health['total_views']:>8,}")
    print(f"  Indexes:          {health['total_indexes']:>8,}")
    print(f"  Triggers:         {health['total_triggers']:>8,}")
    print(f"  Index coverage:   {health['index_coverage_ratio']:>7.1%}")

    # Hot tables
    if health["hot_tables"]:
        print(f"\n  Hot Tables (>100K rows):")
        for name, count in sorted(health["hot_tables"].items(), key=lambda x: -x[1]):
            print(f"    {name:<50} {count:>12,} rows")
    else:
        print(f"\n  No tables exceed 100K rows.")

    # Top 20 by row count
    sorted_tables = sorted(health["row_counts"].items(), key=lambda x: -x[1])[:20]
    if sorted_tables:
        print(f"\n  Top 20 Tables by Row Count:")
        for i, (name, count) in enumerate(sorted_tables, 1):
            print(f"    {i:>3}. {name:<48} {count:>12,}")

    # Tables missing indexes
    missing = health["tables_no_index"]
    if missing:
        print(f"\n  Tables with NO indexes ({len(missing)} total):")
        for name in sorted(missing)[:40]:
            print(f"    - {name}")
        if len(missing) > 40:
            print(f"    ... and {len(missing) - 40} more")
    else:
        print(f"\n  All tables have at least one index.")

    # --- PRAGMA Settings ---
    print(f"\n{'[2] PRAGMA SETTINGS':^76}")
    print(separator("-"))
    for pragma, info in pragmas.items():
        status = "OK" if info["ok"] else "MISMATCH"
        print(f"  {pragma:<20} expected={info['expected']:<10} actual={info['actual']:<10} [{status}]")

    # --- Composite Indexes ---
    print(f"\n{'[3] COMPOSITE INDEX OPERATIONS':^76}")
    print(separator("-"))
    for entry in indexes:
        print(f"  {entry['index']}")
        print(f"    Table:   {entry['table']}({entry['columns']})")
        print(f"    Status:  {entry['status']}")

    # --- FTS5 Health ---
    print(f"\n{'[4] FTS5 VIRTUAL TABLE HEALTH':^76}")
    print(separator("-"))
    if fts:
        for entry in fts:
            status = "POPULATED" if entry["populated"] else "EMPTY"
            note = f"  ({entry.get('note', '')})" if entry.get("note") else ""
            print(f"  {entry['table']:<50} {entry['row_count']:>10,} rows  [{status}]{note}")
    else:
        print("  No FTS5 tables found.")

    # --- Bloat Analysis ---
    print(f"\n{'[5] BLOAT ANALYSIS':^76}")
    print(separator("-"))
    print(f"  Page size:        {bloat['page_size']:>12,} bytes")
    print(f"  Total pages:      {bloat['page_count']:>12,}")
    print(f"  Database size:    {bloat['total_gb']:>11.3f} GB  ({bloat['total_mb']:,.1f} MB)")
    print(f"  Freelist pages:   {bloat['freelist_pages']:>12,}")
    print(f"  Freelist size:    {bloat['free_mb']:>11.2f} MB")
    print(f"  Bloat percentage: {bloat['bloat_pct']:>11.2f}%")

    if bloat["vacuum_recommended"]:
        print(f"\n  *** VACUUM RECOMMENDED ***")
        print(f"  Freelist exceeds {BLOAT_THRESHOLD_PCT}% of total pages.")
        print(f"  Run:  VACUUM;  (WARNING: requires ~{bloat['total_gb']:.1f} GB free disk space)")
        print(f"  Alternative:  PRAGMA incremental_vacuum(N);  for partial reclaim")
    else:
        print(f"\n  Bloat is within acceptable limits. No VACUUM needed.")

    print(f"\n{separator('=')}")
    print(f"  Report complete.")
    print(separator("="))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="LitigationOS Database Optimizer")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help="Path to SQLite database")
    parser.add_argument("--skip-indexes", action="store_true", help="Skip index creation (audit only)")
    parser.add_argument("--json", action="store_true", help="Output JSON instead of text")
    args = parser.parse_args()

    db_path = args.db.resolve()
    if not db_path.exists():
        print(f"ERROR: Database not found: {db_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Connecting to: {db_path}")
    print(f"File size on disk: {db_path.stat().st_size / (1024**3):.3f} GB")

    start = time.time()
    conn = connect(db_path)

    try:
        print("Running schema health audit...")
        health = schema_health_audit(conn)

        print("Checking PRAGMA settings...")
        pragmas = check_pragmas(conn)

        print("Managing composite indexes...")
        indexes = add_composite_indexes(conn, dry_run=args.skip_indexes)

        print("Checking FTS5 tables...")
        fts = fts5_health_check(conn)

        print("Analyzing bloat...")
        bloat = bloat_analysis(conn)

        elapsed = round(time.time() - start, 2)

        if args.json:
            report = {
                "db_path": str(db_path),
                "elapsed_seconds": elapsed,
                "schema_health": {
                    "total_tables": health["total_tables"],
                    "real_tables": health["real_tables"],
                    "total_views": health["total_views"],
                    "total_indexes": health["total_indexes"],
                    "total_triggers": health["total_triggers"],
                    "index_coverage_ratio": health["index_coverage_ratio"],
                    "hot_tables": health["hot_tables"],
                    "tables_no_index_count": len(health["tables_no_index"]),
                    "top20_by_rows": dict(
                        sorted(health["row_counts"].items(), key=lambda x: -x[1])[:20]
                    ),
                },
                "pragmas": pragmas,
                "composite_indexes": indexes,
                "fts5_tables": fts,
                "bloat": bloat,
            }
            print(json.dumps(report, indent=2, default=str))
        else:
            print_report(health, pragmas, indexes, fts, bloat)
            print(f"\n  Elapsed: {elapsed}s\n")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
