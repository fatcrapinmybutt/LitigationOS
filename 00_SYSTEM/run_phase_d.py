"""
Phase D: DB Path Migration — Standalone executor.
Migrates ~62K paths in litigation_context.db from D:\, F:\, G:\, I:\ → J:\CONSOLIDATED\X_DRIVE\
Prerequisite: Phase C must have copied files successfully.

Safety: Creates backup, verifies Phase C completion, gates on copy count > 0.
Rollback: revert_db_paths.py can undo this if needed.
"""

import sqlite3
import shutil
import os
import time
from datetime import datetime
from pathlib import Path

# ── Config ──────────────────────────────────────────────────────────────
LITIGATION_DB = r"C:\Users\andre\LitigationOS\litigation_context.db"
STATE_DB = r"D:\LitigationOS_tmp\consolidation_state.db"
BACKUP_DIR = r"J:\CONSOLIDATED\BACKUPS"
LOG_FILE = r"D:\LitigationOS_tmp\phase_d_execution.log"

DRIVE_MAP = {
    "D:\\": "J:\\CONSOLIDATED\\D_DRIVE\\",
    "F:\\": "J:\\CONSOLIDATED\\F_DRIVE\\",
    "G:\\": "J:\\CONSOLIDATED\\G_DRIVE\\",
    "I:\\": "J:\\CONSOLIDATED\\I_DRIVE\\",
}

# Tables and columns to migrate
MIGRATION_TARGETS = [
    ("evidence_quotes", "source_file"),
    ("documents", "file_path"),
    ("impeachment_matrix", "source_file"),
    ("file_inventory", "file_path"),
    ("authority_chains_v2", "source_document"),
]


def log(msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def check_phase_c_completion() -> dict:
    """Verify Phase C ran and copied files. Returns stats."""
    conn = sqlite3.connect(f"file:{STATE_DB}?mode=ro", uri=True)
    conn.execute("PRAGMA busy_timeout=60000")

    stats = {}
    for status in ["CANONICAL", "COPIED", "VERIFIED", "DUPLICATE_SKIP", "EMPTY_SKIP", "COPY_ERROR", "SOURCE_MISSING"]:
        count = conn.execute(
            "SELECT COUNT(*) FROM file_inventory WHERE copy_status = ?", (status,)
        ).fetchone()[0]
        stats[status] = count

    null_count = conn.execute(
        "SELECT COUNT(*) FROM file_inventory WHERE copy_status IS NULL"
    ).fetchone()[0]
    stats["NULL"] = null_count

    conn.close()
    return stats


def verify_table_exists(conn: sqlite3.Connection, table: str) -> bool:
    """Check if table exists in DB."""
    row = conn.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?",
        (table,)
    ).fetchone()
    return row[0] > 0


def verify_column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    """Check if column exists in table."""
    cols = {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}
    return column in cols


def count_paths_to_migrate(conn: sqlite3.Connection, table: str, column: str) -> dict:
    """Count paths per drive prefix that need migration."""
    counts = {}
    for old_prefix in DRIVE_MAP:
        try:
            row = conn.execute(
                f"SELECT COUNT(*) FROM [{table}] WHERE [{column}] LIKE ?",
                (old_prefix + "%",)
            ).fetchone()
            counts[old_prefix] = row[0]
        except sqlite3.OperationalError:
            counts[old_prefix] = -1
    return counts


def create_backup() -> str:
    """Create timestamped backup of litigation_context.db."""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKUP_DIR, f"litigation_context_pre_phase_d_{ts}.db")

    if os.path.exists(backup_path):
        log(f"  Backup already exists: {backup_path}")
        return backup_path

    log(f"  Creating backup: {backup_path}")
    log(f"  Source size: {os.path.getsize(LITIGATION_DB) / (1024**3):.2f} GB")

    # Use SQLite backup API for consistency (avoids file lock issues)
    src = sqlite3.connect(LITIGATION_DB)
    src.execute("PRAGMA busy_timeout=60000")
    dst = sqlite3.connect(backup_path)
    src.backup(dst)
    dst.close()
    src.close()

    backup_size = os.path.getsize(backup_path) / (1024**3)
    log(f"  Backup complete: {backup_size:.2f} GB")
    return backup_path


