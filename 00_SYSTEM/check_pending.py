import sqlite3
conn = sqlite3.connect(r'D:\LitigationOS_tmp\consolidation_state.db')
cursor = conn.cursor()

print("Files by copy_status and xxhash NULL status:")
print("-" * 80)
cursor.execute("""
    SELECT 
        copy_status,
        CASE WHEN xxhash IS NULL THEN 'NULL' 
             WHEN xxhash = '' THEN 'EMPTY' 
             WHEN xxhash LIKE 'ERROR%' THEN 'ERROR' 
             WHEN xxhash = 'EMPTY_FILE' THEN 'EMPTY_FILE'
             ELSE 'VALID' 
        END as hash_status,
        COUNT(*) as count
    FROM file_inventory
    GROUP BY copy_status, 
             CASE WHEN xxhash IS NULL THEN 'NULL' 
                  WHEN xxhash = '' THEN 'EMPTY' 
                  WHEN xxhash LIKE 'ERROR%' THEN 'ERROR' 
                  WHEN xxhash = 'EMPTY_FILE' THEN 'EMPTY_FILE'
                  ELSE 'VALID' 
             END
    ORDER BY copy_status, hash_status
""")

for row in cursor.fetchall():
    print(f"  {row[0]:20s} | {row[1]:12s} | {row[2]:8d}")

print()
print("Sample pending files with VALID hashes:")
print("-" * 80)
cursor.execute("""
    SELECT id, source_drive, source_path, xxhash
    FROM file_inventory
    WHERE copy_status = 'pending'
    AND xxhash IS NOT NULL
    AND xxhash != ''
    AND NOT xxhash LIKE 'ERROR%'
    AND xxhash != 'EMPTY_FILE'
    LIMIT 5
""")

for row in cursor.fetchall():
    print(f"  {row}")

conn.close()
