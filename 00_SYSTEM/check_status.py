import sqlite3
conn = sqlite3.connect(r'D:\LitigationOS_tmp\consolidation_state.db')
cursor = conn.cursor()

print("Current file inventory by copy_status:")
print("-" * 80)
cursor.execute("""
    SELECT 
        copy_status,
        COUNT(*) as count,
        COALESCE(SUM(file_size), 0) as total_bytes,
        COUNT(DISTINCT source_drive) as drives
    FROM file_inventory
    GROUP BY copy_status
    ORDER BY copy_status
""")

for row in cursor.fetchall():
    status = row[0] if row[0] else "NULL"
    count = row[1]
    total_bytes = row[2]
    drives = row[3]
    size_str = f"{total_bytes / (1024**3):.1f} GB" if total_bytes >= 1024**3 else f"{total_bytes / (1024**2):.1f} MB"
    print(f"  {status:20s}: {count:8d} files | {size_str:12s} | {drives} drive(s)")

print()
print("Files pending/null processing by drive and hash validity:")
cursor.execute("""
    SELECT 
        source_drive,
        CASE WHEN xxhash IS NULL THEN 'NULL_HASH' 
             WHEN xxhash = '' THEN 'EMPTY_HASH' 
             WHEN xxhash LIKE 'ERROR%' THEN 'ERROR_HASH' 
             WHEN xxhash = 'EMPTY_FILE' THEN 'EMPTY_FILE_HASH'
             ELSE 'VALID_HASH' 
        END as hash_status,
        COUNT(*) as count
    FROM file_inventory
    WHERE copy_status IS NULL OR copy_status = 'pending'
    GROUP BY source_drive, 
             CASE WHEN xxhash IS NULL THEN 'NULL_HASH' 
                  WHEN xxhash = '' THEN 'EMPTY_HASH' 
                  WHEN xxhash LIKE 'ERROR%' THEN 'ERROR_HASH' 
                  WHEN xxhash = 'EMPTY_FILE' THEN 'EMPTY_FILE_HASH'
                  ELSE 'VALID_HASH' 
             END
    ORDER BY source_drive, hash_status
""")

rows = cursor.fetchall()
if rows:
    for row in rows:
        print(f"  {row[0]:6s} | {row[1]:20s} | {row[2]:6d}")
else:
    print("  No pending/null files found")

conn.close()
