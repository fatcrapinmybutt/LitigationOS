#!/usr/bin/env python3
"""
health_check.py - System health monitor for LitigationOS.

Checks drives, database integrity, FTS5 indexes, Ollama status,
engine inventory, WAL size, and available memory.

CLI:
    python health_check.py
"""

import os
import sys
import json
import time
import shutil
import sqlite3
import ctypes
import glob as globmod
import datetime

# ── Paths ────────────────────────────────────────────────────────────────────
LOS_ROOT   = r"C:\Users\andre\LitigationOS"
DB_PATH    = os.path.join(LOS_ROOT, "litigation_context.db")
ENGINE_DIR = os.path.join(LOS_ROOT, "00_SYSTEM", "engines")
REPORT_OUT = os.path.join(LOS_ROOT, "00_SYSTEM", "health_report.json")

DRIVES = {
    "C:": {"label": "System",          "warn_gb": 5, "crit_gb": 2},
    "I:": {"label": "Litigation data", "warn_gb": 0, "crit_gb": 0},
    "F:": {"label": "Reference data",  "warn_gb": 0, "crit_gb": 0},
    "G:": {"label": "Evidence data",   "warn_gb": 0, "crit_gb": 0},
}


def fmt_bytes(n):
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(n) < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"


# ── Individual checks ────────────────────────────────────────────────────────

def check_drives():
    """Check drive accessibility and free space."""
    results = []
    for drive, info in DRIVES.items():
        entry = {"drive": drive, "label": info["label"]}
        try:
            total, used, free = shutil.disk_usage(drive + "\\")
            free_gb = free / (1024 ** 3)
            entry["accessible"] = True
            entry["total"]      = fmt_bytes(total)
            entry["free"]       = fmt_bytes(free)
            entry["free_gb"]    = round(free_gb, 2)
            if info["crit_gb"] and free_gb < info["crit_gb"]:
                entry["status"] = "CRITICAL"
            elif info["warn_gb"] and free_gb < info["warn_gb"]:
                entry["status"] = "WARNING"
            else:
                entry["status"] = "OK"
        except Exception as exc:
            entry["accessible"] = False
            entry["status"]     = "UNAVAILABLE"
            entry["error"]      = str(exc)
        results.append(entry)
    return results


def check_db_integrity():
    """Run PRAGMA integrity_check and gather DB stats."""
    result = {"path": DB_PATH}
    if not os.path.exists(DB_PATH):
        result["status"] = "MISSING"
        return result
    try:
        result["size"] = fmt_bytes(os.path.getsize(DB_PATH))
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        # Integrity
        cur.execute("PRAGMA integrity_check;")
        ic = cur.fetchone()[0]
        result["integrity"] = ic
        result["status"] = "OK" if ic == "ok" else "FAIL"

        # Table count
        cur.execute("SELECT count(*) FROM sqlite_master WHERE type='table';")
        result["table_count"] = cur.fetchone()[0]

        # Table list
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        result["tables"] = [r[0] for r in cur.fetchall()]

        conn.close()
    except Exception as exc:
        result["status"] = "ERROR"
        result["error"]  = str(exc)
    return result


def check_fts5():
    """Check FTS5 virtual tables and run a sample query."""
    result = {"indexes": [], "sample_query": None}
    if not os.path.exists(DB_PATH):
        result["status"] = "SKIPPED"
        return result
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND sql LIKE '%fts5%' "
            "ORDER BY name;"
        )
        fts_tables = [r[0] for r in cur.fetchall()]
        result["indexes"] = fts_tables
        result["count"]   = len(fts_tables)

        if fts_tables:
            tbl = fts_tables[0]
            try:
                cur.execute(f"SELECT count(*) FROM [{tbl}];")
                cnt = cur.fetchone()[0]
                result["sample_query"] = {"table": tbl, "row_count": cnt, "status": "OK"}
            except Exception as exc:
                result["sample_query"] = {"table": tbl, "status": "ERROR", "error": str(exc)}
        result["status"] = "OK"
        conn.close()
    except Exception as exc:
        result["status"] = "ERROR"
        result["error"]  = str(exc)
    return result


def check_wal():
    """Check WAL file size."""
    wal_path = DB_PATH + "-wal"
    result = {"path": wal_path}
    if not os.path.exists(wal_path):
        result["status"] = "NO_WAL"
        result["size"]   = "0 B"
        return result
    size = os.path.getsize(wal_path)
    result["size"]    = fmt_bytes(size)
    result["size_mb"] = round(size / (1024 * 1024), 2)
    if size > 500 * 1024 * 1024:
        result["status"] = "WARNING"
    else:
        result["status"] = "OK"
    return result


def check_ollama():
    """Check Ollama status and loaded models."""
    import requests
    url = os.environ.get("OLLAMA_URL", "http://localhost:11434")
    result = {"endpoint": url}
    try:
        r = requests.get(f"{url}/api/tags", timeout=10)
        r.raise_for_status()
        models = [m["name"] for m in r.json().get("models", [])]
        result["models"]    = models
        result["connected"] = True

        need = ["qwen2.5:7b", "nomic-embed-text"]
        missing = [m for m in need if not any(m in loaded for loaded in models)]
        result["required_models"] = need
        result["missing_models"]  = missing
        result["status"] = "OK" if not missing else "WARNING"
    except Exception as exc:
        result["connected"] = False
        result["status"]    = "OFFLINE"
        result["error"]     = str(exc)
    return result


