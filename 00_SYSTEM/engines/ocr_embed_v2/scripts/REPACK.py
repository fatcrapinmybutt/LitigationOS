
from __future__ import annotations

import zipfile
from pathlib import Path

def repack(root: Path, out_zip: Path) -> None:
    files = [p for p in root.rglob("*") if p.is_file()]
    # exclude outputs and work dirs
    keep = []
    for p in files:
        rel = p.relative_to(root)
        if rel.parts and rel.parts[0] in {".out", ".work"}:
            continue
        keep.append(p)
    keep = sorted(keep, key=lambda p: str(p.relative_to(root)).replace("\\","/"))
    if out_zip.exists():
        out_zip.unlink()
    with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for p in keep:
            arc = str(p.relative_to(root)).replace("\\","/")
            z.write(p, arcname=arc)
    with zipfile.ZipFile(out_zip, "r") as z:
        bad = z.testzip()
        if bad:
            raise SystemExit(f"ZIP integrity failure at: {bad}")
    print("Wrote", out_zip, "bytes", out_zip.stat().st_size)

def main():
    root = Path(__file__).resolve().parent.parent
    out_zip = root / "REPACKED.zip"
    repack(root, out_zip)

if __name__ == "__main__":
    main()
