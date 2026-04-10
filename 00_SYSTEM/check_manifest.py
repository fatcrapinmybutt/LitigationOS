import sqlite3
import os
from pathlib import Path

# Database path
db_path = r'C:\Users\andre\LitigationOS\00_SYSTEM\manifests\drive_I_manifest.db'

# Verify database exists
if not os.path.exists(db_path):
    print(f"ERROR: Database not found at {db_path}")
    exit(1)

print(f"Connecting to: {db_path}\n")

try:
    # Connect with WAL mode and busy timeout
    conn = sqlite3.connect(db_path)
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA busy_timeout=60000')
    cursor = conn.cursor()
    
    print("=" * 80)
    print("QUERY 1: Total files by scan_status")
    print("=" * 80)
    query1 = """
    SELECT scan_status, COUNT(*), printf('%.1f GB', SUM(size_bytes)/1024.0/1024/1024) 
    FROM files GROUP BY scan_status
    """
    cursor.execute(query1)
    results = cursor.fetchall()
    for row in results:
        print(f"  {row[0]:15} | Count: {row[1]:>12} | Size: {row[2]:>15}")
    print()
    
    print("=" * 80)
    print("QUERY 2: Variant files - how many have hashes?")
    print("=" * 80)
    query2 = """
    SELECT 
      COUNT(*) as total_variants,
      SUM(CASE WHEN sha256_1mb IS NOT NULL THEN 1 ELSE 0 END) as with_hash,
      SUM(CASE WHEN sha256_1mb IS NULL THEN 1 ELSE 0 END) as without_hash
    FROM files 
    WHERE is_litos_variant = 1 AND scan_status != 'deleted'
    """
    cursor.execute(query2)
    result = cursor.fetchone()
    print(f"  Total Variants:   {result[0]:>10}")
    print(f"  With Hash:        {result[1]:>10}")
    print(f"  Without Hash:     {result[2]:>10}")
    print()
    
    print("=" * 80)
    print("QUERY 3: Category distribution (top 15)")
    print("=" * 80)
    query3 = """
    SELECT category, COUNT(*) as cnt, printf('%.1f GB', SUM(size_bytes)/1024.0/1024/1024) as size 
    FROM files WHERE scan_status != 'deleted' 
    GROUP BY category ORDER BY cnt DESC LIMIT 15
    """
    cursor.execute(query3)
    results = cursor.fetchall()
    for row in results:
        print(f"  {row[0]:30} | Count: {row[1]:>10} | Size: {row[2]:>15}")
    print()
    
    print("=" * 80)
    print("QUERY 4: Legal score distribution")
    print("=" * 80)
    query4 = """
    SELECT 
      CASE WHEN legal_score = 0 THEN '0 (none)' 
           WHEN legal_score < 20 THEN '1-19 (low)' 
           WHEN legal_score < 50 THEN '20-49 (medium)' 
           ELSE '50+ (high)' END as range,
      COUNT(*) 
    FROM files WHERE scan_status != 'deleted' 
    GROUP BY range ORDER BY range
    """
    cursor.execute(query4)
    results = cursor.fetchall()
    for row in results:
        print(f"  {row[0]:25} | Count: {row[1]:>12}")
    print()
    
    print("=" * 80)
    print("QUERY 5: Top 10 directories by file count")
    print("=" * 80)
    query5 = """
    SELECT parent_dir, COUNT(*) as cnt FROM files WHERE scan_status != 'deleted' 
    GROUP BY parent_dir ORDER BY cnt DESC LIMIT 10
    """
    cursor.execute(query5)
    results = cursor.fetchall()
    for row in results:
        print(f"  Count: {row[1]:>10} | {row[0]}")
    print()
    
    print("=" * 80)
    print("QUERY 6: Trash breakdown")
    print("=" * 80)
    query6 = """
    SELECT is_trash, COUNT(*), printf('%.1f GB', SUM(size_bytes)/1024.0/1024/1024) 
    FROM files WHERE scan_status != 'deleted' GROUP BY is_trash
    """
    cursor.execute(query6)
    results = cursor.fetchall()
    for row in results:
        is_trash_label = "Trash" if row[0] else "Not Trash"
        print(f"  {is_trash_label:15} | Count: {row[1]:>12} | Size: {row[2]:>15}")
    print()
    
    print("=" * 80)
    print("ALL QUERIES COMPLETED SUCCESSFULLY")
    print("=" * 80)
    
    conn.close()
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
