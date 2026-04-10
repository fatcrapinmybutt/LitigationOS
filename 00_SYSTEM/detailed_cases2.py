import sqlite3

db_path = r'C:\Users\andre\LitigationOS\litigation_context.db'

conn = sqlite3.connect(db_path)
conn.execute('PRAGMA busy_timeout=60000')
cursor = conn.cursor()

print("="*100)
print("DETAILED CASE INFORMATION - FINAL REPORT")
print("="*100)

# 1. EVICTION CASE - Lane E
print("\n" + "="*100)
print("1. EVICTION CASE (LANE E) - Related to Maria Ladas")
print("="*100)

cursor.execute("""
    SELECT DISTINCT case_number FROM documents WHERE lane = 'E' 
    LIMIT 1
""")
lane_e_info = cursor.fetchone()
print(f"Lane E case number: {lane_e_info}")

# Get Eviction docket events
cursor.execute("""
    SELECT event_date, event_type, description, filed_by 
    FROM docket_events 
    WHERE LOWER(case_number) LIKE '%1507%' OR LOWER(case_number) LIKE '%dc%'
    ORDER BY event_date DESC
    LIMIT 15
""")
events = cursor.fetchall()
print(f"\nDocket events in eviction-related cases: {len(events)}")
for event in events[:10]:
    filed_by = event[3] if event[3] else "Unknown"
    print(f"  {str(event[0])[:12]} | {str(event[1])[:20]} | By: {filed_by[:15]}")
    if event[2]:
        preview = event[2][:75] if len(event[2]) > 75 else event[2]
        print(f"    {preview}")

# Search for Maria Ladas
cursor.execute("""
    SELECT DISTINCT quote_text, source_file, lane 
    FROM evidence_quotes 
    WHERE LOWER(quote_text) LIKE '%maria ladas%' OR LOWER(quote_text) LIKE '%ladas hoopes%'
    LIMIT 10
""")
quotes = cursor.fetchall()
print(f"\nEvidence quotes mentioning Maria Ladas or Judge Ladas-Hoopes: {len(quotes)}")
for i, quote in enumerate(quotes[:3], 1):
    source = quote[1][:60] if quote[1] else "Unknown"
    text = quote[0][:100] if quote[0] else ""
    print(f"  {i}. Source: {source}")
    print(f"     Text: {text}...")

# 2. SHADY OAKS CASE - Lane B/D (2025-002760-CZ)
print("\n" + "="*100)
print("2. SHADY OAKS CIVIL CASE (LANE B) - Case 2025-002760-CZ")
print("="*100)

cursor.execute("""
    SELECT COUNT(*) FROM documents WHERE lane = 'B'
""")
lane_b_count = cursor.fetchone()[0]
print(f"Total documents in Lane B: {lane_b_count}")

cursor.execute("""
    SELECT title FROM documents WHERE lane = 'B' LIMIT 5
""")
sample_docs = cursor.fetchall()
print(f"Sample documents:")
for doc in sample_docs:
    print(f"  - {doc[0][:80]}")

# Get violations in Lane B
cursor.execute("""
    SELECT violation_type, description, date_occurred, severity 
    FROM judicial_violations 
    WHERE lane = 'B'
    LIMIT 10
""")
violations = cursor.fetchall()
print(f"\nJudicial violations in Lane B: {len(violations)}")
for i, viol in enumerate(violations[:3], 1):
    date_str = str(viol[2]) if viol[2] else "Unknown"
    print(f"  {i}. Type: {viol[0]} | Severity: {viol[3]} | Date: {date_str}")
    print(f"     {viol[1][:75]}")

# Search for Hoopes in Shady Oaks
cursor.execute("""
    SELECT COUNT(*) FROM evidence_quotes WHERE lane = 'B' AND LOWER(quote_text) LIKE '%hoopes%'
""")
hoopes_count = cursor.fetchone()[0]
print(f"\nHoopes references in Shady Oaks case: {hoopes_count}")

cursor.execute("""
    SELECT DISTINCT quote_text FROM evidence_quotes 
    WHERE lane = 'B' AND LOWER(quote_text) LIKE '%hoopes%'
    LIMIT 3
""")
hoopes_quotes = cursor.fetchall()
for i, quote in enumerate(hoopes_quotes, 1):
    print(f"  {i}. {quote[0][:90]}")

# 3. CUSTODY CASE - Lane E (2024-001507-DC)
print("\n" + "="*100)
print("3. CUSTODY CASE (LANE E) - Case 2024-001507-DC")
print("="*100)

cursor.execute("""
    SELECT COUNT(*) FROM documents WHERE lane = 'E'
""")
lane_e_doc_count = cursor.fetchone()[0]
print(f"Total documents in Lane E: {lane_e_doc_count}")

cursor.execute("""
    SELECT COUNT(*), SUM(CASE WHEN LOWER(quote_text) LIKE '%custody%' THEN 1 ELSE 0 END)
    FROM evidence_quotes WHERE lane = 'E'
""")
lane_e_stats = cursor.fetchone()
print(f"Evidence quotes in Lane E: {lane_e_stats[0]}, Custody-related: {lane_e_stats[1]}")

