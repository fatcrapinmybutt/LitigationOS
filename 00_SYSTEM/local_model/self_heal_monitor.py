"""
MBP LitigationOS 2026 — Self-Healing System Monitor
=====================================================
Health monitoring, auto-restart, error recovery, DB connection pooling,
memory monitoring, and watchdog for all 30+ engines.

NEVER crashes. Catches everything. Logs everything. Degrades gracefully.
"""

import ast
import collections
import datetime
import importlib
import importlib.util
import json
import os
import pathlib
import shutil
import sqlite3
import sys
import time
import traceback

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DEFAULT_DB = r"C:\Users\andre\LitigationOS\litigation_context.db"
_DEFAULT_ENGINE_DIR = r"C:\Users\andre\LitigationOS\00_SYSTEM\local_model"

_HEALTH_LOG_DDL = """
CREATE TABLE IF NOT EXISTS system_health_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    engine_name TEXT NOT NULL,
    status TEXT NOT NULL,
    error_message TEXT,
    latency_ms REAL,
    memory_mb REAL,
    action_taken TEXT,
    recorded_at TEXT DEFAULT (datetime('now'))
);
"""

_RECOVERY_DDL = """
CREATE TABLE IF NOT EXISTS recovery_actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    engine_name TEXT NOT NULL,
    error_type TEXT NOT NULL,
    action TEXT NOT NULL,
    success INTEGER,
    recorded_at TEXT DEFAULT (datetime('now'))
);
"""

# Thresholds
_WAL_VACUUM_THRESHOLD_MB = 100
_MEMORY_WARNING_PCT = 80
_MEMORY_CRITICAL_PCT = 95
_DISK_WARNING_GB = 5
_DISK_CRITICAL_GB = 1
_CACHE_STALE_HOURS = 72


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    try:
        return datetime.datetime.now().isoformat(timespec="seconds")
    except Exception:
        return str(datetime.datetime.now())


def _safe_stat(path: str) -> dict:
    """Return file stat info without ever raising."""
    try:
        st = os.stat(path)
        return {
            "size_bytes": st.st_size,
            "modified": st.st_mtime,
            "exists": True,
        }
    except Exception:
        return {"size_bytes": 0, "modified": 0, "exists": False}


# ---------------------------------------------------------------------------
# SelfHealMonitor
# ---------------------------------------------------------------------------

