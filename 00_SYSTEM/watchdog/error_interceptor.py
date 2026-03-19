"""
ERROR INTERCEPTOR & AUTO-REPAIR ENGINE
=======================================
Catches common shell/command errors, auto-repairs them, and retries.
Integrated with Shell Watchdog system.

Error classes handled:
- Unknown option / unrecognized flag
- Command not found / not recognized
- File/path not found
- Permission denied
- Encoding errors (Windows UTF-8)
- Git-specific errors
- Python-specific errors
- PowerShell syntax errors
- Database lock errors
- Memory/disk errors
- Pipe buffer exhaustion (EAGAIN/EWOULDBLOCK/EPIPE)
- File descriptor exhaustion (EMFILE)
"""

import re
import json
import os
import sys
import time
import sqlite3
import subprocess
from datetime import datetime
from pathlib import Path

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

# ── Constants ────────────────────────────────────────────────────────
WATCHDOG_DIR = Path(__file__).parent
ERROR_LOG = WATCHDOG_DIR / "error_log.jsonl"
REPAIR_DB = WATCHDOG_DIR / "watchdog.db"
MAX_RETRIES = 3

# ── Error Pattern Database ───────────────────────────────────────────
# Each pattern: (regex, error_class, auto_fix_function_name, description)
ERROR_PATTERNS = [
    # Git errors
    (r"unknown option[:\s]+['\"]?(--[\w-]+)", "git_unknown_option",
     "fix_git_unknown_option", "Git flag used on wrong subcommand"),
    (r"error: unknown option '(--[\w-]+)'", "git_unknown_option",
     "fix_git_unknown_option", "Git flag not recognized"),
    (r"not a git repository", "git_not_repo",
     "fix_git_not_repo", "Command run outside git repo"),
    (r"fatal: bad default revision 'HEAD'", "git_no_commits",
     "fix_git_no_commits", "Git repo has no commits"),

    # PowerShell errors
    (r"The term '(.+?)' is not recognized", "command_not_found",
     "fix_command_not_found", "Command/tool not in PATH"),

    # Python errors (BEFORE PS syntax to avoid false match)
    (r"SyntaxError: unterminated string literal", "py_syntax",
     "fix_py_write_file", "Python inline code with bad escaping"),
    (r"(?<!Syntax)unterminated string literal", "ps_syntax",
     "fix_ps_syntax", "PowerShell string escaping issue"),
    (r"Cannot bind argument to parameter '(.+?)' because it is null", "ps_null_param",
     "fix_ps_null_param", "Null parameter in PowerShell"),
    (r"FullyQualifiedErrorId\s*:\s*PathNotFound", "path_not_found",
     "fix_path_not_found", "File or directory not found"),

    # Python errors (continued)
    (r"UnicodeDecodeError", "py_encoding",
     "fix_py_encoding", "Python encoding error on Windows"),
    (r"UnicodeEncodeError", "py_encoding",
     "fix_py_encoding", "Python encoding error on output"),
    (r"ModuleNotFoundError: No module named '(.+?)'", "py_module",
     "fix_py_module", "Missing Python module"),
    (r"sqlite3\.OperationalError: database is locked", "db_locked",
     "fix_db_locked", "SQLite database lock contention"),
    (r"sqlite3\.OperationalError: no such table: (\w+)", "db_no_table",
     "fix_db_no_table", "Table doesn't exist in database"),
    (r"sqlite3\.OperationalError: no such column: (\w+)", "db_no_column",
     "fix_db_no_column", "Column doesn't exist in table"),

    # ripgrep / search tool errors
    (r"rg: unrecognized flag (--[\w-]+)", "rg_bad_flag",
     "fix_rg_bad_flag", "Ripgrep flag error (pattern looks like flag)"),

    # File system errors
    (r"Access to the path '(.+?)' is denied", "permission_denied",
     "fix_permission_denied", "File access permission error"),
    (r"The process cannot access the file", "file_locked",
     "fix_file_locked", "File is locked by another process"),
    (r"There is not enough space on the disk", "disk_full",
     "fix_disk_full", "Disk space exhausted"),

    # Copilot CLI errors
    (r"try 'copilot --help' for more information", "copilot_cli_error",
     "fix_copilot_cli_error", "Copilot CLI received bad flag or command"),
    (r"Error:.*copilot.*unrecognized", "copilot_cli_error",
     "fix_copilot_cli_error", "Copilot CLI unrecognized command"),

    # MCP server errors
    (r"MCP server .* failed|mcp.*connection refused|mcp.*timed out", "mcp_server_error",
     "fix_mcp_server_error", "MCP server crashed or timed out"),
    (r"npx.*ERR!|npm ERR!", "npm_error",
     "fix_npm_error", "NPX/NPM command failed"),

    # Network / timeout
    (r"Operation timed out", "timeout",
     "fix_timeout", "Command timed out"),
    (r"Invalid shell ID", "shell_dead",
     "fix_shell_dead", "PowerShell session expired"),

    # Pipe / buffer exhaustion (EAGAIN)
    (r"write EAGAIN|EAGAIN|resource temporarily unavailable", "pipe_eagain",
     "fix_pipe_eagain", "Pipe buffer full — write cannot complete (non-blocking I/O exhaustion)"),
    (r"EWOULDBLOCK|ENOBUFS", "pipe_eagain",
     "fix_pipe_eagain", "Socket/pipe buffer exhaustion variant"),
    (r"write EPIPE|broken pipe|SIGPIPE", "pipe_broken",
     "fix_pipe_broken", "Pipe reader disconnected — downstream process died"),
    (r"EMFILE|too many open files", "fd_exhaustion",
     "fix_fd_exhaustion", "File descriptor limit reached — too many open handles"),
]

