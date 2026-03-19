"""
dupe_analyzer.py — Duplication pre-analysis on omega_filesystem_map.
Groups files by (size_bytes, extension) to find probable duplicates,
estimates wasted space, cross-drive overlap, and hotspot directories.
Results saved to omega_dupe_analysis table.
"""

import sys, os, sqlite3, time
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"

# ── helpers ──────────────────────────────────────────────────────────
GB = 1 << 30

def parent_dir(path: str, filename: str) -> str:
    """Return the directory portion of a full path."""
    if filename and path.endswith(filename):
        return path[: -len(filename)].rstrip("\\").rstrip("/")
    return path


def top_n(mapping: dict, n: int = 15) -> list:
    return sorted(mapping.items(), key=lambda kv: -kv[1])[:n]


# ── 1. load data ────────────────────────────────────────────────────
print("=" * 72)
print("  DUPE PRE-ANALYSIS  —  omega_filesystem_map")
print("=" * 72)

t0 = time.perf_counter()
ro_conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
cur = ro_conn.cursor()

# Only consider real files with a positive size
cur.execute("""
    SELECT drive, path, filename, extension, size_bytes
    FROM omega_filesystem_map
    WHERE size_bytes > 0
""")
rows = cur.fetchall()
total_files = len(rows)
print(f"\n  Loaded {total_files:,} files in {time.perf_counter()-t0:.1f}s")

# ── 2. group by (size_bytes, extension) ─────────────────────────────
t1 = time.perf_counter()
buckets = defaultdict(list)  # (size, ext) -> [(drive, path, filename), ...]
for drive, path, filename, ext, size in rows:
    buckets[(size, ext or "")].append((drive, path, filename))

# Keep only buckets with 2+ files (the dupes)
dupe_buckets = {k: v for k, v in buckets.items() if len(v) >= 2}
del buckets  # free memory

dupe_file_count = sum(len(v) for v in dupe_buckets.values())
dupe_group_count = len(dupe_buckets)
print(f"  Dupe groups (size+ext): {dupe_group_count:,}")
print(f"  Files in dupe groups:   {dupe_file_count:,}")
print(f"  Grouping took {time.perf_counter()-t1:.1f}s")

# ── 3. wasted bytes per drive ────────────────────────────────────────
waste_per_drive = defaultdict(int)     # drive -> wasted bytes
total_per_drive = defaultdict(int)     # drive -> total bytes
dupe_per_drive  = defaultdict(int)     # drive -> files in dupe groups

for (size, ext), members in dupe_buckets.items():
    # "wasted" = (copies - 1) * size, attributed to each copy's drive
    drives_count = defaultdict(int)
    for drv, _, _ in members:
        drives_count[drv] += 1
    for drv, cnt in drives_count.items():
        # Within this drive, (cnt-1) copies are waste; but if file also
        # exists on another drive we still count the extras here.
        waste_per_drive[drv] += size * (cnt - 1) if cnt > 1 else 0
        dupe_per_drive[drv] += cnt

# Total bytes per drive (all files)
for drive, path, filename, ext, size in rows:
    total_per_drive[drive] += size

# ── 4. cross-drive overlap ──────────────────────────────────────────
# For each (size, ext) group that spans >1 drive, sum the bytes
cross_drive_bytes = defaultdict(int)   # drive -> bytes also on another drive
cross_drive_pairs = defaultdict(int)   # (drv_a, drv_b) -> shared bytes

for (size, ext), members in dupe_buckets.items():
    drives_in_group = set(drv for drv, _, _ in members)
    if len(drives_in_group) < 2:
        continue
    for drv in drives_in_group:
        cross_drive_bytes[drv] += size
    drv_list = sorted(drives_in_group)
    for i in range(len(drv_list)):
        for j in range(i + 1, len(drv_list)):
            cross_drive_pairs[(drv_list[i], drv_list[j])] += size

# ── 5. hotspot directories ──────────────────────────────────────────
dir_dupe_count = defaultdict(int)    # directory -> count of dupe files
dir_dupe_bytes = defaultdict(int)    # directory -> bytes in dupe files

for (size, ext), members in dupe_buckets.items():
    for drv, path, filename in members:
        d = parent_dir(path, filename)
        dir_dupe_count[d] += 1
        dir_dupe_bytes[d] += size

# ── 6. save results to omega_dupe_analysis ───────────────────────────
print("\n  Saving results …")
rw_conn = sqlite3.connect(DB_PATH)
rw_cur = rw_conn.cursor()

rw_cur.execute("DROP TABLE IF EXISTS omega_dupe_analysis")
rw_cur.execute("""
    CREATE TABLE omega_dupe_analysis (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        category    TEXT NOT NULL,
        key         TEXT NOT NULL,
        value_num   REAL,
        value_text  TEXT,
        ts          TEXT DEFAULT (datetime('now'))
    )
""")

