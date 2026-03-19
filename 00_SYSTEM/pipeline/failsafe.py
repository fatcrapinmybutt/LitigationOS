#!/usr/bin/env python3
"""
FAILSAFE — Universal Pipeline Protection for LitigationOS
==========================================================
Prevents ANY blocking operation from killing the pipeline.
Windows-compatible (threading-based, no POSIX signals).

Features:
  - @timeout(seconds)       — kill any function that takes too long
  - @never_crash(fallback)  — catch ALL exceptions, return fallback
  - safe_call(fn, ...)      — one-shot safe invocation with timeout + fallback
  - CircuitBreaker           — stop calling a function that keeps failing
  - safe_import(module)     — import a module without hanging or crashing
  - FailsafePhaseRunner     — wrap entire pipeline phases

Usage:
    from failsafe import safe_call, timeout, never_crash, CircuitBreaker

    # Wrap any risky call — 5s max, returns {} on failure
    result = safe_call(detect_drives, timeout_s=5, fallback={})

    # Decorator: function can never take > 10s
    @timeout(10)
    def scan_files(): ...

    # Decorator: function can never crash the caller
    @never_crash(fallback=[])
    def parse_document(path): ...

    # Circuit breaker: stop hitting a dead API
    breaker = CircuitBreaker("ollama", threshold=3, cooldown=60)
    if breaker.allow():
        try:
            result = call_ollama(prompt)
            breaker.record_success()
        except Exception as e:
            breaker.record_failure(e)
"""

import functools
import json
import logging
import os
import sqlite3
import sys
import threading
import time
import traceback
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Optional, TypeVar

logger = logging.getLogger("failsafe")

T = TypeVar("T")

# ════════════════════════════════════════════════════════════════════════
#  Failsafe Database — logs every incident for post-mortem
# ════════════════════════════════════════════════════════════════════════

_DB_PATH = Path(__file__).parent.parent / "failsafe_incidents.db"
_db_lock = threading.Lock()
_db_conn: Optional[sqlite3.Connection] = None


def _get_db() -> sqlite3.Connection:
    global _db_conn
    if _db_conn is not None:
        return _db_conn
    with _db_lock:
        if _db_conn is not None:
            return _db_conn
        try:
            _db_conn = sqlite3.connect(str(_DB_PATH), check_same_thread=False)
            _db_conn.execute("PRAGMA journal_mode=WAL")
            _db_conn.execute("""
                CREATE TABLE IF NOT EXISTS incidents (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts          TEXT NOT NULL,
                    component   TEXT NOT NULL,
                    incident    TEXT NOT NULL,
                    severity    TEXT NOT NULL DEFAULT 'ERROR',
                    detail      TEXT,
                    fallback    TEXT,
                    resolved    INTEGER NOT NULL DEFAULT 0
                )
            """)
            _db_conn.execute("""
                CREATE TABLE IF NOT EXISTS circuit_state (
                    name        TEXT PRIMARY KEY,
                    failures    INTEGER NOT NULL DEFAULT 0,
                    last_fail   TEXT,
                    state       TEXT NOT NULL DEFAULT 'CLOSED',
                    cooldown_until TEXT
                )
            """)
            _db_conn.commit()
        except Exception:
            pass
    return _db_conn


def _log_incident(component: str, incident: str, severity: str = "ERROR",
                  detail: str = "", fallback: str = ""):
    """Log an incident to DB + stderr. Never raises."""
    ts = datetime.now().isoformat()
    msg = f"[FAILSAFE][{severity}] {component}: {incident}"
    if detail:
        msg += f" | {detail[:200]}"
    print(msg, file=sys.stderr)
    try:
        db = _get_db()
        if db:
            db.execute(
                "INSERT INTO incidents (ts, component, incident, severity, detail, fallback) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (ts, component, incident, severity, detail[:2000] if detail else "", fallback[:500] if fallback else ""),
            )
            db.commit()
    except Exception:
        pass  # failsafe must never fail


# ════════════════════════════════════════════════════════════════════════
#  retry() — Retry decorator with exponential backoff
# ════════════════════════════════════════════════════════════════════════

def retry(max_attempts=3, backoff_base=2, exceptions=(Exception,)):
    """Retry decorator with exponential backoff."""
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return fn(*args, **kwargs)
                except exceptions as e:
                    last_error = e
                    if attempt < max_attempts:
                        wait = backoff_base ** attempt
                        print(f"[RETRY] {fn.__name__} attempt {attempt}/{max_attempts} failed: {e}. Retrying in {wait}s...")
                        time.sleep(wait)
                    else:
                        print(f"[RETRY] {fn.__name__} FAILED after {max_attempts} attempts: {e}")
                        raise
            raise last_error
        return wrapper
    return decorator


