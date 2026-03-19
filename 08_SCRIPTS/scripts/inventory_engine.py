#!/usr/bin/env python3
"""
DRIVE INVENTORY + DEDUP ENGINE
Scans all drives, classifies files, detects duplicates by content peek.
"""
import sqlite3, os, json, time, sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict

DB_PATH = r"I:\DRIVE_ORG\drive_inventory.db"
LOG_PATH = r"I:\DRIVE_ORG\operations.log"
DEDUP_CANDIDATES_PATH = r"I:\DRIVE_ORG\DEDUP_CANDIDATES.json"
JUNK_TARGETS_PATH = r"I:\DRIVE_ORG\JUNK_TARGETS.json"

# Classification rules
LITIGATION_DIRS = {'01_case_files','02_evidence','03_authorities','04_court_filings',
                   '05_filings','06_timelines','07_communications','08_financial',
                   'court','evidence','legal','filings','pleadings','exhibits',
                   'drafts','authorities','litigationos_delta99'}
JUNK_EXTENSIONS = {'.exe','.dll','.sys','.msi','.cab','.tmp','.log','.pdb',
                   '.obj','.lib','.exp','.ilk','.cache','.nupkg','.whl'}
EVIDENCE_EXTENSIONS = {'.pdf','.png','.jpg','.jpeg','.tiff','.bmp','.gif','.mp3','.mp4','.wav','.mov'}
DB_EXTENSIONS = {'.db','.sqlite','.sqlite3'}
JUNK_FILENAMES = {'windows.db','windows-gather.db','windows-usn.db','thumbs.db',
                  'desktop.ini','.ds_store','ntuser.dat'}

SCAN_TARGETS = [
    (r"C:\Users\andre\LitigationOS", "C_LitigationOS"),
    (r"D:\\", "D"),
    (r"F:\\", "F"),
    (r"G:\\", "G"),
    (r"H:\\", "H"),
    (r"I:\\", "I"),
]

def log(msg):
    ts = datetime.now().isoformat()
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_PATH, 'a', encoding='utf-8') as f:
        f.write(line + '\n')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("""CREATE TABLE IF NOT EXISTS files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        drive TEXT, path TEXT UNIQUE, filename TEXT, extension TEXT,
        size INTEGER, modified TEXT, classification TEXT,
        dedup_group TEXT, is_duplicate INTEGER DEFAULT 0,
        is_junk INTEGER DEFAULT 0, notes TEXT
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS dedup_groups (
        group_id TEXT PRIMARY KEY,
        filename TEXT, size INTEGER, file_count INTEGER,
        keep_path TEXT, status TEXT DEFAULT 'pending'
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS scan_progress (
        drive TEXT PRIMARY KEY, status TEXT, files_scanned INTEGER,
        started TEXT, finished TEXT
    )""")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_files_namesize ON files(filename, size)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_files_class ON files(classification)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_files_drive ON files(drive)")
    conn.commit()
    return conn

def classify_file(path_str, filename, ext, size):
    fn_lower = filename.lower()
    ext_lower = ext.lower()
    path_lower = path_str.lower()
    
    # Junk by filename
    if fn_lower in JUNK_FILENAMES:
        return 'JUNK'
    
    # Junk by extension
    if ext_lower in JUNK_EXTENSIONS:
        return 'JUNK'
    
    # Database
    if ext_lower in DB_EXTENSIONS:
        if fn_lower in JUNK_FILENAMES:
            return 'JUNK'
        return 'DATABASE'
    
    # Windows search DBs are junk even without junk extension match
    if 'windows' in fn_lower and ext_lower == '.db':
        return 'JUNK'
    
    # Check if in litigation directory
    parts = set(p.lower() for p in Path(path_str).parts)
    if parts & LITIGATION_DIRS:
        if ext_lower in EVIDENCE_EXTENSIONS:
            return 'EVIDENCE'
        return 'LITIGATION'
    
    # Evidence by extension in any legal-adjacent path
    if ext_lower in {'.pdf','.docx','.doc'} and any(kw in path_lower for kw in 
        ['litigation','legal','court','evidence','filing','motion','brief','exhibit','authority']):
        return 'LITIGATION'
    
    if ext_lower in EVIDENCE_EXTENSIONS:
        return 'EVIDENCE'
    
    # System files
    if any(kw in path_lower for kw in ['\\windows\\','\\program files','\\appdata\\','node_modules',
                                        '\\__pycache__','\\site-packages','\\venv\\','.git\\']):
        return 'SYSTEM'
    
    return 'UNKNOWN'

