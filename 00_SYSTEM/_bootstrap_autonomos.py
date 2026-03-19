#!/usr/bin/env python3
"""
AUTONOMOS Bootstrap — Run this ONCE from any terminal to fix the shell infrastructure.

Usage:
    cd C:\Users\andre\LitigationOS
    python 00_SYSTEM\_bootstrap_autonomos.py

What it does:
    1. Creates all AUTONOMOS directory tree
    2. Installs Python watchdog package (for filesystem monitoring)
    3. Creates the File-Based Command Server
    4. Creates __init__.py package files
    5. Starts the command server (optional, with --start-server)
    6. Verifies everything works

This script requires NO PowerShell — it uses only Python stdlib.
"""
import sys
import os
import subprocess
import json
import hashlib
import time
from pathlib import Path
from datetime import datetime

# ── UTF-8 fix ────────────────────────────────────────────────────────
if sys.platform == "win32":
    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')
    sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', errors='replace')

# ── Constants ────────────────────────────────────────────────────────
LITIGOS_ROOT = Path(r"C:\Users\andre\LitigationOS")
SYSTEM_DIR = LITIGOS_ROOT / "00_SYSTEM"
AUTONOMOS_ROOT = SYSTEM_DIR / "autonomos"
WATCHDOG_DIR = SYSTEM_DIR / "watchdog"

DIRECTORIES = [
    AUTONOMOS_ROOT,
    AUTONOMOS_ROOT / "sentinel",
    AUTONOMOS_ROOT / "inquisitor",
    AUTONOMOS_ROOT / "shared",
    AUTONOMOS_ROOT / "db",
    AUTONOMOS_ROOT / "tests",
    AUTONOMOS_ROOT / ".inbox",
    AUTONOMOS_ROOT / ".outbox",
    AUTONOMOS_ROOT / ".archive",
]

PACKAGES = [
    AUTONOMOS_ROOT,
    AUTONOMOS_ROOT / "sentinel",
    AUTONOMOS_ROOT / "inquisitor",
    AUTONOMOS_ROOT / "shared",
]

REQUIRED_PACKAGES = ["watchdog"]


def banner(msg: str):
    """Print a visible banner."""
    print(f"\n{'='*60}")
    print(f"  {msg}")
    print(f"{'='*60}")


def step(n: int, msg: str):
    """Print a step indicator."""
    print(f"\n[{n}/6] {msg}...")


# ── Step 1: Create Directories ──────────────────────────────────────
def create_directories():
    step(1, "Creating AUTONOMOS directory tree")
    created = 0
    for d in DIRECTORIES:
        if not d.exists():
            d.mkdir(parents=True, exist_ok=True)
            print(f"  ✓ Created: {d.relative_to(LITIGOS_ROOT)}")
            created += 1
        else:
            print(f"  · Exists:  {d.relative_to(LITIGOS_ROOT)}")
    print(f"  → {created} directories created, {len(DIRECTORIES) - created} already existed")
    return created


# ── Step 2: Create __init__.py Files ────────────────────────────────
def create_packages():
    step(2, "Creating Python package files")
    created = 0
    for pkg in PACKAGES:
        init_file = pkg / "__init__.py"
        pkg_name = pkg.name if pkg != AUTONOMOS_ROOT else "autonomos"
        if not init_file.exists():
            init_file.write_text(
                f'"""AUTONOMOS — {pkg_name} package."""\n',
                encoding='utf-8'
            )
            print(f"  ✓ Created: {init_file.relative_to(LITIGOS_ROOT)}")
            created += 1
        else:
            print(f"  · Exists:  {init_file.relative_to(LITIGOS_ROOT)}")
    return created


# ── Step 3: Install Dependencies ────────────────────────────────────
def install_dependencies():
    step(3, "Installing Python dependencies")
    for pkg in REQUIRED_PACKAGES:
        try:
            __import__(pkg)
            print(f"  · Already installed: {pkg}")
        except ImportError:
            print(f"  ⟳ Installing: {pkg}")
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", pkg, "--quiet"],
                capture_output=True, text=True, timeout=120,
            )
            if result.returncode == 0:
                print(f"  ✓ Installed: {pkg}")
            else:
                print(f"  ✗ Failed to install {pkg}: {result.stderr[:200]}")
                return False
    return True


