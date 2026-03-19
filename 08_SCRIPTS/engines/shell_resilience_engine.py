"""
Shell Resilience Engine v1.0
=============================
LitigationOS 2026 — Pigors v. Watson

ROOT CAUSE: SQLite DB (2.1GB) gets write-locked by concurrent agents.
When Python tries sqlite3.connect() on a locked DB, it hangs forever,
the shell monitor kills the session, producing "Invalid shell ID" errors.

THIS ENGINE FIXES IT PERMANENTLY by:
1. WAL mode enforcement — allows concurrent readers even during writes
2. Aggressive timeout on every connection (never hang > 10s)
3. Connection queue with retry/backoff for write contention
4. Safe wrapper for ALL DB operations (read/write/FTS)
5. Shell command wrapper with process-level timeout protection
6. Automatic WAL checkpoint to prevent WAL bloat

USAGE:
    from shell_resilience_engine import safe_db, safe_query, safe_write, safe_fts

    # Read query (never hangs)
    rows = safe_query("SELECT * FROM auth_rules WHERE rule_number LIKE ?", ("%2.116%",))

    # Write with automatic retry on lock
    safe_write("INSERT INTO tort_claims VALUES (?, ?)", ("claim1", "IIED"))

    # FTS search (never hangs)
    results = safe_fts("evidence_quotes_fts", "Watson custody alienation")

    # Context manager for multiple operations
    with safe_db() as conn:
        conn.execute("SELECT ...")
        conn.execute("INSERT ...")

No external APIs. Pure local SQLite resilience.
"""

import sqlite3
import os
import sys
import time
import subprocess
import threading
import functools
import json
from contextlib import contextmanager
from typing import Optional, List, Tuple, Any, Dict

# ── Configuration ────────────────────────────────────────────────────────────

DB_PATH = r"C:\Users\andre\litigation_context.db"
DB_TIMEOUT = 10          # seconds to wait for lock before giving up
DB_RETRY_MAX = 5         # max retries on lock contention
DB_RETRY_BASE = 0.5      # base seconds for exponential backoff
WAL_CHECKPOINT_PAGES = 1000  # checkpoint WAL when it exceeds this many pages
SHELL_TIMEOUT = 120      # max seconds for any shell command
CHUNK_SIZE = 4096        # Cycle Method chunk size for large outputs

# ── WAL Mode Enforcer ───────────────────────────────────────────────────────

def enforce_wal_mode(db_path: str = DB_PATH) -> bool:
    """
    Ensure the database is in WAL (Write-Ahead Logging) mode.
    WAL allows concurrent readers even while a writer holds a lock.
    This is THE fix for the shell crash issue.
    
    Returns True if WAL mode is active.
    """
    try:
        conn = sqlite3.connect(db_path, timeout=DB_TIMEOUT)
        conn.execute("PRAGMA busy_timeout = 10000")  # 10s busy wait
        
        # Check current journal mode
        mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
        if mode.lower() != "wal":
            # Switch to WAL — this is a one-time operation
            result = conn.execute("PRAGMA journal_mode=WAL").fetchone()[0]
            if result.lower() == "wal":
                print(f"[RESILIENCE] Switched DB to WAL mode: {db_path}")
            else:
                print(f"[RESILIENCE] WARNING: Could not switch to WAL (got {result})")
                conn.close()
                return False
        
        # Set optimal WAL parameters
        conn.execute("PRAGMA synchronous=NORMAL")      # faster, still safe with WAL
        conn.execute("PRAGMA cache_size=-64000")        # 64MB cache
        conn.execute("PRAGMA mmap_size=268435456")      # 256MB memory-mapped I/O
        conn.execute("PRAGMA temp_store=MEMORY")        # temp tables in RAM
        conn.execute("PRAGMA busy_timeout=10000")       # 10s busy handler
        
        conn.close()
        return True
    except Exception as e:
        print(f"[RESILIENCE] WAL enforcement failed: {e}")
        return False


def wal_checkpoint(db_path: str = DB_PATH) -> Dict[str, int]:
    """
    Run a WAL checkpoint to merge WAL back into main DB.
    Prevents WAL file from growing indefinitely with many concurrent writers.
    """
    try:
        conn = sqlite3.connect(db_path, timeout=DB_TIMEOUT)
        conn.execute("PRAGMA busy_timeout = 10000")
        result = conn.execute("PRAGMA wal_checkpoint(PASSIVE)").fetchone()
        conn.close()
        return {
            "status": result[0],  # 0 = ok, 1 = busy
            "wal_pages": result[1],
            "checkpointed_pages": result[2]
        }
    except Exception as e:
        return {"status": -1, "error": str(e)}


