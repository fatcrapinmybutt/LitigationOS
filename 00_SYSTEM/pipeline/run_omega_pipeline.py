"""
OMEGA Master Orchestrator: run_omega_pipeline.py
Executes all pipeline phases in order, respecting checkpoints.
Handles Ctrl+C gracefully, supports --start-phase / --end-phase / --skip-phases.
"""
import importlib
import json
import signal
import sys
import time
from datetime import datetime
from pathlib import Path

# Ensure tooling/ is importable
TOOLING_DIR = Path(__file__).resolve().parent
if str(TOOLING_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLING_DIR))

from config import (
    PHASES, MASTER_ROOT, BACKUPS_DIR, get_cyclepack_dir, CYCLE_TS,
)
from safety import (
    create_snapshot, verify_snapshot_exists, is_phase_done,
    write_phase_checkpoint,
)
try:
    from failsafe import safe_call, FailsafePhaseRunner, _log_incident, get_robust_connection
except ImportError:
    def safe_call(fn, *a, timeout_s=30, fallback=None, **kw): return fn(*a, **kw)
    _log_incident = lambda *a, **kw: None
    get_robust_connection = None

_CENTRAL_DB = Path('C:/Users/andre/LitigationOS/litigation_context.db')


def _log_phase_to_db(run_id: str, started_at: str, status: str,
                     completed_phases: list, total_files: int = 0):
    """Log pipeline progress to the central litigation_context.db."""
    try:
        import sqlite3 as _sql
        db = _sql.connect(str(_CENTRAL_DB), timeout=120)
        db.execute('PRAGMA journal_mode=WAL')
        db.execute('''CREATE TABLE IF NOT EXISTS pipeline_runs (
            run_id TEXT PRIMARY KEY,
            started_at TEXT NOT NULL,
            finished_at TEXT,
            status TEXT,
            phases_completed TEXT,
            total_files_processed INTEGER,
            total_errors INTEGER,
            config_snapshot TEXT
        )''')
        db.execute('''INSERT OR REPLACE INTO pipeline_runs
            (run_id, started_at, status, phases_completed, total_files_processed)
            VALUES (?, ?, ?, ?, ?)''',
            (run_id, started_at, status, json.dumps(completed_phases),
             total_files))
        db.commit()
        db.close()
    except Exception as e:
        print(f"[WARN] Could not update pipeline_runs: {e}", file=sys.stderr)

# ── Phase module → run function mapping ─────────────────────────────
PHASE_RUNNERS: dict[str, tuple[str, str]] = {
    "phase0_5_drive_ingest":    ("phase0_5_drive_ingest",    "run_drive_ingest"),
    "phase1_inventory":         ("phase1_inventory",         "run_inventory"),
    "phase2_dedup":             ("phase2_dedup",             "run_dedup"),
    "phase3_classify":          ("phase3_classify",          "run_classify"),
    "phase4a_pdf_extract":      ("phase4a_pdf_extract",      "run_pdf_extract"),
    "phase4b_docx_extract":     ("phase4b_docx_extract",     "run_docx_extract"),
    "phase4c_structured_extract":("phase4c_structured_extract","run_structured_extract"),
    "phase4d_atomize":          ("phase4d_atomize",          "run_atomize"),
    "phase4e_archive_extract":  ("phase4e_archive_extract",  "run_archive_extract"),
    "phase5_brain_feed":        ("phase5_brain_feed",        "run_brain_feed"),
    "phase6_gap_analysis":      ("phase6_gap_analysis",      "run_gap_analysis"),
    "phase7a_graph_delta":      ("phase7a_graph_delta",      "run_graph_delta"),
    "phase7b_synthesis_merge":  ("phase7b_synthesis_merge",  "run_synthesis_merge"),
    "phase7c_knowledge_merge":  ("phase7c_knowledge_merge",  "run_knowledge_merge"),
    "phase8_litigation_refresh": ("phase8_litigation_refresh","run_litigation_refresh"),
    "phase9_mcp_ingest":        ("phase9_mcp_ingest",        "run_mcp_ingest"),
    "phase10_judicial_analysis": ("phase10_judicial_analysis","run_judicial_analysis"),
    "phase11_legal_action_discovery": ("phase11_legal_action_discovery", "run_legal_action_discovery"),
    "phase12_rule_audit":       ("phase12_rule_audit",       "run_rule_audit"),
    "phase13_refinement":       ("phase13_refinement",       "run_refinement"),
    "phase14_finalize":         ("phase14_finalize",         "run_finalize"),
    "phase15_validation":       ("phase15_validation",       "run_validation"),
    "phase16_desktop":          ("phase16_desktop",          "run_desktop_offload"),
}

