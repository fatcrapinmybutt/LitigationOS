#!/usr/bin/env python3
"""Fix Phase C bug: restore DB backup + reset state DB."""
import sqlite3, os, shutil, time

STATE_DB = r"D:\LitigationOS_tmp\consolidation_state.db"
LIT_DB = r"C:\Users\andre\LitigationOS\litigation_context.db"
LIT_SHM = LIT_DB + "-shm"
LIT_WAL = LIT_DB + "-wal"
BACKUP = r"J:\CONSOLIDATED\BACKUPS\litigation_context_pre_consolidation_20260404_172115.db"

print("=" * 60)
print("FIX: Restore DB + Reset State")
print("=" * 60)

# Step 1: Reset state DB (easy part)
print("\n[1] Resetting state DB 'pending' -> NULL...")
db = sqlite3.connect(STATE_DB)
db.execute("PRAGMA busy_timeout = 60000")
db.execute("PRAGMA journal_mode = WAL")
n = db.execute("UPDATE file_inventory SET copy_status = NULL WHERE copy_status = 'pending'").rowcount
db.execute("UPDATE file_inventory SET target_path = NULL, copied_at = NULL")
db.commit()
# Verify
null_ct = db.execute("SELECT COUNT(*) FROM file_inventory WHERE copy_status IS NULL").fetchone()[0]
total = db.execute("SELECT COUNT(*) FROM file_inventory").fetchone()[0]
print(f"   Reset {n:,} files. NULL={null_ct:,}, Total={total:,}")
db.close()

# Step 2: Force-checkpoint and remove WAL/SHM before restore
print("\n[2] Force-checkpointing litigation_context.db...")
try:
    c = sqlite3.connect(LIT_DB)
    c.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    c.close()
    time.sleep(2)
except Exception as e:
    print(f"   Checkpoint warning: {e}")

# Remove WAL/SHM files to release memory-mapped sections
for f in [LIT_SHM, LIT_WAL]:
    if os.path.exists(f):
        try:
            os.remove(f)
            print(f"   Removed {os.path.basename(f)}")
        except Exception as e:
            print(f"   Could not remove {os.path.basename(f)}: {e}")

time.sleep(2)

# Step 3: Restore from backup
print(f"\n[3] Restoring from backup ({os.path.getsize(BACKUP)/1073741824:.2f} GB)...")
try:
    shutil.copy2(BACKUP, LIT_DB)
    print(f"   Restored! New size: {os.path.getsize(LIT_DB)/1073741824:.2f} GB")
except Exception as e:
    print(f"   ERROR: {e}")
    print("   Trying alternative: delete target first...")
    try:
        os.remove(LIT_DB)
        time.sleep(1)
        shutil.copy2(BACKUP, LIT_DB)
        print(f"   Restored via delete+copy! Size: {os.path.getsize(LIT_DB)/1073741824:.2f} GB")
    except Exception as e2:
        print(f"   FATAL: Could not restore: {e2}")
        print("   The MCP server or VS Code may be locking the file.")
        print("   Close VS Code SQLite extensions and retry.")
        exit(1)

# Step 4: Verify restoration
print("\n[4] Verifying restored DB...")
ldb = sqlite3.connect(LIT_DB)
ldb.execute("PRAGMA busy_timeout = 60000")
cnt_i = ldb.execute("SELECT COUNT(*) FROM evidence_quotes WHERE source_file LIKE 'I:\\%'").fetchone()[0]
cnt_j = ldb.execute("SELECT COUNT(*) FROM evidence_quotes WHERE source_file LIKE 'J:\\CONSOLIDATED\\%'").fetchone()[0]
cnt_tot = ldb.execute("SELECT COUNT(*) FROM evidence_quotes").fetchone()[0]
print(f"   evidence_quotes total: {cnt_tot:,}")
print(f"   I:\\ paths: {cnt_i:,}")
print(f"   J:\\CONSOLIDATED\\ paths: {cnt_j:,}")

if cnt_j == 0 and cnt_i > 0:
    print("   RESTORED SUCCESSFULLY - original paths intact")
else:
    print("   WARNING: Unexpected path distribution")
ldb.close()

print("\n" + "=" * 60)
print("READY: State DB reset + litigation DB restored.")
print("Now re-run execute_consolidation.py")
print("=" * 60)
