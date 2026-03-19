"""
OMEGA Phase 8: Impeachment + Adversary Refresh
Orchestrate i_impeachment, b_authority_chains, a_readiness, k_adversary
against new transcript extracts in cycle_dir/extracts/.
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

from config import (
    SCANS_ROOT, get_cyclepack_dir, report_progress, CYCLE_TS,
)
from safety import write_phase_checkpoint, is_phase_done

# Existing scripts in C:\Users\andre\scans
SCRIPTS = {
    "impeachment":      SCANS_ROOT / "i_impeachment.py",
    "authority_chains":  SCANS_ROOT / "b_authority_chains.py",
    "readiness":         SCANS_ROOT / "a_readiness.py",
    "adversary":         SCANS_ROOT / "k_adversary.py",
}


def _collect_new_extracts(cycle_dir: Path) -> list[Path]:
    """Gather .txt/.json extract files from cycle_dir/extracts/."""
    extracts_dir = cycle_dir / "extracts"
    if not extracts_dir.exists():
        return []
    results: list[Path] = []
    for root, _dirs, files in os.walk(str(extracts_dir)):
        for f in files:
            if f.endswith((".txt", ".json", ".jsonl")):
                results.append(Path(root) / f)
    return sorted(results)


def _run_script(script_path: Path, label: str, dry_run: bool) -> dict:
    """Run an existing script via subprocess, return status dict."""
    result = {
        "script": label,
        "path": str(script_path),
        "status": "skipped",
        "elapsed_seconds": 0,
        "error": None,
    }
    if not script_path.exists():
        result["status"] = "not_found"
        result["error"] = f"Script not found: {script_path}"
        return result

    if dry_run:
        result["status"] = "dry_run"
        return result

    start = time.time()
    try:
        proc = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=600,
            cwd=str(script_path.parent),
        )
        result["elapsed_seconds"] = round(time.time() - start, 1)
        result["returncode"] = proc.returncode
        if proc.returncode == 0:
            result["status"] = "success"
        else:
            result["status"] = "error"
            result["error"] = (proc.stderr or proc.stdout or "")[-500:]
    except subprocess.TimeoutExpired:
        result["elapsed_seconds"] = round(time.time() - start, 1)
        result["status"] = "timeout"
        result["error"] = "Script timed out after 600s"
    except Exception as e:
        result["elapsed_seconds"] = round(time.time() - start, 1)
        result["status"] = "exception"
        result["error"] = str(e)[:500]

    return result


def run_litigation_refresh(cycle_dir: Path, dry_run: bool = False):
    if is_phase_done(cycle_dir, "phase8"):
        print("[PHASE8] Already complete, skipping", file=sys.stderr)
        return

    print("[PHASE8] Litigation Refresh starting...", file=sys.stderr)
    start = time.time()

    # Collect new extracts
    extracts = _collect_new_extracts(cycle_dir)
    print(f"[PHASE8] Found {len(extracts)} extract files in {cycle_dir / 'extracts'}", file=sys.stderr)

    # Run each script in sequence
    script_results: list[dict] = []
    for idx, (label, script_path) in enumerate(SCRIPTS.items(), 1):
        print(f"[PHASE8] Running {label} ({idx}/{len(SCRIPTS)})...", file=sys.stderr)
        res = _run_script(script_path, label, dry_run)
        script_results.append(res)
        report_progress("phase8", idx, len(SCRIPTS))
        if res["status"] not in ("success", "dry_run", "skipped"):
            print(f"[PHASE8] WARNING: {label} returned {res['status']}: {res.get('error', '')}", file=sys.stderr)

    elapsed = round(time.time() - start, 1)

    # Build report
    report = {
        "phase": "phase8_litigation_refresh",
        "cycle_dir": str(cycle_dir),
        "extracts_found": len(extracts),
        "extract_files": [str(e) for e in extracts[:50]],
        "script_results": script_results,
        "summary": {
            "total_scripts": len(script_results),
            "success": sum(1 for r in script_results if r["status"] == "success"),
            "errors": sum(1 for r in script_results if r["status"] in ("error", "exception", "timeout")),
            "dry_run": sum(1 for r in script_results if r["status"] == "dry_run"),
            "not_found": sum(1 for r in script_results if r["status"] == "not_found"),
        },
        "elapsed_seconds": elapsed,
    }

    # Write output
    if not dry_run:
        cycle_dir.mkdir(parents=True, exist_ok=True)
        report_path = cycle_dir / "litigation_refresh_report.json"
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"[PHASE8] Report written: {report_path}", file=sys.stderr)

        write_phase_checkpoint(cycle_dir, "phase8", {
            "status": "done",
            "extracts": len(extracts),
            "scripts_ok": report["summary"]["success"],
            "scripts_err": report["summary"]["errors"],
            "elapsed": f"{elapsed:.0f}s",
        })
    else:
        print(f"[PHASE8] DRY RUN — would write litigation_refresh_report.json", file=sys.stderr)

    print(f"[PHASE8] Complete in {elapsed:.0f}s — "
          f"{report['summary']['success']}/{len(SCRIPTS)} scripts OK",
          file=sys.stderr)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Phase 8: Litigation Refresh")
    parser.add_argument("--cycle-ts", default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    run_litigation_refresh(get_cyclepack_dir(args.cycle_ts or CYCLE_TS), args.dry_run)
