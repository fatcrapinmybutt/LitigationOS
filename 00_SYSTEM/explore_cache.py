import sqlite3

def explore_cache_db(db_path, db_name):
    print(f"\n{'='*70}")
    print(f"DATABASE: {db_name}")
    print(f"Path: {db_path}")
    print(f"{'='*70}\n")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"TABLES: {len(tables)} tables found\n")
        
        total_rows = 0
        
        for table in tables:
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM '{table}';")
            count = cursor.fetchone()[0]
            total_rows += count
            
            # Get column info
            cursor.execute(f"PRAGMA table_info('{table}');")
            columns = cursor.fetchall()
            col_names = [col[1] for col in columns]
            col_types = [col[2] for col in columns]
            
            print(f"  Table: {table}")
            print(f"    Rows: {count:,}")
            print(f"    Columns ({len(col_names)}): {', '.join([f'{n}({t})' for n,t in zip(col_names, col_types)])}")
            
            # Sample first 3 rows
            if count > 0:
                cursor.execute(f"SELECT * FROM '{table}' LIMIT 3;")
                rows = cursor.fetchall()
                print(f"    Sample data:")
                for i, row in enumerate(rows, 1):
                    print(f"      Row {i}: {row}")
            print()
        
        print(f"\nTOTAL TABLES: {len(tables)}")
        print(f"TOTAL ROWS: {total_rows:,}")
        
        # Search for specific values
        print(f"\n{'='*70}")
        print("SEARCHING FOR TARGET VALUES IN TEXT/NUMERIC COLUMNS...")
        print(f"{'='*70}\n")
        
        target_values = ['76329', '76,329', '82250', '305', '24']
        
        for table in tables:
            cursor.execute(f"PRAGMA table_info('{table}');")
            columns = cursor.fetchall()
            
            for col in columns:
                col_name = col[1]
                
                for target in target_values:
                    try:
                        # Search as exact values
                        cursor.execute(f"SELECT COUNT(*) FROM '{table}' WHERE CAST('{col_name}' AS TEXT) = ?;", (target,))
                        match_count = cursor.fetchone()[0]
                        if match_count > 0:
                            cursor.execute(f"SELECT DISTINCT '{col_name}' FROM '{table}' WHERE CAST('{col_name}' AS TEXT) = ? LIMIT 5;", (target,))
                            matches = cursor.fetchall()
                            print(f"  FOUND: {table}.{col_name} = '{target}' ({match_count} rows)")
                            for m in matches:
                                print(f"    Value: {m}")
                    except:
                        pass
        
        conn.close()
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

# Explore cache databases
explore_cache_db(r'G:\_CONVERGENCE_DUPES\cache_1773489732.sqlite', 'CACHE DB (cache_1773489732.sqlite)')
explore_cache_db(r'G:\_CONVERGENCE_DUPES\cache_1773489736.sqlite', 'CACHE DB (cache_1773489736.sqlite)')
