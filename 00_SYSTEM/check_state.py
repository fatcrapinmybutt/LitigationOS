"""Quick check on consolidation state DB."""
import sqlite3, os
DB = r"D:\LitigationOS_tmp\consolidation_state.db"
if not os.path.exists(DB):
    print("State DB not found!")
    raise SystemExit(1)
conn = sqlite3.connect(DB)
conn.execute("PRAGMA busy_timeout=5000")
print("=== CONSOLIDATION STATE ===\n")
# Per-drive counts
rows = conn.execute("""
    SELECT source_drive, COUNT(*) as files, 
           ROUND(SUM(file_size)/1073741824.0, 2) as gb
    FROM file_inventory 
    GROUP BY source_drive 
    ORDER BY files DESC
""").fetchall()
total_files = 0
total_gb = 0
for drive, cnt, gb in rows:
    print(f"  {drive:6s}  {cnt:>8,} files  {gb:>8.2f} GB")
    total_files += cnt
    total_gb += (gb or 0)
print(f"  {'TOTAL':6s}  {total_files:>8,} files  {total_gb:>8.2f} GB")
print()
# Phase status
phases = conn.execute("SELECT phase, status, files_processed, files_total FROM progress ORDER BY phase").fetchall()
for phase, status, fp, ft in phases:
    print(f"  Phase {phase}: {status} ({fp or 0}/{ft or 0})")
conn.close()
