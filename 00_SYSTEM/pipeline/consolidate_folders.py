#!/usr/bin/env python3
"""
DRIVE CONSOLIDATOR — Merge 12 old folders into 7 tight folders
================================================================
Runs on drives already organized by v2/v3. Merges:
  01_SCANNED_EVIDENCE + 07_MEDIA       → Evidence
  02_COURT_DOCUMENTS + 09_FORMS        → Court
  03_LEGAL_ANALYSIS + 10_REFERENCE     → Legal
  04_CASE_DATA                         → Data
  05_CODE_AND_TOOLS + 11_SYSTEM_FILES  → Code
  08_LLM_AND_PROMPTS                   → AI
  06_ARCHIVES                          → Archives
  _RECYCLE                             → _Trash

Max depth: 2 (Drive:\\Category\\file). No sub-nesting.

Usage:
    python consolidate_folders.py G H        # consolidate organized drives
    python consolidate_folders.py --dry-run G H
"""
import os
import sys
import shutil
import time
from pathlib import Path
from collections import Counter
from datetime import datetime

# Merge map: old folder → new folder
MERGE_MAP = {
    "01_SCANNED_EVIDENCE":   "Evidence",
    "07_MEDIA":              "Evidence",
    "02_COURT_DOCUMENTS":    "Court",
    "09_FORMS_AND_TEMPLATES":"Court",
    "03_LEGAL_ANALYSIS":     "Legal",
    "10_REFERENCE":          "Legal",
    "04_CASE_DATA":          "Data",
    "05_CODE_AND_TOOLS":     "Code",
    "11_SYSTEM_FILES":       "Code",
    "08_LLM_AND_PROMPTS":    "AI",
    "06_ARCHIVES":           "Archives",
    "_RECYCLE":              "_Trash",
}

NEW_FOLDERS = ["Evidence", "Court", "Legal", "Data", "Code", "AI", "Archives", "_Trash"]