def scan_drive(conn, root_path, drive_name):
    """Scan a drive and insert all files into inventory DB."""
    log(f"SCAN START: {drive_name} ({root_path})")
    conn.execute("INSERT OR REPLACE INTO scan_progress VALUES (?,?,?,?,?)",
                (drive_name, 'scanning', 0, datetime.now().isoformat(), None))
    conn.commit()
    
    count = 0
    batch = []
    skip_dirs = {'.git', 'node_modules', '__pycache__', '.venv', 'venv', 
                 '.copilot', 'session-state'}  # Skip Copilot session dirs
    
    for dirpath, dirnames, filenames in os.walk(root_path, topdown=True):
        # Skip certain directories
        dirnames[:] = [d for d in dirnames if d not in skip_dirs]
        
        # Skip DEDUP_ARCHIVE and DRIVE_ORG themselves
        dp_lower = dirpath.lower()
        if 'dedup_archive' in dp_lower or 'drive_org' in dp_lower:
            dirnames.clear()
            continue
        
        for fname in filenames:
            try:
                fpath = os.path.join(dirpath, fname)
                ext = os.path.splitext(fname)[1]
                try:
                    stat = os.stat(fpath)
                    size = stat.st_size
                    mtime = datetime.fromtimestamp(stat.st_mtime).isoformat()
                except (OSError, PermissionError):
                    continue
                
                cls = classify_file(fpath, fname, ext, size)
                is_junk = 1 if cls == 'JUNK' else 0
                
                batch.append((drive_name, fpath, fname, ext.lower(), size, mtime, cls, is_junk))
                count += 1
                
                if len(batch) >= 5000:
                    conn.executemany(
                        "INSERT OR IGNORE INTO files (drive,path,filename,extension,size,modified,classification,is_junk) VALUES (?,?,?,?,?,?,?,?)",
                        batch)
                    conn.commit()
                    batch.clear()
                    if count % 50000 == 0:
                        log(f"  {drive_name}: {count:,} files scanned...")
            except Exception as e:
                continue
    
    if batch:
        conn.executemany(
            "INSERT OR IGNORE INTO files (drive,path,filename,extension,size,modified,classification,is_junk) VALUES (?,?,?,?,?,?,?,?)",
            batch)
        conn.commit()
    
    conn.execute("UPDATE scan_progress SET status='done', files_scanned=?, finished=? WHERE drive=?",
                (count, datetime.now().isoformat(), drive_name))
    conn.commit()
    log(f"SCAN DONE: {drive_name} — {count:,} files")
    return count

def detect_duplicates(conn):
    """Find duplicate groups by filename + size, then content-peek to confirm."""
    log("DEDUP DETECT: Finding candidate groups...")
    
    # Find files with same name+size appearing in 2+ locations
    cursor = conn.execute("""
        SELECT filename, size, COUNT(*) as cnt 
        FROM files 
        WHERE size > 0 AND is_junk = 0
        GROUP BY filename, size 
        HAVING cnt > 1
        ORDER BY size * cnt DESC
    """)
    
    groups = cursor.fetchall()
    log(f"  Found {len(groups)} potential duplicate groups")
    
    dedup_candidates = []
    total_recoverable = 0
    confirmed_groups = 0
    
    # Keep priority: C:\LitigationOS > I:\LitigationOS_Delta99 > I:\ > other
    def keep_priority(path):
        p = path.lower()
        if p.startswith(r'c:\users\andre\litigationos'): return 0
        if 'litigationos_delta99' in p: return 1
        if p.startswith('i:\\'): return 2
        return 3
    
    for fname, fsize, cnt in groups:
        if fsize < 1024:  # Skip files < 1KB
            continue
            
        # Get all paths for this name+size combo
        paths = [r[0] for r in conn.execute(
            "SELECT path FROM files WHERE filename=? AND size=?", (fname, fsize)).fetchall()]
        
        if len(paths) < 2:
            continue
        
        # Content peek: read first 8KB + last 8KB
        confirmed = []
        reference_head = None
        reference_tail = None
        keep_path = None
        
        # Sort by keep priority
        paths.sort(key=keep_priority)
        
        for p in paths:
            try:
                with open(p, 'rb') as f:
                    head = f.read(8192)
                    if fsize > 8192:
                        f.seek(max(0, fsize - 8192))
                        tail = f.read(8192)
                    else:
                        tail = head
                
                if reference_head is None:
                    reference_head = head
                    reference_tail = tail
                    keep_path = p
                    confirmed.append(p)
                elif head == reference_head and tail == reference_tail:
                    confirmed.append(p)
                # else: different content, skip
            except (OSError, PermissionError):
                continue
        
        if len(confirmed) >= 2:
            group_id = f"G{confirmed_groups:06d}"
            dupe_paths = confirmed[1:]  # First one (highest priority) is kept
            recoverable = fsize * len(dupe_paths)
            total_recoverable += recoverable
            
            dedup_candidates.append({
                "group_id": group_id,
                "filename": fname,
                "size": fsize,
                "keep": keep_path,
                "duplicates": dupe_paths,
                "recoverable_bytes": recoverable
            })
            
            # Store in DB
            conn.execute("INSERT OR REPLACE INTO dedup_groups VALUES (?,?,?,?,?,?)",
                        (group_id, fname, fsize, len(confirmed), keep_path, 'confirmed'))
            for dp in dupe_paths:
                conn.execute("UPDATE files SET dedup_group=?, is_duplicate=1 WHERE path=?",
                            (group_id, dp))
            
            confirmed_groups += 1
            
            if confirmed_groups % 1000 == 0:
                conn.commit()
                log(f"  {confirmed_groups} groups confirmed, {total_recoverable/1024/1024/1024:.1f}GB recoverable...")
    
    conn.commit()
    
    # Save candidates
    with open(DEDUP_CANDIDATES_PATH, 'w', encoding='utf-8') as f:
        json.dump({
            "generated": datetime.now().isoformat(),
            "total_groups": confirmed_groups,
            "total_recoverable_gb": round(total_recoverable / 1024/1024/1024, 2),
            "groups": dedup_candidates[:500]  # Top 500 by size
        }, f, indent=2)
    
    log(f"DEDUP DONE: {confirmed_groups} groups, {total_recoverable/1024/1024/1024:.1f}GB recoverable")
    return confirmed_groups, total_recoverable