insert = "INSERT INTO omega_dupe_analysis (category, key, value_num, value_text) VALUES (?,?,?,?)"
rows_to_insert = []

# summary
rows_to_insert.append(("summary", "total_files", total_files, None))
rows_to_insert.append(("summary", "dupe_groups", dupe_group_count, None))
rows_to_insert.append(("summary", "files_in_dupe_groups", dupe_file_count, None))

# per-drive waste
for drv in sorted(total_per_drive):
    rows_to_insert.append(("drive_total_bytes", drv, total_per_drive[drv], None))
    rows_to_insert.append(("drive_waste_bytes", drv, waste_per_drive.get(drv, 0), None))
    rows_to_insert.append(("drive_dupe_files", drv, dupe_per_drive.get(drv, 0), None))

# cross-drive overlap
for drv in sorted(cross_drive_bytes):
    rows_to_insert.append(("cross_drive_bytes", drv, cross_drive_bytes[drv], None))

for (a, b), sz in top_n(cross_drive_pairs, 30):
    rows_to_insert.append(("cross_drive_pair", f"{a} <-> {b}", sz, None))

# hotspot dirs by count
for d, cnt in top_n(dir_dupe_count, 30):
    rows_to_insert.append(("hotspot_count", d, cnt, f"{dir_dupe_bytes.get(d,0)/GB:.2f} GB"))

# hotspot dirs by bytes
for d, byt in top_n(dir_dupe_bytes, 30):
    rows_to_insert.append(("hotspot_bytes", d, byt, f"{byt/GB:.2f} GB"))

# top dupe groups by wasted bytes
top_groups = sorted(dupe_buckets.items(), key=lambda kv: kv[0][0] * (len(kv[1]) - 1), reverse=True)[:50]
for (size, ext), members in top_groups:
    wasted = size * (len(members) - 1)
    sample = members[0]
    rows_to_insert.append((
        "top_dupe_group", f"{ext}|{size}",
        wasted, f"copies={len(members)} sample={sample[2]}"
    ))

rw_cur.executemany(insert, rows_to_insert)
rw_conn.commit()
rw_conn.close()
print(f"  Wrote {len(rows_to_insert)} rows to omega_dupe_analysis")

# ── 7. dashboard ─────────────────────────────────────────────────────
ro_conn.close()

print("\n" + "=" * 72)
print("  DASHBOARD")
print("=" * 72)

total_waste = sum(waste_per_drive.values())
total_all   = sum(total_per_drive.values())

print(f"\n  Total files analysed:   {total_files:>12,}")
print(f"  Dupe groups (size+ext): {dupe_group_count:>12,}")
print(f"  Files in dupe groups:   {dupe_file_count:>12,}")
print(f"  Est. wasted space:      {total_waste/GB:>12.2f} GB")
print(f"  Total scanned:          {total_all/GB:>12.2f} GB")
if total_all > 0:
    print(f"  Waste ratio:            {total_waste/total_all*100:>11.1f} %")

print(f"\n  {'Drive':<14} {'Total GB':>10} {'Waste GB':>10} {'Waste %':>8} {'Dupe files':>11}")
print("  " + "-" * 57)
for drv in sorted(total_per_drive):
    tot = total_per_drive[drv]
    wst = waste_per_drive.get(drv, 0)
    pct = wst / tot * 100 if tot else 0
    dfc = dupe_per_drive.get(drv, 0)
    print(f"  {drv:<14} {tot/GB:>10.2f} {wst/GB:>10.2f} {pct:>7.1f}% {dfc:>11,}")

print(f"\n  CROSS-DRIVE OVERLAP")
print(f"  {'Pair':<26} {'Shared GB':>10}")
print("  " + "-" * 38)
for (a, b), sz in top_n(cross_drive_pairs, 10):
    print(f"  {a+' <-> '+b:<26} {sz/GB:>10.2f}")

print(f"\n  TOP HOTSPOT DIRECTORIES (by dupe file count)")
print(f"  {'Count':>7}  {'Bytes':>10}  Directory")
print("  " + "-" * 68)
for d, cnt in top_n(dir_dupe_count, 15):
    print(f"  {cnt:>7,}  {dir_dupe_bytes.get(d,0)/GB:>9.2f} GB  {d}")

print(f"\n  TOP DUPE GROUPS (by wasted bytes)")
print(f"  {'Copies':>7} {'Size':>12} {'Wasted':>12}  Ext    Sample")
print("  " + "-" * 72)
for (size, ext), members in top_groups[:15]:
    wasted = size * (len(members) - 1)
    sample_name = members[0][2] or "(no name)"
    print(f"  {len(members):>7} {size/GB:>11.4f} GB {wasted/GB:>11.4f} GB  {ext or '(none)':<6} {sample_name[:40]}")

elapsed = time.perf_counter() - t0
print(f"\n  Completed in {elapsed:.1f}s")
print("=" * 72)
