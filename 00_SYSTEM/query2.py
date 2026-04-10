import sqlite3
print('=' * 70)
print('ALL TABLES IN court_forms.db')
print('=' * 70)
conn = sqlite3.connect(r'C:\Users\andre\LitigationOS\court_forms.db')
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = cursor.fetchall()
if not tables:
  print('(No tables found)')
else:
  for (table,) in tables:
    cursor.execute("PRAGMA table_info({})".format(table))
    cols = cursor.fetchall()
    cursor.execute("SELECT COUNT(*) FROM {}".format(table))
    count = cursor.fetchone()[0]
    col_names = ', '.join([col[1] for col in cols])
    print()
    print('  ' + table)
    print('    Columns: ' + col_names)
    print('    Rows: ' + str(count))

conn.close()
