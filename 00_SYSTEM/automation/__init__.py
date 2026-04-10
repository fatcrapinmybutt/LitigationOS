"""
LitigationOS Automation Registry
=================================

Central registry for all 13 omega/utility automation scripts.
Provides discovery, dispatch, and execution with stdout/stderr capture.

Usage:
    from automation import run_automation, list_automations, AUTOMATION_REGISTRY

    # List available tasks
    for task in list_automations():
        print(task["name"], task["description"])

    # Run a specific automation
    result = run_automation("file_forensics", target="/path/to/folder")
    print(result["status"], result["output"])
"""

import importlib
import io
import logging
import sys
import traceback
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from typing import Any

logger = logging.getLogger("automation")

_AUTOMATION_DIR = Path(__file__).resolve().parent

# ─── Registry ────────────────────────────────────────────────────
# Maps task_name → metadata about the script and its entry point.
# "module" is the Python module name (relative to this package).
# "entry" is the callable name inside that module.
# "needs_target" indicates whether the entry function requires a folder path arg.

AUTOMATION_REGISTRY: dict[str, dict[str, Any]] = {
    "file_forensics": {
        "script_path": str(_AUTOMATION_DIR / "omega_01_file_forensics.py"),
        "module": "omega_01_file_forensics",
        "entry": "scan_folder",
        "needs_target": True,
        "description": "Deep file metadata analysis, integrity checks, and timestamp forensics",
        "schedule_hint": "weekly",
    },
    "legal_audit": {
        "script_path": str(_AUTOMATION_DIR / "omega_02_legal_audit.py"),
        "module": "omega_02_legal_audit",
        "entry": "audit_folder",
        "needs_target": True,
        "description": "Audit legal documents for MCR/MCL compliance, hallucinations, and formatting",
        "schedule_hint": "before_filing",
    },
    "evidence_harvest": {
        "script_path": str(_AUTOMATION_DIR / "omega_03_evidence_harvest.py"),
        "module": "omega_03_evidence_harvest",
        "entry": "harvest_folder",
        "needs_target": True,
        "description": "Extract quotes, dates, names, and allegations into structured evidence index",
        "schedule_hint": "on_new_documents",
    },
    "citation_extract": {
        "script_path": str(_AUTOMATION_DIR / "omega_04_citation_extract.py"),
        "module": "omega_04_citation_extract",
        "entry": "extract_folder",
        "needs_target": True,
        "description": "Extract and catalog all legal citations (MCR, MCL, MRE, case law) with frequency analysis",
        "schedule_hint": "on_new_documents",
    },
    "hash_verify": {
        "script_path": str(_AUTOMATION_DIR / "omega_05_hash_verify.py"),
        "module": "omega_05_hash_verify",
        "entry": "verify_folder",
        "needs_target": True,
        "description": "SHA-256 integrity verification — baseline on first run, tamper detection on subsequent",
        "schedule_hint": "daily",
    },
    "timeline_build": {
        "script_path": str(_AUTOMATION_DIR / "omega_06_timeline_builder.py"),
        "module": "omega_06_timeline_builder",
        "entry": "build_timeline",
        "needs_target": True,
        "description": "Auto-generate chronological timeline from all documents with source citations",
        "schedule_hint": "on_new_documents",
    },
    "redaction_scan": {
        "script_path": str(_AUTOMATION_DIR / "omega_07_redaction_scan.py"),
        "module": "omega_07_redaction_scan",
        "entry": "scan_folder",
        "needs_target": True,
        "description": "Scan for PII (SSN, DOB, phone, financial info, minor names) before filing",
        "schedule_hint": "before_filing",
    },
    "exhibit_stamp": {
        "script_path": str(_AUTOMATION_DIR / "omega_08_exhibit_stamper.py"),
        "module": "omega_08_exhibit_stamper",
        "entry": "stamp_folder",
        "needs_target": True,
        "description": "Auto-assign Bates numbers and exhibit labels with index generation",
        "schedule_hint": "before_filing",
    },
    "contradiction_scan": {
        "script_path": str(_AUTOMATION_DIR / "omega_09_contradiction_scan.py"),
        "module": "omega_09_contradiction_scan",
        "entry": "scan_folder",
        "needs_target": True,
        "description": "Detect contradictions across documents using semantic opposition analysis",
        "schedule_hint": "weekly",
    },
    "court_package": {
        "script_path": str(_AUTOMATION_DIR / "omega_10_court_packager.py"),
        "module": "omega_10_court_packager",
        "entry": "package_folder",
        "needs_target": True,
        "description": "Assemble complete court filing package with checklist, exhibit index, and manifest",
        "schedule_hint": "before_filing",
    },
    "dedupe": {
        "script_path": str(_AUTOMATION_DIR / "dedupe_target.py"),
        "module": "dedupe_target",
        "entry": "dedupe_folder",
        "needs_target": True,
        "description": "SHA-256 deduplication — move duplicate files to _DEDUP_TRASH with collision log",
        "schedule_hint": "weekly",
    },
    "organize_by_type": {
        "script_path": str(_AUTOMATION_DIR / "organize_by_type.py"),
        "module": "organize_by_type",
        "entry": "organize_folder",
        "needs_target": True,
        "description": "Sort files into type-based buckets (_PDF, _TXT, _MD, etc.) preserving structure",
        "schedule_hint": "on_new_documents",
    },
    "scheduled_maintenance": {
        "script_path": str(_AUTOMATION_DIR / "scheduled_maintenance.py"),
        "module": "scheduled_maintenance",
        "entry": "main",
        "needs_target": False,
        "description": "Full maintenance cycle: organize → dedupe → ingest from external drives → health report",
        "schedule_hint": "daily",
    },
}


