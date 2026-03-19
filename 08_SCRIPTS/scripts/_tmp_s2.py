import sys, sqlite3
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')
db = r'C:\Users\andre\LitigationOS\litigation_context.db'
conn = sqlite3.connect(db)
conn.execute('PRAGMA busy_timeout=60000')
# Get deadlines schema
cols = conn.execute("PRAGMA table_info(deadlines)").fetchall()
print("=== deadlines columns ===")
for c in cols: print(c[1], c[2])
# Get all deadlines
rows = conn.execute("SELECT * FROM deadlines LIMIT 20").fetchall()
colnames = [c[1] for c in cols]
print("\n=== deadlines rows ===")
for r in rows:
    print(dict(zip(colnames, r)))
conn.close()
