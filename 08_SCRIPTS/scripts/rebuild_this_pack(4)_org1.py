from __future__ import annotations
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
ZIP_PATH = ROOT.parent / "LITIGATION_COMMAND_CENTER_DELTA11_ORDER_EVIDENCE_LINEAGE_APPEND_PACK_20260222.zip"

def main():
    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in sorted(ROOT.rglob("*")):
            if p.is_dir():
                continue
            if p.resolve() == ZIP_PATH.resolve():
                continue
            zf.write(p, p.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(ZIP_PATH, "r") as zf:
        bad = zf.testzip()
    print({"zip": str(ZIP_PATH), "bad_entry": bad})

if __name__ == "__main__":
    main()