# ── Known Fix Mappings ───────────────────────────────────────────────
# Maps bad commands/flags to their correct versions
GIT_FLAG_FIXES = {
    "--no-walk": {
        "valid_subcommands": ["log", "show", "rev-list"],
        "fix": "Move --no-walk after the subcommand, not before it",
        "example_bad": "git --no-walk log",
        "example_good": "git log --no-walk"
    },
    "--no-pager": {
        "valid_position": "before subcommand",
        "fix": "git --no-pager <subcommand>",
    },
    "--no-warn": {
        "fix": "This is not a git flag. For node: use NODE_NO_WARNINGS=1",
    },
    "--no-warnings": {
        "fix": "Use --quiet for git, or NODE_OPTIONS=--no-warnings for node",
    }
}

COMMAND_ALTERNATIVES = {
    "rg": ["Select-String", "findstr"],
    "grep": ["Select-String", "findstr"],
    "cat": ["Get-Content", "type"],
    "ls": ["Get-ChildItem", "dir"],
    "rm": ["Remove-Item"],
    "cp": ["Copy-Item"],
    "mv": ["Move-Item"],
    "touch": ["New-Item"],
    "which": ["Get-Command"],
    "curl": ["Invoke-WebRequest", "Invoke-RestMethod"],
    "sed": ["(Get-Content) -replace"],
    "awk": ["Select-Object", "ForEach-Object"],
    "wc": ["Measure-Object"],
}

ENCODING_FIX_HEADER = (
    "import sys\n"
    "sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')\n"
    "sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', errors='replace')\n"
)