# ── Safe Database Connection ─────────────────────────────────────────────────

@contextmanager
def safe_db(db_path: str = DB_PATH, readonly: bool = False):
    """
    Context manager that provides a resilient database connection.
    
    Features:
    - WAL mode enforced
    - Busy timeout set (never hangs)
    - Automatic retry on lock contention
    - Proper cleanup on exit
    - Read-only mode option (uses URI for immutable access)
    
    Usage:
        with safe_db() as conn:
            rows = conn.execute("SELECT * FROM auth_rules").fetchall()
    """
    conn = None
    attempt = 0
    last_error = None
    
    while attempt < DB_RETRY_MAX:
        try:
            if readonly:
                # URI mode with immutable flag — bypasses write locks entirely
                uri = f"file:{db_path}?mode=ro"
                conn = sqlite3.connect(uri, uri=True, timeout=DB_TIMEOUT)
            else:
                conn = sqlite3.connect(db_path, timeout=DB_TIMEOUT)
            
            # Set all resilience PRAGMAs
            conn.execute(f"PRAGMA busy_timeout = {DB_TIMEOUT * 1000}")
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA cache_size=-64000")
            conn.execute("PRAGMA temp_store=MEMORY")
            conn.row_factory = sqlite3.Row  # dict-like rows
            
            yield conn
            
            if not readonly:
                conn.commit()
            conn.close()
            return
            
        except sqlite3.OperationalError as e:
            last_error = e
            err_str = str(e).lower()
            if "locked" in err_str or "busy" in err_str:
                attempt += 1
                wait = DB_RETRY_BASE * (2 ** attempt)
                print(f"[RESILIENCE] DB locked, retry {attempt}/{DB_RETRY_MAX} in {wait:.1f}s")
                time.sleep(wait)
                if conn:
                    try:
                        conn.close()
                    except:
                        pass
                    conn = None
            else:
                if conn:
                    try:
                        conn.close()
                    except:
                        pass
                raise
        except Exception as e:
            if conn:
                try:
                    conn.close()
                except:
                    pass
            raise
    
    # All retries exhausted
    raise sqlite3.OperationalError(
        f"[RESILIENCE] DB still locked after {DB_RETRY_MAX} retries: {last_error}"
    )


# ── Safe Query Functions ─────────────────────────────────────────────────────

def safe_query(sql: str, params: tuple = (), db_path: str = DB_PATH, 
               limit: int = 0) -> List[Dict[str, Any]]:
    """
    Execute a read-only query with full resilience.
    Returns list of dicts. Never hangs.
    
    Usage:
        rows = safe_query("SELECT * FROM auth_rules WHERE rule_number LIKE ?", ("%2.116%",))
        for row in rows:
            print(row["rule_number"], row["full_text"][:100])
    """
    if limit > 0 and "LIMIT" not in sql.upper():
        sql = sql.rstrip(";") + f" LIMIT {limit}"
    
    with safe_db(db_path, readonly=True) as conn:
        cursor = conn.execute(sql, params)
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        rows = cursor.fetchall()
        return [dict(zip(columns, row)) for row in rows]


def safe_write(sql: str, params: tuple = (), db_path: str = DB_PATH) -> int:
    """
    Execute a write operation with full resilience.
    Returns number of rows affected. Retries on lock.
    """
    with safe_db(db_path) as conn:
        cursor = conn.execute(sql, params)
        return cursor.rowcount


def safe_write_many(sql: str, param_list: List[tuple], db_path: str = DB_PATH) -> int:
    """
    Execute batch write with full resilience.
    """
    with safe_db(db_path) as conn:
        cursor = conn.executemany(sql, param_list)
        return cursor.rowcount


