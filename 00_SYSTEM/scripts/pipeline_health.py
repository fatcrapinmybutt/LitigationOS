#!/usr/bin/env python3
"""
pipeline_health.py — Comprehensive Pipeline Health Check for LitigationOS
==========================================================================
Checks all databases for corruption, verifies WAL mode, reports table/row
counts for the central litigation_context.db, detects orphaned temp files,
and outputs a machine-readable JSON report.

Usage:
    python pipeline_health.py              # Print report to stdout
    python pipeline_health.py --json       # JSON to stdout only
    python pipeline_health.py --file       # Write to PIPELINE_HEALTH.json

Output:
    00_SYSTEM/PIPELINE_HEALTH.json
"""

import json
import os
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path

# Force UTF-8 output on Windows
sys.stdout = open(
    sys.stdout.fileno(), mode="w", encoding="utf-8",
    errors="replace", closefd=False,
)

LITIGOS_ROOT = Path(r"C:\Users\andre\LitigationOS")
REPORT_PATH = LITIGOS_ROOT / "00_SYSTEM" / "PIPELINE_HEALTH.json"
CENTRAL_DB = LITIGOS_ROOT / "litigation_context.db"

# Directories to scan for .db files
DB_SCAN_DIRS = [
    LITIGOS_ROOT,
    LITIGOS_ROOT / "databases",
    LITIGOS_ROOT / "00_SYSTEM" / "pipeline",
    LITIGOS_ROOT / "00_SYSTEM" / "pipeline" / "agents",
    LITIGOS_ROOT / "00_SYSTEM" / "novel",
    LITIGOS_ROOT / "00_SYSTEM" / "darwin",
    LITIGOS_ROOT / "00_SYSTEM" / "manifests",
    LITIGOS_ROOT / "00_SYSTEM" / "local_model",
    LITIGOS_ROOT / "09_DATA",
]

# Directories to check for orphaned temp files
TEMP_SCAN_DIRS = [
    LITIGOS_ROOT / "temp",
    LITIGOS_ROOT / "00_SYSTEM" / "temp",
    LITIGOS_ROOT / "00_SYSTEM" / "pipeline" / "temp",
]

TEMP_EXTENSIONS = {".tmp", ".bak", ".pyc", ".log", ".swp", ".pid"}


def _connect_readonly(db_path: str, timeout: int = 10) -> sqlite3.Connection:
    """Open a read-only connection with proper PRAGMAs."""
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=timeout)
    conn.execute("PRAGMA busy_timeout=60000")
    return conn


def check_database(db_path: Path) -> dict:
    """Run integrity and WAL checks on a single database."""
    result = {
        "path": str(db_path),
        "name": db_path.name,
        "size_bytes": 0,
        "size_kb": 0,
        "integrity": "unknown",
        "journal_mode": "unknown",
        "wal_mode": False,
        "table_count": 0,
        "error": None,
    }

    if not db_path.exists():
        result["integrity"] = "missing"
        result["error"] = "File does not exist"
        return result

    try:
        result["size_bytes"] = db_path.stat().st_size
        result["size_kb"] = result["size_bytes"] // 1024
    except OSError as exc:
        result["error"] = f"Cannot stat file: {exc}"
        return result

    if result["size_bytes"] == 0:
        result["integrity"] = "empty"
        return result

    try:
        conn = _connect_readonly(str(db_path))
    except (sqlite3.OperationalError, sqlite3.DatabaseError) as exc:
        result["integrity"] = "cannot_open"
        result["error"] = str(exc)
        return result

    try:
        # Integrity check
        row = conn.execute("PRAGMA integrity_check(1)").fetchone()
        result["integrity"] = "ok" if row and row[0] == "ok" else "corrupt"
        if result["integrity"] != "ok" and row:
            result["error"] = row[0]

        # Journal mode
        jm = conn.execute("PRAGMA journal_mode").fetchone()
        if jm:
            result["journal_mode"] = jm[0]
            result["wal_mode"] = jm[0].lower() == "wal"

        # Table count
        tc = conn.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
        ).fetchone()
        result["table_count"] = tc[0] if tc else 0

    except (sqlite3.OperationalError, sqlite3.DatabaseError) as exc:
        if result["integrity"] == "unknown":
            result["integrity"] = "error"
        result["error"] = str(exc)
    finally:
        conn.close()

    return result


