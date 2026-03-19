#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract_archive.py

Tries to extract intake/DOCKETSPPO.zip. Fails fast if archive is not a valid zip.
(If you upload a true zip, this will work.)

Usage:
  python extract_archive.py --root <CyclePackRoot> [--force]
"""
from __future__ import annotations
import argparse, json, zipfile, shutil
from pathlib import Path

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    root = Path(args.root).expanduser().resolve()
    zpath = root/"intake"/"DOCKETSPPO.zip"
    outdir = root/"intake"/"DOCKETSPPO_extracted"
    if not zpath.exists():
        print("Missing:", zpath)
        return 2
    try:
        with zipfile.ZipFile(zpath, "r") as z:
            names = z.namelist()
    except Exception as e:
        print("Not a valid zip in this runtime:", type(e).__name__, str(e))
        return 3

    if outdir.exists():
        if not args.force:
            print("Already exists (use --force):", outdir)
            return 4
        shutil.rmtree(outdir)

    outdir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zpath, "r") as z:
        z.extractall(outdir)

    (outdir/"manifest.json").write_text(json.dumps({"entries": len(names), "files": names}, indent=2), encoding="utf-8")
    print("Extracted:", outdir)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
