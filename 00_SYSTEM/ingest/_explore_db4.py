import sqlite3
conn = sqlite3.connect(r'C:\Users\andre\LitigationOS\litigation_context.db')
cur = conn.cursor()

# Violations
print('=== VIOLATIONS (first 5) ===')
cur.execute("SELECT violation_type, content, legal_basis, severity, relevance FROM appclose_violations LIMIT 5")
for row in cur.fetchall():
    print(f'TYPE: {row[0]} | SEV: {row[3]}')
    print(f'  CONTENT: {repr((row[1] or "")[:200])}')
    print(f'  LEGAL: {repr((row[2] or "")[:200])}')
    print(f'  RELEVANCE: {repr((row[4] or "")[:200])}')
    print()

# Adversary evidence quotes
print('=== ADVERSARY EVIDENCE QUOTES ===')
cur.execute("SELECT speaker, COUNT(*) FROM evidence_quotes WHERE lower(speaker) LIKE '%watson%' OR lower(speaker) LIKE '%mcneill%' OR lower(speaker) LIKE '%judge%' GROUP BY speaker")
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

# Sample judicial violations
print('\n=== JUDICIAL VIOLATIONS sample ===')
cur.execute("SELECT canon_number, severity, violation_description FROM judicial_violations LIMIT 3")
for row in cur.fetchall():
    print(f'CANON: {row[0]} | SEV: {row[1]}')
    print(f'  DESC: {repr((row[2] or "")[:200])}')
    print()

# Emily last messages
print('=== EMILY LAST 5 MESSAGES ===')
cur.execute("SELECT id, message_date, message_time, message_text FROM appclose_messages WHERE sender='Emily Watson' ORDER BY id DESC LIMIT 5")
for row in cur.fetchall():
    print(f'ID:{row[0]} | {row[1]} {row[2]}')
    print(f'  TEXT: {repr((row[3] or "")[:300])}')
    print()

conn.close()