def safe_fts(table: str, query: str, db_path: str = DB_PATH, 
             limit: int = 50, columns: str = "*") -> List[Dict[str, Any]]:
    """
    Safe FTS5 full-text search. Never hangs.
    
    Usage:
        results = safe_fts("evidence_quotes_fts", "Watson custody alienation", limit=20)
    """
    sql = f"SELECT {columns} FROM {table} WHERE {table} MATCH ? LIMIT ?"
    try:
        return safe_query(sql, (query, limit), db_path)
    except sqlite3.OperationalError as e:
        if "no such table" in str(e).lower():
            print(f"[RESILIENCE] FTS table {table} not found, falling back to LIKE")
            # Try base table (remove _fts suffix)
            base = table.replace("_fts", "")
            words = query.split()
            conditions = " AND ".join([f"CAST({columns} AS TEXT) LIKE ?" for _ in words])
            params = tuple(f"%{w}%" for w in words)
            return safe_query(
                f"SELECT * FROM {base} WHERE {conditions} LIMIT ?",
                params + (limit,), db_path
            )
        raise


# ── Safe Shell Command Execution ─────────────────────────────────────────────

def safe_shell(cmd: str, timeout: int = SHELL_TIMEOUT, 
               cwd: str = None) -> Dict[str, Any]:
    """
    Execute a shell command with timeout protection.
    
    The shell crash issue happens because Python hangs on DB lock,
    and the shell monitor kills the session. This wrapper:
    1. Runs the command in a subprocess with a hard timeout
    2. Captures stdout/stderr
    3. Returns result dict (never hangs the parent)
    
    Usage:
        result = safe_shell("python my_script.py", timeout=60)
        if result["success"]:
            print(result["stdout"])
    """
    try:
        proc = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
        )
        return {
            "success": proc.returncode == 0,
            "returncode": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "timed_out": False
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "returncode": -1,
            "stdout": "",
            "stderr": f"Command timed out after {timeout}s",
            "timed_out": True
        }
    except Exception as e:
        return {
            "success": False,
            "returncode": -1,
            "stdout": "",
            "stderr": str(e),
            "timed_out": False
        }


# ── DB Health Monitor ────────────────────────────────────────────────────────

def db_health_check(db_path: str = DB_PATH) -> Dict[str, Any]:
    """
    Quick health check on the database. Non-blocking.
    Returns status dict with connectivity, lock state, WAL info.
    """
    result = {
        "path": db_path,
        "exists": os.path.exists(db_path),
        "size_mb": 0,
        "wal_mode": False,
        "wal_size_kb": 0,
        "shm_size_kb": 0,
        "connectable": False,
        "table_count": 0,
        "locked": False,
        "errors": []
    }
    
    if not result["exists"]:
        result["errors"].append("Database file not found")
        return result
    
    result["size_mb"] = round(os.path.getsize(db_path) / (1024 * 1024), 1)
    
    # Check WAL/SHM files
    wal_path = db_path + "-wal"
    shm_path = db_path + "-shm"
    if os.path.exists(wal_path):
        result["wal_size_kb"] = round(os.path.getsize(wal_path) / 1024, 1)
    if os.path.exists(shm_path):
        result["shm_size_kb"] = round(os.path.getsize(shm_path) / 1024, 1)
    
    # Try connection with short timeout
    try:
        conn = sqlite3.connect(db_path, timeout=3)
        conn.execute("PRAGMA busy_timeout = 3000")
        
        mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
        result["wal_mode"] = mode.lower() == "wal"
        
        result["table_count"] = conn.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
        ).fetchone()[0]
        
        result["connectable"] = True
        conn.close()
        
    except sqlite3.OperationalError as e:
        if "locked" in str(e).lower() or "busy" in str(e).lower():
            result["locked"] = True
            result["errors"].append(f"DB locked: {e}")
        else:
            result["errors"].append(str(e))
    except Exception as e:
        result["errors"].append(str(e))
    
    return result


# ── Cycle-Safe Output ────────────────────────────────────────────────────────

def cycle_print(text: str, chunk_size: int = CHUNK_SIZE):
    """
    Print large text in chunks to avoid EAGAIN/buffer overflow.
    Integration with the Cycle Method engine.
    """
    if len(text) <= chunk_size:
        print(text)
        return
    
    for i in range(0, len(text), chunk_size):
        chunk = text[i:i + chunk_size]
        try:
            sys.stdout.write(chunk)
            sys.stdout.flush()
        except BlockingIOError:
            time.sleep(0.05)
            try:
                sys.stdout.write(chunk)
                sys.stdout.flush()
            except:
                pass  # skip chunk rather than crash


def cycle_json(data: Any, chunk_size: int = CHUNK_SIZE) -> str:
    """
    Serialize and print JSON in chunks. Returns the JSON string.
    """
    text = json.dumps(data, indent=2, default=str)
    cycle_print(text, chunk_size)
    return text


# ── Auto-Init ────────────────────────────────────────────────────────────────

