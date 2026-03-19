import sqlite3
import json

db_path = r"C:\Users\andre\LitigationOS\00_SYSTEM\manifests\drive_H_manifest.db"

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [t[0] for t in cursor.fetchall()]
    print("=" * 80)
    print("DEEP FORENSIC SCAN RESULTS - H: DRIVE")
    print("=" * 80)
    print(f"\nDatabase Tables Found: {tables}\n")
    
    # Get summary stats if they exist
    for table_name in tables:
        print(f"\n{'─' * 80}")
        print(f"TABLE: {table_name.upper()}")
        print(f"{'─' * 80}")
        
        cursor.execute(f"SELECT COUNT(*) FROM [{table_name}]")
        count = cursor.fetchone()[0]
        print(f"Total Records: {count}\n")
        
        cursor.execute(f"PRAGMA table_info([{table_name}])")
        cols = cursor.fetchall()
        col_names = [col[1] for col in cols]
        print(f"Columns: {col_names}\n")
        
        # Get all rows
        cursor.execute(f"SELECT * FROM [{table_name}] LIMIT 200")
        rows = cursor.fetchall()
        
        if table_name == 'summary':
            print("SUMMARY DATA:")
            for row in rows:
                print(row)
        elif table_name == 'files_by_category':
            print("FILES BY CATEGORY:")
            for row in rows:
                print(f"  {row}")
        elif table_name == 'duplicates':
            print("DUPLICATES:")
            for i, row in enumerate(rows[:50]):
                print(f"  {row}")
            if len(rows) > 50:
                print(f"  ... and {len(rows) - 50} more duplicate groups")
        elif table_name == 'legal_files':
            print("LEGAL FILES:")
            for i, row in enumerate(rows[:50]):
                print(f"  {row}")
            if len(rows) > 50:
                print(f"  ... and {len(rows) - 50} more legal files")
        elif table_name == 'projects':
            print("PROJECTS DETECTED:")
            for row in rows:
                print(f"  {row}")
        elif table_name == 'databases':
            print("DATABASES FOUND:")
            for row in rows:
                print(f"  {row}")
        else:
            for row in rows:
                print(row)
            if len(rows) > len(rows):
                total = cursor.execute(f"SELECT COUNT(*) FROM [{table_name}]").fetchone()[0]
                print(f"... showing {len(rows)} of {total} rows")
    
    conn.close()
    print("\n" + "=" * 80)
    print("END OF SCAN RESULTS")
    print("=" * 80)
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
