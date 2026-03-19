from __future__ import annotations
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
ZIP_PATH = ROOT.parent / "LITIGATION_COMMAND_CENTER_DELTA10_MAIN_UI_INTEGRATION_APPEND_PACK_20260222.zip"

def main():
    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in sorted(ROOT.rglob("*")):
            if p.is_dir():
                continue
            zf.write(p, p.relative_to(ROOT).as_posix())
    bad = zipfile.ZipFile(ZIP_PATH).testzip()
    print({"zip": str(ZIP_PATH), "bad_entry": bad})

if __name__ == "__main__":
    main()
