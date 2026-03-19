from __future__ import annotations
import hashlib
from pathlib import Path
from datetime import datetime, timezone

def deterministic_cycle_id(seed_parts: list[str]) -> str:
    payload = "|".join(seed_parts).encode("utf-8")
    h = hashlib.sha256(payload).hexdigest()[:20].upper()
    return f"CYCLE-09-{h}"

def make_cycle_id_from_paths(paths: list[str]) -> str:
    resolved = []
    for p in sorted(paths):
        fp = Path(p)
        if fp.exists():
            st = fp.stat()
            resolved.append(f"{fp.name}:{st.st_size}:{int(st.st_mtime)}")
        else:
            resolved.append(f"{fp}:MISSING")
    return deterministic_cycle_id(resolved)

if __name__ == "__main__":
    sample = make_cycle_id_from_paths(["Desktop.zip"])
    print(sample)
