import sqlite3
db = sqlite3.connect(r'C:\Users\andre\LitigationOS\litigation_context.db')
c = db.cursor()
print("=== SHADYOAKS CLAIM TABLE ===")
cols = [r[1] for r in c.execute("PRAGMA table_info(shadyoaks_claim_table)")]
print(f"Columns: {cols}")
for row in c.execute("SELECT * FROM shadyoaks_claim_table LIMIT 20"):
    print(row)
print()
print("=== HOUSING VIOLATIONS (sample) ===")
cols = [r[1] for r in c.execute("PRAGMA table_info(housing_violations)")]
print(f"Columns: {cols}")
for row in c.execute("SELECT * FROM housing_violations LIMIT 10"):
    print(row)
print()
print("=== SHADYOAKS EVIDENCE ===")
for row in c.execute("SELECT * FROM shadyoaks_evidence"):
    print(row)
db.close()
