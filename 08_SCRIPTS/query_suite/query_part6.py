import sqlite3

db_path = r'C:\Users\andre\LitigationOS\litigation_context.db'

conn = sqlite3.connect(db_path, timeout=60)
cur = conn.cursor()

print("=" * 100)
print("VIOLATION TYPES BREAKDOWN")
print("=" * 100)

# Judicial violations by canon
print("\n1. JUDICIAL VIOLATIONS BY CANON NUMBER:")
cur.execute("""
    SELECT canon_number, COUNT(*) as cnt
    FROM judicial_violations
    GROUP BY canon_number
    ORDER BY cnt DESC
    LIMIT 20
""")
for row in cur.fetchall():
    print(f"  {row[0]:<30} : {row[1]:>5}")

# Constitutional violations by amendment
print("\n2. CONSTITUTIONAL VIOLATIONS BY AMENDMENT:")
cur.execute("""
    SELECT amendment, COUNT(*) as cnt
    FROM constitutional_violations
    GROUP BY amendment
    ORDER BY cnt DESC
""")
for row in cur.fetchall():
    print(f"  Amendment {row[0]:<20} : {row[1]:>3}")

# Actor violations by actor and type
print("\n3. TOP ACTOR VIOLATIONS (Actor + Violation Type):")
cur.execute("""
    SELECT actor, violation_type, COUNT(*) as cnt
    FROM actor_violations
    GROUP BY actor, violation_type
    ORDER BY cnt DESC
    LIMIT 25
""")
for row in cur.fetchall():
    print(f"  {row[0]:<20} | {row[1]:<30} : {row[2]:>4}")

print("\n4. CONTRADICTION MAP - CONTRADICTION TYPES:")
cur.execute("""
    SELECT contradiction_type, COUNT(*) as cnt
    FROM contradiction_map
    GROUP BY contradiction_type
    ORDER BY cnt DESC
""")
for row in cur.fetchall():
    print(f"  {row[0]:<40} : {row[1]:>5}")

print("\n5. REBUTTAL MATRIX - ASSERTION CATEGORIES:")
cur.execute("""
    SELECT assertion_category, COUNT(*) as cnt
    FROM rebuttal_matrix
    GROUP BY assertion_category
    ORDER BY cnt DESC
    LIMIT 20
""")
for row in cur.fetchall():
    print(f"  {row[0]:<40} : {row[1]:>4}")

print("\n6. EXTRACTED HARMS - CATEGORIES:")
cur.execute("""
    SELECT category, COUNT(*) as cnt
    FROM extracted_harms
    GROUP BY category
    ORDER BY cnt DESC
    LIMIT 30
""")
for row in cur.fetchall():
    print(f"  {row[0]:<40} : {row[1]:>5}")

print("\n7. EXTRACTED HARMS - SUBCATEGORIES (Top 25):")
cur.execute("""
    SELECT category, subcategory, COUNT(*) as cnt
    FROM extracted_harms
    GROUP BY category, subcategory
    ORDER BY cnt DESC
    LIMIT 25
""")
for row in cur.fetchall():
    print(f"  {row[0]:<25} / {row[1]:<25} : {row[2]:>4}")

print("\n8. ADVERSARY HARM SUMMARY:")
cur.execute("""
    SELECT adversary, harm_count, total_mentions
    FROM adversary_harm_summary
    ORDER BY harm_count DESC
""")
for row in cur.fetchall():
    print(f"  {row[0]:<30} : {row[1]:>4} harms in {row[2]:>5} mentions")

print("\n9. ALIENATION TACTICS:")
cur.execute("""
    SELECT tactic, description FROM alienation_tactics LIMIT 50
""")
for row in cur.fetchall():
    print(f"  {row[0]:<40}")
    print(f"    -> {row[1][:80]}")

print("\n10. VIOLATION PATTERNS:")
cur.execute("""
    SELECT pattern_name, frequency
    FROM violation_patterns
    ORDER BY frequency DESC
    LIMIT 20
""")
for row in cur.fetchall():
    print(f"  {row[0]:<40} : {row[1]:>4} occurrences")

conn.close()
