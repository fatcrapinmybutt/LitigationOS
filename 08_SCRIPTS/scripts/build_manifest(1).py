from __future__ import annotations
from pathlib import Path
import json, zlib
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "manifests" / "build_manifest.json"

def file_record(p: Path):
    b = p.read_bytes()
    crc = zlib.crc32(b) & 0xffffffff
    st = p.stat()
    return {
        "path": p.relative_to(ROOT).as_posix(),
        "bytes": st.st_size,
        "mtime": int(st.st_mtime),
        "crc32": f"{crc:08x}",
        "integrity_key": f"{p.relative_to(ROOT).as_posix()}|{crc:08x}|{st.st_size}|{int(st.st_mtime)}"
    }

def main():
    files = []
    for p in sorted(ROOT.rglob("*")):
        if p.is_dir():
            continue
        files.append(file_record(p))
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "root": ROOT.name,
        "file_count": len(files),
        "files": files
    }
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print({"out": str(OUT), "file_count": len(files)})

if __name__ == "__main__":
    main()
