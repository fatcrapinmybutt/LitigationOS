#!/usr/bin/env python3
"""
Command Runner MCP Server — Replaces the PowerShell session pool.

One persistent FastMCP process → unlimited command executions → zero session
pool consumption. This permanently eliminates the shell pool exhaustion issue
that kills command execution after ~120 sessions per Copilot session.

Tools provided:
  - exec_command: Run any shell command via subprocess
  - exec_python: Run Python scripts with shadow-module safety
  - exec_git: Git operations with --no-pager
  - exec_pipeline_phase: Run pipeline phases directly
  - system_status: System health without needing a shell

Usage (auto-started via .vscode/mcp.json):
  python command_runner.py
"""

import logging
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

from mcp.server.fastmcp import FastMCP

# ── Configuration ──────────────────────────────────────────────────────

LITIGOS_ROOT = Path(r"C:\Users\andre\LitigationOS")
SAFE_CWD = LITIGOS_ROOT / "00_SYSTEM" / "scripts"
PIPELINE_DIR = LITIGOS_ROOT / "00_SYSTEM" / "pipeline"
MAX_OUTPUT = 100_000  # 100KB output cap to prevent context overflow
DEFAULT_TIMEOUT = 300  # 5 minutes
MAX_TIMEOUT = 600      # 10 minutes

# Shadow modules in repo root — NEVER set CWD there
SHADOW_MODULES = {
    'json.py', 'typing.py', 'tokenize.py', 'numpy.py', 'pandas.py',
    'io.py', 'os.py', 'sys.py', 'time.py', 'math.py', 'random.py',
    'logging.py', 'collections.py', 'functools.py', 'itertools.py',
    'pathlib.py', 're.py', 'hashlib.py', 'sqlite3.py', 'shutil.py',
    'argparse.py', 'subprocess.py',
}

logger = logging.getLogger("command_runner")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%H:%M:%S',
)

# ── Server ─────────────────────────────────────────────────────────────

mcp = FastMCP("command_runner")


# ── Safety Helpers ─────────────────────────────────────────────────────

def _safe_cwd(requested: Optional[str]) -> str:
    """Resolve a safe working directory, never allowing repo root."""
    if not requested:
        return str(SAFE_CWD)

    cwd = Path(requested).resolve()

    # Block repo root (shadow modules will break Python)
    if cwd == LITIGOS_ROOT.resolve():
        logger.warning("Blocked CWD at repo root (shadow modules). Using %s", SAFE_CWD)
        return str(SAFE_CWD)

    # Verify directory exists
    if not cwd.exists():
        logger.warning("CWD %s does not exist, falling back to %s", cwd, SAFE_CWD)
        return str(SAFE_CWD)

    return str(cwd)


def _truncate(text: str, limit: int = MAX_OUTPUT) -> str:
    """Truncate output to prevent context overflow."""
    if len(text) <= limit:
        return text
    half = limit // 2
    return (
        text[:half]
        + f"\n\n... [TRUNCATED: {len(text) - limit} chars omitted] ...\n\n"
        + text[-half:]
    )


def _run(cmd: list, cwd: str, timeout: int, env: Optional[dict] = None) -> dict:
    """Execute a command and return structured result."""
    merged_env = os.environ.copy()
    merged_env["PYTHONUTF8"] = "1"
    merged_env["PYTHONDONTWRITEBYTECODE"] = "1"
    if env:
        merged_env.update(env)

    start = time.time()
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=min(timeout, MAX_TIMEOUT),
            env=merged_env,
            encoding='utf-8',
            errors='replace',
        )
        elapsed = round(time.time() - start, 2)

        stdout = _truncate(result.stdout or "")
        stderr = _truncate(result.stderr or "")

        return {
            "exit_code": result.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "elapsed_seconds": elapsed,
            "cwd": cwd,
            "status": "success" if result.returncode == 0 else "failed",
        }
    except subprocess.TimeoutExpired:
        return {
            "exit_code": -1,
            "stdout": "",
            "stderr": f"Command timed out after {timeout}s",
            "elapsed_seconds": timeout,
            "cwd": cwd,
            "status": "timeout",
        }
    except Exception as e:
        return {
            "exit_code": -1,
            "stdout": "",
            "stderr": str(e),
            "elapsed_seconds": round(time.time() - start, 2),
            "cwd": cwd,
            "status": "error",
        }