# ── Step 4: Create Command Server ───────────────────────────────────
def create_command_server():
    step(4, "Creating File-Based Command Server")
    server_path = AUTONOMOS_ROOT / "shared" / "cmd_server.py"
    if server_path.exists():
        print(f"  · Already exists: {server_path.relative_to(LITIGOS_ROOT)}")
        return True

    server_code = r'''#!/usr/bin/env python3
"""
AUTONOMOS File-Based Command Server v1.0

Watches .inbox/ for .cmd.py files, executes them, writes output to .outbox/.
This enables Copilot to execute commands using ONLY create + view tools.

Protocol:
    1. Copilot creates:  .inbox/001_task_name.cmd.py
    2. Server detects:   Executes the Python file
    3. Server writes:    .outbox/001_task_name.cmd.out (JSON result)
    4. Server archives:  .archive/001_task_name.cmd.py (original)
    5. Copilot reads:    .outbox/001_task_name.cmd.out via view tool

Usage:
    python cmd_server.py              # Run in foreground
    python cmd_server.py --daemon     # Run as background process
    python cmd_server.py --status     # Check if running
    python cmd_server.py --stop       # Stop the server
"""
import sys, os, json, time, subprocess, signal, hashlib, shutil
from pathlib import Path
from datetime import datetime

if sys.platform == "win32":
    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')
    sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', errors='replace')

AUTONOMOS_ROOT = Path(r"C:\Users\andre\LitigationOS\00_SYSTEM\autonomos")
INBOX = AUTONOMOS_ROOT / ".inbox"
OUTBOX = AUTONOMOS_ROOT / ".outbox"
ARCHIVE = AUTONOMOS_ROOT / ".archive"
PID_FILE = AUTONOMOS_ROOT / ".cmd_server.pid"
LOG_FILE = AUTONOMOS_ROOT / ".cmd_server.log"

POLL_INTERVAL = 1.0  # seconds
MAX_EXEC_TIMEOUT = 300  # 5 minutes per command
PYTHON = sys.executable

# UTF-8 header injected into every command file
UTF8_HEADER = (
    "import sys\n"
    "if sys.platform == 'win32':\n"
    "    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')\n"
    "    sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', errors='replace')\n"
)


def log(msg: str):
    """Append to log file."""
    ts = datetime.now().isoformat(timespec='seconds')
    line = f"[{ts}] {msg}\n"
    print(line.rstrip())
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(line)
    except:
        pass


def execute_command(cmd_file: Path) -> dict:
    """Execute a .cmd.py file and return result dict."""
    start = time.time()
    name = cmd_file.stem  # e.g., "001_mkdir"
    
    try:
        # Read the command file
        code = cmd_file.read_text(encoding='utf-8')
        
        # Write to temp file with UTF-8 header
        tmp_file = INBOX / f"_running_{name}.py"
        tmp_file.write_text(UTF8_HEADER + "\n" + code, encoding='utf-8')
        
        # Execute
        result = subprocess.run(
            [PYTHON, str(tmp_file)],
            capture_output=True, text=True,
            timeout=MAX_EXEC_TIMEOUT,
            encoding='utf-8', errors='replace',
            cwd=str(Path(r"C:\Users\andre\LitigationOS")),
            env={**os.environ, "PYTHONIOENCODING": "utf-8"}
        )
        
        duration = round(time.time() - start, 2)
        
        # Clean up temp file
        tmp_file.unlink(missing_ok=True)
        
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "duration": duration,
            "command_file": str(cmd_file.name),
            "timestamp": datetime.now().isoformat(),
        }
        
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"TIMEOUT: Command exceeded {MAX_EXEC_TIMEOUT}s limit",
            "returncode": -1,
            "duration": round(time.time() - start, 2),
            "command_file": str(cmd_file.name),
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": str(e),
            "returncode": -1,
            "duration": round(time.time() - start, 2),
            "command_file": str(cmd_file.name),
            "timestamp": datetime.now().isoformat(),
        }


def process_inbox():
    """Check inbox for .cmd.py files and process them."""
    cmd_files = sorted(INBOX.glob("*.cmd.py"))
    for cmd_file in cmd_files:
        # Skip temp files
        if cmd_file.name.startswith("_running_"):
            continue
            
        log(f"Processing: {cmd_file.name}")
        
        # Execute
        result = execute_command(cmd_file)
        
        # Write output
        out_name = cmd_file.stem + ".cmd.out"
        out_file = OUTBOX / out_name
        out_file.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
        
        # Archive original
        archive_file = ARCHIVE / cmd_file.name
        shutil.move(str(cmd_file), str(archive_file))
        
        status = "✓" if result["success"] else "✗"
        log(f"  {status} {cmd_file.name} → {out_name} ({result['duration']}s)")


def write_pid():
    """Write PID file."""
    PID_FILE.write_text(str(os.getpid()), encoding='utf-8')


def read_pid() -> int:
    """Read PID from file, return 0 if not found."""
    try:
        return int(PID_FILE.read_text().strip())
    except:
        return 0


def is_running() -> bool:
    """Check if server is already running."""
    pid = read_pid()
    if pid == 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        PID_FILE.unlink(missing_ok=True)
        return False


def stop_server():
    """Stop the running server."""
    pid = read_pid()
    if pid and is_running():
        try:
            os.kill(pid, signal.SIGTERM)
            log(f"Sent SIGTERM to PID {pid}")
            time.sleep(1)
            PID_FILE.unlink(missing_ok=True)
        except:
            pass
    else:
        log("Server not running")


def run_server():
    """Main server loop."""
    if is_running():
        log(f"Server already running (PID {read_pid()})")
        return
    
    write_pid()
    log(f"Command Server started (PID {os.getpid()})")
    log(f"  Inbox:   {INBOX}")
    log(f"  Outbox:  {OUTBOX}")
    log(f"  Archive: {ARCHIVE}")
    log(f"  Poll:    {POLL_INTERVAL}s")
    
    running = True
    
    def handle_signal(sig, frame):
        nonlocal running
        log("Shutdown signal received")
        running = False
    
    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)
    
    while running:
        try:
            process_inbox()
            time.sleep(POLL_INTERVAL)
        except KeyboardInterrupt:
            break
        except Exception as e:
            log(f"ERROR: {e}")
            time.sleep(5)
    
    PID_FILE.unlink(missing_ok=True)
    log("Command Server stopped")


def status():
    """Print server status."""
    if is_running():
        pid = read_pid()
        inbox_count = len(list(INBOX.glob("*.cmd.py")))
        outbox_count = len(list(OUTBOX.glob("*.cmd.out")))
        archive_count = len(list(ARCHIVE.glob("*.cmd.py")))
        print(f"Status: RUNNING (PID {pid})")
        print(f"  Inbox:   {inbox_count} pending")
        print(f"  Outbox:  {outbox_count} results")
        print(f"  Archive: {archive_count} completed")
    else:
        print("Status: STOPPED")


if __name__ == "__main__":
    args = sys.argv[1:]
    
    if "--status" in args:
        status()
    elif "--stop" in args:
        stop_server()
    elif "--daemon" in args:
        # Detach and run in background
        if sys.platform == "win32":
            subprocess.Popen(
                [PYTHON, __file__],
                creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            print(f"Command Server started in background")
        else:
            if os.fork() == 0:
                os.setsid()
                run_server()
            else:
                print("Command Server started in background")
    else:
        run_server()
'''
    server_path.write_text(server_code, encoding='utf-8')
    print(f"  ✓ Created: {server_path.relative_to(LITIGOS_ROOT)}")
    return True


