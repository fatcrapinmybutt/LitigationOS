"""Check communities table schema in mbp_brain.db"""
import sqlite3, os

db = r"C:\Users\andre\LitigationOS\mbp_brain.db"
conn = sqlite3.connect(db)
conn.execute("PRAGMA busy_timeout=60000")

print("=== communities table schema ===")
for row in conn.execute("PRAGMA table_info(communities)").fetchall():
    print(f"  col {row[0]}: {row[1]} ({row[2]}) nullable={not row[3]} default={row[4]}")

print("\n=== communities sample (5 rows) ===")
for row in conn.execute("SELECT * FROM communities LIMIT 5").fetchall():
    print(f"  {row}")

print(f"\n=== communities row count ===")
cnt = conn.execute("SELECT COUNT(*) FROM communities").fetchone()[0]
print(f"  {cnt} rows")

print("\n=== node_analytics sample (3 rows) ===")
for row in conn.execute("SELECT * FROM node_analytics LIMIT 3").fetchall():
    print(f"  {row}")

print("\n=== detected_patterns sample (3 rows) ===")
for row in conn.execute("SELECT * FROM detected_patterns LIMIT 3").fetchall():
    print(f"  {row}")

conn.close()
print("\nDONE")