# ── Core Error Interceptor Class ─────────────────────────────────────
class ErrorInterceptor:
    """Catches, classifies, repairs, and retries failed commands."""

    def __init__(self):
        self.db_path = REPAIR_DB
        self._init_tables()
        self.error_count = 0
        self.repair_count = 0

    def _init_tables(self):
        """Create error tracking tables if they don't exist."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.execute("""
                CREATE TABLE IF NOT EXISTS error_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT DEFAULT (datetime('now')),
                    command TEXT,
                    error_output TEXT,
                    error_class TEXT,
                    pattern_matched TEXT,
                    repair_action TEXT,
                    repaired_command TEXT,
                    repair_success INTEGER DEFAULT 0,
                    retries INTEGER DEFAULT 0,
                    notes TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS error_prevention_rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    error_class TEXT UNIQUE,
                    occurrences INTEGER DEFAULT 0,
                    last_seen TEXT,
                    prevention_rule TEXT,
                    auto_fix_enabled INTEGER DEFAULT 1
                )
            """)
            conn.commit()
            conn.close()
        except Exception:
            pass  # Watchdog DB might not exist yet

    def classify_error(self, error_output: str) -> list:
        """Classify an error by matching against known patterns.
        Returns list of (error_class, match_groups, fix_function, description)."""
        matches = []
        for pattern, err_class, fix_func, desc in ERROR_PATTERNS:
            m = re.search(pattern, error_output, re.IGNORECASE)
            if m:
                matches.append({
                    "error_class": err_class,
                    "match": m.group(0),
                    "groups": m.groups(),
                    "fix_function": fix_func,
                    "description": desc
                })
        return matches

    def generate_repair(self, command: str, error_output: str, error_info: dict) -> dict:
        """Generate a repair action for the given error.
        Returns dict with 'repaired_command', 'explanation', 'confidence'."""
        fix_func = error_info.get("fix_function", "")
        handler = getattr(self, fix_func, None)
        if handler:
            return handler(command, error_output, error_info)
        return {"repaired_command": None, "explanation": "No auto-fix available", "confidence": 0}

    def intercept_and_repair(self, command: str, error_output: str) -> dict:
        """Main entry point: classify error, generate repair, log it."""
        self.error_count += 1
        classifications = self.classify_error(error_output)

        if not classifications:
            self._log_error(command, error_output, "unclassified", "", "", None, False)
            return {
                "classified": False,
                "error_class": "unclassified",
                "repair": None,
                "explanation": "Error not in known pattern database"
            }

        # Use first (most specific) match
        best = classifications[0]
        repair = self.generate_repair(command, error_output, best)

        success = repair.get("repaired_command") is not None
        if success:
            self.repair_count += 1

        self._log_error(
            command, error_output,
            best["error_class"], best["match"],
            best["fix_function"],
            repair.get("repaired_command"),
            success
        )

        return {
            "classified": True,
            "error_class": best["error_class"],
            "description": best["description"],
            "repair": repair,
            "all_matches": classifications
        }

    def _log_error(self, command, error_output, error_class, pattern,
                   repair_action, repaired_command, success):
        """Log error event to DB and JSONL."""
        # JSONL log (always works)
        entry = {
            "timestamp": datetime.now().isoformat(),
            "command": command[:500],
            "error_class": error_class,
            "pattern": pattern[:200] if pattern else "",
            "repair_action": repair_action,
            "repaired_command": repaired_command[:500] if repaired_command else None,
            "success": success
        }
        try:
            with open(ERROR_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception:
            pass

        # DB log
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.execute("""
                INSERT INTO error_events
                (command, error_output, error_class, pattern_matched,
                 repair_action, repaired_command, repair_success)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (command[:1000], error_output[:2000], error_class,
                  pattern[:500], repair_action, repaired_command, int(success)))
            conn.execute("""
                INSERT INTO error_prevention_rules (error_class, occurrences, last_seen, prevention_rule)
                VALUES (?, 1, datetime('now'), ?)
                ON CONFLICT(error_class) DO UPDATE SET
                    occurrences = occurrences + 1,
                    last_seen = datetime('now')
            """, (error_class, f"Auto-fix: {repair_action}"))
            conn.commit()
            conn.close()
        except Exception:
            pass

    # ── Fix Functions ────────────────────────────────────────────────

    def fix_git_unknown_option(self, command, error_output, error_info):
        """Fix git commands with flags in wrong position."""
        bad_flag = error_info["groups"][0] if error_info["groups"] else ""

        if bad_flag in GIT_FLAG_FIXES:
            info = GIT_FLAG_FIXES[bad_flag]
            if "valid_subcommands" in info:
                # Move the flag after the subcommand
                # Parse: git [--global-flags] <subcommand> [--sub-flags]
                parts = command.split()
                if bad_flag in parts:
                    parts.remove(bad_flag)
                    # Find the subcommand position
                    sub_idx = None
                    for i, p in enumerate(parts):
                        if not p.startswith("-") and p != "git":
                            sub_idx = i
                            break
                    if sub_idx is not None:
                        parts.insert(sub_idx + 1, bad_flag)
                        repaired = " ".join(parts)
                        return {
                            "repaired_command": repaired,
                            "explanation": f"Moved {bad_flag} after subcommand (was before)",
                            "confidence": 0.9
                        }

        # Generic: try removing the bad flag
        if bad_flag:
            repaired = command.replace(f" {bad_flag}", "").replace(f"{bad_flag} ", "")
            return {
                "repaired_command": repaired,
                "explanation": f"Removed unrecognized flag {bad_flag}",
                "confidence": 0.6
            }

        return {"repaired_command": None, "explanation": "Cannot determine fix", "confidence": 0}

    def fix_git_not_repo(self, command, error_output, error_info):
        """Fix commands run outside a git repo."""
        return {
            "repaired_command": None,
            "explanation": "Not in a git repository. cd to a repo first, or use -C <path>",
            "confidence": 0,
            "suggestion": "Wrap with: git -C <repo_path> <subcommand>"
        }

    def fix_git_no_commits(self, command, error_output, error_info):
        """Fix git commands on empty repos."""
        return {
            "repaired_command": None,
            "explanation": "Repository has no commits yet. Run git commit first.",
            "confidence": 0
        }

    def fix_command_not_found(self, command, error_output, error_info):
        """Suggest alternative commands for missing tools."""
        missing_cmd = error_info["groups"][0] if error_info["groups"] else ""
        # Strip quotes and path
        missing_cmd = missing_cmd.strip("'\"").split("\\")[-1].split("/")[-1]

        if missing_cmd in COMMAND_ALTERNATIVES:
            alts = COMMAND_ALTERNATIVES[missing_cmd]
            repaired = command.replace(missing_cmd, alts[0], 1)
            return {
                "repaired_command": repaired,
                "explanation": f"'{missing_cmd}' not found. Using '{alts[0]}' instead.",
                "confidence": 0.7,
                "alternatives": alts
            }
        return {
            "repaired_command": None,
            "explanation": f"'{missing_cmd}' is not available. Install it or use a PowerShell equivalent.",
            "confidence": 0
        }

    def fix_ps_syntax(self, command, error_output, error_info):
        """Fix PowerShell syntax errors (usually string escaping)."""
        return {
            "repaired_command": None,
            "explanation": "PowerShell string escaping issue. Write code to a .py file and execute it instead of inline.",
            "confidence": 0,
            "suggestion": "Use safe_exec.py safe_python() to avoid PS escaping problems"
        }

    def fix_ps_null_param(self, command, error_output, error_info):
        """Fix null parameter errors."""
        param = error_info["groups"][0] if error_info["groups"] else "unknown"
        return {
            "repaired_command": None,
            "explanation": f"Parameter '{param}' is null. Add null check: if ($var) {{ ... }}",
            "confidence": 0.3
        }

    def fix_path_not_found(self, command, error_output, error_info):
        """Fix path not found errors."""
        return {
            "repaired_command": None,
            "explanation": "Path does not exist. Check spelling, use Test-Path, or create with New-Item/mkdir.",
            "confidence": 0
        }

    def fix_py_write_file(self, command, error_output, error_info):
        """Fix Python inline code issues by suggesting file-based execution."""
        return {
            "repaired_command": None,
            "explanation": "Python inline code has escaping issues. Write to .py file first, then execute.",
            "confidence": 0,
            "suggestion": "Use: python script.py instead of python -c '...'"
        }

    def fix_py_encoding(self, command, error_output, error_info):
        """Fix Python encoding errors on Windows."""
        if "python" in command.lower():
            # Check if it's running a script file
            py_match = re.search(r'python\s+(\S+\.py)', command)
            if py_match:
                script = py_match.group(1)
                return {
                    "repaired_command": command,
                    "explanation": f"Add encoding fix to top of {script}: {ENCODING_FIX_HEADER.strip()}",
                    "confidence": 0.8,
                    "auto_patch": {
                        "file": script,
                        "prepend": ENCODING_FIX_HEADER
                    }
                }
        return {
            "repaired_command": f"$env:PYTHONIOENCODING='utf-8'; {command}",
            "explanation": "Set PYTHONIOENCODING=utf-8 environment variable",
            "confidence": 0.7
        }

    def fix_py_module(self, command, error_output, error_info):
        """Fix missing Python module by suggesting pip install."""
        module = error_info["groups"][0] if error_info["groups"] else "unknown"
        return {
            "repaired_command": f"pip install {module} && {command}",
            "explanation": f"Module '{module}' not installed. Installing with pip.",
            "confidence": 0.8
        }

    def fix_db_locked(self, command, error_output, error_info):
        """Fix database lock by adding retry with timeout."""
        return {
            "repaired_command": command,
            "explanation": "Database is locked. Retry after short delay (another process may be writing).",
            "confidence": 0.9,
            "retry_delay": 3,
            "suggestion": "Add timeout=30 to sqlite3.connect() call"
        }

    def fix_db_no_table(self, command, error_output, error_info):
        """Fix missing table error."""
        table = error_info["groups"][0] if error_info["groups"] else "unknown"
        return {
            "repaired_command": None,
            "explanation": f"Table '{table}' does not exist. Check table name against schema_reference table.",
            "confidence": 0,
            "suggestion": f"Run: SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%{table}%'"
        }

    def fix_db_no_column(self, command, error_output, error_info):
        """Fix missing column error."""
        column = error_info["groups"][0] if error_info["groups"] else "unknown"
        return {
            "repaired_command": None,
            "explanation": f"Column '{column}' not found. Check schema_reference for correct column names.",
            "confidence": 0,
            "suggestion": f"Run: PRAGMA table_info(<table_name>) to see available columns"
        }

    def fix_rg_bad_flag(self, command, error_output, error_info):
        """Fix ripgrep interpreting search pattern as a flag."""
        bad_flag = error_info["groups"][0] if error_info["groups"] else ""
        if bad_flag.startswith("--"):
            # Pattern looks like a flag - need to use -e or -- separator
            repaired = command.replace(bad_flag, f"-e '{bad_flag}'", 1)
            return {
                "repaired_command": repaired,
                "explanation": f"Pattern '{bad_flag}' looks like a flag. Use -e to mark it as pattern, or -- separator.",
                "confidence": 0.9
            }
        return {"repaired_command": None, "explanation": "Unknown rg flag", "confidence": 0}

    def fix_permission_denied(self, command, error_output, error_info):
        """Fix file permission errors."""
        return {
            "repaired_command": None,
            "explanation": "File access denied. Check if file is open in another program, or run as admin.",
            "confidence": 0
        }

    def fix_file_locked(self, command, error_output, error_info):
        """Fix file locked errors."""
        return {
            "repaired_command": command,
            "explanation": "File locked by another process. Retry after delay.",
            "confidence": 0.6,
            "retry_delay": 2
        }

    def fix_disk_full(self, command, error_output, error_info):
        """Handle disk full errors."""
        return {
            "repaired_command": None,
            "explanation": "Disk is full. Free space before retrying.",
            "confidence": 0,
            "suggestion": "Check disk usage with: Get-PSDrive C | Select Used,Free"
        }

    def fix_timeout(self, command, error_output, error_info):
        """Handle timeout errors."""
        return {
            "repaired_command": command,
            "explanation": "Operation timed out. Retry with longer timeout.",
            "confidence": 0.5,
            "retry_delay": 5
        }

    def fix_shell_dead(self, command, error_output, error_info):
        """Handle dead shell session errors."""
        return {
            "repaired_command": command,
            "explanation": "Shell session expired. Start a new session and retry.",
            "confidence": 0.8,
            "new_session_required": True
        }

    def fix_copilot_cli_error(self, command, error_output, error_info):
        """Handle Copilot CLI errors — usually MCP server failures or bad internal commands."""
        return {
            "repaired_command": None,
            "explanation": (
                "Copilot CLI error: likely caused by MCP server crash or timeout. "
                "Check mcp.json config at ~/.copilot/mcp.json. "
                "Common fixes: restart MCP servers, fix DB path, reduce DB size for MCP."
            ),
            "confidence": 0.6,
            "check_mcp_config": True
        }

    def fix_mcp_server_error(self, command, error_output, error_info):
        """Handle MCP server crashes."""
        return {
            "repaired_command": None,
            "explanation": (
                "MCP server failed. The sqlite MCP server may be timing out on the "
                "7.5GB database. Consider: (1) removing sqlite MCP if Copilot has "
                "built-in SQL tools, (2) pointing to a smaller summary DB."
            ),
            "confidence": 0.7,
            "restart_mcp": True
        }

    def fix_npm_error(self, command, error_output, error_info):
        """Handle NPX/NPM errors."""
        return {
            "repaired_command": command,
            "explanation": "NPX/NPM error — may need 'npm cache clean --force' or reinstall.",
            "confidence": 0.4,
        }

    def fix_pipe_eagain(self, command, error_output, error_info):
        """Handle EAGAIN pipe buffer exhaustion with exponential backoff retry.

        Root cause: Too many concurrent processes writing to stdin/stdout pipes.
        The OS pipe buffer (64KB on Windows) fills up when multiple agents run
        simultaneously. Node.js gets EAGAIN on non-blocking write() calls.

        Fix strategy:
        1. Wait with exponential backoff (0.5s, 1s, 2s, 4s)
        2. Reduce concurrent agent count (max 2 background agents)
        3. Retry the command after buffer drains
        4. If persistent, kill idle MCP server processes to free pipe resources
        """
        retry_count = error_info.get("retry_count", 0)
        backoff = min(0.5 * (2 ** retry_count), 8.0)  # 0.5, 1, 2, 4, 8 max

        repair = {
            "repaired_command": command,
            "explanation": (
                f"EAGAIN: Pipe buffer full. Retrying after {backoff}s backoff "
                f"(attempt {retry_count + 1}/{MAX_RETRIES}). "
                "Root cause: too many concurrent processes saturating pipe buffers. "
                "Reduce background agents to max 2 simultaneously."
            ),
            "confidence": 0.85,
            "retry_delay": backoff,
            "max_concurrent_agents": 2,
            "pipe_exhaustion": True,
        }

        # On 2nd+ retry, suggest killing idle node processes
        if retry_count >= 2:
            repair["kill_idle_mcp"] = True
            repair["explanation"] += (
                " Consider killing idle MCP/node processes to free pipe resources."
            )

        return repair

    def fix_pipe_broken(self, command, error_output, error_info):
        """Handle broken pipe — downstream process died."""
        return {
            "repaired_command": command,
            "explanation": (
                "Broken pipe: The receiving process closed its end. "
                "This usually means an MCP server or child process crashed. "
                "Restart the session and retry with smaller output."
            ),
            "confidence": 0.7,
            "new_session_required": True,
            "restart_mcp": True,
        }

    def fix_fd_exhaustion(self, command, error_output, error_info):
        """Handle too many open files / file descriptor exhaustion."""
        return {
            "repaired_command": command,
            "explanation": (
                "File descriptor limit reached. Too many open files/pipes/sockets. "
                "Fix: close unused DB connections, reduce concurrent agents, "
                "or increase system ulimit/handle limit."
            ),
            "confidence": 0.6,
            "reduce_concurrency": True,
        }

    # ── Copilot Health Check ────────────────────────────────────────

    def check_copilot_health(self) -> dict:
        """Check Copilot CLI process health: memory, CPU, uptime, MCP node count."""
        result = {
            "status": "unknown",
            "memory_mb": 0,
            "cpu_seconds": 0,
            "uptime_seconds": 0,
            "node_count": 0,
            "warnings": [],
        }

        if HAS_PSUTIL:
            # Find copilot.exe process
            copilot_proc = None
            node_count = 0
            for proc in psutil.process_iter(["name", "pid", "memory_info", "cpu_times", "create_time"]):
                try:
                    name = (proc.info["name"] or "").lower()
                    if "copilot" in name and name.endswith(".exe"):
                        copilot_proc = proc
                    if name in ("node.exe", "node"):
                        node_count += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            result["node_count"] = node_count

            if copilot_proc:
                try:
                    mem = copilot_proc.info["memory_info"]
                    cpu = copilot_proc.info["cpu_times"]
                    create_time = copilot_proc.info["create_time"]
                    result["memory_mb"] = round(mem.rss / (1024 * 1024), 1)
                    result["cpu_seconds"] = round((cpu.user or 0) + (cpu.system or 0), 1)
                    result["uptime_seconds"] = round(time.time() - create_time, 0)
                    result["status"] = "running"

                    if result["memory_mb"] > 2048:
                        result["warnings"].append(f"HIGH MEMORY: {result['memory_mb']}MB (>2GB)")
                    if node_count > 10:
                        result["warnings"].append(f"Many node processes: {node_count} (possible MCP leak)")
                except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                    result["status"] = "error"
                    result["warnings"].append(f"Could not read process info: {e}")
            else:
                result["status"] = "not_found"
                result["warnings"].append("copilot.exe process not found")
        else:
            # Fallback without psutil — use subprocess
            try:
                out = subprocess.run(
                    ["tasklist", "/FI", "IMAGENAME eq copilot.exe", "/FO", "CSV", "/NH"],
                    capture_output=True, text=True, timeout=10
                )
                lines = [l for l in out.stdout.strip().split("\n") if "copilot" in l.lower()]
                if lines:
                    result["status"] = "running"
                    # Parse CSV: "copilot.exe","PID","Console","1","mem K"
                    parts = lines[0].replace('"', '').split(",")
                    if len(parts) >= 5:
                        mem_str = parts[4].strip().replace(" K", "").replace(",", "")
                        try:
                            result["memory_mb"] = round(int(mem_str) / 1024, 1)
                        except ValueError:
                            pass
                        if result["memory_mb"] > 2048:
                            result["warnings"].append(f"HIGH MEMORY: {result['memory_mb']}MB (>2GB)")
                else:
                    result["status"] = "not_found"

                # Count node.exe processes
                out2 = subprocess.run(
                    ["tasklist", "/FI", "IMAGENAME eq node.exe", "/FO", "CSV", "/NH"],
                    capture_output=True, text=True, timeout=10
                )
                node_lines = [l for l in out2.stdout.strip().split("\n") if "node" in l.lower()]
                result["node_count"] = len(node_lines)
            except Exception as e:
                result["status"] = "error"
                result["warnings"].append(f"Fallback check failed: {e}")

        if not result["warnings"]:
            result["status"] = result.get("status", "unknown")

        return result

    # ── Reporting ────────────────────────────────────────────────────

    def get_stats(self) -> dict:
        """Get error/repair statistics."""
        stats = {"total_errors": 0, "total_repairs": 0, "by_class": {}}
        try:
            conn = sqlite3.connect(str(self.db_path))
            rows = conn.execute("""
                SELECT error_class, COUNT(*) as cnt,
                       SUM(repair_success) as fixed,
                       MAX(timestamp) as last_seen
                FROM error_events GROUP BY error_class
                ORDER BY cnt DESC
            """).fetchall()
            for cls, cnt, fixed, last in rows:
                stats["total_errors"] += cnt
                stats["total_repairs"] += (fixed or 0)
                stats["by_class"][cls] = {
                    "count": cnt, "fixed": fixed or 0, "last_seen": last
                }
            conn.close()
        except Exception:
            pass
        return stats

    def get_prevention_rules(self) -> list:
        """Get all active prevention rules."""
        rules = []
        try:
            conn = sqlite3.connect(str(self.db_path))
            rows = conn.execute("""
                SELECT error_class, occurrences, last_seen, prevention_rule, auto_fix_enabled
                FROM error_prevention_rules ORDER BY occurrences DESC
            """).fetchall()
            for cls, occ, last, rule, enabled in rows:
                rules.append({
                    "error_class": cls, "occurrences": occ,
                    "last_seen": last, "rule": rule, "enabled": bool(enabled)
                })
            conn.close()
        except Exception:
            pass
        return rules


