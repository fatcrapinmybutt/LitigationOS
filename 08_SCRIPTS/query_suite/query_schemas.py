import sqlite3
import os

brain_dir = r"C:\Users\andre\LitigationOS\00_SYSTEM\brains"
brains = [
    'authority_brain.db',
    'narrative_brain.db',
    'interpretation_brain.db',
    'entity_brain.db',
    'claims_brain.db',
    'cross_brain_index.db'
]

for brain in brains:
    db_path = os.path.join(brain_dir, brain)
    print(f"\n{'='*80}")
    print(f"DATABASE: {brain}")
    print(f"{'='*80}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    
    print(f"Tables found: {', '.join(tables)}\n")
    
    for table in tables:
        print(f"\n--- TABLE: {table} ---")
        
        # Get PRAGMA table_info
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        print("Columns:")
        for col in columns:
            cid, name, type_, notnull, dflt_value, pk = col
            print(f"  {name:30} {type_:15} PK={pk}, NOT NULL={notnull}, DEFAULT={dflt_value}")
        
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM [{table}]")
        count = cursor.fetchone()[0]
        print(f"Row count: {count}")
    
    conn.close()
