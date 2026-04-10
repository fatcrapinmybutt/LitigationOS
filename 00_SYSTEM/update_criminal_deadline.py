"""Update criminal trial deadline — pushed back ~1 month."""
import sqlite3, os
from datetime import date

DB = r"C:\Users\andre\LitigationOS\litigation_context.db"
conn = sqlite3.connect(DB)
conn.execute("PRAGMA busy_timeout=60000")
conn.execute("PRAGMA journal_mode=WAL")

# Update criminal trial deadline from Apr 7 to May 7, 2026
cur = conn.execute("""
    UPDATE deadlines SET due_date = '2026-05-07'
    WHERE title LIKE '%Criminal%Trial%' OR title LIKE '%People v. Pigors%'
""")
print(f"Updated {cur.rowcount} deadline row(s) for criminal trial → 2026-05-07")

# Also check timeline_events for the trial date
cur2 = conn.execute("""
    SELECT id, event_date, event_description FROM timeline_events
    WHERE event_description LIKE '%criminal%trial%' OR event_description LIKE '%People v. Pigors%trial%'
    ORDER BY id DESC LIMIT 5
""")
rows = cur2.fetchall()
if rows:
    print(f"\nRelated timeline events ({len(rows)}):")
    for r in rows:
        print(f"  id={r[0]} date={r[1]} desc={r[2][:80]}")

conn.commit()
conn.close()
print("\n✅ Criminal trial deadline updated to May 7, 2026")