# ── Safe Execute with Interception ───────────────────────────────────
def safe_execute(command: str, cwd: str = None, timeout: int = 120,
                 max_retries: int = MAX_RETRIES) -> dict:
    """Execute a command with automatic error interception and repair.
    
    Returns:
        dict with keys: success, output, error, retries, repairs, command_used
    """
    interceptor = ErrorInterceptor()
    current_cmd = command
    repairs = []

    for attempt in range(max_retries + 1):
        try:
            result = subprocess.run(
                current_cmd, shell=True, capture_output=True,
                text=True, cwd=cwd, timeout=timeout,
                encoding='utf-8', errors='replace'
            )

            if result.returncode == 0:
                return {
                    "success": True,
                    "output": result.stdout,
                    "error": result.stderr,
                    "retries": attempt,
                    "repairs": repairs,
                    "command_used": current_cmd
                }

            # Error occurred - try to intercept and repair
            error_text = (result.stderr or "") + (result.stdout or "")
            diagnosis = interceptor.intercept_and_repair(current_cmd, error_text)

            if diagnosis["classified"] and diagnosis["repair"]:
                repair = diagnosis["repair"]
                repairs.append({
                    "attempt": attempt,
                    "error_class": diagnosis["error_class"],
                    "repair": repair["explanation"],
                    "confidence": repair.get("confidence", 0)
                })

                if repair.get("repaired_command") and repair.get("confidence", 0) >= 0.5:
                    # Apply the fix and retry
                    delay = repair.get("retry_delay", 1)
                    time.sleep(delay)
                    current_cmd = repair["repaired_command"]
                    continue
                else:
                    # Can't auto-fix, return with diagnosis
                    return {
                        "success": False,
                        "output": result.stdout,
                        "error": error_text,
                        "retries": attempt,
                        "repairs": repairs,
                        "command_used": current_cmd,
                        "diagnosis": diagnosis
                    }
            else:
                # Unclassified error
                return {
                    "success": False,
                    "output": result.stdout,
                    "error": error_text,
                    "retries": attempt,
                    "repairs": repairs,
                    "command_used": current_cmd,
                    "diagnosis": diagnosis
                }

        except subprocess.TimeoutExpired:
            repairs.append({"attempt": attempt, "error_class": "timeout",
                          "repair": "Command timed out", "confidence": 0})
            if attempt < max_retries:
                timeout = int(timeout * 1.5)  # Increase timeout
                continue
            return {
                "success": False, "output": "", "error": f"Timed out after {timeout}s",
                "retries": attempt, "repairs": repairs, "command_used": current_cmd
            }

        except Exception as e:
            return {
                "success": False, "output": "", "error": str(e),
                "retries": attempt, "repairs": repairs, "command_used": current_cmd
            }

    return {
        "success": False, "output": "", "error": "Max retries exceeded",
        "retries": max_retries, "repairs": repairs, "command_used": current_cmd
    }


