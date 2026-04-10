import sqlite3
conn = sqlite3.connect(r'C:\Users\andre\LitigationOS\court_forms.db')
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
print('TABLES:')
for row in c.fetchall():
    print('  ' + row[0])
