"""
Brain Sync Execute — Merge rich brain data into central litigation_context.db.

Scans all 7 brain databases in 00_SYSTEM/brains/, compares row counts and schemas,
and syncs missing rows into the central DB using INSERT OR IGNORE with column mapping.
"""
import sys
import os
import sqlite3
import time
from datetime import datetime

sys.path.insert(0, r"C:\Users\andre\LitigationOS")

CENTRAL_DB = r"C:\Users\andre\LitigationOS\litigation_context.db"
BRAINS_DIR = r"C:\Users\andre\LitigationOS\00_SYSTEM\brains"
SYNC_THRESHOLD = 0.10  # 10% more rows triggers sync

# Column mappings: brain_table → {brain_col: central_col}
# For tables with different schemas between brain and central
COLUMN_MAPS = {
    ("narrative_brain.db", "timeline_events"): {
        "event_date": "event_date",
        "event_description": "event_description",
        "actors": "actors",
        "case_lane": "lane",
        "event_type": "category",
        "source_file": "source_table",
        "source_page": "source_id",
        "significance": "severity",
        "extracted_at": "created_at",
    },
    ("entity_brain.db", "parties"): {
        "legal_name": "name",
        "role": "role",
        "party_type": "party_type",
        "bar_number": "bar_number",
        "email": "email",
        "phone": "phone",
        "address": "address",
        "case_lanes": "case_id",
    },
}


def get_columns(conn, table):
    """Get column names for a table via PRAGMA table_info."""
    try:
        info = conn.execute(f"PRAGMA table_info([{table}])").fetchall()
        return [row[1] for row in info]
    except Exception:
        return []


def get_row_count(conn, table):
    """Get row count for a table, returns 0 on error."""
    try:
        return conn.execute(f"SELECT COUNT(*) FROM [{table}]").fetchone()[0]
    except Exception:
        return 0


def table_exists(conn, table):
    """Check if a table exists."""
    r = conn.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?",
        (table,)
    ).fetchone()
    return r[0] > 0


def find_common_columns(central_cols, brain_cols, column_map=None):
    """Find columns that can be synced between brain and central."""
    if column_map:
        pairs = []
        for brain_col, central_col in column_map.items():
            if brain_col in brain_cols and central_col in central_cols:
                pairs.append((brain_col, central_col))
        return pairs
    common = [c for c in brain_cols if c in central_cols]
    return [(c, c) for c in common if c not in ("id", "rowid")]


def get_dedup_columns(table, central_cols):
    """Identify columns to use for deduplication (avoiding ID columns)."""
    dedup_priorities = {
        "timeline_events": ["event_date", "event_description"],
        "parties": ["name", "role"],
        "evidence_quotes": ["source_file", "quote_text"],
        "judicial_violations": ["violation_type", "description", "date_occurred"],
        "contradiction_map": ["source_a", "source_b", "contradiction_text"],
        "impeachment_matrix": ["category", "evidence_summary", "quote_text"],
        "authority_chains_v2": ["primary_citation", "supporting_citation", "relationship"],
        "police_reports": ["report_number", "report_date"],
    }
    if table in dedup_priorities:
        return [c for c in dedup_priorities[table] if c in central_cols]
    text_cols = [c for c in central_cols if c not in ("id", "rowid", "created_at", "updated_at")]
    return text_cols[:3] if text_cols else central_cols[:2]


def create_central_table_from_brain(central_conn, brain_conn, table, brain_cols):
    """Create a new table in central that mirrors the brain table schema."""
    create_sql = brain_conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone()
    if create_sql and create_sql[0]:
        try:
            central_conn.execute(create_sql[0])
            central_conn.commit()
            return True
        except sqlite3.OperationalError:
            return False
    return False


