import sys
import os
import sqlite3
from pathlib import Path

# Fix encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

db_path = Path("litigation_context.db")

if not db_path.exists():
    print(f"ERROR: {db_path} not found in {os.getcwd()}")
    sys.exit(1)

conn = sqlite3.connect(str(db_path))
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Query 1: omega_legal_actions
print("\n" + "="*80)
print("QUERY 1: SELECT * FROM omega_legal_actions")
print("="*80)
try:
    cursor.execute("SELECT * FROM omega_legal_actions")
    rows = cursor.fetchall()
    if rows:
        print(f"Columns: {[desc[0] for desc in cursor.description]}")
        print(f"Row count: {len(rows)}")
        for i, row in enumerate(rows):
            print(f"Row {i+1}: {dict(row)}")
    else:
        print("No rows found")
except Exception as e:
    print(f"ERROR: {e}")

# Query 2: omega_filing_readiness
print("\n" + "="*80)
print("QUERY 2: SELECT vehicle_name, readiness_score, status FROM omega_filing_readiness")
print("="*80)
try:
    cursor.execute("SELECT vehicle_name, readiness_score, status FROM omega_filing_readiness")
    rows = cursor.fetchall()
    if rows:
        print(f"Row count: {len(rows)}")
        for i, row in enumerate(rows):
            print(f"Row {i+1}: {dict(row)}")
    else:
        print("No rows found")
except Exception as e:
    print(f"ERROR: {e}")

# Query 3: omega_scores
print("\n" + "="*80)
print("QUERY 3: SELECT * FROM omega_scores")
print("="*80)
try:
    cursor.execute("SELECT * FROM omega_scores")
    rows = cursor.fetchall()
    if rows:
        print(f"Columns: {[desc[0] for desc in cursor.description]}")
        print(f"Row count: {len(rows)}")
        for i, row in enumerate(rows):
            print(f"Row {i+1}: {dict(row)}")
    else:
        print("No rows found")
except Exception as e:
    print(f"ERROR: {e}")

# Query 4: deadlines
print("\n" + "="*80)
print("QUERY 4: SELECT * FROM deadlines ORDER BY due_date_iso LIMIT 20")
print("="*80)
try:
    cursor.execute("SELECT * FROM deadlines ORDER BY due_date_iso LIMIT 20")
    rows = cursor.fetchall()
    if rows:
        print(f"Row count: {len(rows)}")
        for i, row in enumerate(rows):
            print(f"Row {i+1}: {dict(row)}")
    else:
        print("No rows found")
except Exception as e:
    print(f"ERROR: {e}")

# Query 5: extracted_harms
print("\n" + "="*80)
print("QUERY 5: SELECT DISTINCT harm_category, COUNT(*) as cnt FROM extracted_harms GROUP BY harm_category ORDER BY cnt DESC")
print("="*80)
try:
    cursor.execute("SELECT DISTINCT harm_category, COUNT(*) as cnt FROM extracted_harms GROUP BY harm_category ORDER BY cnt DESC")
    rows = cursor.fetchall()
    if rows:
        print(f"Row count: {len(rows)}")
        for i, row in enumerate(rows):
            print(f"Row {i+1}: {dict(row)}")
    else:
        print("No rows found")
except Exception as e:
    print(f"ERROR: {e}")

# Query 6: filing_readiness
print("\n" + "="*80)
print("QUERY 6: SELECT * FROM filing_readiness")
print("="*80)
try:
    cursor.execute("SELECT * FROM filing_readiness")
    rows = cursor.fetchall()
    if rows:
        print(f"Columns: {[desc[0] for desc in cursor.description]}")
        print(f"Row count: {len(rows)}")
        for i, row in enumerate(rows):
            print(f"Row {i+1}: {dict(row)}")
    else:
        print("No rows found")
except Exception as e:
    print(f"ERROR: {e}")

# Query 7: claims
print("\n" + "="*80)
print("QUERY 7: SELECT claim_id, proposition, lane, status FROM claims LIMIT 30")
print("="*80)
try:
    cursor.execute("SELECT claim_id, proposition, lane, status FROM claims LIMIT 30")
    rows = cursor.fetchall()
    if rows:
        print(f"Row count: {len(rows)}")
        for i, row in enumerate(rows):
            print(f"Row {i+1}: {dict(row)}")
    else:
        print("No rows found")
except Exception as e:
    print(f"ERROR: {e}")

# Query 8: evidence_quotes count
print("\n" + "="*80)
print("QUERY 8: SELECT COUNT(*) FROM evidence_quotes")
print("="*80)
try:
    cursor.execute("SELECT COUNT(*) FROM evidence_quotes")
    count = cursor.fetchone()[0]
    print(f"Total count: {count}")
except Exception as e:
    print(f"ERROR: {e}")

# Query 9: judicial_violations count
print("\n" + "="*80)
print("QUERY 9: SELECT COUNT(*) FROM judicial_violations")
print("="*80)
try:
    cursor.execute("SELECT COUNT(*) FROM judicial_violations")
    count = cursor.fetchone()[0]
    print(f"Total count: {count}")
except Exception as e:
    print(f"ERROR: {e}")

# Query 10: impeachment_items count
print("\n" + "="*80)
print("QUERY 10: SELECT COUNT(*) FROM impeachment_items")
print("="*80)
try:
    cursor.execute("SELECT COUNT(*) FROM impeachment_items")
    count = cursor.fetchone()[0]
    print(f"Total count: {count}")
except Exception as e:
    print(f"ERROR: {e}")

# Query 11: contradiction_map count
print("\n" + "="*80)
print("QUERY 11: SELECT COUNT(*) FROM contradiction_map")
print("="*80)
try:
    cursor.execute("SELECT COUNT(*) FROM contradiction_map")
    count = cursor.fetchone()[0]
    print(f"Total count: {count}")
except Exception as e:
    print(f"ERROR: {e}")

# Query 12: master_citations count
print("\n" + "="*80)
print("QUERY 12: SELECT COUNT(*) FROM master_citations")
print("="*80)
try:
    cursor.execute("SELECT COUNT(*) FROM master_citations")
    count = cursor.fetchone()[0]
    print(f"Total count: {count}")
except Exception as e:
    print(f"ERROR: {e}")

# Query 13: adversary_harm_summary
print("\n" + "="*80)
print("QUERY 13: SELECT adversary_name, total_harms, severity_score FROM adversary_harm_summary ORDER BY total_harms DESC")
print("="*80)
try:
    cursor.execute("SELECT adversary_name, total_harms, severity_score FROM adversary_harm_summary ORDER BY total_harms DESC")
    rows = cursor.fetchall()
    if rows:
        print(f"Row count: {len(rows)}")
        for i, row in enumerate(rows):
            print(f"Row {i+1}: {dict(row)}")
    else:
        print("No rows found")
except Exception as e:
    print(f"ERROR: {e}")

conn.close()
print("\n" + "="*80)
print("QUERIES COMPLETE")
print("="*80)
