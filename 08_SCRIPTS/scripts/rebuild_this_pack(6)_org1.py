from __future__ import annotations
import json, zipfile, hashlib, zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_ZIP = ROOT.parent / (ROOT.name + "_REBUILT.zip")

def main():
    files = [p for p in ROOT.rglob("*") if p.is_file()]
    with zipfile.ZipFile(OUT_ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(files):
            z.write(p, p.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(OUT_ZIP, "r") as z:
        bad = z.testzip()
        if bad:
            raise RuntimeError(f"Zip test failed at {bad}")
    print(f"Built {OUT_ZIP}")

if __name__ == "__main__":
    main()
