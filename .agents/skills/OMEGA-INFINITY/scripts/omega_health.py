#!/usr/bin/env python3
"""OMEGA-INFINITY System Health Dashboard.

Reports DB sizes, table counts, staleness detection, evidence coverage,
filing readiness summary, and gap analysis.
"""
from __future__ import annotations

import argparse
import json
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

# Tables that should have data if the system is healthy
EXPECTED_POPULATED_TABLES = [
    "evidence_quotes",
    "evidence_authentication",
    "bates_registry",
    "claims",
    "filing_readiness",
    "witness_list",
    "judicial_violations",
    "timeline_events",
    "docket_events",
    "authority_master_index",
    "documents",
    "deadlines",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path), timeout=60)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    conn.execute("PRAGMA temp_store=MEMORY")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.row_factory = sqlite3.Row
    return conn


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone()
    return bool(row and row[0] > 0)


def _safe_count(conn: sqlite3.Connection, table: str) -> int:
    if not _table_exists(conn, table):
        return -1
    return conn.execute(f"SELECT COUNT(*) FROM [{table}]").fetchone()[0]


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------
def db_health(db_path: Path) -> dict:
    """File size, table count, total rows, WAL size."""
    result: dict = {"path": str(db_path), "exists": db_path.is_file()}
    if not result["exists"]:
        return result

    result["size_mb"] = round(db_path.stat().st_size / (1024 * 1024), 2)

    wal_path = db_path.parent / (db_path.name + "-wal")
    result["wal_size_mb"] = round(wal_path.stat().st_size / (1024 * 1024), 2) if wal_path.is_file() else 0

    try:
        conn = _connect(db_path)
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        result["table_count"] = len(tables)

        # Total rows across all tables (sample top 50 to avoid timeout)
        total_rows = 0
        table_names = [t["name"] for t in tables[:50]]
        for tbl in table_names:
            try:
                cnt = conn.execute(f"SELECT COUNT(*) FROM [{tbl}]").fetchone()[0]
                total_rows += cnt
            except Exception:
                pass
        if len(tables) > 50:
            result["note"] = f"Row count sampled from 50/{len(tables)} tables"
        result["total_rows_sampled"] = total_rows
        conn.close()
    except Exception as exc:
        result["error"] = str(exc)

    return result


def evidence_coverage(conn: sqlite3.Connection) -> dict:
    """Per-lane counts from evidence_quotes, documents, judicial_violations."""
    coverage: dict = {"lanes": {}}
    lane_labels = {"A": "Custody", "B": "Housing", "C": "Convergence", "D": "PPO", "E": "Misconduct", "F": "Appellate"}

    for lane_code, label in lane_labels.items():
        lane_data: dict = {"label": label}

        if _table_exists(conn, "evidence_quotes"):
            # Try common lane column names
            for col in ("case_lane", "lane", "vehicle_name"):
                try:
                    cnt = conn.execute(
                        f"SELECT COUNT(*) FROM evidence_quotes WHERE [{col}] LIKE ?",
                        (f"%{lane_code}%",),
                    ).fetchone()[0]
                    lane_data["evidence_quotes"] = cnt
                    break
                except Exception:
                    continue
            if "evidence_quotes" not in lane_data:
                lane_data["evidence_quotes"] = "N/A"

        if _table_exists(conn, "documents"):
            for col in ("case_lane", "lane", "category"):
                try:
                    cnt = conn.execute(
                        f"SELECT COUNT(*) FROM documents WHERE [{col}] LIKE ?",
                        (f"%{lane_code}%",),
                    ).fetchone()[0]
                    lane_data["documents"] = cnt
                    break
                except Exception:
                    continue
            if "documents" not in lane_data:
                lane_data["documents"] = "N/A"

        if lane_code == "E" and _table_exists(conn, "judicial_violations"):
            lane_data["judicial_violations"] = _safe_count(conn, "judicial_violations")

        coverage["lanes"][lane_code] = lane_data

    # Totals
    coverage["totals"] = {
        "evidence_quotes": _safe_count(conn, "evidence_quotes"),
        "documents": _safe_count(conn, "documents"),
        "judicial_violations": _safe_count(conn, "judicial_violations"),
    }
    return coverage


def staleness_check(conn: sqlite3.Connection) -> list[dict]:
    """Find tables with potential staleness indicators."""
    stale: list[dict] = []
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()

    timestamp_cols = ["created_at", "updated_at", "timestamp", "date_added", "last_modified", "ingested_at"]

    for tbl_row in tables:
        tbl = tbl_row["name"]
        try:
            cols_info = conn.execute(f"PRAGMA table_info([{tbl}])").fetchall()
            col_names = [c["name"] for c in cols_info]
            ts_col = next((c for c in timestamp_cols if c in col_names), None)

            if ts_col:
                row = conn.execute(
                    f"SELECT MAX([{ts_col}]) as latest FROM [{tbl}]"
                ).fetchone()
                latest = row["latest"] if row else None
                if latest and isinstance(latest, str) and len(latest) >= 10:
                    stale.append({"table": tbl, "column": ts_col, "latest": latest})
        except Exception:
            continue

    return stale


