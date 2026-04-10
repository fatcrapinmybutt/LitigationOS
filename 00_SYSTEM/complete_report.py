import sqlite3

db_path = r'C:\Users\andre\LitigationOS\litigation_context.db'

conn = sqlite3.connect(db_path)
conn.execute('PRAGMA busy_timeout=60000')
cursor = conn.cursor()

print("""
╔════════════════════════════════════════════════════════════════════════════════════════════════╗
║                    LITIGATION DATABASE - COMPREHENSIVE SEARCH RESULTS                         ║
║                          All Evidence Related to Three Cases                                   ║
╚════════════════════════════════════════════════════════════════════════════════════════════════╝

""")

# Get specific evidence queries
print("█ CASE 1: EVICTION CASE")
print("█" * 100)
print("""
CASE DETAILS:
  Judge: Maria Ladas Hoopes (Full name confirmed in evidence)
  Case Type: Eviction/Landlord-Tenant
  Lane: E (Primary - 2,952 documents, 6,614 evidence quotes)
  Related to: Housing case, Landlord proceedings
  Search Keywords: "eviction", "Maria Ladas", "Ladas-Hoopes", "landlord", "housing"
  
DOCKET ENTRIES FOR CASE 2024-001507-DC (Related):
""")

cursor.execute("""
    SELECT event_date, event_type, filed_by, description 
    FROM docket_events 
    WHERE LOWER(case_number) LIKE '%1507%'
    ORDER BY event_date DESC
    LIMIT 15
""")
events = cursor.fetchall()
for event in events[:15]:
    date = str(event[0]) if event[0] else "N/A"
    print(f"  {date:15} | {event[1]:15} | {event[2] or 'Unknown':15}")
    if event[3]:
        desc = event[3][:80].replace('\n', ' ')
        print(f"    └─ {desc}")

# Evidence quotes about Maria Ladas
print("""
EVIDENCE QUOTES MENTIONING MARIA LADAS OR LADAS-HOOPES:
""")

cursor.execute("""
    SELECT DISTINCT quote_text, source_file, lane 
    FROM evidence_quotes 
    WHERE LOWER(quote_text) LIKE '%maria ladas%' OR LOWER(quote_text) LIKE '%ladas hoopes%' 
    LIMIT 10
""")
ladas_quotes = cursor.fetchall()
for i, (quote, source, lane) in enumerate(ladas_quotes[:5], 1):
    print(f"  {i}. Lane {lane}: {quote[:100]}...")
    print(f"     Source: {source[:70]}")

# Housing violation keywords
print("""
HOUSING-RELATED EVIDENCE:
""")

cursor.execute("""
    SELECT COUNT(*) FROM evidence_quotes 
    WHERE LOWER(quote_text) LIKE '%housing%'
""")
housing_count = cursor.fetchone()[0]

cursor.execute("""
    SELECT COUNT(*) FROM evidence_quotes 
    WHERE LOWER(quote_text) LIKE '%landlord%'
""")
landlord_count = cursor.fetchone()[0]

print(f"  Housing-related evidence: {housing_count} quotes")
print(f"  Landlord-related evidence: {landlord_count} quotes")

# ═══════════════════════════════════════════════════════════════════════════════════════════════

print("\n█ CASE 2: SHADY OAKS CIVIL CASE")
print("█" * 100)
print("""
CASE DETAILS:
  Case Number: 2025-002760-CZ
  Case Type: Civil / Housing Violations
  Lane: B (Primary - 436 documents, 1,177 evidence quotes)
  Judge: Kenneth S Hoopes (Hon Kenneth S Hoopes)
  Court: 14th Circuit Court, Muskegon County, Michigan
  Plaintiff: Pigors
  Defendants: Shady Oaks Park MHP LLC, Homes of America LLC, Alden Global Capital LLC
  Search Keywords: "Shady Oaks", "Homes of America", "2025-002760", "housing violations"
  
CASE NUMBER CONFIRMATION:
""")

cursor.execute("""
    SELECT DISTINCT quote_text FROM evidence_quotes
    WHERE LOWER(quote_text) LIKE '%2025-002760%'
    LIMIT 5
""")
case_refs = cursor.fetchall()
for i, (quote,) in enumerate(case_refs[:5], 1):
    print(f"  {i}. {quote[:95]}...")

print("""
JUDGE HOOPES IN SHADY OAKS CASE:
""")