def check_central_db() -> dict:
    """Detailed inspection of litigation_context.db: tables, row counts, size."""
    info = {
        "path": str(CENTRAL_DB),
        "exists": CENTRAL_DB.exists(),
        "size_mb": 0,
        "table_count": 0,
        "total_rows": 0,
        "tables": [],
        "wal_mode": False,
        "integrity": "unknown",
    }

    if not info["exists"]:
        info["integrity"] = "missing"
        return info

    info["size_mb"] = round(CENTRAL_DB.stat().st_size / (1024 * 1024), 1)

    try:
        conn = _connect_readonly(str(CENTRAL_DB), timeout=30)
    except Exception as exc:
        info["integrity"] = "cannot_open"
        info["error"] = str(exc)
        return info

    try:
        # Integrity (quick — limit to 1 page)
        row = conn.execute("PRAGMA integrity_check(1)").fetchone()
        info["integrity"] = "ok" if row and row[0] == "ok" else "suspect"

        # Journal mode
        jm = conn.execute("PRAGMA journal_mode").fetchone()
        info["wal_mode"] = jm and jm[0].lower() == "wal"

        # Enumerate tables and row counts
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        info["table_count"] = len(tables)

        total_rows = 0
        table_details = []
        for (tname,) in tables:
            try:
                rc = conn.execute(f'SELECT COUNT(*) FROM "{tname}"').fetchone()
                row_count = rc[0] if rc else 0
            except Exception:
                row_count = -1  # table exists but can't count (e.g. virtual)
            total_rows += max(row_count, 0)
            table_details.append({"name": tname, "rows": row_count})

        info["total_rows"] = total_rows
        # Include top-50 tables by row count for the report
        table_details.sort(key=lambda t: t["rows"], reverse=True)
        info["tables"] = table_details[:50]

    except Exception as exc:
        info["error"] = str(exc)
    finally:
        conn.close()

    return info


def find_databases() -> list[Path]:
    """Discover all .db files in scan directories."""
    seen = set()
    dbs = []
    for scan_dir in DB_SCAN_DIRS:
        if not scan_dir.exists():
            continue
        # Non-recursive for repo root, recursive for subdirs
        pattern = "*.db" if scan_dir == LITIGOS_ROOT else "**/*.db"
        for db_file in scan_dir.glob(pattern):
            real = db_file.resolve()
            if real not in seen and real.suffix == ".db":
                seen.add(real)
                dbs.append(real)
    return sorted(dbs)


def find_orphaned_temp_files() -> list[dict]:
    """Scan temp directories for stale files."""
    orphans = []
    for temp_dir in TEMP_SCAN_DIRS:
        if not temp_dir.is_dir():
            continue
        for item in temp_dir.rglob("*"):
            if item.is_file() and item.suffix.lower() in TEMP_EXTENSIONS:
                try:
                    age_hours = (time.time() - item.stat().st_mtime) / 3600
                except OSError:
                    age_hours = -1
                orphans.append({
                    "path": str(item),
                    "size_kb": item.stat().st_size // 1024 if item.exists() else 0,
                    "age_hours": round(age_hours, 1),
                    "extension": item.suffix,
                })
    return orphans


