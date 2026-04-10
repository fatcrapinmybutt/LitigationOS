"""
SHADYOAKS-DESTRUCTION — Phase 1: Extract all file paths from both desktop file lists.
Outputs: D:\LitigationOS_tmp\shadyoaks_all_paths.txt (deduplicated master list)
         D:\LitigationOS_tmp\shadyoaks_stats.txt (extension/drive breakdown)
"""
import sys
import csv
import re
import os
from collections import Counter, defaultdict

LIST1 = r"C:\Users\andre\Desktop\shadyoaksfilelocations2.txt"
LIST2 = r"C:\Users\andre\Desktop\SHADYOAKSFILELOCATIONS"
OUT_PATHS = r"D:\LitigationOS_tmp\shadyoaks_all_paths.txt"
OUT_STATS = r"D:\LitigationOS_tmp\shadyoaks_stats.txt"

paths = set()
errors = []

# --- List 1: numbered quoted paths (format: `1. "I:\...\file.ext"`) ---
try:
    with open(LIST1, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # Strip leading number + dot + space
            line = re.sub(r'^\d+\.\s*', '', line)
            # Strip surrounding quotes
            line = line.strip('"').strip("'")
            if len(line) > 3 and line[1] == ':' and line[2] == '\\':
                paths.add(line)
    print(f"List1 loaded: {len(paths)} paths so far")
except Exception as e:
    errors.append(f"List1 error: {e}")
    print(f"ERROR list1: {e}")

count_before_list2 = len(paths)

# --- List 2: WizTree CSV (column 1 = quoted file path) ---
try:
    with open(LIST2, "r", encoding="utf-8-sig", errors="replace") as f:
        reader = csv.reader(f)
        row_count = 0
        for row in reader:
            if not row:
                continue
            cell = row[0].strip().strip('"').strip("'").strip()
            # Must look like a path: X:\...
            if len(cell) > 3 and cell[1] == ':' and cell[2] == '\\':
                # Skip if it's a directory (no extension, ends with \)
                # Include both files and directories for now
                paths.add(cell)
                row_count += 1
    print(f"List2 loaded {row_count} rows; total paths now: {len(paths)}")
except Exception as e:
    errors.append(f"List2 error: {e}")
    print(f"ERROR list2: {e}")

# --- Deduplicate and sort ---
sorted_paths = sorted(paths)
print(f"\nTotal unique paths: {len(sorted_paths)}")

# --- Stats ---
drive_counts = Counter()
ext_counts = Counter()
missing_files = []
existing_files = []

for p in sorted_paths:
    drive = p[0].upper()
    drive_counts[drive] += 1
    _, ext = os.path.splitext(p)
    ext_counts[ext.lower()] += 1

# --- Write master path list ---
with open(OUT_PATHS, "w", encoding="utf-8") as f:
    f.write(f"# SHADYOAKS-DESTRUCTION Master File List\n")
    f.write(f"# Total: {len(sorted_paths)} unique paths\n")
    f.write(f"# Source 1: {LIST1}\n")
    f.write(f"# Source 2: {LIST2}\n\n")
    for p in sorted_paths:
        f.write(p + "\n")

# --- Write stats ---
with open(OUT_STATS, "w", encoding="utf-8") as f:
    f.write(f"SHADYOAKS-DESTRUCTION File List Statistics\n")
    f.write(f"{'='*50}\n")
    f.write(f"Total unique paths: {len(sorted_paths)}\n")
    f.write(f"From List1 only: {count_before_list2}\n")
    f.write(f"From List2 (incremental): {len(sorted_paths) - count_before_list2}\n\n")
    f.write("By Drive:\n")
    for drive, count in sorted(drive_counts.items()):
        f.write(f"  {drive}:\\ — {count} files\n")
    f.write("\nTop 30 Extensions:\n")
    for ext, count in ext_counts.most_common(30):
        ext_label = ext if ext else "(no extension)"
        f.write(f"  {ext_label:<15} {count}\n")
    if errors:
        f.write(f"\nErrors:\n")
        for e in errors:
            f.write(f"  {e}\n")

print("\n=== STATS ===")
print(f"Total unique paths: {len(sorted_paths)}")
print("By Drive:")
for drive, count in sorted(drive_counts.items()):
    print(f"  {drive}:\\ — {count}")
print("Top 20 Extensions:")
for ext, count in ext_counts.most_common(20):
    print(f"  {ext or '(none)':<15} {count}")
print(f"\nOutputs written:")
print(f"  {OUT_PATHS}")
print(f"  {OUT_STATS}")
