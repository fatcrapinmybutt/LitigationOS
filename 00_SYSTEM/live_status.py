"""Quick live status check — read-only."""
import sqlite3, time
from datetime import datetime

STATE_DB = r"D:\LitigationOS_tmp\consolidation_state.db"

conn = sqlite3.connect(f"file:{STATE_DB}?mode=ro", uri=True)
conn.execute("PRAGMA busy_timeout=60000")

print("=" * 70)
print(f"  PHASE C LIVE STATUS — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)

rows = conn.execute(
    "SELECT copy_status, COUNT(*), COALESCE(SUM(file_size),0) "
    "FROM file_inventory GROUP BY copy_status ORDER BY COUNT(*) DESC"
).fetchall()

total = 0
copied = 0
canonical = 0
errors = 0
for status, count, sz in rows:
    gb = sz / (1024**3)
    marker = ""
    if status == "COPIED":
        copied = count
        marker = " <<<< COPIED"
    elif status == "CANONICAL":
        canonical = count
        marker = " <<<< REMAINING"
    elif status in ("COPY_ERROR", "SOURCE_MISSING"):
        errors += count
        marker = " <<<< ERROR"
    print(f"  {status or 'NULL':20s}  {count:>8,} files  {gb:>8.2f} GB{marker}")
    total += count

print(f"  {'─' * 50}")
print(f"  {'TOTAL':20s}  {total:>8,} files")

# Progress bar
target = copied + canonical  # total that need copying
if target > 0:
    pct = copied / target * 100
    bar_len = 40
    filled = int(bar_len * copied / target)
    bar = "█" * filled + "░" * (bar_len - filled)
    print(f"\n  [{bar}] {pct:.1f}%")
    print(f"  {copied:,} / {copied + canonical:,} files copied")

# Per-drive
print(f"\n  Per-drive COPIED:")
for r in conn.execute(
    "SELECT source_drive, COUNT(*), COALESCE(SUM(file_size),0) "
    "FROM file_inventory WHERE copy_status='COPIED' "
    "GROUP BY source_drive ORDER BY source_drive"
):
    print(f"    {r[0]}: {r[1]:,} files ({r[2]/(1024**3):.2f} GB)")

print(f"\n  Per-drive CANONICAL (remaining):")
for r in conn.execute(
    "SELECT source_drive, COUNT(*), COALESCE(SUM(file_size),0) "
    "FROM file_inventory WHERE copy_status='CANONICAL' "
    "GROUP BY source_drive ORDER BY source_drive"
):
    print(f"    {r[0]}: {r[1]:,} files ({r[2]/(1024**3):.2f} GB)")

if errors > 0:
    print(f"\n  ⚠️  Errors: {errors}")
    for r in conn.execute(
        "SELECT source_drive, copy_status, COUNT(*) FROM file_inventory "
        "WHERE copy_status IN ('COPY_ERROR','SOURCE_MISSING') "
        "GROUP BY source_drive, copy_status"
    ):
        print(f"    {r[0]} [{r[1]}]: {r[2]}")

conn.close()

# Check if phase-c process is still running
import subprocess
result = subprocess.run(
    ["powershell", "-Command", "Get-Process python -ErrorAction SilentlyContinue | Select-Object Id,StartTime,CPU | Format-Table -AutoSize"],
    capture_output=True, text=True, timeout=10
)
print(f"\n  Python processes:")
print(result.stdout.strip() if result.stdout.strip() else "  (none running)")