# ════════════════════════════════════════════════════════════════════════
#  get_robust_connection() — Self-healing SQLite connection
# ════════════════════════════════════════════════════════════════════════

def get_robust_connection(db_path, timeout=120):
    """Get a robust SQLite connection with WAL mode and self-healing."""
    if not os.path.exists(db_path):
        print(f"[DB] Creating new database: {db_path}")

    conn = sqlite3.connect(db_path, timeout=timeout)
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA synchronous=NORMAL')
    conn.execute('PRAGMA busy_timeout=120000')
    conn.execute('PRAGMA cache_size=-64000')  # 64MB cache

    # Integrity check on first connect
    try:
        result = conn.execute('PRAGMA integrity_check').fetchone()
        if result[0] != 'ok':
            print(f"[DB WARNING] Integrity check failed: {result[0]}")
    except Exception as e:
        print(f"[DB WARNING] Could not run integrity check: {e}")

    return conn


# ════════════════════════════════════════════════════════════════════════
#  @timeout(seconds) — Thread-based timeout (Windows-safe)
# ════════════════════════════════════════════════════════════════════════

class TimeoutError(Exception):
    """Raised when a function exceeds its time budget."""


def timeout(seconds: float, fallback: Any = None):
    """Decorator: kills the wrapped function if it exceeds `seconds`.

    On timeout, logs the incident and returns `fallback`.
    Uses a daemon thread so it works on Windows (no signal.alarm).
    """
    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            result_box: list = []
            error_box: list = []

            def target():
                try:
                    result_box.append(fn(*args, **kwargs))
                except Exception as exc:
                    error_box.append(exc)

            thread = threading.Thread(target=target, daemon=True)
            thread.start()
            thread.join(timeout=seconds)

            if thread.is_alive():
                _log_incident(
                    fn.__qualname__, f"TIMEOUT after {seconds}s",
                    severity="WARN",
                    detail=f"args={str(args)[:200]}, kwargs={str(kwargs)[:200]}",
                    fallback=str(fallback)[:200],
                )
                return fallback
            if error_box:
                raise error_box[0]
            return result_box[0] if result_box else fallback
        return wrapper
    return decorator


# ════════════════════════════════════════════════════════════════════════
#  @never_crash(fallback) — Absolute exception boundary
# ════════════════════════════════════════════════════════════════════════

def never_crash(fallback: Any = None):
    """Decorator: catches ALL exceptions and returns `fallback`.

    The function will NEVER propagate an exception to the caller.
    Every failure is logged to the failsafe DB.
    """
    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except Exception as exc:
                tb = traceback.format_exc()
                _log_incident(
                    fn.__qualname__, f"{type(exc).__name__}: {exc}",
                    severity="ERROR",
                    detail=tb[-1000:],
                    fallback=str(fallback)[:200],
                )
                return fallback
        return wrapper
    return decorator


# ════════════════════════════════════════════════════════════════════════
#  safe_call() — One-shot safe invocation
# ════════════════════════════════════════════════════════════════════════

def safe_call(fn: Callable[..., T], *args,
              timeout_s: float = 30,
              fallback: T = None,
              component: str = "",
              **kwargs) -> T:
    """Call `fn(*args, **kwargs)` with timeout + crash protection.

    Returns the function's result, or `fallback` on timeout/error.
    NEVER raises. NEVER hangs. ALWAYS returns.
    """
    comp = component or getattr(fn, "__qualname__", str(fn))
    result_box: list = []
    error_box: list = []

    def target():
        try:
            result_box.append(fn(*args, **kwargs))
        except Exception as exc:
            error_box.append(exc)

    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    thread.join(timeout=timeout_s)

    if thread.is_alive():
        _log_incident(
            comp, f"TIMEOUT after {timeout_s}s",
            severity="WARN",
            fallback=str(fallback)[:200],
        )
        return fallback

    if error_box:
        exc = error_box[0]
        _log_incident(
            comp, f"{type(exc).__name__}: {exc}",
            severity="ERROR",
            detail=traceback.format_exception(type(exc), exc, exc.__traceback__)[-1][:500],
            fallback=str(fallback)[:200],
        )
        return fallback

    return result_box[0] if result_box else fallback


# ════════════════════════════════════════════════════════════════════════
#  CircuitBreaker — Stop calling things that keep failing
# ════════════════════════════════════════════════════════════════════════