def generate_report() -> dict:
    """Generate the full pipeline health report."""
    t0 = time.time()
    report = {
        "generated_at": datetime.now().isoformat(),
        "engine": "LitigationOS Pipeline Health Check v1.0",
        "litigos_root": str(LITIGOS_ROOT),
    }

    # ── Central DB detailed analysis ──
    print("Checking central database...", file=sys.stderr, flush=True)
    report["central_db"] = check_central_db()

    # ── All databases ──
    print("Scanning for databases...", file=sys.stderr, flush=True)
    db_files = find_databases()
    report["database_count"] = len(db_files)

    db_results = []
    ok_count = 0
    wal_count = 0
    corrupt_count = 0
    for db_path in db_files:
        r = check_database(db_path)
        db_results.append(r)
        if r["integrity"] == "ok":
            ok_count += 1
        elif r["integrity"] in ("corrupt", "error"):
            corrupt_count += 1
        if r["wal_mode"]:
            wal_count += 1

    report["databases"] = db_results
    report["summary"] = {
        "total_databases": len(db_files),
        "healthy": ok_count,
        "corrupt_or_error": corrupt_count,
        "empty": sum(1 for r in db_results if r["integrity"] == "empty"),
        "wal_enabled": wal_count,
        "non_wal": len(db_files) - wal_count,
    }

    # ── Orphaned temp files ──
    print("Checking for orphaned temp files...", file=sys.stderr, flush=True)
    orphans = find_orphaned_temp_files()
    report["orphaned_temp_files"] = {
        "count": len(orphans),
        "total_size_kb": sum(o["size_kb"] for o in orphans),
        "files": orphans[:100],  # cap at 100 entries
    }

    # ── Overall health verdict ──
    if corrupt_count > 0:
        verdict = "CRITICAL"
    elif report["central_db"]["integrity"] != "ok":
        verdict = "WARNING"
    elif len(orphans) > 50:
        verdict = "NEEDS_CLEANUP"
    else:
        verdict = "HEALTHY"

    report["verdict"] = verdict
    report["elapsed_seconds"] = round(time.time() - t0, 2)

    return report


def print_summary(report: dict) -> None:
    """Print a human-readable summary to stdout."""
    s = report.get("summary", {})
    cdb = report.get("central_db", {})
    orp = report.get("orphaned_temp_files", {})

    print(f"\n{'='*60}")
    print(f"  LitigationOS Pipeline Health — {report.get('verdict', '?')}")
    print(f"{'='*60}")
    print(f"  Generated: {report.get('generated_at', '?')}")
    print(f"  Central DB: {cdb.get('size_mb', 0)} MB, "
          f"{cdb.get('table_count', 0)} tables, "
          f"{cdb.get('total_rows', 0):,} rows, "
          f"integrity={cdb.get('integrity', '?')}")
    print(f"  Databases: {s.get('total_databases', 0)} found, "
          f"{s.get('healthy', 0)} healthy, "
          f"{s.get('corrupt_or_error', 0)} corrupt/error, "
          f"{s.get('empty', 0)} empty")
    print(f"  WAL mode: {s.get('wal_enabled', 0)}/{s.get('total_databases', 0)} databases")
    print(f"  Temp files: {orp.get('count', 0)} orphans ({orp.get('total_size_kb', 0)} KB)")
    print(f"  Elapsed: {report.get('elapsed_seconds', 0)}s")
    print(f"{'='*60}\n")

    # Show corrupt databases if any
    corrupt = [d for d in report.get("databases", [])
               if d["integrity"] in ("corrupt", "error")]
    if corrupt:
        print("⚠️  CORRUPT/ERROR DATABASES:")
        for d in corrupt:
            print(f"  - {d['name']}: {d['integrity']} — {d.get('error', '?')}")
        print()

    # Show top-10 tables in central DB
    tables = cdb.get("tables", [])
    if tables:
        print("Top 10 tables in litigation_context.db:")
        for t in tables[:10]:
            print(f"  {t['name']:40s} {t['rows']:>10,} rows")
        print()


if __name__ == "__main__":
    report = generate_report()

    if "--json" in sys.argv:
        print(json.dumps(report, indent=2, default=str))
    elif "--file" in sys.argv:
        REPORT_PATH.write_text(
            json.dumps(report, indent=2, default=str), encoding="utf-8",
        )
        print(f"Report written to {REPORT_PATH}")
        print_summary(report)
    else:
        print_summary(report)
        # Always write JSON report
        REPORT_PATH.write_text(
            json.dumps(report, indent=2, default=str), encoding="utf-8",
        )
        print(f"JSON report: {REPORT_PATH}")
