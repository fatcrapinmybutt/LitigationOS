import sys, sqlite3, os
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')
db = r'C:\Users\andre\LitigationOS\litigation_context.db'
conn = sqlite3.connect(db)
conn.execute('PRAGMA busy_timeout=60000')
# Search deadlines for sanction
rows = conn.execute("SELECT * FROM deadlines WHERE description LIKE '%sanction%' OR description LIKE '%250%' OR due_date_iso LIKE '%sanction%'").fetchall()
cols = [d[0] for d in conn.execute("SELECT * FROM deadlines LIMIT 0").description]
print("=== DEADLINES w/ sanction ===")
for r in rows:
    print(dict(zip(cols, r)))
# Search claims
rows2 = conn.execute("SELECT claim_id, claim_type, description FROM claims WHERE description LIKE '%sanction%' OR description LIKE '%frivolous%' LIMIT 10").fetchall()
print("\n=== CLAIMS w/ sanction/frivolous ===")
for r in rows2:
    print(r)
# Search judicial_violations
try:
    rows3 = conn.execute("SELECT COUNT(*) FROM judicial_violations WHERE description LIKE '%sanction%' OR description LIKE '%frivolous%'").fetchone()
    print(f"\n=== Judicial violations mentioning sanction/frivolous: {rows3[0]} ===")
except: pass
conn.close()
