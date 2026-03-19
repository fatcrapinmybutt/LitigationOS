import sys, os, hashlib, json
from collections import defaultdict
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

root = r"C:\Users\andre\LitigationOS"

# Phase 1: Group files by size (fast filter)
print("Scanning for duplicates by file size...")
size_groups = defaultdict(list)
total = 0
for dirpath, dirnames, filenames in os.walk(root):
    # Skip the archives/dedup dir itself
    if 'dedup' in dirpath.lower():
        continue
    for fn in filenames:
        fp = os.path.join(dirpath, fn)
        try:
            sz = os.path.getsize(fp)
            if sz > 1024:  # Only files > 1KB
                size_groups[sz].append(fp)
                total += 1
        except:
            pass

print(f"Scanned {total} files")

# Phase 2: For same-size groups, compute SHA-256
print("Computing hashes for size-matched groups...")
potential_dupes = {sz: paths for sz, paths in size_groups.items() if len(paths) > 1}
print(f"  {len(potential_dupes)} size groups with potential duplicates")

def quick_hash(path, chunk_size=65536):
    h = hashlib.sha256()
    try:
        with open(path, 'rb') as f:
            chunk = f.read(chunk_size)
            h.update(chunk)
    except:
        return None
    return h.hexdigest()

hash_groups = defaultdict(list)
hashed = 0
for sz, paths in potential_dupes.items():
    for p in paths:
        h = quick_hash(p)
        if h:
            hash_groups[(sz, h)].append(p)
            hashed += 1
    if hashed % 5000 == 0 and hashed > 0:
        print(f"  Hashed {hashed} files...")

# Phase 3: Identify actual duplicates
dupes = []
total_dupe_bytes = 0
for key, paths in hash_groups.items():
    if len(paths) > 1:
        sz = key[0]
        # Keep the first one, mark rest as dupes
        keep = paths[0]
        for dup in paths[1:]:
            dupes.append({
                'keep': keep,
                'duplicate': dup,
                'size': sz,
                'hash': key[1][:16]
            })
            total_dupe_bytes += sz

print(f"\nDuplicate files found: {len(dupes)}")
print(f"Duplicate space: {total_dupe_bytes / (1024*1024):.1f} MB")

# Save report
report_path = os.path.join(root, "00_SYSTEM", "dedup_report.json")
with open(report_path, 'w', encoding='utf-8') as f:
    json.dump({
        'total_scanned': total,
        'duplicates_found': len(dupes),
        'duplicate_bytes': total_dupe_bytes,
        'top_duplicates': sorted(dupes, key=lambda x: -x['size'])[:50]
    }, f, indent=2, default=str)
print(f"Report saved: {report_path}")

# Show top 10 largest dupes
print("\nTop 10 largest duplicates:")
for d in sorted(dupes, key=lambda x: -x['size'])[:10]:
    print(f"  {d['size']/1024/1024:.1f} MB: {os.path.basename(d['duplicate'])}")
    print(f"    KEEP: ...{d['keep'][-60:]}")
    print(f"    DUPE: ...{d['duplicate'][-60:]}")
