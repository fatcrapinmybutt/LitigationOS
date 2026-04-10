"""Scan all drives for Shady Oaks evidence files, photos, and documents."""
import os, json
from pathlib import Path

results = {"photos": [], "documents": [], "folders": [], "all_housing": []}

# Directories to scan
scan_dirs = [
    r"C:\Users\andre\Desktop",
    r"C:\Users\andre\LitigationOS\01_EVIDENCE\HOUSING",
    r"C:\Users\andre\LitigationOS\05_FILINGS",
    r"C:\Users\andre\LitigationOS\01_EVIDENCE",
    r"C:\Users\andre\LitigationOS\08_MEDIA",
]

# Also check removable drives
for drive in ["D:\\", "F:\\", "G:\\", "I:\\", "J:\\"]:
    if os.path.exists(drive):
        scan_dirs.append(drive)

PHOTO_EXTS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.heic', '.webp'}
DOC_EXTS = {'.pdf', '.md', '.txt', '.docx', '.doc', '.json', '.csv'}
SHADY_KEYWORDS = ['shady', 'oaks', 'housing', 'eviction', 'sewage', 'egle', 'mobile_home',
                   'mobilehome', 'whitehall', 'lot_17', 'lot17', 'water_shutoff', 'writ']

def matches_shady(name_lower):
    return any(kw in name_lower for kw in SHADY_KEYWORDS)

# Scan the HOUSING directory specifically (shallow)
housing_dir = r"C:\Users\andre\LitigationOS\01_EVIDENCE\HOUSING"
if os.path.isdir(housing_dir):
    for entry in os.scandir(housing_dir):
        ext = os.path.splitext(entry.name)[1].lower()
        if ext in DOC_EXTS or ext in PHOTO_EXTS:
            results["all_housing"].append({
                "path": entry.path,
                "size": entry.stat().st_size if entry.is_file() else 0,
                "ext": ext
            })

# Scan Desktop for SHADY folder
desktop = r"C:\Users\andre\Desktop"
for entry in os.scandir(desktop):
    name_l = entry.name.lower()
    if 'shady' in name_l:
        if entry.is_dir():
            results["folders"].append(entry.path)
            for root, dirs, files in os.walk(entry.path):
                for f in files:
                    fp = os.path.join(root, f)
                    ext = os.path.splitext(f)[1].lower()
                    sz = 0
                    try: sz = os.path.getsize(fp)
                    except: pass
                    if ext in PHOTO_EXTS:
                        results["photos"].append({"path": fp, "size": sz})
                    elif ext in DOC_EXTS:
                        results["documents"].append({"path": fp, "size": sz})
        else:
            ext = os.path.splitext(entry.name)[1].lower()
            sz = entry.stat().st_size if entry.is_file() else 0
            if ext in PHOTO_EXTS:
                results["photos"].append({"path": entry.path, "size": sz})
            elif ext in DOC_EXTS:
                results["documents"].append({"path": entry.path, "size": sz})

# Scan Desktop\PDF for shady-related
pdf_dir = os.path.join(desktop, "PDF")
if os.path.isdir(pdf_dir):
    for f in os.listdir(pdf_dir):
        if matches_shady(f.lower()):
            fp = os.path.join(pdf_dir, f)
            sz = 0
            try: sz = os.path.getsize(fp)
            except: pass
            results["documents"].append({"path": fp, "size": sz})

# Scan Desktop\SHADYOAKS_EVIDENCE_001
ev_dir = os.path.join(desktop, "SHADYOAKS_EVIDENCE_001")
if os.path.isdir(ev_dir):
    results["folders"].append(ev_dir)
    for root, dirs, files in os.walk(ev_dir):
        for f in files:
            fp = os.path.join(root, f)
            ext = os.path.splitext(f)[1].lower()
            sz = 0
            try: sz = os.path.getsize(fp)
            except: pass
            if ext in PHOTO_EXTS:
                results["photos"].append({"path": fp, "size": sz})
            elif ext in DOC_EXTS:
                results["documents"].append({"path": fp, "size": sz})

# Scan LitigationOS for photos with shady/housing keywords
for search_dir in [r"C:\Users\andre\LitigationOS\08_MEDIA", r"C:\Users\andre\LitigationOS\01_EVIDENCE"]:
    if not os.path.isdir(search_dir):
        continue
    for root, dirs, files in os.walk(search_dir):
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in PHOTO_EXTS:
                fp = os.path.join(root, f)
                name_l = f.lower()
                path_l = root.lower()
                if matches_shady(name_l) or matches_shady(path_l) or 'housing' in path_l:
                    sz = 0
                    try: sz = os.path.getsize(fp)
                    except: pass
                    results["photos"].append({"path": fp, "size": sz})

# Quick scan removable drives for shady-related photos (top-level only, fast)
for drive in ["D:\\", "F:\\", "G:\\", "I:\\"]:
    if not os.path.exists(drive):
        continue
    try:
        for entry in os.scandir(drive):
            if entry.is_dir() and matches_shady(entry.name.lower()):
                results["folders"].append(entry.path)
    except: pass

# Summary
print(f"=== SHADY OAKS FILE SCAN RESULTS ===")
print(f"Photos found: {len(results['photos'])}")
print(f"Documents found: {len(results['documents'])}")
print(f"Housing dir files: {len(results['all_housing'])}")
print(f"Shady-related folders: {len(results['folders'])}")
print()

if results["folders"]:
    print("FOLDERS:")
    for f in results["folders"]:
        print(f"  {f}")
    print()

if results["photos"]:
    print("PHOTOS:")
    for p in sorted(results["photos"], key=lambda x: -x["size"])[:30]:
        sz_mb = p["size"] / 1048576
        print(f"  [{sz_mb:.1f} MB] {p['path']}")
    print()

if results["documents"]:
    print("DOCUMENTS:")
    for d in sorted(results["documents"], key=lambda x: -x["size"])[:30]:
        sz_mb = d["size"] / 1048576
        print(f"  [{sz_mb:.1f} MB] {d['path']}")
    print()

if results["all_housing"]:
    print(f"HOUSING DIR ({len(results['all_housing'])} files):")
    by_ext = {}
    for h in results["all_housing"]:
        by_ext.setdefault(h["ext"], []).append(h)
    for ext, files in sorted(by_ext.items()):
        print(f"  {ext}: {len(files)} files")
        for f in sorted(files, key=lambda x: -x["size"])[:5]:
            sz_mb = f["size"] / 1048576
            print(f"    [{sz_mb:.2f} MB] {os.path.basename(f['path'])}")

# Save full results
out_path = r"D:\LitigationOS_tmp\shady_oaks_scan.json"
with open(out_path, "w") as fout:
    json.dump(results, fout, indent=2)
print(f"\nFull results saved to {out_path}")