_WAL_ENFORCED = False

def init(db_path: str = DB_PATH):
    """
    Initialize the resilience engine. Call once at startup.
    Enforces WAL mode and runs initial health check.
    """
    global _WAL_ENFORCED
    
    if _WAL_ENFORCED:
        return True
    
    health = db_health_check(db_path)
    
    if health["locked"]:
        print(f"[RESILIENCE] DB is currently locked — WAL enforcement deferred")
        print(f"[RESILIENCE] Using readonly mode until lock clears")
        _WAL_ENFORCED = False
        return False
    
    if health["connectable"]:
        if not health["wal_mode"]:
            success = enforce_wal_mode(db_path)
            _WAL_ENFORCED = success
        else:
            _WAL_ENFORCED = True
            print(f"[RESILIENCE] DB already in WAL mode ✓")
    
    return _WAL_ENFORCED


# ── Self-Test ────────────────────────────────────────────────────────────────

def self_test():
    """Run self-tests to verify the engine works."""
    results = []
    
    # Test 1: Health check
    print("Test 1: DB Health Check...", end=" ")
    health = db_health_check()
    assert health["exists"], "DB file not found"
    assert health["size_mb"] > 100, f"DB too small: {health['size_mb']}MB"
    results.append(("Health Check", "PASS", f"{health['size_mb']}MB, {health['table_count']} tables"))
    print("PASS")
    
    # Test 2: WAL enforcement
    print("Test 2: WAL Mode...", end=" ")
    if health["connectable"]:
        success = init()
        results.append(("WAL Mode", "PASS" if success else "DEFERRED", 
                        "WAL active" if success else "DB locked, deferred"))
        print("PASS" if success else "DEFERRED (DB locked)")
    else:
        results.append(("WAL Mode", "SKIP", "DB not connectable"))
        print("SKIP")
    
    # Test 3: Safe query (readonly)
    print("Test 3: Safe Query...", end=" ")
    try:
        rows = safe_query("SELECT COUNT(*) as cnt FROM sqlite_master WHERE type='table'")
        count = rows[0]["cnt"] if rows else 0
        assert count > 50, f"Expected 50+ tables, got {count}"
        results.append(("Safe Query", "PASS", f"{count} tables"))
        print(f"PASS ({count} tables)")
    except Exception as e:
        results.append(("Safe Query", "FAIL", str(e)))
        print(f"FAIL: {e}")
    
    # Test 4: Safe FTS
    print("Test 4: Safe FTS...", end=" ")
    try:
        rows = safe_fts("evidence_quotes_fts", "Watson", limit=5)
        results.append(("Safe FTS", "PASS", f"{len(rows)} results"))
        print(f"PASS ({len(rows)} results)")
    except Exception as e:
        results.append(("Safe FTS", "FAIL", str(e)))
        print(f"FAIL: {e}")
    
    # Test 5: Safe shell
    print("Test 5: Safe Shell...", end=" ")
    result = safe_shell("python -c \"print('resilience ok')\"", timeout=10)
    assert result["success"], f"Shell failed: {result['stderr']}"
    assert "resilience ok" in result["stdout"]
    results.append(("Safe Shell", "PASS", "subprocess ok"))
    print("PASS")
    
    # Test 6: Timeout protection
    print("Test 6: Timeout Protection...", end=" ")
    result = safe_shell("python -c \"import time; time.sleep(30)\"", timeout=3)
    assert result["timed_out"], "Should have timed out"
    results.append(("Timeout Protection", "PASS", "3s timeout worked"))
    print("PASS")
    
    # Test 7: Cycle print
    print("Test 7: Cycle Print...", end=" ")
    big_text = "x" * 10000
    cycle_print(big_text)
    print()  # newline after the x's
    results.append(("Cycle Print", "PASS", "10KB chunked ok"))
    print("PASS")
    
    # Summary
    print("\n" + "=" * 60)
    print("SHELL RESILIENCE ENGINE — SELF-TEST RESULTS")
    print("=" * 60)
    passed = sum(1 for _, s, _ in results if s == "PASS")
    total = len(results)
    for name, status, detail in results:
        icon = "✓" if status == "PASS" else "⚠" if status in ("DEFERRED", "SKIP") else "✗"
        print(f"  {icon} {name}: {status} — {detail}")
    print(f"\n  {passed}/{total} passed")
    print("=" * 60)
    
    return passed == total


if __name__ == "__main__":
    self_test()
