"""
system_health.py — LitigationOS System Health Dashboard
========================================================
LitigationOS 2026 v1.0 — Pigors v. Watson

Standalone health check: DB connectivity, table counts, skills import,
convergence engine status, upcoming deadlines, memory retriever, filesystem.

Usage:
    python system_health.py
    python system_health.py --json    (machine-readable output)

No network calls. Pure SQLite + filesystem checks.
"""

import sqlite3
import os
import sys
import importlib
import json
import traceback
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple

# ── Paths ─────────────────────────────────────────────────────────────
DB_PATH = r"C:\Users\andre\litigation_context.db"
SYSTEM_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LITIGATION_ROOT = os.path.dirname(SYSTEM_ROOT)
SKILLS_DIR = os.path.join(SYSTEM_ROOT, "skills")
TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))

EXPECTED_DIRS = {
    "00_SYSTEM": os.path.join(LITIGATION_ROOT, "00_SYSTEM"),
    "01_INTAKE": os.path.join(LITIGATION_ROOT, "01_INTAKE"),
    "02_AUTHORITY": os.path.join(LITIGATION_ROOT, "02_AUTHORITY"),
    "03_EVIDENCE": os.path.join(LITIGATION_ROOT, "03_EVIDENCE"),
    "04_COURT_FILINGS": os.path.join(LITIGATION_ROOT, "04_COURT_FILINGS"),
    "05_ANALYSIS": os.path.join(LITIGATION_ROOT, "05_ANALYSIS"),
    "06_VEHICLES": os.path.join(LITIGATION_ROOT, "06_VEHICLES"),
    "07_VALIDATION": os.path.join(LITIGATION_ROOT, "07_VALIDATION"),
    "08_APPS": os.path.join(LITIGATION_ROOT, "08_APPS"),
}

KEY_TABLES = [
    "auth_rules", "auth_authority_passages", "evidence_quotes",
    "master_citations", "documents", "claims", "deadlines",
    "docket_events", "vehicles", "contradiction_map",
    "impeachment_items", "judicial_violations", "adversary_models",
    "pages", "md_sections", "atoms", "convergence_log",
]

SKILL_MODULES = [
    "skill_convergence_engine",
    "skill_chess_mode",
    "skill_timeline_builder",
    "skill_rose_glass_coherence",
    "skill_business_corporate",
    "skill_defenses_setoffs",
    "skill_landlord_tenant",
    "skill_michigan_tort_lawsuit",
    "skill_torts_claims",
]


def _separator(title: str) -> str:
    return f"\n{'─' * 60}\n  {title}\n{'─' * 60}"


def check_db_connectivity() -> Dict[str, Any]:
    """Check DB connectivity and basic stats."""
    result = {"status": "FAIL", "path": DB_PATH, "size_mb": 0, "table_count": 0}
    try:
        if not os.path.exists(DB_PATH):
            result["error"] = "Database file not found"
            return result
        result["size_mb"] = round(os.path.getsize(DB_PATH) / (1024 * 1024), 1)
        conn = sqlite3.connect(DB_PATH, timeout=10)
        conn.execute("PRAGMA journal_mode")  # quick connectivity test
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
        result["table_count"] = cur.fetchone()[0]
        conn.close()
        result["status"] = "OK"
    except Exception as e:
        result["error"] = str(e)
    return result


def check_table_row_counts() -> List[Tuple[str, int, str]]:
    """Return (table_name, row_count, status) for key tables."""
    results = []
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10)
        conn.row_factory = sqlite3.Row
        for table in KEY_TABLES:
            try:
                cur = conn.execute(f"SELECT COUNT(*) as cnt FROM [{table}]")
                count = cur.fetchone()["cnt"]
                results.append((table, count, "OK"))
            except Exception:
                results.append((table, -1, "MISSING"))
        conn.close()
    except Exception as e:
        results.append(("__connection__", -1, f"DB ERROR: {e}"))
    return results


def check_skills_import() -> List[Tuple[str, str, str]]:
    """Try importing each skill module. Returns (name, status, error)."""
    results = []
    # Ensure skills dir is on path
    if SKILLS_DIR not in sys.path:
        sys.path.insert(0, SKILLS_DIR)
    if SYSTEM_ROOT not in sys.path:
        sys.path.insert(0, SYSTEM_ROOT)

    for skill in SKILL_MODULES:
        try:
            importlib.import_module(skill)
            results.append((skill, "OK", ""))
        except Exception as e:
            results.append((skill, "FAIL", str(e)[:80]))
    return results


