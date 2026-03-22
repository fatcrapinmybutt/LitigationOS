#!/usr/bin/env python3
"""OMEGA-INFINITY Master Query Router.

Accepts natural language queries, routes to appropriate brain module(s),
executes relevant DB queries, and returns merged results.
"""
from __future__ import annotations

import argparse
import json
import re
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

# Brain routing patterns (MEEK-style regex)
BRAIN_PATTERNS: dict[str, re.Pattern[str]] = {
    "Ω1": re.compile(
        r"(?i)(litigation|case|claim|tort|cause.?of.?action|complaint|"
        r"case.?number|2024.?001507|2023.?5907|2025.?002760)"
    ),
    "Ω2": re.compile(
        r"(?i)(evidence|exhibit|scan|document|proof|bates|"
        r"authentication|chain.?of.?custody|quote|attestation)"
    ),
    "Ω3": re.compile(
        r"(?i)(form|SCAO|MC\s?\d|DC\s?\d|CC\s?\d|court.?form|"
        r"template|auto.?fill|caption)"
    ),
    "Ω4": re.compile(
        r"(?i)(rule|authority|MCR|MCL|statute|citation|"
        r"precedent|case.?law|stare.?decisis|standard.?of.?review)"
    ),
    "Ω5": re.compile(
        r"(?i)(Watson|Berry|Emily|adversary|opponent|"
        r"accusation|harm|pattern|retaliation|alienation)"
    ),
    "Ω6": re.compile(
        r"(?i)(timeline|chronolog|date|when|event|sequence|"
        r"history|calendar|deadline|docket)"
    ),
    "Ω7": re.compile(
        r"(?i)(McNeill|judge|judicial|misconduct|JTC|"
        r"bias|recusal|disqualif|canon|ex.?parte|nonservice)"
    ),
    "Ω8": re.compile(
        r"(?i)(money|damage|cost|financial|fee|fine|"
        r"garnish|child.?support|income|expense|mileage)"
    ),
    "Ω9": re.compile(
        r"(?i)(witness|testimony|deposition|credib|"
        r"impeach|cross.?exam|affidavit|sworn)"
    ),
    "Ω10": re.compile(
        r"(?i)(filing|motion|brief|petition|response|"
        r"order|packet|service|readiness|efil)"
    ),
    "Ω11": re.compile(
        r"(?i)(agent|pipeline|fleet|orchestrat|phase|"
        r"tier|delta|omega.?system|convergence)"
    ),
    "Ω12": re.compile(
        r"(?i)(context|memory|session|handoff|recall|"
        r"previous|last.?time|history|snapshot)"
    ),
}

# Brain → DB table mapping (primary query targets)
BRAIN_TABLES: dict[str, list[str]] = {
    "Ω1": ["claims", "omega_legal_actions", "actionable_evidence"],
    "Ω2": ["evidence_quotes", "documents", "evidence_consolidated"],
    "Ω3": ["court_forms_complete"],
    "Ω4": ["authority_master_index", "master_citations", "filing_rule_map"],
    "Ω5": ["adversary_harm_summary", "extracted_harms", "contradiction_map"],
    "Ω6": ["timeline_events", "docket_events", "deadlines"],
    "Ω7": ["judicial_violations", "impeachment_items"],
    "Ω8": ["claims"],  # financial subset
    "Ω9": ["witness_list", "witness_profiles", "impeachment_items"],
    "Ω10": ["filing_readiness", "filing_packages", "filing_documents"],
    "Ω11": ["pipeline_registry"],
    "Ω12": ["session_handoff", "session_intelligence", "master_todos"],
}

