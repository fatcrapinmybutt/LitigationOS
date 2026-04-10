import sqlite3

print("=" * 70)
print("ALL TABLES IN court_forms.db")
print("=" * 70)
conn = sqlite3.connect(r"C:\Users\andre\LitigationOS\court_forms.db")
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = cursor.fetchall()
if not tables:
  print("(No tables found)")
else:
  for (table,) in tables:
    cursor.execute(f"PRAGMA table_info({table})")
    cols = cursor.fetchall()
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    count = cursor.fetchone()[0]
    col_names = ", ".join([col[1] for col in cols])
    print(f"\n▶ {table}")
    print(f"   Columns: {col_names}")
    print(f"   Rows: {count}")

conn.close()
