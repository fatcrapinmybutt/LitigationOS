#!/usr/bin/env python3
"""OMEGA-INFINITY Cognitive Kernel Boot Sequence.

Verifies all databases are accessible, all 12 brain reference files exist,
key tables are present, and reports vital statistics.
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path

sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", errors="replace")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
REPO_ROOT = Path(r"C:\Users\andre\LitigationOS")
DEFAULT_DB = REPO_ROOT / "litigation_context.db"
COURT_FORMS_DB = REPO_ROOT / "court_forms.db"
JURISDICTION_DIR = REPO_ROOT / "databases"
REFERENCES_DIR = REPO_ROOT / ".agents" / "skills" / "OMEGA-INFINITY" / "references"

BRAIN_FILES = [
    "Ω1-litigation-brain.md",
    "Ω2-evidence-brain.md",
    "Ω3-forms-brain.md",
    "Ω4-rules-brain.md",
    "Ω5-adversary-brain.md",
    "Ω6-timeline-brain.md",
    "Ω7-judicial-brain.md",
    "Ω8-financial-brain.md",
    "Ω9-witness-brain.md",
    "Ω10-filing-brain.md",
    "Ω11-agent-brain.md",
    "Ω12-context-brain.md",
]

KEY_TABLES = [
    "evidence_quotes",
    "documents",
    "court_forms_complete",
    "authority_master_index",
    "filing_readiness",
    "judicial_violations",
    "docket_events",
    "timeline_events",
    "claims",
    "deadlines",
]

MIN_BRAIN_SIZE_KB = 10


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _connect(db_path: Path) -> sqlite3.Connection:
    """Open a connection with mandatory PRAGMAs."""
    conn = sqlite3.connect(str(db_path), timeout=60)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    conn.execute("PRAGMA temp_store=MEMORY")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    ).fetchone()
    return bool(row and row[0] > 0)


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------
def verify_databases() -> list[dict]:
    """Check all known DBs are accessible."""
    results: list[dict] = []

    # Primary DB
    for label, path in [("litigation_context", DEFAULT_DB), ("court_forms", COURT_FORMS_DB)]:
        entry: dict = {"name": label, "path": str(path), "exists": path.is_file(), "accessible": False}
        if entry["exists"]:
            try:
                c = _connect(path)
                c.execute("SELECT 1")
                c.close()
                entry["accessible"] = True
                entry["size_mb"] = round(path.stat().st_size / (1024 * 1024), 2)
            except Exception as exc:
                entry["error"] = str(exc)
        results.append(entry)

    # Jurisdiction DBs
    if JURISDICTION_DIR.is_dir():
        for db_file in sorted(JURISDICTION_DIR.glob("*.db")):
            entry = {"name": db_file.stem, "path": str(db_file), "exists": True, "accessible": False}
            try:
                c = _connect(db_file)
                c.execute("SELECT 1")
                c.close()
                entry["accessible"] = True
                entry["size_mb"] = round(db_file.stat().st_size / (1024 * 1024), 2)
            except Exception as exc:
                entry["error"] = str(exc)
            results.append(entry)
    else:
        results.append({"name": "jurisdiction_dir", "path": str(JURISDICTION_DIR), "exists": False, "accessible": False})

    return results


def verify_brain_references() -> list[dict]:
    """Check all 12 Ω*.md files exist in references/ and are ≥10 KB."""
    results: list[dict] = []
    for fname in BRAIN_FILES:
        fpath = REFERENCES_DIR / fname
        entry: dict = {"file": fname, "exists": fpath.is_file(), "ok": False}
        if entry["exists"]:
            size_kb = fpath.stat().st_size / 1024
            entry["size_kb"] = round(size_kb, 2)
            entry["ok"] = size_kb >= MIN_BRAIN_SIZE_KB
        results.append(entry)
    return results


def verify_tables(conn: sqlite3.Connection) -> list[dict]:
    """Check key tables exist in the primary DB."""
    results: list[dict] = []
    for tbl in KEY_TABLES:
        results.append({"table": tbl, "exists": _table_exists(conn, tbl)})
    return results


def get_vital_stats(conn: sqlite3.Connection) -> dict:
    """Run consolidated COUNT(*) for key tables using subquery pattern."""
    # Build one query with subqueries for each table that exists
    existing: list[str] = [t for t in KEY_TABLES if _table_exists(conn, t)]
    if not existing:
        return {"error": "No key tables found"}

    subqueries = ", ".join(
        f"(SELECT COUNT(*) FROM [{tbl}]) AS [{tbl}]" for tbl in existing
    )
    sql = f"SELECT {subqueries}"
    row = conn.execute(sql).fetchone()

    stats: dict = {}
    for i, tbl in enumerate(existing):
        stats[tbl] = row[i] if row else 0
    return stats


def boot_report(
    db_results: list[dict],
    brain_results: list[dict],
    table_results: list[dict],
    vital_stats: dict,
    as_json: bool = False,
    quiet: bool = False,
) -> bool:
    """Print formatted boot report. Returns True if all checks pass."""
    all_ok = True

    report = {
        "databases": db_results,
        "brain_references": brain_results,
        "tables": table_results,
        "vital_stats": vital_stats,
    }

    # Evaluate pass/fail
    db_ok = all(d.get("accessible") or not d.get("exists", True) for d in db_results)
    brains_ok = all(b.get("ok") for b in brain_results)
    tables_ok = all(t.get("exists") for t in table_results)

    report["status"] = {
        "databases": "PASS" if db_ok else "FAIL",
        "brain_references": "PASS" if brains_ok else "FAIL",
        "tables": "PASS" if tables_ok else "FAIL",
        "overall": "PASS" if (db_ok and brains_ok and tables_ok) else "FAIL",
    }
    all_ok = db_ok and brains_ok and tables_ok

    if as_json:
        print(json.dumps(report, indent=2, default=str))
        return all_ok

    if quiet:
        status = "✅ BOOT OK" if all_ok else "❌ BOOT FAILED"
        print(status)
        return all_ok

    # Pretty print
    print("=" * 70)
    print("  OMEGA-INFINITY COGNITIVE KERNEL — BOOT SEQUENCE")
    print("=" * 70)

    # Databases
    print("\n📁 DATABASE VERIFICATION")
    print("-" * 50)
    for d in db_results:
        icon = "✅" if d.get("accessible") else "❌"
        size = f" ({d['size_mb']} MB)" if "size_mb" in d else ""
        print(f"  {icon} {d['name']}{size}")
    print(f"  Status: {report['status']['databases']}")

    # Brains
    print("\n🧠 BRAIN REFERENCES")
    print("-" * 50)
    for b in brain_results:
        icon = "✅" if b.get("ok") else "❌"
        size = f" ({b['size_kb']} KB)" if "size_kb" in b else " (MISSING)"
        print(f"  {icon} {b['file']}{size}")
    print(f"  Status: {report['status']['brain_references']}")

    # Tables
    print("\n📋 KEY TABLES")
    print("-" * 50)
    for t in table_results:
        icon = "✅" if t["exists"] else "❌"
        print(f"  {icon} {t['table']}")
    print(f"  Status: {report['status']['tables']}")

    # Vital stats
    print("\n📊 VITAL STATISTICS")
    print("-" * 50)
    if "error" in vital_stats:
        print(f"  ⚠️  {vital_stats['error']}")
    else:
        for tbl, count in vital_stats.items():
            print(f"  {tbl}: {count:,} rows")

    # Overall
    print("\n" + "=" * 70)
    overall = report["status"]["overall"]
    icon = "✅" if overall == "PASS" else "❌"
    print(f"  {icon} OVERALL: {overall}")
    print("=" * 70)

    return all_ok


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    parser = argparse.ArgumentParser(
        description="OMEGA-INFINITY Cognitive Kernel Boot Sequence",
    )
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help="Path to primary DB")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--quiet", action="store_true", help="Minimal output")
    args = parser.parse_args()

    db_results = verify_databases()
    brain_results = verify_brain_references()

    conn = None
    table_results: list[dict] = []
    vital_stats: dict = {}

    db_path = args.db
    if db_path.is_file():
        try:
            conn = _connect(db_path)
            table_results = verify_tables(conn)
            vital_stats = get_vital_stats(conn)
        except Exception as exc:
            vital_stats = {"error": str(exc)}
    else:
        table_results = [{"table": t, "exists": False} for t in KEY_TABLES]
        vital_stats = {"error": f"DB not found: {db_path}"}

    ok = boot_report(db_results, brain_results, table_results, vital_stats, as_json=args.json, quiet=args.quiet)

    if conn:
        conn.close()

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
