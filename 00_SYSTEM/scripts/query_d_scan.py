import sqlite3
import json

db_path = r"C:\Users\andre\LitigationOS\00_SYSTEM\manifests\drive_D_manifest.db"

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get summary
    print("=" * 80)
    print("DEEP FORENSIC SCAN RESULTS - D: DRIVE (DEPTH 4)")
    print("=" * 80)
    
    # Summary stats
    cursor.execute("SELECT key, value FROM summary")
    summary = dict(cursor.fetchall())
    if summary:
        print("\n📊 SCAN SUMMARY:")
        for k, v in summary.items():
            try:
                val = json.loads(v)
                if isinstance(val, dict):
                    print(f"  {k}: {val}")
                else:
                    print(f"  {k}: {v}")
            except:
                print(f"  {k}: {v}")
    
    # File categories
    print(f"\n📁 FILE CATEGORIES:")
    cursor.execute("SELECT category, COUNT(*) as cnt, SUM(size_bytes)/1048576.0 as size_mb FROM files GROUP BY category ORDER BY cnt DESC")
    for cat, cnt, size_mb in cursor.fetchall():
        print(f"    {cat:25s} {cnt:>7,} files  {size_mb or 0:>10.1f} MB")
    
    # Top legal files
    print(f"\n⚖️  TOP LEGAL-RELEVANT FILES:")
    cursor.execute("SELECT path, legal_score, legal_signals FROM files WHERE legal_score > 10 ORDER BY legal_score DESC LIMIT 20")
    legal_rows = cursor.fetchall()
    if legal_rows:
        for path, score, signals in legal_rows:
            print(f"    [{score:3d}] {path}")
            if signals:
                try:
                    sigs = json.loads(signals)
                    print(f"           signals: {sigs}")
                except:
                    print(f"           signals: {signals}")
    else:
        print("    No legal files found")
    
    # Duplicates
    print(f"\n🔁 DUPLICATE DETECTION (by SHA256):")
    cursor.execute('''SELECT sha256_1mb, COUNT(*) as cnt, SUM(size_bytes) as total_size
        FROM files WHERE sha256_1mb IS NOT NULL 
        GROUP BY sha256_1mb HAVING cnt > 1
        ORDER BY total_size DESC LIMIT 15''')
    dupes = cursor.fetchall()
    total_dupe_waste = 0
    if dupes:
        for sha, cnt, tsize in dupes:
            cursor.execute('SELECT path FROM files WHERE sha256_1mb=? LIMIT 3', (sha,))
            paths = [r[0] for r in cursor.fetchall()]
            waste = tsize - (tsize // cnt)
            total_dupe_waste += waste
            print(f"    {cnt}x copies ({tsize/1048576:.1f}MB total, {waste/1048576:.1f}MB wasted)")
            for p in paths:
                print(f"      └─ {p}")
        
        cursor.execute('''SELECT COUNT(*), SUM(size_bytes) FROM (
            SELECT sha256_1mb, COUNT(*) as cnt, SUM(size_bytes) as size_bytes
            FROM files WHERE sha256_1mb IS NOT NULL
            GROUP BY sha256_1mb HAVING cnt > 1)''')
        dupe_groups, dupe_total = cursor.fetchone()
        print(f"\n  Total duplicate groups: {dupe_groups or 0}")
        print(f"  Estimated recoverable space: {(total_dupe_waste/1048576):.1f} MB")
    else:
        print("    No duplicates found")
    
    # Trash/empty
    cursor.execute("SELECT COUNT(*), SUM(size_bytes) FROM files WHERE is_trash=1")
    trash_count, trash_size = cursor.fetchone()
    cursor.execute("SELECT COUNT(*) FROM files WHERE is_empty=1")
    empty_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM files WHERE is_corrupt=1")
    corrupt_count = cursor.fetchone()[0]
    print(f"\n🗑️  CLEANUP TARGETS:")
    print(f"    Trash files:   {trash_count or 0:,} ({(trash_size or 0)/1048576:.1f} MB)")
    print(f"    Empty files:   {empty_count:,}")
    print(f"    Corrupt files: {corrupt_count:,}")
    
    # Projects
    print(f"\n📁 PROJECT STRUCTURES DETECTED:")
    cursor.execute("SELECT root_path, project_type, file_count, total_size_bytes FROM projects ORDER BY total_size_bytes DESC LIMIT 20")
    proj_rows = cursor.fetchall()
    if proj_rows:
        for root, ptype, fcount, psize in proj_rows:
            print(f"    [{ptype:30s}] {root} ({fcount} files, {psize/1048576:.1f}MB)")
    else:
        print("    No projects detected")
    
    # Databases
    print(f"\n💾 DATABASES:")
    cursor.execute("SELECT path, size_bytes FROM files WHERE category='database' ORDER BY size_bytes DESC LIMIT 15")
    db_rows = cursor.fetchall()
    if db_rows:
        for path, size in db_rows:
            print(f"    {size/1048576:>10.1f} MB — {path}")
    else:
        print("    No databases found")
    
    # Largest files
    print(f"\n📏 LARGEST FILES:")
    cursor.execute("SELECT path, size_bytes FROM files ORDER BY size_bytes DESC LIMIT 20")
    for path, size in cursor.fetchall():
        print(f"    {size/1048576:>10.1f} MB — {path}")
    
    conn.close()
    
    print(f"\n{'=' * 80}")
    print(f"  Manifest DB: {db_path}")
    print(f"{'=' * 80}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