def check_engines():
    """List all .py engine files."""
    result = {"directory": ENGINE_DIR}
    if not os.path.isdir(ENGINE_DIR):
        result["status"] = "MISSING"
        return result
    py_files = sorted(globmod.glob(os.path.join(ENGINE_DIR, "*.py")))
    result["engines"] = [os.path.basename(f) for f in py_files]
    result["count"]   = len(py_files)
    result["status"]  = "OK"
    return result


def check_memory():
    """Check available RAM (Windows)."""
    result = {}
    try:
        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
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
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(mem))
        result["total"]       = fmt_bytes(mem.ullTotalPhys)
        result["available"]   = fmt_bytes(mem.ullAvailPhys)
        result["used_pct"]    = mem.dwMemoryLoad
        result["avail_gb"]    = round(mem.ullAvailPhys / (1024 ** 3), 2)
        result["status"]      = "OK" if mem.dwMemoryLoad < 90 else "WARNING"
    except Exception as exc:
        result["status"] = "ERROR"
        result["error"]  = str(exc)
    return result


# ── Main report ──────────────────────────────────────────────────────────────

def run_health_check():
    ts = datetime.datetime.now().isoformat()
    print("=" * 64)
    print("  LitigationOS Health Check")
    print(f"  Timestamp: {ts}")
    print("=" * 64)

    report = {"timestamp": ts, "checks": {}}

    # 1. Drives
    print("\n[1/7] Drive checks …")
    drives = check_drives()
    report["checks"]["drives"] = drives
    for d in drives:
        icon = {"OK": "✓", "WARNING": "⚠", "CRITICAL": "✗"}.get(d["status"], "?")
        line = f"  {icon} {d['drive']} ({d['label']}): {d['status']}"
        if d.get("accessible"):
            line += f" — {d['free']} free"
        print(line)

    # 2. DB integrity
    print("\n[2/7] Database integrity …")
    db = check_db_integrity()
    report["checks"]["database"] = db
    icon = "✓" if db.get("status") == "OK" else "✗"
    print(f"  {icon} Integrity: {db.get('integrity', db.get('status'))}")
    if db.get("table_count"):
        print(f"    Tables: {db['table_count']}  Size: {db.get('size', '?')}")

    # 3. FTS5
    print("\n[3/7] FTS5 indexes …")
    fts = check_fts5()
    report["checks"]["fts5"] = fts
    print(f"  {'✓' if fts['status'] == 'OK' else '⚠'} {fts.get('count', 0)} FTS5 index(es)")
    if fts.get("sample_query"):
        sq = fts["sample_query"]
        print(f"    Sample: {sq['table']} → {sq.get('row_count', '?')} rows ({sq['status']})")

    # 4. WAL
    print("\n[4/7] WAL file …")
    wal = check_wal()
    report["checks"]["wal"] = wal
    icon = {"OK": "✓", "WARNING": "⚠", "NO_WAL": "–"}.get(wal["status"], "?")
    print(f"  {icon} WAL: {wal['size']} ({wal['status']})")

    # 5. Ollama
    print("\n[5/7] Ollama status …")
    oll = check_ollama()
    report["checks"]["ollama"] = oll
    if oll.get("connected"):
        icon = "✓" if oll["status"] == "OK" else "⚠"
        print(f"  {icon} Connected — {len(oll.get('models', []))} model(s)")
        if oll.get("missing_models"):
            print(f"    ⚠ Missing: {', '.join(oll['missing_models'])}")
    else:
        print(f"  ✗ Ollama offline: {oll.get('error', 'unknown')}")

    # 6. Engines
    print("\n[6/7] Engine inventory …")
    eng = check_engines()
    report["checks"]["engines"] = eng
    print(f"  ✓ {eng.get('count', 0)} engine(s) in {ENGINE_DIR}")

    # 7. Memory
    print("\n[7/7] Memory …")
    mem = check_memory()
    report["checks"]["memory"] = mem
    if mem.get("status") != "ERROR":
        icon = "✓" if mem.get("status") == "OK" else "⚠"
        print(f"  {icon} {mem.get('available', '?')} available "
              f"({mem.get('used_pct', '?')}% used)")
    else:
        print(f"  ✗ {mem.get('error', 'unknown')}")

    # Overall
    all_statuses = []
    for v in report["checks"].values():
        if isinstance(v, list):
            all_statuses.extend(item.get("status", "") for item in v)
        elif isinstance(v, dict):
            all_statuses.append(v.get("status", ""))

    if any(s in ("CRITICAL", "FAIL") for s in all_statuses):
        report["overall"] = "CRITICAL"
    elif any(s in ("WARNING", "OFFLINE", "UNAVAILABLE") for s in all_statuses):
        report["overall"] = "WARNING"
    else:
        report["overall"] = "HEALTHY"

    print("\n" + "=" * 64)
    print(f"  Overall: {report['overall']}")
    print("=" * 64)

    # Save JSON report
    try:
        os.makedirs(os.path.dirname(REPORT_OUT), exist_ok=True)
        with open(REPORT_OUT, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"\n  Report saved → {REPORT_OUT}")
    except Exception as exc:
        print(f"\n  ⚠ Could not save report: {exc}")

    return report


if __name__ == "__main__":
    run_health_check()
