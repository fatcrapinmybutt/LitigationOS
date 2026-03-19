import sqlite3
conn = sqlite3.connect(r'C:\Users\andre\LitigationOS\litigation_context.db')
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [r[0] for r in cur.fetchall()]
print(f'Total tables: {len(tables)}\n')
for t in tables:
    try:
        cur.execute(f'SELECT COUNT(*) FROM [{t}]')
        cnt = cur.fetchone()[0]
        if cnt > 0:
            cur.execute(f'PRAGMA table_info([{t}])')
            cols = [r[1] for r in cur.fetchall()]
            print(f'{t}: {cnt:,} rows | {cols[:8]}')
    except:
        pass
conn.close()
