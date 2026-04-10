#!/usr/bin/env python3
"""
LitigationOS Dedupe — Right-click context menu target.
Usage: python dedupe_target.py <folder_path>
Deduplicates files by SHA-256 within the target folder.
Moves duplicates to _DEDUP_TRASH/ with hash collision log.
"""
import sys, os, hashlib, shutil, csv, time
from pathlib import Path
from datetime import datetime

TRASH_NAME = "_DEDUP_TRASH"
PROTECTED = {".git", ".github", ".agents", ".venv", ".vscode", "00_SYSTEM",
             "node_modules", "__pycache__", "site-packages", "_DEDUP_TRASH"}

def sha256(path, block=65536):
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            while chunk := f.read(block):
                h.update(chunk)
    except (OSError, PermissionError):
        return None
    return h.hexdigest()

def dedupe_folder(target):
    target = Path(target).resolve()
    if not target.is_dir():
        print(f"ERROR: {target} is not a directory")
        return

    trash = target / TRASH_NAME
    trash.mkdir(exist_ok=True)
    log_path = trash / f"dedup_log_{datetime.now():%Y%m%d_%H%M%S}.csv"

    seen = {}
    moved = 0
    freed = 0
    errors = 0

    all_files = []
    for root, dirs, files in os.walk(target):
        dirs[:] = [d for d in dirs if d not in PROTECTED and d != TRASH_NAME]
        for f in files:
            fp = Path(root) / f
            if fp.suffix.lower() == ".py":
                continue
            all_files.append(fp)

    total = len(all_files)
    print(f"Scanning {total:,} files in {target}...")

    with open(log_path, "w", newline="", encoding="utf-8") as csvf:
        writer = csv.writer(csvf)
        writer.writerow(["action", "path", "hash", "size", "canonical"])

        for i, fp in enumerate(all_files):
            if i % 500 == 0 and i > 0:
                print(f"  Progress: {i:,}/{total:,} ({moved:,} dupes found)")
            try:
                h = sha256(fp)
                if h is None:
                    continue
                sz = fp.stat().st_size

                if h in seen:
                    dest = trash / fp.name
                    counter = 0
                    while dest.exists():
                        counter += 1
                        dest = trash / f"{fp.stem}_{counter}{fp.suffix}"
                    shutil.move(str(fp), str(dest))
                    writer.writerow(["MOVED_DUPE", str(fp), h, sz, str(seen[h])])
                    moved += 1
                    freed += sz
                else:
                    seen[h] = fp
                    writer.writerow(["CANONICAL", str(fp), h, sz, ""])
            except Exception as e:
                errors += 1
                writer.writerow(["ERROR", str(fp), "", 0, str(e)])

    print(f"\n{'='*60}")
    print(f"DEDUP COMPLETE: {target}")
    print(f"  Files scanned:  {total:,}")
    print(f"  Duplicates:     {moved:,}")
    print(f"  Space freed:    {freed / (1024**2):.1f} MB")
    print(f"  Errors:         {errors}")
    print(f"  Log:            {log_path}")
    print(f"{'='*60}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python dedupe_target.py <folder_path>")
        sys.exit(1)
    dedupe_folder(sys.argv[1])
    input("\nPress Enter to close...")
