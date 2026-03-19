
from __future__ import annotations

import hashlib
import json
from pathlib import Path

def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        while True:
            b = f.read(1024*1024)
            if not b: break
            h.update(b)
    return h.hexdigest()

def main():
    root = Path(__file__).resolve().parent.parent
    manifest = []
    for p in sorted(root.rglob("*")):
        if p.is_dir(): continue
        if ".out" in p.parts or ".work" in p.parts: 
            continue
        manifest.append({"path": str(p.relative_to(root)).replace("\\","/"), "sha256": sha256(p), "size": p.stat().st_size})
    out = root / "MANIFEST.pack.json"
    out.write_text(json.dumps({"files": manifest}, indent=2), encoding="utf-8")
    print("Wrote", out)
if __name__=="__main__":
    main()