# ── Graceful shutdown ───────────────────────────────────────────────
_interrupted = False
_current_phase = None
_cycle_dir_global = None


def _handle_sigint(signum, frame):
    global _interrupted
    _interrupted = True
    print("\n[OMEGA] Ctrl+C received — finishing current phase then stopping...", file=sys.stderr)
    if _cycle_dir_global and _current_phase:
        try:
            write_phase_checkpoint(_cycle_dir_global, f"{_current_phase}_partial", {
                "status": "interrupted",
                "interrupted_at": datetime.now().isoformat(),
            })
            cleanup_marker = _cycle_dir_global / "CLEANUP_NEEDED.marker"
            cleanup_marker.write_text(json.dumps({
                "interrupted_phase": _current_phase,
                "timestamp": datetime.now().isoformat(),
            }), encoding="utf-8")
        except Exception as e:
            print(f"[OMEGA] Warning in signal handler: {e}", file=sys.stderr)


signal.signal(signal.SIGINT, _handle_sigint)


# ── Progress dashboard ──────────────────────────────────────────────
def _print_dashboard(phases_list: list[tuple], results: dict[str, dict], elapsed_total: float):
    width = 70
    print(f"\n{'=' * width}", file=sys.stderr)
    print(f"  OMEGA PIPELINE DASHBOARD", file=sys.stderr)
    print(f"{'=' * width}", file=sys.stderr)
    cumulative = 0.0
    for phase_id, module_name, label in phases_list:
        result = results.get(phase_id, {})
        status = result.get("status", "pending")
        elapsed = result.get("elapsed", "")
        icon = {"done": "✓", "skip": "»", "error": "✗", "pending": "·"}.get(status, "?")
        # Accumulate numeric elapsed times for cumulative display
        phase_secs = 0.0
        if elapsed and elapsed not in ("", "checkpoint", "no_runner"):
            try:
                phase_secs = float(elapsed.rstrip("s"))
            except ValueError:
                pass
        cumulative += phase_secs
        elapsed_str = f" ({elapsed})" if elapsed else ""
        cumul_str = f" [{cumulative:.0f}s]" if cumulative > 0 else ""
        print(f"  {icon} Phase {phase_id:>3s} │ {label:<30s} │ {status:<8s}{elapsed_str}{cumul_str}", file=sys.stderr)
    print(f"{'─' * width}", file=sys.stderr)
    print(f"  Total elapsed: {elapsed_total:.0f}s", file=sys.stderr)
    print(f"{'=' * width}\n", file=sys.stderr)


