import sqlite3
import json

db_path = r"C:\Users\andre\LitigationOS\00_SYSTEM\manifests\drive_C_manifest.db"

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("=" * 90)
    print("DEEP FORENSIC SCAN RESULTS - C: DRIVE (Depth 6)")
    print("SCAN COMPLETED SUCCESSFULLY")
    print("=" * 90)
    
    # ─── FILE CATEGORIES ───
    print("\n" + "─" * 90)
    print("FILE CATEGORIES BREAKDOWN")
    print("─" * 90)
    cursor.execute("SELECT category, COUNT(*) as count, SUM(size_bytes) as total_size FROM files GROUP BY category ORDER BY count DESC")
    total_files = 0
    total_size = 0
    for cat, count, size in cursor.fetchall():
        total_files += count
        total_size += size if size else 0
        size_mb = size / (1024*1024) if size else 0
        print(f"  {cat:30} {count:8} files   {size_mb:12.2f} MB")
    total_gb = total_size / (1024*1024*1024)
    print(f"  {'─' * 47}")
    print(f"  {'TOTAL':30} {total_files:8} files   {total_gb:12.2f} GB")
    
    # ─── LEGAL DOCUMENTS ───
    print("\n" + "─" * 90)
    print("LEGAL DOCUMENTS (Top 50 by Legal Score)")
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
            try:
                sig_list = json.loads(signals)
                print(f"       Signals: {', '.join(sig_list)}")
            except:
                print(f"       Signals: {signals}")
    print(f"\nTotal legal documents found: {legal_count}")
    
    # ─── DUPLICATES ───
    print("\n" + "─" * 90)
    print("DUPLICATE FILES (By SHA256 Hash, First 1MB)")
    print("─" * 90)
    cursor.execute("""
        SELECT sha256_1mb, COUNT(*) as count, SUM(size_bytes) as total_size
        FROM files 
        WHERE sha256_1mb IS NOT NULL
        GROUP BY sha256_1mb
        HAVING count > 1
        ORDER BY total_size DESC
        LIMIT 20
    """)
    dup_count = 0
    total_dup_size = 0
    for sha, count, size in cursor.fetchall():
        dup_count += 1
        total_dup_size += size if size else 0
        size_mb = size / (1024*1024) if size else 0
        print(f"\n  Hash: {sha[:16]}...")
        print(f"  Copies: {count}   Total Size: {size_mb:12.2f} MB")
        # Show first 3 files
        cursor.execute("""
            SELECT path FROM files WHERE sha256_1mb = ? ORDER BY path LIMIT 3
        """, (sha,))
        for (fpath,) in cursor.fetchall():
            print(f"    - {fpath}")
    total_dup_gb = total_dup_size / (1024*1024*1024)
    print(f"\nTotal duplicate sets found: {dup_count}")
    print(f"Total size of duplicates: {total_dup_gb:.2f} GB")
    
    # ─── TRASH & CORRUPT ───
    print("\n" + "─" * 90)
    print("TRASH, EMPTY & CORRUPT FILES")
    print("─" * 90)
    cursor.execute("""
        SELECT category, COUNT(*) as count FROM files 
        WHERE category IN ('trash', 'temp_trash', 'empty', 'corrupt')
        GROUP BY category
    """)
    for cat, count in cursor.fetchall():
        print(f"  {cat}: {count} files")
    
    # ─── DATABASES ───
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
    print(f"\nTotal databases: {db_count}")
    
    # ─── PROJECTS ───
    print("\n" + "─" * 90)
    print("PROJECTS DETECTED")
    print("─" * 90)
    cursor.execute("""
        SELECT project_type, COUNT(*) as count, SUM(total_size_bytes) as total_size
        FROM projects 
        GROUP BY project_type
        ORDER BY total_size DESC
    """)
    for ptype, pcount, psize in cursor.fetchall():
        size_mb = psize / (1024*1024) if psize else 0
        print(f"  {ptype:30} {pcount:3} projects   {size_mb:12.2f} MB")
    
    # Show specific project details
    print("\n  Project Details:")
    cursor.execute("""
        SELECT project_type, root_path, file_count, total_size_bytes
        FROM projects 
        ORDER BY total_size_bytes DESC
        LIMIT 20
    """)
    for ptype, rpath, fcount, psize in cursor.fetchall():
        size_mb = psize / (1024*1024)
        print(f"    [{ptype:20}] {fcount:4} files  {size_mb:8.2f} MB  {rpath}")
    
    # ─── LARGEST DIRECTORIES ───
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
    
    # ─── SUMMARY STATS ───
    print("\n" + "─" * 90)
    print("SCAN SUMMARY")
    print("─" * 90)
    cursor.execute("SELECT COUNT(*) FROM files")
    file_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM directories")
    dir_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM projects")
    proj_count = cursor.fetchone()[0]
    
    print(f"  Total Files Scanned:        {file_count:,}")
    print(f"  Total Directories:          {dir_count:,}")
    print(f"  Total Projects Detected:    {proj_count:,}")
    print(f"  Total Size:                 {total_gb:.2f} GB")
    print(f"  Duplicate Size (wasted):    {total_dup_gb:.2f} GB")
    print(f"  Legal Documents Found:      {legal_count}")
    print(f"  Databases:                  {db_count}")
    
    conn.close()
    print("\n" + "=" * 90)
    print("END OF SCAN RESULTS")
    print("=" * 90)
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
