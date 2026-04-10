import sqlite3
import os

db_path = r"C:\Users\andre\LitigationOS\litigation_context.db"

# Check if database exists
if not os.path.exists(db_path):
    print(f"ERROR: Database file not found at {db_path}")
    exit(1)

# List of tables to survey
tables = [
    "evidence_quotes",
    "authority_chains_v2",
    "timeline_events",
    "md_sections",
    "master_citations",
    "michigan_rules_extracted",
    "md_cross_refs",
    "contradiction_map",
    "judicial_violations",
    "impeachment_matrix",
    "weapon_chains",
    "police_reports",
    "berry_mcneill_intelligence",
    "filing_packages",
    "filing_readiness",
    "causal_chains",
    "semantic_vectors",
    "documents",
    "pages",
    "claims",
    "deadlines"
]

try:
    conn = sqlite3.connect(db_path, timeout=60)
    
    # Set pragmas
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    
    print("=" * 100)
    print("DATABASE SCHEMA SURVEY")
    print(f"Database: {db_path}")
    print("=" * 100)
    print()
    
    for table_name in tables:
        try:
            # Get table info
            cursor = conn.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            if not columns:
                print(f"[{table_name}] - TABLE NOT FOUND")
                print()
                continue
            
            # Get row count
            count_cursor = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = count_cursor.fetchone()[0]
            
            # Format output
            print(f"[{table_name}]")
            print(f"  Row Count: {row_count}")
            print(f"  Columns:")
            for col in columns:
                cid, name, col_type, notnull, dflt_value, pk = col
                print(f"    - {name}: {col_type}" + (" (PK)" if pk else "") + (" NOT NULL" if notnull else ""))
            print()
            
        except sqlite3.OperationalError as e:
            print(f"[{table_name}] - ERROR: {str(e)}")
            print()
        except Exception as e:
            print(f"[{table_name}] - UNEXPECTED ERROR: {str(e)}")
            print()
    
    print("=" * 100)
    print("SURVEY COMPLETE")
    print("=" * 100)
    
    conn.close()

except sqlite3.DatabaseError as e:
    print(f"DATABASE ERROR: {str(e)}")
    exit(1)
except Exception as e:
    print(f"ERROR: {str(e)}")
    exit(1)
