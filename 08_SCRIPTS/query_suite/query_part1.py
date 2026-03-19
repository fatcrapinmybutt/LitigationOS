import sqlite3
import sys
from pathlib import Path

db_path = r'C:\Users\andre\LitigationOS\litigation_context.db'

try:
    conn = sqlite3.connect(db_path, timeout=60)
    conn.execute('PRAGMA busy_timeout=60000')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    print("=" * 100)
    print("QUERY 1: All unique violation types in judicial_violations")
    print("=" * 100)
    try:
        cur.execute("""
            SELECT violation_type, COUNT(*) as cnt 
            FROM judicial_violations 
            GROUP BY violation_type 
            ORDER BY cnt DESC
        """)
        rows = cur.fetchall()
        if rows:
            for row in rows:
                print(f"{row[0]:<50} | Count: {row[1]}")
        else:
            print("[No results]")
    except Exception as e:
        print(f"[Error] {e}")
    
    print("\n" + "=" * 100)
    print("QUERY 2: All evidence categories in evidence_quotes")
    print("=" * 100)
    try:
        cur.execute("""
            SELECT evidence_category, COUNT(*) as cnt 
            FROM evidence_quotes 
            GROUP BY evidence_category 
            ORDER BY cnt DESC 
            LIMIT 50
        """)
        rows = cur.fetchall()
        if rows:
            for row in rows:
                print(f"{row[0]:<50} | Count: {row[1]}")
        else:
            print("[No results]")
    except Exception as e:
        print(f"[Error] {e}")
    
    print("\n" + "=" * 100)
    print("QUERY 3: All claim types in claims table")
    print("=" * 100)
    try:
        print("\n--- Table Schema ---")
        cur.execute("PRAGMA table_info(claims)")
        schema = cur.fetchall()
        for row in schema:
            print(f"  {row[1]:<30} | {row[2]}")
        
        print("\n--- Claim Types ---")
        cur.execute("""
            SELECT claim_type, COUNT(*) as cnt 
            FROM claims 
            GROUP BY claim_type 
            ORDER BY cnt DESC 
            LIMIT 50
        """)
        rows = cur.fetchall()
        if rows:
            for row in rows:
                print(f"{row[0]:<50} | Count: {row[1]}")
        else:
            print("[No results]")
    except Exception as e:
        print(f"[Error] {e}")
    
    print("\n" + "=" * 100)
    print("QUERY 4: All contradiction types")
    print("=" * 100)
    try:
        print("\n--- Table Schema ---")
        cur.execute("PRAGMA table_info(contradiction_map)")
        schema = cur.fetchall()
        for row in schema:
            print(f"  {row[1]:<30} | {row[2]}")
        
        print("\n--- Contradiction Types ---")
        cur.execute("""
            SELECT contradiction_type, COUNT(*) as cnt 
            FROM contradiction_map 
            GROUP BY contradiction_type 
            ORDER BY cnt DESC 
            LIMIT 30
        """)
        rows = cur.fetchall()
        if rows:
            for row in rows:
                print(f"{row[0]:<50} | Count: {row[1]}")
        else:
            print("[No results]")
    except Exception as e:
        print(f"[Error] {e}")
    
    print("\n" + "=" * 100)
    print("QUERY 5: All impeachment categories")
    print("=" * 100)
    try:
        print("\n--- Table Schema ---")
        cur.execute("PRAGMA table_info(impeachment_items)")
        schema = cur.fetchall()
        for row in schema:
            print(f"  {row[1]:<30} | {row[2]}")
        
        print("\n--- Impeachment Categories ---")
        cur.execute("""
            SELECT category, COUNT(*) as cnt 
            FROM impeachment_items 
            GROUP BY category 
            ORDER BY cnt DESC 
            LIMIT 30
        """)
        rows = cur.fetchall()
        if rows:
            for row in rows:
                print(f"{row[0]:<50} | Count: {row[1]}")
        else:
            print("[No results]")
    except Exception as e:
        print(f"[Error] {e}")
    
    print("\n" + "=" * 100)
    print("QUERY 6: All vehicle names (filing vehicles)")
    print("=" * 100)
    try:
        print("\n--- Table Schema ---")
        cur.execute("PRAGMA table_info(vehicles)")
        schema = cur.fetchall()
        for row in schema:
            print(f"  {row[1]:<30} | {row[2]}")
        
        print("\n--- Vehicles ---")
        cur.execute("""
            SELECT vehicle_name, status, COUNT(*) as cnt 
            FROM vehicles 
            GROUP BY vehicle_name, status 
            ORDER BY cnt DESC
        """)
        rows = cur.fetchall()
        if rows:
            for row in rows:
                print(f"{row[0]:<40} | {row[1]:<15} | Count: {row[2]}")
        else:
            print("[No results]")
    except Exception as e:
        print(f"[Error] {e}")
    
    conn.close()
    
except Exception as e:
    print(f"Failed to connect to database: {e}")
    sys.exit(1)