# ── Main orchestrator ───────────────────────────────────────────────
def run_pipeline(
    cycle_ts: str,
    dry_run: bool = False,
    start_phase: str | None = None,
    end_phase: str | None = None,
    skip_phases: set[str] | None = None,
    create_snap: bool = False,
):
    global _current_phase, _cycle_dir_global

    cycle_dir = get_cyclepack_dir(cycle_ts)
    cycle_dir.mkdir(parents=True, exist_ok=True)
    _cycle_dir_global = cycle_dir

    print(f"[OMEGA] Cycle: {cycle_ts}", file=sys.stderr)
    print(f"[OMEGA] Cycle dir: {cycle_dir}", file=sys.stderr)
    print(f"[OMEGA] Dry run: {dry_run}", file=sys.stderr)

    # Snapshot handling
    snap_dir = BACKUPS_DIR / f"SNAPSHOT_{cycle_ts}"
    if dry_run:
        print("[OMEGA] DRY RUN — skipping snapshot verification", file=sys.stderr)
    elif create_snap:
        print("[OMEGA] Creating safety snapshot...", file=sys.stderr)
        create_snapshot(cycle_ts)
    else:
        if not verify_snapshot_exists(snap_dir):
            found = False
            if BACKUPS_DIR.exists():
                snaps = sorted(BACKUPS_DIR.glob("SNAPSHOT_*"), reverse=True)
                for s in snaps:
                    if verify_snapshot_exists(s):
                        print(f"[OMEGA] Using existing snapshot: {s.name}", file=sys.stderr)
                        found = True
                        break
            if not found:
                print("[OMEGA] No snapshot found. Use --create-snapshot or run safety.py first.",
                      file=sys.stderr)
                if dry_run:
                    print("[OMEGA] DRY RUN: would need snapshot — continuing anyway", file=sys.stderr)
                else:
                    sys.exit(1)

    # Determine phase range
    phase_ids = [p[0] for p in PHASES]
    start_idx = 0
    end_idx = len(PHASES) - 1

    if start_phase:
        if start_phase in phase_ids:
            start_idx = phase_ids.index(start_phase)
        else:
            print(f"[OMEGA] Unknown --start-phase '{start_phase}'", file=sys.stderr)
            sys.exit(1)

    if end_phase:
        if end_phase in phase_ids:
            end_idx = phase_ids.index(end_phase)
        else:
            print(f"[OMEGA] Unknown --end-phase '{end_phase}'", file=sys.stderr)
            sys.exit(1)

    skip = skip_phases or set()
    active_phases = PHASES[start_idx:end_idx + 1]
    results: dict[str, dict] = {}
    pipeline_start = time.time()
    run_id = f"omega_{cycle_ts}"
    started_at = datetime.now().isoformat()
    completed_phases: list[str] = []

    for phase_id, module_name, label in active_phases:
        if _interrupted:
            results[phase_id] = {"status": "skip", "elapsed": ""}
            continue

        if phase_id in skip:
            print(f"[OMEGA] Skipping phase {phase_id} ({label})", file=sys.stderr)
            results[phase_id] = {"status": "skip", "elapsed": ""}
            continue

        # Skip safety phase (handled above)
        if module_name == "safety":
            results[phase_id] = {"status": "done", "elapsed": "0s"}
            continue

        # Check checkpoint
        cp_name = module_name.replace("phase", "phase").split("_", 1)
        # Use the standard checkpoint name pattern
        checkpoint_name = module_name
        # Try common checkpoint naming: phase1, phase2, phase4d, etc.
        if phase_id.isdigit() or (len(phase_id) <= 3):
            checkpoint_name = f"phase{phase_id}"

        if is_phase_done(cycle_dir, checkpoint_name):
            print(f"[OMEGA] Phase {phase_id} ({label}) already done, skipping", file=sys.stderr)
            results[phase_id] = {"status": "done", "elapsed": "checkpoint"}
            continue

        # Resolve runner
        runner_info = PHASE_RUNNERS.get(module_name)
        if not runner_info:
            print(f"[OMEGA] No runner for {module_name}, skipping", file=sys.stderr)
            results[phase_id] = {"status": "skip", "elapsed": "no_runner"}
            continue

        mod_name, func_name = runner_info
        _current_phase = phase_id
        phase_start = time.time()

        try:
            # Failsafe: import with 30s timeout (blocks from config.py etc. are caught)
            mod = safe_call(importlib.import_module, mod_name, timeout_s=30, fallback=None)
            if mod is None:
                print(f"[OMEGA] Phase {phase_id} import timed out or failed — SKIPPING (pipeline continues)", file=sys.stderr)
                results[phase_id] = {"status": "error", "elapsed": f"{time.time() - phase_start:.0f}s"}
                _print_dashboard(active_phases, results, time.time() - pipeline_start)
                continue
            runner = getattr(mod, func_name)
            print(f"\n[OMEGA] ▶ Phase {phase_id}: {label}", file=sys.stderr)
            # Failsafe: run phase with 600s timeout (10 min max per phase)
            phase_result = safe_call(runner, cycle_dir, dry_run, timeout_s=600, fallback="__TIMEOUT__")
            phase_elapsed = time.time() - phase_start
            if phase_result == "__TIMEOUT__":
                print(f"[OMEGA] Phase {phase_id} TIMED OUT after 600s — SKIPPING (pipeline continues)", file=sys.stderr)
                results[phase_id] = {"status": "timeout", "elapsed": f"{phase_elapsed:.0f}s"}
            else:
                results[phase_id] = {"status": "done", "elapsed": f"{phase_elapsed:.0f}s"}
                completed_phases.append(phase_id)
                _log_phase_to_db(run_id, started_at, 'running', completed_phases)
        except SystemExit:
            print(f"[OMEGA] Phase {phase_id} exited (missing prerequisite in dry-run?)", file=sys.stderr)
            results[phase_id] = {"status": "skip", "elapsed": f"{time.time() - phase_start:.0f}s"}
        except ImportError as e:
            print(f"[OMEGA] Phase {phase_id} import error: {e}", file=sys.stderr)
            results[phase_id] = {"status": "error", "elapsed": f"{time.time() - phase_start:.0f}s"}
        except Exception as e:
            print(f"[OMEGA] Phase {phase_id} error: {e} — pipeline continues", file=sys.stderr)
            results[phase_id] = {"status": "error", "elapsed": f"{time.time() - phase_start:.0f}s"}

        _print_dashboard(active_phases, results, time.time() - pipeline_start)

    # Final validation
    if not _interrupted and not dry_run:
        try:
            from validate import validate
            snap_name = f"SNAPSHOT_{cycle_ts}"
            if (BACKUPS_DIR / snap_name).exists():
                print("\n[OMEGA] Running final validation...", file=sys.stderr)
                report = validate(snap_name)
                print(f"[OMEGA] Validation result: {report.get('status', 'UNKNOWN')}", file=sys.stderr)
        except Exception as e:
            print(f"[OMEGA] Validation error: {e}", file=sys.stderr)

    total_elapsed = time.time() - pipeline_start

    # Log final status to central DB
    final_status = 'interrupted' if _interrupted else 'complete'
    _log_phase_to_db(run_id, started_at, final_status, completed_phases)

    # Write pipeline summary
    if not dry_run:
        summary = {
            "cycle_ts": cycle_ts,
            "cycle_dir": str(cycle_dir),
            "total_elapsed_seconds": round(total_elapsed, 1),
            "interrupted": _interrupted,
            "phases": results,
            "completed_at": datetime.now().isoformat(),
        }
        (cycle_dir / "pipeline_summary.json").write_text(
            json.dumps(summary, indent=2), encoding="utf-8",
        )

    _print_dashboard(active_phases, results, total_elapsed)
    print(f"[OMEGA] Pipeline {'INTERRUPTED' if _interrupted else 'COMPLETE'} in {total_elapsed:.0f}s",
          file=sys.stderr)


