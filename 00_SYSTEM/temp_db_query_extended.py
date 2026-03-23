#!/usr/bin/env python3
"""
Extended database query script to explore actual housing/appellate tables
"""
import sqlite3
import os

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"

def print_query_header(query_num, description):
    print(f"\n{'='*80}")
    print(f"QUERY {query_num}: {description}")
    print('='*80)

def print_results(cursor, description, max_col_width=100):
    """Print query results with formatting"""
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description] if cursor.description else []
    
    if not rows:
        print("(No results)")
        return 0
    
    # Print column headers
    print(f"\nColumns: {columns}")
    print(f"Row count: {len(rows)}")
    print("-" * 80)
    
    # Print each row
    for i, row in enumerate(rows, 1):
        print(f"\nRow {i}:")
        for col, value in zip(columns, row):
            if value is None:
                print(f"  {col}: NULL")
            elif isinstance(value, str) and len(value) > max_col_width:
                print(f"  {col}: {value[:max_col_width]}...")
            else:
                print(f"  {col}: {value}")
    
    return len(rows)

def main():
    if not os.path.exists(DB_PATH):
        print(f"ERROR: Database not found at {DB_PATH}")
        return
    
    print(f"Connecting to: {DB_PATH}")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Set pragmas
        print("\nSetting PRAGMA statements...")
        cursor.execute("PRAGMA busy_timeout=60000;")
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA cache_size=-32000;")
        print("Pragmas set successfully")
        
        # Query 1: Shady Oaks evidence table
        print_query_header(1, "shadyoaks_evidence table (all rows)")
        try:
            cursor.execute("SELECT * FROM shadyoaks_evidence LIMIT 50")
            print_results(cursor, "shadyoaks_evidence")
        except sqlite3.OperationalError as e:
            print(f"ERROR: {e}")
        
        # Query 2: Shady Oaks claim table
        print_query_header(2, "shadyoaks_claim_table (all rows)")
        try:
            cursor.execute("SELECT * FROM shadyoaks_claim_table LIMIT 50")
            print_results(cursor, "shadyoaks_claim_table")
        except sqlite3.OperationalError as e:
            print(f"ERROR: {e}")
        
        # Query 3: Shady Oaks claim table 2
        print_query_header(3, "shadyoaks_claim_table_2 (all rows)")
        try:
            cursor.execute("SELECT * FROM shadyoaks_claim_table_2 LIMIT 50")
            print_results(cursor, "shadyoaks_claim_table_2")
        except sqlite3.OperationalError as e:
            print(f"ERROR: {e}")
        
        # Query 4: Housing violations
        print_query_header(4, "housing_violations table (all rows)")
        try:
            cursor.execute("SELECT * FROM housing_violations LIMIT 50")
            print_results(cursor, "housing_violations")
        except sqlite3.OperationalError as e:
            print(f"ERROR: {e}")
        
        # Query 5: Caselaw housing
        print_query_header(5, "caselaw_housing table (all rows)")
        try:
            cursor.execute("SELECT * FROM caselaw_housing LIMIT 50")
            print_results(cursor, "caselaw_housing")
        except sqlite3.OperationalError as e:
            print(f"ERROR: {e}")
        
        # Query 6: Shady Oaks evidence (alternative name)
        print_query_header(6, "shady_oaks_evidence table (all rows)")
        try:
            cursor.execute("SELECT * FROM shady_oaks_evidence LIMIT 50")
            print_results(cursor, "shady_oaks_evidence")
        except sqlite3.OperationalError as e:
            print(f"ERROR: {e}")
        
        # Query 7: Reply brief templates
        print_query_header(7, "reply_brief_templates table (all rows)")
        try:
            cursor.execute("SELECT * FROM reply_brief_templates LIMIT 50")
            print_results(cursor, "reply_brief_templates")
        except sqlite3.OperationalError as e:
            print(f"ERROR: {e}")
        
        # Query 8: Constitutional brief sections
        print_query_header(8, "constitutional_brief_sections table (all rows)")
        try:
            cursor.execute("SELECT * FROM constitutional_brief_sections LIMIT 50")
            print_results(cursor, "constitutional_brief_sections")
        except sqlite3.OperationalError as e:
            print(f"ERROR: {e}")
        
        # Query 9: Hypervisor C11 rebuttal microbriefs
        print_query_header(9, "hypervisor_c11_rebuttal_microbriefs table (all rows)")
        try:
            cursor.execute("SELECT * FROM hypervisor_c11_rebuttal_microbriefs LIMIT 50")
            print_results(cursor, "hypervisor_c11_rebuttal_microbriefs")
        except sqlite3.OperationalError as e:
            print(f"ERROR: {e}")
        
        # Query 10: List all tables with row counts
        print_query_header(10, "All tables with row counts")
        try:
            cursor.execute("""
                SELECT name FROM sqlite_master WHERE type='table' ORDER BY name
            """)
            tables = cursor.fetchall()
            print(f"\nTotal tables: {len(tables)}\n")
            for table in tables:
                table_name = table[0]
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM [{table_name}]")
                    count = cursor.fetchone()[0]
                    print(f"  {table_name}: {count} rows")
                except:
                    print(f"  {table_name}: ERROR")
        except sqlite3.OperationalError as e:
            print(f"ERROR: {e}")
        
        conn.close()
        print(f"\n{'='*80}")
        print("All queries completed successfully")
        print('='*80)
        
    except Exception as e:
        print(f"FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
