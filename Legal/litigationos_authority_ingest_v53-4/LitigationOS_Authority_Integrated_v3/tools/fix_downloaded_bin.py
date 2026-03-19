#!/usr/bin/env python3
"""
fix_downloaded_bin.py (v31)

Problem: Some clients download sandbox links with a generic extension (.bin) even when the
content is a ZIP. This script detects common archive signatures (ZIP, GZIP, TAR) and
renames the file accordingly, then verifies the archive can be opened.

Usage:
  python fix_downloaded_bin.py /path/to/file.bin
  python fix_downloaded_bin.py /path/to/file.bin --out /path/to/file.zip
  python fix_downloaded_bin.py /path/to/file.bin --sha256 <expected_sha256>

Notes:
- Detection is by magic bytes only; no network calls.
- If the file is ZIP, it also runs a zip integrity test.
"""
import argparse, hashlib, os, sys, zipfile, tarfile, gzip

MAGIC = [
    (b"PK\x03\x04", ".zip", "ZIP"),
    (b"\x1f\x8b\x08", ".gz", "GZIP"),
]

def sha256_file(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for chunk in iter(lambda:f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()

def detect(path):
    with open(path,"rb") as f:
        head=f.read(8)
    for sig,ext,kind in MAGIC:
        if head.startswith(sig):
            return ext, kind
    # TAR detection (ustar at offset 257)
    try:
        with open(path,"rb") as f:
            f.seek(257)
            u=f.read(5)
        if u == b"ustar":
            return ".tar", "TAR"
    except Exception:
        pass
    return "", "UNKNOWN"

def verify(path, kind):
    if kind=="ZIP":
        with zipfile.ZipFile(path,"r") as z:
            bad=z.testzip()
        if bad:
            raise RuntimeError(f"ZIP integrity FAIL (first bad member: {bad})")
    elif kind=="TAR":
        with tarfile.open(path,"r") as t:
            t.getmembers()[:1]
    elif kind=="GZIP":
        with gzip.open(path,"rb") as g:
            g.read(1)
    return True

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--out", default="")
    ap.add_argument("--sha256", default="")
    args=ap.parse_args()

    if not os.path.exists(args.path) or os.path.getsize(args.path)==0:
        print("FAIL: file missing or empty", file=sys.stderr); raise SystemExit(2)

    actual=sha256_file(args.path)
    if args.sha256 and args.sha256.lower()!=actual.lower():
        print(f"FAIL: sha256 mismatch\nexpected={args.sha256}\nactual={actual}", file=sys.stderr)
        raise SystemExit(2)

    ext,kind=detect(args.path)
    if kind=="UNKNOWN":
        print(f"FAIL: unknown file type (sha256={actual})", file=sys.stderr)
        raise SystemExit(2)

    out=args.out.strip()
    if not out:
        base=args.path
        # if already has correct ext, keep
        if base.lower().endswith(ext):
            out=base
        else:
            out=base + ext

    if os.path.abspath(out)!=os.path.abspath(args.path):
        if os.path.exists(out):
            print("FAIL: output already exists", file=sys.stderr); raise SystemExit(2)
        os.rename(args.path, out)

    verify(out, kind)
    print(f"OK kind={kind} out={out} sha256={actual}")

if __name__=="__main__":
    main()
