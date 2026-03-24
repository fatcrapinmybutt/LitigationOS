#!/usr/bin/env python3
"""
db_health_check.py — Integrity audit for all LitigationOS SQLite databases
===========================================================================
Scans databases/, 09_DATA/, and repo root for .db files.
Runs PRAGMA integrity_check on each.
Reports: OK, corrupt, empty, or missing.
Moves stale duplicates to I:\backups\ (no deletions).
Outputs JSON report to 00_SYSTEM/SYSTEM_HEALTH/db_health_report.json
"""

import sqlite3
import json
import sys
import os
import shutil
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace', closefd=False)

LITIGOS_ROOT = Path(r"C:\Users\andre\LitigationOS")
REPORT_DIR = LITIGOS_ROOT / "00_SYSTEM" / "SYSTEM_HEALTH"
REPORT_PATH = REPORT_DIR / "db_health_report.json"
BACKUP_DIR = Path(r"I:\backups")

SCAN_LOCATIONS = [
    LITIGOS_ROOT / "databases",
    LITIGOS_ROOT / "09_DATA",
    LITIGOS_ROOT,  # repo root (non-recursive for .db)
    LITIGOS_ROOT / "00_SYSTEM" / "pipeline",
    LITIGOS_ROOT / "00_SYSTEM" / "novel",
    LITIGOS_ROOT / "00_SYSTEM" / "darwin",
]


def check_single_db(db_path):
    """Run integrity check on a single database file."""
    result = {
        "path": str(db_path),
        "filename": os.path.basename(str(db_path)),
        "size_bytes": 0,
        "size_mb": 0.0,
        "status": "unknown",
        "table_count": 0,
        "journal_mode": "",
        "detail": "",
    }

    if not os.path.exists(str(db_path)):
        result["status"] = "missing"
        result["detail"] = "File does not exist"
        return result

    size = os.path.getsize(str(db_path))
    result["size_bytes"] = size
    result["size_mb"] = round(size / (1024 * 1024), 2)

    if size == 0:
        result["status"] = "empty"
        result["detail"] = "0 bytes — needs rebuild"
        return result

    try:
        conn = sqlite3.connect(str(db_path), timeout=15)
        conn.execute("PRAGMA busy_timeout = 15000")

        # Journal mode
        try:
            jm = conn.execute("PRAGMA journal_mode").fetchone()[0]
            result["journal_mode"] = jm
        except Exception:
            result["journal_mode"] = "unknown"

        # Table count
        try:
            tc = conn.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
            ).fetchone()[0]
            result["table_count"] = tc
        except Exception:
            result["table_count"] = -1

        # Integrity check (quick for large DBs)
        try:
            if size > 500 * 1024 * 1024:  # >500MB — use quick check
                integrity = conn.execute("PRAGMA quick_check").fetchone()[0]
            else:
                integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
        except Exception as e:
            integrity = f"error: {e}"

        conn.close()

        if integrity == "ok":
            result["status"] = "ok"
            result["detail"] = f"Integrity OK, {result['table_count']} tables, {result['journal_mode']} mode"
        else:
            result["status"] = "corrupt"
            result["detail"] = str(integrity)[:300]

    except Exception as e:
        result["status"] = "error"
        result["detail"] = str(e)[:300]

    return result


def find_all_dbs():
    """Find all .db files in scan locations."""
    found = set()

    for location in SCAN_LOCATIONS:
        if not location.exists():
            continue
        if location == LITIGOS_ROOT:
            # Non-recursive for repo root
            for f in location.glob("*.db"):
                found.add(f)
        else:
            for f in location.rglob("*.db"):
                found.add(f)

    return sorted(found, key=lambda p: str(p).lower())


def move_stale_duplicates():
    """Move stale duplicate DB files to I:\backups (never delete)."""
    moved = []
    stale_pattern = LITIGOS_ROOT / "litigation_context (2).db"

    if stale_pattern.exists():
        try:
            BACKUP_DIR.mkdir(parents=True, exist_ok=True)
            dest = BACKUP_DIR / f"litigation_context_copy2_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            shutil.move(str(stale_pattern), str(dest))
            moved.append({"source": str(stale_pattern), "destination": str(dest), "status": "moved"})
            print(f"  Moved stale DB: {stale_pattern} -> {dest}")
        except Exception as e:
            moved.append({"source": str(stale_pattern), "destination": "", "status": f"error: {e}"})
            print(f"  ERROR moving stale DB: {e}")

    return moved


def main():
    print("=" * 70)
    print("LitigationOS Database Health Check")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 70)

    # Ensure report directory
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    # Move stale duplicates
    print("\n--- Stale Duplicate Cleanup ---")
    moved = move_stale_duplicates()
    if not moved:
        print("  No stale duplicates found.")

    # Find and check all databases
    print("\n--- Scanning for databases ---")
    db_files = find_all_dbs()
    print(f"  Found {len(db_files)} database files")

    results = []
    ok_count = 0
    error_count = 0
    empty_count = 0

    print("\n--- Integrity Checks ---")
    for db_path in db_files:
        result = check_single_db(db_path)
        results.append(result)

        status_icon = {
            "ok": "✅",
            "empty": "⚪",
            "corrupt": "❌",
            "error": "⚠️",
            "missing": "❓",
        }.get(result["status"], "?")

        print(f"  {status_icon} {result['filename']:45s} {result['size_mb']:>8.1f} MB  {result['status']:>8s}  ({result['detail'][:60]})")

        if result["status"] == "ok":
            ok_count += 1
        elif result["status"] == "empty":
            empty_count += 1
        else:
            error_count += 1

    # Summary
    print("\n--- Summary ---")
    print(f"  Total databases: {len(results)}")
    print(f"  ✅ OK: {ok_count}")
    print(f"  ⚪ Empty: {empty_count}")
    print(f"  ❌ Issues: {error_count}")

    # Build report
    report = {
        "timestamp": datetime.now().isoformat(),
        "scan_locations": [str(loc) for loc in SCAN_LOCATIONS],
        "total_databases": len(results),
        "ok_count": ok_count,
        "empty_count": empty_count,
        "error_count": error_count,
        "stale_moves": moved,
        "databases": results,
    }

    # Write JSON report
    with open(str(REPORT_PATH), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"\n  Report written to: {REPORT_PATH}")


if __name__ == "__main__":
    main()
