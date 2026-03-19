#!/usr/bin/env python3
"""
bin_fix_watcher.py (v32)

Automatically renames newly downloaded .bin (or no-extension) files in a folder if the
file magic indicates a known archive (ZIP/GZIP/TAR). This is the closest possible
"fix it, not me" workaround because some clients ignore the intended filename.

Behavior:
- Monitors a directory (default: ./Downloads or user-provided) on an interval.
- For each candidate file (extensions: .bin, .tmp, or no extension), reads magic bytes.
- If ZIP -> rename to *.zip (or append .zip) and (optionally) integrity-test.
- Never overwrites existing outputs (adds numeric suffix).

Usage:
  python bin_fix_watcher.py --dir "C:\Users\you\Downloads"
  python bin_fix_watcher.py --dir "/sdcard/Download" --interval 2

Exit codes:
- 0 normal
"""
import argparse, os, time, hashlib, zipfile, tarfile, gzip, sys

SIGS=[(b"PK\x03\x04",".zip","ZIP"),
      (b"\x1f\x8b\x08",".gz","GZIP")]

def sha256_file(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for chunk in iter(lambda:f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()

def detect(path):
    try:
        with open(path,"rb") as f:
            head=f.read(8)
        for sig,ext,kind in SIGS:
            if head.startswith(sig):
                return ext,kind
        # TAR detection
        with open(path,"rb") as f:
            f.seek(257)
            u=f.read(5)
        if u==b"ustar":
            return ".tar","TAR"
    except Exception:
        return "","UNKNOWN"
    return "","UNKNOWN"

def safe_rename(src, desired_ext):
    base=src
    if base.lower().endswith(desired_ext):
        return src, False
    dst=base + desired_ext
    if not os.path.exists(dst):
        os.rename(src, dst)
        return dst, True
    # suffix
    i=1
    while True:
        dst2=f"{base}.{i}{desired_ext}"
        if not os.path.exists(dst2):
            os.rename(src, dst2)
            return dst2, True
        i+=1

def verify(path, kind):
    if kind=="ZIP":
        with zipfile.ZipFile(path,"r") as z:
            bad=z.testzip()
        if bad:
            raise RuntimeError(f"ZIP integrity FAIL (bad member: {bad})")
    elif kind=="TAR":
        with tarfile.open(path,"r") as t:
            t.getmembers()[:1]
    elif kind=="GZIP":
        with gzip.open(path,"rb") as g:
            g.read(1)
    return True

def is_candidate(fn):
    lower=fn.lower()
    if lower.endswith(".bin") or lower.endswith(".tmp"):
        return True
    # no extension
    return ("." not in fn)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--dir", default="", help="Folder to watch")
    ap.add_argument("--interval", type=float, default=3.0)
    ap.add_argument("--verify", action="store_true", help="Integrity-check renamed archives")
    ap.add_argument("--once", action="store_true", help="Run one scan then exit")
    args=ap.parse_args()

    watch_dir=args.dir.strip() or os.path.join(os.path.expanduser("~"), "Downloads")
    if not os.path.isdir(watch_dir):
        print(f"FAIL: dir not found: {watch_dir}", file=sys.stderr)
        raise SystemExit(2)

    seen=set()
    def scan_once():
        changed=0
        for fn in os.listdir(watch_dir):
            if not is_candidate(fn):
                continue
            path=os.path.join(watch_dir, fn)
            if not os.path.isfile(path):
                continue
            key=(path, os.path.getsize(path))
            if key in seen:
                continue
            # wait for file to settle (size stable across two checks)
            sz1=os.path.getsize(path)
            time.sleep(0.2)
            sz2=os.path.getsize(path)
            if sz1!=sz2 or sz2==0:
                continue
            ext,kind=detect(path)
            seen.add(key)
            if kind=="UNKNOWN":
                continue
            new_path, did=safe_rename(path, ext)
            if did:
                changed += 1
                if args.verify:
                    try:
                        verify(new_path, kind)
                    except Exception as e:
                        print(f"WARN verify failed: {new_path} :: {e}", file=sys.stderr)
            # record new name too
            seen.add((new_path, os.path.getsize(new_path)))
        return changed

    print(f"OK watching={watch_dir} interval={args.interval}s verify={args.verify} once={args.once}")
    if args.once:
        c=scan_once()
        print(f"OK changed={c}")
        return

    while True:
        scan_once()
        time.sleep(args.interval)

if __name__=="__main__":
    main()