cursor.execute("""
    SELECT DISTINCT event_date, event_type, description 
    FROM docket_events 
    WHERE LOWER(case_number) LIKE '%001507%'
    ORDER BY event_date DESC
    LIMIT 10
""")
custody_events = cursor.fetchall()
print(f"\nDocket events for custody case: {len(custody_events)}")
for i, event in enumerate(custody_events[:5], 1):
    date_str = str(event[0]) if event[0] else "Unknown"
    desc = event[2][:70] if event[2] else "No description"
    print(f"  {i}. {date_str} - {event[1]}: {desc}")

# Get McNeill mentions
cursor.execute("""
    SELECT COUNT(*) FROM evidence_quotes WHERE lane = 'E' AND LOWER(quote_text) LIKE '%mcneill%'
""")
mcneill_count = cursor.fetchone()[0]
print(f"\nJudge McNeill references in custody case: {mcneill_count}")

# Get Watson mentions
cursor.execute("""
    SELECT COUNT(*) FROM evidence_quotes WHERE lane = 'E' AND LOWER(quote_text) LIKE '%watson%'
""")
watson_count = cursor.fetchone()[0]
print(f"Watson (party) references in custody case: {watson_count}")

# 4. CROSS-REFERENCES ANALYSIS
print("\n" + "="*100)
print("4. CROSS-REFERENCES BETWEEN CASES")
print("="*100)

cursor.execute("""
    SELECT DISTINCT lane FROM evidence_quotes WHERE LOWER(quote_text) LIKE '%hoopes%'
    ORDER BY lane
""")
hoopes_lanes = cursor.fetchall()
hoopes_lane_list = [lane[0] for lane in hoopes_lanes if lane[0]]
print(f"Judge Hoopes/Ladas-Hoopes appears in lanes: {hoopes_lane_list}")

cursor.execute("""
    SELECT COUNT(*) FROM evidence_quotes 
    WHERE (LOWER(quote_text) LIKE '%hoopes%' OR LOWER(quote_text) LIKE '%ladas%')
    AND (LOWER(quote_text) LIKE '%shady%' OR LOWER(quote_text) LIKE '%2025-002760%')
""")
shady_hoopes_cross = cursor.fetchone()[0]
print(f"Evidence linking Hoopes to Shady Oaks case: {shady_hoopes_cross}")

cursor.execute("""
    SELECT COUNT(*) FROM evidence_quotes 
    WHERE (LOWER(quote_text) LIKE '%hoopes%' OR LOWER(quote_text) LIKE '%ladas%')
    AND (LOWER(quote_text) LIKE '%eviction%' OR LOWER(quote_text) LIKE '%landlord%')
""")
eviction_hoopes_cross = cursor.fetchone()[0]
print(f"Evidence linking Hoopes to eviction case: {eviction_hoopes_cross}")

# 5. JUDICIAL VIOLATIONS
print("\n" + "="*100)
print("5. JUDICIAL VIOLATIONS ATTRIBUTED TO HOOPES/LADAS-HOOPES")
print("="*100)

cursor.execute("""
    SELECT violation_type, description, date_occurred, severity, lane, mcr_rule 
    FROM judicial_violations 
    WHERE LOWER(description) LIKE '%hoopes%' OR LOWER(source_quote) LIKE '%hoopes%'
    LIMIT 20
""")
hoopes_violations = cursor.fetchall()
print(f"Total violations mentioning Hoopes: {len(hoopes_violations)}")
if hoopes_violations:
    for i, viol in enumerate(hoopes_violations[:5], 1):
        date_str = str(viol[2]) if viol[2] else "Unknown"
        mcr = viol[5] if viol[5] else "Not specified"
        print(f"  {i}. {viol[0]} | Severity: {viol[3]} | Lane: {viol[4]}")
        print(f"     MCR Rule: {mcr}")
        print(f"     Description: {viol[1][:80]}")

# 6. SUMMARY STATISTICS
print("\n" + "="*100)
print("6. SUMMARY STATISTICS")
print("="*100)

cursor.execute("""
    SELECT 
        lane,
        COUNT(*) as total_quotes,
        SUM(CASE WHEN LOWER(quote_text) LIKE '%hoopes%' THEN 1 ELSE 0 END) as hoopes_mentions,
        SUM(CASE WHEN LOWER(quote_text) LIKE '%ladas%' THEN 1 ELSE 0 END) as ladas_mentions,
        SUM(CASE WHEN LOWER(quote_text) LIKE '%mcneill%' THEN 1 ELSE 0 END) as mcneill_mentions,
        SUM(CASE WHEN LOWER(quote_text) LIKE '%watson%' THEN 1 ELSE 0 END) as watson_mentions
    FROM evidence_quotes 
    GROUP BY lane
    ORDER BY total_quotes DESC
""")
stats = cursor.fetchall()
print("\nEvidence by lane:")
print(f"{'Lane':<6} {'Total':<8} {'Hoopes':<8} {'Ladas':<8} {'McNeill':<8} {'Watson':<8}")
print("-" * 50)
for stat in stats:
    lane = stat[0] or "NULL"
    h = stat[2] if stat[2] else 0
    l = stat[3] if stat[3] else 0
    m = stat[4] if stat[4] else 0
    w = stat[5] if stat[5] else 0
    print(f"{lane:<6} {stat[1]:<8} {h:<8} {l:<8} {m:<8} {w:<8}")

conn.close()
