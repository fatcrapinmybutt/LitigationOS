import sqlite3
import json

db_path = r'C:\Users\andre\LitigationOS\litigation_context.db'

conn = sqlite3.connect(db_path)
conn.execute('PRAGMA busy_timeout=60000')
cursor = conn.cursor()

print("="*90)
print("LITIGATION DATABASE COMPREHENSIVE SEARCH")
print("="*90)

# 1. Get all cases
print("\n" + "="*90)
print("1. ALL CASES IN DATABASE")
print("="*90)

cursor.execute("SELECT id, case_number, case_type, title, filed_date, status FROM cases")
all_cases = cursor.fetchall()
print(f"Total cases: {len(all_cases)}\n")
for case in all_cases:
    print(f"  ID: {case[0]} | Case#: {case[1]:15} | Type: {case[2]:15} | Title: {case[3]}")
    print(f"    Filed: {case[4]} | Status: {case[5]}\n")

# 2. Search documents
print("\n" + "="*90)
print("2. DOCUMENTS MATCHING CASE KEYWORDS")
print("="*90)

keywords = ["eviction", "ladas", "shady oaks", "2025-002760", "mcneill", "2024-001507", "watson", "custody", "hoopes"]

for keyword in keywords:
    cursor.execute("""
        SELECT id, title, case_number, lane, doc_type 
        FROM documents 
        WHERE LOWER(title) LIKE ? OR LOWER(content_preview) LIKE ?
        LIMIT 15
    """, (f"%{keyword.lower()}%", f"%{keyword.lower()}%"))
    results = cursor.fetchall()
    if results:
        print(f"\nDocuments matching '{keyword}': {len(results)} found")
        for row in results[:5]:
            print(f"  - {row[1][:60]} | Case: {row[2]} | Lane: {row[3]}")

# 3. Search evidence_quotes for person names and case references
print("\n" + "="*90)
print("3. EVIDENCE QUOTES - KEY PERSONS & CASES")
print("="*90)

persons = ["Maria Ladas", "Hoopes", "McNeill", "Watson", "Ladas-Hoopes"]

for person in persons:
    cursor.execute("""
        SELECT id, quote_text, source_file, lane, category 
        FROM evidence_quotes 
        WHERE LOWER(quote_text) LIKE ? 
        LIMIT 10
    """, (f"%{person.lower()}%",))
    results = cursor.fetchall()
    if results:
        print(f"\nEvidence mentioning '{person}': {len(results)} quotes")
        for row in results[:3]:
            quote = row[1][:100] if row[1] else ""
            print(f"  Source: {row[2][:40]} | Lane: {row[3]}")
            print(f"    {quote}")

# 4. Search docket_events for case numbers
print("\n" + "="*90)
print("4. DOCKET EVENTS")
print("="*90)

cursor.execute("""
    SELECT DISTINCT case_number FROM docket_events ORDER BY case_number
""")
docket_cases = cursor.fetchall()
print(f"Cases with docket events: {len(docket_cases)}")
for case in docket_cases:
    print(f"  - {case[0]}")

# Get events for each target case
for case_num in ["2024-001507", "2025-002760"]:
    cursor.execute("""
        SELECT event_date, event_type, description, filed_by 
        FROM docket_events 
        WHERE case_number = ?
        ORDER BY event_date DESC
        LIMIT 15
    """, (case_num,))
    results = cursor.fetchall()
    if results:
        print(f"\n  Docket events for {case_num}: {len(results)}")
        for row in results:
            print(f"    {row[0]} | {row[1]} | Filed by: {row[3]}")
            print(f"      {row[2][:70]}")

# 5. Search judicial_violations
print("\n" + "="*90)
print("5. JUDICIAL VIOLATIONS")
print("="*90)

cursor.execute("""
    SELECT COUNT(*) FROM judicial_violations
""")
total_violations = cursor.fetchone()[0]
print(f"Total judicial violations: {total_violations}")

for person in ["Hoopes", "Ladas", "Maria"]:
    cursor.execute("""
        SELECT violation_type, description, date_occurred, severity, lane, mcr_rule
        FROM judicial_violations 
        WHERE LOWER(description) LIKE ? OR LOWER(source_quote) LIKE ?
        LIMIT 10
    """, (f"%{person.lower()}%", f"%{person.lower()}%"))
    results = cursor.fetchall()
    if results:
        print(f"\nViolations mentioning '{person}': {len(results)}")
        for row in results[:3]:
            print(f"  Type: {row[0]} | Severity: {row[3]} | Date: {row[2]}")
            print(f"    {row[1][:70]} (MCR: {row[5]})")

# 6. Count evidence by lane
print("\n" + "="*90)
print("6. EVIDENCE COUNT BY LANE")
print("="*90)

cursor.execute("""
    SELECT lane, COUNT(*) as evidence_count 
    FROM evidence_quotes 
    GROUP BY lane 
    ORDER BY evidence_count DESC
""")
lane_counts = cursor.fetchall()
for lane, count in lane_counts:
    print(f"  {lane}: {count} evidence quotes")

# 7. Search for cross-references
print("\n" + "="*90)
print("7. CASE CROSS-REFERENCES")
print("="*90)

cursor.execute("""
    SELECT * FROM filing_cross_reference LIMIT 10
""")
cols = [description[0] for description in cursor.description]
results = cursor.fetchall()
print(f"Filing cross-reference columns: {cols}")
if results:
    print(f"Sample cross-references:")
    for row in results[:3]:
        print(f"  {row}")

conn.close()