def consolidate_drive(drive_letter: str, dry_run: bool = False):
    root = Path(f"{drive_letter}:\\")
    if not root.exists():
        print(f"SKIP {drive_letter}: — not found")
        return

    mode = "DRY RUN" if dry_run else "LIVE"
    print(f"\n{'='*60}")
    print(f"  CONSOLIDATOR — {drive_letter}:\\ [{mode}]")
    print(f"{'='*60}")
    t0 = time.time()

    moved = 0
    errors = []
    folder_counts = Counter()

    # Phase 1: Create new folders
    print(f"\n[{drive_letter}] Phase 1: CREATE NEW FOLDERS")
    for folder in NEW_FOLDERS:
        target = root / folder
        if not dry_run:
            target.mkdir(exist_ok=True)
        print(f"  {'[DRY] ' if dry_run else ''}Created {folder}/")

    # Phase 2: Move files from old folders to new folders
    print(f"\n[{drive_letter}] Phase 2: MERGE OLD → NEW")
    for old_name, new_name in MERGE_MAP.items():
        old_dir = root / old_name
        if not old_dir.exists():
            continue

        files = list(old_dir.rglob("*"))
        file_count = sum(1 for f in files if f.is_file())
        print(f"  {old_name} → {new_name}  ({file_count:,} files)")

        for fp in files:
            if not fp.is_file():
                continue
            dst = root / new_name / fp.name
            # Handle collision
            if dst.exists():
                stem = dst.stem
                suffix = dst.suffix
                counter = 2
                while dst.exists():
                    dst = dst.parent / f"{stem}_{counter}{suffix}"
                    counter += 1

            if not dry_run:
                try:
                    fp.rename(dst)
                    moved += 1
                except OSError:
                    try:
                        shutil.move(str(fp), str(dst))
                        moved += 1
                    except Exception as e:
                        errors.append(f"{fp}: {e}")
            else:
                moved += 1
            folder_counts[new_name] += 1

    # Phase 3: Remove old empty folders
    print(f"\n[{drive_letter}] Phase 3: REMOVE OLD FOLDERS")
    removed = 0
    for old_name in MERGE_MAP:
        old_dir = root / old_name
        if not old_dir.exists():
            continue
        try:
            remaining = list(old_dir.rglob("*"))
            remaining_files = [f for f in remaining if f.is_file()]
            if not remaining_files:
                if not dry_run:
                    shutil.rmtree(str(old_dir), ignore_errors=True)
                removed += 1
                print(f"  {'[DRY] ' if dry_run else ''}Removed {old_name}/")
            else:
                print(f"  KEPT {old_name}/ — {len(remaining_files)} files still inside")
        except Exception as e:
            print(f"  ERROR removing {old_name}: {e}")

    # Phase 4: Flatten any sub-nesting in new folders (max depth = 1 inside category)
    print(f"\n[{drive_letter}] Phase 4: FLATTEN SUB-NESTING")
    flattened = 0
    for folder in NEW_FOLDERS:
        fdir = root / folder
        if not fdir.exists():
            continue
        # Find any files deeper than fdir/file (i.e., in subdirectories)
        for dirpath, dirnames, filenames in os.walk(str(fdir)):
            dp = Path(dirpath)
            if dp == fdir:
                continue  # skip the top level
            for fname in filenames:
                src = dp / fname
                dst = fdir / fname
                if dst.exists():
                    stem = dst.stem
                    suffix = dst.suffix
                    counter = 2
                    while dst.exists():
                        dst = fdir / f"{stem}_{counter}{suffix}"
                        counter += 1
                if not dry_run:
                    try:
                        src.rename(dst)
                        flattened += 1
                    except Exception:
                        try:
                            shutil.move(str(src), str(dst))
                            flattened += 1
                        except Exception as e:
                            errors.append(f"flatten {src}: {e}")
                else:
                    flattened += 1

    # Clean empty subdirs inside new folders
    for folder in NEW_FOLDERS:
        fdir = root / folder
        if not fdir.exists():
            continue
        for dirpath, _, _ in os.walk(str(fdir), topdown=False):
            dp = Path(dirpath)
            if dp == fdir:
                continue
            try:
                if not any(dp.iterdir()):
                    if not dry_run:
                        dp.rmdir()
            except OSError:
                pass

    if flattened:
        print(f"  Flattened {flattened:,} nested files to category root")
    else:
        print(f"  No sub-nesting found")

    # Summary
    elapsed = time.time() - t0
    print(f"\n[{drive_letter}] SUMMARY")
    for folder, count in sorted(folder_counts.items(), key=lambda x: -x[1]):
        print(f"  {folder}: {count:,} files")

    # Write log
    if not dry_run:
        log_dir = root / "_ORGANIZER_LOG"
        log_dir.mkdir(exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        with open(log_dir / f"consolidate_{ts}.txt", "w") as f:
            f.write(f"Consolidation — {drive_letter}:\\\n")
            f.write(f"Elapsed: {elapsed:.1f}s\n")
            f.write(f"Files moved: {moved}\n")
            f.write(f"Old folders removed: {removed}\n")
            f.write(f"Sub-nested files flattened: {flattened}\n\n")
            for folder, count in sorted(folder_counts.items(), key=lambda x: -x[1]):
                f.write(f"  {folder}: {count}\n")
            if errors:
                f.write(f"\nErrors ({len(errors)}):\n")
                for e in errors[:50]:
                    f.write(f"  {e}\n")

    print(f"\n{'─'*60}")
    print(f"  DONE in {elapsed:.1f}s — {drive_letter}:\\")
    print(f"    files_moved: {moved:,}")
    print(f"    old_folders_removed: {removed}")
    print(f"    sub_nested_flattened: {flattened:,}")
    print(f"    errors: {len(errors)}")
    print(f"{'─'*60}")


def main():
    args = sys.argv[1:]
    if not args:
        print("Usage: python consolidate_folders.py [--dry-run] G H D F")
        sys.exit(1)

    dry_run = "--dry-run" in args
    drives = [a.upper().rstrip(":\\") for a in args if a != "--dry-run"]

    for d in drives:
        if d == "C":
            print("SKIPPING C: — use c_drive_organize.py instead")
            continue
        consolidate_drive(d, dry_run=dry_run)


if __name__ == "__main__":
    main()
