"""
OMEGA Async Pipeline Orchestrator: async_pipeline.py
DAG-aware parallel scheduler that replaces sequential phase execution.

Phases with independent dependencies run concurrently (e.g., 4a-4e).
CPU-heavy extraction phases use ProcessPoolExecutor to bypass the GIL.
All DB access uses WAL mode with busy_timeout for safe concurrent reads.

Usage:
    python async_pipeline.py run                     # Full pipeline
    python async_pipeline.py run --start phase3      # Start from phase3
    python async_pipeline.py run --skip phase4e      # Skip a phase
    python async_pipeline.py run --dry-run           # Show execution plan
    python async_pipeline.py run --max-workers 6     # Override parallelism
    python async_pipeline.py dag                     # Show DAG visualization
    python async_pipeline.py status                  # Show last run status
"""
import asyncio
import importlib
import json
import signal
import sqlite3
import sys
import time
import uuid
from collections import defaultdict, deque
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Any

# UTF-8 stdout safety (Windows)
sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", errors="replace")
sys.stderr = open(sys.stderr.fileno(), mode="w", encoding="utf-8", errors="replace")

# Ensure pipeline dir is importable
_PIPELINE_DIR = Path(__file__).resolve().parent
if str(_PIPELINE_DIR) not in sys.path:
    sys.path.insert(0, str(_PIPELINE_DIR))

from config import (
    PHASES, MASTER_ROOT, BACKUPS_DIR, get_cyclepack_dir, CYCLE_TS, LITIGOS_ROOT,
)
from safety import (
    create_snapshot, verify_snapshot_exists, is_phase_done,
    write_phase_checkpoint,
)

_CENTRAL_DB = Path("C:/Users/andre/LitigationOS/litigation_context.db")

# ── DB PRAGMAs (applied to every connection) ────────────────────────
_DB_PRAGMAS = [
    "PRAGMA busy_timeout = 180000",
    "PRAGMA journal_mode = WAL",
    "PRAGMA mmap_size = 12884901888",
    "PRAGMA cache_size = -131072",
    "PRAGMA temp_store = MEMORY",
    "PRAGMA synchronous = NORMAL",
]


def _get_db_connection(db_path: Path | str | None = None) -> sqlite3.Connection:
    """Open a SQLite connection with all required PRAGMAs applied."""
    path = str(db_path or _CENTRAL_DB)
    conn = sqlite3.connect(path, timeout=180)
    for pragma in _DB_PRAGMAS:
        conn.execute(pragma)
    return conn


# ── Phase Runner Registry (module_name → (import_name, function_name)) ──
PHASE_RUNNERS: dict[str, tuple[str, str]] = {
    "phase0_5_drive_ingest":          ("phase0_5_drive_ingest",          "run_drive_ingest"),
    "phase1_inventory":               ("phase1_inventory",               "run_inventory"),
    "phase2_dedup":                   ("phase2_dedup",                   "run_dedup"),
    "phase3_classify":                ("phase3_classify",                "run_classify"),
    "phase4a_pdf_extract":            ("phase4a_pdf_extract",            "run_pdf_extract"),
    "phase4b_docx_extract":           ("phase4b_docx_extract",           "run_docx_extract"),
    "phase4c_structured_extract":     ("phase4c_structured_extract",     "run_structured_extract"),
    "phase4d_atomize":                ("phase4d_atomize",                "run_atomize"),
    "phase4e_archive_extract":        ("phase4e_archive_extract",        "run_archive_extract"),
    "phase5_brain_feed":              ("phase5_brain_feed",              "run_brain_feed"),
    "phase6_gap_analysis":            ("phase6_gap_analysis",            "run_gap_analysis"),
    "phase7a_graph_delta":            ("phase7a_graph_delta",            "run_graph_delta"),
    "phase7b_synthesis_merge":        ("phase7b_synthesis_merge",        "run_synthesis_merge"),
    "phase7c_knowledge_merge":        ("phase7c_knowledge_merge",        "run_knowledge_merge"),
    "phase8_litigation_refresh":      ("phase8_litigation_refresh",      "run_litigation_refresh"),
    "phase9_mcp_ingest":              ("phase9_mcp_ingest",              "run_mcp_ingest"),
    "phase10_judicial_analysis":      ("phase10_judicial_analysis",      "run_judicial_analysis"),
    "phase11_legal_action_discovery": ("phase11_legal_action_discovery", "run_legal_action_discovery"),
    "phase12_rule_audit":             ("phase12_rule_audit",             "run_rule_audit"),
    "phase13_refinement":             ("phase13_refinement",             "run_refinement"),
    "phase14_finalize":               ("phase14_finalize",               "run_finalize"),
    "phase15_validation":             ("phase15_validation",             "run_validation"),
    "phase16_desktop":                ("phase16_desktop",                "run_desktop_offload"),
}