# ── MCP Tools ──────────────────────────────────────────────────────────

@mcp.tool()
def exec_command(
    command: str,
    cwd: Optional[str] = None,
    timeout: int = 300,
) -> str:
    """Execute a shell command and return output.

    Runs via PowerShell subprocess — does NOT consume the Copilot shell pool.
    Default CWD is 00_SYSTEM/scripts (never repo root due to shadow modules).

    Args:
        command: The command to execute (PowerShell syntax)
        cwd: Working directory (default: 00_SYSTEM/scripts, blocked: repo root)
        timeout: Max seconds to wait (default: 300, max: 600)
    """
    safe = _safe_cwd(cwd)
    logger.info("exec_command: %s (cwd=%s, timeout=%d)", command[:100], safe, timeout)

    result = _run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", command],
        cwd=safe,
        timeout=timeout,
    )

    output_parts = []
    if result["stdout"]:
        output_parts.append(result["stdout"])
    if result["stderr"]:
        output_parts.append(f"[STDERR]\n{result['stderr']}")
    output_parts.append(
        f"\n[exit={result['exit_code']} | {result['elapsed_seconds']}s | cwd={result['cwd']}]"
    )
    return "\n".join(output_parts)


@mcp.tool()
def exec_python(
    script_path: str,
    args: Optional[str] = None,
    cwd: Optional[str] = None,
    timeout: int = 600,
) -> str:
    """Execute a Python script safely, avoiding shadow module conflicts.

    CWD is automatically set to the script's parent directory (not repo root)
    to prevent shadow module imports. PYTHONUTF8=1 is forced.

    Args:
        script_path: Absolute or relative path to the .py script
        args: Space-separated arguments to pass to the script
        cwd: Override working directory (default: script's parent dir)
        timeout: Max seconds (default: 600 for longer scripts)
    """
    script = Path(script_path)
    if not script.is_absolute():
        script = LITIGOS_ROOT / script_path

    if not script.exists():
        return f"ERROR: Script not found: {script}"

    # Default CWD to script's parent directory (shadow module safe)
    if not cwd:
        cwd = str(script.parent)
    safe = _safe_cwd(cwd)

    cmd = [sys.executable, str(script)]
    if args:
        cmd.extend(args.split())

    logger.info("exec_python: %s %s (cwd=%s)", script.name, args or "", safe)
    result = _run(cmd, cwd=safe, timeout=timeout)

    output_parts = []
    if result["stdout"]:
        output_parts.append(result["stdout"])
    if result["stderr"]:
        output_parts.append(f"[STDERR]\n{result['stderr']}")
    output_parts.append(
        f"\n[exit={result['exit_code']} | {result['elapsed_seconds']}s | script={script.name}]"
    )
    return "\n".join(output_parts)


@mcp.tool()
def exec_git(args: str, timeout: int = 120) -> str:
    """Execute a git command in the LitigationOS repository.

    Always uses --no-pager to prevent interactive blocking.

    Args:
        args: Git arguments (e.g., 'status', 'diff --stat', 'add -A && git commit -m "msg"')
        timeout: Max seconds (default: 120, git on 125K+ files is slow)
    """
    logger.info("exec_git: git %s", args[:100])

    result = _run(
        ["git", "--no-pager"] + args.split(),
        cwd=str(LITIGOS_ROOT),
        timeout=timeout,
    )

    output_parts = []
    if result["stdout"]:
        output_parts.append(result["stdout"])
    if result["stderr"]:
        output_parts.append(f"[STDERR]\n{result['stderr']}")
    output_parts.append(
        f"\n[exit={result['exit_code']} | {result['elapsed_seconds']}s]"
    )
    return "\n".join(output_parts)