def filing_readiness_summary(conn: sqlite3.Connection) -> list[dict]:
    """Top filing vehicles by readiness score."""
    if not _table_exists(conn, "filing_readiness"):
        return [{"error": "filing_readiness table not found"}]

    # Discover columns first
    cols_info = conn.execute("PRAGMA table_info(filing_readiness)").fetchall()
    col_names = [c["name"] for c in cols_info]

    # Find score-like and name-like columns
    score_col = next((c for c in col_names if "score" in c.lower() or "readiness" in c.lower() or "pct" in c.lower()), None)
    name_col = next((c for c in col_names if "vehicle" in c.lower() or "name" in c.lower() or "filing" in c.lower()), None)

    if not score_col or not name_col:
        # Fallback: return raw first 10 rows
        rows = conn.execute("SELECT * FROM filing_readiness LIMIT 10").fetchall()
        return [dict(r) for r in rows]

    rows = conn.execute(
        f"SELECT * FROM filing_readiness ORDER BY [{score_col}] DESC LIMIT 10"
    ).fetchall()
    return [dict(r) for r in rows]


def gap_summary(conn: sqlite3.Connection) -> list[dict]:
    """Tables with 0 rows that should have data."""
    gaps: list[dict] = []
    for tbl in EXPECTED_POPULATED_TABLES:
        count = _safe_count(conn, tbl)
        if count == 0:
            gaps.append({"table": tbl, "status": "EMPTY", "action": f"Populate {tbl} via pipeline or manual ingest"})
        elif count == -1:
            gaps.append({"table": tbl, "status": "MISSING", "action": f"Create {tbl} table"})
    return gaps


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------
def print_dashboard(
    health: dict,
    coverage: dict,
    stale_tables: list[dict],
    readiness: list[dict],
    gaps: list[dict],
    as_json: bool = False,
    verbose: bool = False,
) -> None:
    report = {
        "db_health": health,
        "evidence_coverage": coverage,
        "staleness": stale_tables if verbose else stale_tables[:10],
        "filing_readiness_top10": readiness,
        "gaps": gaps,
    }

    if as_json:
        print(json.dumps(report, indent=2, default=str))
        return

    print("=" * 70)
    print("  OMEGA-INFINITY HEALTH DASHBOARD")
    print("=" * 70)

    # DB Health
    print("\n💾 DATABASE HEALTH")
    print("-" * 50)
    print(f"  Path:       {health.get('path', 'N/A')}")
    print(f"  Size:       {health.get('size_mb', 'N/A')} MB")
    print(f"  WAL Size:   {health.get('wal_size_mb', 'N/A')} MB")
    print(f"  Tables:     {health.get('table_count', 'N/A')}")
    print(f"  Rows:       {health.get('total_rows_sampled', 'N/A'):,}")

    # Evidence coverage
    print("\n📦 EVIDENCE COVERAGE BY LANE")
    print("-" * 50)
    for lane_code, data in coverage.get("lanes", {}).items():
        eq = data.get("evidence_quotes", "N/A")
        doc = data.get("documents", "N/A")
        eq_str = f"{eq:,}" if isinstance(eq, int) else eq
        doc_str = f"{doc:,}" if isinstance(doc, int) else doc
        print(f"  Lane {lane_code} ({data['label']}): {eq_str} quotes, {doc_str} docs")
    totals = coverage.get("totals", {})
    for k, v in totals.items():
        v_str = f"{v:,}" if isinstance(v, int) and v >= 0 else str(v)
        print(f"  TOTAL {k}: {v_str}")

    # Filing readiness
    print("\n📋 FILING READINESS (Top 10)")
    print("-" * 50)
    for r in readiness:
        if "error" in r:
            print(f"  ⚠️  {r['error']}")
        else:
            vals = list(r.values())[:3]
            print(f"  {' | '.join(str(v) for v in vals)}")

    # Gaps
    print("\n🕳️  DATA GAPS")
    print("-" * 50)
    if gaps:
        for g in gaps:
            print(f"  ❌ {g['table']}: {g['status']} — {g['action']}")
    else:
        print("  ✅ No critical gaps detected")

    # Staleness
    if verbose and stale_tables:
        print("\n⏰ STALENESS CHECK (tables with timestamp columns)")
        print("-" * 50)
        for s in stale_tables[:20]:
            print(f"  {s['table']}.{s['column']}: last = {s['latest']}")

    print("\n" + "=" * 70)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    parser = argparse.ArgumentParser(description="OMEGA-INFINITY System Health Dashboard")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help="Path to primary DB")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--verbose", action="store_true", help="Show detailed staleness info")
    args = parser.parse_args()

    if not args.db.is_file():
        print(json.dumps({"error": f"DB not found: {args.db}"}) if args.json else f"❌ DB not found: {args.db}")
        return 1

    try:
        health = db_health(args.db)
        conn = _connect(args.db)
        cov = evidence_coverage(conn)
        stale = staleness_check(conn)
        readiness = filing_readiness_summary(conn)
        gaps = gap_summary(conn)
        conn.close()
    except Exception as exc:
        print(json.dumps({"error": str(exc)}) if args.json else f"❌ Error: {exc}")
        return 1

    print_dashboard(health, cov, stale, readiness, gaps, as_json=args.json, verbose=args.verbose)
    return 0


if __name__ == "__main__":
    sys.exit(main())
