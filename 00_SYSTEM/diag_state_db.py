"""Diagnose consolidation_state.db — why dedup returns 0."""
import sqlite3

conn = sqlite3.connect(r"D:\LitigationOS_tmp\consolidation_state.db")
conn.execute("PRAGMA busy_timeout=30000")
c = conn.cursor()

print("=== TABLES ===")
for t in c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall():
    print(f"  {t[0]}")

print("\n=== file_inventory SCHEMA ===")
for col in c.execute("PRAGMA table_info(file_inventory)"):
    print(f"  {col[1]:20s} {col[2]:10s}")

print(f"\n=== ROW COUNT: {c.execute('SELECT COUNT(*) FROM file_inventory').fetchone()[0]:,d} ===")

print("\n=== source_drive VALUES ===")
for r in c.execute("SELECT source_drive, COUNT(*) FROM file_inventory GROUP BY source_drive"):
    print(f"  {repr(r[0]):25s} → {r[1]:>8,d} files")

print("\n=== xxhash SAMPLE (10 non-null from I:\\) ===")
for r in c.execute("""
    SELECT xxhash, source_path FROM file_inventory 
    WHERE xxhash IS NOT NULL AND xxhash != '' 
    AND source_drive LIKE '%I%'
    LIMIT 10
"""):
    print(f"  hash={repr(r[0])[:40]:40s}  path={r[1][:60]}")

print("\n=== xxhash NULL vs NOT NULL ===")
for r in c.execute("""
    SELECT source_drive,
           SUM(CASE WHEN xxhash IS NULL OR xxhash = '' THEN 1 ELSE 0 END) as null_cnt,
           SUM(CASE WHEN xxhash IS NOT NULL AND xxhash != '' THEN 1 ELSE 0 END) as hash_cnt
    FROM file_inventory
    GROUP BY source_drive
"""):
    print(f"  {repr(r[0]):25s}  NULL/empty={r[1]:>8,d}  hashed={r[2]:>8,d}")

print("\n=== I:\\ dedup query (HAVING COUNT > 1) ===")
rows = c.execute("""
    SELECT xxhash, COUNT(*) as cnt
    FROM file_inventory
    WHERE source_drive LIKE '%I%' AND xxhash IS NOT NULL AND xxhash != ''
    GROUP BY xxhash
    HAVING COUNT(*) > 1
    ORDER BY cnt DESC
    LIMIT 10
""").fetchall()
print(f"  Groups found: {len(rows)}")
for r in rows:
    print(f"  hash={r[0][:30]}...  count={r[1]}")

# Check if ALL hashes are unique
print("\n=== Hash uniqueness check (I:\\) ===")
total_hashed = c.execute("""
    SELECT COUNT(*) FROM file_inventory
    WHERE source_drive LIKE '%I%' AND xxhash IS NOT NULL AND xxhash != ''
""").fetchone()[0]
unique_hashes = c.execute("""
    SELECT COUNT(DISTINCT xxhash) FROM file_inventory
    WHERE source_drive LIKE '%I%' AND xxhash IS NOT NULL AND xxhash != ''
""").fetchone()[0]
print(f"  Total hashed files: {total_hashed:,d}")
print(f"  Unique hashes:      {unique_hashes:,d}")
print(f"  Duplicates:         {total_hashed - unique_hashes:,d}")

# Cross-drive dupe check (same hash, different drives)
print("\n=== Cross-drive dupes (same hash, different source_drive) ===")
rows = c.execute("""
    SELECT xxhash, COUNT(DISTINCT source_drive) as drive_cnt, COUNT(*) as file_cnt
    FROM file_inventory
    WHERE xxhash IS NOT NULL AND xxhash != ''
    GROUP BY xxhash
    HAVING COUNT(DISTINCT source_drive) > 1
    ORDER BY file_cnt DESC
    LIMIT 10
""").fetchall()
print(f"  Groups found: {len(rows)}")
for r in rows:
    print(f"  hash={r[0][:30]}...  drives={r[1]}  files={r[2]}")

# Check what drive_intelligence.py's DuckDB query actually did differently
print("\n=== DISTINCT xxhash length check ===")
for r in c.execute("""
    SELECT LENGTH(xxhash) as len, COUNT(*) 
    FROM file_inventory 
    WHERE xxhash IS NOT NULL AND xxhash != '' 
    GROUP BY LENGTH(xxhash) 
    ORDER BY COUNT(*) DESC 
    LIMIT 5
"""):
    print(f"  len={r[0]}  count={r[1]:,d}")

conn.close()