# ── CLI Interface ────────────────────────────────────────────────────
def main():
    if len(sys.argv) < 2:
        print("Error Interceptor & Auto-Repair Engine")
        print("Usage:")
        print("  python error_interceptor.py diagnose <error_text>")
        print("  python error_interceptor.py execute <command>")
        print("  python error_interceptor.py stats")
        print("  python error_interceptor.py rules")
        print("  python error_interceptor.py test")
        return

    cmd = sys.argv[1]

    if cmd == "diagnose":
        error_text = " ".join(sys.argv[2:])
        interceptor = ErrorInterceptor()
        matches = interceptor.classify_error(error_text)
        if matches:
            for m in matches:
                print(f"  Class: {m['error_class']}")
                print(f"  Match: {m['match']}")
                print(f"  Description: {m['description']}")
                print(f"  Fix function: {m['fix_function']}")
                print()
        else:
            print("  No known error pattern matched.")

    elif cmd == "execute":
        command = " ".join(sys.argv[2:])
        result = safe_execute(command)
        print(f"Success: {result['success']}")
        print(f"Retries: {result['retries']}")
        if result['repairs']:
            print(f"Repairs attempted: {len(result['repairs'])}")
            for r in result['repairs']:
                print(f"  [{r['attempt']}] {r['error_class']}: {r['repair']}")
        if result['output']:
            print(f"Output: {result['output'][:500]}")
        if not result['success'] and result.get('error'):
            print(f"Error: {result['error'][:500]}")

    elif cmd == "stats":
        interceptor = ErrorInterceptor()
        stats = interceptor.get_stats()
        print(f"Total errors: {stats['total_errors']}")
        print(f"Total repairs: {stats['total_repairs']}")
        if stats['by_class']:
            print("\nBy class:")
            for cls, info in stats['by_class'].items():
                print(f"  {cls}: {info['count']} errors, {info['fixed']} fixed, last: {info['last_seen']}")

    elif cmd == "rules":
        interceptor = ErrorInterceptor()
        rules = interceptor.get_prevention_rules()
        if rules:
            for r in rules:
                status = "ON" if r['enabled'] else "OFF"
                print(f"  [{status}] {r['error_class']}: {r['occurrences']}x, rule: {r['rule']}")
        else:
            print("  No prevention rules yet.")

    elif cmd == "test":
        print("Running error interceptor self-test...")
        interceptor = ErrorInterceptor()

        tests = [
            ("unknown option: --no-walk", "git_unknown_option"),
            ("error: unknown option '--no-warn'", "git_unknown_option"),
            ("The term 'rg' is not recognized", "command_not_found"),
            ("SyntaxError: unterminated string literal", "py_syntax"),
            ("UnicodeDecodeError: 'utf-8' codec", "py_encoding"),
            ("ModuleNotFoundError: No module named 'pandas'", "py_module"),
            ("sqlite3.OperationalError: database is locked", "db_locked"),
            ("sqlite3.OperationalError: no such table: fake_table", "db_no_table"),
            ("rg: unrecognized flag --no-walk", "rg_bad_flag"),
            ("Invalid shell ID", "shell_dead"),
            ("not a git repository", "git_not_repo"),
            ("There is not enough space on the disk", "disk_full"),
        ]

        passed = 0
        for error_text, expected_class in tests:
            matches = interceptor.classify_error(error_text)
            if matches and matches[0]["error_class"] == expected_class:
                passed += 1
                print(f"  PASS: '{error_text[:50]}...' → {expected_class}")
            else:
                got = matches[0]["error_class"] if matches else "NONE"
                print(f"  FAIL: '{error_text[:50]}...' → expected {expected_class}, got {got}")

        print(f"\n  {passed}/{len(tests)} tests passed")

        # Test repair generation
        print("\nTesting repairs...")
        result = interceptor.intercept_and_repair(
            "git --no-walk log --oneline",
            "unknown option: --no-walk"
        )
        if result["classified"] and result["repair"]["repaired_command"]:
            print(f"  PASS: Repaired to: {result['repair']['repaired_command']}")
        else:
            print(f"  FAIL: Could not repair")

        result2 = interceptor.intercept_and_repair(
            "rg --no-walk pattern .",
            "rg: unrecognized flag --no-walk"
        )
        if result2["classified"]:
            print(f"  PASS: Diagnosed rg error: {result2['repair']['explanation']}")

        print("\nSelf-test complete.")


if __name__ == "__main__":
    main()