# ── Phase DAG ───────────────────────────────────────────────────────
# Dependencies are derived from the actual pipeline data flow.
# Phases 4a-4e are independent extraction phases that run in parallel.
# Phase 4d (atomize) depends only on phase3 (not on other 4x phases).
# Phase 5 requires ALL extraction phases to complete.
PHASE_DAG: dict[str, dict[str, Any]] = {
    "0":   {"deps": [],                                 "module": "safety",                        "label": "Safety Snapshot"},
    "0.5": {"deps": ["0"],                              "module": "phase0_5_drive_ingest",         "label": "Drive Ingestion"},
    "1":   {"deps": ["0.5"],                            "module": "phase1_inventory",              "label": "Recursive Inventory"},
    "2":   {"deps": ["1"],                              "module": "phase2_dedup",                  "label": "Hash-Cluster Dedup"},
    "3":   {"deps": ["2"],                              "module": "phase3_classify",               "label": "3-Pass Classification"},
    "4a":  {"deps": ["3"],                              "module": "phase4a_pdf_extract",           "label": "PDF Extraction"},
    "4b":  {"deps": ["3"],                              "module": "phase4b_docx_extract",          "label": "DOCX Extraction"},
    "4c":  {"deps": ["3"],                              "module": "phase4c_structured_extract",    "label": "Structured Data"},
    "4d":  {"deps": ["3"],                              "module": "phase4d_atomize",               "label": "Atom Generation"},
    "4e":  {"deps": ["3"],                              "module": "phase4e_archive_extract",       "label": "Archive Extraction"},
    "5":   {"deps": ["4a", "4b", "4c", "4d", "4e"],    "module": "phase5_brain_feed",             "label": "LEXOS Brain Feed"},
    "6":   {"deps": ["5"],                              "module": "phase6_gap_analysis",           "label": "EGCP Gap Analysis"},
    "7a":  {"deps": ["6"],                              "module": "phase7a_graph_delta",           "label": "Graph Delta"},
    "7b":  {"deps": ["7a"],                             "module": "phase7b_synthesis_merge",       "label": "Synthesis Merge"},
    "7c":  {"deps": ["7b"],                             "module": "phase7c_knowledge_merge",       "label": "Knowledge Merge"},
    "8":   {"deps": ["7c"],                             "module": "phase8_litigation_refresh",     "label": "Litigation Refresh"},
    "9":   {"deps": ["8"],                              "module": "phase9_mcp_ingest",             "label": "MCP Ingest"},
    "10":  {"deps": ["9"],                              "module": "phase10_judicial_analysis",     "label": "Judicial Analysis"},
    "11":  {"deps": ["10"],                             "module": "phase11_legal_action_discovery","label": "Legal Action Discovery"},
    "12":  {"deps": ["11"],                             "module": "phase12_rule_audit",            "label": "MCR/MCL Rule Audit"},
    "13":  {"deps": ["12"],                             "module": "phase13_refinement",            "label": "Document Refinement"},
    "14":  {"deps": ["13"],                             "module": "phase14_finalize",              "label": "Filing Finalization"},
    "15":  {"deps": ["14"],                             "module": "phase15_validation",            "label": "Court-Ready Validation"},
    "16":  {"deps": ["15"],                             "module": "phase16_desktop",               "label": "Desktop Offload"},
}

# Phases that benefit from ProcessPoolExecutor (CPU-heavy extraction)
_CPU_PHASES = {"4a", "4b", "4c", "4d", "4e"}


# ── Phase Run Table (per-phase granularity) ─────────────────────────
_PHASE_RUNS_DDL = """
CREATE TABLE IF NOT EXISTS async_pipeline_runs (
    run_id          TEXT    NOT NULL,
    phase_id        TEXT    NOT NULL,
    status          TEXT    NOT NULL DEFAULT 'pending',
    start_time      REAL,
    end_time        REAL,
    duration_seconds REAL,
    error_message   TEXT,
    rows_processed  INTEGER DEFAULT 0,
    PRIMARY KEY (run_id, phase_id)
)
"""


