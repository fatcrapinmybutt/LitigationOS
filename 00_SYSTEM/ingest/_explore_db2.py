import sqlite3
conn = sqlite3.connect(r'C:\Users\andre\LitigationOS\litigation_context.db')
cur = conn.cursor()

# Focus on key tables
for tbl in ['appclose_messages', 'appclose_violations', 'judicial_violations', 'evidence_quotes']:
    print(f'=== {tbl} ===')
    cur.execute(f'PRAGMA table_info("{tbl}")')
    for col in cur.fetchall():
        print(f'  {col}')
    cur.execute(f'SELECT COUNT(*) FROM "{tbl}"')
    print(f'  ROW COUNT: {cur.fetchone()[0]}')
    print()

# Sample data
print('--- appclose_messages sample ---')
cur.execute('SELECT * FROM appclose_messages LIMIT 2')
cols = [d[0] for d in cur.description]
print('COLS:', cols)
for row in cur.fetchall():
    print(row[:5], '...')

print('\n--- appclose_violations sample ---')
cur.execute('SELECT * FROM appclose_violations LIMIT 2')
cols = [d[0] for d in cur.description]
print('COLS:', cols)
for row in cur.fetchall():
    print(row[:5], '...')

print('\n--- judicial_violations sample ---')
cur.execute('SELECT * FROM judicial_violations LIMIT 2')
cols = [d[0] for d in cur.description]
print('COLS:', cols)
for row in cur.fetchall():
    print(row[:5], '...')

print('\n--- evidence_quotes adversary sample ---')
cur.execute("SELECT * FROM evidence_quotes LIMIT 5")
cols = [d[0] for d in cur.description]
print('COLS:', cols)
for row in cur.fetchall():
    print(row[:5], '...')

# sender stats
print('\n--- sender distribution ---')
cur.execute('SELECT sender, COUNT(*) FROM appclose_messages GROUP BY sender')
for row in cur.fetchall():
    print(row)

conn.close()
