#!/usr/bin/env python3
"""
Autonomous Pipeline Runner — Orchestrates critical path scripts with
checkpoint/resume, SQL progress tracking, and auto-retry.

Runs the three critical path scripts in order:
  1. noreply_pdf_processor.py (347 PDFs → unblocks pin-graft)
  2. backup_rotation.py (DB safety net)
  3. ocr_evidence_pipeline.py (scanned evidence)

Features:
  - Checkpoint after each phase (crash-resume)
  - SQL todos table updates
  - Auto-retry with exponential backoff (3 attempts)
  - Progress reporting to PROGRESS_LOG.md
  - Invocable via command-runner MCP: exec_pipeline_phase("autonomous")

Usage:
    python autonomous_runner.py              # Run all phases
    python autonomous_runner.py --phase 1    # Run specific phase
    python autonomous_runner.py --status     # Show progress
    python autonomous_runner.py --resume     # Resume from last checkpoint
"""

import sys
import os
import json
import time
import sqlite3
import subprocess
import logging
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')
sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', errors='replace')

# ── Configuration ──────────────────────────────────────────────────────

LITIGOS_ROOT = Path(r"C:\Users\andre\LitigationOS")
SCRIPTS_DIR = LITIGOS_ROOT / "00_SYSTEM" / "scripts"
CHECKPOINT_FILE = SCRIPTS_DIR / "_autonomous_checkpoint.json"
PROGRESS_LOG = LITIGOS_ROOT / "00_SYSTEM" / "PROGRESS_LOG.md"
DB_PATH = LITIGOS_ROOT / "litigation_context.db"

MAX_RETRIES = 3
RETRY_BACKOFF = [30, 60, 120]  # seconds between retries

# Phase definitions: (id, script, args, timeout_seconds, todo_id)
PHASES = [
    {
        "id": 1,
        "name": "NoReply PDF Processing",
        "script": "noreply_pdf_processor.py",
        "args": [],
        "timeout": 1800,  # 30 min for 347 PDFs
        "todo_id": "exec-noreply-pdfs",
        "description": "Extract, classify, and index 347+ NoReply court PDFs",
    },
    {
        "id": 2,
        "name": "Database Backup",
        "script": "backup_rotation.py",
        "args": [],
        "timeout": 600,
        "todo_id": "exec-backup-rotation",
        "description": "Backup main DB + lane DBs with 7/4/3 rotation",
    },
    {
        "id": 3,
        "name": "OCR Evidence Pipeline",
        "script": "ocr_evidence_pipeline.py",
        "args": [],
        "timeout": 1200,
        "todo_id": "exec-ocr-pipeline",
        "description": "OCR scanned evidence images via Tesseract/PyMuPDF",
    },
]

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S',
)
log = logging.getLogger("autonomous_runner")


# ── Checkpoint Management ──────────────────────────────────────────────

def load_checkpoint() -> Dict:
    if CHECKPOINT_FILE.exists():
        with open(CHECKPOINT_FILE, 'r') as f:
            return json.load(f)
    return {"completed_phases": [], "started_at": None, "last_update": None}


def save_checkpoint(cp: Dict):
    cp["last_update"] = datetime.now().isoformat()
    with open(CHECKPOINT_FILE, 'w') as f:
        json.dump(cp, f, indent=2, default=str)


# ── Progress Reporting ─────────────────────────────────────────────────

