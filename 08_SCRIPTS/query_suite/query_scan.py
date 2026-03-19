import sqlite3
import json

db_path = r"C:\Users\andre\LitigationOS\00_SYSTEM\manifests\drive_C_manifest.db"

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [t[0] for t in cursor.fetchall()]
    
    print("=" * 90)
    print("DEEP FORENSIC SCAN RESULTS - C: DRIVE (Depth 6)")
    print("=" * 90)
    
    # Get summary if available
    if 'summary' in tables:
        print("\n" + "─" * 90)
        print("SUMMARY STATISTICS")
        print("─" * 90)
        cursor.execute("SELECT * FROM summary")
        cols = [desc[0] for desc in cursor.description]
        for row in cursor.fetchall():
            for col, val in zip(cols, row):
                print(f"  {col}: {val}")
    
    # Get file categories breakdown
    if 'files' in tables:
        print("\n" + "─" * 90)
        print("FILE CATEGORIES")
        print("─" * 90)
        cursor.execute("SELECT category, COUNT(*) as count, SUM(size_bytes) as total_size FROM files GROUP BY category ORDER BY count DESC")
        for cat, count, size in cursor.fetchall():
            size_mb = size / (1024*1024) if size else 0
            print(f"  {cat:30} {count:8} files   {size_mb:12.2f} MB")
    
    # Get legal documents
    if 'files' in tables:
        print("\n" + "─" * 90)
        print("LEGAL DOCUMENTS (score > 0)")
        print("─" * 90)
        cursor.execute("""
            SELECT path, legal_score, legal_signals 
            FROM files 
            WHERE legal_score > 0 
            ORDER BY legal_score DESC 
            LIMIT 50
        """)
        legal_count = 0
        for path, score, signals in cursor.fetchall():
            legal_count += 1
            print(f"  [{score:3}] {path}")
            if signals:
                print(f"       Signals: {signals}")
        if legal_count == 0:
            print("  (No legal documents found)")
    
    # Get duplicate files (by SHA256)
    if 'files' in tables:
        print("\n" + "─" * 90)
        print("DUPLICATE FILES (same SHA256, 1MB sample)")
        print("─" * 90)
        cursor.execute("""
            SELECT sha256_1mb, COUNT(*) as count, SUM(size_bytes) as total_size
            FROM files 
            WHERE sha256_1mb IS NOT NULL
            GROUP BY sha256_1mb
            HAVING count > 1
            ORDER BY total_size DESC
            LIMIT 30
        """)
        dup_count = 0
        for sha, count, size in cursor.fetchall():
            dup_count += 1
            size_mb = size / (1024*1024) if size else 0
            print(f"\n  Hash: {sha[:16]}...")
            print(f"  Copies: {count}   Total Size: {size_mb:12.2f} MB")
            # Show the files
            cursor.execute("""
                SELECT path FROM files WHERE sha256_1mb = ? ORDER BY path
            """, (sha,))
            for (fpath,) in cursor.fetchall():
                print(f"    - {fpath}")
        if dup_count == 0:
            print("  (No duplicates found)")
    
    # Get trash/corrupt files
    if 'files' in tables:
        print("\n" + "─" * 90)
        print("TRASH & CORRUPT FILES")
        print("─" * 90)
        cursor.execute("""
            SELECT category, COUNT(*) as count FROM files 
            WHERE category IN ('trash', 'temp_trash', 'empty', 'corrupt')
            GROUP BY category
        """)
        for cat, count in cursor.fetchall():
            print(f"  {cat}: {count} files")
    
    # Get projects detected
    if 'projects' in tables:
        print("\n" + "─" * 90)
        print("PROJECTS DETECTED")
        print("─" * 90)
        cursor.execute("""
            SELECT project_type, path, file_count FROM projects 
            ORDER BY project_type, path
        """)
        for ptype, ppath, pcount in cursor.fetchall():
            print(f"  [{ptype:25}] {ppath:50} ({pcount} files)")
    
    # Get databases
    if 'files' in tables:
        print("\n" + "─" * 90)
        print("DATABASES FOUND")
        print("─" * 90)
        cursor.execute("""
            SELECT path, size_bytes FROM files 
            WHERE category = 'database'
            ORDER BY size_bytes DESC
        """)
        db_count = 0
        for fpath, size in cursor.fetchall():
            db_count += 1
            size_mb = size / (1024*1024)
            print(f"  {size_mb:10.2f} MB  {fpath}")
        if db_count == 0:
            print("  (No databases found)")
    
    # Get directory statistics
    if 'directories' in tables:
        print("\n" + "─" * 90)
        print("TOP 30 LARGEST DIRECTORIES")
        print("─" * 90)
        cursor.execute("""
            SELECT path, file_count, total_size_bytes 
            FROM directories 
            ORDER BY total_size_bytes DESC 
            LIMIT 30
        """)
        for dpath, fcount, dsize in cursor.fetchall():
            size_gb = dsize / (1024*1024*1024) if dsize else 0
            print(f"  {size_gb:8.2f} GB  [{fcount:6} files]  {dpath}")
    
    conn.close()
    print("\n" + "=" * 90)
    print("END OF SCAN RESULTS")
    print("=" * 90)
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
