import sqlite3
import sys

db_path = r'C:\Users\andre\LitigationOS\litigation_context.db'

try:
    conn = sqlite3.connect(db_path, timeout=60)
    conn.execute('PRAGMA busy_timeout=60000')
    cur = conn.cursor()
    
    print("=" * 100)
    print("QUERY 7: Search for Ella Randall references")
    print("=" * 100)
    try:
        cur.execute("""
            SELECT quote_text, source_file, page_number 
            FROM evidence_quotes 
            WHERE quote_text LIKE '%Randall%' OR quote_text LIKE '%Ella%' 
            LIMIT 20
        """)
        rows = cur.fetchall()
        print(f"[Found {len(rows)} results]")
        if rows:
            for i, row in enumerate(rows, 1):
                print(f"\n{i}. Source: {row[1]} | Page: {row[2]}")
                print(f"   Quote: {row[0][:200]}...")
        else:
            print("[No results]")
    except Exception as e:
        print(f"[Error] {e}")
    
    print("\n" + "=" * 100)
    print("QUERY 8: Search for 'quit nitpicking' or 'nitpick'")
    print("=" * 100)
    try:
        cur.execute("""
            SELECT quote_text, source_file, page_number 
            FROM evidence_quotes 
            WHERE quote_text LIKE '%nitpick%' 
            LIMIT 20
        """)
        rows = cur.fetchall()
        print(f"[Found {len(rows)} results]")
        if rows:
            for i, row in enumerate(rows, 1):
                print(f"\n{i}. Source: {row[1]} | Page: {row[2]}")
                print(f"   Quote: {row[0][:250]}")
        else:
            print("[No results]")
    except Exception as e:
        print(f"[Error] {e}")
    
    print("\n" + "=" * 100)
    print("QUERY 9: Search for meth/drug accusations")
    print("=" * 100)
    try:
        cur.execute("""
            SELECT quote_text, source_file, page_number 
            FROM evidence_quotes 
            WHERE (quote_text LIKE '%meth%' OR quote_text LIKE '%drug%' OR quote_text LIKE '%substance%') 
            AND quote_text NOT LIKE '%method%' 
            LIMIT 30
        """)
        rows = cur.fetchall()
        print(f"[Found {len(rows)} results]")
        if rows:
            for i, row in enumerate(rows, 1):
                print(f"\n{i}. Source: {row[1]} | Page: {row[2]}")
                print(f"   Quote: {row[0][:250]}")
        else:
            print("[No results]")
    except Exception as e:
        print(f"[Error] {e}")
    
    print("\n" + "=" * 100)
    print("QUERY 10: Search for false police report references")
    print("=" * 100)
    try:
        cur.execute("""
            SELECT quote_text, source_file 
            FROM evidence_quotes 
            WHERE (quote_text LIKE '%false%' AND quote_text LIKE '%police%') 
            OR (quote_text LIKE '%false%' AND quote_text LIKE '%report%') 
            LIMIT 20
        """)
        rows = cur.fetchall()
        print(f"[Found {len(rows)} results]")
        if rows:
            for i, row in enumerate(rows, 1):
                print(f"\n{i}. Source: {row[1]}")
                print(f"   Quote: {row[0][:250]}")
        else:
            print("[No results]")
    except Exception as e:
        print(f"[Error] {e}")
    
    print("\n" + "=" * 100)
    print("QUERY 11: Search for perjury / false statements")
    print("=" * 100)
    try:
        cur.execute("""
            SELECT quote_text, source_file 
            FROM evidence_quotes 
            WHERE quote_text LIKE '%perjur%' OR quote_text LIKE '%false statement%' 
            OR quote_text LIKE '%lied%' OR quote_text LIKE '%lying%' 
            LIMIT 30
        """)
        rows = cur.fetchall()
        print(f"[Found {len(rows)} results]")
        if rows:
            for i, row in enumerate(rows, 1):
                print(f"\n{i}. Source: {row[1]}")
                print(f"   Quote: {row[0][:250]}")
        else:
            print("[No results]")
    except Exception as e:
        print(f"[Error] {e}")
    
    print("\n" + "=" * 100)
    print("QUERY 12: All ex parte related entries")
    print("=" * 100)
    try:
        cur.execute("""SELECT COUNT(*) as total FROM evidence_quotes WHERE quote_text LIKE '%ex parte%'""")
        total = cur.fetchone()[0]
        print(f"[Total ex parte entries: {total}]")
        
        cur.execute("""
            SELECT quote_text, source_file 
            FROM evidence_quotes 
            WHERE quote_text LIKE '%ex parte%' 
            LIMIT 15
        """)
        rows = cur.fetchall()
        if rows:
            for i, row in enumerate(rows, 1):
                print(f"\n{i}. Source: {row[1]}")
                print(f"   Quote: {row[0][:250]}")
    except Exception as e:
        print(f"[Error] {e}")
    
    print("\n" + "=" * 100)
    print("QUERY 13: All bias-related entries")
    print("=" * 100)
    try:
        cur.execute("""
            SELECT COUNT(*) as total FROM evidence_quotes 
            WHERE quote_text LIKE '%bias%' OR quote_text LIKE '%prejudic%' OR quote_text LIKE '%impartial%'
        """)
        total = cur.fetchone()[0]
        print(f"[Total bias-related entries: {total}]")
    except Exception as e:
        print(f"[Error] {e}")
    
    print("\n" + "=" * 100)
    print("QUERY 14: All parenting time denial entries")
    print("=" * 100)
    try:
        cur.execute("""
            SELECT COUNT(*) as total FROM evidence_quotes 
            WHERE quote_text LIKE '%parenting time%' 
            AND (quote_text LIKE '%denied%' OR quote_text LIKE '%suspend%' OR quote_text LIKE '%restrict%')
        """)
        total = cur.fetchone()[0]
        print(f"[Total parenting time denial entries: {total}]")
    except Exception as e:
        print(f"[Error] {e}")
    
    conn.close()
    
except Exception as e:
    print(f"Failed to connect to database: {e}")
    sys.exit(1)
