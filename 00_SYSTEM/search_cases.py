import sqlite3
import json

db_path = r'C:\Users\andre\LitigationOS\litigation_context.db'

conn = sqlite3.connect(db_path)
conn.execute('PRAGMA busy_timeout=60000')
cursor = conn.cursor()

print("="*80)
print("LITIGATION DATABASE SEARCH")
print("="*80)

# Define search patterns for each case
eviction_patterns = ["eviction", "maria ladas", "ladas-hoopes", "60th district", "landlord", "housing"]
shady_oaks_patterns = ["shady oaks", "homes of america", "2025-002760", "housing violations"]
custody_patterns = ["2024-001507", "mcneill", "custody", "watson"]

# Search cases table
print("\n" + "="*80)
print("1. SEARCHING CASES TABLE")
print("="*80)

cursor.execute("SELECT * FROM cases LIMIT 5")
cols = [description[0] for description in cursor.description]
print(f"Cases table columns: {cols}")

# Search for all cases
cursor.execute("SELECT case_number, case_type, parties, status, created_at FROM cases")
all_cases = cursor.fetchall()
print(f"\nTotal cases in database: {len(all_cases)}")
for case in all_cases[:10]:
    print(f"  Case: {case[0]} | Type: {case[1]} | Parties: {case[2]} | Status: {case[3]}")

# Search documents table for keywords
print("\n" + "="*80)
print("2. SEARCHING DOCUMENTS TABLE")
print("="*80)

search_keywords = ["eviction", "ladas", "shady oaks", "mcneill", "custody", "hoopes"]

for keyword in search_keywords:
    cursor.execute("""
        SELECT id, title, case_number, lane, doc_type, created_date 
        FROM documents 
        WHERE title LIKE ? OR content_preview LIKE ?
        LIMIT 20
    """, (f"%{keyword}%", f"%{keyword}%"))
    results = cursor.fetchall()
    if results:
        print(f"\nDocuments matching '{keyword}':")
        for row in results:
            print(f"  ID:{row[0]} | Title: {row[1][:60]} | Case: {row[2]} | Lane: {row[3]} | Type: {row[4]}")

# Search evidence_quotes
print("\n" + "="*80)
print("3. SEARCHING EVIDENCE QUOTES TABLE")
print("="*80)

for keyword in ["ladas", "hoopes", "maria", "shady oaks", "mcneill", "watson"]:
    cursor.execute("""
        SELECT id, quote_text, source_file, lane, category 
        FROM evidence_quotes 
        WHERE quote_text LIKE ? 
        LIMIT 15
    """, (f"%{keyword}%",))
    results = cursor.fetchall()
    if results:
        print(f"\nEvidence quotes mentioning '{keyword}':")
        for row in results:
            quote_preview = row[1][:80] if row[1] else ""
            print(f"  Source: {row[2][:50]} | Lane: {row[3]} | Cat: {row[4]}")
            print(f"    Quote: {quote_preview}")

# Search docket_events
print("\n" + "="*80)
print("4. SEARCHING DOCKET EVENTS TABLE")
print("="*80)

case_numbers = ["2024-001507", "2025-002760"]
for case_num in case_numbers:
    cursor.execute("""
        SELECT case_number, event_date, event_type, description, filed_by 
        FROM docket_events 
        WHERE case_number LIKE ?
        ORDER BY event_date DESC
    """, (f"%{case_num}%",))
    results = cursor.fetchall()
    if results:
        print(f"\nDocket events for case {case_num}:")
        for row in results:
            print(f"  Date: {row[1]} | Type: {row[2]} | By: {row[4]}")
            print(f"    Description: {row[3][:70]}")

# Search judicial_violations
print("\n" + "="*80)
print("5. SEARCHING JUDICIAL VIOLATIONS TABLE")
print("="*80)

for keyword in ["hoopes", "ladas", "maria", "mcneill"]:
    cursor.execute("""
        SELECT violation_type, description, date_occurred, mcr_rule, canon, severity, lane 
        FROM judicial_violations 
        WHERE description LIKE ? OR source_quote LIKE ?
        LIMIT 10
    """, (f"%{keyword}%", f"%{keyword}%"))
    results = cursor.fetchall()
    if results:
        print(f"\nJudicial violations mentioning '{keyword}':")
        for row in results:
            print(f"  Type: {row[0]} | Severity: {row[5]} | Lane: {row[6]}")
            print(f"    Description: {row[1][:70]}")
            print(f"    MCR Rule: {row[3]}, Canon: {row[4]}")

# Search claims
print("\n" + "="*80)
print("6. SEARCHING CLAIMS TABLE")
print("="*80)

cursor.execute("SELECT claim_id, claim_type, lane, status, evidence_count FROM claims LIMIT 10")
results = cursor.fetchall()
if results:
    print(f"Sample claims:")
    for row in results:
        print(f"  {row[0]} | Type: {row[1]} | Lane: {row[2]} | Evidence: {row[4]}")

# Get case metadata
print("\n" + "="*80)
print("7. CASE METADATA")
print("="*80)

cursor.execute("SELECT * FROM case_metadata LIMIT 10")
cols = [description[0] for description in cursor.description]
metadata = cursor.fetchall()
print(f"Case metadata columns: {cols}")
if metadata:
    for row in metadata[:5]:
        print(f"  {row}")

conn.close()
