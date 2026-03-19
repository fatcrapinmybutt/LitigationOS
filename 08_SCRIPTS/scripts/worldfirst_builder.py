#!/usr/bin/env python3
"""
worldfirst_builder.py
Rebuilds a deterministic ZIP of this spec pack (or any folder) WITHOUT network.
- Stable file ordering
- Ensures required instruction files exist
- Verifies the resulting zip is non-empty and readable

Usage:
  python worldfirst_builder.py --src . --out ../AGENT_SPEC_PACK_v3_REBUILT.zip
"""
from __future__ import annotations
import argparse, zipfile
from pathlib import Path

REQUIRED_FILES = ["README_START_HERE.txt", "INSTRUCTIONS_STEP_BY_STEP.txt"]

def iter_files(src: Path):
    files = []
    for p in src.rglob("*"):
        if p.is_file():
            rel = p.relative_to(src).as_posix()
            if rel.lower().endswith(".zip"):
                continue
            files.append((rel, p))
    files.sort(key=lambda x: x[0])
    return files

def verify_required(src: Path):
    missing = [f for f in REQUIRED_FILES if not (src / f).exists()]
    if missing:
        raise SystemExit(f"Missing required files: {missing}")

def build_zip(src: Path, out_zip: Path):
    verify_required(src)
    out_zip.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for rel, p in iter_files(src):
            z.write(p, rel)
    if not out_zip.exists() or out_zip.stat().st_size <= 0:
        raise SystemExit("ZIP build failed: output missing or empty.")
    with zipfile.ZipFile(out_zip, "r") as z:
        bad = z.testzip()
        if bad is not None:
            raise SystemExit(f"ZIP failed integrity test at: {bad}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=".", help="Source folder to zip")
    ap.add_argument("--out", required=True, help="Output zip file path")
    args = ap.parse_args()
    src = Path(args.src).resolve()
    out_zip = Path(args.out).resolve()
    if not src.exists() or not src.is_dir():
        raise SystemExit(f"Source folder not found: {src}")
    build_zip(src, out_zip)
    print(str(out_zip))

if __name__ == "__main__":
    main()
