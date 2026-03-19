#!/usr/bin/env python3
"""
LitigationOS Phase 14 Step 1 — Master Drive Inventory
Scans all available drives, collects file statistics, detects
cross-drive duplicates by (filename, size), and outputs JSON + text reports.
"""

import sys
import os
import json
import time
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime

# UTF-8 safety
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPORT_DIR = r"C:\Users\andre\LitigationOS\00_SYSTEM\reports"
JSON_OUT = os.path.join(REPORT_DIR, "master_drive_inventory.json")
TEXT_OUT = os.path.join(REPORT_DIR, "master_drive_inventory_summary.txt")

os.makedirs(REPORT_DIR, exist_ok=True)

CANDIDATE_DRIVES = ["C:\\", "D:\\", "E:\\", "F:\\", "G:\\", "H:\\", "I:\\"]

SKIP_DIRS = {
    "windows", "program files", "program files (x86)", "programdata",
    "$recycle.bin", "system volume information", "recovery",
    ".git", "node_modules", "__pycache__", ".venv", "venv", "env",
    "msocache", "config.msi", "intel", "perflogs",
}

LITIGATION_KEYWORDS = [
    "legal", "filing", "court", "evidence", "case", "motion",
    "complaint", "affidavit", "transcript", "exhibit", "custody",
    "housing", "shady", "watson", "mcneill", "pigors",
    "litigation", "docket", "pleading", "deposition", "subpoena",
]

MIN_DUP_SIZE = 1024          # 1 KB
MAX_DUP_SIZE = 100 * 1024 * 1024  # 100 MB


def should_skip(dirname_lower):
    return dirname_lower in SKIP_DIRS


def is_litigation_relevant(path_lower):
    return any(kw in path_lower for kw in LITIGATION_KEYWORDS)


def fmt_size(nbytes):
    if nbytes < 1024:
        return f"{nbytes} B"
    elif nbytes < 1024 ** 2:
        return f"{nbytes / 1024:.1f} KB"
    elif nbytes < 1024 ** 3:
        return f"{nbytes / (1024 ** 2):.1f} MB"
    else:
        return f"{nbytes / (1024 ** 3):.2f} GB"


def scan_drive(drive_letter):
    """Walk a single drive, collecting stats."""
    total_files = 0
    total_dirs = 0
    total_size = 0
    ext_counter = Counter()
    dir_file_counts = Counter()
    largest_files = []  # will keep top 20, maintained as sorted list
    litigation_paths = set()
    dup_candidates = []  # (filename_lower, size, full_path)
    errors = 0
    start = time.time()

    LARGEST_MIN = 0  # minimum size currently in top-20 list

    print(f"\n{'='*60}")
    print(f"  Scanning drive {drive_letter}")
    print(f"{'='*60}")

    for dirpath, dirnames, filenames in os.walk(drive_letter, topdown=True):
        # Prune skipped directories in-place
        dirnames[:] = [
            d for d in dirnames
            if not should_skip(d.lower())
        ]

        dir_lower = dirpath.lower()
        file_count_in_dir = 0

        for fname in filenames:
            total_files += 1
            file_count_in_dir += 1

            if total_files % 10000 == 0:
                elapsed = time.time() - start
                print(f"  [{drive_letter}] {total_files:>9,} files scanned  "
                      f"({elapsed:.0f}s elapsed, {errors} errors)")

            fpath = os.path.join(dirpath, fname)
            fname_lower = fname.lower()

            # Extension
            _, ext = os.path.splitext(fname_lower)
            if ext:
                ext_counter[ext] += 1
            else:
                ext_counter["(no ext)"] += 1

            # File size
            try:
                fsize = os.path.getsize(fpath)
            except (OSError, PermissionError):
                errors += 1
                continue

            total_size += fsize

            # Largest files tracking (keep top 20)
            if fsize > LARGEST_MIN or len(largest_files) < 20:
                largest_files.append((fsize, fpath))
                if len(largest_files) > 40:
                    largest_files.sort(key=lambda x: x[0], reverse=True)
                    largest_files = largest_files[:20]
                    LARGEST_MIN = largest_files[-1][0]

            # Duplicate candidates
            if MIN_DUP_SIZE <= fsize <= MAX_DUP_SIZE:
                dup_candidates.append((fname_lower, fsize, fpath))

            # Litigation relevance
            path_lower = fpath.lower()
            if is_litigation_relevant(path_lower):
                litigation_paths.add(dirpath)

        total_dirs += 1
        if file_count_in_dir > 0:
            dir_file_counts[dirpath] = file_count_in_dir

    # Finalize largest
    largest_files.sort(key=lambda x: x[0], reverse=True)
    largest_files = largest_files[:20]

    elapsed = time.time() - start
    print(f"  [{drive_letter}] DONE — {total_files:,} files, "
          f"{total_dirs:,} dirs, {fmt_size(total_size)}, "
          f"{errors} errors, {elapsed:.1f}s")

    # Top 20 dirs by file count
    top_dirs = dir_file_counts.most_common(20)

    # Top 20 extensions
    top_exts = ext_counter.most_common(20)

    drive_data = {
        "total_files": total_files,
        "total_dirs": total_dirs,
        "total_size_bytes": total_size,
        "total_size_gb": round(total_size / (1024 ** 3), 2),
        "scan_time_seconds": round(elapsed, 1),
        "errors": errors,
        "top_extensions": [
            {"ext": ext, "count": cnt} for ext, cnt in top_exts
        ],
        "top_dirs_by_count": [
            {"path": p, "file_count": c} for p, c in top_dirs
        ],
        "top_largest_files": [
            {"path": p, "size_mb": round(s / (1024 ** 2), 2)}
            for s, p in largest_files
        ],
        "litigation_paths": sorted(litigation_paths)[:200],
        "litigation_path_count": len(litigation_paths),
    }

    return drive_data, dup_candidates


