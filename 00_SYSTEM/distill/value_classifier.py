"""
Value Classification Engine — Phase 1.4
Classifies every top-level directory across all drives.
RED=Critical, YELLOW=Valuable, GREEN=Movable, WHITE=Junk
"""
import sqlite3
import sys
import os
import re

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"

# Classification rules
CRITICAL_PATTERNS = [
    r'litigation', r'evidence', r'filing', r'court', r'custody',
    r'legal', r'claims', r'judicial', r'motion', r'order',
    r'exhibit', r'deposition', r'affidavit', r'brief', r'appeal',
    r'03_EVIDENCE', r'06_FILINGS', r'07_RESEARCH', r'04_FINANCIAL',
    r'05_COMMS', r'\.db$', r'\.db-wal$', r'\.db-shm$',
]

VALUABLE_PATTERNS = [
    r'code', r'script', r'agent', r'skill', r'config', r'pipeline',
    r'00_SYSTEM', r'01_INBOX', r'02_QUEUE', r'08_PIPELINE',
    r'09_DATA', r'10_GRAPH', r'11_CODE', r'12_ARCHIVE', r'13_TOOLS',
    r'14_LOGS', r'15_TEMP', r'16_OUTBOX', r'\.github',
    r'autopilot', r'omega', r'neo4j', r'apps', r'distill',
]

MOVABLE_PATTERNS = [
    r'video', r'music', r'picture', r'photo', r'download',
    r'backup', r'archive', r'old', r'media', r'image',
    r'OneDrive', r'Pictures', r'Videos', r'Music', r'Downloads',
    r'3D Objects', r'Saved Games', r'Contacts',
]

JUNK_PATTERNS = [
    r'node_modules', r'__pycache__', r'\.cache', r'\.tmp',
    r'AppData.*Local.*Temp', r'\.vs\b', r'\.vscode.*cache',
    r'npm-cache', r'pip.*cache', r'\.ollama',
    r'Cookies$', r'Recent$', r'SendTo$', r'Templates$',
    r'NTUSER', r'ntuser',
]


def classify_path(path):
    """Classify a path into RED/YELLOW/GREEN/WHITE."""
    name = os.path.basename(path)
    full = path.replace('\\', '/')
    
    for p in CRITICAL_PATTERNS:
        if re.search(p, full, re.IGNORECASE):
            return 'RED', 'CRITICAL'
    for p in VALUABLE_PATTERNS:
        if re.search(p, full, re.IGNORECASE):
            return 'YELLOW', 'VALUABLE'
    for p in JUNK_PATTERNS:
        if re.search(p, full, re.IGNORECASE):
            return 'WHITE', 'JUNK'
    for p in MOVABLE_PATTERNS:
        if re.search(p, full, re.IGNORECASE):
            return 'GREEN', 'MOVABLE'
    
    return 'GREEN', 'MOVABLE'  # default