def identify_junk(conn):
    """Identify junk files and estimate space recovery."""
    log("JUNK ANALYSIS: Identifying non-litigation junk...")
    
    cursor = conn.execute("""
        SELECT drive, classification, COUNT(*) as cnt, SUM(size) as total_size
        FROM files
        WHERE is_junk = 1 OR classification IN ('JUNK', 'SYSTEM')
        GROUP BY drive, classification
        ORDER BY total_size DESC
    """)
    
    junk_summary = []
    total_junk = 0
    for drive, cls, cnt, sz in cursor.fetchall():
        sz = sz or 0
        junk_summary.append({
            "drive": drive, "classification": cls,
            "file_count": cnt, "size_gb": round(sz/1024/1024/1024, 2)
        })
        total_junk += sz
    
    # Also find the big Windows.db files specifically
    big_junk = conn.execute("""
        SELECT path, size FROM files 
        WHERE (filename LIKE 'Windows%' AND extension IN ('.db','.sqlite'))
           OR (filename LIKE '%.exe' AND size > 10000000)
        ORDER BY size DESC LIMIT 50
    """).fetchall()
    
    with open(JUNK_TARGETS_PATH, 'w', encoding='utf-8') as f:
        json.dump({
            "generated": datetime.now().isoformat(),
            "total_junk_gb": round(total_junk/1024/1024/1024, 2),
            "summary": junk_summary,
            "big_junk_files": [{"path": p, "size_mb": round(s/1024/1024,1)} for p,s in big_junk]
        }, f, indent=2)
    
    log(f"JUNK DONE: {total_junk/1024/1024/1024:.1f}GB junk identified")
    return total_junk

def main():
    log("=" * 60)
    log("PASS 1: INVENTORY + CLASSIFY + DEDUP DETECT")
    log("=" * 60)
    
    conn = init_db()
    total = 0
    
    for root_path, drive_name in SCAN_TARGETS:
        if not os.path.exists(root_path):
            log(f"SKIP: {root_path} not found")
            continue
        total += scan_drive(conn, root_path, drive_name)
    
    log(f"\nTOTAL FILES SCANNED: {total:,}")
    
    # Classification summary
    log("\nCLASSIFICATION SUMMARY:")
    for row in conn.execute("""
        SELECT classification, COUNT(*), SUM(size) 
        FROM files GROUP BY classification ORDER BY SUM(size) DESC
    """).fetchall():
        cls, cnt, sz = row
        sz = sz or 0
        log(f"  {cls}: {cnt:,} files, {sz/1024/1024/1024:.2f}GB")
    
    # Detect duplicates
    groups, recoverable = detect_duplicates(conn)
    
    # Identify junk
    junk_size = identify_junk(conn)
    
    log(f"\n{'='*60}")
    log(f"PASS 1 COMPLETE")
    log(f"  Total files: {total:,}")
    log(f"  Duplicate groups: {groups}")
    log(f"  Dedup recoverable: {recoverable/1024/1024/1024:.1f}GB")
    log(f"  Junk identified: {junk_size/1024/1024/1024:.1f}GB")
    log(f"  TOTAL RECOVERABLE: {(recoverable+junk_size)/1024/1024/1024:.1f}GB")
    log(f"{'='*60}")
    
    conn.close()

if __name__ == "__main__":
    main()
