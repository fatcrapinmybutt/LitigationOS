#!/usr/bin/env python
from __future__ import annotations
import argparse, os, zipfile, json, zlib
from pathlib import Path
from datetime import datetime

def crc32_file(path: Path) -> str:
    crc = 0
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            crc = zlib.crc32(chunk, crc)
    return format(crc & 0xFFFFFFFF, "08x")

def build_zip(src_dir: Path, out_zip: Path) -> dict:
    files = []
    for p in sorted(src_dir.rglob("*")):
        if p.is_file():
            rel = p.relative_to(src_dir).as_posix()
            files.append({"path": rel, "bytes": p.stat().st_size, "crc32": crc32_file(p)})
    manifest = {
        "built_utc": datetime.utcnow().isoformat(timespec="seconds")+"Z",
        "src_dir": str(src_dir),
        "out_zip": str(out_zip),
        "files": files,
    }
    with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for item in files:
            z.write(src_dir / item["path"], arcname=item["path"])
        z.writestr("CRC32_RECEIPT.json", json.dumps(manifest, indent=2).encode("utf-8"))
    return manifest

def main():
    ap = argparse.ArgumentParser(description="World-first builder: rebuild zip with CRC32 receipts.")
    ap.add_argument("--src", default=".", help="Folder containing the pack files.")
    ap.add_argument("--out", default="OrganizerStack_REBUILT.zip")
    args = ap.parse_args()
    src = Path(args.src).resolve()
    out = Path(args.out).resolve()
    manifest = build_zip(src, out)
    print("BUILT:", out)
    print("FILES:", len(manifest["files"]))

if __name__ == "__main__":
    main()
