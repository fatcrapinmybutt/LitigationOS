#!/usr/bin/env python3
"""
command-runner MCP server for LitigationOS.

Provides 5 tools that replace PowerShell session management:
  exec_command, exec_python, exec_git, exec_pipeline_phase, system_status

Protocol: JSON-RPC 2.0 over stdio (one JSON object per line).
Dependencies: Python stdlib ONLY — no external packages.
"""

# --- Workaround for broken Python installs missing operator.py ----------
# On this machine the Lib/operator.py wrapper is absent but the C extension
# _operator exists.  Patch sys.modules BEFORE any stdlib import that
# transitively needs it (json → re → enum → operator).
import sys as _sys
try:
    import operator as _op_test  # noqa: F401 — probe only
except ModuleNotFoundError:
    import _operator
    _sys.modules["operator"] = _operator
del _sys
# -----------------------------------------------------------------------

import sys
import json
import os
import subprocess
import platform
import shutil
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REPO_ROOT = Path(r"C:\Users\andre\LitigationOS")
PIPELINE_DIR = REPO_ROOT / "00_SYSTEM" / "pipeline"
MAIN_DB = REPO_ROOT / "litigation_context.db"
MAX_OUTPUT_BYTES = 250 * 1024  # 250 KB
DEFAULT_TIMEOUT = 600  # seconds

SERVER_INFO = {
    "name": "command-runner",
    "version": "1.0.0",
}

# Phase name → script mapping (relative to PIPELINE_DIR)
PHASE_MAP = {
    "1":  "phase1_inventory.py",
    "2":  "phase2_dedup.py",
    "3":  "phase3_classify.py",
    "4a": "phase4a_pdf_extract.py",
    "4b": "phase4b_docx_extract.py",
    "4c": "phase4c_structured_extract.py",
    "4d": "phase4d_atomize.py",
    "4e": "phase4e_archive_extract.py",
    "5":  "phase5_brain_feed.py",
    "7a": "phase7a_graph_delta.py",
    "7c": "phase7c_knowledge_merge.py",
    "8":  "phase8_litigation_refresh.py",
    "12": "phase12_rule_audit.py",
    "13": "phase13_refinement.py",
    "14": "phase14_finalize.py",
    "16": "phase16_desktop.py",
    "validate":    "validate.py",
    "status":      "quick_status.py",
    "autopilot":   "autopilot.py",
    "filing":      "filing_factory.py",
}

