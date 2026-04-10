#!/usr/bin/env python3
"""Plan B: Revert DB paths via SQL REPLACE() — no file copy needed.
Works even with active DB connections since we're just doing UPDATEs."""
import sqlite3, time

LIT_DB = r"C:\Users\andre\LitigationOS\litigation_context.db"

# The 4 drive prefixes that were migrated
DRIVE_MAP = {
    r"J:\CONSOLIDATED\I_DRIVE\\": r"I:\\",
    r"J:\CONSOLIDATED\D_DRIVE\\": r"D:\\",
    r"J:\CONSOLIDATED\F_DRIVE\\": r"F:\\",
    r"J:\CONSOLIDATED\G_DRIVE\\": r"G:\\",
}

# Tables and columns that were migrated
TABLES = [
    ("evidence_quotes", "source_file"),
    ("documents", "file_path"),
    ("impeachment_matrix", "source_file"),
]

print("=" * 60)
print("PLAN B: SQL REPLACE() Path Revert")
print("=" * 60)

db = sqlite3.connect(LIT_DB)
db.execute("PRAGMA busy_timeout = 120000")
db.execute("PRAGMA journal_mode = WAL")
db.execute("PRAGMA cache_size = -64000")

# Step 1: Diagnose current state
print("\n[1] Current path distribution:")
for table, col in TABLES:
    for prefix in [r"J:\CONSOLIDATED\%", r"I:\%", r"D:\%", r"F:\%", r"G:\%"]:
        cnt = db.execute(f"SELECT COUNT(*) FROM {table} WHERE {col} LIKE ?", (prefix,)).fetchone()[0]
        if cnt > 0:
            print(f"   {table}.{col} LIKE '{prefix}': {cnt:,}")

# Step 2: Revert all J:\CONSOLIDATED\ paths back to original drives
print("\n[2] Reverting paths...")
total_reverted = 0
for table, col in TABLES:
    for j_prefix, orig_prefix in DRIVE_MAP.items():
        cnt_before = db.execute(
            f"SELECT COUNT(*) FROM {table} WHERE {col} LIKE ?",
            (j_prefix.rstrip("\\") + "%",)
        ).fetchone()[0]
        if cnt_before > 0:
            n = db.execute(
                f"UPDATE {table} SET {col} = REPLACE({col}, ?, ?) WHERE {col} LIKE ?",
                (j_prefix.rstrip("\\"), orig_prefix.rstrip("\\"), j_prefix.rstrip("\\") + "%")
            ).rowcount
            print(f"   {table}.{col}: {j_prefix.rstrip(chr(92))} -> {orig_prefix.rstrip(chr(92))}: {n:,} rows")
            total_reverted += n
    db.commit()

print(f"\n   Total reverted: {total_reverted:,}")

# Step 3: Verify zero J:\CONSOLIDATED\ paths remain
print("\n[3] Verification — J:\\CONSOLIDATED\\ paths remaining:")
all_clear = True
for table, col in TABLES:
    cnt = db.execute(
        f"SELECT COUNT(*) FROM {table} WHERE {col} LIKE ?",
        (r"J:\CONSOLIDATED\%",)
    ).fetchone()[0]
    status = "✅" if cnt == 0 else "❌"
    print(f"   {table}.{col}: {cnt:,} {status}")
    if cnt > 0:
        all_clear = False
        # Show samples
        rows = db.execute(
            f"SELECT {col} FROM {table} WHERE {col} LIKE ? LIMIT 5",
            (r"J:\CONSOLIDATED\%",)
        ).fetchall()
        for r in rows:
            print(f"      SAMPLE: {r[0][:100]}")

# Step 4: Rebuild FTS5 indexes
print("\n[4] Rebuilding FTS5 indexes...")
fts_tables = ["evidence_fts", "timeline_fts", "md_sections_fts"]
for ft in fts_tables:
    try:
        db.execute(f"INSERT INTO {ft}({ft}) VALUES('rebuild')")
        db.commit()
        print(f"   {ft}: rebuilt ✅")
    except Exception as e:
        print(f"   {ft}: {e}")

# Step 5: Final counts
print("\n[5] Final path distribution:")
for table, col in TABLES:
    for prefix_label, prefix in [("I:\\", r"I:\%"), ("D:\\", r"D:\%"), ("F:\\", r"F:\%"), ("G:\\", r"G:\%"), ("J:\\CONSOLIDATED\\", r"J:\CONSOLIDATED\%")]:
        cnt = db.execute(f"SELECT COUNT(*) FROM {table} WHERE {col} LIKE ?", (prefix,)).fetchone()[0]
        if cnt > 0:
            print(f"   {table}.{col} [{prefix_label}]: {cnt:,}")

db.close()

if all_clear:
    print("\n" + "=" * 60)
    print("DB PATHS FULLY REVERTED ✅")
    print("State DB already reset (231,667 files → NULL)")
    print("Ready to fix execute_consolidation.py and re-run")
    print("=" * 60)
else:
    print("\n⚠️  Some J:\\CONSOLIDATED paths remain — manual review needed")
