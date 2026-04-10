import sqlite3
import os

db_dir = r"C:\Users\andre\LitigationOS\00_SYSTEM\brains"
db_files = [f for f in os.listdir(db_dir) if f.endswith('.db')]

for db_file in sorted(db_files):
    db_path = os.path.join(db_dir, db_file)
    
    print(f"\n{'='*100}")
    print(f"DATABASE: {db_file}")
    print(f"{'='*100}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()
        
        table_list = []
        for (table_name,) in tables:
            if not any(x in table_name for x in ['_fts_', '_fts']):
                table_list.append(table_name)
        
        if not table_list:
            print("  [No tables]")
        else:
            for table_name in table_list:
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                
                print(f"\n  TABLE: {table_name} ({len(columns)} columns)")
                print(f"  {'-'*96}")
                for cid, name, col_type, notnull, default, pk in columns:
                    pk_mark = " [PK]" if pk else ""
                    notnull_mark = " NOT NULL" if notnull else ""
                    default_mark = f" = {default}" if default else ""
                    print(f"    {cid:2d}. {name:<35} {col_type:<15}{pk_mark}{notnull_mark}{default_mark}")
        
        conn.close()
    except Exception as e:
        print(f"  ERROR: {e}")

print(f"\n{'='*100}")
