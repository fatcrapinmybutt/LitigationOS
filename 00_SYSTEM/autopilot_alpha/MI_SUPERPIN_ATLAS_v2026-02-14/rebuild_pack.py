#!/usr/bin/env python3
"""Rebuild ZIP + verify manifest hashes.
Run from inside the extracted folder.
"""
import os, csv, hashlib, zipfile, sys

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()

root = os.path.dirname(os.path.abspath(__file__))
manifest = os.path.join(root, "manifest.csv")
ok = True
if os.path.exists(manifest):
    with open(manifest, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            fp = os.path.join(root, row["file"])
            if not os.path.exists(fp):
                print("MISSING:", row["file"]); ok = False; continue
            h = sha256_file(fp)
            if h.lower() != row["sha256"].lower():
                print("HASH MISMATCH:", row["file"]); ok = False
else:
    print("No manifest.csv found; skipping hash verification.")
if not ok:
    print("Verification FAILED.")
    sys.exit(2)

zip_name = os.path.basename(root) + ".zip"
zip_path = os.path.join(os.path.dirname(root), zip_name)
with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
    for fn in os.listdir(root):
        if fn.endswith(".zip"): 
            continue
        z.write(os.path.join(root, fn), arcname=os.path.join(os.path.basename(root), fn))
with zipfile.ZipFile(zip_path, "r") as z:
    bad = z.testzip()
if bad:
    print("ZIP integrity FAILED at:", bad)
    sys.exit(3)
print("OK:", zip_path)
