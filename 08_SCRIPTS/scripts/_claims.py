import sqlite3
db = sqlite3.connect(r'C:\Users\andre\LitigationOS\litigation_context.db')
c = db.cursor()

# Get Shady Oaks claim table details
print("=== SHADYOAKS CLAIM TABLE (49 claims) ===")
cols = [r[1] for r in c.execute("PRAGMA table_info(shadyoaks_claim_table)")]
print(f"Columns: {cols}")
for row in c.execute("SELECT * FROM shadyoaks_claim_table LIMIT 15"):
    print(f"  {row}")

print()
print("=== HOUSING VIOLATIONS (200) ===")
cols = [r[1] for r in c.execute("PRAGMA table_info(housing_violations)")]
print(f"Columns: {cols}")
for row in c.execute("SELECT * FROM housing_violations LIMIT 10"):
    print(f"  {row[:5]}...")

print()
print("=== SHADYOAKS EVIDENCE ===")
cols = [r[1] for r in c.execute("PRAGMA table_info(shadyoaks_evidence)")]
print(f"Columns: {cols}")
for row in c.execute("SELECT * FROM shadyoaks_evidence"):
    print(f"  {row}")

# Top eviction events from chronodb
print()
print("=== TOP EVICTION CHRONODB EVENTS ===")
for row in c.execute("SELECT date_raw, line FROM cyclepack_chronodb WHERE line LIKE '%evict%' OR line LIKE '%shady%' OR line LIKE '%lockout%' OR line LIKE '%abandon%' ORDER BY date_raw LIMIT 20"):
    text = str(row[1])[:150] if row[1] else ''
    print(f"  [{row[0]}] {text}")

# Top housing accusations
print()
print("=== TOP HOUSING ACCUSATIONS ===")
for row in c.execute("SELECT severity, lane, stmt_text FROM hypervisor_c11_accusation_index WHERE stmt_text LIKE '%shady%' OR stmt_text LIKE '%evict%' OR stmt_text LIKE '%housing%' OR stmt_text LIKE '%lockout%' OR stmt_text LIKE '%abandon%' OR stmt_text LIKE '%home%' LIMIT 15"):
    text = str(row[2])[:120] if row[2] else ''
    print(f"  [{row[0]}|{row[1]}] {text}")

# IIED / Watson tort evidence
print()
print("=== IIED / WATSON TORT EVIDENCE (prosecution_timeline) ===")
cols_pt = [r[1] for r in c.execute("PRAGMA table_info(prosecution_timeline)")]
print(f"Columns: {cols_pt[:8]}")
for row in c.execute("SELECT * FROM prosecution_timeline WHERE " + " OR ".join(f"[{c}] LIKE '%IIED%' OR [{c}] LIKE '%Watson%' OR [{c}] LIKE '%tort%' OR [{c}] LIKE '%conspiracy%'" for c in cols_pt[:5]) + " LIMIT 10"):
    print(f"  {row[:5]}...")

db.close()
