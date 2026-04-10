import sqlite3
import sys

db_path = r'C:\Users\andre\LitigationOS\litigation_context.db'
tables = ['evidence_quotes', 'd_drive_events', 'claims', 'docket_events', 'authority_chains', 'deadlines', 'documents', 'judicial_violations', 'filing_readiness', 'schema_reference']

try:
    conn = sqlite3.connect(db_path, timeout=10)
    conn.execute('PRAGMA journal_mode=WAL')
    
    for table in tables:
        print(f"\n{'='*60}")
        print(f"TABLE: {table}")
        print(f"{'='*60}")
        try:
            cursor = conn.execute(f"PRAGMA table_info({table})")
            rows = cursor.fetchall()
            if not rows:
                print(f"  [TABLE DOES NOT EXIST]")
            else:
                print(f"{'cid':<5} {'name':<30} {'type':<15} {'notnull':<8} {'dflt':<15} {'pk':<3}")
                print("-" * 85)
                for row in rows:
                    cid, name, coltype, notnull, dflt, pk = row
                    print(f"{cid:<5} {name:<30} {coltype:<15} {notnull:<8} {str(dflt):<15} {pk:<3}")
        except Exception as e:
            print(f"  ERROR: {e}")
    
    conn.close()
except Exception as e:
    print(f"Connection error: {e}")
    sys.exit(1)
