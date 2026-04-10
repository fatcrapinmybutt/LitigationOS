import sqlite3
conn = sqlite3.connect('court_forms.db')
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = c.fetchall()
for t in tables:
    print(t[0])
    c.execute(f"PRAGMA table_info({t[0]})")
    cols = c.fetchall()
    for col in cols:
        print(f"  {col[1]} ({col[2]})")
conn.close()
