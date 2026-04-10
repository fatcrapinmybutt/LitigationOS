#!/usr/bin/env python3
"""Quick state DB status check — read-only."""
import sqlite3

DB = r"D:\LitigationOS_tmp\consolidation_state.db"
conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
conn.execute("PRAGMA busy_timeout=30000")

total = conn.execute("SELECT COUNT(*) FROM file_inventory").fetchone()[0]
print(f"Total files: {total:,}")

print("\nStatus breakdown:")
for row in conn.execute("""
    SELECT COALESCE(copy_status, 'NULL') as status, COUNT(*) as cnt
    FROM file_inventory GROUP BY copy_status ORDER BY cnt DESC
""").fetchall():
    pct = row[1] * 100.0 / total
    print(f"  {row[0]:20s}: {row[1]:>8,}  ({pct:.1f}%)")

print("\nPer-drive canonical counts:")
for row in conn.execute("""
    SELECT source_drive, copy_status, COUNT(*) as cnt
    FROM file_inventory
    WHERE copy_status IN ('CANONICAL', 'DUPLICATE_SKIP', 'EMPTY_SKIP')
    GROUP BY source_drive, copy_status
    ORDER BY source_drive, copy_status
""").fetchall():
    print(f"  {row[0]} {row[1]:20s}: {row[2]:>8,}")

null_count = conn.execute("SELECT COUNT(*) FROM file_inventory WHERE copy_status IS NULL").fetchone()[0]
print(f"\nUnmarked (NULL): {null_count:,}")

if null_count > 0:
    print("\nSample unmarked files:")
    for row in conn.execute("""
        SELECT source_drive, source_path, file_size, xxhash
        FROM file_inventory WHERE copy_status IS NULL LIMIT 10
    """).fetchall():
        print(f"  [{row[0]}] {row[1]} ({row[2]} bytes, hash={row[3][:16] if row[3] else 'NONE'}...)")

conn.close()
