"""Move large recoverable files from C:\ to D:\ to free disk space."""
import shutil
import os
from pathlib import Path

repo = Path(r"C:\Users\andre\LitigationOS")
dest = Path(r"D:\LitigationOS_archives")
dest.mkdir(exist_ok=True)

moves = [
    (repo / "mbp_brain.db.pre_optimize_bak", dest / "mbp_brain.db.pre_optimize_bak"),
]

total_freed = 0
for src, dst in moves:
    if src.exists():
        size_mb = src.stat().st_size / 1_000_000
        print(f"Moving {src.name} ({size_mb:.1f} MB) to {dst}")
        shutil.move(str(src), str(dst))
        total_freed += size_mb
        print(f"  OK - Done")
    else:
        print(f"  WARN Not found: {src}")

print(f"\nTotal freed: {total_freed:.1f} MB")

# Check new free space
import ctypes
free_bytes = ctypes.c_ulonglong(0)
ctypes.windll.kernel32.GetDiskFreeSpaceExW(r"C:\\", None, None, ctypes.byref(free_bytes))
print(f"C:\\ free space now: {free_bytes.value / 1_000_000:.0f} MB")