# ---------------------------------------------------------------------------
# Tool definitions (returned by tools/list)
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "name": "exec_command",
        "description": (
            "Execute any shell command via subprocess. "
            "Returns stdout and stderr. Timeout 600s. Max output 250KB."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The shell command to execute.",
                },
            },
            "required": ["command"],
        },
    },
    {
        "name": "exec_python",
        "description": (
            "Execute a Python script with PYTHONUTF8=1. "
            "Avoids shadow modules by running outside repo root. "
            "Returns stdout and stderr."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "script_path": {
                    "type": "string",
                    "description": "Absolute or repo-relative path to the .py script.",
                },
                "args": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional command-line arguments for the script.",
                    "default": [],
                },
            },
            "required": ["script_path"],
        },
    },
    {
        "name": "exec_git",
        "description": (
            "Execute a git command with --no-pager in the LitigationOS repo. "
            "Pass the git sub-command and arguments as a single string "
            "(e.g. 'status', 'diff --stat', 'log --oneline -20')."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "args": {
                    "type": "string",
                    "description": "Git sub-command and arguments (e.g. 'status').",
                },
            },
            "required": ["args"],
        },
    },
    {
        "name": "exec_pipeline_phase",
        "description": (
            "Execute a LitigationOS pipeline phase by name. "
            "Valid phases: "
            + ", ".join(sorted(PHASE_MAP.keys()))
            + ". Returns the script output."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "phase": {
                    "type": "string",
                    "description": "Phase identifier (e.g. '1', '4a', 'validate').",
                },
            },
            "required": ["phase"],
        },
    },
    {
        "name": "system_status",
        "description": (
            "Return system health information: Python version, disk space, "
            "DB file size, git branch/status, and OS details."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _truncate(text: str) -> str:
    """Truncate output to MAX_OUTPUT_BYTES, appending a warning if trimmed."""
    encoded = text.encode("utf-8", errors="replace")
    if len(encoded) <= MAX_OUTPUT_BYTES:
        return text
    truncated = encoded[:MAX_OUTPUT_BYTES].decode("utf-8", errors="replace")
    return truncated + "\n\n[OUTPUT TRUNCATED at 250 KB]"


def _run(cmd, *, cwd=None, timeout=DEFAULT_TIMEOUT, shell=True, env=None):
    """Run a subprocess and return (stdout+stderr) as a string."""
    merged_env = os.environ.copy()
    merged_env["PYTHONUTF8"] = "1"
    if env:
        merged_env.update(env)

    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            shell=shell,
            capture_output=True,
            timeout=timeout,
            env=merged_env,
        )
        out = result.stdout.decode("utf-8", errors="replace")
        err = result.stderr.decode("utf-8", errors="replace")

        parts = []
        if out.strip():
            parts.append(out)
        if err.strip():
            parts.append(f"[STDERR]\n{err}")
        if result.returncode != 0:
            parts.append(f"[EXIT CODE: {result.returncode}]")

        text = "\n".join(parts) if parts else "(no output)"
        return _truncate(text)

    except subprocess.TimeoutExpired:
        return f"[ERROR] Command timed out after {timeout}s"
    except FileNotFoundError as exc:
        return f"[ERROR] Command not found: {exc}"
    except Exception as exc:
        return f"[ERROR] {type(exc).__name__}: {exc}"


def _resolve_script(raw_path: str) -> Path:
    """Resolve a script path that may be absolute or repo-relative."""
    p = Path(raw_path)
    if p.is_absolute():
        return p
    return REPO_ROOT / p


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------


def tool_exec_command(arguments: dict) -> str:
    command = arguments.get("command", "")
    if not command:
        return "[ERROR] 'command' parameter is required."
    return _run(command, cwd=str(REPO_ROOT))


def tool_exec_python(arguments: dict) -> str:
    raw = arguments.get("script_path", "")
    if not raw:
        return "[ERROR] 'script_path' parameter is required."

    script = _resolve_script(raw)
    if not script.exists():
        return f"[ERROR] Script not found: {script}"

    args = arguments.get("args") or []
    # CWD = script's own directory to avoid shadow modules in repo root
    cwd = str(script.parent)
    cmd = [sys.executable, str(script)] + list(args)
    return _run(cmd, cwd=cwd, shell=False)


def tool_exec_git(arguments: dict) -> str:
    raw_args = arguments.get("args", "")
    if not raw_args:
        return "[ERROR] 'args' parameter is required."
    cmd = f"git --no-pager {raw_args}"
    return _run(cmd, cwd=str(REPO_ROOT))


def tool_exec_pipeline_phase(arguments: dict) -> str:
    phase = arguments.get("phase", "")
    if not phase:
        return "[ERROR] 'phase' parameter is required."

    script_name = PHASE_MAP.get(phase)
    if not script_name:
        valid = ", ".join(sorted(PHASE_MAP.keys()))
        return f"[ERROR] Unknown phase '{phase}'. Valid phases: {valid}"

    script = PIPELINE_DIR / script_name
    if not script.exists():
        return f"[ERROR] Pipeline script not found: {script}"

    cmd = [sys.executable, str(script)]
    return _run(cmd, cwd=str(PIPELINE_DIR), shell=False)


def tool_system_status(_arguments: dict) -> str:
    lines = []

    # Python
    lines.append(f"Python: {sys.version}")
    lines.append(f"Executable: {sys.executable}")
    lines.append(f"Platform: {platform.platform()}")

    # Disk space for repo drive
    try:
        usage = shutil.disk_usage(str(REPO_ROOT))
        gb = lambda b: f"{b / (1024**3):.1f} GB"
        lines.append(
            f"Disk (C:): {gb(usage.used)} used / {gb(usage.total)} total "
            f"({gb(usage.free)} free)"
        )
    except Exception as exc:
        lines.append(f"Disk: error — {exc}")

    # Main DB size
    try:
        if MAIN_DB.exists():
            size_mb = MAIN_DB.stat().st_size / (1024 * 1024)
            lines.append(f"litigation_context.db: {size_mb:.1f} MB")
        else:
            lines.append("litigation_context.db: NOT FOUND")
    except Exception as exc:
        lines.append(f"litigation_context.db: error — {exc}")

    # Git status (quick)
    try:
        branch = subprocess.run(
            "git --no-pager rev-parse --abbrev-ref HEAD",
            cwd=str(REPO_ROOT),
            shell=True,
            capture_output=True,
            timeout=10,
        )
        branch_name = branch.stdout.decode("utf-8", errors="replace").strip()
        lines.append(f"Git branch: {branch_name}")

        status = subprocess.run(
            "git --no-pager status --porcelain",
            cwd=str(REPO_ROOT),
            shell=True,
            capture_output=True,
            timeout=10,
        )
        changed = len(
            [l for l in status.stdout.decode("utf-8", errors="replace").splitlines() if l.strip()]
        )
        lines.append(f"Git changed files: {changed}")
    except Exception as exc:
        lines.append(f"Git: error — {exc}")

    # Running Python processes (approximate)
    try:
        if platform.system() == "Windows":
            r = subprocess.run(
                'tasklist /FI "IMAGENAME eq python.exe" /NH',
                shell=True,
                capture_output=True,
                timeout=10,
            )
            procs = [
                l for l in r.stdout.decode("utf-8", errors="replace").splitlines()
                if "python" in l.lower()
            ]
            lines.append(f"Python processes: {len(procs)}")
        else:
            lines.append("Python processes: (non-Windows — skipped)")
    except Exception:
        lines.append("Python processes: unknown")

    lines.append(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    return "\n".join(lines)


# Dispatch table
TOOL_DISPATCH = {
    "exec_command": tool_exec_command,
    "exec_python": tool_exec_python,
    "exec_git": tool_exec_git,
    "exec_pipeline_phase": tool_exec_pipeline_phase,
    "system_status": tool_system_status,
}

# ---------------------------------------------------------------------------
# JSON-RPC / MCP protocol handling
# ---------------------------------------------------------------------------


def make_result(request_id, result):
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def make_error(request_id, code, message):
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def handle_request(msg: dict) -> dict | None:
    """Process one JSON-RPC request and return the response (or None for notifications)."""
    method = msg.get("method", "")
    request_id = msg.get("id")
    params = msg.get("params") or {}

    # --- MCP lifecycle ---
    if method == "initialize":
        return make_result(request_id, {
            "capabilities": {"tools": {}},
            "serverInfo": SERVER_INFO,
            "protocolVersion": "2024-11-05",
        })

    if method == "notifications/initialized":
        # Client acknowledgement — no response needed for notifications
        return None

    # --- Tool discovery ---
    if method == "tools/list":
        return make_result(request_id, {"tools": TOOLS})

    # --- Tool execution ---
    if method == "tools/call":
        tool_name = params.get("name", "")
        arguments = params.get("arguments") or {}

        handler = TOOL_DISPATCH.get(tool_name)
        if not handler:
            return make_result(request_id, {
                "content": [{"type": "text", "text": f"[ERROR] Unknown tool: {tool_name}"}],
                "isError": True,
            })

        try:
            text = handler(arguments)
        except Exception as exc:
            text = f"[ERROR] {type(exc).__name__}: {exc}"

        return make_result(request_id, {
            "content": [{"type": "text", "text": text}],
        })

    # --- Catch-all for unknown methods ---
    if request_id is not None:
        return make_error(request_id, -32601, f"Method not found: {method}")

    # Unknown notification — ignore silently
    return None


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------


def main():
    # Force UTF-8 on stdout/stderr to prevent encoding crashes on Windows
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    # Ensure stdin reads as UTF-8 binary lines
    stdin = sys.stdin
    if hasattr(stdin, "reconfigure"):
        stdin.reconfigure(encoding="utf-8", errors="replace")

    while True:
        try:
            line = stdin.readline()
            if not line:
                # EOF — client disconnected
                break

            line = line.strip()
            if not line:
                continue

            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                # Skip malformed input
                continue

            response = handle_request(msg)
            if response is not None:
                out = json.dumps(response, ensure_ascii=False) + "\n"
                sys.stdout.write(out)
                sys.stdout.flush()

        except KeyboardInterrupt:
            break
        except Exception:
            # Never let an unhandled exception kill the server
            continue


if __name__ == "__main__":
    main()