def _ensure_phase_runs_table(conn: sqlite3.Connection) -> None:
    conn.execute(_PHASE_RUNS_DDL)
    conn.commit()


def _log_phase_run(run_id: str, phase_id: str, status: str,
                   start_time: float | None = None, end_time: float | None = None,
                   error_message: str | None = None, rows_processed: int = 0) -> None:
    """Write phase-level run data to central DB."""
    duration = (end_time - start_time) if (start_time and end_time) else None
    try:
        conn = _get_db_connection()
        _ensure_phase_runs_table(conn)
        conn.execute(
            """INSERT OR REPLACE INTO async_pipeline_runs
               (run_id, phase_id, status, start_time, end_time, duration_seconds,
                error_message, rows_processed)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (run_id, phase_id, status, start_time, end_time, duration,
             error_message, rows_processed),
        )
        conn.commit()
        conn.close()
    except Exception as exc:
        print(f"[ASYNC] WARN: DB log failed for {phase_id}: {exc}", file=sys.stderr)


# ── Topological Sort ────────────────────────────────────────────────
def topological_sort(dag: dict[str, dict]) -> list[str]:
    """Kahn's algorithm — returns phases in a valid execution order."""
    in_degree: dict[str, int] = {node: 0 for node in dag}
    children: dict[str, list[str]] = defaultdict(list)
    for node, info in dag.items():
        for dep in info["deps"]:
            children[dep].append(node)
            in_degree[node] += 1

    queue: deque[str] = deque(n for n, d in in_degree.items() if d == 0)
    order: list[str] = []
    while queue:
        node = queue.popleft()
        order.append(node)
        for child in children[node]:
            in_degree[child] -= 1
            if in_degree[child] == 0:
                queue.append(child)

    if len(order) != len(dag):
        missing = set(dag) - set(order)
        raise ValueError(f"DAG has a cycle involving: {missing}")
    return order


# ── Subprocess runner for CPU phases (ProcessPoolExecutor target) ───
def _run_phase_in_subprocess(module_name: str, func_name: str,
                             cycle_dir_str: str, dry_run: bool) -> dict:
    """Executed in a child process — imports the phase module and calls its runner.
    Returns a result dict with status, elapsed, and optional error."""
    # Re-apply sys.path in the child process
    pipeline_dir = str(Path(__file__).resolve().parent)
    if pipeline_dir not in sys.path:
        sys.path.insert(0, pipeline_dir)

    start = time.monotonic()
    try:
        mod = importlib.import_module(module_name)
        runner = getattr(mod, func_name)
        result = runner(Path(cycle_dir_str), dry_run)
        elapsed = time.monotonic() - start
        return {"status": "completed", "elapsed": elapsed, "result": str(result) if result else None}
    except Exception as exc:
        elapsed = time.monotonic() - start
        return {"status": "failed", "elapsed": elapsed, "error": f"{type(exc).__name__}: {exc}"}


# ── Pipeline Result ─────────────────────────────────────────────────
class PipelineResult:
    """Aggregated result of an async pipeline run."""

    def __init__(self, run_id: str, cycle_ts: str):
        self.run_id = run_id
        self.cycle_ts = cycle_ts
        self.phase_results: dict[str, dict] = {}
        self.start_time: float = time.monotonic()
        self.end_time: float | None = None
        self.interrupted = False

    def record(self, phase_id: str, status: str, elapsed: float,
               error: str | None = None) -> None:
        self.phase_results[phase_id] = {
            "status": status,
            "elapsed_seconds": round(elapsed, 2),
            "error": error,
        }

    @property
    def total_elapsed(self) -> float:
        end = self.end_time or time.monotonic()
        return end - self.start_time

    @property
    def succeeded(self) -> list[str]:
        return [p for p, r in self.phase_results.items() if r["status"] == "completed"]

    @property
    def failed(self) -> list[str]:
        return [p for p, r in self.phase_results.items() if r["status"] == "failed"]

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "cycle_ts": self.cycle_ts,
            "total_elapsed_seconds": round(self.total_elapsed, 1),
            "interrupted": self.interrupted,
            "phases_completed": len(self.succeeded),
            "phases_failed": len(self.failed),
            "phases": self.phase_results,
            "completed_at": datetime.now().isoformat(),
        }

    def summary(self) -> str:
        lines = [
            f"Run {self.run_id}  |  {self.total_elapsed:.0f}s total",
            f"  Completed: {len(self.succeeded)}  |  Failed: {len(self.failed)}",
        ]
        if self.failed:
            lines.append(f"  Failed phases: {', '.join(self.failed)}")
        return "\n".join(lines)


