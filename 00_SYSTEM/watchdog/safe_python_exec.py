"""
SAFE PYTHON EXEC — LitigationOS Watchdog
=========================================
Eliminates PowerShell escaping errors by writing Python code to temp files,
executing with subprocess, capturing output, and cleaning up.
The #1 cause of shell errors in Copilot sessions is PS inline Python escaping.
"""

import sys
import os
import json
import time
import sqlite3
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

# ── UTF-8 fix for Windows ────────────────────────────────────────────
if sys.platform == "win32":
    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')
    sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', errors='replace')

# ── Constants ────────────────────────────────────────────────────────
WATCHDOG_DIR = Path(__file__).parent
DEFAULT_DB = Path(r"C:\Users\andre\LitigationOS\litigation_context.db")
EXEC_LOG = WATCHDOG_DIR / "exec_log.jsonl"

UTF8_HEADER = (
    "import sys\n"
    "if sys.platform == 'win32':\n"
    "    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')\n"
    "    sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', errors='replace')\n"
)


# ── Logging ──────────────────────────────────────────────────────────
def _log_exec(code_snippet: str, result: dict):
    """Append execution record to exec_log.jsonl."""
    try:
        entry = {
            "timestamp": datetime.now().isoformat(),
            "code_snippet": code_snippet[:200],
            "success": result.get("success", False),
            "returncode": result.get("returncode", -1),
            "duration": result.get("duration", 0),
        }
        with open(EXEC_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass


# ── Core Functions ───────────────────────────────────────────────────
def run_python(code: str, timeout: int = 300) -> dict:
    """Execute Python code safely via temp file. Returns {success, stdout, stderr, returncode, duration}."""
    tmp_path = None
    start = time.time()
    try:
        # Write code to temp file with UTF-8 header
        fd, tmp_path = tempfile.mkstemp(suffix=".py", prefix="safe_exec_", dir=str(WATCHDOG_DIR))
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(UTF8_HEADER)
            f.write("\n")
            f.write(code)

        # Execute
        result = subprocess.run(
            [sys.executable, tmp_path],
            capture_output=True, text=True, timeout=timeout,
            encoding="utf-8", errors="replace",
            cwd=str(Path(r"C:\Users\andre\LitigationOS")),
            env={**os.environ, "PYTHONIOENCODING": "utf-8"}
        )
        duration = round(time.time() - start, 2)

        out = {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "duration": duration,
        }
        _log_exec(code[:200], out)
        return out

    except subprocess.TimeoutExpired:
        duration = round(time.time() - start, 2)
        out = {"success": False, "stdout": "", "stderr": f"Timed out after {timeout}s",
               "returncode": -1, "duration": duration}
        _log_exec(code[:200], out)
        return out
    except Exception as e:
        duration = round(time.time() - start, 2)
        out = {"success": False, "stdout": "", "stderr": str(e),
               "returncode": -1, "duration": duration}
        _log_exec(code[:200], out)
        return out
    finally:
        # Clean up temp file
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except Exception:
                pass


def run_python_file(filepath: str, timeout: int = 300) -> dict:
    """Execute an existing .py file. Returns {success, stdout, stderr, returncode, duration}."""
    filepath = Path(filepath)
    if not filepath.exists():
        return {"success": False, "stdout": "", "stderr": f"File not found: {filepath}",
                "returncode": -1, "duration": 0}

    start = time.time()
    try:
        result = subprocess.run(
            [sys.executable, str(filepath)],
            capture_output=True, text=True, timeout=timeout,
            encoding="utf-8", errors="replace",
            cwd=str(filepath.parent),
            env={**os.environ, "PYTHONIOENCODING": "utf-8"}
        )
        duration = round(time.time() - start, 2)
        out = {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "duration": duration,
        }
        _log_exec(f"file:{filepath.name}", out)
        return out
    except subprocess.TimeoutExpired:
        duration = round(time.time() - start, 2)
        return {"success": False, "stdout": "", "stderr": f"Timed out after {timeout}s",
                "returncode": -1, "duration": duration}
    except Exception as e:
        duration = round(time.time() - start, 2)
        return {"success": False, "stdout": "", "stderr": str(e),
                "returncode": -1, "duration": duration}


def run_sql(query: str, db_path: str = None) -> dict:
    """Run a SQL query against SQLite and return results as list of dicts."""
    db = Path(db_path) if db_path else DEFAULT_DB
    if not db.exists():
        return {"success": False, "error": f"Database not found: {db}", "results": [], "count": 0}

    start = time.time()
    try:
        conn = sqlite3.connect(str(db), timeout=30)
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(query)
        rows = cursor.fetchall()
        results = [dict(row) for row in rows]
        conn.commit()
        conn.close()
        duration = round(time.time() - start, 2)
        return {"success": True, "results": results, "count": len(results),
                "duration": duration, "error": None}
    except Exception as e:
        duration = round(time.time() - start, 2)
        return {"success": False, "results": [], "count": 0,
                "duration": duration, "error": str(e)}


# ── CLI ──────────────────────────────────────────────────────────────
def main():
    if len(sys.argv) < 2:
        print("Safe Python Exec — LitigationOS Watchdog")
        print("Usage:")
        print('  python safe_python_exec.py "print(\'hello\')"       — Run inline Python')
        print("  python safe_python_exec.py --file script.py         — Run .py file")
        print('  python safe_python_exec.py --sql "SELECT 1"         — Run SQL query')
        print('  python safe_python_exec.py --sql "SELECT 1" --db path/to/db')
        return

    if sys.argv[1] == "--file":
        filepath = sys.argv[2] if len(sys.argv) > 2 else ""
        result = run_python_file(filepath)
    elif sys.argv[1] == "--sql":
        query = sys.argv[2] if len(sys.argv) > 2 else ""
        db = sys.argv[4] if len(sys.argv) > 4 and sys.argv[3] == "--db" else None
        result = run_sql(query, db)
        if result["success"]:
            print(f"Rows: {result['count']} | Duration: {result['duration']}s")
            for row in result["results"][:50]:
                print(row)
        else:
            print(f"SQL Error: {result['error']}")
        return
    else:
        # Inline Python code
        code = " ".join(sys.argv[1:])
        result = run_python(code)

    # Print results
    if result["success"]:
        if result["stdout"]:
            print(result["stdout"], end="")
        print(f"\n[OK] returncode={result['returncode']} duration={result['duration']}s")
    else:
        if result["stdout"]:
            print(result["stdout"], end="")
        if result["stderr"]:
            print(result["stderr"], file=sys.stderr)
        print(f"\n[FAIL] returncode={result['returncode']} duration={result['duration']}s")


if __name__ == "__main__":
    main()
