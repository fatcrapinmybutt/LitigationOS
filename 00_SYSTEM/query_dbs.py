import sqlite3
import os

databases = [
    r"C:\Users\andre\LitigationOS\litigation_context.db",
    r"C:\Users\andre\LitigationOS\00_SYSTEM\pipeline\agents\master_index.db",
    r"C:\Users\andre\LitigationOS\00_SYSTEM\manifests\omega_dedup.db",
    r"C:\Users\andre\LitigationOS\00_SYSTEM\file_catalog.db",
    r"C:\Users\andre\LitigationOS\09_DATA\lane_A_custody.db"
]

for db_path in databases:
    if not os.path.exists(db_path):
        continue
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get table count
        cursor.execute("SELECT count(*) FROM sqlite_master WHERE type='table';")
        table_count = cursor.fetchone()[0]
        
        # Get table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        tables = [row[0] for row in cursor.fetchall()]
        
        db_name = os.path.basename(db_path)
        file_size = os.path.getsize(db_path) / (1024*1024)
        
        print(f"\n[{db_name}]")
        print(f"  Size: {file_size:.2f} MB")
        print(f"  Tables: {table_count}")
        if tables:
            print(f"  Table List:")
            for table in tables[:15]:  # Show first 15 tables
                cursor.execute(f"SELECT COUNT(*) FROM [{table}];")
                row_count = cursor.fetchone()[0]
                print(f"    - {table} ({row_count:,} rows)")
            if len(tables) > 15:
                print(f"    ... and {len(tables)-15} more tables")
        
        conn.close()
    except Exception as e:
        print(f"Error reading {os.path.basename(db_path)}: {e}")

print("\n=== PYTHON QUERY COMPLETE ===")
