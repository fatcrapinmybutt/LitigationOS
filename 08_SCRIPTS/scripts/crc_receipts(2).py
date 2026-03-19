from __future__ import annotations
from pathlib import Path
import json, zlib
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "manifests" / "crc_receipts.json"

INCLUDE_PREFIXES = ("ui/", "data/", "runtime/", "schemas/", "docs/")

def main():
    receipts = []
    for p in sorted(ROOT.rglob("*")):
        if p.is_dir():
            continue
        rel = p.relative_to(ROOT).as_posix()
        if not rel.startswith(INCLUDE_PREFIXES):
            continue
        b = p.read_bytes()
        crc = zlib.crc32(b) & 0xffffffff
        receipts.append({
            "path": rel,
            "crc32": f"{crc:08x}",
            "bytes": len(b)
        })
    OUT.write_text(json.dumps({
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "receipt_count": len(receipts),
        "receipts": receipts
    }, indent=2), encoding="utf-8")
    print({"out": str(OUT), "receipt_count": len(receipts)})

if __name__ == "__main__":
    main()
