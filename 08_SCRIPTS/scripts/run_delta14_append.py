#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

MODULES = [
    ("transcript_exact_quote_extractor", ["runtime/transcript_exact_quote_extractor.py"]),
    ("service_proof_artifact_parser", ["runtime/service_proof_artifact_parser.py"]),
    ("live_docket_importer", ["runtime/live_docket_importer.py"]),
]

def run_cmd(cmd: list[str], cwd: Path) -> dict:
    started = datetime.now(timezone.utc).isoformat()
    try:
        proc = subprocess.run([sys.executable, *cmd], cwd=str(cwd), capture_output=True, text=True, check=False)
        ended = datetime.now(timezone.utc).isoformat()
        return {
            "cmd": [sys.executable, *cmd],
            "returncode": proc.returncode,
            "stdout_tail": proc.stdout[-4000:],
            "stderr_tail": proc.stderr[-4000:],
            "started_utc": started,
            "ended_utc": ended,
            "ok": proc.returncode == 0,
        }
    except Exception as exc:
        ended = datetime.now(timezone.utc).isoformat()
        return {
            "cmd": [sys.executable, *cmd],
            "returncode": -1,
            "stdout_tail": "",
            "stderr_tail": repr(exc),
            "started_utc": started,
            "ended_utc": ended,
            "ok": False,
        }

def main() -> int:
    ap = argparse.ArgumentParser(description="Run DELTA14 append modules (transcript/service/docket importer) end-to-end.")
    ap.add_argument("--root", default=".", help="Litigation Command Center root folder")
    ap.add_argument("--dry-run", action="store_true", help="Print plan only; do not execute")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    runtime_dir = root / "runtime"
    if not runtime_dir.exists():
        print(f"ERROR: runtime dir not found under {root}", file=sys.stderr)
        return 2

    run_id = "delta14-append-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    ledger = {
        "run_id": run_id,
        "root": str(root),
        "dry_run": args.dry_run,
        "modules": [],
    }

    for name, cmd in MODULES:
        if args.dry_run:
            ledger["modules"].append({"name": name, "cmd": [sys.executable, *cmd], "ok": None})
            continue
        result = run_cmd(cmd, root)
        result["name"] = name
        ledger["modules"].append(result)

    ledger["summary"] = {
        "total": len(ledger["modules"]),
        "ok": sum(1 for m in ledger["modules"] if m.get("ok") is True),
        "failed": sum(1 for m in ledger["modules"] if m.get("ok") is False),
    }

    out = root / "manifests" / "delta14_append_runner_ledger.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(ledger, indent=2), encoding="utf-8")
    print(json.dumps({"run_id": run_id, "summary": ledger["summary"], "ledger": str(out)}, indent=2))
    return 0 if ledger["summary"]["failed"] == 0 else 1

if __name__ == "__main__":
    raise SystemExit(main())
