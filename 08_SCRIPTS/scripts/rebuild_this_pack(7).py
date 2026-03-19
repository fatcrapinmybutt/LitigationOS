#!/usr/bin/env python3
from __future__ import annotations
import os, json, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_ZIP = ROOT.with_name(ROOT.name + ".zip")

def main():
    files = []
    for p in sorted(ROOT.rglob("*")):
        if p.is_file() and p != OUT_ZIP:
            files.append(p)
    with zipfile.ZipFile(OUT_ZIP, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for p in files:
            zf.write(p, p.relative_to(ROOT))
    with zipfile.ZipFile(OUT_ZIP, "r") as zf:
        bad = zf.testzip()
        if bad:
            raise SystemExit(f"zip test failed on {bad}")
    print(f"Built: {OUT_ZIP}")
    print(f"Files: {len(files)}")

if __name__ == "__main__":
    main()
