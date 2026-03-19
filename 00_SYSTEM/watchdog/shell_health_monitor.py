"""
SHELL HEALTH MONITOR — LitigationOS Watchdog
=============================================
Lightweight daemon that monitors shell/command execution health.
Tracks session counts, error rates, memory usage, and heartbeat.
"""

import sys
import os
import json
import time
import sqlite3
import platform
from datetime import datetime
from pathlib import Path

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

# ── UTF-8 fix for Windows ────────────────────────────────────────────
if sys.platform == "win32":
    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')
    sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', errors='replace')

# ── Constants ────────────────────────────────────────────────────────
WATCHDOG_DIR = Path(__file__).parent
HEARTBEAT_FILE = WATCHDOG_DIR / "heartbeat.json"
HEALTH_DB = WATCHDOG_DIR / "watchdog.db"
ERROR_LOG = WATCHDOG_DIR / "error_log.jsonl"

# ── Database Setup ───────────────────────────────────────────────────
def _init_health_table():
    """Create shell_health_events table if it doesn't exist."""
    try:
        conn = sqlite3.connect(str(HEALTH_DB))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS shell_health_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT (datetime('now')),
                event_type TEXT NOT NULL,
                details TEXT,
                memory_mb REAL,
                error_count INTEGER DEFAULT 0
            )
        """)
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[WARN] Could not init health table: {e}", file=sys.stderr)

_init_health_table()


# ── Memory Tracking ──────────────────────────────────────────────────
def _get_memory_mb():
    """Get current Python process memory in MB."""
    try:
        import psutil
        proc = psutil.Process(os.getpid())
        return round(proc.memory_info().rss / (1024 * 1024), 1)
    except ImportError:
        # Fallback: read from OS
        if sys.platform == "win32":
            try:
                import ctypes
                from ctypes import wintypes
                class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
                    _fields_ = [("cb", wintypes.DWORD),
                                ("PageFaultCount", wintypes.DWORD),
                                ("PeakWorkingSetSize", ctypes.c_size_t),
                                ("WorkingSetSize", ctypes.c_size_t),
                                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                                ("QuotaPagedPoolUsage", ctypes.c_size_t),
                                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                                ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                                ("PagefileUsage", ctypes.c_size_t),
                                ("PeakPagefileUsage", ctypes.c_size_t)]
                pmc = PROCESS_MEMORY_COUNTERS()
                pmc.cb = ctypes.sizeof(pmc)
                h = ctypes.windll.kernel32.GetCurrentProcess()
                ctypes.windll.psapi.GetProcessMemoryInfo(h, ctypes.byref(pmc), pmc.cb)
                return round(pmc.WorkingSetSize / (1024 * 1024), 1)
            except Exception:
                return -1.0
        return -1.0


# ── Error Rate Tracking ─────────────────────────────────────────────
def _count_recent_errors(minutes=60):
    """Count errors from error_log.jsonl in the last N minutes."""
    counts = {"total": 0, "by_class": {}}
    cutoff = time.time() - (minutes * 60)
    try:
        if ERROR_LOG.exists():
            with open(ERROR_LOG, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        ts = datetime.fromisoformat(entry.get("timestamp", "2000-01-01"))
                        if ts.timestamp() >= cutoff:
                            counts["total"] += 1
                            cls = entry.get("error_class", "unknown")
                            counts["by_class"][cls] = counts["by_class"].get(cls, 0) + 1
                    except (json.JSONDecodeError, ValueError):
                        continue
    except Exception:
        pass
    return counts


# ── Core Functions ───────────────────────────────────────────────────
def log_shell_event(event_type: str, details: str = ""):
    """Log a shell health event to the database."""
    mem = _get_memory_mb()
    err_counts = _count_recent_errors(minutes=5)
    try:
        conn = sqlite3.connect(str(HEALTH_DB))
        conn.execute("""
            INSERT INTO shell_health_events (event_type, details, memory_mb, error_count)
            VALUES (?, ?, ?, ?)
        """, (event_type, details, mem, err_counts["total"]))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[WARN] Could not log event: {e}", file=sys.stderr)
    return {"event_type": event_type, "memory_mb": mem, "error_count": err_counts["total"]}


def check_health() -> dict:
    """Run a full health check and update heartbeat."""
    mem = _get_memory_mb()
    errors = _count_recent_errors(minutes=60)
    errors_5m = _count_recent_errors(minutes=5)

    # Count sessions from DB
    session_stats = {"created": 0, "destroyed": 0}
    try:
        conn = sqlite3.connect(str(HEALTH_DB))
        for etype in ["session_created", "session_destroyed"]:
            row = conn.execute(
                "SELECT COUNT(*) FROM shell_health_events WHERE event_type = ?", (etype,)
            ).fetchone()
            key = etype.replace("session_", "")
            session_stats[key] = row[0] if row else 0
        conn.close()
    except Exception:
        pass

    # Build status
    warnings = []
    if mem > 500:
        warnings.append(f"High memory: {mem}MB")
    if errors_5m["total"] > 10:
        warnings.append(f"High error rate: {errors_5m['total']} errors in 5min")

    # EAGAIN / pipe health tracking
    eagain_count = errors["by_class"].get("pipe_eagain", 0) + errors["by_class"].get("pipe_broken", 0)
    eagain_5m = errors_5m["by_class"].get("pipe_eagain", 0) + errors_5m["by_class"].get("pipe_broken", 0)
    fd_exhaustion = errors["by_class"].get("fd_exhaustion", 0)

    if eagain_5m >= 3:
        warnings.append(f"CRITICAL: {eagain_5m} pipe EAGAIN errors in 5min — reduce agents to 1")
    elif eagain_count >= 5:
        warnings.append(f"HIGH: {eagain_count} pipe EAGAIN errors in 1h — max 2 background agents")
    if fd_exhaustion > 0:
        warnings.append(f"FD exhaustion: {fd_exhaustion} EMFILE errors — close unused connections")

    # Count active node/MCP processes (pipe consumers)
    node_count = 0
    try:
        if HAS_PSUTIL:
            import psutil
            for proc in psutil.process_iter(["name"]):
                try:
                    if "node" in (proc.info["name"] or "").lower():
                        node_count += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        if node_count > 5:
            warnings.append(f"Too many node processes: {node_count} — pipe saturation risk")
    except Exception:
        pass

    status = "WARNING" if warnings else "HEALTHY"

    report = {
        "status": status,
        "timestamp": datetime.now().isoformat(),
        "memory_mb": mem,
        "errors_1h": errors["total"],
        "errors_5m": errors_5m["total"],
        "error_rate_by_class": errors["by_class"],
        "pipe_health": {
            "eagain_1h": eagain_count,
            "eagain_5m": eagain_5m,
            "fd_exhaustion_1h": fd_exhaustion,
            "node_processes": node_count,
            "pipe_status": "CRITICAL" if eagain_5m >= 3 else ("WARN" if eagain_count >= 5 else "OK"),
        },
        "sessions_created": session_stats["created"],
        "sessions_destroyed": session_stats["destroyed"],
        "warnings": warnings,
        "platform": platform.platform(),
        "python": sys.version.split()[0],
    }

    # Write heartbeat
    try:
        with open(HEARTBEAT_FILE, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
    except Exception as e:
        print(f"[WARN] Could not write heartbeat: {e}", file=sys.stderr)

    # Log health check event
    log_shell_event("health_check", json.dumps({"status": status, "mem": mem}))

    return report


def get_health_report() -> str:
    """Get a formatted health report string."""
    r = check_health()
    lines = [
        "═══════════════════════════════════════════",
        f"  Shell Health Monitor — {r['status']}",
        "═══════════════════════════════════════════",
        f"  Time:       {r['timestamp']}",
        f"  Memory:     {r['memory_mb']} MB",
        f"  Errors 1h:  {r['errors_1h']}",
        f"  Errors 5m:  {r['errors_5m']}",
        f"  Pipe:       {r['pipe_health']['pipe_status']} (EAGAIN 1h: {r['pipe_health']['eagain_1h']}, 5m: {r['pipe_health']['eagain_5m']}, nodes: {r['pipe_health']['node_processes']})",
        f"  Sessions:   {r['sessions_created']} created / {r['sessions_destroyed']} destroyed",
        f"  Platform:   {r['platform']}",
        f"  Python:     {r['python']}",
    ]
    if r["warnings"]:
        lines.append("  ⚠ Warnings:")
        for w in r["warnings"]:
            lines.append(f"    - {w}")
    if r["error_rate_by_class"]:
        lines.append("  Error classes (1h):")
        for cls, cnt in sorted(r["error_rate_by_class"].items(), key=lambda x: -x[1]):
            lines.append(f"    {cls}: {cnt}")
    lines.append("═══════════════════════════════════════════")
    return "\n".join(lines)


# ── CLI ──────────────────────────────────────────────────────────────
def main():
    if len(sys.argv) < 2:
        print("Shell Health Monitor — LitigationOS Watchdog")
        print("Usage:")
        print("  python shell_health_monitor.py status   — Show current health")
        print("  python shell_health_monitor.py check    — Run health check, update heartbeat")
        print("  python shell_health_monitor.py log <event_type> [details]  — Log an event")
        return

    cmd = sys.argv[1].lower()

    if cmd in ("status", "check"):
        print(get_health_report())

    elif cmd == "log":
        etype = sys.argv[2] if len(sys.argv) > 2 else "manual"
        details = " ".join(sys.argv[3:]) if len(sys.argv) > 3 else ""
        result = log_shell_event(etype, details)
        print(f"Logged: {result['event_type']} | Memory: {result['memory_mb']}MB | Recent errors: {result['error_count']}")

    elif cmd == "heartbeat":
        # Quick heartbeat update
        check_health()
        print(f"Heartbeat written to {HEARTBEAT_FILE}")

    else:
        print(f"Unknown command: {cmd}")


if __name__ == "__main__":
    main()
