
from __future__ import annotations

import argparse
import json
from pathlib import Path
from .pipeline.harvest import run_harvest

def _parse_args():
    ap = argparse.ArgumentParser(prog="litos_harvest", description="Local-first LitigationOS Harvest Runner")
    ap.add_argument("--config", required=True, help="Path to harvest_config.json")
    ap.add_argument("--root", required=True, help="Root directory to scan (use hub)")
    ap.add_argument("--run-id", required=True, help="Run id (e.g., 20260214_123000)")
    ap.add_argument("--out", required=True, help="Output directory for this run")
    return ap.parse_args()

def main():
    args = _parse_args()
    config_path = Path(args.config).expanduser().resolve()
    root = Path(args.root).expanduser().resolve()
    out = Path(args.out).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)

    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    run_harvest(cfg=cfg, scan_root=root, run_id=args.run_id, out_dir=out)

if __name__ == "__main__":
    main()
