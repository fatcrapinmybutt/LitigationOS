"""
Phase E: Verification Report — Standalone executor.
Comprehensive verification after Phase C (copy) and Phase D (DB migration).
Checks: file counts, DB path integrity, disk usage, spot-check random files.
"""

import sqlite3
import os
import time
import hashlib
import random
from datetime import datetime
from pathlib import Path

# ── Config ──────────────────────────────────────────────────────────────
LITIGATION_DB = r"C:\Users\andre\LitigationOS\litigation_context.db"
STATE_DB = r"D:\LitigationOS_tmp\consolidation_state.db"
CONSOLIDATED_ROOT = r"J:\CONSOLIDATED"
LOG_FILE = r"D:\LitigationOS_tmp\phase_e_verification.log"

DRIVE_PREFIXES = ["D:\\", "F:\\", "G:\\", "I:\\"]
DRIVE_FOLDERS = {
    "D:\\": "D_DRIVE",
    "F:\\": "F_DRIVE",
    "G:\\": "G_DRIVE",
    "I:\\": "I_DRIVE",
}

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


def check_1_state_db_summary():
    """Check 1: State DB file status summary."""
    log("\n" + "─" * 60)
    log("CHECK 1: State DB Summary (consolidation_state.db)")
    log("─" * 60)

    conn = sqlite3.connect(f"file:{STATE_DB}?mode=ro", uri=True)
    conn.execute("PRAGMA busy_timeout=60000")

    # Overall status distribution
    rows = conn.execute(
        "SELECT copy_status, COUNT(*), SUM(file_size) "
        "FROM file_inventory GROUP BY copy_status ORDER BY COUNT(*) DESC"
    ).fetchall()

    total_files = 0
    total_bytes = 0
    for status, count, size_sum in rows:
        size_gb = (size_sum or 0) / (1024**3)
        log(f"  {status or 'NULL':20s}: {count:>8,} files  ({size_gb:>8.2f} GB)")
        total_files += count
        total_bytes += (size_sum or 0)

    log(f"  {'TOTAL':20s}: {total_files:>8,} files  ({total_bytes / (1024**3):>8.2f} GB)")

    # Per-drive breakdown
    log("\n  Per-drive status:")
    drives = conn.execute(
        "SELECT DISTINCT source_drive FROM file_inventory ORDER BY source_drive"
    ).fetchall()

    for (drive,) in drives:
        row = conn.execute(
            "SELECT copy_status, COUNT(*) FROM file_inventory "
            "WHERE source_drive = ? GROUP BY copy_status ORDER BY COUNT(*) DESC",
            (drive,)
        ).fetchall()
        detail = ", ".join(f"{s}={c}" for s, c in row)
        log(f"    {drive}: {detail}")

    # Error details
    errors = conn.execute(
        "SELECT source_path, copy_status FROM file_inventory "
        "WHERE copy_status IN ('COPY_ERROR', 'SOURCE_MISSING') LIMIT 20"
    ).fetchall()

    if errors:
        log(f"\n  ⚠️  Error details (first {len(errors)}):")
        for path, status in errors:
            log(f"    [{status}] {path}")

    conn.close()
    return total_files