# ── Step 5: Create Execution Engine ─────────────────────────────────
def create_exec_engine():
    step(5, "Creating Execution Engine (shell-free command runner)")
    engine_path = AUTONOMOS_ROOT / "shared" / "exec_engine.py"
    if engine_path.exists():
        print(f"  · Already exists: {engine_path.relative_to(LITIGOS_ROOT)}")
        return True

    engine_code = r'''#!/usr/bin/env python3
"""
AUTONOMOS Execution Engine v1.0

Resilient command execution that works WITHOUT PowerShell.
Provides multiple execution strategies with automatic fallback.

Usage:
    from exec_engine import ExecEngine
    engine = ExecEngine()
    
    # Run a shell command
    result = engine.run("dir /b C:\\Users")
    
    # Run Python code
    result = engine.run_python("print('hello')")
    
    # Run a Python file
    result = engine.run_file("C:\\path\\to\\script.py")
    
    # Run SQL against litigation_context.db
    result = engine.run_sql("SELECT COUNT(*) FROM documents")
"""
import sys, os, json, subprocess, tempfile, time, sqlite3, hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional

if sys.platform == "win32":
    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')
    sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', errors='replace')

LITIGOS_ROOT = Path(r"C:\Users\andre\LitigationOS")
SYSTEM_DIR = LITIGOS_ROOT / "00_SYSTEM"
DB_PATH = LITIGOS_ROOT / "litigation_context.db"
EXEC_LOG = SYSTEM_DIR / "autonomos" / ".cmd_server.log"

UTF8_HEADER = (
    "import sys\n"
    "if sys.platform == 'win32':\n"
    "    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')\n"
    "    sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', errors='replace')\n"
)


class ExecResult:
    """Result of a command execution."""
    __slots__ = ('success', 'stdout', 'stderr', 'returncode', 'duration', 'method')
    
    def __init__(self, success, stdout='', stderr='', returncode=0, duration=0.0, method=''):
        self.success = success
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode
        self.duration = duration
        self.method = method
    
    def __bool__(self):
        return self.success
    
    def __repr__(self):
        status = "OK" if self.success else f"FAIL({self.returncode})"
        return f"ExecResult({status}, {self.duration}s, {len(self.stdout)}b stdout)"
    
    def to_dict(self):
        return {
            "success": self.success,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "returncode": self.returncode,
            "duration": self.duration,
            "method": self.method,
        }


class ExecEngine:
    """Resilient command execution engine — no PowerShell required."""
    
    def __init__(self, cwd: str = None, timeout: int = 120, retries: int = 2):
        self.cwd = cwd or str(LITIGOS_ROOT)
        self.timeout = timeout
        self.retries = retries
        self.python = sys.executable
        self.stats = {"commands": 0, "successes": 0, "failures": 0, "total_time": 0.0}
    
    def run(self, command: str, timeout: int = None, cwd: str = None) -> ExecResult:
        """Run a shell command using cmd.exe (not PowerShell)."""
        timeout = timeout or self.timeout
        cwd = cwd or self.cwd
        start = time.time()
        
        for attempt in range(self.retries + 1):
            try:
                result = subprocess.run(
                    command, shell=True, capture_output=True, text=True,
                    timeout=timeout, cwd=cwd,
                    encoding='utf-8', errors='replace',
                    env={**os.environ, "PYTHONIOENCODING": "utf-8"},
                )
                duration = round(time.time() - start, 2)
                self._track(result.returncode == 0, duration)
                return ExecResult(
                    success=result.returncode == 0,
                    stdout=result.stdout,
                    stderr=result.stderr,
                    returncode=result.returncode,
                    duration=duration,
                    method=f"shell(attempt={attempt+1})",
                )
            except subprocess.TimeoutExpired:
                duration = round(time.time() - start, 2)
                if attempt < self.retries:
                    time.sleep(1)
                    continue
                self._track(False, duration)
                return ExecResult(False, '', f'TIMEOUT after {timeout}s', -1, duration, 'shell_timeout')
            except Exception as e:
                duration = round(time.time() - start, 2)
                if attempt < self.retries:
                    time.sleep(1)
                    continue
                self._track(False, duration)
                return ExecResult(False, '', str(e), -1, duration, 'shell_error')
    
    def run_python(self, code: str, timeout: int = None) -> ExecResult:
        """Run Python code via temp file (no escaping issues)."""
        timeout = timeout or self.timeout
        start = time.time()
        tmp_path = None
        
        try:
            fd, tmp_path = tempfile.mkstemp(suffix='.py', prefix='exec_', dir=self.cwd)
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                f.write(UTF8_HEADER + "\n" + code)
            
            result = subprocess.run(
                [self.python, tmp_path],
                capture_output=True, text=True, timeout=timeout,
                cwd=self.cwd, encoding='utf-8', errors='replace',
                env={**os.environ, "PYTHONIOENCODING": "utf-8"},
            )
            duration = round(time.time() - start, 2)
            self._track(result.returncode == 0, duration)
            return ExecResult(
                success=result.returncode == 0,
                stdout=result.stdout,
                stderr=result.stderr,
                returncode=result.returncode,
                duration=duration,
                method='python_tempfile',
            )
        except subprocess.TimeoutExpired:
            duration = round(time.time() - start, 2)
            self._track(False, duration)
            return ExecResult(False, '', f'TIMEOUT after {timeout}s', -1, duration, 'python_timeout')
        except Exception as e:
            duration = round(time.time() - start, 2)
            self._track(False, duration)
            return ExecResult(False, '', str(e), -1, duration, 'python_error')
        finally:
            if tmp_path:
                try:
                    os.unlink(tmp_path)
                except:
                    pass
    
    def run_file(self, filepath: str, timeout: int = None) -> ExecResult:
        """Run a Python file directly."""
        timeout = timeout or self.timeout
        start = time.time()
        
        try:
            result = subprocess.run(
                [self.python, filepath],
                capture_output=True, text=True, timeout=timeout,
                cwd=self.cwd, encoding='utf-8', errors='replace',
                env={**os.environ, "PYTHONIOENCODING": "utf-8"},
            )
            duration = round(time.time() - start, 2)
            self._track(result.returncode == 0, duration)
            return ExecResult(
                success=result.returncode == 0,
                stdout=result.stdout,
                stderr=result.stderr,
                returncode=result.returncode,
                duration=duration,
                method='python_file',
            )
        except Exception as e:
            duration = round(time.time() - start, 2)
            self._track(False, duration)
            return ExecResult(False, '', str(e), -1, duration, 'file_error')
    
    def run_sql(self, query: str, db_path: str = None) -> ExecResult:
        """Run SQL query against a SQLite database."""
        db_path = db_path or str(DB_PATH)
        start = time.time()
        
        try:
            conn = sqlite3.connect(db_path, timeout=30)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=30000")
            cursor = conn.execute(query)
            
            if query.strip().upper().startswith("SELECT"):
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                rows = cursor.fetchall()
                result_data = {"columns": columns, "rows": [list(r) for r in rows], "count": len(rows)}
                stdout = json.dumps(result_data, indent=2, ensure_ascii=False, default=str)
            else:
                conn.commit()
                stdout = json.dumps({"affected_rows": cursor.rowcount})
            
            conn.close()
            duration = round(time.time() - start, 2)
            self._track(True, duration)
            return ExecResult(True, stdout, '', 0, duration, 'sqlite')
        except Exception as e:
            duration = round(time.time() - start, 2)
            self._track(False, duration)
            return ExecResult(False, '', str(e), -1, duration, 'sqlite_error')
    
    def mkdir(self, *paths: str) -> ExecResult:
        """Create directories (pure Python, no shell needed)."""
        start = time.time()
        created = []
        errors = []
        for p in paths:
            try:
                Path(p).mkdir(parents=True, exist_ok=True)
                created.append(p)
            except Exception as e:
                errors.append(f"{p}: {e}")
        
        duration = round(time.time() - start, 2)
        success = len(errors) == 0
        stdout = json.dumps({"created": created, "errors": errors})
        self._track(success, duration)
        return ExecResult(success, stdout, '\n'.join(errors), 0 if success else 1, duration, 'mkdir')
    
    def _track(self, success: bool, duration: float):
        """Track execution stats."""
        self.stats["commands"] += 1
        self.stats["total_time"] += duration
        if success:
            self.stats["successes"] += 1
        else:
            self.stats["failures"] += 1


# ── Convenience Functions ────────────────────────────────────────────
_engine = None

def get_engine() -> ExecEngine:
    """Get or create the singleton engine."""
    global _engine
    if _engine is None:
        _engine = ExecEngine()
    return _engine

def run(command: str, **kwargs) -> ExecResult:
    return get_engine().run(command, **kwargs)

def run_python(code: str, **kwargs) -> ExecResult:
    return get_engine().run_python(code, **kwargs)

def run_file(filepath: str, **kwargs) -> ExecResult:
    return get_engine().run_file(filepath, **kwargs)

def run_sql(query: str, **kwargs) -> ExecResult:
    return get_engine().run_sql(query, **kwargs)

def mkdir(*paths: str) -> ExecResult:
    return get_engine().mkdir(*paths)


if __name__ == "__main__":
    # Self-test
    engine = ExecEngine()
    print("ExecEngine Self-Test")
    print("=" * 40)
    
    # Test 1: Shell command
    r = engine.run("echo hello_from_exec_engine")
    print(f"1. Shell:  {r}")
    
    # Test 2: Python code
    r = engine.run_python("import os; print(f'PID={os.getpid()}, CWD={os.getcwd()}')")
    print(f"2. Python: {r}")
    
    # Test 3: mkdir
    test_dir = str(SYSTEM_DIR / "autonomos" / "tests" / "_selftest")
    r = engine.mkdir(test_dir)
    print(f"3. Mkdir:  {r}")
    
    # Test 4: SQL
    r = engine.run_sql("SELECT COUNT(*) as cnt FROM sqlite_master", db_path=":memory:")
    print(f"4. SQL:    {r}")
    
    # Cleanup
    try:
        Path(test_dir).rmdir()
    except:
        pass
    
    print(f"\nStats: {engine.stats}")
    print("All tests passed!" if engine.stats["failures"] == 0 else "Some tests failed!")
'''
    engine_path.write_text(engine_code, encoding='utf-8')
    print(f"  ✓ Created: {engine_path.relative_to(LITIGOS_ROOT)}")
    return True