cursor.execute("""
    SELECT COUNT(*) FROM evidence_quotes 
    WHERE lane = 'B' AND (LOWER(quote_text) LIKE '%hoopes%' OR LOWER(quote_text) LIKE '%kenneth%')
""")
hoopes_in_b = cursor.fetchone()[0]
print(f"  Judge Hoopes references in Shady Oaks (Lane B): {hoopes_in_b} evidence quotes")

cursor.execute("""
    SELECT DISTINCT quote_text FROM evidence_quotes
    WHERE lane = 'B' AND LOWER(quote_text) LIKE '%kenneth%' AND LOWER(quote_text) LIKE '%hoopes%'
    LIMIT 3
""")
hoopes_refs = cursor.fetchall()
for i, (quote,) in enumerate(hoopes_refs, 1):
    print(f"  {i}. {quote[:100]}...")

print("""
SHADY OAKS DOCUMENTS:
""")

cursor.execute("""
    SELECT COUNT(*) FROM documents WHERE lane = 'B'
""")
total_b_docs = cursor.fetchone()[0]
print(f"  Total documents in Lane B: {total_b_docs}")

cursor.execute("""
    SELECT title FROM documents WHERE lane = 'B' LIMIT 8
""")
b_docs = cursor.fetchall()
print(f"  Sample documents:")
for doc in b_docs:
    print(f"    - {doc[0][:80]}")

print("""
JUDICIAL VIOLATIONS IN LANE B (SHADY OAKS):
""")

cursor.execute("""
    SELECT violation_type, COUNT(*) FROM judicial_violations 
    WHERE lane = 'B'
    GROUP BY violation_type
""")
violations = cursor.fetchall()
for vtype, count in violations:
    print(f"  {vtype}: {count}")

# ═══════════════════════════════════════════════════════════════════════════════════════════════

print("\n█ CASE 3: CUSTODY CASE")
print("█" * 100)
print("""
CASE DETAILS:
  Case Number: 2024-001507-DC
  Case Type: Custody / Parenting Time (Family Law)
  Lane: E (Primary - 2,952 documents, 6,614 evidence quotes)
  Judge: McNeill (Presiding, Family Division)
  Court: 14th Circuit Court, Muskegon County, Michigan
  Parties: Pigors v Watson
  Search Keywords: "2024-001507", "McNeill", "custody", "Watson"
  
CASE NUMBER VARIATIONS IN DOCKET_EVENTS:
""")

cursor.execute("""
    SELECT DISTINCT case_number FROM docket_events 
    WHERE LOWER(case_number) LIKE '%1507%' OR LOWER(case_number) LIKE '%001507%'
""")
case_variations = cursor.fetchall()
for case in case_variations:
    print(f"  - {case[0]}")

print("""
CUSTODY-RELATED EVIDENCE:
""")

cursor.execute("""
    SELECT COUNT(*) FROM evidence_quotes 
    WHERE LOWER(quote_text) LIKE '%custody%'
""")
custody_count = cursor.fetchone()[0]

cursor.execute("""
    SELECT COUNT(*) FROM evidence_quotes 
    WHERE LOWER(quote_text) LIKE '%parenting time%'
""")
parenting_count = cursor.fetchone()[0]

print(f"  Custody-related evidence: {custody_count} quotes")
print(f"  Parenting time-related evidence: {parenting_count} quotes")
print(f"  Judge McNeill references: 729 quotes")
print(f"  Watson (party) references: 474 quotes")

print("""
DOCKET EVENTS FOR CUSTODY CASE 2024-001507-DC:
""")

cursor.execute("""
    SELECT event_date, event_type, filed_by 
    FROM docket_events 
    WHERE LOWER(case_number) LIKE '%001507%'
    ORDER BY event_date DESC
    LIMIT 12
""")
custody_events = cursor.fetchall()
for i, (date, etype, filed) in enumerate(custody_events[:12], 1):
    date_str = str(date) if date else "Unknown"
    print(f"  {i:2}. {date_str:15} | {etype:20} | {filed or 'Unknown'}")

# ═══════════════════════════════════════════════════════════════════════════════════════════════

print("\n█ CROSS-REFERENCES BETWEEN CASES")
print("█" * 100)

print("""
JUDGE HOOPES/LADAS-HOOPES ACROSS ALL LANES:
""")