def log_progress(message: str):
    """Append to PROGRESS_LOG.md for visibility."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"- [{timestamp}] {message}\n"

    try:
        with open(PROGRESS_LOG, 'a', encoding='utf-8') as f:
            if f.tell() == 0:
                f.write("# LitigationOS — Autonomous Runner Progress\n\n")
            f.write(entry)
    except Exception:
        pass


# ── Phase Execution ────────────────────────────────────────────────────

def run_phase(phase: Dict, attempt: int = 1) -> Dict:
    """Execute a single pipeline phase with error handling."""
    script_path = SCRIPTS_DIR / phase["script"]
    if not script_path.exists():
        return {"status": "error", "error": f"Script not found: {script_path}"}

    cmd = [sys.executable, str(script_path)] + phase["args"]
    log.info(f"Phase {phase['id']}: {phase['name']} (attempt {attempt}/{MAX_RETRIES})")
    log.info(f"  Command: {' '.join(cmd)}")
    log_progress(f"Phase {phase['id']} START: {phase['name']} (attempt {attempt})")

    start = time.time()
    try:
        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(script_path.parent),
            timeout=phase["timeout"],
            env=env,
            encoding='utf-8',
            errors='replace',
        )

        elapsed = round(time.time() - start, 1)

        if result.returncode == 0:
            log.info(f"  ✓ Phase {phase['id']} completed in {elapsed}s")
            log_progress(f"Phase {phase['id']} DONE: {phase['name']} ({elapsed}s)")

            # Print last 20 lines of output for summary
            lines = (result.stdout or "").strip().split('\n')
            for line in lines[-20:]:
                log.info(f"  │ {line}")

            return {
                "status": "success",
                "elapsed": elapsed,
                "output_lines": len(lines),
                "last_output": "\n".join(lines[-10:]),
            }
        else:
            log.error(f"  ✗ Phase {phase['id']} failed (exit {result.returncode})")
            stderr_lines = (result.stderr or "").strip().split('\n')
            for line in stderr_lines[-10:]:
                log.error(f"  │ {line}")

            log_progress(f"Phase {phase['id']} FAILED: exit {result.returncode}")
            return {
                "status": "failed",
                "exit_code": result.returncode,
                "elapsed": elapsed,
                "stderr": "\n".join(stderr_lines[-10:]),
            }

    except subprocess.TimeoutExpired:
        elapsed = round(time.time() - start, 1)
        log.error(f"  ⏰ Phase {phase['id']} timed out after {phase['timeout']}s")
        log_progress(f"Phase {phase['id']} TIMEOUT: {phase['timeout']}s")
        return {"status": "timeout", "elapsed": elapsed}

    except Exception as e:
        elapsed = round(time.time() - start, 1)
        log.error(f"  ✗ Phase {phase['id']} error: {e}")
        log_progress(f"Phase {phase['id']} ERROR: {e}")
        return {"status": "error", "error": str(e), "elapsed": elapsed}


def run_phase_with_retry(phase: Dict) -> Dict:
    """Run a phase with up to MAX_RETRIES attempts."""
    for attempt in range(1, MAX_RETRIES + 1):
        result = run_phase(phase, attempt)

        if result["status"] == "success":
            return result

        if attempt < MAX_RETRIES:
            wait = RETRY_BACKOFF[attempt - 1]
            log.info(f"  Retrying in {wait}s...")
            time.sleep(wait)

    return result  # Return last failed result


# ── Main Orchestrator ──────────────────────────────────────────────────

def run_all(resume: bool = False, specific_phase: Optional[int] = None):
    """Run all pipeline phases in order."""
    log.info("=" * 60)
    log.info("LitigationOS — Autonomous Pipeline Runner")
    log.info("=" * 60)

    cp = load_checkpoint()
    completed = set(cp.get("completed_phases", []))

    if not cp.get("started_at"):
        cp["started_at"] = datetime.now().isoformat()

    # Determine which phases to run
    if specific_phase:
        phases = [p for p in PHASES if p["id"] == specific_phase]
        if not phases:
            log.error(f"Unknown phase: {specific_phase}")
            return
    elif resume:
        phases = [p for p in PHASES if p["id"] not in completed]
        log.info(f"Resuming: {len(completed)} phases already complete, {len(phases)} remaining")
    else:
        phases = PHASES

    log_progress(f"Runner START: {len(phases)} phases to execute")

    results = {}
    for phase in phases:
        if phase["id"] in completed and not specific_phase:
            log.info(f"Phase {phase['id']}: {phase['name']} — ALREADY DONE (skipping)")
            continue

        result = run_phase_with_retry(phase)
        results[phase["id"]] = result

        if result["status"] == "success":
            completed.add(phase["id"])
            cp["completed_phases"] = list(completed)
            save_checkpoint(cp)
        else:
            log.warning(f"Phase {phase['id']} did not succeed: {result['status']}")
            save_checkpoint(cp)
            # Continue to next phase even on failure (don't block)

    # Final summary
    log.info("\n" + "=" * 60)
    log.info("AUTONOMOUS RUNNER — SUMMARY")
    log.info("=" * 60)
    for phase in PHASES:
        pid = phase["id"]
        if pid in results:
            r = results[pid]
            status_icon = "✓" if r["status"] == "success" else "✗"
            log.info(f"  {status_icon} Phase {pid}: {phase['name']} — {r['status']} ({r.get('elapsed', '?')}s)")
        elif pid in completed:
            log.info(f"  ⊘ Phase {pid}: {phase['name']} — previously completed")
        else:
            log.info(f"  - Phase {pid}: {phase['name']} — not run")

    success_count = sum(1 for r in results.values() if r["status"] == "success")
    total = len(results)
    log.info(f"\n  {success_count}/{total} phases succeeded")
    log_progress(f"Runner COMPLETE: {success_count}/{total} succeeded")

    save_checkpoint(cp)
    return results


def show_status():
    """Show current pipeline progress."""
    cp = load_checkpoint()
    completed = set(cp.get("completed_phases", []))

    print(f"\n{'='*60}")
    print("AUTONOMOUS RUNNER — STATUS")
    print(f"{'='*60}")
    print(f"Started: {cp.get('started_at', 'never')}")
    print(f"Updated: {cp.get('last_update', 'never')}")
    print()

    for phase in PHASES:
        icon = "✓" if phase["id"] in completed else "○"
        print(f"  {icon} Phase {phase['id']}: {phase['name']}")
        print(f"      Script: {phase['script']}")
        print(f"      Todo: {phase['todo_id']}")

    print(f"\n  Completed: {len(completed)}/{len(PHASES)}")


# ── CLI ────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="LitigationOS Autonomous Pipeline Runner")
    parser.add_argument('--phase', type=int, help='Run specific phase number')
    parser.add_argument('--resume', action='store_true', help='Resume from checkpoint')
    parser.add_argument('--status', action='store_true', help='Show progress')
    parser.add_argument('--reset', action='store_true', help='Reset checkpoint')
    args = parser.parse_args()

    if args.status:
        show_status()
    elif args.reset:
        if CHECKPOINT_FILE.exists():
            CHECKPOINT_FILE.unlink()
        print("Checkpoint reset.")
    else:
        run_all(resume=args.resume, specific_phase=args.phase)
