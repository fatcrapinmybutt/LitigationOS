import sys, os, hashlib, json
from collections import defaultdict
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

root = r"C:\Users\andre\LitigationOS"
unpack = os.path.join(root, "18_UNPACKED_ZIPS")

# Build hash index of unpacked ZIP files only
print("Indexing unpacked ZIP files...")
zip_hashes = {}
zip_count = 0
for dirpath, _, filenames in os.walk(unpack):
    if '_originals' in dirpath:
        continue
    for fn in filenames:
        fp = os.path.join(dirpath, fn)
        try:
            sz = os.path.getsize(fp)
            if sz < 100:
                continue
            with open(fp, 'rb') as f:
                h = hashlib.md5(f.read(4096)).hexdigest()
            key = (sz, h)
            if key not in zip_hashes:
                zip_hashes[key] = fp
            zip_count += 1
        except:
            pass

print(f"Indexed {zip_count} files from unpacked ZIPs ({len(zip_hashes)} unique)")

# Now scan other dirs for matches
print("Scanning other directories for duplicates...")
skip_dirs = {'18_UNPACKED_ZIPS', '14_EXTENSIONS', '17_CONFIG', '.git', '__pycache__'}
dupes = []
scanned = 0

for entry in os.scandir(root):
    if not entry.is_dir() or entry.name in skip_dirs or entry.name.startswith('.'):
        continue
    for dirpath, _, filenames in os.walk(entry.path):
        for fn in filenames:
            fp = os.path.join(dirpath, fn)
            try:
                sz = os.path.getsize(fp)
                if sz < 100:
                    continue
                with open(fp, 'rb') as f:
                    h = hashlib.md5(f.read(4096)).hexdigest()
                key = (sz, h)
                if key in zip_hashes:
                    dupes.append({
                        'original': fp,
                        'zip_copy': zip_hashes[key],
                        'size': sz
                    })
                scanned += 1
                if scanned % 50000 == 0:
                    print(f"  Scanned {scanned}...")
            except:
                pass

print(f"Scanned {scanned} files in other dirs")
print(f"Duplicates found (ZIP contents already exist elsewhere): {len(dupes)}")
total_dup_mb = sum(d['size'] for d in dupes) / (1024*1024)
print(f"Duplicate space: {total_dup_mb:.1f} MB")

# Save
report = os.path.join(root, "00_SYSTEM", "dedup_report.json")
with open(report, 'w', encoding='utf-8') as f:
    json.dump({'dupes_found': len(dupes), 'dup_mb': round(total_dup_mb,1),
               'top': sorted(dupes, key=lambda x: -x['size'])[:30]}, f, indent=2)
print(f"Saved: {report}")

# Show top dupes
for d in sorted(dupes, key=lambda x: -x['size'])[:5]:
    print(f"\n  {d['size']/1024:.0f} KB duplicate:")
    print(f"    EXISTS: ...{d['original'][-70:]}")
    print(f"    ZIP:    ...{d['zip_copy'][-70:]}")