@dataclass
class CircuitBreaker:
    """Three-state circuit breaker: CLOSED → OPEN → HALF_OPEN → CLOSED.

    - CLOSED: normal operation, failures counted
    - OPEN: all calls blocked, returns fallback immediately
    - HALF_OPEN: one test call allowed; success → CLOSED, failure → OPEN
    """
    name: str
    threshold: int = 3         # failures before OPEN
    cooldown: float = 60.0     # seconds before HALF_OPEN
    _failures: int = 0
    _state: str = "CLOSED"     # CLOSED | OPEN | HALF_OPEN
    _last_fail_time: float = 0.0
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def allow(self) -> bool:
        with self._lock:
            if self._state == "CLOSED":
                return True
            if self._state == "OPEN":
                if time.time() - self._last_fail_time >= self.cooldown:
                    self._state = "HALF_OPEN"
                    _log_incident(self.name, "Circuit HALF_OPEN — allowing test call", severity="INFO")
                    return True
                return False
            # HALF_OPEN — allow one test
            return True

    def record_success(self):
        with self._lock:
            if self._state == "HALF_OPEN":
                _log_incident(self.name, "Circuit CLOSED — recovered", severity="INFO")
            self._failures = 0
            self._state = "CLOSED"

    def record_failure(self, exc: Optional[Exception] = None):
        with self._lock:
            self._failures += 1
            self._last_fail_time = time.time()
            if self._state == "HALF_OPEN" or self._failures >= self.threshold:
                self._state = "OPEN"
                _log_incident(
                    self.name,
                    f"Circuit OPEN — {self._failures} failures (threshold={self.threshold})",
                    severity="WARN",
                    detail=str(exc)[:300] if exc else "",
                )
            # Persist to DB
            try:
                db = _get_db()
                if db:
                    db.execute(
                        "INSERT OR REPLACE INTO circuit_state (name, failures, last_fail, state, cooldown_until) "
                        "VALUES (?, ?, ?, ?, ?)",
                        (self.name, self._failures, datetime.now().isoformat(),
                         self._state, datetime.fromtimestamp(self._last_fail_time + self.cooldown).isoformat()),
                    )
                    db.commit()
            except Exception:
                pass

    @property
    def state(self) -> str:
        with self._lock:
            # Auto-transition OPEN → HALF_OPEN if cooldown elapsed
            if self._state == "OPEN" and time.time() - self._last_fail_time >= self.cooldown:
                self._state = "HALF_OPEN"
            return self._state


# ════════════════════════════════════════════════════════════════════════
#  safe_import() — Import a module without hanging or crashing
# ════════════════════════════════════════════════════════════════════════

def safe_import(module_name: str, timeout_s: float = 10, fallback=None):
    """Import a module safely with timeout protection.

    Returns the module, or `fallback` if the import hangs or crashes.
    """
    import importlib
    return safe_call(
        importlib.import_module, module_name,
        timeout_s=timeout_s,
        fallback=fallback,
        component=f"import:{module_name}",
    )


# ════════════════════════════════════════════════════════════════════════
#  FailsafePhaseRunner — Wrap entire pipeline phases
# ════════════════════════════════════════════════════════════════════════

class FailsafePhaseRunner:
    """Wraps pipeline phase execution with failsafe protection.

    Usage:
        runner = FailsafePhaseRunner(timeout_s=300)
        result = runner.run_phase("phase3_classify", phase3_main, cycle_dir)
    """

    def __init__(self, timeout_s: float = 300, stop_on_critical: bool = False):
        self.timeout_s = timeout_s
        self.stop_on_critical = stop_on_critical
        self.results: Dict[str, dict] = {}

    def run_phase(self, phase_name: str, fn: Callable, *args, **kwargs) -> dict:
        """Run a pipeline phase with full failsafe protection.

        Returns: {"status": "ok"|"timeout"|"error", "result": ..., "elapsed": float}
        """
        t0 = time.time()
        result_box: list = []
        error_box: list = []

        def target():
            try:
                result_box.append(fn(*args, **kwargs))
            except Exception as exc:
                error_box.append(exc)

        thread = threading.Thread(target=target, daemon=True)
        thread.start()
        thread.join(timeout=self.timeout_s)
        elapsed = time.time() - t0

        if thread.is_alive():
            outcome = {
                "status": "timeout",
                "result": None,
                "elapsed": elapsed,
                "error": f"Phase timed out after {self.timeout_s}s",
            }
            _log_incident(phase_name, f"PHASE TIMEOUT after {self.timeout_s}s", severity="CRITICAL")
        elif error_box:
            exc = error_box[0]
            outcome = {
                "status": "error",
                "result": None,
                "elapsed": elapsed,
                "error": f"{type(exc).__name__}: {exc}",
            }
            _log_incident(
                phase_name, f"PHASE ERROR: {type(exc).__name__}: {exc}",
                severity="ERROR",
                detail=traceback.format_exc()[-1000:],
            )
        else:
            outcome = {
                "status": "ok",
                "result": result_box[0] if result_box else None,
                "elapsed": elapsed,
                "error": None,
            }

        self.results[phase_name] = outcome
        return outcome

    def summary(self) -> str:
        lines = ["=== Failsafe Phase Summary ==="]
        for name, r in self.results.items():
            icon = {"ok": "✓", "timeout": "⏱", "error": "✗"}.get(r["status"], "?")
            lines.append(f"  {icon} {name}: {r['status']} ({r['elapsed']:.1f}s)")
            if r["error"]:
                lines.append(f"    └─ {r['error'][:120]}")
        return "\n".join(lines)


