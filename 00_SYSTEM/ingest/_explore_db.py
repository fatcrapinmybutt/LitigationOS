import sqlite3
conn = sqlite3.connect(r'C:\Users\andre\LitigationOS\litigation_context.db')
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cur.fetchall()
for t in tables:
    name = t[0]
    print(f'=== {name} ===')
    cur.execute(f'PRAGMA table_info("{name}")')
    for col in cur.fetchall():
        print(f'  {col}')
    cur.execute(f'SELECT COUNT(*) FROM "{name}"')
    print(f'  ROW COUNT: {cur.fetchone()[0]}')
    print()
conn.close()
