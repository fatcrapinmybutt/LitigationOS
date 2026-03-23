#!/usr/bin/env python3
"""
Database query script for litigation_context.db
Executes 10 queries and prints all results with formatting
"""
import sqlite3
import os

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"

def print_query_header(query_num, description):
    print(f"\n{'='*80}")
    print(f"QUERY {query_num}: {description}")
    print('='*80)

def print_results(cursor, description):
    """Print query results with formatting"""
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description] if cursor.description else []
    
    if not rows:
        print("(No results)")
        return
    
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
            elif isinstance(value, str) and len(value) > 200:
                print(f"  {col}: {value[:200]}...")
            else:
                print(f"  {col}: {value}")

def main():
    # Check if database exists
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
        
        # Query 1: Housing/Shady Oaks claims
        print_query_header(1, "Housing/Shady Oaks claims")
        try:
            cursor.execute("""
                SELECT * FROM claims 
                WHERE claim_type LIKE '%hous%' 
                   OR claim_type LIKE '%shady%' 
                   OR claim_type LIKE '%landlord%' 
                   OR claim_type LIKE '%tenant%' 
                   OR claim_type LIKE '%habitab%' 
                LIMIT 30
            """)
            print_results(cursor, "Housing/Shady Oaks claims")
        except sqlite3.OperationalError as e:
            print(f"ERROR: {e}")
        
        # Query 2: Lane B evidence count
        print_query_header(2, "Lane B evidence count")
        try:
            cursor.execute("""
                SELECT COUNT(*) FROM evidence_quotes 
                WHERE vehicle_name LIKE '%B%' 
                   OR vehicle_name LIKE '%hous%' 
                   OR vehicle_name LIKE '%shady%'
            """)
            print_results(cursor, "Lane B evidence count")
        except sqlite3.OperationalError as e:
            print(f"ERROR: {e}")
        
        # Query 3: Appellate claims
        print_query_header(3, "Appellate claims")
        try:
            cursor.execute("""
                SELECT * FROM claims 
                WHERE claim_type LIKE '%appeal%' 
                   OR claim_type LIKE '%COA%' 
                   OR claim_type LIKE '%appell%' 
                LIMIT 30
            """)
            print_results(cursor, "Appellate claims")
        except sqlite3.OperationalError as e:
            print(f"ERROR: {e}")
        
        # Query 4: Filing readiness
        print_query_header(4, "Filing readiness")
        try:
            cursor.execute("""
                SELECT * FROM filing_readiness 
                WHERE vehicle_name LIKE '%shady%' 
                   OR vehicle_name LIKE '%hous%' 
                   OR vehicle_name LIKE '%COA%' 
                   OR vehicle_name LIKE '%appeal%'
            """)
            print_results(cursor, "Filing readiness")
        except sqlite3.OperationalError as e:
            print(f"ERROR: {e}")
        
        # Query 5: All tables related to housing
        print_query_header(5, "All tables related to housing")
        try:
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' 
                AND (name LIKE '%hous%' 
                  OR name LIKE '%shady%' 
                  OR name LIKE '%landlord%' 
                  OR name LIKE '%tenant%' 
                  OR name LIKE '%lane_b%' 
                  OR name LIKE '%habitat%')
            """)
            print_results(cursor, "Housing-related tables")
        except sqlite3.OperationalError as e:
            print(f"ERROR: {e}")
        
        # Query 6: All tables related to appellate
        print_query_header(6, "All tables related to appellate")
        try:
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' 
                AND (name LIKE '%appeal%' 
                  OR name LIKE '%appell%' 
                  OR name LIKE '%coa%' 
                  OR name LIKE '%lane_f%' 
                  OR name LIKE '%brief%')
            """)
            print_results(cursor, "Appellate-related tables")
        except sqlite3.OperationalError as e:
            print(f"ERROR: {e}")
        
        # Query 7: Evidence quotes for housing
        print_query_header(7, "Evidence quotes for housing")
        try:
            cursor.execute("""
                SELECT * FROM evidence_quotes 
                WHERE vehicle_name LIKE '%B%' 
                   OR quote_text LIKE '%shady%' 
                   OR quote_text LIKE '%hous%' 
                   OR quote_text LIKE '%landlord%' 
                   OR quote_text LIKE '%rent%' 
                   OR quote_text LIKE '%habitab%' 
                LIMIT 30
            """)
            print_results(cursor, "Evidence quotes for housing")
        except sqlite3.OperationalError as e:
            print(f"ERROR: {e}")
        
        # Query 8: Evidence quotes for appellate
        print_query_header(8, "Evidence quotes for appellate")
        try:
            cursor.execute("""
                SELECT * FROM evidence_quotes 
                WHERE vehicle_name LIKE '%F%' 
                   OR quote_text LIKE '%appeal%' 
                   OR quote_text LIKE '%COA%' 
                   OR quote_text LIKE '%appell%' 
                LIMIT 30
            """)
            print_results(cursor, "Evidence quotes for appellate")
        except sqlite3.OperationalError as e:
            print(f"ERROR: {e}")
        
        # Query 9: Deadlines for housing and appellate
        print_query_header(9, "Deadlines for housing and appellate")
        try:
            cursor.execute("""
                SELECT * FROM deadlines 
                WHERE vehicle_name LIKE '%hous%' 
                   OR vehicle_name LIKE '%shady%' 
                   OR vehicle_name LIKE '%COA%' 
                   OR vehicle_name LIKE '%appeal%' 
                   OR vehicle_name LIKE '%Lane B%' 
                   OR vehicle_name LIKE '%Lane F%' 
                LIMIT 20
            """)
            print_results(cursor, "Housing and appellate deadlines")
        except sqlite3.OperationalError as e:
            print(f"ERROR: {e}")
        
        # Query 10: Documents table if exists
        print_query_header(10, "Documents table if exists")
        try:
            cursor.execute("""
                SELECT * FROM documents 
                WHERE file_path LIKE '%shady%' 
                   OR file_path LIKE '%hous%' 
                   OR file_path LIKE '%appeal%' 
                   OR file_path LIKE '%COA%' 
                   OR title LIKE '%shady%' 
                   OR title LIKE '%hous%' 
                   OR title LIKE '%appeal%' 
                LIMIT 20
            """)
            print_results(cursor, "Documents related to housing and appellate")
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
