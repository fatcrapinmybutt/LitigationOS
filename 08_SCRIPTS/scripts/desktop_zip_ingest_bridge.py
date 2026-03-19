from __future__ import annotations
import json, zipfile, hashlib, zlib, re
from pathlib import Path
from collections import defaultdict, Counter

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def crc32_hex(b: bytes) -> str:
    return f"{zlib.crc32(b) & 0xffffffff:08x}"

copy_suffix_re = re.compile(r"\s*\(\d+\)$")

def normalized_stem(name: str) -> str:
    stem = Path(name).stem.replace(" ", "_")
    return copy_suffix_re.sub("", stem)

def classify(name: str) -> str:
    ext = Path(name).suffix.lower()
    n = name.lower()
    if ext in [".md", ".txt"] and any(k in n for k in ["hyperpin", "prompt", "event_horizon", "eh24"]):
        return "prompt_text"
    if ext == ".json" and "catalog" in n:
        return "operator_catalog"
    if ext == ".json" and ("schema" in n or "replay" in n or "transition" in n):
        return "schema_or_runtime"
    if ext in [".ps1", ".bat"]:
        return "launcher"
    if ext == ".svg":
        return "svg_blueprint"
    if ext == ".py":
        return "python_code"
    return ext.lstrip(".") or "other"

def ingest(zip_path: Path):
    records = []
    with zipfile.ZipFile(zip_path) as z:
        for info in z.infolist():
            if info.is_dir():
                continue
            raw = z.read(info.filename)
            records.append({
                "name": info.filename,
                "class": classify(info.filename),
                "bytes": info.file_size,
                "sha256": sha256_bytes(raw),
                "crc32": crc32_hex(raw),
                "normalized_stem": normalized_stem(info.filename),
            })
    return records

if __name__ == "__main__":
    import sys
    zp = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("Desktop.zip")
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("desktop_corpus_inventory.min.json")
    records = ingest(zp)
    out.write_text(json.dumps(records, indent=2), encoding="utf-8")
    print(f"Wrote {len(records)} records to {out}")
