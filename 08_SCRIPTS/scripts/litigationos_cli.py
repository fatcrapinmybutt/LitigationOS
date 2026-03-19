#!/usr/bin/env python3
"""
LitigationOS CLI (MI-only) - deterministic, append-only.

Commands:
  init   - ensure canonical subfolders exist under --root
  ingest - scan and emit EvidenceAtoms + ChronoEvents + Packet shell

No network calls. Open-source dependencies optional.
"""

from __future__ import annotations
import argparse
from pathlib import Path
import sys

# Ensure pack root is on sys.path (so `import agents.*` works regardless of cwd)
PACK_ROOT = Path(__file__).resolve().parents[1]
if str(PACK_ROOT) not in sys.path:
    sys.path.insert(0, str(PACK_ROOT))

from agents.orchestrator import run as run_orchestrator  # noqa: E402

DEFAULT_CASE = "UNKNOWN_CASE"

def cmd_init(args: argparse.Namespace) -> int:
    root = Path(args.root)
    (root / "Evidence").mkdir(parents=True, exist_ok=True)
    (root / "Authority").mkdir(parents=True, exist_ok=True)
    (root / "ChronoDB").mkdir(parents=True, exist_ok=True)
    (root / "Artifacts").mkdir(parents=True, exist_ok=True)
    (root / "Logs").mkdir(parents=True, exist_ok=True)
    print(f"OK init: {root}")
    return 0

def cmd_ingest(args: argparse.Namespace) -> int:
    root = Path(args.root)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    run_dir = run_orchestrator(case_id=args.case_id, root=root, out_dir=out_dir)
    print(str(run_dir))
    return 0

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="litigationos_cli", description="LitigationOS CLI (MI-only, append-only).")
    sp = p.add_subparsers(dest="cmd", required=True)

    p_init = sp.add_parser("init", help="Create canonical folders under --root.")
    p_init.add_argument("--root", required=True, help="Canonical root folder (Windows or POSIX).")
    p_init.set_defaults(func=cmd_init)

    p_ingest = sp.add_parser("ingest", help="Scan --root and emit JSONL outputs to --out.")
    p_ingest.add_argument("--root", required=True, help="Folder to scan.")
    p_ingest.add_argument("--out", required=True, help="Output folder for this run family.")
    p_ingest.add_argument("--case-id", default=DEFAULT_CASE, help="Case identifier (e.g., 2024-001507-DC).")
    p_ingest.set_defaults(func=cmd_ingest)

    return p

def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)

if __name__ == "__main__":
    raise SystemExit(main())
