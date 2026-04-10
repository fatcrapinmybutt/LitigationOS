#!/usr/bin/env python3
"""Fix remaining Phase A issues: reset 'pending' → re-mark, verify 'COPIED'."""
import sqlite3, os

DB = r"D:\LitigationOS_tmp\consolidation_state.db"
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
conn.execute("PRAGMA busy_timeout=60000")
conn.execute("PRAGMA journal_mode=WAL")

# ── Step 1: Reset 2,500 'pending' to NULL ──
reset = conn.execute("UPDATE file_inventory SET copy_status = NULL WHERE copy_status = 'pending'").rowcount
conn.commit()
print(f"Step 1: Reset {reset:,} 'pending' → NULL")

# ── Step 2: Re-mark the newly NULL files ──
DRIVES = {'D:': 'D_DRIVE', 'F:': 'F_DRIVE', 'G:': 'G_DRIVE', 'I:': 'I_DRIVE'}
total_can = 0
total_dup = 0
total_empty = 0

# Mark empty
emp = conn.execute("""
    UPDATE file_inventory SET copy_status = 'EMPTY_SKIP'
    WHERE (file_size = 0 OR file_size IS NULL)
    AND (copy_status IS NULL OR copy_status = '')
""").rowcount
conn.commit()
total_empty = emp
print(f"Step 2a: Marked {emp} empty files")

for drive in DRIVES:
    rows = conn.execute("""
        SELECT id, xxhash, modified_date, source_path
        FROM file_inventory
        WHERE source_drive = ?
        AND file_size > 0
        AND xxhash IS NOT NULL AND xxhash != '' AND xxhash NOT LIKE 'ERROR%' AND xxhash != 'EMPTY_FILE'
        AND (copy_status IS NULL OR copy_status = '')
        ORDER BY xxhash, modified_date DESC, LENGTH(source_path) ASC
    """, (drive,)).fetchall()

    if not rows:
        continue

    current_hash = None
    batch_can = []
    batch_dup = []

    for r in rows:
        fid, xhash = r['id'], r['xxhash']
        # Check if this hash already has a CANONICAL on ANY drive
        existing = conn.execute(
            "SELECT COUNT(*) FROM file_inventory WHERE xxhash = ? AND copy_status = 'CANONICAL'",
            (xhash,)
        ).fetchone()[0]

        if existing > 0:
            # Hash already has a canonical somewhere — this is a duplicate
            batch_dup.append((fid,))
        elif xhash != current_hash:
            current_hash = xhash
            batch_can.append((fid,))
        else:
            batch_dup.append((fid,))

    if batch_can:
        conn.executemany("UPDATE file_inventory SET copy_status='CANONICAL' WHERE id=?", batch_can)
    if batch_dup:
        conn.executemany("UPDATE file_inventory SET copy_status='DUPLICATE_SKIP' WHERE id=?", batch_dup)
    conn.commit()

    print(f"Step 2b [{drive}]: {len(batch_can)} canonical, {len(batch_dup)} duplicates")
    total_can += len(batch_can)
    total_dup += len(batch_dup)

print(f"\nRe-marked: {total_can} canonical + {total_dup} duplicates + {total_empty} empty")

# ── Step 3: Verify 280 'COPIED' files exist on J:\ ──
copied_rows = conn.execute("""
    SELECT id, source_path, target_path FROM file_inventory WHERE copy_status = 'COPIED'
""").fetchall()

verified = 0
missing = 0
no_target = 0
for r in copied_rows:
    tp = r['target_path']
    if not tp:
        no_target += 1
        continue
    if os.path.exists(tp):
        conn.execute("UPDATE file_inventory SET copy_status = 'VERIFIED' WHERE id = ?", (r['id'],))
        verified += 1
    else:
        # Target doesn't exist — reset to CANONICAL so Phase C re-copies
        conn.execute("UPDATE file_inventory SET copy_status = 'CANONICAL' WHERE id = ?", (r['id'],))
        missing += 1
conn.commit()
print(f"\nStep 3: COPIED verification: {verified} verified, {missing} missing (reset to CANONICAL), {no_target} no target path")

# ── Final Summary ──
print("\n═══ FINAL STATUS ═══")
for row in conn.execute("""
    SELECT COALESCE(copy_status, 'NULL') as status, COUNT(*) as cnt
    FROM file_inventory GROUP BY copy_status ORDER BY cnt DESC
""").fetchall():
    print(f"  {row['status']:20s}: {row['cnt']:>8,}")

null_rem = conn.execute("SELECT COUNT(*) FROM file_inventory WHERE copy_status IS NULL").fetchone()[0]
print(f"\n  Remaining NULL: {null_rem}")
conn.close()
print("\n✅ Phase A COMPLETE")