# ── Async Pipeline Orchestrator ─────────────────────────────────────
class AsyncPipelineOrchestrator:
    """DAG-aware async pipeline scheduler with parallel phase execution."""

    def __init__(self, db_path: Path | str | None = None,
                 max_workers: int = 4, phase_timeout: int = 600):
        self.dag = dict(PHASE_DAG)
        self.db_path = Path(db_path) if db_path else _CENTRAL_DB
        self.max_workers = max_workers
        self.phase_timeout = phase_timeout
        # Phase execution state
        self.completed: set[str] = set()
        self.failed: set[str] = set()
        self.skipped: set[str] = set()
        self.running: set[str] = set()
        # Concurrency controls
        self._worker_sem: asyncio.Semaphore | None = None
        self._db_write_sem: asyncio.Semaphore | None = None
        self._process_pool: ProcessPoolExecutor | None = None
        # Interruption
        self._interrupted = False

    async def run(self, cycle_ts: str | None = None,
                  start_phase: str | None = None,
                  end_phase: str | None = None,
                  skip_phases: set[str] | None = None,
                  dry_run: bool = False,
                  create_snap: bool = False) -> PipelineResult:
        """Execute the pipeline with DAG-aware parallel scheduling."""
        cycle_ts = cycle_ts or CYCLE_TS
        cycle_dir = get_cyclepack_dir(cycle_ts)
        cycle_dir.mkdir(parents=True, exist_ok=True)
        run_id = f"async_{cycle_ts}_{uuid.uuid4().hex[:8]}"
        result = PipelineResult(run_id, cycle_ts)

        print(f"[ASYNC] Run ID: {run_id}", file=sys.stderr)
        print(f"[ASYNC] Cycle dir: {cycle_dir}", file=sys.stderr)
        print(f"[ASYNC] Max workers: {self.max_workers}", file=sys.stderr)
        print(f"[ASYNC] Phase timeout: {self.phase_timeout}s", file=sys.stderr)

        # Determine active phases
        active_dag = self._filter_dag(start_phase, end_phase, skip_phases or set())

        if dry_run:
            self._print_execution_plan(active_dag)
            return result

        # Snapshot handling
        if not self._handle_snapshot(cycle_ts, create_snap):
            return result

        # Initialize concurrency controls
        self._worker_sem = asyncio.Semaphore(self.max_workers)
        self._db_write_sem = asyncio.Semaphore(3)  # max 3 concurrent DB writers
        self._process_pool = ProcessPoolExecutor(max_workers=self.max_workers)

        # Register SIGINT handler
        loop = asyncio.get_running_loop()
        original_handler = signal.getsignal(signal.SIGINT)

        def _sigint_handler(sig, frame):
            self._interrupted = True
            print("\n[ASYNC] Ctrl+C — finishing running phases then stopping...",
                  file=sys.stderr)

        signal.signal(signal.SIGINT, _sigint_handler)

        try:
            await self._execute_dag(active_dag, cycle_dir, dry_run, run_id, result)
        finally:
            self._process_pool.shutdown(wait=False, cancel_futures=True)
            signal.signal(signal.SIGINT, original_handler)

        result.end_time = time.monotonic()
        result.interrupted = self._interrupted

        # Write pipeline summary
        summary_path = cycle_dir / "async_pipeline_summary.json"
        summary_path.write_text(json.dumps(result.to_dict(), indent=2), encoding="utf-8")
        self._print_dashboard(active_dag, result)
        print(f"\n[ASYNC] Pipeline {'INTERRUPTED' if self._interrupted else 'COMPLETE'} "
              f"in {result.total_elapsed:.0f}s", file=sys.stderr)

        return result

    def _filter_dag(self, start_phase: str | None, end_phase: str | None,
                    skip: set[str]) -> dict[str, dict]:
        """Return a filtered DAG based on start/end/skip parameters."""
        topo = topological_sort(self.dag)

        # Determine the valid range
        if start_phase:
            if start_phase not in self.dag:
                raise ValueError(f"Unknown start phase: {start_phase}")
            start_idx = topo.index(start_phase)
        else:
            start_idx = 0

        if end_phase:
            if end_phase not in self.dag:
                raise ValueError(f"Unknown end phase: {end_phase}")
            end_idx = topo.index(end_phase)
        else:
            end_idx = len(topo) - 1

        active_ids = set(topo[start_idx:end_idx + 1]) - skip

        # When starting from a mid-point, treat missing upstream deps as completed
        upstream = set(topo[:start_idx])
        self.completed = upstream
        self.skipped = skip & set(topo[start_idx:end_idx + 1])

        # Build filtered DAG with only the active phases
        filtered: dict[str, dict] = {}
        for pid in active_ids:
            info = dict(self.dag[pid])
            # Deps that are not in the active set are treated as already satisfied
            info["deps"] = [d for d in info["deps"] if d in active_ids]
            filtered[pid] = info
        return filtered

    async def _execute_dag(self, dag: dict[str, dict], cycle_dir: Path,
                           dry_run: bool, run_id: str,
                           result: PipelineResult) -> None:
        """Core DAG executor — launches phases as their dependencies complete."""
        pending = set(dag.keys()) - self.completed - self.skipped
        phase_events: dict[str, asyncio.Event] = {pid: asyncio.Event() for pid in dag}

        # Mark already-completed/skipped phases as done
        for pid in list(self.completed) + list(self.skipped):
            if pid in phase_events:
                phase_events[pid].set()

        async def _phase_wrapper(phase_id: str) -> None:
            """Wait for deps, then execute a single phase."""
            info = dag[phase_id]

            # Wait for all dependencies to complete
            for dep in info["deps"]:
                if dep in phase_events:
                    await phase_events[dep].wait()
                # If a dependency failed and this phase depends on it, skip
                if dep in self.failed:
                    self.skipped.add(phase_id)
                    result.record(phase_id, "skipped", 0.0,
                                  error=f"Dependency {dep} failed")
                    _log_phase_run(run_id, phase_id, "skipped",
                                   error_message=f"Dependency {dep} failed")
                    phase_events[phase_id].set()
                    pending.discard(phase_id)
                    return

            if self._interrupted:
                self.skipped.add(phase_id)
                result.record(phase_id, "skipped", 0.0, error="Interrupted")
                phase_events[phase_id].set()
                pending.discard(phase_id)
                return

            async with self._worker_sem:
                await self._run_phase(phase_id, info, cycle_dir, dry_run,
                                      run_id, result)
            phase_events[phase_id].set()
            pending.discard(phase_id)

        # Launch all phases as tasks — each waits for its own deps internally
        tasks = [asyncio.create_task(_phase_wrapper(pid), name=f"phase-{pid}")
                 for pid in dag if pid not in self.completed and pid not in self.skipped]

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _run_phase(self, phase_id: str, info: dict, cycle_dir: Path,
                         dry_run: bool, run_id: str,
                         result: PipelineResult) -> None:
        """Import and execute a single phase, with timeout and error handling."""
        module_name = info["module"]
        label = info["label"]
        self.running.add(phase_id)

        # Phase 0 (safety) is handled separately
        if module_name == "safety":
            self.completed.add(phase_id)
            self.running.discard(phase_id)
            result.record(phase_id, "completed", 0.0)
            _log_phase_run(run_id, phase_id, "completed", time.time(), time.time())
            return

        # Check checkpoint — already done?
        checkpoint_name = f"phase{phase_id}" if (phase_id.replace(".", "").isalnum() and len(phase_id) <= 3) else module_name
        if is_phase_done(cycle_dir, checkpoint_name):
            print(f"[ASYNC] Phase {phase_id} ({label}) — checkpoint found, skipping",
                  file=sys.stderr)
            self.completed.add(phase_id)
            self.running.discard(phase_id)
            result.record(phase_id, "completed", 0.0)
            _log_phase_run(run_id, phase_id, "completed", time.time(), time.time())
            return

        runner_info = PHASE_RUNNERS.get(module_name)
        if not runner_info:
            print(f"[ASYNC] No runner for phase {phase_id} ({module_name}), skipping",
                  file=sys.stderr)
            self.skipped.add(phase_id)
            self.running.discard(phase_id)
            result.record(phase_id, "skipped", 0.0, error="No runner registered")
            return

        mod_name, func_name = runner_info
        start_time = time.time()
        _log_phase_run(run_id, phase_id, "running", start_time=start_time)

        print(f"\n[ASYNC] ▶ Phase {phase_id}: {label}  (workers: {len(self.running)})",
              file=sys.stderr)

        try:
            if phase_id in _CPU_PHASES:
                # CPU-heavy: run in ProcessPoolExecutor
                phase_result = await asyncio.wait_for(
                    asyncio.get_running_loop().run_in_executor(
                        self._process_pool,
                        _run_phase_in_subprocess,
                        mod_name, func_name, str(cycle_dir), dry_run,
                    ),
                    timeout=self.phase_timeout,
                )
                elapsed = phase_result.get("elapsed", time.time() - start_time)
                if phase_result["status"] == "failed":
                    raise RuntimeError(phase_result.get("error", "Unknown subprocess error"))
            else:
                # IO / sequential: run in the event loop thread
                mod = importlib.import_module(mod_name)
                runner = getattr(mod, func_name)
                phase_result = await asyncio.wait_for(
                    asyncio.get_running_loop().run_in_executor(
                        None,  # default ThreadPoolExecutor
                        lambda: runner(cycle_dir, dry_run),
                    ),
                    timeout=self.phase_timeout,
                )
                elapsed = time.time() - start_time

            end_time = time.time()
            self.completed.add(phase_id)
            result.record(phase_id, "completed", elapsed)
            _log_phase_run(run_id, phase_id, "completed", start_time, end_time)

            # Write checkpoint
            write_phase_checkpoint(cycle_dir, checkpoint_name, {
                "status": "done",
                "elapsed": f"{elapsed:.1f}s",
                "runner": "async_pipeline",
            })
            print(f"[ASYNC] ✓ Phase {phase_id} completed in {elapsed:.1f}s",
                  file=sys.stderr)

        except asyncio.TimeoutError:
            elapsed = time.time() - start_time
            self.failed.add(phase_id)
            error_msg = f"Timed out after {self.phase_timeout}s"
            result.record(phase_id, "failed", elapsed, error=error_msg)
            _log_phase_run(run_id, phase_id, "failed", start_time, time.time(),
                           error_message=error_msg)
            print(f"[ASYNC] ✗ Phase {phase_id} TIMED OUT after {self.phase_timeout}s",
                  file=sys.stderr)

        except Exception as exc:
            elapsed = time.time() - start_time
            error_msg = f"{type(exc).__name__}: {exc}"
            self.failed.add(phase_id)
            result.record(phase_id, "failed", elapsed, error=error_msg)
            _log_phase_run(run_id, phase_id, "failed", start_time, time.time(),
                           error_message=error_msg)
            print(f"[ASYNC] ✗ Phase {phase_id} FAILED: {error_msg}",
                  file=sys.stderr)

        finally:
            self.running.discard(phase_id)

    def get_ready_phases(self) -> list[str]:
        """Return phases whose deps are all completed and not yet running/done."""
        ready = []
        for pid, info in self.dag.items():
            if pid in self.completed or pid in self.failed or pid in self.running or pid in self.skipped:
                continue
            if all(d in self.completed for d in info["deps"]):
                ready.append(pid)
        return ready

    # ── Snapshot Handling ───────────────────────────────────────────
    def _handle_snapshot(self, cycle_ts: str, create_snap: bool) -> bool:
        """Verify or create a safety snapshot. Returns False if we must abort."""
        snap_dir = BACKUPS_DIR / f"SNAPSHOT_{cycle_ts}"
        if create_snap:
            print("[ASYNC] Creating safety snapshot...", file=sys.stderr)
            create_snapshot(cycle_ts)
            return True

        if verify_snapshot_exists(snap_dir):
            return True

        # Try to find any existing snapshot
        if BACKUPS_DIR.exists():
            for s in sorted(BACKUPS_DIR.glob("SNAPSHOT_*"), reverse=True):
                if verify_snapshot_exists(s):
                    print(f"[ASYNC] Using existing snapshot: {s.name}", file=sys.stderr)
                    return True

        print("[ASYNC] No snapshot found. Use --create-snapshot or run safety.py first.",
              file=sys.stderr)
        return False

    # ── Dry-Run Execution Plan ──────────────────────────────────────
    def _print_execution_plan(self, dag: dict[str, dict]) -> None:
        """Print the execution plan showing parallelism opportunities."""
        topo = topological_sort(dag)
        # Build wave-based schedule (phases at the same depth run together)
        depth: dict[str, int] = {}
        for pid in topo:
            dep_depths = [depth[d] for d in dag[pid]["deps"] if d in depth]
            depth[pid] = (max(dep_depths) + 1) if dep_depths else 0

        waves: dict[int, list[str]] = defaultdict(list)
        for pid, d in depth.items():
            waves[d].append(pid)

        print(f"\n{'=' * 70}", file=sys.stderr)
        print("  ASYNC PIPELINE — EXECUTION PLAN (DRY RUN)", file=sys.stderr)
        print(f"{'=' * 70}", file=sys.stderr)
        for wave_num in sorted(waves):
            phases = waves[wave_num]
            parallel_tag = " [PARALLEL]" if len(phases) > 1 else ""
            executor_tags = []
            for pid in phases:
                tag = "CPU" if pid in _CPU_PHASES else "IO"
                label = dag[pid]["label"]
                executor_tags.append(f"    {pid:>4s} │ {label:<30s} │ {tag}")
            print(f"\n  Wave {wave_num}{parallel_tag}:", file=sys.stderr)
            for line in executor_tags:
                print(line, file=sys.stderr)

        total_waves = len(waves)
        total_phases = len(dag)
        max_parallel = max(len(v) for v in waves.values()) if waves else 0
        print(f"\n{'─' * 70}", file=sys.stderr)
        print(f"  {total_phases} phases in {total_waves} waves  |  "
              f"Max parallelism: {max_parallel}  |  Workers: {self.max_workers}",
              file=sys.stderr)
        print(f"{'=' * 70}\n", file=sys.stderr)

    # ── Dashboard ───────────────────────────────────────────────────
    def _print_dashboard(self, dag: dict[str, dict], result: PipelineResult) -> None:
        """Print a summary dashboard after pipeline completion."""
        topo = topological_sort(dag)
        width = 74
        print(f"\n{'=' * width}", file=sys.stderr)
        print("  ASYNC PIPELINE DASHBOARD", file=sys.stderr)
        print(f"{'=' * width}", file=sys.stderr)
        for pid in topo:
            pr = result.phase_results.get(pid, {"status": "pending", "elapsed_seconds": 0})
            status = pr["status"]
            elapsed = pr["elapsed_seconds"]
            icon = {"completed": "✓", "failed": "✗", "skipped": "»", "pending": "·"}.get(status, "?")
            label = dag[pid]["label"]
            elapsed_str = f"{elapsed:.1f}s" if elapsed > 0 else ""
            err_str = ""
            if pr.get("error"):
                err_str = f"  [{pr['error'][:40]}]"
            print(f"  {icon} Phase {pid:>4s} │ {label:<30s} │ {status:<10s} {elapsed_str}{err_str}",
                  file=sys.stderr)
        print(f"{'─' * width}", file=sys.stderr)
        print(f"  Total: {result.total_elapsed:.0f}s  |  "
              f"OK: {len(result.succeeded)}  |  "
              f"Failed: {len(result.failed)}  |  "
              f"Interrupted: {result.interrupted}", file=sys.stderr)
        print(f"{'=' * width}\n", file=sys.stderr)

    # ── DAG Visualization ───────────────────────────────────────────
    @staticmethod
    def visualize_dag() -> str:
        """Return a Mermaid diagram of the phase DAG."""
        lines = ["graph TD"]
        for pid, info in PHASE_DAG.items():
            safe_id = pid.replace(".", "_")
            label = info["label"]
            lines.append(f'    {safe_id}["{pid}: {label}"]')
        lines.append("")
        for pid, info in PHASE_DAG.items():
            safe_id = pid.replace(".", "_")
            for dep in info["deps"]:
                safe_dep = dep.replace(".", "_")
                lines.append(f"    {safe_dep} --> {safe_id}")

        # Also produce a compact ASCII representation
        lines.append("")
        lines.append("%% ASCII Summary:")
        lines.append("%% 0 → 0.5 → 1 → 2 → 3 ─┬─ 4a ─┐")
        lines.append("%%                        ├─ 4b ─┤")
        lines.append("%%                        ├─ 4c ─┼─ 5 → 6 → 7a → 7b → 7c")
        lines.append("%%                        ├─ 4d ─┤")
        lines.append("%%                        └─ 4e ─┘")
        lines.append("%%   → 8 → 9 → 10 → 11 → 12 → 13 → 14 → 15 → 16")
        return "\n".join(lines)