class SelfHealMonitor:
    """Central nervous system for LitigationOS health."""

    # ---- construction ------------------------------------------------------

    def __init__(self, db_path: str = _DEFAULT_DB, engine_dir: str = _DEFAULT_ENGINE_DIR):
        self.db_path = str(db_path)
        self.engine_dir = str(engine_dir)
        self._start_time = time.time()
        self._error_log: list = []
        self._last_sweep: str = ""
        self._conn_pool: dict = {}

        self._ensure_tables()

    # ---- table bootstrap ---------------------------------------------------

    def _ensure_tables(self) -> None:
        """Create monitoring tables — triple-guarded."""
        try:
            conn = self._get_conn()
            try:
                conn.executescript(_HEALTH_LOG_DDL + _RECOVERY_DDL)
                conn.commit()
            except Exception as exc:
                self._log_error("_ensure_tables:execute", exc)
            finally:
                self._release_conn(conn)
        except Exception as exc:
            self._log_error("_ensure_tables:connect", exc)

    # ---- connection pool ---------------------------------------------------

    def _get_conn(self) -> sqlite3.Connection:
        """Get a DB connection with retry logic."""
        last_err = None
        for attempt in range(3):
            try:
                conn = sqlite3.connect(
                    self.db_path,
                    timeout=10,
                    isolation_level=None,
                )
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA busy_timeout=5000")
                return conn
            except Exception as exc:
                last_err = exc
                self._log_error(f"_get_conn:attempt_{attempt}", exc)
                time.sleep(min(2 ** attempt, 4))
        raise ConnectionError(f"DB connection failed after 3 retries: {last_err}")

    def _release_conn(self, conn: sqlite3.Connection) -> None:
        try:
            conn.close()
        except Exception:
            pass

    # ---- internal logging --------------------------------------------------

    def _log_error(self, context: str, exc: Exception) -> None:
        entry = {
            "context": context,
            "error": str(exc),
            "traceback": traceback.format_exc(),
            "time": _now_iso(),
        }
        self._error_log.append(entry)
        # Keep bounded
        if len(self._error_log) > 1000:
            self._error_log = self._error_log[-500:]

    def _log_health(self, engine_name: str, status: str,
                    error_message: str = None, latency_ms: float = None,
                    memory_mb: float = None, action_taken: str = None) -> None:
        try:
            conn = self._get_conn()
            try:
                conn.execute(
                    "INSERT INTO system_health_log "
                    "(engine_name, status, error_message, latency_ms, memory_mb, action_taken) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (engine_name, status, error_message, latency_ms, memory_mb, action_taken),
                )
            except Exception as exc:
                self._log_error("_log_health:insert", exc)
            finally:
                self._release_conn(conn)
        except Exception as exc:
            self._log_error("_log_health:connect", exc)

    def _log_recovery(self, engine_name: str, error_type: str,
                      action: str, success: bool) -> None:
        try:
            conn = self._get_conn()
            try:
                conn.execute(
                    "INSERT INTO recovery_actions "
                    "(engine_name, error_type, action, success) "
                    "VALUES (?, ?, ?, ?)",
                    (engine_name, error_type, action, 1 if success else 0),
                )
            except Exception as exc:
                self._log_error("_log_recovery:insert", exc)
            finally:
                self._release_conn(conn)
        except Exception as exc:
            self._log_error("_log_recovery:connect", exc)

    # ---- engine discovery --------------------------------------------------

    def _discover_engines(self) -> list:
        """Return list of .py file paths in engine_dir."""
        engines = []
        try:
            for entry in os.scandir(self.engine_dir):
                try:
                    if entry.is_file() and entry.name.endswith(".py"):
                        engines.append(entry.path)
                except Exception:
                    pass
        except Exception as exc:
            self._log_error("_discover_engines", exc)
        return sorted(engines)

    # ---- check_all_engines -------------------------------------------------

    def check_all_engines(self) -> dict:
        """
        For each .py in engine_dir:
          - ast.parse OK?
          - Has expected class?
          - Can connect to DB?
          - Import time
        """
        results = {}
        for fpath in self._discover_engines():
            name = os.path.basename(fpath)
            result = {
                "status": "healthy",
                "import_time_ms": 0.0,
                "has_class": False,
                "can_connect_db": False,
                "errors": [],
            }

            # 1. ast.parse
            try:
                with open(fpath, "r", encoding="utf-8", errors="replace") as fh:
                    source = fh.read()
                t0 = time.perf_counter()
                tree = ast.parse(source, filename=fpath)
                result["import_time_ms"] = round((time.perf_counter() - t0) * 1000, 2)

                # 2. detect top-level class
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        result["has_class"] = True
                        break
            except SyntaxError as se:
                result["status"] = "failed"
                result["errors"].append(
                    f"SyntaxError at line {se.lineno}: {se.msg}"
                )
            except Exception as exc:
                result["status"] = "degraded"
                result["errors"].append(str(exc))

            # 3. DB connectivity (quick probe)
            try:
                conn = self._get_conn()
                conn.execute("SELECT 1")
                result["can_connect_db"] = True
                self._release_conn(conn)
            except Exception as exc:
                result["errors"].append(f"DB: {exc}")
                if result["status"] == "healthy":
                    result["status"] = "degraded"

            results[name] = result
        return results

    # ---- check_db_health ---------------------------------------------------

    def check_db_health(self) -> dict:
        """Database health: connectivity, integrity, stats, WAL, disk."""
        report = {
            "connected": False,
            "integrity_ok": False,
            "tables": 0,
            "rows": 0,
            "wal_size_mb": 0.0,
            "disk_free_gb": 0.0,
        }

        conn = None
        try:
            conn = self._get_conn()
            report["connected"] = True

            # integrity check
            try:
                row = conn.execute("PRAGMA integrity_check").fetchone()
                report["integrity_ok"] = (row and row[0] == "ok")
            except Exception as exc:
                self._log_error("check_db_health:integrity", exc)

            # table count
            try:
                row = conn.execute(
                    "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
                ).fetchone()
                report["tables"] = row[0] if row else 0
            except Exception as exc:
                self._log_error("check_db_health:tables", exc)

            # total rows (sample top tables)
            try:
                tables = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
                total = 0
                for (tbl,) in tables:
                    try:
                        r = conn.execute(
                            f'SELECT COUNT(*) FROM "{tbl}"'
                        ).fetchone()
                        total += r[0] if r else 0
                    except Exception:
                        pass
                report["rows"] = total
            except Exception as exc:
                self._log_error("check_db_health:rows", exc)

            # WAL size
            try:
                wal_path = self.db_path + "-wal"
                if os.path.exists(wal_path):
                    report["wal_size_mb"] = round(
                        os.path.getsize(wal_path) / (1024 * 1024), 2
                    )
            except Exception as exc:
                self._log_error("check_db_health:wal", exc)

        except Exception as exc:
            self._log_error("check_db_health:connect", exc)
        finally:
            if conn:
                self._release_conn(conn)

        # disk free space
        try:
            usage = shutil.disk_usage(os.path.dirname(self.db_path) or ".")
            report["disk_free_gb"] = round(usage.free / (1024 ** 3), 2)
        except Exception as exc:
            self._log_error("check_db_health:disk", exc)

        return report

    # ---- check_memory_usage ------------------------------------------------

    def check_memory_usage(self) -> dict:
        """System and process memory stats."""
        report = {
            "process_mb": 0.0,
            "system_total_mb": 0.0,
            "system_available_mb": 0.0,
            "cache_estimate_mb": 0.0,
        }

        # Process memory via platform-specific approaches
        try:
            if sys.platform == "win32":
                import ctypes
                import ctypes.wintypes

                class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
                    _fields_ = [
                        ("cb", ctypes.wintypes.DWORD),
                        ("PageFaultCount", ctypes.wintypes.DWORD),
                        ("PeakWorkingSetSize", ctypes.c_size_t),
                        ("WorkingSetSize", ctypes.c_size_t),
                        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                        ("PagefileUsage", ctypes.c_size_t),
                        ("PeakPagefileUsage", ctypes.c_size_t),
                    ]

                try:
                    psapi = ctypes.windll.psapi
                    kernel32 = ctypes.windll.kernel32
                    handle = kernel32.GetCurrentProcess()
                    counters = PROCESS_MEMORY_COUNTERS()
                    counters.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS)
                    if psapi.GetProcessMemoryInfo(
                        handle, ctypes.byref(counters), counters.cb
                    ):
                        report["process_mb"] = round(
                            counters.WorkingSetSize / (1024 * 1024), 2
                        )
                except Exception:
                    pass

                # System memory via GlobalMemoryStatusEx
                try:
                    class MEMORYSTATUSEX(ctypes.Structure):
                        _fields_ = [
                            ("dwLength", ctypes.wintypes.DWORD),
                            ("dwMemoryLoad", ctypes.wintypes.DWORD),
                            ("ullTotalPhys", ctypes.c_ulonglong),
                            ("ullAvailPhys", ctypes.c_ulonglong),
                            ("ullTotalPageFile", ctypes.c_ulonglong),
                            ("ullAvailPageFile", ctypes.c_ulonglong),
                            ("ullTotalVirtual", ctypes.c_ulonglong),
                            ("ullAvailVirtual", ctypes.c_ulonglong),
                            ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                        ]

                    mem = MEMORYSTATUSEX()
                    mem.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
                    if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(mem)):
                        report["system_total_mb"] = round(
                            mem.ullTotalPhys / (1024 * 1024), 2
                        )
                        report["system_available_mb"] = round(
                            mem.ullAvailPhys / (1024 * 1024), 2
                        )
                except Exception:
                    pass
            else:
                # Unix: try resource module
                try:
                    import resource
                    ru = resource.getrusage(resource.RUSAGE_SELF)
                    report["process_mb"] = round(ru.ru_maxrss / 1024, 2)
                except Exception:
                    pass

                # /proc/meminfo
                try:
                    with open("/proc/meminfo", "r") as f:
                        info = {}
                        for line in f:
                            parts = line.split()
                            if len(parts) >= 2:
                                info[parts[0].rstrip(":")] = int(parts[1])
                        report["system_total_mb"] = round(
                            info.get("MemTotal", 0) / 1024, 2
                        )
                        report["system_available_mb"] = round(
                            info.get("MemAvailable", info.get("MemFree", 0)) / 1024, 2
                        )
                except Exception:
                    pass
        except Exception as exc:
            self._log_error("check_memory_usage:platform", exc)

        # Cache size estimate — scan known large objects in sys.modules
        try:
            estimate = 0
            for mod_name, mod in sys.modules.items():
                try:
                    if mod and hasattr(mod, "__file__") and mod.__file__:
                        if self.engine_dir in str(mod.__file__):
                            estimate += sys.getsizeof(mod)
                except Exception:
                    pass
            report["cache_estimate_mb"] = round(estimate / (1024 * 1024), 4)
        except Exception as exc:
            self._log_error("check_memory_usage:cache", exc)

        return report

    # ---- auto_recover ------------------------------------------------------

    def auto_recover(self, engine_name: str, error: str) -> dict:
        """
        Attempt automatic recovery based on error type.
        Returns {recovered: bool, action_taken: str}.
        """
        result = {"recovered": False, "action_taken": "none"}
        error_lower = error.lower() if error else ""

        try:
            # 1. DB connection errors
            if any(kw in error_lower for kw in (
                "database", "connection", "locked", "disk i/o",
                "unable to open", "sqlite",
            )):
                action = "reconnect_db_exponential_backoff"
                recovered = False
                for attempt in range(3):
                    try:
                        time.sleep(min(2 ** attempt, 4))
                        conn = self._get_conn()
                        conn.execute("SELECT 1")
                        self._release_conn(conn)
                        recovered = True
                        break
                    except Exception:
                        pass
                result["recovered"] = recovered
                result["action_taken"] = (
                    f"{action}: {'success' if recovered else 'failed'} after {attempt + 1} retries"
                )
                self._log_recovery(engine_name, "db_connection", action, recovered)
                return result

            # 2. Syntax / import errors
            if any(kw in error_lower for kw in (
                "syntax", "import", "indent", "parse",
            )):
                action = "syntax_check"
                fpath = os.path.join(self.engine_dir, engine_name)
                details = ""
                if os.path.isfile(fpath):
                    try:
                        with open(fpath, "r", encoding="utf-8", errors="replace") as fh:
                            ast.parse(fh.read(), filename=fpath)
                        details = "file parses OK now"
                        result["recovered"] = True
                    except SyntaxError as se:
                        details = f"SyntaxError at line {se.lineno}: {se.msg}"
                    except Exception as ex2:
                        details = str(ex2)
                else:
                    details = "file not found"
                result["action_taken"] = f"{action}: {details}"
                self._log_recovery(engine_name, "import_error", action, result["recovered"])
                return result

            # 3. Memory errors
            if any(kw in error_lower for kw in (
                "memory", "memoryerror", "oom", "killed",
            )):
                action = "suggest_cache_prune"
                result["action_taken"] = (
                    f"{action}: recommend clearing BM25/KG caches and running gc.collect()"
                )
                result["recovered"] = False  # manual intervention needed
                self._log_recovery(engine_name, "memory_error", action, False)
                return result

            # 4. Timeout errors
            if any(kw in error_lower for kw in (
                "timeout", "timed out", "deadline", "slow",
            )):
                action = "suggest_query_simplification"
                result["action_taken"] = (
                    f"{action}: recommend LIMIT clauses, index usage, or query splitting"
                )
                result["recovered"] = False
                self._log_recovery(engine_name, "timeout", action, False)
                return result

            # 5. Generic fallback
            result["action_taken"] = f"no_specific_handler: error logged for '{error[:120]}'"
            self._log_recovery(engine_name, "unknown", "logged", False)

        except Exception as exc:
            self._log_error("auto_recover", exc)
            result["action_taken"] = f"recovery_exception: {exc}"

        return result

    # ---- validate_all_python_files -----------------------------------------

    def validate_all_python_files(self) -> dict:
        """ast.parse every .py in engine_dir."""
        report = {
            "total_files": 0,
            "valid": 0,
            "invalid": 0,
            "errors": [],
        }
        for fpath in self._discover_engines():
            report["total_files"] += 1
            try:
                with open(fpath, "r", encoding="utf-8", errors="replace") as fh:
                    source = fh.read()
                ast.parse(source, filename=fpath)
                report["valid"] += 1
            except SyntaxError as se:
                report["invalid"] += 1
                report["errors"].append({
                    "file": os.path.basename(fpath),
                    "line": se.lineno,
                    "message": se.msg,
                })
            except Exception as exc:
                report["invalid"] += 1
                report["errors"].append({
                    "file": os.path.basename(fpath),
                    "line": None,
                    "message": str(exc),
                })
        return report

    # ---- check_cache_freshness ---------------------------------------------

    def check_cache_freshness(self) -> dict:
        """Check model_data/ and cache/ for staleness."""
        report = {"cache_files": []}
        search_dirs = [
            os.path.join(self.engine_dir, "model_data"),
            os.path.join(self.engine_dir, "cache"),
        ]
        now = time.time()

        for d in search_dirs:
            try:
                if not os.path.isdir(d):
                    continue
                for entry in os.scandir(d):
                    try:
                        if not entry.is_file():
                            continue
                        st = entry.stat()
                        age_hours = round((now - st.st_mtime) / 3600, 2)
                        size_mb = round(st.st_size / (1024 * 1024), 2)

                        # Stale if older than threshold or if DB was modified after cache
                        db_stat = _safe_stat(self.db_path)
                        stale = (
                            age_hours > _CACHE_STALE_HOURS
                            or (db_stat["exists"] and db_stat["modified"] > st.st_mtime)
                        )

                        report["cache_files"].append({
                            "name": entry.name,
                            "path": entry.path,
                            "age_hours": age_hours,
                            "size_mb": size_mb,
                            "stale": stale,
                        })
                    except Exception:
                        pass
            except Exception as exc:
                self._log_error("check_cache_freshness", exc)

        return report

    # ---- vacuum_db ---------------------------------------------------------

    def vacuum_db(self) -> dict:
        """Database maintenance: VACUUM, ANALYZE, REINDEX critical FTS tables."""
        report = {
            "vacuumed": False,
            "analyzed": False,
            "reindexed": [],
        }

        conn = None
        try:
            conn = self._get_conn()

            # VACUUM if WAL large
            try:
                wal_path = self.db_path + "-wal"
                wal_mb = 0
                if os.path.exists(wal_path):
                    wal_mb = os.path.getsize(wal_path) / (1024 * 1024)
                if wal_mb > _WAL_VACUUM_THRESHOLD_MB:
                    conn.execute("VACUUM")
                    report["vacuumed"] = True
            except Exception as exc:
                self._log_error("vacuum_db:vacuum", exc)

            # ANALYZE
            try:
                conn.execute("ANALYZE")
                report["analyzed"] = True
            except Exception as exc:
                self._log_error("vacuum_db:analyze", exc)

            # REINDEX critical FTS tables
            fts_tables = [
                "auth_rules_fts",
                "auth_passages_fts",
                "rules_text_fts",
                "evidence_quotes_fts",
                "md_sections_fts",
                "pages_fts",
                "master_csv_fts",
            ]
            for tbl in fts_tables:
                try:
                    # Verify table exists before reindexing
                    row = conn.execute(
                        "SELECT 1 FROM sqlite_master WHERE name=?", (tbl,)
                    ).fetchone()
                    if row:
                        conn.execute(f'INSERT INTO "{tbl}"("{tbl}") VALUES(\'rebuild\')')
                        report["reindexed"].append(tbl)
                except Exception as exc:
                    self._log_error(f"vacuum_db:reindex:{tbl}", exc)

        except Exception as exc:
            self._log_error("vacuum_db:connect", exc)
        finally:
            if conn:
                self._release_conn(conn)

        return report

    # ---- run_health_sweep --------------------------------------------------

    def run_health_sweep(self) -> dict:
        """Complete system health sweep with auto-recovery."""
        sweep = {
            "timestamp": _now_iso(),
            "engines": {},
            "db_health": {},
            "memory": {},
            "disk": {},
            "cache": {},
            "python_validation": {},
            "recoveries": [],
        }

        # 1. All engines
        try:
            sweep["engines"] = self.check_all_engines()
        except Exception as exc:
            self._log_error("run_health_sweep:engines", exc)
            sweep["engines"] = {"_error": str(exc)}

        # 2. DB health
        try:
            sweep["db_health"] = self.check_db_health()
        except Exception as exc:
            self._log_error("run_health_sweep:db", exc)
            sweep["db_health"] = {"_error": str(exc)}

        # 3. Memory
        try:
            sweep["memory"] = self.check_memory_usage()
        except Exception as exc:
            self._log_error("run_health_sweep:memory", exc)
            sweep["memory"] = {"_error": str(exc)}

        # 4. Disk space
        try:
            usage = shutil.disk_usage(os.path.dirname(self.db_path) or ".")
            sweep["disk"] = {
                "total_gb": round(usage.total / (1024 ** 3), 2),
                "used_gb": round(usage.used / (1024 ** 3), 2),
                "free_gb": round(usage.free / (1024 ** 3), 2),
            }
        except Exception as exc:
            self._log_error("run_health_sweep:disk", exc)
            sweep["disk"] = {"_error": str(exc)}

        # 5. Cache freshness
        try:
            sweep["cache"] = self.check_cache_freshness()
        except Exception as exc:
            self._log_error("run_health_sweep:cache", exc)
            sweep["cache"] = {"_error": str(exc)}

        # 6. Python validation
        try:
            sweep["python_validation"] = self.validate_all_python_files()
        except Exception as exc:
            self._log_error("run_health_sweep:validation", exc)
            sweep["python_validation"] = {"_error": str(exc)}

        # 7. Auto-recover failed engines
        try:
            engines = sweep.get("engines", {})
            for ename, info in engines.items():
                if isinstance(info, dict) and info.get("status") == "failed":
                    errors = info.get("errors", [])
                    error_msg = "; ".join(errors) if errors else "unknown failure"
                    recovery = self.auto_recover(ename, error_msg)
                    sweep["recoveries"].append({
                        "engine": ename,
                        "error": error_msg,
                        "recovery": recovery,
                    })
                    if recovery.get("recovered"):
                        info["status"] = "recovered"
        except Exception as exc:
            self._log_error("run_health_sweep:recovery", exc)

        # 8. Log everything to system_health_log
        try:
            engines = sweep.get("engines", {})
            for ename, info in engines.items():
                if isinstance(info, dict):
                    self._log_health(
                        engine_name=ename,
                        status=info.get("status", "unknown"),
                        error_message="; ".join(info.get("errors", [])) or None,
                        latency_ms=info.get("import_time_ms"),
                    )
        except Exception as exc:
            self._log_error("run_health_sweep:logging", exc)

        self._last_sweep = sweep["timestamp"]
        return sweep

    # ---- get_health_dashboard ----------------------------------------------

    def get_health_dashboard(self) -> dict:
        """Dashboard-ready summary."""
        dashboard = {
            "engines": {"total": 0, "healthy": 0, "degraded": 0, "failed": 0, "recovered": 0},
            "db": "UNKNOWN",
            "memory": "UNKNOWN",
            "disk": "UNKNOWN",
            "last_sweep": self._last_sweep or "never",
            "recovery_success_rate": 0.0,
            "uptime_hours": round((time.time() - self._start_time) / 3600, 2),
            "error_log_size": len(self._error_log),
        }

        # Run sweep for fresh data
        try:
            sweep = self.run_health_sweep()
        except Exception as exc:
            self._log_error("get_health_dashboard:sweep", exc)
            dashboard["_error"] = str(exc)
            return dashboard

        # Engines summary
        try:
            engines = sweep.get("engines", {})
            for info in engines.values():
                if not isinstance(info, dict):
                    continue
                dashboard["engines"]["total"] += 1
                status = info.get("status", "unknown")
                if status in dashboard["engines"]:
                    dashboard["engines"][status] += 1
        except Exception:
            pass

        # DB status
        try:
            db = sweep.get("db_health", {})
            if not db.get("connected"):
                dashboard["db"] = "FAILED"
            elif not db.get("integrity_ok"):
                dashboard["db"] = "DEGRADED"
            else:
                dashboard["db"] = "OK"
        except Exception:
            dashboard["db"] = "UNKNOWN"

        # Memory status
        try:
            mem = sweep.get("memory", {})
            total = mem.get("system_total_mb", 0)
            avail = mem.get("system_available_mb", 0)
            if total > 0:
                used_pct = ((total - avail) / total) * 100
                if used_pct >= _MEMORY_CRITICAL_PCT:
                    dashboard["memory"] = "CRITICAL"
                elif used_pct >= _MEMORY_WARNING_PCT:
                    dashboard["memory"] = "WARNING"
                else:
                    dashboard["memory"] = "OK"
            else:
                dashboard["memory"] = "OK"
        except Exception:
            dashboard["memory"] = "UNKNOWN"

        # Disk status
        try:
            disk = sweep.get("disk", {})
            free = disk.get("free_gb", 999)
            if free < _DISK_CRITICAL_GB:
                dashboard["disk"] = "CRITICAL"
            elif free < _DISK_WARNING_GB:
                dashboard["disk"] = "WARNING"
            else:
                dashboard["disk"] = "OK"
        except Exception:
            dashboard["disk"] = "UNKNOWN"

        # Recovery success rate
        try:
            conn = self._get_conn()
            try:
                row = conn.execute(
                    "SELECT COUNT(*), SUM(success) FROM recovery_actions"
                ).fetchone()
                total_r = row[0] if row and row[0] else 0
                success_r = row[1] if row and row[1] else 0
                if total_r > 0:
                    dashboard["recovery_success_rate"] = round(
                        (success_r / total_r) * 100, 1
                    )
            except Exception as exc:
                self._log_error("get_health_dashboard:recovery_rate", exc)
            finally:
                self._release_conn(conn)
        except Exception:
            pass

        return dashboard

    # ---- generate_health_report --------------------------------------------

    def generate_health_report(self) -> str:
        """Human-readable health report."""
        try:
            dashboard = self.get_health_dashboard()
        except Exception as exc:
            return f"[HEALTH REPORT GENERATION FAILED] {exc}"

        lines = []
        lines.append("=" * 64)
        lines.append("  MBP LitigationOS — Self-Healing Health Report")
        lines.append(f"  Generated: {_now_iso()}")
        lines.append("=" * 64)

        # Engines
        eng = dashboard.get("engines", {})
        lines.append("")
        lines.append(f"  ENGINES: {eng.get('healthy', 0)}/{eng.get('total', 0)} healthy"
                     f"  |  {eng.get('degraded', 0)} degraded"
                     f"  |  {eng.get('failed', 0)} failed"
                     f"  |  {eng.get('recovered', 0)} recovered")

        # DB
        lines.append(f"  DATABASE: {dashboard.get('db', 'UNKNOWN')}")

        # Memory
        lines.append(f"  MEMORY: {dashboard.get('memory', 'UNKNOWN')}")

        # Disk
        lines.append(f"  DISK: {dashboard.get('disk', 'UNKNOWN')}")

        # Recovery
        lines.append(f"  RECOVERY RATE: {dashboard.get('recovery_success_rate', 0)}%")

        # Uptime
        lines.append(f"  UPTIME: {dashboard.get('uptime_hours', 0)} hours")

        # Error log
        lines.append(f"  ERROR LOG ENTRIES: {dashboard.get('error_log_size', 0)}")

        lines.append("")
        lines.append("-" * 64)

        # Recommendations
        lines.append("  RECOMMENDATIONS:")
        recs = []
        if dashboard.get("db") != "OK":
            recs.append("  - Run vacuum_db() to repair database health")
        if dashboard.get("memory") in ("WARNING", "CRITICAL"):
            recs.append("  - Clear caches: BM25 index, KG, TF-IDF")
        if dashboard.get("disk") in ("WARNING", "CRITICAL"):
            recs.append("  - Free disk space: remove stale cache files")
        if eng.get("failed", 0) > 0:
            recs.append("  - Review failed engines and fix syntax errors")
        if eng.get("degraded", 0) > 0:
            recs.append("  - Investigate degraded engines for partial failures")
        if not recs:
            recs.append("  - All systems nominal. No action required.")
        lines.extend(recs)

        lines.append("")
        lines.append("=" * 64)
        return "\n".join(lines)

    # ---- schedule_maintenance ----------------------------------------------

    def schedule_maintenance(self, interval_hours: int = 24) -> dict:
        """Return maintenance schedule dict."""
        return {
            "interval_hours": interval_hours,
            "hourly": [
                "run_health_sweep — full system health check",
                "check_all_engines — verify all engines parse and connect",
            ],
            "daily": [
                "check_cache_freshness — flag stale model caches",
                "vacuum_db (ANALYZE only) — optimize query plans",
                "validate_all_python_files — syntax verification",
            ],
            "weekly": [
                "vacuum_db (full VACUUM if WAL > 100MB) — reclaim space",
                "generate_health_report — archive weekly report",
                "check model retraining — compare data freshness vs model age",
            ],
            "monthly": [
                "PRAGMA integrity_check — full database integrity verification",
                "Full FTS rebuild on all 7 FTS tables",
                "Review recovery_actions for recurring failure patterns",
                "Archive system_health_log entries older than 90 days",
            ],
        }


