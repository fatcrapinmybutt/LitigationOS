"""Optimized dedup detection - batch approach."""
import sqlite3, json, os, time
from datetime import datetime
from collections import defaultdict

DB_PATH = r"I:\DRIVE_ORG\drive_inventory.db"
LOG_PATH = r"I:\DRIVE_ORG\operations.log"
CANDIDATES_PATH = r"I:\DRIVE_ORG\DEDUP_CANDIDATES.json"
JUNK_PATH = r"I:\DRIVE_ORG\JUNK_TARGETS.json"

def log(msg):
    ts = datetime.now().isoformat()
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_PATH, 'a', encoding='utf-8') as f:
        f.write(line + '\n')

def keep_priority(path):
    p = path.lower()
    if 'litigationos_delta99' in p: return 0  # Delta99 finalized = highest
    if p.startswith(r'c:\users\andre\litigationos'): return 1
    if p.startswith('i:\\'): return 2
    return 3

def run():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    
    log("DEDUP PHASE 2: Optimized batch detection")
    
    # Step 1: Get ALL candidate groups (name+size appearing 2+ times, size > 1KB)
    log("  Step 1: Fetching all duplicate candidates from DB...")
    candidates = conn.execute("""
        SELECT filename, size, GROUP_CONCAT(path, '|||') as paths
        FROM files 
        WHERE size > 1024 AND is_junk = 0
        GROUP BY filename, size 
        HAVING COUNT(*) > 1
        ORDER BY size * COUNT(*) DESC
    """).fetchall()
    
    log(f"  Found {len(candidates):,} candidate groups")
    
    # Step 2: Content-peek in batches
    confirmed_groups = []
    total_recoverable = 0
    group_num = 0
    errors = 0
    
    for i, (fname, fsize, paths_str) in enumerate(candidates):
        paths = paths_str.split('|||')
        if len(paths) < 2:
            continue
        
        # Sort by keep priority
        paths.sort(key=keep_priority)
        
        # Read reference file (first = highest priority)
        ref_path = paths[0]
        try:
            with open(ref_path, 'rb') as f:
                ref_head = f.read(8192)
                if fsize > 16384:
                    f.seek(max(0, fsize - 8192))
                    ref_tail = f.read(8192)
                else:
                    ref_tail = ref_head
        except (OSError, PermissionError):
            errors += 1
            continue
        
        # Compare all other files
        dupes = []
        for p in paths[1:]:
            try:
                with open(p, 'rb') as f:
                    head = f.read(8192)
                    if fsize > 16384:
                        f.seek(max(0, fsize - 8192))
                        tail = f.read(8192)
                    else:
                        tail = head
                
                if head == ref_head and tail == ref_tail:
                    dupes.append(p)
            except (OSError, PermissionError):
                errors += 1
                continue
        
        if dupes:
            group_id = f"G{group_num:06d}"
            recoverable = fsize * len(dupes)
            total_recoverable += recoverable
            
            confirmed_groups.append({
                "group_id": group_id,
                "filename": fname,
                "size": fsize,
                "keep": ref_path,
                "duplicates": dupes,
                "recoverable_bytes": recoverable
            })
            
            # Update DB
            conn.execute("INSERT OR REPLACE INTO dedup_groups VALUES (?,?,?,?,?,?)",
                        (group_id, fname, fsize, 1 + len(dupes), ref_path, 'confirmed'))
            for dp in dupes:
                conn.execute("UPDATE files SET dedup_group=?, is_duplicate=1 WHERE path=?",
                            (group_id, dp))
            
            group_num += 1
        
        if (i + 1) % 5000 == 0:
            conn.commit()
            log(f"  Processed {i+1:,}/{len(candidates):,} | {group_num:,} confirmed | {total_recoverable/1024/1024/1024:.1f}GB recoverable | {errors} errors")
    
    conn.commit()
    
    # Step 3: Generate junk analysis
    log("  Generating junk analysis...")
    junk_data = conn.execute("""
        SELECT drive, COUNT(*), SUM(size) 
        FROM files 
        WHERE classification IN ('JUNK','SYSTEM') OR is_junk=1
        GROUP BY drive 
        ORDER BY SUM(size) DESC
    """).fetchall()
    
    big_junk = conn.execute("""
        SELECT path, size, classification FROM files 
        WHERE (classification='JUNK' OR is_junk=1) AND size > 1000000
        ORDER BY size DESC LIMIT 100
    """).fetchall()
    
    total_junk = sum(r[2] or 0 for r in junk_data)
    
    with open(JUNK_PATH, 'w', encoding='utf-8') as f:
        json.dump({
            "generated": datetime.now().isoformat(),
            "total_junk_gb": round(total_junk/1024/1024/1024, 2),
            "by_drive": [{"drive": d, "files": c, "size_gb": round((s or 0)/1024/1024/1024, 2)} for d,c,s in junk_data],
            "big_junk_files": [{"path": p, "size_mb": round(s/1024/1024,1), "class": cl} for p,s,cl in big_junk]
        }, f, indent=2)
    
    # Step 4: Save dedup candidates (top 1000 by recoverable bytes)
    confirmed_groups.sort(key=lambda g: g['recoverable_bytes'], reverse=True)
    
    with open(CANDIDATES_PATH, 'w', encoding='utf-8') as f:
        json.dump({
            "generated": datetime.now().isoformat(),
            "total_groups": group_num,
            "total_recoverable_gb": round(total_recoverable/1024/1024/1024, 2),
            "total_junk_gb": round(total_junk/1024/1024/1024, 2),
            "combined_recovery_gb": round((total_recoverable + total_junk)/1024/1024/1024, 2),
            "top_groups": confirmed_groups[:1000]
        }, f, indent=2)
    
    log(f"\n{'='*60}")
    log(f"PASS 1 COMPLETE — DEDUP DETECTION DONE")
    log(f"  Total candidate groups checked: {len(candidates):,}")
    log(f"  Confirmed duplicate groups: {group_num:,}")
    log(f"  Duplicate files: {sum(len(g['duplicates']) for g in confirmed_groups):,}")
    log(f"  Dedup recoverable: {total_recoverable/1024/1024/1024:.2f}GB")
    log(f"  Junk identified: {total_junk/1024/1024/1024:.2f}GB")
    log(f"  TOTAL RECOVERABLE: {(total_recoverable+total_junk)/1024/1024/1024:.2f}GB")
    log(f"  Errors: {errors}")
    log(f"{'='*60}")
    
    # Per-drive dedup summary
    log("\nPER-DRIVE DUPLICATE SUMMARY:")
    drive_stats = conn.execute("""
        SELECT drive, COUNT(*), SUM(size) 
        FROM files WHERE is_duplicate=1 
        GROUP BY drive ORDER BY SUM(size) DESC
    """).fetchall()
    for d, c, s in drive_stats:
        log(f"  {d}: {c:,} dupes, {(s or 0)/1024/1024/1024:.2f}GB")
    
    conn.close()

if __name__ == "__main__":
    run()