# ── Step 6: Verify Everything ───────────────────────────────────────
def verify():
    step(6, "Verifying installation")
    issues = []
    
    # Check directories
    for d in DIRECTORIES:
        if not d.exists():
            issues.append(f"Missing directory: {d}")
    
    # Check packages
    for pkg in PACKAGES:
        init_file = pkg / "__init__.py"
        if not init_file.exists():
            issues.append(f"Missing __init__.py: {init_file}")
    
    # Check key files
    key_files = [
        AUTONOMOS_ROOT / "shared" / "cmd_server.py",
        AUTONOMOS_ROOT / "shared" / "exec_engine.py",
    ]
    for f in key_files:
        if not f.exists():
            issues.append(f"Missing file: {f}")
    
    # Check watchdog package
    try:
        import watchdog
        print(f"  ✓ watchdog package: v{watchdog.__version__ if hasattr(watchdog, '__version__') else 'installed'}")
    except ImportError:
        issues.append("watchdog package not installed")
    
    if issues:
        print(f"\n  ✗ {len(issues)} issues found:")
        for issue in issues:
            print(f"    - {issue}")
        return False
    else:
        print("  ✓ All checks passed!")
        return True


# ── Main ─────────────────────────────────────────────────────────────
def main():
    banner("AUTONOMOS Bootstrap — LitigationOS Shell Infrastructure Fix")
    print(f"  Root: {LITIGOS_ROOT}")
    print(f"  Time: {datetime.now().isoformat(timespec='seconds')}")
    
    # Run all steps
    create_directories()
    create_packages()
    deps_ok = install_dependencies()
    create_command_server()
    create_exec_engine()
    all_ok = verify()
    
    # Summary
    banner("Bootstrap Complete!")
    if all_ok:
        print("  ✓ All systems operational")
        print()
        print("  Next steps:")
        print("  1. Start command server (optional):")
        print("     python 00_SYSTEM\\autonomos\\shared\\cmd_server.py --daemon")
        print()
        print("  2. Test exec engine:")
        print("     python 00_SYSTEM\\autonomos\\shared\\exec_engine.py")
        print()
        print("  3. Return to Copilot and say: 'shell fix complete, resume work'")
    else:
        print("  ⚠ Some issues found — see above")
        print("  Fix the issues and re-run this script")
    
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
