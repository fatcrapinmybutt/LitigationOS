import sqlite3

db_path = r'C:\Users\andre\LitigationOS\litigation_context.db'

conn = sqlite3.connect(db_path, timeout=60)
cur = conn.cursor()

print("=" * 100)
print("HEARING & PROCEDURAL ANALYSIS")
print("=" * 100)

print("\n1. HEARING CALENDAR (by result type):")
try:
    cur.execute("""
        SELECT event_type, COUNT(*) as cnt
        FROM docket_events
        WHERE event_type LIKE '%hearing%'
        GROUP BY event_type
        ORDER BY cnt DESC
    """)
    for row in cur.fetchall():
        print(f"  {row[0]:<40} : {row[1]:>3}")
except Exception as e:
    print(f"  [Error] {e}")

print("\n2. ALL DOCKET EVENT TYPES (Summary):")
try:
    cur.execute("""
        SELECT event_type, COUNT(*) as cnt
        FROM docket_events
        GROUP BY event_type
        ORDER BY cnt DESC
    """)
    for row in cur.fetchall():
        print(f"  {row[0]:<40} : {row[1]:>3}")
except Exception as e:
    print(f"  [Error] {e}")

print("\n3. PPO TIMELINE COMPLETE (row count & sample):")
try:
    cur.execute("PRAGMA table_info(ppo_timeline_complete)")
    schema = cur.fetchall()
    print("  Columns:")
    for row in schema[:8]:
        print(f"    - {row[1]} ({row[2]})")
    
    cur.execute("SELECT COUNT(*) FROM ppo_timeline_complete")
    count = cur.fetchone()[0]
    print(f"\n  Total records: {count}")
except Exception as e:
    print(f"  [Error] {e}")

print("\n4. PERMAFIX R12/R13/R14 OPERATING ORDERS:")
for table in ['permafix_r12_operating_orders', 'permafix_r14_operating_orders']:
    try:
        cur.execute(f"PRAGMA table_info({table})")
        schema = cur.fetchall()
        if schema:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]
            print(f"\n  {table} ({count} records):")
            print("    Columns:")
            for row in schema[:6]:
                print(f"      - {row[1]} ({row[2]})")
    except Exception as e:
        pass

print("\n5. CONTRADICTION TIMELINE ANALYSIS:")
try:
    cur.execute("PRAGMA table_info(contradiction_timeline)")
    schema = cur.fetchall()
    if schema:
        cur.execute("SELECT COUNT(*) FROM contradiction_timeline")
        count = cur.fetchone()[0]
        print(f"  Records: {count}")
        print("  Columns:")
        for row in schema[:8]:
            print(f"    - {row[1]} ({row[2]})")
except Exception as e:
    print(f"  [Error] {e}")

print("\n6. CONSTITUTIONAL BRIEF SECTIONS:")
try:
    cur.execute("""
        SELECT section_title, COUNT(*) as cnt
        FROM constitutional_brief_sections
        GROUP BY section_title
        ORDER BY cnt DESC
        LIMIT 20
    """)
    rows = cur.fetchall()
    if rows:
        for row in rows:
            print(f"  {row[0]:<50} : {row[1]:>3}")
    else:
        print("  [No results]")
except Exception as e:
    print(f"  [Error] {e}")

print("\n7. CHRONOLOGICAL MISCONDUCT TIMELINE (sample):")
try:
    cur.execute("""
        SELECT date, issue
        FROM chronological_misconduct
        ORDER BY date DESC
        LIMIT 20
    """)
    rows = cur.fetchall()
    for row in rows:
        print(f"  {row[0]:<20} | {row[1]:<50}")
except Exception as e:
    print(f"  [Error] {e}")

print("\n8. HEARING TRANSCRIPTS (row count):")
try:
    cur.execute("SELECT COUNT(*) FROM hearing_transcripts")
    count = cur.fetchone()[0]
    print(f"  Total records: {count}")
    
    cur.execute("PRAGMA table_info(hearing_transcripts)")
    schema = cur.fetchall()
    print("  Columns:")
    for row in schema[:6]:
        print(f"    - {row[1]} ({row[2]})")
except Exception as e:
    print(f"  [Error] {e}")

print("\n9. PPO CUSTODY CROSS REFERENCE:")
try:
    cur.execute("""
        SELECT COUNT(*) FROM ppo_custody_cross_reference
    """)
    count = cur.fetchone()[0]
    print(f"  Total records: {count}")
    
    cur.execute("PRAGMA table_info(ppo_custody_cross_reference)")
    schema = cur.fetchall()
    print("  Columns:")
    for row in schema[:6]:
        print(f"    - {row[1]} ({row[2]})")
except Exception as e:
    print(f"  [Error] {e}")

print("\n10. PROPOSED ORDERS (by disposition):")
try:
    cur.execute("""
        SELECT status, COUNT(*) as cnt
        FROM proposed_orders
        GROUP BY status
        ORDER BY cnt DESC
    """)
    rows = cur.fetchall()
    if rows:
        for row in rows:
            print(f"  {row[0]:<40} : {row[1]:>3}")
    else:
        print("  [No results]")
except Exception as e:
    print(f"  [Error] {e}")

conn.close()