# ── Status Reporter ─────────────────────────────────────────────────
def show_status() -> None:
    """Print status of the most recent async pipeline run from the DB."""
    try:
        conn = _get_db_connection()
        _ensure_phase_runs_table(conn)
        rows = conn.execute(
            """SELECT run_id, phase_id, status, duration_seconds, error_message
               FROM async_pipeline_runs
               WHERE run_id = (SELECT run_id FROM async_pipeline_runs
                               ORDER BY start_time DESC LIMIT 1)
               ORDER BY start_time""",
        ).fetchall()
        conn.close()
    except Exception as exc:
        print(f"[ASYNC] Could not read status: {exc}", file=sys.stderr)
        return

    if not rows:
        print("[ASYNC] No pipeline runs found.", file=sys.stderr)
        return

    run_id = rows[0][0]
    print(f"\n  Last run: {run_id}", file=sys.stderr)
    print(f"  {'Phase':<8s} {'Status':<12s} {'Duration':<12s} {'Error'}", file=sys.stderr)
    print(f"  {'─' * 8} {'─' * 12} {'─' * 12} {'─' * 30}", file=sys.stderr)
    for _, phase_id, status, duration, error in rows:
        dur_str = f"{duration:.1f}s" if duration else "—"
        err_str = (error[:30] + "...") if error and len(error) > 30 else (error or "")
        icon = {"completed": "✓", "failed": "✗", "skipped": "»", "running": "▶", "pending": "·"}.get(status, "?")
        print(f"  {icon} {phase_id:<6s} {status:<12s} {dur_str:<12s} {err_str}", file=sys.stderr)

    # Also check filesystem for the latest cycle
    cyclepacks = MASTER_ROOT / "cyclepacks"
    if cyclepacks.exists():
        summaries = sorted(cyclepacks.glob("CYCLE_*/async_pipeline_summary.json"), reverse=True)
        if summaries:
            data = json.loads(summaries[0].read_text(encoding="utf-8"))
            print(f"\n  Total elapsed: {data.get('total_elapsed_seconds', 0):.0f}s  |  "
                  f"Completed: {data.get('phases_completed', 0)}  |  "
                  f"Failed: {data.get('phases_failed', 0)}", file=sys.stderr)


