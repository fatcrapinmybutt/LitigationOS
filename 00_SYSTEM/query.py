import sqlite3
print('=' * 70)
print('AUTHORITY/LEGAL TABLES IN litigation_context.db')
print('=' * 70)
conn = sqlite3.connect(r'C:\Users\andre\LitigationOS\litigation_context.db')
conn.execute('PRAGMA busy_timeout=60000')
conn.execute('PRAGMA journal_mode=WAL')
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND (name LIKE '%authority%' OR name LIKE '%mcr%' OR name LIKE '%mcl%' OR name LIKE '%mre%' OR name LIKE '%rule%' OR name LIKE '%statute%' OR name LIKE '%canon%' OR name LIKE '%benchbook%' OR name LIKE '%court_form%' OR name LIKE '%citation%') ORDER BY name")
tables = cursor.fetchall()
if not tables:
  print('(No matching tables found)')
else:
  for (table,) in tables:
    print('  ' + table)

print('\nALL TABLES IN litigation_context.db:')
print('=' * 70)
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
all_tables = cursor.fetchall()
for (table,) in all_tables:
  cursor.execute("SELECT COUNT(*) FROM " + table)
  count = cursor.fetchone()[0]
  print("  {}: {} rows".format(table, count))

conn.close()