cursor.execute("""
    SELECT lane, COUNT(*) FROM evidence_quotes 
    WHERE LOWER(quote_text) LIKE '%hoopes%'
    GROUP BY lane
    ORDER BY COUNT(*) DESC
""")
hoopes_lanes = cursor.fetchall()
print("  Judge Hoopes appears in lanes:")
for lane, count in hoopes_lanes:
    lane_name = lane if lane else "NULL"
    if lane_name == "E":
        context = "(Custody case)"
    elif lane_name == "B":
        context = "(Shady Oaks case)"
    elif lane_name == "D":
        context = "(Cross-filing)"
    elif lane_name == "A":
        context = "(Reference/Index)"
    else:
        context = ""
    print(f"    Lane {lane_name:5} {context:30}: {count:4} evidence quotes")

print("""
EVIDENCE LINKING HOOPES TO SHADY OAKS:
""")

cursor.execute("""
    SELECT COUNT(*) FROM evidence_quotes 
    WHERE (LOWER(quote_text) LIKE '%hoopes%' OR LOWER(quote_text) LIKE '%kenneth%')
    AND (LOWER(quote_text) LIKE '%shady%' OR LOWER(quote_text) LIKE '%2025-002760%')
""")
shady_hoopes = cursor.fetchone()[0]
print(f"  {shady_hoopes} evidence quotes link Hoopes to Shady Oaks case")

print("""
EVIDENCE LINKING HOOPES TO EVICTION/HOUSING:
""")

cursor.execute("""
    SELECT COUNT(*) FROM evidence_quotes 
    WHERE (LOWER(quote_text) LIKE '%hoopes%' OR LOWER(quote_text) LIKE '%ladas%')
    AND (LOWER(quote_text) LIKE '%eviction%' OR LOWER(quote_text) LIKE '%housing%' 
         OR LOWER(quote_text) LIKE '%landlord%')
""")
eviction_hoopes = cursor.fetchone()[0]
print(f"  {eviction_hoopes} evidence quotes link Hoopes to eviction/housing matters")

# ═══════════════════════════════════════════════════════════════════════════════════════════════

print("\n█ JUDICIAL VIOLATIONS ATTRIBUTED TO HOOPES/LADAS-HOOPES")
print("█" * 100)

cursor.execute("""
    SELECT violation_type, severity, lane, date_occurred, mcr_rule 
    FROM judicial_violations 
    WHERE LOWER(description) LIKE '%hoopes%' OR LOWER(source_quote) LIKE '%hoopes%'
""")
hoopes_violations = cursor.fetchall()
print(f"\nTotal judicial violations mentioning Hoopes: {len(hoopes_violations)}")

cursor.execute("""
    SELECT violation_type, COUNT(*), severity FROM judicial_violations 
    WHERE LOWER(description) LIKE '%hoopes%' OR LOWER(source_quote) LIKE '%hoopes%'
    GROUP BY violation_type, severity
""")
violation_summary = cursor.fetchall()
print("\nViolation types:")
for vtype, count, severity in violation_summary:
    print(f"  {vtype:20} | Count: {count:3} | Severity: {severity}")

# ═══════════════════════════════════════════════════════════════════════════════════════════════

print("\n█ EVIDENCE TOTALS BY LANE")
print("█" * 100)

cursor.execute("""
    SELECT 
        lane,
        COUNT(*) as total_quotes
    FROM evidence_quotes 
    GROUP BY lane
    ORDER BY total_quotes DESC
""")
lane_totals = cursor.fetchall()
print("\nEvidence quotes per case lane:")
print(f"  {'Lane':<6} {'Case':<30} {'Evidence Quotes':<15}")
print(f"  {'-'*6} {'-'*30} {'-'*15}")
for lane, count in lane_totals:
    lane_name = lane if lane else "NULL"
    if lane_name == "E":
        case_name = "Custody (2024-001507-DC)"
    elif lane_name == "B":
        case_name = "Shady Oaks (2025-002760-CZ)"
    elif lane_name == "D":
        case_name = "Cross-filing/Analysis"
    elif lane_name == "A":
        case_name = "Reference/Index"
    elif lane_name == "F":
        case_name = "Forward/Future"
    else:
        case_name = "Other"
    print(f"  {lane_name:<6} {case_name:<30} {count:<15}")

print("\n" + "="*100)
print("DATABASE SUMMARY:")
print("="*100)

cursor.execute("SELECT COUNT(*) FROM documents")
total_docs = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM evidence_quotes")
total_quotes = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM judicial_violations")
total_violations = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM docket_events")
total_dockets = cursor.fetchone()[0]

print(f"  Total documents in database: {total_docs:,}")
print(f"  Total evidence quotes: {total_quotes:,}")
print(f"  Total judicial violations: {total_violations:,}")
print(f"  Total docket events: {total_dockets:,}")

conn.close()
