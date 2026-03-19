#!/usr/bin/env python3
from __future__ import annotations

import py_compile
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent

def main() -> None:
    py_compile.compile(str(HERE / "gdrive_scoped_organizer.py"), doraise=True)
    print("[OK] py_compile")

    p = subprocess.run(
        [sys.executable, str(HERE / "gdrive_scoped_organizer.py"), "--self-test", "--mock"],
        cwd=str(HERE),
        text=True,
        capture_output=True,
    )
    sys.stdout.write(p.stdout)
    if p.returncode != 0:
        sys.stderr.write(p.stderr)
        raise SystemExit(p.returncode)
    print("[OK] mock self-test")

if __name__ == "__main__":
    main()
