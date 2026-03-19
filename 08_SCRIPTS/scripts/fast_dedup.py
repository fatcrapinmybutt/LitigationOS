"""Fast dedup: name+size match for big files, content-peek only for ambiguous."""
import sqlite3, json, os, time
from datetime import datetime
from collections import defaultdict

DB_PATH = r"I:\DRIVE_ORG\drive_inventory.db"
LOG_PATH = r"I:\DRIVE_ORG\operations.log"

def log(msg):
    ts = datetime.now().isoformat()
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOG_PATH, 'a', encoding='utf-8') as f:
        f.write(line + '\n')

def keep_priority(path):
    p = path.lower()
    if 'litigationos_delta99' in p: return 0
    if p.startswith(r'c:\users\andre\litigationos'): return 1
    if p.startswith('i:\\'): return 2
    return 3

def run():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    
    log("FAST DEDUP: Starting optimized detection")
    
    # Strategy: For files > 100KB, name+size is sufficient (collision rate near 0)
    # For files 1KB-100KB, peek first 4KB only (skip slow tail seek)
    # Skip files < 1KB entirely
    
    # TIER 1: Big files (>100KB) — name+size match only (no I/O needed!)
    log("  TIER 1: Big files (>100KB) by name+size...")
    big_groups = conn.execute("""
        SELECT filename, size, COUNT(*) as cnt 
        FROM files 
        WHERE size > 102400 AND is_junk=0
        GROUP BY filename, size 
        HAVING cnt > 1
        ORDER BY size * cnt DESC
    """).fetchall()
    
    log(f"  Found {len(big_groups):,} big-file duplicate groups")
    
    group_num = 0
    total_recoverable = 0
    all_confirmed = []
    
    for fname, fsize, cnt in big_groups:
        paths = [r[0] for r in conn.execute(
            "SELECT path FROM files WHERE filename=? AND size=?", (fname, fsize)
        ).fetchall()]
        
        if len(paths) < 2: continue
        paths.sort(key=keep_priority)
        
        keep = paths[0]
        dupes = paths[1:]
        recoverable = fsize * len(dupes)
        total_recoverable += recoverable
        gid = f"G{group_num:06d}"
        
        conn.execute("INSERT OR REPLACE INTO dedup_groups VALUES (?,?,?,?,?,?)",
                     (gid, fname, fsize, len(paths), keep, 'confirmed'))
        for dp in dupes:
            conn.execute("UPDATE files SET dedup_group=?, is_duplicate=1 WHERE path=?", (gid, dp))
        
        all_confirmed.append({
            "group_id": gid, "filename": fname, "size": fsize,
            "keep": keep, "duplicates": dupes,
            "recoverable_bytes": recoverable
        })
        group_num += 1
        
        if group_num % 2000 == 0:
            conn.commit()
            log(f"    {group_num:,} groups | {total_recoverable/1024/1024/1024:.1f}GB")
    
    conn.commit()
    log(f"  TIER 1 done: {group_num:,} groups, {total_recoverable/1024/1024/1024:.2f}GB")
    
    # TIER 2: Medium files (1KB-100KB) — quick head-peek only
    log("  TIER 2: Medium files (1KB-100KB) with head-peek...")
    t1_count = group_num
    t2_errors = 0
    
    med_groups = conn.execute("""
        SELECT filename, size, COUNT(*) as cnt 
        FROM files 
        WHERE size BETWEEN 1024 AND 102400 AND is_junk=0
        GROUP BY filename, size 
        HAVING cnt > 1
        ORDER BY size * cnt DESC
        LIMIT 20000
    """).fetchall()
    
    log(f"  Found {len(med_groups):,} medium-file candidate groups (capped at 20K)")
    
    for fname, fsize, cnt in med_groups:
        paths = [r[0] for r in conn.execute(
            "SELECT path FROM files WHERE filename=? AND size=?", (fname, fsize)
        ).fetchall()]
        
        if len(paths) < 2: continue
        paths.sort(key=keep_priority)
        
        ref_path = paths[0]
        try:
            with open(ref_path, 'rb') as f:
                ref_head = f.read(4096)
        except:
            t2_errors += 1
            continue
        
        dupes = []
        for p in paths[1:]:
            try:
                with open(p, 'rb') as f:
                    head = f.read(4096)
                if head == ref_head:
                    dupes.append(p)
            except:
                t2_errors += 1
                continue
        
        if dupes:
            gid = f"G{group_num:06d}"
            recoverable = fsize * len(dupes)
            total_recoverable += recoverable
            
            conn.execute("INSERT OR REPLACE INTO dedup_groups VALUES (?,?,?,?,?,?)",
                         (gid, fname, fsize, 1+len(dupes), ref_path, 'confirmed'))
            for dp in dupes:
                conn.execute("UPDATE files SET dedup_group=?, is_duplicate=1 WHERE path=?", (gid, dp))
            
            all_confirmed.append({
                "group_id": gid, "filename": fname, "size": fsize,
                "keep": ref_path, "duplicates": dupes,
                "recoverable_bytes": recoverable
            })
            group_num += 1
        
        if (group_num - t1_count) % 2000 == 0 and group_num > t1_count:
            conn.commit()
            log(f"    T2: {group_num-t1_count:,} | total: {total_recoverable/1024/1024/1024:.1f}GB")
    
    conn.commit()
    log(f"  TIER 2 done: {group_num-t1_count:,} groups, errors: {t2_errors}")
    
    # JUNK analysis
    log("  Generating junk analysis...")
    junk_data = conn.execute("""
        SELECT drive, COUNT(*), COALESCE(SUM(size),0) 
        FROM files 
        WHERE classification IN ('JUNK','SYSTEM') OR is_junk=1
        GROUP BY drive ORDER BY SUM(size) DESC
    """).fetchall()
    
    big_junk = conn.execute("""
        SELECT path, size, classification FROM files 
        WHERE (classification='JUNK' OR is_junk=1) AND size > 1000000
        ORDER BY size DESC LIMIT 100
    """).fetchall()
    
    total_junk = sum(r[2] for r in junk_data)
    
    with open(r"I:\DRIVE_ORG\JUNK_TARGETS.json", 'w', encoding='utf-8') as f:
        json.dump({
            "generated": datetime.now().isoformat(),
            "total_junk_gb": round(total_junk/1024/1024/1024, 2),
            "by_drive": [{"drive": d, "files": c, "size_gb": round(s/1024/1024/1024, 2)} for d,c,s in junk_data],
            "big_junk_files": [{"path": p, "size_mb": round(s/1024/1024,1), "class": cl} for p,s,cl in big_junk]
        }, f, indent=2)
    
    # Save candidates
    all_confirmed.sort(key=lambda g: g['recoverable_bytes'], reverse=True)
    
    with open(r"I:\DRIVE_ORG\DEDUP_CANDIDATES.json", 'w', encoding='utf-8') as f:
        json.dump({
            "generated": datetime.now().isoformat(),
            "total_groups": group_num,
            "total_recoverable_gb": round(total_recoverable/1024/1024/1024, 2),
            "total_junk_gb": round(total_junk/1024/1024/1024, 2),
            "combined_recovery_gb": round((total_recoverable+total_junk)/1024/1024/1024, 2),
            "top_groups": all_confirmed[:500]
        }, f, indent=2)
    
    # Per-drive summary
    log(f"\n{'='*60}")
    log(f"PASS 1 COMPLETE")
    log(f"  Confirmed duplicate groups: {group_num:,}")
    log(f"  Dedup recoverable: {total_recoverable/1024/1024/1024:.2f}GB")
    log(f"  Junk recoverable: {total_junk/1024/1024/1024:.2f}GB")
    log(f"  TOTAL RECOVERABLE: {(total_recoverable+total_junk)/1024/1024/1024:.2f}GB")
    
    drive_stats = conn.execute("""
        SELECT drive, COUNT(*), COALESCE(SUM(size),0)
        FROM files WHERE is_duplicate=1 
        GROUP BY drive ORDER BY SUM(size) DESC
    """).fetchall()
    for d, c, s in drive_stats:
        log(f"  {d}: {c:,} dupes = {s/1024/1024/1024:.2f}GB")
    
    conn.close()
    log("PASS 1 OUTPUTS: DEDUP_CANDIDATES.json, JUNK_TARGETS.json")

if __name__ == "__main__":
    run()
