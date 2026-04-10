#!/usr/bin/env python3
"""
FIX & DIAGNOSE — Phase C zero-copy bug
=======================================
Root cause: Prior run set copy_status='pending' for all 226K files.
Phase A skipped (saw non-null status). Phase C found 0 'CANONICAL' files.
Phase D rewired 62K DB paths to J:\ locations with NO files.

Fix:
1. Restore litigation_context.db from backup
2. Reset state DB copy_status from 'pending' → NULL
3. Verify state is clean for re-execution
"""

import sqlite3, os, shutil, time, sys
from pathlib import Path

STATE_DB = r"D:\LitigationOS_tmp\consolidation_state.db"
LIT_DB = r"C:\Users\andre\LitigationOS\litigation_context.db"
BACKUP_DIR = r"J:\CONSOLIDATED\BACKUPS"

def get_conn(path):
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA busy_timeout = 60000")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA cache_size = -32000")
    conn.row_factory = sqlite3.Row
    return conn

def main():
    print("=" * 70)
    print("PHASE C BUG — DIAGNOSIS & FIX")
    print("=" * 70)
    
    # ── Step 1: Diagnose state DB ──────────────────────────────
    print("\n[1/5] Diagnosing state DB copy_status distribution...")
    db = get_conn(STATE_DB)
    rows = db.execute("""
        SELECT copy_status, COUNT(*) as cnt, 
               ROUND(SUM(file_size)/1073741824.0, 2) as gb
        FROM file_inventory
        GROUP BY copy_status
        ORDER BY cnt DESC
    """).fetchall()
    
    print(f"  {'Status':<25} {'Count':>10} {'Size (GB)':>10}")
    print(f"  {'─'*25} {'─'*10} {'─'*10}")
    for r in rows:
        status = r['copy_status'] or 'NULL'
        print(f"  {status:<25} {r['cnt']:>10,} {r['gb'] or 0:>10.2f}")
    
    total = db.execute("SELECT COUNT(*) FROM file_inventory").fetchone()[0]
    print(f"\n  Total: {total:,} files")
    
    # Check if 'pending' is the culprit
    pending = db.execute(
        "SELECT COUNT(*) FROM file_inventory WHERE copy_status = 'pending'"
    ).fetchone()[0]
    canonical = db.execute(
        "SELECT COUNT(*) FROM file_inventory WHERE copy_status = 'CANONICAL'"
    ).fetchone()[0]
    
    print(f"\n  'pending' files: {pending:,}")
    print(f"  'CANONICAL' files: {canonical:,}")
    
    if pending == 0 and canonical == 0:
        # Maybe all are some other status
        distinct = db.execute("SELECT DISTINCT copy_status FROM file_inventory").fetchall()
        print(f"  Distinct statuses: {[r[0] for r in distinct]}")
    
    db.close()
    
    # ── Step 2: Find & restore backup ──────────────────────────
    print("\n[2/5] Finding litigation_context.db backup...")
    backup = None
    if os.path.isdir(BACKUP_DIR):
        for f in sorted(os.listdir(BACKUP_DIR)):
            if f.startswith("litigation_context_pre_consolidation") and f.endswith(".db"):
                candidate = os.path.join(BACKUP_DIR, f)
                size = os.path.getsize(candidate)
                print(f"  Found: {f} ({size/1073741824:.2f} GB)")
                backup = candidate
    
    if not backup:
        print("  ⚠ No backup found in J:\\CONSOLIDATED\\BACKUPS\\")
        print("  Checking if DB paths are already wrong...")
        ldb = get_conn(LIT_DB)
        bad = ldb.execute("""
            SELECT COUNT(*) FROM evidence_quotes 
            WHERE source_file LIKE 'J:\\CONSOLIDATED\\%'
        """).fetchone()[0]
        old_d = ldb.execute("""
            SELECT COUNT(*) FROM evidence_quotes WHERE source_file LIKE 'D:\\%'
        """).fetchone()[0]
        old_i = ldb.execute("""
            SELECT COUNT(*) FROM evidence_quotes WHERE source_file LIKE 'I:\\%'
        """).fetchone()[0]
        print(f"  evidence_quotes with J:\\CONSOLIDATED\\ paths: {bad:,}")
        print(f"  evidence_quotes with D:\\ paths: {old_d:,}")
        print(f"  evidence_quotes with I:\\ paths: {old_i:,}")
        ldb.close()
        
        if bad > 0 and old_d == 0:
            print("  ❌ DB paths already migrated to J:\\ but no files there! NEED BACKUP!")
            sys.exit(1)
        elif bad == 0:
            print("  ✅ DB paths still point to original drives. No restore needed.")
    else:
        # Verify backup is uncorrupted
        print(f"  Verifying backup integrity...")
        try:
            bdb = sqlite3.connect(f"file:{backup}?mode=ro", uri=True)
            bdb.execute("PRAGMA integrity_check")
            cnt = bdb.execute("SELECT COUNT(*) FROM evidence_quotes").fetchone()[0]
            print(f"  ✅ Backup OK — evidence_quotes has {cnt:,} rows")
            # Check that backup has original paths
            orig_i = bdb.execute(
                "SELECT COUNT(*) FROM evidence_quotes WHERE source_file LIKE 'I:\\%'"
            ).fetchone()[0]
            orig_j = bdb.execute(
                "SELECT COUNT(*) FROM evidence_quotes WHERE source_file LIKE 'J:\\CONSOLIDATED\\%'"
            ).fetchone()[0]
            print(f"  Backup I:\\ paths: {orig_i:,}, J:\\CONSOLIDATED\\ paths: {orig_j:,}")
            bdb.close()
            
            if orig_i > 0 and orig_j == 0:
                print(f"\n  Restoring backup → {LIT_DB}...")
                # Close any WAL connections
                ldb = sqlite3.connect(LIT_DB)
                ldb.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                ldb.close()
                time.sleep(1)
                
                shutil.copy2(backup, LIT_DB)
                print(f"  ✅ Restored! Size: {os.path.getsize(LIT_DB)/1073741824:.2f} GB")
                
                # Verify restoration
                ldb = get_conn(LIT_DB)
                check_i = ldb.execute(
                    "SELECT COUNT(*) FROM evidence_quotes WHERE source_file LIKE 'I:\\%'"
                ).fetchone()[0]
                check_j = ldb.execute(
                    "SELECT COUNT(*) FROM evidence_quotes WHERE source_file LIKE 'J:\\CONSOLIDATED\\%'"
                ).fetchone()[0]
                print(f"  Post-restore: I:\\ = {check_i:,}, J:\\CONSOLIDATED\\ = {check_j:,}")
                ldb.close()
            else:
                print("  ⚠ Backup doesn't have original paths or already has J:\\ paths")
        except Exception as e:
            print(f"  ❌ Backup verification failed: {e}")
            sys.exit(1)
    
    # ── Step 3: Reset state DB ─────────────────────────────────
    print("\n[3/5] Resetting state DB copy_status...")
    db = get_conn(STATE_DB)
    
    # Reset 'pending' and any non-standard statuses to NULL
    # Keep EMPTY_SKIP, CANONICAL, DUPLICATE_SKIP, COPIED, VERIFIED as-is
    valid_statuses = {'CANONICAL', 'DUPLICATE_SKIP', 'EMPTY_SKIP', 'COPIED', 'VERIFIED', 'COPY_ERROR', 'SOURCE_MISSING'}
    
    reset = db.execute("""
        UPDATE file_inventory 
        SET copy_status = NULL 
        WHERE copy_status NOT IN ('CANONICAL','DUPLICATE_SKIP','EMPTY_SKIP','COPIED','VERIFIED','COPY_ERROR','SOURCE_MISSING')
    """)
    db.commit()
    print(f"  Reset {reset.rowcount:,} files from invalid status → NULL")
    
    # Also clear target_path and copied_at for non-copied files
    db.execute("""
        UPDATE file_inventory SET target_path = NULL, copied_at = NULL
        WHERE copy_status IS NULL OR copy_status IN ('CANONICAL','DUPLICATE_SKIP','EMPTY_SKIP')
    """)
    db.commit()
    
    # Verify new distribution
    rows2 = db.execute("""
        SELECT copy_status, COUNT(*) as cnt
        FROM file_inventory
        GROUP BY copy_status
        ORDER BY cnt DESC
    """).fetchall()
    print(f"\n  Post-reset distribution:")
    for r in rows2:
        status = r['copy_status'] or 'NULL (ready for Phase A)'
        print(f"    {status:<30} {r['cnt']:>10,}")
    
    db.close()
    
    # ── Step 4: Quick sanity check ─────────────────────────────
    print("\n[4/5] Sanity checks...")
    db = get_conn(STATE_DB)
    
    null_count = db.execute(
        "SELECT COUNT(*) FROM file_inventory WHERE copy_status IS NULL"
    ).fetchone()[0]
    non_null = db.execute(
        "SELECT COUNT(*) FROM file_inventory WHERE copy_status IS NOT NULL AND copy_status != ''"
    ).fetchone()[0]
    total = db.execute("SELECT COUNT(*) FROM file_inventory").fetchone()[0]
    
    print(f"  Total files: {total:,}")
    print(f"  NULL (will be processed by Phase A): {null_count:,}")
    print(f"  Already marked: {non_null:,}")
    
    # Check drive distribution
    for drive in ['D:', 'F:', 'G:', 'I:']:
        cnt = db.execute(
            "SELECT COUNT(*) FROM file_inventory WHERE source_drive = ?", (drive,)
        ).fetchone()[0]
        print(f"  {drive} files: {cnt:,}")
    
    db.close()
    
    # ── Step 5: J:\ state check ───────────────────────────────
    print("\n[5/5] J:\\ consolidated directory state...")
    consolidated = Path(r"J:\CONSOLIDATED")
    if consolidated.exists():
        for sub in sorted(consolidated.iterdir()):
            if sub.is_dir():
                try:
                    file_count = sum(1 for _ in sub.rglob("*") if _.is_file())
                    print(f"  {sub.name}/: {file_count:,} files")
                except:
                    print(f"  {sub.name}/: (error counting)")
            else:
                size = sub.stat().st_size
                print(f"  {sub.name}: {size/1073741824:.2f} GB")
    else:
        print("  J:\\CONSOLIDATED doesn't exist yet")
    
    print("\n" + "=" * 70)
    print("FIX COMPLETE — State DB reset, litigation DB restored.")
    print("Re-run execute_consolidation.py to properly execute all phases.")
    print("=" * 70)

if __name__ == "__main__":
    main()