def migrate_paths(conn: sqlite3.Connection, table: str, column: str) -> dict:
    """Migrate paths in one table/column. Returns per-drive update counts."""
    results = {}
    for old_prefix, new_prefix in DRIVE_MAP.items():
        drive_letter = old_prefix[0]
        try:
            # Count before
            before = conn.execute(
                f"SELECT COUNT(*) FROM [{table}] WHERE [{column}] LIKE ?",
                (old_prefix + "%",)
            ).fetchone()[0]

            if before == 0:
                results[drive_letter] = 0
                continue

            # Execute REPLACE
            conn.execute(
                f"UPDATE [{table}] SET [{column}] = REPLACE([{column}], ?, ?) "
                f"WHERE [{column}] LIKE ?",
                (old_prefix, new_prefix, old_prefix + "%")
            )

            # Count after (should be 0 for this prefix now)
            after = conn.execute(
                f"SELECT COUNT(*) FROM [{table}] WHERE [{column}] LIKE ?",
                (old_prefix + "%",)
            ).fetchone()[0]

            updated = before - after
            results[drive_letter] = updated

            if after > 0:
                log(f"    ⚠️  {after} rows still have {old_prefix} prefix after migration!")

        except sqlite3.OperationalError as e:
            log(f"    ❌ Error migrating {drive_letter}: in {table}.{column}: {e}")
            results[drive_letter] = -1

    return results


def rebuild_fts5_indexes(conn: sqlite3.Connection):
    """Rebuild FTS5 indexes that reference migrated paths."""
    fts_tables = [
        ("evidence_fts", "evidence_quotes"),
        ("timeline_fts", "timeline_events"),
        ("md_sections_fts", "md_sections"),
    ]

    for fts_name, _source in fts_tables:
        # Check if FTS table exists
        exists = conn.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?",
            (fts_name,)
        ).fetchone()[0]

        if not exists:
            log(f"  ⚠️  FTS table {fts_name} not found — skipping")
            continue

        log(f"  Rebuilding {fts_name}...")
        try:
            conn.execute(f"INSERT INTO [{fts_name}]([{fts_name}]) VALUES('rebuild')")
            log(f"  ✅ {fts_name} rebuilt")
        except sqlite3.OperationalError as e:
            log(f"  ❌ FTS rebuild failed for {fts_name}: {e}")


def verify_migration(conn: sqlite3.Connection) -> dict:
    """Post-migration verification: count remaining old-drive references."""
    remaining = {}
    for table, column in MIGRATION_TARGETS:
        if not verify_table_exists(conn, table):
            continue
        if not verify_column_exists(conn, table, column):
            continue

        counts = count_paths_to_migrate(conn, table, column)
        total = sum(v for v in counts.values() if v > 0)
        if total > 0:
            remaining[f"{table}.{column}"] = counts

    return remaining


