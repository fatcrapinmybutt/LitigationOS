#!/usr/bin/env python3
"""
rebuild_verify.py
- Verifies manifest hashes inside an extracted packet folder.
Usage:
  python rebuild_verify.py --root "<extracted_folder>"
"""
import argparse, csv, hashlib, os, sys

def sha256_file(path, chunk=1024*1024):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        while True:
            b=f.read(chunk)
            if not b: break
            h.update(b)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root", required=True, help="Path to extracted packet folder (contains manifest.csv)")
    args=ap.parse_args()
    root=os.path.abspath(args.root)
    man=os.path.join(root,"manifest.csv")
    if not os.path.exists(man):
        print("ERROR: manifest.csv not found at:", man)
        return 2
    ok=0; bad=0; missing=0
    with open(man, newline="", encoding="utf-8") as f:
        r=csv.DictReader(f)
        for row in r:
            rel=row["relpath"]
            expect=row["sha256"].lower().strip()
            p=os.path.join(root, rel.replace("/", os.sep))
            if not os.path.exists(p):
                print("MISSING:", rel)
                missing += 1
                continue
            got=sha256_file(p)
            if got != expect:
                print("BADHASH:", rel, "got", got, "expected", expect)
                bad += 1
            else:
                ok += 1
    print(f"OK={ok} BADHASH={bad} MISSING={missing}")
    return 0 if (bad==0 and missing==0) else 1

if __name__ == "__main__":
    raise SystemExit(main())