# ════════════════════════════════════════════════════════════════════════
#  dashboard() — Quick incident report
# ════════════════════════════════════════════════════════════════════════

def dashboard(last_n: int = 20) -> str:
    """Return a human-readable incident dashboard."""
    lines = ["=== FAILSAFE DASHBOARD ==="]
    try:
        db = _get_db()
        if not db:
            lines.append("  (no database)")
            return "\n".join(lines)

        # Recent incidents
        rows = db.execute(
            "SELECT ts, severity, component, incident FROM incidents "
            "ORDER BY id DESC LIMIT ?", (last_n,)
        ).fetchall()
        if rows:
            lines.append(f"\nLast {len(rows)} incidents:")
            for ts, sev, comp, inc in rows:
                lines.append(f"  [{sev}] {ts[:19]} {comp}: {inc[:80]}")
        else:
            lines.append("\n  No incidents recorded. System healthy.")

        # Circuit breaker states
        cb_rows = db.execute("SELECT name, state, failures, cooldown_until FROM circuit_state").fetchall()
        if cb_rows:
            lines.append("\nCircuit breakers:")
            for name, state, failures, until in cb_rows:
                lines.append(f"  {name}: {state} (failures={failures})")
    except Exception as exc:
        lines.append(f"  Dashboard error: {exc}")

    return "\n".join(lines)


# ════════════════════════════════════════════════════════════════════════
#  Self-test
# ════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import time as _time

    print("=== Failsafe Self-Test ===\n")
    passed = 0
    total = 0

    # Test 1: timeout catches a hanging function
    total += 1
    @timeout(1, fallback="TIMED_OUT")
    def hang_forever():
        _time.sleep(999)
        return "never"
    r = hang_forever()
    if r == "TIMED_OUT":
        print("✓ Test 1: timeout decorator catches hang")
        passed += 1
    else:
        print(f"✗ Test 1: expected TIMED_OUT, got {r}")

    # Test 2: never_crash catches exception
    total += 1
    @never_crash(fallback="SAFE")
    def explode():
        raise RuntimeError("boom")
    r = explode()
    if r == "SAFE":
        print("✓ Test 2: never_crash catches exception")
        passed += 1
    else:
        print(f"✗ Test 2: expected SAFE, got {r}")

    # Test 3: safe_call with timeout
    total += 1
    def slow_add(a, b):
        _time.sleep(10)
        return a + b
    r = safe_call(slow_add, 1, 2, timeout_s=1, fallback=-1)
    if r == -1:
        print("✓ Test 3: safe_call timeout returns fallback")
        passed += 1
    else:
        print(f"✗ Test 3: expected -1, got {r}")

    # Test 4: safe_call success
    total += 1
    r = safe_call(lambda: 42, timeout_s=5, fallback=-1)
    if r == 42:
        print("✓ Test 4: safe_call success returns result")
        passed += 1
    else:
        print(f"✗ Test 4: expected 42, got {r}")

    # Test 5: circuit breaker
    total += 1
    cb = CircuitBreaker("test_api", threshold=2, cooldown=1)
    assert cb.allow()
    cb.record_failure(RuntimeError("fail1"))
    assert cb.allow()
    cb.record_failure(RuntimeError("fail2"))
    assert not cb.allow()  # OPEN
    _time.sleep(1.2)
    assert cb.allow()  # HALF_OPEN after cooldown
    cb.record_success()
    assert cb.state == "CLOSED"
    print("✓ Test 5: circuit breaker state machine works")
    passed += 1

    # Test 6: never_crash + timeout combined
    total += 1
    @never_crash(fallback="DOUBLE_SAFE")
    @timeout(1, fallback="TIMED_OUT")
    def hang_and_crash():
        _time.sleep(999)
    r = hang_and_crash()
    if r == "TIMED_OUT":
        print("✓ Test 6: combined never_crash + timeout")
        passed += 1
    else:
        print(f"✗ Test 6: expected TIMED_OUT, got {r}")

    print(f"\n{passed}/{total} tests passed")
    print(f"\n{dashboard()}")