@mcp.tool()
def exec_pipeline_phase(
    phase: str,
    dry_run: bool = False,
    timeout: int = 600,
) -> str:
    """Execute a LitigationOS pipeline phase or critical path script.

    Available phases:
      - noreply_pdfs: Process 347+ NoReply PDF court documents
      - ocr_evidence: OCR scanned evidence images
      - backup: Run database backup with rotation
      - syntax_check: Validate Python syntax of pipeline modules
      - pipeline: Run full 16-phase Omega pipeline
      - Any phase name from run_omega_pipeline.py

    Args:
        phase: Phase name to execute
        dry_run: If True, preview without writing (default: False)
        timeout: Max seconds (default: 600)
    """
    phase_scripts = {
        "noreply_pdfs": (SAFE_CWD / "noreply_pdf_processor.py", []),
        "ocr_evidence": (SAFE_CWD / "ocr_evidence_pipeline.py", []),
        "ocr_check": (SAFE_CWD / "ocr_evidence_pipeline.py", ["--check"]),
        "backup": (SAFE_CWD / "backup_rotation.py", []),
        "backup_status": (SAFE_CWD / "backup_rotation.py", ["--status"]),
        "syntax_check": (LITIGOS_ROOT / "00_SYSTEM" / "scripts" / "syntax_check.py", []),
        "pipeline": (PIPELINE_DIR / "run_omega_pipeline.py", []),
        "validate": (SAFE_CWD / "phase3_validate.py", []),
        "autonomous": (SAFE_CWD / "autonomous_runner.py", []),
        "autonomous_resume": (SAFE_CWD / "autonomous_runner.py", ["--resume"]),
        "autonomous_status": (SAFE_CWD / "autonomous_runner.py", ["--status"]),
    }

    if phase not in phase_scripts:
        available = ", ".join(sorted(phase_scripts.keys()))
        return f"Unknown phase: {phase}\nAvailable: {available}"

    script, extra_args = phase_scripts[phase]
    if not script.exists():
        return f"ERROR: Script not found: {script}"

    cmd = [sys.executable, str(script)] + extra_args
    if dry_run:
        cmd.append("--dry-run")

    logger.info("exec_pipeline_phase: %s (dry_run=%s)", phase, dry_run)
    result = _run(cmd, cwd=str(script.parent), timeout=timeout)

    output_parts = [f"═══ Pipeline Phase: {phase} ═══"]
    if result["stdout"]:
        output_parts.append(result["stdout"])
    if result["stderr"]:
        output_parts.append(f"[STDERR]\n{result['stderr']}")
    output_parts.append(
        f"\n[phase={phase} | exit={result['exit_code']} | {result['elapsed_seconds']}s | "
        f"status={result['status']}]"
    )
    return "\n".join(output_parts)


@mcp.tool()
def system_status() -> str:
    """Get system health status without consuming a shell session.

    Reports: Python version, disk space, DB sizes, process count, memory.
    """
    import shutil
    import sqlite3

    lines = ["═══ LitigationOS System Status ═══"]

    # Python
    lines.append(f"Python: {sys.version}")
    lines.append(f"CWD: {os.getcwd()}")

    # Disk space for key drives
    for drive in ["C:\\", "I:\\", "F:\\", "G:\\"]:
        try:
            usage = shutil.disk_usage(drive)
            free_gb = usage.free / (1024**3)
            total_gb = usage.total / (1024**3)
            lines.append(f"Disk {drive}: {free_gb:.1f} GB free / {total_gb:.1f} GB total")
        except (OSError, FileNotFoundError):
            lines.append(f"Disk {drive}: NOT MOUNTED")

    # Main DB size
    db_path = LITIGOS_ROOT / "litigation_context.db"
    if db_path.exists():
        size_gb = db_path.stat().st_size / (1024**3)
        lines.append(f"Main DB: {size_gb:.2f} GB")
        try:
            conn = sqlite3.connect(str(db_path), timeout=10)
            tables = conn.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
            ).fetchone()[0]
            conn.close()
            lines.append(f"DB Tables: {tables}")
        except Exception as e:
            lines.append(f"DB Access: ERROR ({e})")

    # Lane DB status
    lane_dbs = ["lane_A_custody", "lane_B_housing", "lane_C_convergence",
                "lane_D_ppo", "lane_E_misconduct", "lane_F_appellate"]
    for name in lane_dbs:
        p = LITIGOS_ROOT / f"{name}.db"
        if p.exists():
            size_mb = p.stat().st_size / (1024**2)
            lines.append(f"  {name}: {size_mb:.1f} MB")

    # Timestamp
    lines.append(f"\nTimestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    return "\n".join(lines)


# ── Main ───────────────────────────────────────────────────────────────

def main():
    """Start the command runner MCP server."""
    logger.info("Command Runner MCP starting (stdio transport)")
    logger.info("Root: %s", LITIGOS_ROOT)
    logger.info("Safe CWD: %s", SAFE_CWD)
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
