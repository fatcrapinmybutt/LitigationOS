import sqlite3
import json

def explore_db(db_path, db_name):
    print(f"\n{'='*60}")
    print(f"DATABASE: {db_name}")
    print(f"Path: {db_path}")
    print(f"{'='*60}\n")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"TABLES: {len(tables)} tables found\n")
        
        total_rows = 0
        table_info = {}
        
        for table in tables:
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM \{table}\;")
            count = cursor.fetchone()[0]
            total_rows += count
            
            # Get column info
            cursor.execute(f"PRAGMA table_info({table});")
            columns = cursor.fetchall()
            col_names = [col[1] for col in columns]
            
            table_info[table] = {
                'count': count,
                'columns': col_names
            }
            
            print(f"  {table}: {count:,} rows")
            print(f"    Columns: {', '.join(col_names)}")
        
        print(f"\nTOTAL TABLES: {len(tables)}")
        print(f"TOTAL ROWS: {total_rows:,}")
        
        conn.close()
        return table_info
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None

# Explore databases
explore_db(r'G:\_CONVERGENCE_DUPES\LITIGATION_OS__CAPSTONE__Windows_fdd648c1.db', 
           'CAPSTONE DB (fdd648c1)')
explore_db(r'G:\_CONVERGENCE_DUPES\cache_1773489732.sqlite', 
           'CACHE DB (1773489732)')
