#!/usr/bin/env python3
"""
db_backup_engine.py - Database backup engine for LitigationOS.

Features:
  - WAL checkpoint (TRUNCATE) before backup
  - Timestamped copy to backup destination
  - Keeps last 3 backups, deletes older ones
  - Verifies backup integrity after copy
  - Logs to phase0b_ingest_log table

CLI:
    python db_backup_engine.py
    python db_backup_engine.py --checkpoint-only
    python db_backup_engine.py --dest "D:\\MyBackup"
"""

import os
import sys
import shutil
import sqlite3
import argparse
import datetime
import glob as globmod

# ── Config ───────────────────────────────────────────────────────────────────
LOS_ROOT        = r"C:\Users\andre\LitigationOS"
DB_PATH         = os.path.join(LOS_ROOT, "litigation_context.db")
DEFAULT_DEST    = r"I:\LitigationOS_Backup"
KEEP_BACKUPS    = 3
BACKUP_PREFIX   = "litigation_context_"
BACKUP_SUFFIX   = ".db"


def fmt_bytes(n):
    for unit in ("B", "KB", "MB", "GB"):
        if abs(n) < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def log_to_db(message, status="INFO"):
    """Log a message to the phase0b_ingest_log table if it exists."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        # Check if table exists
        cur.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name='phase0b_ingest_log';"
        )
        if cur.fetchone():
            cur.execute(
                "INSERT INTO phase0b_ingest_log (timestamp, source, message, status) "
                "VALUES (?, ?, ?, ?);",
                (datetime.datetime.now().isoformat(), "db_backup_engine", message, status),
            )
            conn.commit()
        conn.close()
    except Exception:
        pass  # Don't fail the backup because logging failed


def wal_checkpoint():
    """Run WAL checkpoint in TRUNCATE mode. Returns (pages_checkpointed, log_size)."""
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Database not found: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("PRAGMA wal_checkpoint(TRUNCATE);")
    result = cur.fetchone()  # (busy, log, checkpointed)
    conn.close()
    return result


def prune_old_backups(dest_dir):
    """Keep only the latest KEEP_BACKUPS backups, delete the rest."""
    pattern = os.path.join(dest_dir, f"{BACKUP_PREFIX}*{BACKUP_SUFFIX}")
    backups = sorted(globmod.glob(pattern))
    removed = []
    while len(backups) > KEEP_BACKUPS:
        old = backups.pop(0)
        try:
            os.remove(old)
            removed.append(os.path.basename(old))
        except Exception as exc:
            print(f"  ⚠ Could not delete {old}: {exc}")
    return removed


def verify_backup(backup_path):
    """Run integrity check on the backup copy."""
    try:
        conn = sqlite3.connect(backup_path)
        cur = conn.cursor()
        cur.execute("PRAGMA integrity_check;")
        result = cur.fetchone()[0]
        conn.close()
        return result == "ok", result
    except Exception as exc:
        return False, str(exc)


def run_backup(dest_dir=None, checkpoint_only=False):
    ts_start = datetime.datetime.now()
    ts_str   = ts_start.strftime("%Y%m%d_%H%M%S")

    print("=" * 60)
    print("  LitigationOS Database Backup")
    print(f"  Timestamp : {ts_start.isoformat()}")
    print(f"  Source DB : {DB_PATH}")
    print("=" * 60)

    if not os.path.exists(DB_PATH):
        print(f"\n  ✗ Database not found: {DB_PATH}")
        log_to_db("Backup failed — database not found", "ERROR")
        return False

    db_size = os.path.getsize(DB_PATH)
    print(f"\n  DB size: {fmt_bytes(db_size)}")

    # 1. WAL Checkpoint
    print("\n[1] WAL checkpoint (TRUNCATE) …")
    try:
        busy, log_pages, checkpointed = wal_checkpoint()
        print(f"  ✓ Checkpoint complete — log={log_pages}, checkpointed={checkpointed}")
        log_to_db(f"WAL checkpoint: log={log_pages}, cp={checkpointed}")
    except Exception as exc:
        print(f"  ⚠ Checkpoint failed: {exc}")
        log_to_db(f"WAL checkpoint failed: {exc}", "WARNING")

    if checkpoint_only:
        print("\n  → --checkpoint-only mode, skipping copy.")
        return True

    # 2. Copy
    dest = dest_dir or DEFAULT_DEST
    print(f"\n[2] Copying to {dest} …")
    if not os.path.isdir(dest):
        try:
            os.makedirs(dest, exist_ok=True)
            print(f"  → Created directory: {dest}")
        except Exception as exc:
            print(f"  ✗ Cannot create destination: {exc}")
            log_to_db(f"Backup failed — cannot create dest: {exc}", "ERROR")
            return False

    backup_name = f"{BACKUP_PREFIX}{ts_str}{BACKUP_SUFFIX}"
    backup_path = os.path.join(dest, backup_name)
    try:
        shutil.copy2(DB_PATH, backup_path)
        bk_size = os.path.getsize(backup_path)
        print(f"  ✓ Copied → {backup_name} ({fmt_bytes(bk_size)})")
        log_to_db(f"Backup created: {backup_name} ({fmt_bytes(bk_size)})")
    except Exception as exc:
        print(f"  ✗ Copy failed: {exc}")
        log_to_db(f"Backup copy failed: {exc}", "ERROR")
        return False

    # 3. Verify
    print("\n[3] Verifying backup integrity …")
    ok, detail = verify_backup(backup_path)
    if ok:
        print(f"  ✓ Integrity check passed")
        log_to_db(f"Backup verified: {backup_name}")
    else:
        print(f"  ✗ Integrity check FAILED: {detail}")
        log_to_db(f"Backup integrity FAILED: {detail}", "ERROR")

    # 4. Prune
    print(f"\n[4] Pruning old backups (keep last {KEEP_BACKUPS}) …")
    removed = prune_old_backups(dest)
    if removed:
        for r in removed:
            print(f"  → Deleted: {r}")
        log_to_db(f"Pruned {len(removed)} old backup(s)")
    else:
        print("  – Nothing to prune")

    elapsed = (datetime.datetime.now() - ts_start).total_seconds()
    print("\n" + "=" * 60)
    print(f"  Backup complete in {elapsed:.1f}s")
    print(f"  Backup: {backup_path}")
    print("=" * 60)

    log_to_db(f"Backup complete in {elapsed:.1f}s: {backup_name}", "SUCCESS")
    return ok


def main():
    parser = argparse.ArgumentParser(description="LitigationOS Database Backup Engine")
    parser.add_argument("--checkpoint-only", action="store_true",
                        help="Run WAL checkpoint only, do not copy")
    parser.add_argument("--dest", type=str, default=None,
                        help=f"Backup destination (default: {DEFAULT_DEST})")
    args = parser.parse_args()

    ok = run_backup(dest_dir=args.dest, checkpoint_only=args.checkpoint_only)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
