#!/usr/bin/env python3
"""Direct classify+sort for H: drive (bypasses root flatten to avoid dir entry limit)."""
import os
import sys
import shutil
import time
from pathlib import Path
from collections import Counter
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))
try:
    from drive_organizer_v2 import DriveOrganizer, TARGET_FOLDERS, SKIP_DIRS
except ImportError:
    try:
        from drive_organizer_v4 import TARGET_FOLDERS, SKIP_DIRS
        DriveOrganizer = None
    except ImportError:
        print("[ERROR] Neither drive_organizer_v2 nor v4 found. Cannot run H drive fix.")
        sys.exit(1)

root = Path("H:\\")
log_dir = root / "_ORGANIZER_LOG"
log_dir.mkdir(exist_ok=True)

if DriveOrganizer is None:
    print("[WARN] DriveOrganizer class not available in v4. Running in limited mode.")
    org = None
else:
    org = DriveOrganizer("H", dry_run=False)
folder_counts = Counter()
errors = []
moved = 0
skipped = 0

target_names_lower = {k.lower() for k in TARGET_FOLDERS}

# Phase A: Sort ALL files from every location directly to target folders
print("Phase A: Direct classify + sort all files on H:")
print("Scanning...")

all_files = []
for dirpath, dirnames, filenames in os.walk(str(root)):
    dp = Path(dirpath)
    rel = dp.relative_to(root)
    parts_lower = [p.lower() for p in rel.parts]

    do_skip = False
    for p in parts_lower:
        if p in SKIP_DIRS or p.startswith("$") or p in target_names_lower:
            do_skip = True
            break
    if do_skip:
        dirnames.clear()
        continue

    for fname in filenames:
        fp = dp / fname
        all_files.append(fp)

print(f"  Found {len(all_files):,} files to sort")
t0 = time.time()

for i, fp in enumerate(all_files):
    if not fp.exists():
        skipped += 1
        continue
    try:
        target_folder = org._classify(fp)
        dst = root / target_folder / fp.name
        if dst.exists():
            stem = dst.stem
            suffix = dst.suffix
            counter = 2
            while dst.exists():
                dst = dst.parent / f"{stem}_{counter}{suffix}"
                counter += 1

        dst.parent.mkdir(parents=True, exist_ok=True)
        fp.rename(dst)
        folder_counts[target_folder] += 1
        moved += 1
    except Exception as e:
        try:
            shutil.move(str(fp), str(dst))
            folder_counts[target_folder] += 1
            moved += 1
        except Exception as e2:
            errors.append(f"{fp}: {e2}")

    if (i + 1) % 2000 == 0:
        print(f"  Processed {i+1:,}/{len(all_files):,} ...")

print(f"\nPhase A complete: {moved:,} files moved, {skipped:,} skipped")
for folder, count in sorted(folder_counts.items(), key=lambda x: -x[1]):
    print(f"  {folder}: {count:,} files")

# Phase B: Sort staged files from __pycache__
pycache = root / "__pycache__"
staged_moved = 0
if pycache.exists():
    print(f"\nPhase B: Sorting staged files from __pycache__")
    staged = [f for f in pycache.iterdir() if f.is_file()]
    for fp in staged:
        try:
            target_folder = org._classify(fp)
            dst = root / target_folder / fp.name
            if dst.exists():
                stem = dst.stem
                suffix = dst.suffix
                counter = 2
                while dst.exists():
                    dst = dst.parent / f"{stem}_{counter}{suffix}"
                    counter += 1
            fp.rename(dst)
            folder_counts[target_folder] += 1
            staged_moved += 1
        except Exception as e:
            errors.append(f"staged: {fp.name}: {e}")
    print(f"  Moved {staged_moved:,} staged files")

# Phase C: Clean empty directories
print(f"\nPhase C: Cleaning empty directories")
cleaned = 0
for dirpath, dirnames, filenames in os.walk(str(root), topdown=False):
    dp = Path(dirpath)
    if dp == root:
        continue
    name_lower = dp.name.lower()
    if name_lower in SKIP_DIRS or name_lower.startswith("$") or dp.name in TARGET_FOLDERS:
        continue
    if name_lower == "_organizer_log":
        continue
    try:
        if not any(dp.iterdir()):
            dp.rmdir()
            cleaned += 1
    except OSError:
        pass
print(f"  Removed {cleaned} empty directories")

# Phase D: Write log
elapsed = time.time() - t0
ts = datetime.now().strftime("%Y%m%d_%H%M%S")
summary_path = log_dir / f"summary_{ts}.txt"
with open(summary_path, "w") as f:
    f.write(f"Drive Organizer — H:\\\n")
    f.write(f"Mode: Direct sort (root entry limit workaround)\n")
    f.write(f"Elapsed: {elapsed:.1f}s\n")
    f.write(f"Files moved: {moved + staged_moved}\n")
    f.write(f"Dirs removed: {cleaned}\n\n")
    for folder, count in sorted(folder_counts.items(), key=lambda x: -x[1]):
        f.write(f"  {folder}: {count}\n")
    if errors:
        f.write(f"\nErrors ({len(errors)}):\n")
        for e in errors[:50]:
            f.write(f"  {e}\n")

total = moved + staged_moved
print(f"\n{'='*60}")
print(f"  H: DONE in {elapsed:.1f}s — {total:,} files organized")
print(f"  Dirs removed: {cleaned}")
if errors:
    print(f"  Errors: {len(errors)}")
    for e in errors[:5]:
        print(f"    {e}")
print(f"{'='*60}")
