import sys, os, zipfile, json, hashlib
from datetime import datetime
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

root = r"C:\Users\andre\LitigationOS"
zip_dir = os.path.join(root, "18_UNPACKED_ZIPS", "_originals")
unpack_base = os.path.join(root, "18_UNPACKED_ZIPS")
log_file = os.path.join(root, "00_SYSTEM", "reorg_move_log.jsonl")

# Categorize destination subfolders
def get_category(name):
    nl = name.lower()
    if 'event_horizon' in nl or 'eh_' in nl or 'eh24' in nl:
        return 'event_horizon'
    elif 'cyclepack' in nl or 'cycle' in nl:
        return 'cyclepacks'
    elif 'delta' in nl:
        return 'deltas'
    elif 'litigation' in nl or 'litos' in nl:
        return 'litigation_packs'
    elif 'blueprint' in nl:
        return 'blueprints'
    elif 'warchest' in nl or 'pinnacle' in nl:
        return 'warchest'
    elif 'sovereign' in nl or 'omega' in nl:
        return 'omega_packs'
    elif 'court' in nl or 'filing' in nl:
        return 'court_packs'
    elif 'copilot' in nl:
        return 'copilot_packs'
    else:
        return 'misc_packs'

success = 0
failed = 0
skipped = 0
new_files = []

for zf_name in sorted(os.listdir(zip_dir)):
    if not zf_name.lower().endswith('.zip'):
        continue
    zf_path = os.path.join(zip_dir, zf_name)
    category = get_category(zf_name)
    dest_dir = os.path.join(unpack_base, category, os.path.splitext(zf_name)[0])
    
    if os.path.exists(dest_dir):
        skipped += 1
        continue
    
    try:
        with zipfile.ZipFile(zf_path, 'r') as zf:
            # Test integrity first
            bad = zf.testzip()
            if bad:
                print(f"CORRUPT entry in {zf_name}: {bad}")
            
            os.makedirs(dest_dir, exist_ok=True)
            zf.extractall(dest_dir)
            
            # Track new files
            for info in zf.infolist():
                if not info.is_dir():
                    new_files.append({
                        'source_zip': zf_name,
                        'path': os.path.join(dest_dir, info.filename),
                        'size': info.file_size,
                        'ext': os.path.splitext(info.filename)[1].lower()
                    })
            
            success += 1
            if success % 10 == 0:
                print(f"  Unpacked {success} ZIPs...")
    except zipfile.BadZipFile:
        failed += 1
        print(f"BAD ZIP (skipped): {zf_name}")
    except Exception as e:
        failed += 1
        print(f"ERROR {zf_name}: {e}")

print(f"\nResults: {success} unpacked, {failed} failed, {skipped} skipped")
print(f"New files discovered: {len(new_files)}")

# Save new files catalog
catalog_path = os.path.join(root, "00_SYSTEM", "new_files_from_zips.json")
with open(catalog_path, 'w', encoding='utf-8') as f:
    json.dump(new_files, f, indent=2, default=str)
print(f"Catalog saved: {catalog_path}")

# Extension breakdown
from collections import Counter
ext_counts = Counter(nf['ext'] for nf in new_files)
print("\nFile types discovered:")
for ext, count in ext_counts.most_common(15):
    print(f"  {count:>6}x {ext or '(no ext)'}")
