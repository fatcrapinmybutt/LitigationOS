import sqlite3
print('ALL TABLES IN litigation_context.db (continued)')
print('=' * 70)
conn = sqlite3.connect(r'C:\Users\andre\LitigationOS\litigation_context.db')
cursor = conn.cursor()

# Skip first ~100 tables and list the rest
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
all_tables = [t[0] for t in cursor.fetchall()]

# Show tables 100+ 
for i, table in enumerate(sorted(all_tables)[100:200]):
  cursor.execute("SELECT COUNT(*) FROM {}".format(table))
  count = cursor.fetchone()[0]
  print("  {}: {} rows".format(table, count))

conn.close()
