#!/usr/bin/env python3
"""
Rebuilds the zip bundle deterministically from the current folder contents.
Usage: python rebuild_pack.py
"""
import os, zipfile, hashlib, json, pathlib

BASE = os.path.dirname(os.path.abspath(__file__))
ZIP_NAME = os.path.join(BASE, "COA_DRAFT_STACK_REBUILT.zip")

def sha256_path(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for chunk in iter(lambda: f.read(1<<20), b''):
            h.update(chunk)
    return h.hexdigest()

files=[]
for p in sorted(pathlib.Path(BASE).glob("*")):
    if p.is_file() and p.name not in [os.path.basename(ZIP_NAME)]:
        files.append(p)

with zipfile.ZipFile(ZIP_NAME, "w", compression=zipfile.ZIP_DEFLATED) as z:
    for p in files:
        z.write(p, arcname=p.name)

# verify
with zipfile.ZipFile(ZIP_NAME, "r") as z:
    bad = z.testzip()
    if bad:
        raise SystemExit(f"ZIP integrity failed at: {bad}")

manifest=[]
for p in files:
    manifest.append({"path": p.name, "bytes": p.stat().st_size, "sha256": sha256_path(str(p))})
print(json.dumps({"zip": os.path.basename(ZIP_NAME), "count": len(files), "manifest": manifest}, indent=2))
print("OK")