def _import_entry(task_name: str):
    """Lazily import and return the entry-point callable for a task.

    Uses importlib to avoid loading all 13 scripts at module import time.
    The automation directory is temporarily added to sys.path so that
    bare module names resolve correctly.
    """
    meta = AUTOMATION_REGISTRY.get(task_name)
    if meta is None:
        raise KeyError(f"Unknown automation task: {task_name!r}")

    module_name = meta["module"]
    entry_name = meta["entry"]
    automation_dir = str(_AUTOMATION_DIR)

    # Ensure the automation directory is on sys.path for import resolution
    path_added = False
    if automation_dir not in sys.path:
        sys.path.insert(0, automation_dir)
        path_added = True

    try:
        mod = importlib.import_module(module_name)
        fn = getattr(mod, entry_name)
        return fn
    finally:
        if path_added:
            try:
                sys.path.remove(automation_dir)
            except ValueError:
                pass


def run_automation(task_name: str, **kwargs) -> dict[str, Any]:
    """Execute an automation task by name, capturing stdout/stderr.

    Parameters
    ----------
    task_name : str
        Key from AUTOMATION_REGISTRY (e.g. "file_forensics", "dedupe").
    **kwargs
        Passed to the entry-point function.  For target-based scripts,
        supply ``target="/path/to/folder"``.

    Returns
    -------
    dict with keys:
        status  : "completed" | "error"
        output  : captured stdout (str)
        errors  : captured stderr (str)
        result  : return value from the entry function (if any)
    """
    meta = AUTOMATION_REGISTRY.get(task_name)
    if meta is None:
        return {
            "status": "error",
            "output": "",
            "errors": f"Unknown automation task: {task_name!r}",
            "result": None,
        }

    try:
        fn = _import_entry(task_name)
    except Exception as exc:
        logger.error("Failed to import automation %s: %s", task_name, exc, exc_info=True)
        return {
            "status": "error",
            "output": "",
            "errors": f"Import failed for {task_name}: {exc}",
            "result": None,
        }

    # Build positional args for the entry function
    call_args: list[Any] = []
    if meta["needs_target"]:
        target = kwargs.pop("target", None)
        if not target:
            return {
                "status": "error",
                "output": "",
                "errors": f"Automation {task_name!r} requires a 'target' folder path",
                "result": None,
            }
        target_path = Path(target)
        if not target_path.exists():
            return {
                "status": "error",
                "output": "",
                "errors": f"Target path does not exist: {target}",
                "result": None,
            }
        call_args.append(str(target_path))

    # Capture stdout/stderr during execution
    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()

    try:
        with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
            result = fn(*call_args, **kwargs)

        return {
            "status": "completed",
            "output": stdout_buf.getvalue(),
            "errors": stderr_buf.getvalue(),
            "result": result,
        }
    except Exception as exc:
        logger.error(
            "Automation %s raised: %s", task_name, exc, exc_info=True
        )
        return {
            "status": "error",
            "output": stdout_buf.getvalue(),
            "errors": stderr_buf.getvalue() + "\n" + traceback.format_exc(),
            "result": None,
        }


def list_automations() -> list[dict[str, str]]:
    """Return a list of available automation tasks with metadata.

    Each entry contains:
        name          : task key for run_automation()
        description   : human-readable purpose
        schedule_hint : suggested run frequency
        script_path   : absolute path to the script file
        needs_target  : whether a folder path argument is required
    """
    return [
        {
            "name": name,
            "description": meta["description"],
            "schedule_hint": meta["schedule_hint"],
            "script_path": meta["script_path"],
            "needs_target": meta["needs_target"],
        }
        for name, meta in AUTOMATION_REGISTRY.items()
    ]