def check_2_db_path_integrity():
    """Check 2: Verify no old-drive references remain in litigation_context.db."""
    log("\n" + "─" * 60)
    log("CHECK 2: DB Path Integrity (litigation_context.db)")
    log("─" * 60)

    conn = sqlite3.connect(LITIGATION_DB)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")

    violations = {}
    clean_tables = 0

    for table, column in MIGRATION_TARGETS:
        # Check table/column exist
        tables = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )}
        if table not in tables:
            log(f"  ⚠️  Table {table} not found")
            continue

        cols = {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}
        if column not in cols:
            log(f"  ⚠️  Column {table}.{column} not found")
            continue

        for prefix in DRIVE_PREFIXES:
            count = conn.execute(
                f"SELECT COUNT(*) FROM [{table}] WHERE [{column}] LIKE ?",
                (prefix + "%",)
            ).fetchone()[0]

            if count > 0:
                key = f"{table}.{column}"
                if key not in violations:
                    violations[key] = {}
                violations[key][prefix[0]] = count

        # Count J:\CONSOLIDATED refs (should be > 0 after migration)
        j_count = conn.execute(
            f"SELECT COUNT(*) FROM [{table}] WHERE [{column}] LIKE 'J:\\CONSOLIDATED\\%'"
        ).fetchone()[0]

        if not any(f"{table}.{column}" in k for k in violations):
            clean_tables += 1
            log(f"  ✅ {table}.{column}: CLEAN (J:\\CONSOLIDATED refs: {j_count:,})")
        else:
            v = violations[f"{table}.{column}"]
            detail = ", ".join(f"{k}:={v}" for k, v in v.items())
            log(f"  ❌ {table}.{column}: {detail} old refs remain (J: refs: {j_count:,})")

    conn.close()

    if not violations:
        log(f"\n  ✅ ALL {clean_tables} table/columns CLEAN — zero old-drive references!")
        return True
    else:
        total_violations = sum(sum(v.values()) for v in violations.values())
        log(f"\n  ❌ {total_violations:,} old-drive references remain across {len(violations)} columns")
        return False


def check_3_disk_usage():
    """Check 3: J:\CONSOLIDATED disk usage report."""
    log("\n" + "─" * 60)
    log("CHECK 3: J:\\CONSOLIDATED Disk Usage")
    log("─" * 60)

    if not os.path.exists(CONSOLIDATED_ROOT):
        log("  ❌ J:\\CONSOLIDATED does not exist!")
        return

    total_files = 0
    total_size = 0

    for drive_folder in ["D_DRIVE", "F_DRIVE", "G_DRIVE", "I_DRIVE", "BACKUPS", "ROOT_CLEANUP"]:
        folder = os.path.join(CONSOLIDATED_ROOT, drive_folder)
        if not os.path.exists(folder):
            log(f"  {drive_folder}: (not found)")
            continue

        folder_files = 0
        folder_size = 0
        for root, dirs, files in os.walk(folder):
            for f in files:
                fp = os.path.join(root, f)
                try:
                    folder_size += os.path.getsize(fp)
                    folder_files += 1
                except OSError:
                    pass

        size_gb = folder_size / (1024**3)
        log(f"  {drive_folder:15s}: {folder_files:>8,} files  ({size_gb:>8.2f} GB)")
        total_files += folder_files
        total_size += folder_size

    log(f"  {'TOTAL':15s}: {total_files:>8,} files  ({total_size / (1024**3):>8.2f} GB)")

    # J:\ free space
    try:
        import shutil
        total, used, free = shutil.disk_usage("J:\\")
        log(f"\n  J:\\ disk: {total / (1024**3):.1f} GB total, "
            f"{used / (1024**3):.1f} GB used, {free / (1024**3):.1f} GB free")
    except Exception as e:
        log(f"  Could not check J:\\ disk usage: {e}")


def check_4_spot_check(n: int = 20):
    """Check 4: Spot-check random copied files exist and match source."""
    log("\n" + "─" * 60)
    log(f"CHECK 4: Spot-Check {n} Random Files")
    log("─" * 60)

    conn = sqlite3.connect(f"file:{STATE_DB}?mode=ro", uri=True)
    conn.execute("PRAGMA busy_timeout=60000")

    # Get random COPIED/VERIFIED files
    samples = conn.execute(
        "SELECT source_path, target_path, file_size, xxhash "
        "FROM file_inventory "
        "WHERE copy_status IN ('COPIED', 'VERIFIED') AND target_path IS NOT NULL "
        "ORDER BY RANDOM() LIMIT ?",
        (n,)
    ).fetchall()

    conn.close()

    if not samples:
        log("  ⚠️  No COPIED/VERIFIED files found in state DB")
        return

    found = 0
    missing = 0
    size_match = 0
    size_mismatch = 0

    for source, target, expected_size, expected_hash in samples:
        if not target or not os.path.exists(target):
            missing += 1
            log(f"  ❌ MISSING: {target}")
            continue

        found += 1
        actual_size = os.path.getsize(target)

        if actual_size == expected_size:
            size_match += 1
        else:
            size_mismatch += 1
            log(f"  ⚠️  SIZE MISMATCH: {target}")
            log(f"       Expected: {expected_size:,} bytes, Got: {actual_size:,} bytes")

    log(f"\n  Results:")
    log(f"    Found on disk:   {found}/{len(samples)}")
    log(f"    Missing:         {missing}/{len(samples)}")
    log(f"    Size match:      {size_match}/{found}")
    log(f"    Size mismatch:   {size_mismatch}/{found}")

    if missing == 0 and size_mismatch == 0:
        log(f"  ✅ ALL {n} spot-checks PASSED")
    else:
        log(f"  ⚠️  {missing + size_mismatch} issues found in spot-check")


