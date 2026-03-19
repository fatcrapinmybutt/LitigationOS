\
#!/usr/bin/env python3
"""
mbp_worldfirst_builder.py
Rebuilds a durable local zip from this folder.
"""
from __future__ import annotations
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def main() -> int:
    out = ROOT / "LitigationOS_AutopilotSuite_WORLD_FIRST.zip"
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for p in sorted(ROOT.rglob("*")):
            if p.is_dir():
                continue
            if p.name == out.name:
                continue
            z.write(p, arcname=str(p.relative_to(ROOT)))
    print(out, out.stat().st_size)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
