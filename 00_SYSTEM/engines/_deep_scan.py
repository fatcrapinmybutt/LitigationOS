import os
import json
from collections import defaultdict

LOS = r'C:\Users\andre\LitigationOS'

# Full recursive scan
folder_tree = {}
folder_stats = {}

for root, dirs, files in os.walk(LOS):
    rel = os.path.relpath(root, LOS)
    depth = 0 if rel == '.' else rel.count(os.sep) + 1
    file_count = len(files)
    dir_count = len(dirs)
    
    # Calculate size
    total_size = 0
    extensions = defaultdict(int)
    for f in files:
        fp = os.path.join(root, f)
        try:
            sz = os.path.getsize(fp)
            total_size += sz
            ext = os.path.splitext(f)[1].lower()
            extensions[ext] += 1
        except:
            pass
    
    folder_stats[rel] = {
        'depth': depth,
        'files': file_count,
        'dirs': dir_count,
        'size_mb': round(total_size / 1048576, 1),
        'top_exts': dict(sorted(extensions.items(), key=lambda x: -x[1])[:5])
    }

# Print tree with indentation
print(f"LITIGATIONOS FULL RECURSIVE SCAN")
print(f"Total folders: {len(folder_stats)}")
print(f"=" * 90)

# Sort by path
for rel in sorted(folder_stats.keys()):
    s = folder_stats[rel]
    depth = s['depth']
    if depth > 4:  # Cap display depth
        continue
    
    indent = "  " * depth
    name = os.path.basename(rel) if rel != '.' else 'LitigationOS/'
    
    # Format
    exts = ', '.join(f"{e}:{c}" for e, c in list(s['top_exts'].items())[:3])
    size_str = f"{s['size_mb']}MB" if s['size_mb'] >= 1 else f"{s['size_mb']*1024:.0f}KB"
    
    print(f"{indent}{name}/ ({s['files']}f, {s['dirs']}d, {size_str}) [{exts}]")

# Summary: top-level folders sorted by total recursive size
print(f"\n{'='*90}")
print(f"TOP-LEVEL FOLDER SUMMARY (recursive)")
print(f"{'='*90}")

top_level = {}
for rel, s in folder_stats.items():
    if rel == '.':
        continue
    top = rel.split(os.sep)[0]
    if top not in top_level:
        top_level[top] = {'files': 0, 'size_mb': 0, 'max_depth': 0, 'subdirs': 0}
    top_level[top]['files'] += s['files']
    top_level[top]['size_mb'] += s['size_mb']
    top_level[top]['max_depth'] = max(top_level[top]['max_depth'], s['depth'])
    top_level[top]['subdirs'] += s['dirs']

for name in sorted(top_level.keys(), key=lambda x: -top_level[x]['size_mb']):
    t = top_level[name]
    print(f"  {name:70s} {t['files']:6}f  {t['size_mb']:8.0f}MB  depth={t['max_depth']}  subdirs={t['subdirs']}")

# Count UNPACKED folders
unpacked = [k for k in top_level.keys() if 'UNPACKED' in k or 'CYCLEPACK' in k or k.startswith('2026')]
print(f"\nUNPACKED/TEMP folders: {len(unpacked)}")
for u in sorted(unpacked):
    t = top_level[u]
    print(f"  {u}: {t['files']}f, {t['size_mb']:.0f}MB")