def show_status():
    """Print status of the most recent pipeline cycle."""
    cyclepacks = MASTER_ROOT / "cyclepacks"
    if not cyclepacks.exists():
        print("No cycles found")
        return
    cycles = sorted([d for d in cyclepacks.iterdir() if d.is_dir() and d.name.startswith("CYCLE_")], reverse=True)
    if not cycles:
        print("No cycles found")
        return
    latest = cycles[0]
    print(f"Latest cycle: {latest.name}")
    # Read checkpoints
    cp_dir = latest / "checkpoints"
    if cp_dir.exists():
        for cp in sorted(cp_dir.glob("*_complete.json")):
            try:
                data = json.loads(cp.read_text(encoding="utf-8"))
                print(f"  {cp.stem}: {data.get('status', '?')} ({data.get('elapsed', '')})")
            except (json.JSONDecodeError, OSError):
                print(f"  {cp.stem}: <unreadable>")
    else:
        print("  No checkpoints yet")
    # Read summary
    summary = latest / "pipeline_summary.json"
    if summary.exists():
        try:
            data = json.loads(summary.read_text(encoding="utf-8"))
            print(f"  Total elapsed: {data.get('total_elapsed_seconds', 0):.0f}s")
            print(f"  Interrupted: {data.get('interrupted', False)}")
        except (json.JSONDecodeError, OSError):
            print("  Summary: <unreadable>")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="OMEGA Master Pipeline Orchestrator")
    parser.add_argument("--cycle-ts", default=CYCLE_TS,
                        help="Cycle timestamp (default: current time)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Run without writing any files")
    parser.add_argument("--start-phase", default=None,
                        help="Phase ID to start from (e.g., '4d', '12')")
    parser.add_argument("--end-phase", default=None,
                        help="Phase ID to stop after (e.g., '7c', '16')")
    parser.add_argument("--skip-phases", default=None,
                        help="Comma-separated phase IDs to skip (e.g., '4e,9')")
    parser.add_argument("--create-snapshot", action="store_true",
                        help="Create safety snapshot before running")
    parser.add_argument("--list-phases", action="store_true",
                        help="List all available phases and exit")
    parser.add_argument("--status", action="store_true",
                        help="Show status of the most recent cycle and exit")
    args = parser.parse_args()

    if args.status:
        show_status()
        sys.exit(0)

    if args.list_phases:
        print("Available OMEGA pipeline phases:")
        print(f"  {'ID':<6s}  {'Module':<35s}  Label")
        print(f"  {'─'*6}  {'─'*35}  {'─'*30}")
        for phase_id, module_name, label in PHASES:
            runner = "✓" if module_name in PHASE_RUNNERS else "–"
            print(f"  {phase_id:<6s}  {module_name:<35s}  {label}  [{runner}]")
        sys.exit(0)

    skip = set()
    if args.skip_phases:
        skip = {s.strip() for s in args.skip_phases.split(",")}

    run_pipeline(
        cycle_ts=args.cycle_ts,
        dry_run=args.dry_run,
        start_phase=args.start_phase,
        end_phase=args.end_phase,
        skip_phases=skip,
        create_snap=args.create_snapshot,
    )
