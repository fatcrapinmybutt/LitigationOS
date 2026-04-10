"""Find large files in LitigationOS repo root that could be cleaned up."""
import os
from pathlib import Path

repo = Path(r"C:\Users\andre\LitigationOS")
big_files = []

for f in repo.iterdir():
    if f.is_file():
        sz = f.stat().st_size
        if sz > 1_000_000:  # >1MB
            big_files.append((sz, f.name))

big_files.sort(reverse=True)
print("Large files in repo root (>1MB):")
for sz, name in big_files[:20]:
    print(f"  {sz/1_000_000:.1f} MB  {name}")

# Check build/ and dist/ dirs
for subdir in ["build", "dist", "D_tmp"]:
    d = repo / subdir
    if d.exists():
        total = sum(f.stat().st_size for f in d.rglob("*") if f.is_file())
        print(f"\n{subdir}/: {total/1_000_000:.1f} MB total")
