import sqlite3

db_path = r'C:\Users\andre\LitigationOS\litigation_context.db'

conn = sqlite3.connect(db_path, timeout=60)
cur = conn.cursor()

print("=" * 100)
print("QUERY 15: All tables that might contain analysis targets")
print("=" * 100)

patterns = [
    'violation', 'contradiction', 'impeach', 'bias', 'fraud', 'perjur',
    'false', 'abuse', 'harm', 'denial', 'misconduct', 'pattern',
    'complaint', 'accusation', 'rebuttal', 'alienation', 'custody',
    'best_interest', 'due_process', 'constitutional', 'rights',
    'order', 'ruling', 'hearing', 'police', 'ppo', 'protection'
]

try:
    cur.execute("""
        SELECT name FROM sqlite_master WHERE type='table' 
        ORDER BY name
    """)
    all_tables = [row[0] for row in cur.fetchall()]
    
    # Filter tables matching any pattern
    matching_tables = []
    for table in all_tables:
        lower_table = table.lower()
        for pattern in patterns:
            if pattern in lower_table:
                matching_tables.append(table)
                break
    
    print(f"[Found {len(matching_tables)} relevant tables]")
    for table in sorted(matching_tables):
        print(f"  - {table}")
except Exception as e:
    print(f"[Error] {e}")

print("\n" + "=" * 100)
print("QUERY 16: Docket events table")
print("=" * 100)
try:
    print("\n--- Table Schema ---")
    cur.execute("PRAGMA table_info(docket_events)")
    schema = cur.fetchall()
    if schema:
        for row in schema:
            print(f"  {row[1]:<30} | {row[2]}")
        
        print("\n--- Event Types ---")
        cur.execute("""
            SELECT event_type, COUNT(*) FROM docket_events 
            GROUP BY event_type 
            ORDER BY COUNT(*) DESC 
            LIMIT 30
        """)
        rows = cur.fetchall()
        for row in rows:
            print(f"{row[0]:<50} | Count: {row[1]}")
    else:
        print("[Table not found]")
except Exception as e:
    print(f"[Error] {e}")

print("\n" + "=" * 100)
print("QUERY 17: Pages table - sources and page counts")
print("=" * 100)
try:
    print("\n--- Table Schema ---")
    cur.execute("PRAGMA table_info(pages)")
    schema = cur.fetchall()
    if schema:
        for row in schema:
            print(f"  {row[1]:<30} | {row[2]}")
    
    print("\n--- Top 30 sources by page count ---")
    cur.execute("""
        SELECT source_file, COUNT(*) as page_count 
        FROM pages 
        GROUP BY source_file 
        ORDER BY page_count DESC 
        LIMIT 30
    """)
    rows = cur.fetchall()
    for i, row in enumerate(rows, 1):
        print(f"{i:2}. {row[0]:<50} | {row[1]} pages")
except Exception as e:
    print(f"[Error] {e}")

print("\n" + "=" * 100)
print("COMPLETE SUMMARY OF DATABASE CONTENTS")
print("=" * 100)
try:
    cur.execute("SELECT COUNT(DISTINCT type) as type_count FROM sqlite_master")
    result = cur.fetchone()
    
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    all_tables = [row[0] for row in cur.fetchall()]
    
    print(f"\nTotal tables in database: {len(all_tables)}")
    
    # Count rows in key tables
    key_tables = [
        'evidence_quotes', 'claims', 'contradiction_map', 'impeachment_items',
        'vehicles', 'docket_events', 'pages'
    ]
    
    print(f"\nKey table row counts:")
    for table in key_tables:
        try:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]
            print(f"  {table:<30} : {count:>15,}")
        except:
            pass
    
except Exception as e:
    print(f"[Error] {e}")

conn.close()
