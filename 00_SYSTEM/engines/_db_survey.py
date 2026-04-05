import sqlite3
from pathlib import Path
conn = sqlite3.connect(str(Path(__file__).resolve().parents[2] / "litigation_context.db"))
conn.execute("PRAGMA busy_timeout=60000")
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA cache_size=-32000")
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
    except Exception:
        pass
conn.close()