def main():
    start = time.time()
    log("=" * 70)
    log("PHASE D: DB PATH MIGRATION")
    log(f"Started: {datetime.now().isoformat()}")
    log("=" * 70)

    # ── Step 1: Verify Phase C completion ──
    log("\n[Step 1] Checking Phase C completion...")
    stats = check_phase_c_completion()
    log(f"  Phase C stats:")
    for k, v in sorted(stats.items()):
        if v > 0:
            log(f"    {k}: {v:,}")

    copied = stats.get("COPIED", 0) + stats.get("VERIFIED", 0)
    canonical_remaining = stats.get("CANONICAL", 0)
    errors = stats.get("COPY_ERROR", 0) + stats.get("SOURCE_MISSING", 0)

    if copied == 0:
        log("\n❌ ABORT: Phase C has not copied any files yet!")
        log("   Run Phase C first, then re-run Phase D.")
        return False

    if canonical_remaining > 0:
        log(f"\n⚠️  WARNING: {canonical_remaining:,} files still marked CANONICAL (not yet copied)")
        log("   Phase C may still be running. Proceeding with caution.")
        log("   Only paths for COPIED/VERIFIED files will resolve correctly.")

    if errors > 0:
        log(f"\n⚠️  WARNING: {errors:,} copy errors detected.")
        log("   These paths will be migrated but files won't exist at target.")

    log(f"\n  Total copied+verified: {copied:,}")
    log(f"  Proceeding with DB path migration.")

    # ── Step 2: Create backup ──
    log("\n[Step 2] Creating backup...")
    backup_path = create_backup()
    log(f"  Backup: {backup_path}")

    # ── Step 3: Pre-migration audit ──
    log("\n[Step 3] Pre-migration path audit...")
    conn = sqlite3.connect(LITIGATION_DB)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")

    total_to_migrate = 0
    for table, column in MIGRATION_TARGETS:
        if not verify_table_exists(conn, table):
            log(f"  ⚠️  Table {table} not found — skipping")
            continue
        if not verify_column_exists(conn, table, column):
            log(f"  ⚠️  Column {table}.{column} not found — skipping")
            continue

        counts = count_paths_to_migrate(conn, table, column)
        subtotal = sum(v for v in counts.values() if v > 0)
        total_to_migrate += subtotal
        if subtotal > 0:
            detail = ", ".join(f"{k[0]}:={v}" for k, v in counts.items() if v > 0)
            log(f"  {table}.{column}: {subtotal:,} paths ({detail})")
        else:
            log(f"  {table}.{column}: 0 paths (already migrated or none)")

    log(f"\n  TOTAL paths to migrate: {total_to_migrate:,}")

    if total_to_migrate == 0:
        log("\n✅ No paths to migrate — all already at J:\\CONSOLIDATED\\ or no external refs.")
        conn.close()
        return True

    # ── Step 4: Execute migration ──
    log("\n[Step 4] Executing path migration...")
    grand_total = 0

    for table, column in MIGRATION_TARGETS:
        if not verify_table_exists(conn, table):
            continue
        if not verify_column_exists(conn, table, column):
            continue

        log(f"\n  Migrating {table}.{column}...")
        results = migrate_paths(conn, table, column)
        subtotal = sum(v for v in results.values() if v > 0)
        grand_total += subtotal

        for drive, count in sorted(results.items()):
            if count > 0:
                log(f"    {drive}:\\ → J:\\CONSOLIDATED\\{drive}_DRIVE\\: {count:,} rows")
            elif count < 0:
                log(f"    {drive}:\\: ERROR")

    conn.commit()
    log(f"\n  TOTAL rows updated: {grand_total:,}")

    # ── Step 5: Rebuild FTS5 ──
    log("\n[Step 5] Rebuilding FTS5 indexes...")
    rebuild_fts5_indexes(conn)
    conn.commit()

    # ── Step 6: Post-migration verification ──
    log("\n[Step 6] Post-migration verification...")
    remaining = verify_migration(conn)

    if not remaining:
        log("  ✅ ZERO old-drive references remaining — migration complete!")
    else:
        log("  ⚠️  Remaining old-drive references:")
        for key, counts in remaining.items():
            detail = ", ".join(f"{k}={v}" for k, v in counts.items() if v > 0)
            log(f"    {key}: {detail}")

    # ── Step 7: Verify J:\CONSOLIDATED\ references exist ──
    log("\n[Step 7] Spot-checking new paths...")
    sample = conn.execute(
        "SELECT source_file FROM evidence_quotes "
        "WHERE source_file LIKE 'J:\\CONSOLIDATED\\%' "
        "ORDER BY RANDOM() LIMIT 10"
    ).fetchall()

    found, missing = 0, 0
    for (path,) in sample:
        if os.path.exists(path):
            found += 1
        else:
            missing += 1
            log(f"  ❌ NOT FOUND: {path}")

    if sample:
        log(f"  Spot check: {found}/{len(sample)} files exist on disk")
        if missing > 0:
            log(f"  ⚠️  {missing} files not found — may need Phase C re-run for errors")
    else:
        log("  No J:\\CONSOLIDATED\\ paths in evidence_quotes yet")

    conn.close()

    elapsed = time.time() - start
    log(f"\n{'=' * 70}")
    log(f"PHASE D COMPLETE in {elapsed:.1f}s")
    log(f"  Rows updated: {grand_total:,}")
    log(f"  Backup: {backup_path}")
    log(f"  Remaining old refs: {len(remaining)} table/columns")
    log(f"{'=' * 70}")

    return len(remaining) == 0


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
