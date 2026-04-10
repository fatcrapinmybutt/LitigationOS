import sqlite3
import os

databases = [
    (r"C:\Users\andre\LitigationOS\00_SYSTEM\chromadb_store\chroma.sqlite3", "Chroma Vector Store"),
    (r"C:\Users\andre\LitigationOS\00_SYSTEM\manifests\consolidation_plan.db", "Consolidation Plan"),
    (r"C:\Users\andre\LitigationOS\00_SYSTEM\MEEK234\HIGHSIGNAL\MEEK234_HIGHSIGNAL_DB.sqlite", "MEEK234 Case"),
    (r"C:\Users\andre\LitigationOS\00_SYSTEM\manifests\omega_C_manifest.db", "Omega C Manifest"),
]

for db_path, description in databases:
    if not os.path.exists(db_path):
        print(f"\n[MISSING] {description}")
        print(f"  Path: {db_path}")
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
        
        print(f"\n[{description}]")
        print(f"  File: {db_name}")
        print(f"  Size: {file_size:.2f} MB")
        print(f"  Tables: {table_count}")
        if tables:
            print(f"  Table List:")
            for table in tables[:20]:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM [{table}];")
                    row_count = cursor.fetchone()[0]
                    print(f"    - {table} ({row_count:,} rows)")
                except:
                    print(f"    - {table} (query failed)")
            if len(tables) > 20:
                print(f"    ... and {len(tables)-20} more tables")
        
        # Get database info
        cursor.execute("SELECT page_count * page_size FROM pragma_page_count(), pragma_page_size();")
        db_bytes = cursor.fetchone()[0]
        print(f"  Actual Size: {db_bytes / (1024*1024):.2f} MB")
        
        conn.close()
    except Exception as e:
        print(f"Error reading {description}: {e}")

print("\n=== EXTENDED QUERY COMPLETE ===")