def classify_all_dirs(conn):
    """Classify top-level directories on every drive."""
    print("Classifying top-level directories...")
    
    # Get drive root paths
    drive_roots = conn.execute("""
        SELECT DISTINCT drive, MIN(path) as sample_path FROM omega_filesystem_map GROUP BY drive
    """).fetchall()
    
    print(f"  Drives found: {[d[0] for d in drive_roots]}")
    
    # For each drive, find unique top-level subdirs
    all_dirs = []
    for drive, sample in drive_roots:
        # Determine root prefix (e.g. C:\Users\andre\LitigationOS for C_LITIGOS)
        # Find common prefix for all paths on this drive
        first_paths = conn.execute(
            "SELECT DISTINCT path FROM omega_filesystem_map WHERE drive = ? LIMIT 100", (drive,)
        ).fetchall()
        
        paths = [p[0] for p in first_paths]
        if not paths:
            continue
        
        # Find root by taking the shortest path
        root = min(paths, key=len)
        # If root has backslash after drive letter, use drive:\
        if len(root) >= 3 and root[1] == ':':
            # Use one level deeper than drive root
            parts = root.split('\\')
            # For C_LITIGOS: root is C:\Users\andre\LitigationOS
            # For D: root is D:\
            pass
        
        # Get top-level dirs within this drive
        rows = conn.execute("""
            SELECT path, COUNT(*) as fc, SUM(size_bytes) as tb
            FROM omega_filesystem_map
            WHERE drive = ? AND depth <= 1
            GROUP BY path
            ORDER BY tb DESC
        """, (drive,)).fetchall()
        
        if not rows:
            # Try depth 2
            rows = conn.execute("""
                SELECT path, COUNT(*) as fc, SUM(size_bytes) as tb
                FROM omega_filesystem_map
                WHERE drive = ?
                GROUP BY path
                ORDER BY tb DESC
                LIMIT 50
            """, (drive,)).fetchall()
        
        for path, fc, tb in rows:
            all_dirs.append((drive, path, fc, tb or 0))
    
    # If depth-based approach doesn't work well, try extracting first subdir from path
    if len(all_dirs) < 20:
        print("  Falling back to path-based extraction...")
        all_dirs = []
        rows = conn.execute("""
            SELECT drive, path, SUM(size_bytes) as total_bytes, COUNT(*) as file_count
            FROM omega_filesystem_map
            WHERE depth BETWEEN 0 AND 2
            GROUP BY drive, path
            ORDER BY total_bytes DESC
            LIMIT 500
        """).fetchall()
        all_dirs = [(r[0], r[1], r[3], r[2] or 0) for r in rows]
    
    print(f"  Found {len(all_dirs)} directory entries to classify")
    
    # Create classification table
    conn.execute("DROP TABLE IF EXISTS omega_value_classification")
    conn.execute("""
        CREATE TABLE omega_value_classification (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            drive TEXT,
            dir_path TEXT,
            color TEXT,
            classification TEXT,
            file_count INTEGER,
            total_bytes INTEGER,
            total_mb REAL
        )
    """)
    
    stats = {'RED': 0, 'YELLOW': 0, 'GREEN': 0, 'WHITE': 0}
    size_stats = {'RED': 0, 'YELLOW': 0, 'GREEN': 0, 'WHITE': 0}
    
    for drive, top_dir, fcount, tbytes in all_dirs:
        color, cls = classify_path(top_dir)
        mb = (tbytes or 0) / 1048576
        
        conn.execute(
            "INSERT INTO omega_value_classification (drive, dir_path, color, classification, file_count, total_bytes, total_mb) VALUES (?,?,?,?,?,?,?)",
            (drive, top_dir, color, cls, fcount, tbytes, round(mb, 2))
        )
        
        stats[color] += 1
        size_stats[color] += tbytes or 0
    
    conn.commit()
    
    print(f"\n  CLASSIFICATION RESULTS:")
    for color, label in [('RED', 'CRITICAL'), ('YELLOW', 'VALUABLE'), ('GREEN', 'MOVABLE'), ('WHITE', 'JUNK')]:
        gb = size_stats[color] / (1024**3)
        emoji = {'RED': '[!]', 'YELLOW': '[V]', 'GREEN': '[M]', 'WHITE': '[J]'}[color]
        print(f"  {emoji} {label:10s}: {stats[color]:>5} dirs, {gb:>8.2f} GB")
    
    total_gb = sum(size_stats.values()) / (1024**3)
    print(f"  {'':10s}  TOTAL: {sum(stats.values()):>5} dirs, {total_gb:>8.2f} GB")
    
    # Show junk candidates for space reclamation
    junk = conn.execute("""
        SELECT dir_path, total_mb, file_count FROM omega_value_classification
        WHERE color = 'WHITE' ORDER BY total_mb DESC LIMIT 15
    """).fetchall()
    
    if junk:
        print(f"\n  TOP JUNK CANDIDATES (reclaimable):")
        for path, mb, fc in junk:
            print(f"    {mb:>8.1f} MB  {fc:>6} files  {path}")
    
    return stats, size_stats


if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)
    stats, sizes = classify_all_dirs(conn)
    conn.close()
    print("\n[DONE] Value classification complete")
