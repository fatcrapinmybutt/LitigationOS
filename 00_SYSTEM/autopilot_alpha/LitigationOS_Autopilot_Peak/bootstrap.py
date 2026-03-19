#!/usr/bin/env python3
"""
bootstrap.py — self-assembling runner
- creates .venv (optional)
- installs python deps from requirements_peak.txt (optional)
- runs autopilot module commands through the venv interpreter

Usage:
  python bootstrap.py scan --auto
  python bootstrap.py run --auto --profile peak --stages inventory,unpack,ocr,convert,chunk

Notes:
- Network is required only if you choose to install deps.
- You can disable installs with --no-install.
"""
from __future__ import annotations
import argparse
import os
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
VENV_DIR = BASE / ".venv"
REQ_FILE = BASE / "requirements_peak.txt"

def _run(cmd: list[str]) -> int:
    return subprocess.call(cmd)

def _py_in_venv() -> Path:
    if os.name == "nt":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"

def ensure_venv() -> Path:
    py = _py_in_venv()
    if py.exists():
        return py
    print(f"[bootstrap] Creating venv at: {VENV_DIR}")
    rc = _run([sys.executable, "-m", "venv", str(VENV_DIR)])
    if rc != 0:
        raise SystemExit(rc)
    return py

def pip_install(py: Path) -> None:
    if not REQ_FILE.exists():
        print("[bootstrap] No requirements file found; skipping install.")
        return
    print("[bootstrap] Upgrading pip...")
    _run([str(py), "-m", "pip", "install", "--upgrade", "pip"])
    print(f"[bootstrap] Installing deps from: {REQ_FILE.name}")
    rc = _run([str(py), "-m", "pip", "install", "-r", str(REQ_FILE)])
    if rc != 0:
        raise SystemExit(rc)

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="LitigationOS Autopilot bootstrapper")
    p.add_argument("--no-venv", action="store_true", help="Run with system python (no venv)")
    p.add_argument("--no-install", action="store_true", help="Do not install deps (even if venv is created)")

    # everything after the bootstrap flags is passed to -m autopilot
    p.add_argument("autopilot_args", nargs=argparse.REMAINDER, help="Args forwarded to: python -m autopilot ...")

    args = p.parse_args(argv)

    forwarded = args.autopilot_args
    if forwarded and forwarded[0] == "--":
        forwarded = forwarded[1:]
    if not forwarded:
        print("Examples:\n  python bootstrap.py -- scan --auto\n  python bootstrap.py -- run --auto --profile peak")
        return 2

    if args.no_venv:
        py = Path(sys.executable)
    else:
        py = ensure_venv()
        if not args.no_install:
            pip_install(py)

    cmd = [str(py), "-m", "autopilot"] + forwarded
    print("[bootstrap] Running:", " ".join(cmd))
    return _run(cmd)

if __name__ == "__main__":
    raise SystemExit(main())