def sync_table_mapped(central_conn, brain_conn, table, column_pairs, brain_name):
    """Sync rows from brain to central using column mapping."""
    brain_select_cols = [p[0] for p in column_pairs]
    central_insert_cols = [p[1] for p in column_pairs]
    central_cols = get_columns(central_conn, table)
    dedup_cols = get_dedup_columns(table, central_insert_cols)

    if not dedup_cols:
        return 0

    brain_select = ", ".join(f"[{c}]" for c in brain_select_cols)
    rows = brain_conn.execute(f"SELECT {brain_select} FROM [{table}]").fetchall()

    if not rows:
        return 0

    col_index = {col: i for i, col in enumerate(brain_select_cols)}
    central_dedup_idx = {p[1]: i for i, p in enumerate(column_pairs)}

    existing = set()
    dedup_central_cols = [c for c in dedup_cols if c in central_cols]
    if dedup_central_cols:
        dedup_select = ", ".join(f"COALESCE(CAST([{c}] AS TEXT), '')" for c in dedup_central_cols)
        try:
            for r in central_conn.execute(f"SELECT {dedup_select} FROM [{table}]"):
                existing.add(tuple(str(v) for v in r))
        except Exception:
            pass

    dedup_brain_map = []
    for dc in dedup_central_cols:
        for brain_col, central_col in column_pairs:
            if central_col == dc:
                dedup_brain_map.append(brain_select_cols.index(brain_col))
                break

    insert_cols_str = ", ".join(f"[{c}]" for c in central_insert_cols)
    placeholders = ", ".join("?" for _ in central_insert_cols)
    insert_sql = f"INSERT OR IGNORE INTO [{table}] ({insert_cols_str}) VALUES ({placeholders})"

    batch = []
    synced = 0
    for row in rows:
        if dedup_brain_map:
            key = tuple(str(row[i]) if row[i] is not None else "" for i in dedup_brain_map)
            if key in existing:
                continue
            existing.add(key)

        values = []
        for brain_col in brain_select_cols:
            idx = col_index[brain_col]
            values.append(row[idx])
        batch.append(tuple(values))

        if len(batch) >= 5000:
            central_conn.executemany(insert_sql, batch)
            synced += len(batch)
            batch = []

    if batch:
        central_conn.executemany(insert_sql, batch)
        synced += len(batch)

    central_conn.commit()
    return synced


def sync_new_table(central_conn, brain_conn, table):
    """Sync an entirely new table from brain to central."""
    brain_cols = get_columns(brain_conn, table)
    if not brain_cols:
        return 0

    if table.endswith("_fts") or table.endswith("_fts_config") or \
       table.endswith("_fts_data") or table.endswith("_fts_docsize") or \
       table.endswith("_fts_idx") or table == "sqlite_sequence":
        return 0

    created = create_central_table_from_brain(central_conn, brain_conn, table, brain_cols)
    if not created:
        return 0

    col_str = ", ".join(f"[{c}]" for c in brain_cols)
    placeholders = ", ".join("?" for _ in brain_cols)
    insert_sql = f"INSERT OR IGNORE INTO [{table}] ({col_str}) VALUES ({placeholders})"

    rows = brain_conn.execute(f"SELECT {col_str} FROM [{table}]").fetchall()
    if not rows:
        return 0

    for i in range(0, len(rows), 5000):
        central_conn.executemany(insert_sql, rows[i:i+5000])
    central_conn.commit()
    return len(rows)


