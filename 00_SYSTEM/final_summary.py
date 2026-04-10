import sqlite3

db_path = r'C:\Users\andre\LitigationOS\litigation_context.db'

conn = sqlite3.connect(db_path)
conn.execute('PRAGMA busy_timeout=60000')
cursor = conn.cursor()

print("="*110)
print("LITIGATION CASE DATABASE - FINAL COMPREHENSIVE SUMMARY")
print("="*110)

# Get all case numbers from docket_events
print("\n" + "="*110)
print("CASE NUMBERS AND DATES")
print("="*110)

cursor.execute("""
    SELECT DISTINCT case_number FROM docket_events WHERE case_number IS NOT NULL
    ORDER BY case_number
""")
all_case_nums = cursor.fetchall()
print(f"\nAll case numbers in docket_events table:")
for case in all_case_nums:
    print(f"  - {case[0]}")

# Get detailed docket events for custody case
print("\n" + "="*110)
print("CUSTODY CASE 2024-001507-DC - DOCKET ENTRIES")
print("="*110)

cursor.execute("""
    SELECT event_date, event_type, description, filed_by, source_file
    FROM docket_events 
    WHERE case_number LIKE '%001507%' OR case_number LIKE '%1507%'
    ORDER BY event_date DESC
    LIMIT 30
""")
custody_dockets = cursor.fetchall()
print(f"\nTotal docket entries: {len(custody_dockets)}")
for i, event in enumerate(custody_dockets, 1):
    date_str = str(event[0]) if event[0] else "Unknown"
    filed = event[3] if event[3] else "Unknown"
    print(f"\n{i}. Date: {date_str} | Type: {event[1]} | Filed By: {filed}")
    if event[2]:
        desc = event[2][:120] if len(event[2]) > 120 else event[2]
        print(f"   Description: {desc}")
    if event[4]:
        print(f"   Source File: {event[4][:80]}")

# Get more evidence about Shady Oaks and case number
print("\n" + "="*110)
print("SHADY OAKS CASE - CASE NUMBER 2025-002760-CZ")
print("="*110)

cursor.execute("""
    SELECT DISTINCT quote_text FROM evidence_quotes
    WHERE LOWER(quote_text) LIKE '%2025-002760%'
    LIMIT 10
""")
shady_oaks_refs = cursor.fetchall()
print(f"\nReferences to case 2025-002760-CZ: {len(shady_oaks_refs)}")
for i, quote in enumerate(shady_oaks_refs[:5], 1):
    print(f"  {i}. {quote[0][:100]}")

# Get eviction case information
print("\n" + "="*110)
print("EVICTION CASE - JUDGE MARIA LADAS HOOPES")
print("="*110)

cursor.execute("""
    SELECT DISTINCT quote_text, source_file FROM evidence_quotes
    WHERE LOWER(quote_text) LIKE '%maria ladas%' OR LOWER(quote_text) LIKE '%judge:%' AND LOWER(quote_text) LIKE '%ladas%'
    LIMIT 10
""")
ladas_refs = cursor.fetchall()
print(f"\nReferences mentioning Judge Maria Ladas or Maria Ladas Hoopes: {len(ladas_refs)}")
for i, (quote, source) in enumerate(ladas_refs[:5], 1):
    print(f"  {i}. Source: {source[:70] if source else 'Unknown'}")
    print(f"     Quote: {quote[:100]}")

# Get Hoopes references across all lanes
print("\n" + "="*110)
print("JUDGE HOOPES/LADAS-HOOPES - ALL REFERENCES ACROSS CASES")
print("="*110)

cursor.execute("""
    SELECT DISTINCT lane, COUNT(*) as count FROM evidence_quotes
    WHERE LOWER(quote_text) LIKE '%hoopes%'
    GROUP BY lane
    ORDER BY count DESC
""")
hoopes_by_lane = cursor.fetchall()
print(f"\nJudge Hoopes mentions by lane:")
for lane, count in hoopes_by_lane:
    lane_name = lane if lane else "NULL"
    print(f"  Lane {lane_name}: {count} evidence quotes")

cursor.execute("""
    SELECT DISTINCT quote_text, lane FROM evidence_quotes
    WHERE LOWER(quote_text) LIKE '%kenneth%' AND LOWER(quote_text) LIKE '%hoopes%'
    LIMIT 5
""")
kenneth_hoopes = cursor.fetchall()
print(f"\nReferences to Kenneth S Hoopes (judge): {len(kenneth_hoopes)}")
for quote, lane in kenneth_hoopes[:3]:
    print(f"  Lane {lane}: {quote[:90]}")

# Get all judicial violations
print("\n" + "="*110)
print("JUDICIAL VIOLATIONS - ALL RECORDS")
print("="*110)

cursor.execute("""
    SELECT COUNT(*) FROM judicial_violations
""")
total_violations = cursor.fetchone()[0]
print(f"\nTotal judicial violations in database: {total_violations}")

cursor.execute("""
    SELECT lane, COUNT(*) FROM judicial_violations
    GROUP BY lane
    ORDER BY COUNT(*) DESC
""")
violations_by_lane = cursor.fetchall()
print(f"\nViolations by lane:")
for lane, count in violations_by_lane:
    lane_name = lane if lane else "NULL"
    print(f"  Lane {lane_name}: {count}")

# Get violation types
cursor.execute("""
    SELECT violation_type, COUNT(*) FROM judicial_violations
    GROUP BY violation_type
    ORDER BY COUNT(*) DESC
""")
violations_by_type = cursor.fetchall()
print(f"\nViolations by type:")
for vtype, count in violations_by_type[:10]:
    print(f"  {vtype}: {count}")

# Get specific Hoopes violations
cursor.execute("""
    SELECT DISTINCT violation_type, severity, lane 
    FROM judicial_violations
    WHERE LOWER(description) LIKE '%hoopes%' OR LOWER(source_quote) LIKE '%hoopes%'
""")
hoopes_violations_types = cursor.fetchall()
print(f"\nJudicial violation types attributed to Hoopes: {len(hoopes_violations_types)}")
for vtype, severity, lane in hoopes_violations_types:
    print(f"  Type: {vtype} | Severity: {severity} | Lane: {lane}")

# Claims by lane
print("\n" + "="*110)
print("CLAIMS SUMMARY BY LANE")
print("="*110)

cursor.execute("""
    SELECT lane, COUNT(*) as count, SUM(evidence_count) as total_evidence
    FROM claims
    GROUP BY lane
    ORDER BY count DESC
""")
claims_by_lane = cursor.fetchall()
print(f"\nClaims by lane:")
for lane, count, evidence in claims_by_lane:
    lane_name = lane if lane else "NULL"
    evidence_count = evidence if evidence else 0
    print(f"  Lane {lane_name}: {count} claims, {evidence_count} evidence references")

conn.close()
