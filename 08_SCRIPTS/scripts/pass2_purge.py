"""PASS 2: Purge junk + move duplicates. Safe protocol."""
import sqlite3, os, shutil, time
from datetime import datetime

DB = r"I:\DRIVE_ORG\drive_inventory.db"
LOG = r"I:\DRIVE_ORG\operations.log"
ARCHIVE = r"I:\DEDUP_ARCHIVE"

def log(msg):
    ts = datetime.now().isoformat()
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def safe_delete(path):
    """Delete file, return bytes freed."""
    try:
        sz = os.path.getsize(path)
        os.remove(path)
        return sz
    except:
        return 0

def safe_move_to_archive(path, drive_label):
    """Move duplicate to archive, return bytes freed on source."""
    try:
        sz = os.path.getsize(path)
        # Build archive path preserving relative structure
        rel = os.path.relpath(path, os.path.splitdrive(path)[0] + os.sep)
        dest = os.path.join(ARCHIVE, drive_label, rel)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.move(path, dest)
        return sz
    except Exception as e:
        return 0

def run():
    os.makedirs(ARCHIVE, exist_ok=True)
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA journal_mode=WAL")

    log("=" * 60)
    log("PASS 2: PURGE + ORGANIZE")
    log("=" * 60)

    # PHASE A: Delete JUNK on all drives (no backup needed)
    log("\nPHASE A: JUNK DELETION")
    
    # Get junk files sorted by size desc, prioritize D: and C:
    junk_files = conn.execute("""
        SELECT path, size, drive FROM files
        WHERE (classification = 'JUNK' OR is_junk = 1)
        AND size > 10000
        ORDER BY 
            CASE drive 
                WHEN 'D' THEN 0 
                WHEN 'C_LitigationOS' THEN 1 
                ELSE 2 
            END,
            size DESC
    """).fetchall()
    
    log(f"  Junk targets: {len(junk_files):,} files")
    
    # Safety: skip anything in LitigationOS core paths or Delta99
    PROTECTED = [
        r"c:\users\andre\litigationos\00_system",
        r"c:\users\andre\litigationos\01_case_files",
        r"c:\users\andre\litigationos\02_evidence",
        r"c:\users\andre\litigationos\03_authorities",
        r"c:\users\andre\litigationos\litigation_context.db",
        r"i:\litigationos_delta99",
        r"i:\drive_org",
    ]
    
    freed_junk = 0
    deleted_count = 0
    skipped = 0
    
    for path, size, drive in junk_files:
        pl = path.lower()
        # Safety check
        if any(pl.startswith(p) for p in PROTECTED):
            skipped += 1
            continue
        # Skip small stuff for speed
        if size < 100000 and freed_junk > 5 * 1024**3:
            continue
        
        freed = safe_delete(path)
        if freed > 0:
            freed_junk += freed
            deleted_count += 1
            conn.execute("UPDATE files SET is_junk=1 WHERE path=?", (path,))
        
        if deleted_count % 500 == 0 and deleted_count > 0:
            conn.commit()
            log(f"    Deleted {deleted_count:,} junk files = {freed_junk/1024/1024/1024:.2f}GB")
    
    conn.commit()
    log(f"  JUNK PHASE DONE: {deleted_count:,} deleted = {freed_junk/1024/1024/1024:.2f}GB freed, {skipped} protected")

    # PHASE B: Move duplicates (keep=best, move rest to archive)
    log("\nPHASE B: DUPLICATE ARCHIVAL")
    
    # Process by drive priority: D first (critical), then F, G, H, C, I last
    drive_order = ["D", "F", "G", "H", "C_LitigationOS", "I"]
    
    freed_dedup = 0
    moved_count = 0
    move_errors = 0
    
    for target_drive in drive_order:
        dupes = conn.execute("""
            SELECT f.path, f.size, f.dedup_group, dg.keep_path
            FROM files f
            JOIN dedup_groups dg ON f.dedup_group = dg.group_id
            WHERE f.is_duplicate = 1 
            AND f.drive = ?
            AND f.size > 10000
            ORDER BY f.size DESC
        """, (target_drive,)).fetchall()
        
        if not dupes:
            continue
        
        drive_total = sum(d[1] for d in dupes)
        log(f"  {target_drive}: {len(dupes):,} dupes = {drive_total/1024/1024/1024:.2f}GB")
        
        for path, size, group, keep in dupes:
            pl = path.lower()
            if any(pl.startswith(p) for p in PROTECTED):
                continue
            
            # Verify keep file still exists before deleting duplicate
            if not os.path.exists(keep):
                move_errors += 1
                continue
            
            # For files on I: that are dupes, just delete (archive IS on I:)
            if target_drive == "I":
                freed = safe_delete(path)
            else:
                # Move to archive on I:
                drive_label = target_drive.replace(":", "").replace("_", "-")
                freed = safe_move_to_archive(path, drive_label)
            
            if freed > 0:
                freed_dedup += freed
                moved_count += 1
            else:
                move_errors += 1
            
            if moved_count % 500 == 0 and moved_count > 0:
                conn.commit()
                log(f"    Moved/deleted {moved_count:,} = {freed_dedup/1024/1024/1024:.2f}GB")
        
        conn.commit()
        log(f"    {target_drive} done: {freed_dedup/1024/1024/1024:.2f}GB total freed so far")

    log(f"\n{'='*60}")
    log(f"PASS 2 COMPLETE")
    log(f"  Junk deleted: {deleted_count:,} files = {freed_junk/1024/1024/1024:.2f}GB")
    log(f"  Dupes archived: {moved_count:,} files = {freed_dedup/1024/1024/1024:.2f}GB")
    log(f"  TOTAL FREED: {(freed_junk+freed_dedup)/1024/1024/1024:.2f}GB")
    log(f"  Errors: {move_errors}")
    log(f"{'='*60}")
    
    conn.close()

if __name__ == "__main__":
    run()
