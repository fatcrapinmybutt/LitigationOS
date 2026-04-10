import sqlite3

db_path = r'C:\Users\andre\LitigationOS\litigation_context.db'

conn = sqlite3.connect(db_path)
conn.execute('PRAGMA busy_timeout=60000')
cursor = conn.cursor()

print("="*100)
print("DETAILED CASE INFORMATION")
print("="*100)

# 1. EVICTION CASE - Lane E
print("\n" + "="*100)
print("1. EVICTION CASE (LANE E)")
print("="*100)

cursor.execute("""
    SELECT DISTINCT case_number FROM documents WHERE lane = 'E' AND (
        LOWER(title) LIKE '%eviction%' OR 
        LOWER(title) LIKE '%pretrial%' OR
        LOWER(title) LIKE '%ladas%' OR
        LOWER(title) LIKE '%landlord%'
    )
    LIMIT 10
""")
case_nums = cursor.fetchall()
print(f"Documents in Lane E related to eviction: {[c[0] for c in case_nums]}")

# Get Eviction docket events
cursor.execute("""
    SELECT event_date, event_type, description, filed_by 
    FROM docket_events 
    WHERE LOWER(case_number) LIKE '%1507%' OR LOWER(case_number) LIKE '%dc%'
    ORDER BY event_date DESC
""")
events = cursor.fetchall()
print(f"\nEviction docket events: {len(events)}")
for event in events[:10]:
    print(f"  {event[0]:12} | {event[1]:20} | By: {event[3]:15}")
    print(f"    {event[2][:80]}")

# Search for Maria Ladas and judge references
cursor.execute("""
    SELECT quote_text, source_file, lane 
    FROM evidence_quotes 
    WHERE LOWER(quote_text) LIKE '%maria ladas%' OR LOWER(quote_text) LIKE '%ladas hoopes%'
    LIMIT 15
""")
quotes = cursor.fetchall()
print(f"\nEvidence quotes about Maria Ladas/Judge Hoopes:")
for quote in quotes[:5]:
    print(f"  Source: {quote[1][:50]}")
    print(f"    {quote[0][:100]}")

# 2. SHADY OAKS CASE - Lane B/D (2025-002760)
print("\n" + "="*100)
print("2. SHADY OAKS CIVIL CASE (LANE B) - Case 2025-002760-CZ")
print("="*100)

cursor.execute("""
    SELECT title, lane, doc_type, created_date 
    FROM documents 
    WHERE lane = 'B' OR (LOWER(title) LIKE '%2025-002760%' OR LOWER(title) LIKE '%shady oaks%')
    LIMIT 20
""")
docs = cursor.fetchall()
print(f"Shady Oaks documents found: {len(docs)}")
for doc in docs[:10]:
    print(f"  {doc[0][:70]} | Lane: {doc[1]} | Type: {doc[2]}")

# Get violations in Lane B
cursor.execute("""
    SELECT violation_type, description, date_occurred, severity 
    FROM judicial_violations 
    WHERE lane = 'B'
    LIMIT 15
""")
violations = cursor.fetchall()
print(f"\nJudicial violations in Lane B (Shady Oaks): {len(violations)}")
for viol in violations[:5]:
    print(f"  {viol[0]:15} | Severity: {viol[3]} | Date: {viol[2]}")
    print(f"    {viol[1][:70]}")

# Search for Hoopes in Shady Oaks
cursor.execute("""
    SELECT quote_text, source_file 
    FROM evidence_quotes 
    WHERE lane = 'B' AND LOWER(quote_text) LIKE '%hoopes%'
    LIMIT 10
""")
hoopes_quotes = cursor.fetchall()
print(f"\nHoopes references in Shady Oaks case: {len(hoopes_quotes)}")
for quote in hoopes_quotes[:3]:
    print(f"  {quote[0][:80]}")

# 3. CUSTODY CASE - Lane E (2024-001507-DC)
print("\n" + "="*100)
print("3. CUSTODY CASE (LANE E) - Case 2024-001507-DC / 2024-1507-DC")
print("="*100)