# ── CLI ─────────────────────────────────────────────────────────────
def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="OMEGA Async Pipeline Orchestrator — DAG-aware parallel scheduling",
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # run
    run_parser = subparsers.add_parser("run", help="Execute the pipeline")
    run_parser.add_argument("--cycle-ts", default=None,
                            help="Cycle timestamp (default: current time)")
    run_parser.add_argument("--dry-run", action="store_true",
                            help="Show execution plan without running")
    run_parser.add_argument("--start", default=None, metavar="PHASE",
                            help="Phase ID to start from (e.g., '3', '4d')")
    run_parser.add_argument("--end", default=None, metavar="PHASE",
                            help="Phase ID to stop after (e.g., '7c', '16')")
    run_parser.add_argument("--skip", default=None, metavar="PHASES",
                            help="Comma-separated phase IDs to skip (e.g., '4e,9')")
    run_parser.add_argument("--max-workers", type=int, default=4,
                            help="Max parallel workers (default: 4)")
    run_parser.add_argument("--phase-timeout", type=int, default=600,
                            help="Per-phase timeout in seconds (default: 600)")
    run_parser.add_argument("--create-snapshot", action="store_true",
                            help="Create safety snapshot before running")

    # dag
    subparsers.add_parser("dag", help="Show DAG visualization")

    # status
    subparsers.add_parser("status", help="Show last run status")

    args = parser.parse_args()

    if args.command == "dag":
        print(AsyncPipelineOrchestrator.visualize_dag())
        return

    if args.command == "status":
        show_status()
        return

    if args.command == "run":
        skip = set()
        if args.skip:
            skip = {s.strip() for s in args.skip.split(",")}

        orchestrator = AsyncPipelineOrchestrator(
            max_workers=args.max_workers,
            phase_timeout=args.phase_timeout,
        )

        result = asyncio.run(
            orchestrator.run(
                cycle_ts=args.cycle_ts,
                start_phase=args.start,
                end_phase=args.end,
                skip_phases=skip,
                dry_run=args.dry_run,
                create_snap=args.create_snapshot,
            ),
        )

        print(result.summary())
        return

    parser.print_help()


if __name__ == "__main__":
    main()
