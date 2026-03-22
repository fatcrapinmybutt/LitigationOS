#!/usr/bin/env python3
"""OMEGA-INFINITY Gap Detector.

Scans all 12 brains for gaps — missing data, empty tables, weak coverage
areas — and generates prioritized acquisition tasks.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", errors="replace")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
REPO_ROOT = Path(r"C:\Users\andre\LitigationOS")
DEFAULT_DB = REPO_ROOT / "litigation_context.db"

LANE_LABELS: dict[str, str] = {
    "A": "Custody (2024-001507-DC)",
    "B": "Housing (2025-002760-CZ)",
    "C": "Convergence",
    "D": "PPO (2023-5907-PP)",
    "E": "Misconduct (JTC)",
    "F": "Appellate (COA 366810)",
}

PRIORITY_WEIGHTS: dict[str, int] = {
    "evidence": 90,
    "form": 70,
    "authority": 80,
    "filing": 95,
    "timeline": 60,
    "witness": 75,
}


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


def _safe_count(conn: sqlite3.Connection, table: str, where: str = "", params: tuple = ()) -> int:
    if not _table_exists(conn, table):
        return -1
    sql = f"SELECT COUNT(*) FROM [{table}]"
    if where:
        sql += f" WHERE {where}"
    return conn.execute(sql, params).fetchone()[0]


def _get_columns(conn: sqlite3.Connection, table: str) -> list[str]:
    if not _table_exists(conn, table):
        return []
    return [r["name"] for r in conn.execute(f"PRAGMA table_info([{table}])").fetchall()]


def _find_lane_col(cols: list[str]) -> str | None:
    for candidate in ("case_lane", "lane", "vehicle_name"):
        if candidate in cols:
            return candidate
    return None


# ---------------------------------------------------------------------------
# Gap detection functions
# ---------------------------------------------------------------------------
def detect_evidence_gaps(conn: sqlite3.Connection, lane_filter: str | None = None) -> list[dict]:
    """Evidence auth (0 rows), Bates (0 rows), per-lane coverage imbalance."""
    gaps: list[dict] = []

    # Check critical evidence infrastructure tables
    for tbl, desc in [
        ("evidence_authentication", "Evidence authentication records"),
        ("bates_registry", "Bates stamp registry"),
    ]:
        cnt = _safe_count(conn, tbl)
        if cnt <= 0:
            gaps.append({
                "type": "evidence",
                "subtype": "infrastructure",
                "table": tbl,
                "description": f"{desc}: {'MISSING' if cnt == -1 else 'EMPTY'}",
                "severity": "HIGH",
                "count": cnt,
            })

    # Per-lane coverage analysis from evidence_quotes
    if _table_exists(conn, "evidence_quotes"):
        cols = _get_columns(conn, "evidence_quotes")
        lane_col = _find_lane_col(cols)

        if lane_col:
            lane_counts: dict[str, int] = {}
            for lane_code in LANE_LABELS:
                if lane_filter and lane_code != lane_filter:
                    continue
                cnt = _safe_count(conn, "evidence_quotes", f"[{lane_col}] LIKE ?", (f"%{lane_code}%",))
                lane_counts[lane_code] = max(cnt, 0)

            if lane_counts:
                avg_count = sum(lane_counts.values()) / max(len(lane_counts), 1)
                for lane_code, cnt in lane_counts.items():
                    if cnt < avg_count * 0.3 and cnt < 100:
                        gaps.append({
                            "type": "evidence",
                            "subtype": "coverage_imbalance",
                            "lane": lane_code,
                            "description": f"Lane {lane_code} ({LANE_LABELS[lane_code]}): only {cnt} evidence quotes (avg={avg_count:.0f})",
                            "severity": "MEDIUM" if cnt > 0 else "HIGH",
                            "count": cnt,
                        })

    return gaps


def detect_form_gaps(conn: sqlite3.Connection, lane_filter: str | None = None) -> list[dict]:
    """Missing forms per lane."""
    gaps: list[dict] = []

    if not _table_exists(conn, "court_forms_complete"):
        gaps.append({
            "type": "form",
            "subtype": "table_missing",
            "description": "court_forms_complete table does not exist",
            "severity": "HIGH",
        })
        return gaps

    total = _safe_count(conn, "court_forms_complete")
    if total == 0:
        gaps.append({
            "type": "form",
            "subtype": "empty",
            "description": "court_forms_complete is empty — no forms loaded",
            "severity": "HIGH",
        })
        return gaps

    # Check forms coverage by examining filing_readiness vehicle needs
    if _table_exists(conn, "filing_readiness"):
        cols_fr = _get_columns(conn, "filing_readiness")
        form_col = next((c for c in cols_fr if "form" in c.lower()), None)
        if form_col:
            rows = conn.execute(
                f"SELECT DISTINCT [{form_col}] FROM filing_readiness WHERE [{form_col}] IS NOT NULL"
            ).fetchall()
            for r in rows:
                form_name = r[0]
                if form_name:
                    # Check if form exists in court_forms_complete
                    cols_cf = _get_columns(conn, "court_forms_complete")
                    name_col = next((c for c in cols_cf if "name" in c.lower() or "form" in c.lower() or "number" in c.lower()), cols_cf[0] if cols_cf else None)
                    if name_col:
                        match = _safe_count(conn, "court_forms_complete", f"[{name_col}] LIKE ?", (f"%{form_name}%",))
                        if match == 0:
                            gaps.append({
                                "type": "form",
                                "subtype": "missing_form",
                                "description": f"Form '{form_name}' needed by filing_readiness but not in court_forms_complete",
                                "severity": "MEDIUM",
                            })

    return gaps


def detect_authority_gaps(conn: sqlite3.Connection) -> list[dict]:
    """Rules referenced in filings but not in authority_master_index."""
    gaps: list[dict] = []

    if not _table_exists(conn, "authority_master_index"):
        gaps.append({
            "type": "authority",
            "subtype": "table_missing",
            "description": "authority_master_index table does not exist",
            "severity": "HIGH",
        })
        return gaps

    total = _safe_count(conn, "authority_master_index")
    if total == 0:
        gaps.append({
            "type": "authority",
            "subtype": "empty",
            "description": "authority_master_index is empty",
            "severity": "HIGH",
        })
        return gaps

    # Check filing_rule_map references
    if _table_exists(conn, "filing_rule_map"):
        cols_frm = _get_columns(conn, "filing_rule_map")
        rule_col = next((c for c in cols_frm if "rule" in c.lower() or "authority" in c.lower() or "citation" in c.lower()), None)
        if rule_col:
            rules_in_filings = conn.execute(
                f"SELECT DISTINCT [{rule_col}] FROM filing_rule_map WHERE [{rule_col}] IS NOT NULL LIMIT 100"
            ).fetchall()

            cols_ami = _get_columns(conn, "authority_master_index")
            auth_col = next(
                (c for c in cols_ami if "rule" in c.lower() or "citation" in c.lower() or "authority" in c.lower() or "name" in c.lower()),
                cols_ami[0] if cols_ami else None,
            )
            if auth_col:
                for r in rules_in_filings:
                    rule_ref = r[0]
                    if rule_ref and len(str(rule_ref)) > 3:
                        match = _safe_count(conn, "authority_master_index", f"[{auth_col}] LIKE ?", (f"%{rule_ref}%",))
                        if match == 0:
                            gaps.append({
                                "type": "authority",
                                "subtype": "missing_authority",
                                "description": f"Rule '{rule_ref}' in filing_rule_map but not in authority_master_index",
                                "severity": "MEDIUM",
                            })

    return gaps


def detect_filing_gaps(conn: sqlite3.Connection, lane_filter: str | None = None) -> list[dict]:
    """Filings with readiness < 70%."""
    gaps: list[dict] = []

    if not _table_exists(conn, "filing_readiness"):
        gaps.append({
            "type": "filing",
            "subtype": "table_missing",
            "description": "filing_readiness table does not exist",
            "severity": "CRITICAL",
        })
        return gaps

    cols = _get_columns(conn, "filing_readiness")
    score_col = next((c for c in cols if "score" in c.lower() or "readiness" in c.lower() or "pct" in c.lower()), None)
    name_col = next((c for c in cols if "vehicle" in c.lower() or "name" in c.lower() or "filing" in c.lower()), None)

    if not score_col:
        gaps.append({
            "type": "filing",
            "subtype": "schema",
            "description": f"Cannot find score column in filing_readiness (cols: {cols})",
            "severity": "MEDIUM",
        })
        return gaps

    # Find filings below 70% readiness
    rows = conn.execute(
        f"SELECT * FROM filing_readiness WHERE [{score_col}] < 70 ORDER BY [{score_col}] ASC"
    ).fetchall()

    for r in rows:
        row_dict = dict(r)
        vehicle = row_dict.get(name_col, "Unknown") if name_col else "Unknown"
        score = row_dict.get(score_col, 0)
        gaps.append({
            "type": "filing",
            "subtype": "low_readiness",
            "vehicle": str(vehicle),
            "score": score,
            "description": f"Filing '{vehicle}' at {score}% readiness (below 70% threshold)",
            "severity": "HIGH" if score < 40 else "MEDIUM",
        })

    return gaps


def detect_timeline_gaps(conn: sqlite3.Connection) -> list[dict]:
    """Date ranges with no events (>30 day gaps)."""
    gaps: list[dict] = []

    for tbl in ("timeline_events", "docket_events"):
        if not _table_exists(conn, tbl):
            gaps.append({
                "type": "timeline",
                "subtype": "table_missing",
                "table": tbl,
                "description": f"{tbl} table does not exist",
                "severity": "MEDIUM",
            })
            continue

        cols = _get_columns(conn, tbl)
        date_col = next(
            (c for c in cols if "date" in c.lower() or "when" in c.lower() or "timestamp" in c.lower()),
            None,
        )
        if not date_col:
            continue

        # Get all dates, look for 30+ day gaps
        rows = conn.execute(
            f"SELECT DISTINCT [{date_col}] FROM [{tbl}] WHERE [{date_col}] IS NOT NULL "
            f"ORDER BY [{date_col}]"
        ).fetchall()

        dates: list[str] = [str(r[0]) for r in rows if r[0] and len(str(r[0])) >= 10]

        prev_date = None
        for d in dates:
            if prev_date:
                try:
                    from datetime import datetime

                    d1 = datetime.strptime(prev_date[:10], "%Y-%m-%d")
                    d2 = datetime.strptime(d[:10], "%Y-%m-%d")
                    delta = (d2 - d1).days
                    if delta > 30:
                        gaps.append({
                            "type": "timeline",
                            "subtype": "date_gap",
                            "table": tbl,
                            "description": f"{delta}-day gap in {tbl}: {prev_date[:10]} → {d[:10]}",
                            "severity": "LOW" if delta < 90 else "MEDIUM",
                            "gap_days": delta,
                        })
                except (ValueError, IndexError):
                    pass
            prev_date = d

    return gaps


def detect_witness_gaps(conn: sqlite3.Connection, lane_filter: str | None = None) -> list[dict]:
    """Lanes with no witness records."""
    gaps: list[dict] = []

    for tbl in ("witness_list", "witness_profiles"):
        if not _table_exists(conn, tbl):
            gaps.append({
                "type": "witness",
                "subtype": "table_missing",
                "table": tbl,
                "description": f"{tbl} table does not exist",
                "severity": "HIGH" if tbl == "witness_list" else "MEDIUM",
            })
            continue

        cnt = _safe_count(conn, tbl)
        if cnt == 0:
            gaps.append({
                "type": "witness",
                "subtype": "empty",
                "table": tbl,
                "description": f"{tbl} is empty — no witnesses cataloged",
                "severity": "HIGH",
            })

    return gaps


def generate_acquisition_tasks(all_gaps: list[dict]) -> list[dict]:
    """Convert gaps to actionable tasks with priority scoring."""
    tasks: list[dict] = []
    for i, gap in enumerate(all_gaps, 1):
        gap_type = gap.get("type", "unknown")
        base_priority = PRIORITY_WEIGHTS.get(gap_type, 50)

        severity_bonus = {"CRITICAL": 10, "HIGH": 5, "MEDIUM": 0, "LOW": -10}.get(
            gap.get("severity", "MEDIUM"), 0
        )

        task: dict[str, Any] = {
            "task_id": f"ACQ-{i:03d}",
            "type": gap_type,
            "priority": min(base_priority + severity_bonus, 100),
            "severity": gap.get("severity", "MEDIUM"),
            "description": gap.get("description", ""),
            "action": _gap_to_action(gap),
        }
        if "lane" in gap:
            task["lane"] = gap["lane"]
        if "vehicle" in gap:
            task["vehicle"] = gap["vehicle"]

        tasks.append(task)

    # Sort by priority descending
    tasks.sort(key=lambda t: t["priority"], reverse=True)
    return tasks


def _gap_to_action(gap: dict) -> str:
    """Convert a gap to a human-readable action."""
    gap_type = gap.get("type", "")
    subtype = gap.get("subtype", "")

    if subtype in ("table_missing", "empty"):
        return f"Run pipeline to populate {gap.get('table', gap.get('description', ''))}"
    if gap_type == "evidence" and subtype == "coverage_imbalance":
        return f"Harvest more evidence for Lane {gap.get('lane', '?')}"
    if gap_type == "filing" and subtype == "low_readiness":
        return f"Complete filing package for '{gap.get('vehicle', '?')}'"
    if gap_type == "authority":
        return "Research and add missing legal authority citations"
    if gap_type == "timeline":
        return "Fill timeline gap with court records or personal logs"
    if gap_type == "witness":
        return "Identify and catalog witnesses for this lane"
    if gap_type == "form":
        return "Locate and load missing SCAO court form"
    return f"Investigate: {gap.get('description', '')}"


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------
def print_gap_report(
    all_gaps: list[dict],
    tasks: list[dict],
    as_json: bool = False,
) -> None:
    report = {
        "total_gaps": len(all_gaps),
        "gaps_by_type": {},
        "gaps": all_gaps,
        "acquisition_tasks": tasks,
    }
    for g in all_gaps:
        t = g.get("type", "unknown")
        report["gaps_by_type"][t] = report["gaps_by_type"].get(t, 0) + 1

    if as_json:
        print(json.dumps(report, indent=2, default=str))
        return

    print("=" * 70)
    print("  OMEGA-INFINITY GAP DETECTOR REPORT")
    print("=" * 70)

    print(f"\n  Total gaps detected: {len(all_gaps)}")
    for gtype, count in sorted(report["gaps_by_type"].items()):
        print(f"    {gtype}: {count}")

    print("\n" + "-" * 70)
    print("  GAPS BY CATEGORY")
    print("-" * 70)
    for g in all_gaps:
        sev = g.get("severity", "?")
        icon = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}.get(sev, "⚪")
        print(f"  {icon} [{sev}] {g.get('description', '')}")

    print("\n" + "-" * 70)
    print("  PRIORITIZED ACQUISITION TASKS")
    print("-" * 70)
    for t in tasks[:20]:
        print(f"  [{t['task_id']}] P{t['priority']} {t['severity']:8s} → {t['action']}")

    print("\n" + "=" * 70)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    parser = argparse.ArgumentParser(description="OMEGA-INFINITY Gap Detector")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help="Path to primary DB")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--lane", choices=["A", "B", "C", "D", "E", "F"], help="Filter to specific lane")
    args = parser.parse_args()

    if not args.db.is_file():
        msg = f"DB not found: {args.db}"
        print(json.dumps({"error": msg}) if args.json else f"❌ {msg}")
        return 1

    try:
        conn = _connect(args.db)

        all_gaps: list[dict] = []
        all_gaps.extend(detect_evidence_gaps(conn, args.lane))
        all_gaps.extend(detect_form_gaps(conn, args.lane))
        all_gaps.extend(detect_authority_gaps(conn))
        all_gaps.extend(detect_filing_gaps(conn, args.lane))
        all_gaps.extend(detect_timeline_gaps(conn))
        all_gaps.extend(detect_witness_gaps(conn, args.lane))

        tasks = generate_acquisition_tasks(all_gaps)

        print_gap_report(all_gaps, tasks, as_json=args.json)
        conn.close()
    except Exception as exc:
        msg = str(exc)
        print(json.dumps({"error": msg}) if args.json else f"❌ Error: {msg}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
