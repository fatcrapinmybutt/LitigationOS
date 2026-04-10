#!/usr/bin/env python3
"""P1C: Database Optimization — FTS5 rebuild, ANALYZE, composite indexes, WAL checkpoint.

Targets litigation_context.db for maximum query performance.
"""

import sqlite3
import time
import os
import sys

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH, timeout=120)
    conn.execute("PRAGMA busy_timeout = 120000")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA cache_size = -64000")  # 64 MB
    conn.execute("PRAGMA temp_store = MEMORY")
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.execute("PRAGMA mmap_size = 4294967296")  # 4 GB mmap
    return conn


def rebuild_fts5(conn):
    """Rebuild all FTS5 indexes for integrity and performance."""
    fts_tables = []
    for row in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND sql LIKE '%fts5%'"
    ).fetchall():
        fts_tables.append(row[0])

    # Also check for known FTS5 tables that might not match the LIKE pattern
    known_fts = ["evidence_fts", "timeline_fts", "md_sections_fts"]
    for name in known_fts:
        if name not in fts_tables:
            # Check if it exists
            exists = conn.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE name = ?", (name,)
            ).fetchone()[0]
            if exists:
                fts_tables.append(name)

    print(f"\n[P1C] FTS5 Indexes Found: {len(fts_tables)}")
    for tbl in sorted(set(fts_tables)):
        try:
            t0 = time.time()
            conn.execute(f"INSERT INTO [{tbl}]([{tbl}]) VALUES('rebuild')")
            conn.commit()
            elapsed = time.time() - t0
            row_count = conn.execute(f"SELECT COUNT(*) FROM [{tbl}]").fetchone()[0]
            print(f"  [OK] {tbl}: rebuilt ({row_count:,} rows, {elapsed:.1f}s)")
        except Exception as e:
            print(f"  [SKIP] {tbl}: {e}")

    return len(fts_tables)


def analyze_tables(conn):
    """Run ANALYZE on hot tables for query planner stats."""
    hot_tables = [
        "evidence_quotes", "authority_chains_v2", "timeline_events",
        "michigan_rules_extracted", "md_sections", "md_cross_refs",
        "master_citations", "contradiction_map", "judicial_violations",
        "impeachment_matrix", "police_reports", "berry_mcneill_intelligence",
        "file_inventory", "documents", "pages",
    ]

    print(f"\n[P1C] Running ANALYZE on {len(hot_tables)} hot tables...")
    analyzed = 0
    for tbl in hot_tables:
        try:
            exists = conn.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE name = ?", (tbl,)
            ).fetchone()[0]
            if not exists:
                print(f"  [SKIP] {tbl}: table not found")
                continue
            t0 = time.time()
            conn.execute(f"ANALYZE [{tbl}]")
            elapsed = time.time() - t0
            row_count = conn.execute(f"SELECT COUNT(*) FROM [{tbl}]").fetchone()[0]
            print(f"  [OK] {tbl}: analyzed ({row_count:,} rows, {elapsed:.1f}s)")
            analyzed += 1
        except Exception as e:
            print(f"  [SKIP] {tbl}: {e}")

    # Global ANALYZE for cross-table stats
    t0 = time.time()
    conn.execute("ANALYZE")
    conn.commit()
    elapsed = time.time() - t0
    print(f"  [OK] Global ANALYZE complete ({elapsed:.1f}s)")
    return analyzed


def create_composite_indexes(conn):
    """Add composite indexes for common multi-column WHERE patterns."""
    indexes = [
        # evidence_quotes: lane + category (common filter pattern)
        ("idx_eq_lane_cat", "evidence_quotes", "lane, category"),
        # evidence_quotes: source_file (common join/filter)
        ("idx_eq_source", "evidence_quotes", "source_file"),
        # evidence_quotes: is_duplicate (filter out dupes)
        ("idx_eq_dedup", "evidence_quotes", "is_duplicate"),
        # authority_chains_v2: primary + supporting citation
        ("idx_ac_primary", "authority_chains_v2", "primary_citation"),
        ("idx_ac_supporting", "authority_chains_v2", "supporting_citation"),
        ("idx_ac_lane", "authority_chains_v2", "lane"),
        # timeline_events: date ordering
        ("idx_te_date", "timeline_events", "event_date"),
        ("idx_te_lane", "timeline_events", "lane"),
        # michigan_rules: rule_number + rule_type
        ("idx_mr_number_type", "michigan_rules_extracted", "rule_number, rule_type"),
        # impeachment_matrix: target + impeachment_value
        ("idx_im_target", "impeachment_matrix", "target"),
        ("idx_im_value", "impeachment_matrix", "impeachment_value DESC"),
        # contradiction_map: severity
        ("idx_cm_severity", "contradiction_map", "severity"),
        # judicial_violations: category
        ("idx_jv_category", "judicial_violations", "category"),
        # md_sections: source_file
        ("idx_ms_source", "md_sections", "source_file"),
        # md_cross_refs: ref_type + ref_value
        ("idx_mcr_type_val", "md_cross_refs", "ref_type, ref_value"),
        # file_inventory: drive + extension
        ("idx_fi_drive_ext", "file_inventory", "drive_letter, extension"),
    ]

    print(f"\n[P1C] Creating {len(indexes)} composite indexes...")
    created = 0
    for idx_name, table, columns in indexes:
        try:
            # Check table exists
            exists = conn.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE name = ?", (table,)
            ).fetchone()[0]
            if not exists:
                print(f"  [SKIP] {idx_name}: table {table} not found")
                continue

            # Verify columns exist
            col_info = {r[1] for r in conn.execute(f"PRAGMA table_info([{table}])").fetchall()}
            col_list = [c.strip().split()[0] for c in columns.split(",")]
            missing = [c for c in col_list if c not in col_info]
            if missing:
                print(f"  [SKIP] {idx_name}: missing columns {missing} in {table}")
                continue

            t0 = time.time()
            conn.execute(f"CREATE INDEX IF NOT EXISTS [{idx_name}] ON [{table}]({columns})")
            conn.commit()
            elapsed = time.time() - t0
            print(f"  [OK] {idx_name} on {table}({columns}) ({elapsed:.1f}s)")
            created += 1
        except Exception as e:
            print(f"  [SKIP] {idx_name}: {e}")

    return created


