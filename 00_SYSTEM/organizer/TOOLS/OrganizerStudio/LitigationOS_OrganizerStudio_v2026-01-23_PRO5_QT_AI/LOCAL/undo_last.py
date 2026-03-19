#!/usr/bin/env python
from __future__ import annotations
import argparse, csv, os, shutil
from pathlib import Path
from datetime import datetime

def main():
    ap = argparse.ArgumentParser(description="Undo last OrganizerStack APPLY using undo.csv")
    ap.add_argument("--run_dir", required=True)
    args = ap.parse_args()
    run_dir = Path(args.run_dir)
    undo = run_dir / "undo.csv"
    if not undo.exists():
        raise SystemExit(f"undo.csv not found in {run_dir}")

    rows = list(csv.DictReader(open(undo, "r", encoding="utf-8")))
    # reverse order
    for r in reversed(rows):
        ua = (r.get("undo_action") or "").upper()
        src = Path(r.get("src",""))
        dst = Path(r.get("dst",""))
        try:
            if ua == "MOVE_BACK":
                # src is current location (moved-to), dst is original (moved-from)
                if src.exists():
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    # do not overwrite
                    if dst.exists():
                        # collision: place next to dst with suffix
                        alt = dst.parent / f"{dst.stem}__UNDO_{datetime.now().strftime('%Y%m%d_%H%M%S')}{dst.suffix}"
                        shutil.move(str(src), str(alt))
                    else:
                        shutil.move(str(src), str(dst))
            elif ua == "DELETE":
                if src.exists() and src.is_file():
                    src.unlink()
        except Exception:
            continue

    print("UNDO COMPLETE")


def run(argv: list[str]) -> int:
    """Programmatic entrypoint for GUI and tests."""
    import sys as _sys
    old = _sys.argv
    _sys.argv = [old[0]] + list(argv)
    try:
        main()
        return 0
    except SystemExit as e:
        try:
            return int(e.code or 0)
        except Exception:
            return 1
    finally:
        _sys.argv = old


if __name__ == "__main__":
    main()
