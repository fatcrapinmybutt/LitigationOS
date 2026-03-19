import sqlite3

db_path = r'C:\Users\andre\LitigationOS\litigation_context.db'

conn = sqlite3.connect(db_path, timeout=60)
cur = conn.cursor()

print("=" * 100)
print("DETAILED HARM ANALYSIS")
print("=" * 100)

print("\n1. EXTRACTED HARMS - BY SUBCATEGORY (Top 25):")
cur.execute("""
    SELECT category, subcategory, COUNT(*) as cnt
    FROM extracted_harms
    WHERE subcategory IS NOT NULL
    GROUP BY category, subcategory
    ORDER BY cnt DESC
    LIMIT 25
""")
rows = cur.fetchall()
for row in rows:
    sub = row[1] if row[1] else "null"
    print(f"  {row[0]:<25} / {sub:<25} : {row[2]:>4}")

print("\n2. ADVERSARY HARM SUMMARY (with details):")
cur.execute("""
    SELECT adversary, harm_count, total_mentions, top_categories
    FROM adversary_harm_summary
    ORDER BY harm_count DESC
""")
rows = cur.fetchall()
for row in rows:
    print(f"\n  {row[0]}:")
    print(f"    Harms: {row[1]:<4} | Total Mentions: {row[2]:<5}")
    if row[3]:
        print(f"    Top Categories: {row[3]}")

print("\n3. ALIENATION SCORING FRAMEWORK:")
cur.execute("""
    SELECT indicator_name, framework, category, score, max_score
    FROM alienation_scoring
    ORDER BY framework, score DESC
""")
for row in cur.fetchall():
    print(f"  {row[0]:<35} [{row[1]:<10}] {row[2]:<20} Score: {row[3]:>2}/{row[4]}")

print("\n4. PARENTAL ALIENATION EVIDENCE:")
cur.execute("""
    SELECT event_date, description, mcl_factor, severity
    FROM parental_alienation_evidence
    ORDER BY event_date DESC
""")
for row in cur.fetchall():
    print(f"\n  Date: {row[0]:<20} | MCL: {row[2]:<10} | Severity: {row[3]}")
    print(f"    {row[1][:100]}")

print("\n5. WATSON PERJURY COMPILATION - STATEMENT TYPES:")
cur.execute("""
    SELECT COUNT(*) as cnt, watson_member
    FROM watson_perjury_compilation
    GROUP BY watson_member
    ORDER BY cnt DESC
""")
for row in cur.fetchall():
    print(f"  {row[1]:<30} : {row[0]:>5} statement contradictions")

print("\n6. OMEGA VIOLATION ANALYSIS:")
cur.execute("""
    SELECT analysis_type, category, count, severity_breakdown
    FROM omega_violation_analysis
    ORDER BY count DESC
    LIMIT 20
""")
for row in cur.fetchall():
    print(f"  [{row[0]}] {row[1]:<40} : {row[2]:>4}")
    if row[3]:
        print(f"    Severity: {row[3][:80]}")

print("\n7. OMEGA EVIDENCE PATTERNS (Top 25):")
cur.execute("""
    SELECT category, keyword, match_count
    FROM omega_evidence_patterns
    ORDER BY match_count DESC
    LIMIT 25
""")
for row in cur.fetchall():
    print(f"  {row[0]:<25} | '{row[1]:<30}' : {row[2]:>4} matches")

print("\n8. BERRY ETHICS VIOLATIONS BY MRPC:")
cur.execute("""
    SELECT mrpc_rule, violation_type, COUNT(*) as cnt
    FROM berry_ethics_violations
    GROUP BY mrpc_rule, violation_type
    ORDER BY cnt DESC
    LIMIT 20
""")
for row in cur.fetchall():
    print(f"  {row[0]:<15} | {row[1]:<30} : {row[2]:>3}")

print("\n9. APPCLOSE VIOLATIONS:")
cur.execute("""
    SELECT violation_type, COUNT(*) as cnt
    FROM appclose_violations
    GROUP BY violation_type
    ORDER BY cnt DESC
""")
for row in cur.fetchall():
    print(f"  {row[0]:<40} : {row[1]:>3}")

conn.close()