def check_convergence_status() -> Dict[str, Any]:
    """Check convergence engine status from DB."""
    result = {"status": "UNKNOWN", "total_cycles": 0, "latest_cycle": None}
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10)
        conn.row_factory = sqlite3.Row
        # Check if convergence_log table exists
        cur = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='convergence_log'"
        )
        if not cur.fetchone():
            result["status"] = "NO TABLE"
            conn.close()
            return result
        cur = conn.execute("SELECT COUNT(*) as cnt FROM convergence_log")
        result["total_cycles"] = cur.fetchone()["cnt"]
        cur = conn.execute(
            "SELECT * FROM convergence_log ORDER BY rowid DESC LIMIT 1"
        )
        row = cur.fetchone()
        if row:
            result["latest_cycle"] = dict(row)
            result["status"] = "ACTIVE"
        else:
            result["status"] = "EMPTY"
        conn.close()
    except Exception as e:
        result["status"] = f"ERROR: {e}"
    return result


def check_upcoming_deadlines(days_ahead: int = 30) -> List[Dict[str, Any]]:
    """Query deadlines table for upcoming items."""
    results = []
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10)
        conn.row_factory = sqlite3.Row
        # Check table exists
        cur = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='deadlines'"
        )
        if not cur.fetchone():
            return [{"error": "deadlines table not found"}]
        # Try to get upcoming deadlines
        try:
            cur = conn.execute(
                """SELECT * FROM deadlines
                   WHERE due_date_iso >= date('now')
                     AND due_date_iso <= date('now', ?)
                   ORDER BY due_date_iso ASC
                   LIMIT 10""",
                (f"+{days_ahead} days",),
            )
            rows = cur.fetchall()
            results = [dict(r) for r in rows]
        except Exception:
            # Fallback: just get recent deadlines regardless of date filtering
            cur = conn.execute("SELECT * FROM deadlines ORDER BY rowid DESC LIMIT 10")
            rows = cur.fetchall()
            results = [dict(r) for r in rows]
            if results:
                results.insert(0, {"note": "Date filter failed; showing latest entries"})
        conn.close()
    except Exception as e:
        results.append({"error": str(e)})
    return results


def check_memory_retriever() -> Dict[str, str]:
    """Check if memory_retriever.py is importable and has expected attributes."""
    result = {"status": "UNKNOWN"}
    try:
        if TOOLS_DIR not in sys.path:
            sys.path.insert(0, TOOLS_DIR)
        if SYSTEM_ROOT not in sys.path:
            sys.path.insert(0, SYSTEM_ROOT)
        spec = importlib.util.find_spec("memory_retriever")
        if spec is None:
            result["status"] = "NOT FOUND"
            return result
        mod = importlib.import_module("memory_retriever")
        result["status"] = "OK"
        result["path"] = str(spec.origin) if spec.origin else "unknown"
        # Check for key objects
        for attr in ["DB_PATH", "VEHICLES_ROOT", "DOCUMENT_TOPICS"]:
            result[f"has_{attr}"] = "yes" if hasattr(mod, attr) else "no"
    except Exception as e:
        result["status"] = f"IMPORT ERROR: {str(e)[:80]}"
    return result


def check_filesystem() -> List[Tuple[str, str]]:
    """Check expected directories exist."""
    results = []
    for name, path in EXPECTED_DIRS.items():
        if os.path.isdir(path):
            count = len(os.listdir(path))
            results.append((name, f"OK ({count} items)"))
        else:
            results.append((name, "MISSING"))
    return results


def run_full_health_check() -> Dict[str, Any]:
    """Run all health checks and return combined report."""
    report = {}
    report["timestamp"] = datetime.now().isoformat()
    report["db"] = check_db_connectivity()
    report["table_rows"] = check_table_row_counts()
    report["skills"] = check_skills_import()
    report["convergence"] = check_convergence_status()
    report["deadlines"] = check_upcoming_deadlines()
    report["memory_retriever"] = check_memory_retriever()
    report["filesystem"] = check_filesystem()
    return report