# Lane filter patterns
LANE_PATTERNS: dict[str, re.Pattern[str]] = {
    "A": re.compile(r"(?i)(custody|parenting|FOC|child|MCL\s+722|best.?interest)"),
    "B": re.compile(r"(?i)(shady.?oaks|housing|landlord|tenant|mobile.?home|habitability)"),
    "D": re.compile(r"(?i)(PPO|protection.?order|contempt|MCL\s+600\.2950|restrain)"),
    "E": re.compile(r"(?i)(bias|JTC|disqualif|MCR\s+2\.003|judicial.?misconduct)"),
    "F": re.compile(r"(?i)(appell|COA|MSC|MCR\s+7\.|leave.?to.?appeal|de.?novo)"),
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


def _get_columns(conn: sqlite3.Connection, table: str) -> list[str]:
    return [r["name"] for r in conn.execute(f"PRAGMA table_info([{table}])").fetchall()]


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------
def classify_query(text: str) -> list[str]:
    """Keyword-based routing to brain modules. Returns list of brain IDs."""
    matched: list[str] = []
    for brain_id, pattern in BRAIN_PATTERNS.items():
        if pattern.search(text):
            matched.append(brain_id)
    # Default to Ω2 (evidence) if nothing matches
    return matched if matched else ["Ω2"]


def detect_lane(text: str, explicit_lane: str | None = None) -> str | None:
    """Detect which case lane a query relates to."""
    if explicit_lane:
        return explicit_lane.upper()
    for lane_code, pattern in LANE_PATTERNS.items():
        if pattern.search(text):
            return lane_code
    return None


def query_brain(brain_id: str, query: str, conn: sqlite3.Connection, lane: str | None = None) -> dict[str, Any]:
    """Execute relevant queries against a brain's DB tables."""
    tables = BRAIN_TABLES.get(brain_id, [])
    results: dict[str, Any] = {"brain": brain_id, "tables_queried": [], "results": []}

    # Extract search keywords (words ≥3 chars)
    keywords = [w for w in re.findall(r"\w+", query.lower()) if len(w) >= 3]

    for tbl in tables:
        if not _table_exists(conn, tbl):
            continue

        cols = _get_columns(conn, tbl)
        results["tables_queried"].append(tbl)

        # Build WHERE clause: search text columns for keywords
        text_cols = [c for c in cols if any(
            hint in c.lower() for hint in
            ("name", "text", "quote", "desc", "title", "summary", "content", "type", "claim", "vehicle", "source")
        )]

        if not text_cols:
            # No obvious text columns — just get summary count
            cnt = conn.execute(f"SELECT COUNT(*) FROM [{tbl}]").fetchone()[0]
            results["results"].append({"table": tbl, "total_count": cnt})
            continue

        # Search with LIKE for each keyword on each text column
        conditions: list[str] = []
        params: list[str] = []
        for kw in keywords[:5]:  # Limit to 5 keywords
            col_ors = " OR ".join(f"[{c}] LIKE ?" for c in text_cols)
            conditions.append(f"({col_ors})")
            params.extend([f"%{kw}%"] * len(text_cols))

        # Add lane filter if applicable
        lane_col = next((c for c in cols if c.lower() in ("case_lane", "lane", "vehicle_name")), None)
        if lane and lane_col:
            conditions.append(f"[{lane_col}] LIKE ?")
            params.append(f"%{lane}%")

        where = " AND ".join(conditions) if conditions else "1=1"
        sql = f"SELECT * FROM [{tbl}] WHERE {where} LIMIT 20"

        try:
            rows = conn.execute(sql, params).fetchall()
            results["results"].append({
                "table": tbl,
                "match_count": len(rows),
                "rows": [dict(r) for r in rows],
            })
        except Exception as exc:
            results["results"].append({"table": tbl, "error": str(exc)})

    return results


def cross_wire(brain_results: list[dict]) -> dict:
    """Merge results from multiple brains, deduplicate."""
    merged: dict = {
        "brains_queried": [r["brain"] for r in brain_results],
        "total_tables": sum(len(r.get("tables_queried", [])) for r in brain_results),
        "total_matches": 0,
        "combined_results": [],
    }

    seen_keys: set[str] = set()
    for br in brain_results:
        for table_result in br.get("results", []):
            for row in table_result.get("rows", []):
                # Dedup by creating a key from first few values
                vals = list(row.values())[:3]
                key = "|".join(str(v) for v in vals)
                if key not in seen_keys:
                    seen_keys.add(key)
                    merged["combined_results"].append({
                        "brain": br["brain"],
                        "table": table_result.get("table"),
                        **row,
                    })
                    merged["total_matches"] += 1

    return merged


def format_output(merged: dict, as_json: bool = False) -> None:
    """Pretty-print or JSON output."""
    if as_json:
        # Sanitize for JSON serialization
        print(json.dumps(merged, indent=2, default=str))
        return

    print("=" * 70)
    print("  OMEGA-INFINITY QUERY RESULTS")
    print("=" * 70)
    print(f"\n  Brains queried: {', '.join(merged['brains_queried'])}")
    print(f"  Tables searched: {merged['total_tables']}")
    print(f"  Matches found:  {merged['total_matches']}")
    print("-" * 70)

    if not merged["combined_results"]:
        print("\n  No results found. Try broadening your query.")
    else:
        for i, row in enumerate(merged["combined_results"][:25], 1):
            brain = row.pop("brain", "?")
            table = row.pop("table", "?")
            print(f"\n  [{i}] {brain} → {table}")
            for k, v in list(row.items())[:6]:
                val_str = str(v)[:120] if v else ""
                if val_str:
                    print(f"      {k}: {val_str}")

    print("\n" + "=" * 70)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    parser = argparse.ArgumentParser(description="OMEGA-INFINITY Master Query Router")
    parser.add_argument("query", nargs="?", help="Natural language query")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help="Path to primary DB")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--lane", choices=["A", "B", "C", "D", "E", "F"], help="Filter to specific lane")
    args = parser.parse_args()

    if not args.query:
        parser.error("Please provide a query, e.g.: omega_kernel.py \"What evidence about McNeill?\"")

    if not args.db.is_file():
        msg = f"DB not found: {args.db}"
        print(json.dumps({"error": msg}) if args.json else f"❌ {msg}")
        return 1

    try:
        conn = _connect(args.db)

        # Classify query → brain IDs
        brains = classify_query(args.query)
        lane = detect_lane(args.query, args.lane)

        # Query each brain
        brain_results: list[dict] = []
        for brain_id in brains:
            result = query_brain(brain_id, args.query, conn, lane)
            brain_results.append(result)

        # Merge and deduplicate
        merged = cross_wire(brain_results)
        merged["query"] = args.query
        merged["detected_lane"] = lane

        format_output(merged, as_json=args.json)
        conn.close()
    except Exception as exc:
        msg = str(exc)
        print(json.dumps({"error": msg}) if args.json else f"❌ Error: {msg}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
