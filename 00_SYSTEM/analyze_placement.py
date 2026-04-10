"""
Consolidation Intelligence — Analyze what's where, what's duplicated,
and where each file OPTIMALLY belongs.

Questions to answer:
1. What drives have duplicates of C:\ repo content? (remove them)
2. What's unique on external drives that C:\ is missing? (absorb or archive)
3. For each unique file — what's the optimal home? C:\repo subfolder or J:\archive?
4. Does a similar file already exist that this enhances/expands?
"""
import sqlite3, os, json
from pathlib import Path
from collections import defaultdict

DB = Path(r"C:\Users\andre\LitigationOS\litigation_context.db")
STATE = Path(r"D:\LitigationOS_tmp\consolidation_state.db")

def get_conn(path, readonly=False):
    uri = f"file:///{path}?mode=ro" if readonly else str(path)
    c = sqlite3.connect(uri, uri=readonly)
    c.execute("PRAGMA busy_timeout=30000")
    c.execute("PRAGMA journal_mode=WAL")
    return c

def section(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")

# ============================================================
# STEP 1: What's on each drive in the litigation DB?
# ============================================================
section("STEP 1: DRIVE FOOTPRINT IN LITIGATION DB")

conn = get_conn(DB, readonly=True)

# Check which tables have path columns
path_tables = {}
for tbl in ["evidence_quotes", "documents", "file_inventory", 
            "impeachment_matrix", "authority_chains_v2", "police_reports",
            "timeline_events", "md_sections"]:
    try:
        cols = [r[1] for r in conn.execute(f"PRAGMA table_info({tbl})").fetchall()]
        path_col = None
        for c in cols:
            if c in ("source_file", "file_path", "source_path", "source_document", "file_source"):
                path_col = c
                break
        if path_col:
            path_tables[tbl] = path_col
    except:
        pass

print(f"\nTables with file path columns: {len(path_tables)}")
for tbl, col in path_tables.items():
    print(f"  {tbl:30s} -> {col}")

# For each table, count rows by drive letter
print(f"\n--- Rows by drive letter per table ---")
drive_map = defaultdict(lambda: defaultdict(int))

for tbl, col in path_tables.items():
    try:
        rows = conn.execute(f"""
            SELECT 
                CASE 
                    WHEN {col} LIKE 'C:%' OR {col} LIKE 'c:%' THEN 'C:'
                    WHEN {col} LIKE 'D:%' OR {col} LIKE 'd:%' THEN 'D:'
                    WHEN {col} LIKE 'F:%' OR {col} LIKE 'f:%' THEN 'F:'
                    WHEN {col} LIKE 'G:%' OR {col} LIKE 'g:%' THEN 'G:'
                    WHEN {col} LIKE 'H:%' OR {col} LIKE 'h:%' THEN 'H:'
                    WHEN {col} LIKE 'I:%' OR {col} LIKE 'i:%' THEN 'I:'
                    WHEN {col} LIKE 'J:%' OR {col} LIKE 'j:%' THEN 'J:'
                    ELSE 'OTHER'
                END as drive,
                COUNT(*) as cnt
            FROM {tbl}
            WHERE {col} IS NOT NULL AND {col} != ''
            GROUP BY drive
            ORDER BY cnt DESC
        """).fetchall()
        
        print(f"\n  {tbl} ({col}):")
        for drive, cnt in rows:
            print(f"    {drive}: {cnt:>10,}")
            drive_map[drive][tbl] = cnt
    except Exception as e:
        print(f"  {tbl}: ERROR - {e}")

# ============================================================
# STEP 2: What external-drive content is UNIQUE vs DUPLICATE?
# ============================================================
section("STEP 2: EXTERNAL DRIVE CONTENT ANALYSIS")

# Use the v1 state DB to understand what's on external drives
if STATE.exists():
    sconn = get_conn(STATE, readonly=True)
    
    # What file types are on each drive?
    print("\n--- File types per external drive ---")
    for drive in ["D:", "F:", "G:", "I:"]:
        rows = sconn.execute("""
            SELECT type_category, COUNT(*) as n, 
                   ROUND(SUM(file_size)/1048576.0, 1) as mb
            FROM file_inventory
            WHERE source_drive = ?
            GROUP BY type_category
            ORDER BY mb DESC
        """, (drive + "\\",)).fetchall()
        
        total = sum(r[1] for r in rows)
        total_mb = sum(r[2] or 0 for r in rows)
        print(f"\n  {drive} ({total:,} files, {total_mb:,.0f} MB):")
        for cat, n, mb in rows:
            print(f"    {cat or 'UNKNOWN':15s}: {n:>6,} files  {mb or 0:>8.1f} MB")

    # Hash-based exact duplicates across drives
    print("\n--- Exact hash duplicates (same xxhash across different drives) ---")
    dupes = sconn.execute("""
        SELECT xxhash, COUNT(DISTINCT source_drive) as drive_count,
               COUNT(*) as total_copies,
               GROUP_CONCAT(DISTINCT source_drive) as drives,
               MIN(file_name) as sample_name,
               MIN(file_size) as size
        FROM file_inventory
        WHERE xxhash IS NOT NULL AND xxhash != '' AND xxhash NOT LIKE 'ERROR%'
        GROUP BY xxhash
        HAVING COUNT(DISTINCT source_drive) > 1
        ORDER BY size DESC
        LIMIT 30
    """).fetchall()
    
    print(f"\n  Files found on MULTIPLE drives: {len(dupes)} unique hashes")
    cross_drive_waste = 0
    for h, dc, tc, drives, name, sz in dupes[:15]:
        waste = sz * (tc - 1)
        cross_drive_waste += waste
        print(f"    {name[:50]:50s} {sz/1048576:>8.1f} MB  x{tc} on {drives}")
    
    if len(dupes) > 15:
        # Sum the rest
        for h, dc, tc, drives, name, sz in dupes[15:]:
            cross_drive_waste += sz * (tc - 1)
    
    # Full cross-drive dupe count
    full_dupes = sconn.execute("""
        SELECT COUNT(*) FROM (
            SELECT xxhash FROM file_inventory
            WHERE xxhash IS NOT NULL AND xxhash != '' AND xxhash NOT LIKE 'ERROR%'
            GROUP BY xxhash
            HAVING COUNT(DISTINCT source_drive) > 1
        )
    """).fetchone()[0]
    
    full_waste = sconn.execute("""
        SELECT SUM(waste) FROM (
            SELECT xxhash, SUM(file_size) - MIN(file_size) as waste
            FROM file_inventory
            WHERE xxhash IS NOT NULL AND xxhash != '' AND xxhash NOT LIKE 'ERROR%'
            GROUP BY xxhash
            HAVING COUNT(*) > 1
        )
    """).fetchone()[0] or 0
    
    print(f"\n  TOTAL cross-drive duplicate groups: {full_dupes:,}")
    print(f"  TOTAL wasted space from ALL dupes: {full_waste/1073741824:.2f} GB")

    # ============================================================
    # STEP 3: What's UNIQUE on external drives (not on C:\)?
    # ============================================================
    section("STEP 3: UNIQUE FILES ON EXTERNAL DRIVES")
    
    # Files that exist ONLY on external drives (no C:\ copy by hash)
    for drive in ["D:", "F:", "G:", "I:"]:
        unique = sconn.execute("""
            SELECT COUNT(*), ROUND(SUM(file_size)/1073741824.0, 2)
            FROM file_inventory
            WHERE source_drive = ?
            AND xxhash IS NOT NULL AND xxhash != '' AND xxhash NOT LIKE 'ERROR%'
            AND xxhash NOT IN (
                SELECT xxhash FROM file_inventory 
                WHERE source_drive = 'C:\\'
                AND xxhash IS NOT NULL AND xxhash != '' AND xxhash NOT LIKE 'ERROR%'
            )
        """, (drive + "\\",)).fetchall()
        
        all_count = sconn.execute(
            "SELECT COUNT(*) FROM file_inventory WHERE source_drive = ?",
            (drive + "\\",)
        ).fetchone()[0]
        
        u_count, u_gb = unique[0]
        u_gb = u_gb or 0
        print(f"\n  {drive}: {u_count:,} unique files ({u_gb:.2f} GB) out of {all_count:,} total")
        
        # Breakdown by type
        by_type = sconn.execute("""
            SELECT type_category, COUNT(*) as n, 
                   ROUND(SUM(file_size)/1048576.0, 1) as mb
            FROM file_inventory
            WHERE source_drive = ?
            AND xxhash IS NOT NULL AND xxhash != '' AND xxhash NOT LIKE 'ERROR%'
            AND xxhash NOT IN (
                SELECT xxhash FROM file_inventory 
                WHERE source_drive = 'C:\\'
                AND xxhash IS NOT NULL AND xxhash != '' AND xxhash NOT LIKE 'ERROR%'
            )
            GROUP BY type_category ORDER BY mb DESC
        """, (drive + "\\",)).fetchall()
        
        for cat, n, mb in by_type:
            print(f"    {cat or 'UNKNOWN':15s}: {n:>6,} files  {mb or 0:>8.1f} MB")
    
    # ============================================================
    # STEP 4: What's already on J:\?
    # ============================================================
    section("STEP 4: J:\\ CURRENT STATE")
    
    # Check J:\ directly
    j_root = Path("J:\\")
    if j_root.exists():
        print("\n  Top-level directories on J:\\:")
        try:
            for item in sorted(j_root.iterdir()):
                if item.is_dir():
                    # Quick count
                    try:
                        count = sum(1 for _ in item.rglob("*") if _.is_file())
                        size = sum(f.stat().st_size for f in item.rglob("*") if f.is_file())
                        print(f"    {item.name:40s}  {count:>6,} files  {size/1073741824:.2f} GB")
                    except:
                        print(f"    {item.name:40s}  (scan error)")
                elif item.is_file():
                    print(f"    {item.name:40s}  {item.stat().st_size/1048576:.1f} MB")
        except Exception as e:
            print(f"  Error scanning J:\\: {e}")
    
    import shutil
    try:
        total, used, free = shutil.disk_usage("J:\\")
        print(f"\n  J:\\ capacity: {total/1073741824:.0f} GB total, {used/1073741824:.0f} GB used, {free/1073741824:.0f} GB free")
    except:
        pass

    # ============================================================
    # STEP 5: DECISION MATRIX — Where does each category go?
    # ============================================================
    section("STEP 5: PLACEMENT DECISION MATRIX")
    
    print("""
    PRINCIPLE: C:\\ is the active workspace. J:\\ is deep archive.
    
    DECISION RULES:
    1. If file already exists on C:\\ (by hash) -> DELETE external copy
    2. If file is evidence/legal doc NOT on C:\\ -> ABSORB into C:\\repo structure
       (01_EVIDENCE, 02_AUTHORITY, 03_COURT, etc.)
    3. If file is large media (video, audio, raw images) -> J:\\ARCHIVE
    4. If file is a database backup/snapshot -> J:\\DB_ARCHIVE  
    5. If file is a tool/script/code -> CHECK if useful, else J:\\CODE_ARCHIVE
    6. NEVER keep redundant copies across multiple drives
    """)
    
    sconn.close()

conn.close()
print("\n[DONE] Analysis complete. Review decisions above.")
