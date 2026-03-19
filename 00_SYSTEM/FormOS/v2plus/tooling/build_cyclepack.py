#!/usr/bin/env python3
"""
build_cyclepack.py

Creates a "CyclePack" ZIP from a vault folder or specific output folder.
- Writes manifest.json with sha256 + byte counts.
- Zips everything deterministically (stable file ordering).

Usage:
  python tooling/build_cyclepack.py --root D:/LitigationOS_Vault --out D:/LitigationOS_Vault/90_REPORTS/CyclePack.zip
"""

from __future__ import annotations
import argparse, hashlib, json, zipfile
from pathlib import Path

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for ch in iter(lambda: f.read(1024*1024), b""):
            h.update(ch)
    return h.hexdigest()

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, help="Folder to pack")
    ap.add_argument("--out", required=True, help="Output zip path")
    ap.add_argument("--exclude", nargs="*", default=["00_OBJECTS"], help="Top-level subfolders to exclude (default: 00_OBJECTS)")
    args = ap.parse_args()

    root = Path(args.root)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    files = []
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(root)
        if rel.parts and rel.parts[0] in set(args.exclude):
            continue
        files.append(p)

    manifest = {"root": str(root), "file_count": len(files), "files": []}
    for p in files:
        rel = str(p.relative_to(root)).replace("\\","/")
        manifest["files"].append({"path": rel, "bytes": p.stat().st_size, "sha256": sha256_file(p)})
    man_path = out.with_suffix(".manifest.json")
    man_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.write(man_path, arcname=man_path.name)
        for p in files:
            rel = str(p.relative_to(root)).replace("\\","/")
            z.write(p, arcname=rel)

    print(f"OK: cyclepack={out} manifest={man_path}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