def wal_checkpoint(conn):
    """Force WAL checkpoint to merge WAL into main database."""
    print("\n[P1C] WAL Checkpoint...")
    try:
        t0 = time.time()
        result = conn.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()
        elapsed = time.time() - t0
        print(f"  [OK] WAL checkpoint: status={result[0]}, "
              f"log_pages={result[1]}, checkpointed={result[2]} ({elapsed:.1f}s)")
        return True
    except Exception as e:
        print(f"  [WARN] WAL checkpoint: {e}")
        return False


def optimize_pragma(conn):
    """Run PRAGMA optimize for query planner improvements."""
    print("\n[P1C] Running PRAGMA optimize...")
    try:
        t0 = time.time()
        conn.execute("PRAGMA optimize")
        elapsed = time.time() - t0
        print(f"  [OK] PRAGMA optimize complete ({elapsed:.1f}s)")
        return True
    except Exception as e:
        print(f"  [WARN] optimize: {e}")
        return False


def db_stats(conn):
    """Report final database statistics."""
    print("\n[P1C] Database Statistics:")
    db_size = os.path.getsize(DB_PATH)
    print(f"  Database size: {db_size / 1024 / 1024:.1f} MB")

    # Count tables and indexes
    tables = conn.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
    ).fetchone()[0]
    indexes = conn.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='index'"
    ).fetchone()[0]
    print(f"  Tables: {tables}")
    print(f"  Indexes: {indexes}")

    # WAL file size
    wal_path = DB_PATH + "-wal"
    if os.path.exists(wal_path):
        wal_size = os.path.getsize(wal_path)
        print(f"  WAL file: {wal_size / 1024 / 1024:.1f} MB")
    else:
        print("  WAL file: none")

    # Key table counts
    key_tables = [
        ("evidence_quotes", None),
        ("authority_chains_v2", None),
        ("timeline_events", None),
        ("michigan_rules_extracted", None),
        ("md_sections", None),
        ("impeachment_matrix", None),
        ("file_inventory", None),
    ]
    print("\n  Key table row counts:")
    for tbl, _ in key_tables:
        try:
            count = conn.execute(f"SELECT COUNT(*) FROM [{tbl}]").fetchone()[0]
            print(f"    {tbl}: {count:,}")
        except:
            print(f"    {tbl}: (not found)")


def main():
    print("=" * 70)
    print("  P1C: DATABASE OPTIMIZATION")
    print(f"  Target: {DB_PATH}")
    print(f"  Size: {os.path.getsize(DB_PATH) / 1024 / 1024:.1f} MB")
    print("=" * 70)

    t_start = time.time()
    conn = get_conn()

    # 1. Rebuild FTS5 indexes
    fts_count = rebuild_fts5(conn)

    # 2. Create composite indexes
    idx_count = create_composite_indexes(conn)

    # 3. ANALYZE all hot tables
    analyzed = analyze_tables(conn)

    # 4. WAL checkpoint
    wal_checkpoint(conn)

    # 5. PRAGMA optimize
    optimize_pragma(conn)

    # 6. Final stats
    db_stats(conn)

    elapsed = time.time() - t_start
    print(f"\n{'=' * 70}")
    print(f"  P1C COMPLETE: {fts_count} FTS5 rebuilt, {idx_count} indexes created,")
    print(f"  {analyzed} tables analyzed in {elapsed:.1f}s")
    print(f"{'=' * 70}")

    conn.close()


if __name__ == "__main__":
    main()