cursor.execute("""
    SELECT title, lane, doc_type, created_date 
    FROM documents 
    WHERE lane = 'E' AND (LOWER(title) LIKE '%custody%' OR LOWER(title) LIKE '%watson%' OR LOWER(title) LIKE '%2024-001507%')
    LIMIT 20
""")
custody_docs = cursor.fetchall()
print(f"Custody case documents: {len(custody_docs)}")
for doc in custody_docs[:10]:
    print(f"  {doc[0][:70]} | Type: {doc[2]}")

# Get docket events for custody
cursor.execute("""
    SELECT event_date, event_type, description, filed_by 
    FROM docket_events 
    WHERE LOWER(case_number) LIKE '%001507%' OR LOWER(case_number) LIKE '%1507%'
    ORDER BY event_date DESC
    LIMIT 20
""")
custody_events = cursor.fetchall()
print(f"\nCustody docket events: {len(custody_events)}")
for event in custody_events[:10]:
    print(f"  {event[0]:12} | {event[1]:20} | By: {event[3]}")
    print(f"    {event[2][:80]}")

# 4. CROSS-REFERENCES
print("\n" + "="*100)
print("4. CROSS-REFERENCES BETWEEN CASES")
print("="*100)

# Check if Hoopes appears in multiple lanes
cursor.execute("""
    SELECT DISTINCT lane 
    FROM evidence_quotes 
    WHERE LOWER(quote_text) LIKE '%hoopes%'
""")
hoopes_lanes = cursor.fetchall()
print(f"Hoopes mentioned in lanes: {[lane[0] for lane in hoopes_lanes]}")

# Check for any judicial violations mentioning multiple names
cursor.execute("""
    SELECT violation_type, description, lane, severity 
    FROM judicial_violations 
    WHERE (LOWER(description) LIKE '%hoopes%' OR LOWER(source_quote) LIKE '%hoopes%')
        AND (LOWER(description) LIKE '%shady%' OR LOWER(source_quote) LIKE '%shady%')
    LIMIT 5
""")
cross_refs = cursor.fetchall()
print(f"\nViolations linking Hoopes to Shady Oaks: {len(cross_refs)}")
for ref in cross_refs:
    print(f"  {ref[0]:15} | Lane: {ref[2]} | Severity: {ref[3]}")
    print(f"    {ref[1][:80]}")

# 5. EVIDENCE TOTALS
print("\n" + "="*100)
print("5. EVIDENCE TOTALS BY LANE")
print("="*100)

cursor.execute("""
    SELECT 
        lane,
        COUNT(*) as total_quotes,
        SUM(CASE WHEN LOWER(quote_text) LIKE '%hoopes%' THEN 1 ELSE 0 END) as hoopes_mentions,
        SUM(CASE WHEN LOWER(quote_text) LIKE '%ladas%' THEN 1 ELSE 0 END) as ladas_mentions,
        SUM(CASE WHEN LOWER(quote_text) LIKE '%mcneill%' THEN 1 ELSE 0 END) as mcneill_mentions
    FROM evidence_quotes 
    GROUP BY lane
    ORDER BY total_quotes DESC
""")
lane_stats = cursor.fetchall()
print("\nEvidence counts by lane:")
print(f"{'Lane':<6} {'Total':<8} {'Hoopes':<8} {'Ladas':<8} {'McNeill':<8}")
print("-" * 45)
for stat in lane_stats:
    lane = stat[0] or "NULL"
    print(f"{lane:<6} {stat[1]:<8} {stat[2] or 0:<8} {stat[3] or 0:<8} {stat[4] or 0:<8}")

# 6. CLAIMS SUMMARY
print("\n" + "="*100)
print("6. CLAIMS BY LANE")
print("="*100)

cursor.execute("""
    SELECT lane, claim_type, COUNT(*) as count, SUM(evidence_count) as total_evidence
    FROM claims
    GROUP BY lane, claim_type
    ORDER BY lane, count DESC
""")
claims = cursor.fetchall()
print("\nClaims by lane:")
for claim in claims:
    lane = claim[0] or "NULL"
    print(f"  Lane {lane}: {claim[1]} ({claim[2]} claims, {claim[3] or 0} evidence refs)")

conn.close()