def check_5_fts5_health():
    """Check 5: FTS5 index health — ensure searchable after migration."""
    log("\n" + "─" * 60)
    log("CHECK 5: FTS5 Index Health")
    log("─" * 60)

    conn = sqlite3.connect(LITIGATION_DB)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")

    fts_tables = {
        "evidence_fts": "custody",
        "timeline_fts": "custody",
        "md_sections_fts": "custody",
    }

    for fts_name, test_query in fts_tables.items():
        exists = conn.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?",
            (fts_name,)
        ).fetchone()[0]

        if not exists:
            log(f"  ⚠️  {fts_name}: NOT FOUND")
            continue

        try:
            count = conn.execute(
                f"SELECT COUNT(*) FROM [{fts_name}] WHERE [{fts_name}] MATCH ?",
                (test_query,)
            ).fetchone()[0]
            log(f"  ✅ {fts_name}: operational ('{test_query}' → {count:,} hits)")
        except sqlite3.OperationalError as e:
            log(f"  ❌ {fts_name}: ERROR — {e}")

    conn.close()


def check_6_backup_integrity():
    """Check 6: Verify backup exists and is reasonable size."""
    log("\n" + "─" * 60)
    log("CHECK 6: Backup Integrity")
    log("─" * 60)

    if not os.path.exists(BACKUP_DIR):
        log("  ⚠️  Backup directory not found")
        return

    backups = sorted(Path(BACKUP_DIR).glob("litigation_context_*.db"))
    if not backups:
        log("  ⚠️  No backup files found!")
        return

    source_size = os.path.getsize(LITIGATION_DB) / (1024**3)
    log(f"  Source DB: {source_size:.2f} GB")

    for bp in backups:
        bp_size = bp.stat().st_size / (1024**3)
        ratio = bp_size / source_size if source_size > 0 else 0
        status = "✅" if 0.5 < ratio < 1.5 else "⚠️"
        log(f"  {status} {bp.name}: {bp_size:.2f} GB (ratio: {ratio:.2f})")


BACKUP_DIR = r"J:\CONSOLIDATED\BACKUPS"


def main():
    start = time.time()
    log("=" * 70)
    log("PHASE E: COMPREHENSIVE VERIFICATION REPORT")
    log(f"Started: {datetime.now().isoformat()}")
    log("=" * 70)

    # Run all checks
    check_1_state_db_summary()
    paths_clean = check_2_db_path_integrity()
    check_3_disk_usage()
    check_4_spot_check(20)
    check_5_fts5_health()
    check_6_backup_integrity()

    # ── Final Verdict ──
    elapsed = time.time() - start
    log("\n" + "=" * 70)
    log("VERIFICATION SUMMARY")
    log("=" * 70)

    if paths_clean:
        log("  ✅ DB path integrity: CLEAN")
    else:
        log("  ❌ DB path integrity: OLD REFERENCES REMAIN")

    log(f"\n  Verification completed in {elapsed:.1f}s")
    log(f"  Full log: {LOG_FILE}")
    log("=" * 70)

    return paths_clean


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