def main():
    start_time = time.time()
    print("=" * 90)
    print(f"  BRAIN SYNC EXECUTE — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 90)

    central_conn = sqlite3.connect(CENTRAL_DB)
    central_conn.execute("PRAGMA busy_timeout=60000")
    central_conn.execute("PRAGMA journal_mode=WAL")
    central_conn.execute("PRAGMA cache_size=-32000")
    central_conn.execute("PRAGMA temp_store=MEMORY")
    central_conn.execute("PRAGMA synchronous=NORMAL")

    central_tables = {}
    for row in central_conn.execute("SELECT name FROM sqlite_master WHERE type='table'"):
        central_tables[row[0]] = get_row_count(central_conn, row[0])

    total_synced = 0
    total_new_tables = 0
    report_rows = []

    brain_files = sorted(f for f in os.listdir(BRAINS_DIR) if f.endswith(".db"))

    for brain_file in brain_files:
        brain_path = os.path.join(BRAINS_DIR, brain_file)
        print(f"\n{'-' * 90}")
        print(f"  Processing: {brain_file} ({os.path.getsize(brain_path)/1024/1024:.1f} MB)")
        print(f"{'-' * 90}")

        brain_conn = sqlite3.connect(brain_path)
        brain_conn.execute("PRAGMA busy_timeout=60000")

        brain_tables = {}
        for row in brain_conn.execute("SELECT name FROM sqlite_master WHERE type='table'"):
            brain_tables[row[0]] = get_row_count(brain_conn, row[0])

        for table, brain_count in sorted(brain_tables.items()):
            if table.endswith("_fts") or table.endswith("_fts_config") or \
               table.endswith("_fts_data") or table.endswith("_fts_docsize") or \
               table.endswith("_fts_idx") or table == "sqlite_sequence" or \
               table == "brain_meta":
                continue

            if brain_count == 0:
                continue

            central_before = central_tables.get(table, 0)
            map_key = (brain_file, table)
            column_map = COLUMN_MAPS.get(map_key)

            if table not in central_tables:
                print(f"  [NEW] TABLE: {table} ({brain_count} rows) -> creating in central...")
                synced = sync_new_table(central_conn, brain_conn, table)
                if synced > 0:
                    total_new_tables += 1
                    total_synced += synced
                    central_after = get_row_count(central_conn, table)
                    central_tables[table] = central_after
                    report_rows.append((brain_file, table, 0, brain_count, synced, central_after, "NEW"))
                    print(f"    [OK] Created + synced {synced} rows")
                else:
                    print(f"    [WARN] Could not create table")
                continue

            if brain_count <= central_before:
                continue

            delta_pct = (brain_count - central_before) / max(central_before, 1)

            if column_map or delta_pct >= SYNC_THRESHOLD:
                brain_cols = get_columns(brain_conn, table)
                central_cols = get_columns(central_conn, table)

                column_pairs = find_common_columns(central_cols, brain_cols, column_map)

                if not column_pairs:
                    print(f"  [WARN] {table}: No compatible columns found, skipping")
                    continue

                print(f"  [SYNC] {table} (central={central_before}, brain={brain_count}, "
                      f"delta={delta_pct*100:.1f}%)")
                print(f"    Mapping: {[(b,c) for b,c in column_pairs]}")

                synced = sync_table_mapped(central_conn, brain_conn, table, column_pairs, brain_file)
                central_after = get_row_count(central_conn, table)
                central_tables[table] = central_after
                total_synced += synced
                status = "SYNCED" if synced > 0 else "NO_NEW"
                report_rows.append((brain_file, table, central_before, brain_count,
                                    synced, central_after, status))
                print(f"    [OK] Synced {synced} new rows (central now: {central_after})")

        brain_conn.close()

    elapsed = time.time() - start_time

    print("\n" + "=" * 90)
    print("  COMPREHENSIVE SYNC REPORT")
    print("=" * 90)
    print(f"\n{'Brain':<30} {'Table':<30} {'Before':>8} {'Brain':>8} {'Synced':>8} {'After':>8} {'Status':<8}")
    print("-" * 110)
    for row in report_rows:
        print(f"{row[0]:<30} {row[1]:<30} {row[2]:>8} {row[3]:>8} {row[4]:>8} {row[5]:>8} {row[6]:<8}")
    print("-" * 110)
    print(f"{'TOTALS':<60} {'':<8} {'':<8} {total_synced:>8}")
    print(f"\nNew tables created: {total_new_tables}")
    print(f"Total rows synced: {total_synced}")
    print(f"Elapsed time: {elapsed:.1f}s")

    # Verify key tables
    print("\n" + "=" * 90)
    print("  POST-SYNC VERIFICATION")
    print("=" * 90)
    verify_tables = [
        "timeline_events", "parties", "evidence_quotes", "judicial_violations",
        "impeachment_matrix", "contradiction_map", "authority_chains_v2",
        "court_orders", "testimony", "document_extractions",
        "authority_citations", "statutes", "case_law", "legal_arguments",
        "chat_intelligence", "contradictions", "causes_of_action",
        "strategy_analysis", "impeachment_analysis",
    ]
    for t in verify_tables:
        if table_exists(central_conn, t):
            cnt = get_row_count(central_conn, t)
            print(f"  {t}: {cnt:,} rows")

    central_conn.close()
    print(f"\n{'=' * 90}")
    print(f"  BRAIN SYNC COMPLETE — {total_synced:,} rows synced across {len(report_rows)} operations")
    print(f"{'=' * 90}")


if __name__ == "__main__":
    main()
