#!/usr/bin/env python3
"""Phase A: Mark canonical files in consolidation_state.db (dedup selection)."""
import sqlite3, time, sys

STATE_DB = r"D:\LitigationOS_tmp\consolidation_state.db"
DRIVE_MAP = {'D:': 'D_DRIVE', 'F:': 'F_DRIVE', 'G:': 'G_DRIVE', 'I:': 'I_DRIVE'}
REAL = ('CANONICAL','DUPLICATE_SKIP','EMPTY_SKIP','COPIED','VERIFIED','COPY_ERROR','SOURCE_MISSING')

def run():
    db = sqlite3.connect(STATE_DB)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA busy_timeout=60000")
    db.execute("PRAGMA journal_mode=WAL")

    total = db.execute("SELECT COUNT(*) FROM file_inventory").fetchone()[0]
    already = db.execute(
        f"SELECT COUNT(*) FROM file_inventory WHERE copy_status IN ({','.join('?'*len(REAL))})", REAL
    ).fetchone()[0]

    print(f"Total files: {total:,}")
    print(f"Already marked (real status): {already:,}")

    if already >= total:
        print("All files already marked. Done.")
        db.close()
        return

    # Reset any bogus statuses (like 'pending') back to NULL
    reset = db.execute(
        f"UPDATE file_inventory SET copy_status = NULL WHERE copy_status IS NOT NULL AND copy_status NOT IN ({','.join('?'*len(REAL))})", REAL
    ).rowcount
    if reset > 0:
        db.commit()
        print(f"Reset {reset:,} invalid statuses to NULL")

    # Mark empty files
    db.execute("""
        UPDATE file_inventory SET copy_status = 'EMPTY_SKIP'
        WHERE (file_size = 0 OR file_size IS NULL)
        AND (copy_status IS NULL OR copy_status = '')
    """)
    db.commit()
    empty = db.execute("SELECT COUNT(*) FROM file_inventory WHERE copy_status = 'EMPTY_SKIP'").fetchone()[0]
    print(f"Empty files: {empty:,}")

    t0 = time.time()
    total_can = 0
    total_dup = 0

    for drive in DRIVE_MAP:
        rows = db.execute("""
            SELECT id, xxhash, modified_date, source_path
            FROM file_inventory
            WHERE source_drive = ?
            AND file_size > 0
            AND xxhash IS NOT NULL AND xxhash != '' AND xxhash NOT LIKE 'ERROR%' AND xxhash != 'EMPTY_FILE'
            AND (copy_status IS NULL OR copy_status = '')
            ORDER BY xxhash, modified_date DESC, LENGTH(source_path) ASC
        """, (drive,)).fetchall()

        if not rows:
            print(f"  {drive}: No unmarked files")
            continue

        current_hash = None
        batch_can = []
        batch_dup = []

        for r in rows:
            if r['xxhash'] != current_hash:
                current_hash = r['xxhash']
                batch_can.append((r['id'],))
            else:
                batch_dup.append((r['id'],))

        db.executemany("UPDATE file_inventory SET copy_status='CANONICAL' WHERE id=?", batch_can)
        db.executemany("UPDATE file_inventory SET copy_status='DUPLICATE_SKIP' WHERE id=?", batch_dup)
        db.commit()

        print(f"  {drive}: {len(batch_can):,} canonical, {len(batch_dup):,} duplicates")
        total_can += len(batch_can)
        total_dup += len(batch_dup)

    elapsed = time.time() - t0
    print(f"\nPhase A done in {elapsed:.1f}s: {total_can:,} canonical + {total_dup:,} duplicates + {empty:,} empty")

    # Final summary
    for st in REAL[:3]:
        cnt = db.execute("SELECT COUNT(*) FROM file_inventory WHERE copy_status=?", (st,)).fetchone()[0]
        print(f"  {st}: {cnt:,}")

    unmarked = db.execute("SELECT COUNT(*) FROM file_inventory WHERE copy_status IS NULL").fetchone()[0]
    print(f"  UNMARKED: {unmarked:,}")
    db.close()

if __name__ == '__main__':
    run()
