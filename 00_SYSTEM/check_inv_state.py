"""Check consolidation state DB for current inventory progress."""
import sqlite3, os

DB = r"D:\LitigationOS_tmp\consolidation_state.db"
if not os.path.exists(DB):
    print("State DB not found - will be created fresh on next run")
    raise SystemExit(0)

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row

# Check progress table
print("=== PHASE PROGRESS ===")
cols = [r[1] for r in conn.execute("PRAGMA table_info(progress)")]
print(f"  Columns: {cols}")
for row in conn.execute("SELECT * FROM progress ORDER BY phase"):
    print(f"  {dict(row)}")

# Check file_inventory per drive
print("\n=== FILES PER DRIVE ===")
for row in conn.execute("SELECT source_drive, COUNT(*) as cnt, SUM(file_size) as sz FROM file_inventory GROUP BY source_drive ORDER BY source_drive"):
    sz = row['sz'] or 0
    print(f"  {row['source_drive']:4s} | {row['cnt']:>8,} files | {sz/1e9:.2f} GB")

total = conn.execute("SELECT COUNT(*) FROM file_inventory").fetchone()[0]
print(f"\n  TOTAL: {total:,} files in inventory")

conn.close()
