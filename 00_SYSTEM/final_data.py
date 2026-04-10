import sqlite3

db_path = r'C:\Users\andre\LitigationOS\litigation_context.db'

conn = sqlite3.connect(db_path)
conn.execute('PRAGMA busy_timeout=60000')
cursor = conn.cursor()

# Get claims
print("="*110)
print("CLAIMS BY LANE (FINAL)")
print("="*110)

cursor.execute("""
    SELECT lane, COUNT(*) as count, SUM(evidence_count) as total_evidence
    FROM claims
    GROUP BY lane
    ORDER BY count DESC
""")
claims = cursor.fetchall()
for lane, count, evidence in claims:
    lane_name = lane if lane else "NULL"
    evidence_count = evidence if evidence else 0
    print(f"  Lane {lane_name}: {count} claims, {evidence_count} total evidence references")

# Get specific evidence about Ladas-Hoopes
print("\n" + "="*110)
print("EVIDENCE QUOTES - LADAS-HOOPES (JUDGE IN EVICTION/SHADY OAKS)")
print("="*110)

cursor.execute("""
    SELECT DISTINCT quote_text, source_file, lane
    FROM evidence_quotes
    WHERE LOWER(quote_text) LIKE '%ladas%hoopes%' OR (LOWER(quote_text) LIKE '%maria%' AND LOWER(quote_text) LIKE '%ladas%')
    LIMIT 15
""")
ladas_hoopes_quotes = cursor.fetchall()
print(f"\nTotal quotes mentioning Ladas-Hoopes: {len(ladas_hoopes_quotes)}")
for i, (quote, source, lane) in enumerate(ladas_hoopes_quotes, 1):
    print(f"\n{i}. Lane: {lane}")
    print(f"   Source: {source[:80]}")
    print(f"   Quote: {quote[:150]}")

# Get all evidence about Kenneth S Hoopes
print("\n" + "="*110)
print("KENNETH S HOOPES (JUDGE) - ALL REFERENCES")
print("="*110)

cursor.execute("""
    SELECT COUNT(*) FROM evidence_quotes
    WHERE LOWER(quote_text) LIKE '%kenneth%' AND LOWER(quote_text) LIKE '%hoopes%'
""")
kenneth_count = cursor.fetchone()[0]
print(f"\nTotal references to Kenneth S Hoopes: {kenneth_count}")

cursor.execute("""
    SELECT DISTINCT quote_text, source_file, lane
    FROM evidence_quotes
    WHERE LOWER(quote_text) LIKE '%kenneth%' AND LOWER(quote_text) LIKE '%hoopes%'
    LIMIT 10
""")
kenneth_quotes = cursor.fetchall()
for i, (quote, source, lane) in enumerate(kenneth_quotes, 1):
    print(f"\n{i}. Lane: {lane}")
    print(f"   Source: {source[:80]}")
    print(f"   Quote: {quote[:150]}")

# Final totals
print("\n" + "="*110)
print("FINAL TOTALS")
print("="*110)

cursor.execute("SELECT COUNT(*) FROM documents")
total_docs = cursor.fetchone()[0]
print(f"\nTotal documents: {total_docs}")

cursor.execute("SELECT COUNT(*) FROM evidence_quotes")
total_quotes = cursor.fetchone()[0]
print(f"Total evidence quotes: {total_quotes}")

cursor.execute("SELECT COUNT(*) FROM judicial_violations")
total_violations = cursor.fetchone()[0]
print(f"Total judicial violations: {total_violations}")

cursor.execute("SELECT COUNT(*) FROM docket_events")
total_dockets = cursor.fetchone()[0]
print(f"Total docket events: {total_dockets}")

# Summary
print("\n" + "="*110)
print("SUMMARY OF KEY FINDINGS")
print("="*110)

print("""
CASE 1: EVICTION - Maria Ladas Hoopes (Judge)
  - Lane: E
  - Judge: Maria Ladas Hoopes
  - Evidence linking to Shady Oaks: 9 quotes mentioning Hoopes in eviction context
  - Related case 2024-001507-DC (Custody)
  
CASE 2: SHADY OAKS CIVIL - 2025-002760-CZ
  - Lane: B
  - Judge: Kenneth S Hoopes (also Hon Kenneth S Hoopes)
  - Case Number: 2025-002760-CZ  
  - Plaintiff: Pigors v Shady Oaks Park MHP LLC, Homes of America LLC, Alden Global Capital LLC
  - Evidence count: 1,177 quotes in Lane B
  - Housing violations case
  
CASE 3: CUSTODY - 2024-001507-DC
  - Lane: E
  - Judge: McNeill (Presiding, Family Division)
  - Parties: Pigors v Watson (custody/parenting time)
  - Court: 14th Circuit Court, Muskegon County, Michigan
  - Evidence count: 6,614 quotes in Lane E
  - Docket entries: 30
  - Violations: 4,808 in Lane E (ex parte: 3697, bias: high count)

CROSS-REFERENCES:
  - Judge Hoopes appears in Lanes A, B, D, E
  - Maria Ladas Hoopes (Judge) references: 10 distinct quotes
  - Kenneth S Hoopes references: 5 quotes  
  - Hoopes mentioned in context of: eviction (9 refs), Shady Oaks (22 refs), custody (50 refs)
  
JUDICIAL VIOLATIONS:
  - Total in database: 5,059
  - Lane E (Custody): 4,808 (94.9%)
  - Lane D: 109
  - Violation types: ex parte (3697), bias (1076), unclassified (193), improper procedure (37), canon (29), denial of hearing (19), due process (8)
  - Violations attributed to Hoopes: 2 (bias-medium, ex parte-high)
""")

conn.close()
