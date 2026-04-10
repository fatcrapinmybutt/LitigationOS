"""Query ex parte orders from litigation_context.db for Tab G-1 tabulation."""
import sqlite3
import os

DB = r"C:\Users\andre\LitigationOS\litigation_context.db"

conn = sqlite3.connect(DB)
conn.execute("PRAGMA busy_timeout=60000")
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA cache_size=-32000")

print("=== TIMELINE EVENTS: EX PARTE ORDERS ===")
try:
    rows = conn.execute("""
        SELECT event_date, event_text 
        FROM timeline_events 
        WHERE event_text LIKE '%ex parte%order%'
        ORDER BY event_date
    """).fetchall()
    for r in rows[:80]:
        print(f"  {r[0]} | {r[1][:150]}")
    print(f"  TOTAL: {len(rows)} rows")
except Exception as e:
    print(f"  ERROR: {e}")

print("\n=== TIMELINE EVENTS: SPECIFIC ORDER DATES ===")
try:
    rows = conn.execute("""
        SELECT DISTINCT event_date, event_text 
        FROM timeline_events 
        WHERE (event_text LIKE '%ex parte%' AND event_text LIKE '%order%')
           OR (event_text LIKE '%ex parte%' AND event_text LIKE '%signed%')
           OR (event_text LIKE '%ex parte%' AND event_text LIKE '%entered%')
           OR (event_text LIKE '%ex parte%' AND event_text LIKE '%issued%')
        ORDER BY event_date
    """).fetchall()
    for r in rows[:60]:
        print(f"  {r[0]} | {r[1][:160]}")
    print(f"  TOTAL: {len(rows)} rows")
except Exception as e:
    print(f"  ERROR: {e}")

print("\n=== JUDICIAL VIOLATIONS: EX PARTE TYPE ===")
try:
    cols = [r[1] for r in conn.execute("PRAGMA table_info(judicial_violations)").fetchall()]
    print(f"  Columns: {cols}")
    
    rows = conn.execute("""
        SELECT * FROM judicial_violations 
        WHERE violation_type LIKE '%ex_parte%' OR violation_type LIKE '%ex parte%'
        ORDER BY date_occurred
        LIMIT 40
    """).fetchall()
    for r in rows[:40]:
        print(f"  {r}")
    print(f"  TOTAL ex_parte violations: {len(rows)}")
except Exception as e:
    print(f"  ERROR: {e}")

print("\n=== KEY DATES: ORDERS IN APPENDIX ===")
key_dates = [
    '2023-10-15', '2023-12-04', '2024-04-11', '2024-04-29', 
    '2024-05-23', '2024-07-01', '2024-07-17', '2024-08-23',
    '2025-04-25', '2025-07-17', '2025-08-08', '2025-08-09',
    '2025-09-09', '2025-09-28', '2025-10-08'
]
for d in key_dates:
    try:
        rows = conn.execute("""
            SELECT event_date, event_text FROM timeline_events
            WHERE event_date = ? OR event_date LIKE ?
            LIMIT 5
        """, (d, d + '%')).fetchall()
        if rows:
            for r in rows:
                print(f"  {r[0]} | {r[1][:150]}")
    except:
        pass

print("\n=== MOTIONS FILED BY FATHER ===")
try:
    rows = conn.execute("""
        SELECT event_date, event_text FROM timeline_events
        WHERE (event_text LIKE '%Pigors%filed%' OR event_text LIKE '%father%filed%' 
               OR event_text LIKE '%plaintiff%filed%' OR event_text LIKE '%Andrew%filed%'
               OR event_text LIKE '%filed%motion%')
        ORDER BY event_date
        LIMIT 40
    """).fetchall()
    for r in rows:
        print(f"  {r[0]} | {r[1][:160]}")
    print(f"  TOTAL: {len(rows)}")
except Exception as e:
    print(f"  ERROR: {e}")

print("\n=== MOTION DISPOSITIONS ===")
try:
    rows = conn.execute("""
        SELECT event_date, event_text FROM timeline_events
        WHERE event_text LIKE '%denied%' OR event_text LIKE '%dismissed%'
           OR event_text LIKE '%overruled%' OR event_text LIKE '%frivolous%'
        ORDER BY event_date
        LIMIT 30
    """).fetchall()
    for r in rows:
        print(f"  {r[0]} | {r[1][:160]}")
    print(f"  TOTAL: {len(rows)}")
except Exception as e:
    print(f"  ERROR: {e}")

print("\n=== EVIDENCE QUOTES: MCR 2.003 DISQUALIFICATION ===")
try:
    rows = conn.execute("""
        SELECT quote_text, source_file FROM evidence_quotes
        WHERE quote_text LIKE '%disqualif%' AND quote_text LIKE '%denied%'
        AND is_duplicate = 0
        LIMIT 10
    """).fetchall()
    for r in rows:
        print(f"  {r[1]} | {r[0][:200]}")
except Exception as e:
    print(f"  ERROR: {e}")

print("\n=== EVIDENCE: $250 FILING DEPOSIT ===")
try:
    rows = conn.execute("""
        SELECT quote_text, source_file FROM evidence_quotes
        WHERE (quote_text LIKE '%$250%' OR quote_text LIKE '%filing deposit%' 
               OR quote_text LIKE '%bond%requirement%')
        AND is_duplicate = 0
        LIMIT 10
    """).fetchall()
    for r in rows:
        print(f"  {r[1]} | {r[0][:200]}")
except Exception as e:
    print(f"  ERROR: {e}")

conn.close()
print("\nDONE")
