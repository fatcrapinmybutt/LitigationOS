import sqlite3
conn = sqlite3.connect(r'C:\Users\andre\LitigationOS\litigation_context.db')
cur = conn.cursor()

# Sample Emily messages
print('=== EMILY MESSAGES (first 5) ===')
cur.execute("SELECT id, message_date, message_time, message_text FROM appclose_messages WHERE sender='Emily Watson' ORDER BY id LIMIT 5")
for row in cur.fetchall():
    print(f'ID:{row[0]} | {row[1]} {row[2]}')
    print(f'  TEXT: {repr(row[3][:200])}')
    print()

# Sample Andrew messages
print('=== ANDREW MESSAGES (first 5) ===')
cur.execute("SELECT id, message_date, message_time, message_text FROM appclose_messages WHERE sender='Andrew Pigors' ORDER BY id LIMIT 5")
for row in cur.fetchall():
    print(f'ID:{row[0]} | {row[1]} {row[2]}')
    print(f'  TEXT: {repr(row[3][:200])}')
    print()

# Sample violations
print('=== VIOLATIONS (first 5) ===')
cur.execute("SELECT violation_type, content, legal_basis, severity FROM appclose_violations LIMIT 5")
for row in cur.fetchall():
    print(f'TYPE: {row[0]} | SEV: {row[3]}')
    print(f'  CONTENT: {repr(row[1][:150])}')
    print(f'  LEGAL: {repr(row[2][:150])}')
    print()

# Adversary evidence quotes count
print('=== ADVERSARY EVIDENCE QUOTES ===')
cur.execute("SELECT speaker, COUNT(*) FROM evidence_quotes WHERE speaker LIKE '%watson%' OR speaker LIKE '%mcneill%' OR speaker LIKE '%judge%' GROUP BY speaker")
for row in cur.fetchall():
    print(row)

# Violation types
print('\n=== VIOLATION TYPES ===')
cur.execute("SELECT violation_type, COUNT(*) FROM appclose_violations GROUP BY violation_type")
for row in cur.fetchall():
    print(row)

# Judicial violation judges
print('\n=== JUDGES ===')
cur.execute("SELECT judge_name, COUNT(*) FROM judicial_violations GROUP BY judge_name")
for row in cur.fetchall():
    print(row)

conn.close()