def find_cross_drive_duplicates(all_candidates):
    """Find files appearing on multiple drives with same name+size."""
    # Group by (filename, size)
    groups = defaultdict(list)
    for fname_lower, fsize, fpath in all_candidates:
        groups[(fname_lower, fsize)].append(fpath)

    duplicates = []
    for (fname, fsize), paths in groups.items():
        # Only care about files on DIFFERENT drives
        drives_seen = set()
        for p in paths:
            drives_seen.add(p[:3].upper())
        if len(drives_seen) >= 2:
            duplicates.append({
                "filename": fname,
                "size": fsize,
                "size_human": fmt_size(fsize),
                "locations": paths[:10],  # cap at 10 locations
                "location_count": len(paths),
            })

    # Sort by size descending
    duplicates.sort(key=lambda x: x["size"], reverse=True)
    return duplicates[:500]  # cap report at 500 entries


def main():
    print("=" * 60)
    print("  LitigationOS Phase 14 — Master Drive Inventory")
    print(f"  Started: {datetime.now().isoformat()}")
    print("=" * 60)

    overall_start = time.time()

    # Detect available drives
    available = []
    for d in CANDIDATE_DRIVES:
        if os.path.isdir(d):
            available.append(d)
            print(f"  [OK] {d} detected")
        else:
            print(f"  [--] {d} not available")

    report = {
        "scan_date": datetime.now().isoformat(timespec="seconds"),
        "script": "master_drive_inventory.py",
        "phase": "Phase 14 Step 1",
        "drives": {},
        "cross_drive_duplicates": {"by_name_and_size": []},
        "summary": {},
    }

    all_dup_candidates = []
    total_files_all = 0
    total_size_all = 0
    total_litigation = 0

    for drive in available:
        drive_key = drive.rstrip("\\")
        try:
            drive_data, dup_cands = scan_drive(drive)
            report["drives"][drive_key] = drive_data
            all_dup_candidates.extend(dup_cands)
            total_files_all += drive_data["total_files"]
            total_size_all += drive_data["total_size_bytes"]
            total_litigation += drive_data["litigation_path_count"]
        except Exception as exc:
            print(f"  [ERROR] Failed scanning {drive}: {exc}")
            report["drives"][drive_key] = {"error": str(exc)}

    # Cross-drive duplicates
    print(f"\n{'='*60}")
    print(f"  Cross-drive duplicate analysis ({len(all_dup_candidates):,} candidates)")
    print(f"{'='*60}")

    duplicates = find_cross_drive_duplicates(all_dup_candidates)
    report["cross_drive_duplicates"]["by_name_and_size"] = duplicates

    total_elapsed = time.time() - overall_start

    report["summary"] = {
        "total_files_all_drives": total_files_all,
        "total_size_all_drives_gb": round(total_size_all / (1024 ** 3), 2),
        "total_size_all_drives_human": fmt_size(total_size_all),
        "drives_scanned": len(available),
        "drives_available": [d.rstrip("\\") for d in available],
        "litigation_dirs_found": total_litigation,
        "potential_cross_drive_duplicates": len(duplicates),
        "scan_time_seconds": round(total_elapsed, 1),
    }

    # Write JSON
    with open(JSON_OUT, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\n  JSON report: {JSON_OUT}")

    # Write human-readable summary
    lines = []
    lines.append("=" * 70)
    lines.append("  LitigationOS Phase 14 — Master Drive Inventory Summary")
    lines.append(f"  Scan date: {report['scan_date']}")
    lines.append("=" * 70)
    lines.append("")
    lines.append(f"  Drives scanned:          {report['summary']['drives_scanned']}")
    lines.append(f"  Total files (all drives): {total_files_all:,}")
    lines.append(f"  Total size (all drives):  {fmt_size(total_size_all)}")
    lines.append(f"  Litigation-relevant dirs: {total_litigation:,}")
    lines.append(f"  Cross-drive duplicates:   {len(duplicates):,}")
    lines.append(f"  Scan time:                {total_elapsed:.1f}s")
    lines.append("")

    for dk, dd in report["drives"].items():
        if "error" in dd:
            lines.append(f"  {dk}: ERROR — {dd['error']}")
            continue
        lines.append("-" * 70)
        lines.append(f"  Drive {dk}")
        lines.append(f"    Files:  {dd['total_files']:>12,}")
        lines.append(f"    Dirs:   {dd['total_dirs']:>12,}")
        lines.append(f"    Size:   {dd['total_size_gb']:>12.2f} GB")
        lines.append(f"    Errors: {dd['errors']:>12,}")
        lines.append(f"    Litigation dirs: {dd['litigation_path_count']:,}")
        lines.append("")
        lines.append(f"    Top 10 extensions:")
        for item in dd["top_extensions"][:10]:
            lines.append(f"      {item['ext']:<12} {item['count']:>10,}")
        lines.append("")
        lines.append(f"    Top 10 largest files:")
        for item in dd["top_largest_files"][:10]:
            lines.append(f"      {item['size_mb']:>10.1f} MB  {item['path']}")
        lines.append("")
        lines.append(f"    Top 10 dirs by file count:")
        for item in dd["top_dirs_by_count"][:10]:
            lines.append(f"      {item['file_count']:>8,} files  {item['path']}")
        lines.append("")

    if duplicates:
        lines.append("-" * 70)
        lines.append(f"  Cross-Drive Duplicates (top 30 by size)")
        lines.append("")
        for dup in duplicates[:30]:
            lines.append(f"    {dup['filename']}  ({dup['size_human']})")
            for loc in dup["locations"][:5]:
                lines.append(f"      → {loc}")
            if dup["location_count"] > 5:
                lines.append(f"      ... and {dup['location_count'] - 5} more")
            lines.append("")

    lines.append("=" * 70)
    lines.append("  End of report")
    lines.append("=" * 70)

    summary_text = "\n".join(lines)

    with open(TEXT_OUT, "w", encoding="utf-8") as f:
        f.write(summary_text)
    print(f"  Text summary: {TEXT_OUT}")

    # Print summary to stdout
    print("\n" + summary_text[:3000])
    print(f"\n  PHASE 14 STEP 1 COMPLETE")


if __name__ == "__main__":
    main()