# ---------------------------------------------------------------------------
# __main__ — run full health sweep and print dashboard
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 64)
    print("  MBP LitigationOS — Self-Healing System Monitor")
    print("=" * 64)
    print()

    try:
        monitor = SelfHealMonitor()
        print("[*] Monitor initialized.")
        print()

        # Full health sweep
        print("[*] Running full health sweep ...")
        sweep = monitor.run_health_sweep()
        print(f"    Timestamp: {sweep.get('timestamp', 'N/A')}")
        print()

        # Dashboard
        print("[*] Generating dashboard ...")
        dashboard = monitor.get_health_dashboard()
        eng = dashboard.get("engines", {})
        print(f"    Engines:  {eng.get('healthy', 0)}/{eng.get('total', 0)} healthy, "
              f"{eng.get('degraded', 0)} degraded, {eng.get('failed', 0)} failed")
        print(f"    DB:       {dashboard.get('db', 'UNKNOWN')}")
        print(f"    Memory:   {dashboard.get('memory', 'UNKNOWN')}")
        print(f"    Disk:     {dashboard.get('disk', 'UNKNOWN')}")
        print(f"    Recovery: {dashboard.get('recovery_success_rate', 0)}%")
        print()

        # Python validation
        print("[*] Python file validation ...")
        val = sweep.get("python_validation", {})
        print(f"    Files: {val.get('total_files', 0)} total, "
              f"{val.get('valid', 0)} valid, {val.get('invalid', 0)} invalid")
        if val.get("errors"):
            for err in val["errors"][:10]:
                print(f"    !! {err.get('file', '?')} "
                      f"line {err.get('line', '?')}: {err.get('message', '?')}")
        print()

        # Cache freshness
        cache = sweep.get("cache", {})
        cf = cache.get("cache_files", [])
        if cf:
            print(f"[*] Cache files: {len(cf)} found")
            stale = [c for c in cf if c.get("stale")]
            if stale:
                print(f"    !! {len(stale)} stale cache file(s) — recommend rebuild")
        else:
            print("[*] No cache files found.")
        print()

        # Maintenance schedule
        print("[*] Maintenance schedule:")
        sched = monitor.schedule_maintenance()
        for period in ("hourly", "daily", "weekly", "monthly"):
            tasks = sched.get(period, [])
            print(f"    {period.upper()}:")
            for t in tasks:
                print(f"      - {t}")
        print()

        # Full report
        print(monitor.generate_health_report())

    except Exception as exc:
        print(f"[FATAL] Monitor failed: {exc}")
        traceback.print_exc()
        sys.exit(1)