def print_report(report: Dict[str, Any]) -> None:
    """Print a clean, formatted text report."""
    print("=" * 60)
    print("  LitigationOS System Health Report")
    print(f"  Generated: {report['timestamp']}")
    print("=" * 60)

    # ── DB Connectivity ──
    db = report["db"]
    print(_separator("DATABASE CONNECTIVITY"))
    print(f"  Path:       {db['path']}")
    print(f"  Status:     {db['status']}")
    print(f"  Size:       {db['size_mb']} MB")
    print(f"  Tables:     {db['table_count']}")
    if "error" in db:
        print(f"  ERROR:      {db['error']}")

    # ── Table Row Counts ──
    print(_separator("KEY TABLE ROW COUNTS"))
    total_rows = 0
    for name, count, status in report["table_rows"]:
        if status == "OK":
            total_rows += count
            print(f"  {name:<35} {count:>10,}  {status}")
        else:
            print(f"  {name:<35} {'---':>10}  {status}")
    print(f"  {'TOTAL (key tables)':<35} {total_rows:>10,}")

    # ── Skills Import ──
    print(_separator("SKILLS IMPORT CHECK"))
    ok_count = sum(1 for _, s, _ in report["skills"] if s == "OK")
    fail_count = len(report["skills"]) - ok_count
    for name, status, error in report["skills"]:
        icon = "✓" if status == "OK" else "✗"
        line = f"  {icon} {name:<40} {status}"
        if error:
            line += f"  ({error})"
        print(line)
    print(f"  Summary: {ok_count} OK, {fail_count} FAIL")

    # ── Convergence Engine ──
    print(_separator("CONVERGENCE ENGINE"))
    conv = report["convergence"]
    print(f"  Status:       {conv['status']}")
    print(f"  Total cycles: {conv['total_cycles']}")
    if conv.get("latest_cycle"):
        latest = conv["latest_cycle"]
        for k, v in list(latest.items())[:5]:
            print(f"  Latest {k}: {v}")

    # ── Upcoming Deadlines ──
    print(_separator("UPCOMING DEADLINES (next 30 days)"))
    deadlines = report["deadlines"]
    if not deadlines:
        print("  No upcoming deadlines found.")
    else:
        for d in deadlines:
            if "error" in d:
                print(f"  ERROR: {d['error']}")
            elif "note" in d:
                print(f"  NOTE: {d['note']}")
            else:
                title = d.get("title", d.get("description", "untitled"))
                due = d.get("due_date_iso", "no date")
                status = d.get("status", "unknown")
                print(f"  [{status:^10}] {due}  {title}")

    # ── Memory Retriever ──
    print(_separator("MEMORY RETRIEVER"))
    mem = report["memory_retriever"]
    for k, v in mem.items():
        print(f"  {k:<20} {v}")

    # ── Filesystem ──
    print(_separator("FILESYSTEM STRUCTURE"))
    for name, status in report["filesystem"]:
        icon = "✓" if status.startswith("OK") else "✗"
        print(f"  {icon} {name:<25} {status}")

    # ── Overall ──
    print(_separator("OVERALL ASSESSMENT"))
    issues = []
    if db["status"] != "OK":
        issues.append("Database connectivity FAILED")
    if fail_count > 0:
        issues.append(f"{fail_count} skill(s) failed to import")
    missing_dirs = [n for n, s in report["filesystem"] if not s.startswith("OK")]
    if missing_dirs:
        issues.append(f"Missing directories: {', '.join(missing_dirs)}")
    if conv["status"] not in ("ACTIVE", "EMPTY"):
        issues.append(f"Convergence engine: {conv['status']}")

    if not issues:
        print("  ✓ ALL SYSTEMS OPERATIONAL")
    else:
        print(f"  ⚠ {len(issues)} issue(s) detected:")
        for issue in issues:
            print(f"    • {issue}")
    print()


def main():
    json_mode = "--json" in sys.argv
    try:
        report = run_full_health_check()
        if json_mode:
            # Convert tuples to dicts for JSON serialization
            report["table_rows"] = [
                {"table": t, "rows": r, "status": s}
                for t, r, s in report["table_rows"]
            ]
            report["skills"] = [
                {"module": m, "status": s, "error": e}
                for m, s, e in report["skills"]
            ]
            report["filesystem"] = [
                {"directory": d, "status": s}
                for d, s in report["filesystem"]
            ]
            print(json.dumps(report, indent=2, default=str))
        else:
            print_report(report)
    except Exception as e:
        print(f"FATAL ERROR running health check: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
