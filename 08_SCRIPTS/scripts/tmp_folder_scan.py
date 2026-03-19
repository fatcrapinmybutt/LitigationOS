import sys, os, json, time
from pathlib import Path
from collections import defaultdict
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

root = Path("I:/")
folder_data = []
count = 0

for dirpath, subdirs, filenames in os.walk(root):
    dp = Path(dirpath)
    parts_lower = [p.lower() for p in dp.parts]
    if any(skip in parts_lower for skip in ['$recycle.bin', 'system volume information']):
        subdirs.clear()
        continue
    if not filenames:
        continue
    total_size = 0
    file_count = 0
    for fn in filenames:
        try:
            total_size += (dp / fn).stat().st_size
            file_count += 1
        except:
            pass
    if total_size > 0:
        folder_data.append({
            'path': str(dp),
            'name': dp.name.lower(),
            'size': total_size,
            'files': file_count,
            'depth': len(dp.parts) - 2,  # depth from I:\
        })
        count += 1
        if count % 500 == 0:
            print(f"  Scanned {count} folders...", flush=True)

print(f"\nTotal folders with files: {count}")

# Group by (name, size, file_count) — dead giveaway
groups = defaultdict(list)
for f in folder_data:
    key = (f['name'], f['size'], f['files'])
    groups[key].append(f)

dup_groups = {k: v for k, v in groups.items() if len(v) >= 2}
total_dup_folders = sum(len(v) for v in dup_groups.values())
total_waste = sum(v[0]['size'] * (len(v) - 1) for v in dup_groups.values())

print(f"\nDuplicate folder groups (same name+size+filecount): {len(dup_groups)}")
print(f"Total duplicate folders: {total_dup_folders}")
print(f"Estimated wasted space: {total_waste / (1024**3):.2f} GB")

# Top 20 by wasted space
print(f"\n{'='*70}")
print(f"TOP 25 DUPLICATE FOLDER GROUPS BY WASTED SPACE")
print(f"{'='*70}")
sorted_groups = sorted(dup_groups.items(), key=lambda x: x[0][1] * (len(x[1]) - 1), reverse=True)
for i, (key, members) in enumerate(sorted_groups[:25], 1):
    name, size, fcount = key
    waste = size * (len(members) - 1)
    print(f"\n{i}. '{name}' | {size/(1024**2):.1f}MB | {fcount} files | {len(members)} copies | {waste/(1024**3):.2f}GB wasted")
    for m in members:
        print(f"   {m['path']}")

# Also: group by size only (catch renamed folders with same content)
size_groups = defaultdict(list)
for f in folder_data:
    if f['size'] > 1_000_000:  # only folders > 1MB
        key = (f['size'], f['files'])
        size_groups[key].append(f)

size_dups = {k: v for k, v in size_groups.items() if len(v) >= 2}
size_waste = sum(v[0]['size'] * (len(v) - 1) for v in size_dups.values())
print(f"\n{'='*70}")
print(f"SIZE-ONLY MATCHES (>1MB folders, same size+filecount, different names)")
print(f"Groups: {len(size_dups)}, Waste: {size_waste/(1024**3):.2f} GB")
for i, (key, members) in enumerate(sorted(size_dups.items(), key=lambda x: x[0][0] * (len(x[1])-1), reverse=True)[:15], 1):
    sz, fc = key
    names = set(m['name'] for m in members)
    if len(names) > 1:  # only show groups with different names
        print(f"\n{i}. SIZE={sz/(1024**2):.1f}MB | {fc} files | {len(members)} folders")
        for m in members:
            print(f"   {m['path']}")
