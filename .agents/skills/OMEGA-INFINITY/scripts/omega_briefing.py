#!/usr/bin/env python3
"""OMEGA-INFINITY Per-Lane Intelligence Briefing Generator.

Generates comprehensive status briefings for any litigation lane (A-F)
or an executive summary across all lanes.
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

LANE_CONFIG: dict[str, dict[str, Any]] = {
    "A": {
        "label": "Custody",
        "case_number": "2024-001507-DC",
        "parties": "Pigors v. Watson",
        "judge": "Hon. Jenny L. McNeill",
        "court": "14th Circuit Court, Family Division",
        "meek": "MEEK2",
        "key_topics": ["custody", "parenting", "FOC", "best interest", "MCL 722"],
    },
    "B": {
        "label": "Housing",
        "case_number": "2025-002760-CZ",
        "parties": "Pigors v. Shady Oaks / Homes of America",
        "judge": "TBD",
        "court": "14th Circuit Court, Civil Division",
        "meek": "MEEK1",
        "key_topics": ["shady oaks", "housing", "habitability", "lockout", "title"],
    },
    "C": {
        "label": "Convergence",
        "case_number": "Multi-lane",
        "parties": "Cross-lane coordination",
        "judge": "Multiple",
        "court": "Multiple",
        "meek": None,
        "key_topics": ["convergence", "cross-lane", "multi-case"],
    },
    "D": {
        "label": "PPO / Protection Orders",
        "case_number": "2023-5907-PP",
        "parties": "Watson v. Pigors (PPO)",
        "judge": "Hon. Jenny L. McNeill",
        "court": "14th Circuit Court",
        "meek": "MEEK3",
        "key_topics": ["PPO", "protection order", "contempt", "bond"],
    },
    "E": {
        "label": "Judicial Misconduct",
        "case_number": "2024-001507-DC (JTC)",
        "parties": "Re: Hon. Jenny L. McNeill",
        "judge": "JTC Panel",
        "court": "Judicial Tenure Commission",
        "meek": "MEEK4",
        "key_topics": ["bias", "JTC", "disqualification", "MCR 2.003", "misconduct"],
    },
    "F": {
        "label": "Appellate",
        "case_number": "COA 366810",
        "parties": "Pigors v. Watson (Appeal)",
        "judge": "COA Panel",
        "court": "Michigan Court of Appeals",
        "meek": "MEEK5",
        "key_topics": ["appeal", "COA", "MSC", "standard of review", "MCR 7"],
    },
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


def _lane_where(cols: list[str], lane: str) -> tuple[str, tuple]:
    """Build WHERE clause for lane filtering."""
    lane_col = _find_lane_col(cols)
    if lane_col:
        return f"[{lane_col}] LIKE ?", (f"%{lane}%",)
    return "1=1", ()


# ---------------------------------------------------------------------------
# Briefing components
# ---------------------------------------------------------------------------
def _evidence_summary(conn: sqlite3.Connection, lane: str) -> dict:
    """Evidence count + top 5 strongest quotes for this lane."""
    result: dict[str, Any] = {"count": 0, "top_quotes": []}

    if not _table_exists(conn, "evidence_quotes"):
        result["note"] = "evidence_quotes table not found"
        return result

    cols = _get_columns(conn, "evidence_quotes")
    where, params = _lane_where(cols, lane)

    result["count"] = _safe_count(conn, "evidence_quotes", where, params)

    # Find text and strength columns
    text_col = next((c for c in cols if "quote" in c.lower() or "text" in c.lower()), None)
    strength_col = next((c for c in cols if "strength" in c.lower() or "score" in c.lower() or "weight" in c.lower()), None)

    if text_col:
        order = f"ORDER BY [{strength_col}] DESC" if strength_col else ""
        sql = f"SELECT * FROM evidence_quotes WHERE {where} {order} LIMIT 5"
        rows = conn.execute(sql, params).fetchall()
        for r in rows:
            row_dict = dict(r)
            quote_text = str(row_dict.get(text_col, ""))[:200]
            entry: dict[str, Any] = {"text": quote_text}
            if strength_col and strength_col in row_dict:
                entry["strength"] = row_dict[strength_col]
            result["top_quotes"].append(entry)

    return result


def _filing_readiness(conn: sqlite3.Connection, lane: str) -> list[dict]:
    """Filing readiness for vehicles in this lane."""
    if not _table_exists(conn, "filing_readiness"):
        return [{"note": "filing_readiness table not found"}]

    cols = _get_columns(conn, "filing_readiness")
    where, params = _lane_where(cols, lane)

    rows = conn.execute(
        f"SELECT * FROM filing_readiness WHERE {where} LIMIT 10", params
    ).fetchall()

    if not rows:
        # Try without lane filter (small table, show all)
        rows = conn.execute("SELECT * FROM filing_readiness LIMIT 10").fetchall()

    return [dict(r) for r in rows]


def _authority_coverage(conn: sqlite3.Connection, lane: str) -> dict:
    """Key MCR/MCL rules coverage."""
    result: dict[str, Any] = {"count": 0, "key_authorities": []}

    if not _table_exists(conn, "authority_master_index"):
        result["note"] = "authority_master_index table not found"
        return result

    result["count"] = _safe_count(conn, "authority_master_index")

    cols = _get_columns(conn, "authority_master_index")
    # Find a text column to search for lane-relevant rules
    text_col = next(
        (c for c in cols if any(h in c.lower() for h in ("rule", "citation", "authority", "name", "title"))),
        cols[0] if cols else None,
    )

    if text_col:
        config = LANE_CONFIG.get(lane, {})
        topics = config.get("key_topics", [])
        for topic in topics[:3]:
            rows = conn.execute(
                f"SELECT [{text_col}] FROM authority_master_index WHERE [{text_col}] LIKE ? LIMIT 5",
                (f"%{topic}%",),
            ).fetchall()
            for r in rows:
                result["key_authorities"].append(str(r[0])[:120])

    return result


def _timeline_summary(conn: sqlite3.Connection, lane: str) -> dict:
    """Key dates and next deadline."""
    result: dict[str, Any] = {"event_count": 0, "next_deadline": None, "recent_events": []}

    # Timeline events
    for tbl in ("timeline_events", "docket_events"):
        if not _table_exists(conn, tbl):
            continue
        cols = _get_columns(conn, tbl)
        where, params = _lane_where(cols, lane)
        cnt = _safe_count(conn, tbl, where, params)
        result["event_count"] += max(cnt, 0)

        date_col = next((c for c in cols if "date" in c.lower()), None)
        desc_col = next((c for c in cols if any(h in c.lower() for h in ("desc", "title", "event", "text", "summary"))), None)

        if date_col:
            sql = f"SELECT * FROM [{tbl}] WHERE {where} ORDER BY [{date_col}] DESC LIMIT 5"
            rows = conn.execute(sql, params).fetchall()
            for r in rows:
                rd = dict(r)
                entry: dict[str, Any] = {"date": rd.get(date_col)}
                if desc_col:
                    entry["description"] = str(rd.get(desc_col, ""))[:100]
                result["recent_events"].append(entry)

    # Next deadline
    if _table_exists(conn, "deadlines"):
        cols_dl = _get_columns(conn, "deadlines")
        date_col = next((c for c in cols_dl if "date" in c.lower() or "due" in c.lower()), None)
        if date_col:
            dl_where, dl_params = _lane_where(cols_dl, lane)
            row = conn.execute(
                f"SELECT * FROM deadlines WHERE {dl_where} AND [{date_col}] >= date('now') ORDER BY [{date_col}] ASC LIMIT 1",
                dl_params,
            ).fetchone()
            if row:
                result["next_deadline"] = dict(row)

    return result


def _adversary_posture(conn: sqlite3.Connection, lane: str) -> dict:
    """Adversary posture assessment."""
    result: dict[str, Any] = {"harms": 0, "contradictions": 0, "patterns": []}

    for tbl, key in [("adversary_harm_summary", "harms"), ("extracted_harms", "harms")]:
        if _table_exists(conn, tbl):
            cols = _get_columns(conn, tbl)
            where, params = _lane_where(cols, lane)
            cnt = _safe_count(conn, tbl, where, params)
            if cnt > 0:
                result[key] = cnt

    if _table_exists(conn, "contradiction_map"):
        result["contradictions"] = _safe_count(conn, "contradiction_map")

    return result


def _lane_gaps(conn: sqlite3.Connection, lane: str) -> list[str]:
    """Quick gap check for this lane."""
    gaps: list[str] = []

    # Check evidence count
    if _table_exists(conn, "evidence_quotes"):
        cols = _get_columns(conn, "evidence_quotes")
        where, params = _lane_where(cols, lane)
        cnt = _safe_count(conn, "evidence_quotes", where, params)
        if cnt < 50:
            gaps.append(f"Low evidence count ({cnt}) — need more evidence harvest")

    # Check witness coverage
    for tbl in ("witness_list", "witness_profiles"):
        if _table_exists(conn, tbl):
            cols = _get_columns(conn, tbl)
            where, params = _lane_where(cols, lane)
            cnt = _safe_count(conn, tbl, where, params)
            if cnt == 0:
                gaps.append(f"No witnesses cataloged in {tbl}")

    return gaps


# ---------------------------------------------------------------------------
# Main briefing functions
# ---------------------------------------------------------------------------
def lane_briefing(lane: str, conn: sqlite3.Connection) -> dict:
    """Full briefing for one lane."""
    config = LANE_CONFIG.get(lane, {})

    briefing: dict[str, Any] = {
        "lane": lane,
        "label": config.get("label", "Unknown"),
        "case_number": config.get("case_number", "N/A"),
        "parties": config.get("parties", "N/A"),
        "judge": config.get("judge", "N/A"),
        "court": config.get("court", "N/A"),
        "evidence": _evidence_summary(conn, lane),
        "filing_readiness": _filing_readiness(conn, lane),
        "authority_coverage": _authority_coverage(conn, lane),
        "timeline": _timeline_summary(conn, lane),
        "adversary_posture": _adversary_posture(conn, lane),
        "gaps": _lane_gaps(conn, lane),
        "recommended_actions": [],
    }

    # Generate recommendations from gaps
    for gap in briefing["gaps"]:
        if "evidence" in gap.lower():
            briefing["recommended_actions"].append("Run evidence-warfare-commander for this lane")
        elif "witness" in gap.lower():
            briefing["recommended_actions"].append("Run subpoena-engine to identify witnesses")

    ev_count = briefing["evidence"].get("count", 0)
    if isinstance(ev_count, int) and ev_count > 100:
        briefing["recommended_actions"].append("Evidence base is strong — focus on filing readiness")

    return briefing


def all_lanes_briefing(conn: sqlite3.Connection) -> dict:
    """Executive summary across all 6 lanes."""
    summary: dict[str, Any] = {"lanes": {}, "totals": {"evidence": 0, "events": 0}}

    for lane_code in LANE_CONFIG:
        brief = lane_briefing(lane_code, conn)
        ev_count = brief["evidence"].get("count", 0)
        ev_count = ev_count if isinstance(ev_count, int) and ev_count > 0 else 0
        event_count = brief["timeline"].get("event_count", 0)

        summary["lanes"][lane_code] = {
            "label": brief["label"],
            "case_number": brief["case_number"],
            "evidence_count": ev_count,
            "event_count": event_count,
            "gap_count": len(brief["gaps"]),
            "next_deadline": brief["timeline"].get("next_deadline"),
        }
        summary["totals"]["evidence"] += ev_count
        summary["totals"]["events"] += event_count

    return summary


def compare_lanes(conn: sqlite3.Connection) -> list[dict]:
    """Cross-lane strength comparison table."""
    rows: list[dict] = []

    for lane_code in LANE_CONFIG:
        config = LANE_CONFIG[lane_code]
        ev_count = 0
        if _table_exists(conn, "evidence_quotes"):
            cols = _get_columns(conn, "evidence_quotes")
            where, params = _lane_where(cols, lane_code)
            ev_count = max(_safe_count(conn, "evidence_quotes", where, params), 0)

        jv_count = 0
        if lane_code == "E" and _table_exists(conn, "judicial_violations"):
            jv_count = _safe_count(conn, "judicial_violations")

        rows.append({
            "lane": lane_code,
            "label": config["label"],
            "evidence": ev_count,
            "judicial_violations": jv_count if lane_code == "E" else "N/A",
            "strength": "STRONG" if ev_count > 500 else "MODERATE" if ev_count > 100 else "WEAK" if ev_count > 0 else "EMPTY",
        })

    return rows


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------
def print_briefing(data: dict, lane: str | None, as_json: bool = False) -> None:
    if as_json:
        print(json.dumps(data, indent=2, default=str))
        return

    print("=" * 70)

    if lane and lane != "ALL":
        # Single lane briefing
        print(f"  OMEGA-INFINITY INTELLIGENCE BRIEFING — LANE {lane}")
        print("=" * 70)

        print(f"\n  Case:    {data.get('case_number', 'N/A')}")
        print(f"  Parties: {data.get('parties', 'N/A')}")
        print(f"  Judge:   {data.get('judge', 'N/A')}")
        print(f"  Court:   {data.get('court', 'N/A')}")

        # Evidence
        ev = data.get("evidence", {})
        print(f"\n  📦 EVIDENCE: {ev.get('count', 0):,} records")
        for q in ev.get("top_quotes", [])[:3]:
            print(f"     \"{q.get('text', '')[:100]}...\"")

        # Filing readiness
        print(f"\n  📋 FILING READINESS")
        for fr in data.get("filing_readiness", [])[:5]:
            vals = list(fr.values())[:4]
            print(f"     {' | '.join(str(v) for v in vals)}")

        # Timeline
        tl = data.get("timeline", {})
        print(f"\n  📅 TIMELINE: {tl.get('event_count', 0)} events")
        if tl.get("next_deadline"):
            dl = tl["next_deadline"]
            print(f"     ⏰ Next deadline: {dl}")
        for ev_item in tl.get("recent_events", [])[:3]:
            print(f"     {ev_item.get('date', '?')}: {ev_item.get('description', '')}")

        # Adversary
        adv = data.get("adversary_posture", {})
        print(f"\n  ⚔️  ADVERSARY POSTURE")
        print(f"     Harms documented: {adv.get('harms', 0)}")
        print(f"     Contradictions: {adv.get('contradictions', 0)}")

        # Gaps
        gaps = data.get("gaps", [])
        if gaps:
            print(f"\n  🕳️  GAPS ({len(gaps)})")
            for g in gaps:
                print(f"     ❌ {g}")

        # Recommendations
        recs = data.get("recommended_actions", [])
        if recs:
            print(f"\n  💡 RECOMMENDED ACTIONS")
            for r in recs:
                print(f"     → {r}")

    else:
        # Executive summary
        print("  OMEGA-INFINITY EXECUTIVE BRIEFING — ALL LANES")
        print("=" * 70)

        lanes_data = data.get("lanes", {})
        totals = data.get("totals", {})

        print(f"\n  {'Lane':<6} {'Label':<25} {'Evidence':>10} {'Events':>8} {'Gaps':>6}")
        print(f"  {'─' * 60}")
        for lc, ld in lanes_data.items():
            print(
                f"  {lc:<6} {ld['label']:<25} {ld['evidence_count']:>10,} {ld['event_count']:>8} {ld['gap_count']:>6}"
            )
        print(f"  {'─' * 60}")
        print(
            f"  {'TOTAL':<6} {'':<25} {totals.get('evidence', 0):>10,} {totals.get('events', 0):>8}"
        )

    print("\n" + "=" * 70)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    parser = argparse.ArgumentParser(description="OMEGA-INFINITY Per-Lane Intelligence Briefing")
    parser.add_argument("--lane", choices=["A", "B", "C", "D", "E", "F", "ALL"], default="ALL", help="Lane to brief")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help="Path to primary DB")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    if not args.db.is_file():
        msg = f"DB not found: {args.db}"
        print(json.dumps({"error": msg}) if args.json else f"❌ {msg}")
        return 1

    try:
        conn = _connect(args.db)

        if args.lane == "ALL":
            data = all_lanes_briefing(conn)
            print_briefing(data, "ALL", as_json=args.json)

            if not args.json:
                # Also print comparison table
                comparison = compare_lanes(conn)
                print("\n  CROSS-LANE STRENGTH COMPARISON")
                print(f"  {'─' * 55}")
                for row in comparison:
                    print(
                        f"  Lane {row['lane']} ({row['label']:<20}): "
                        f"{row['evidence']:>6} evidence → {row['strength']}"
                    )
        else:
            data = lane_briefing(args.lane, conn)
            print_briefing(data, args.lane, as_json=args.json)

        conn.close()
    except Exception as exc:
        msg = str(exc)
        print(json.dumps({"error": msg}) if args.json else f"❌ Error: {msg}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
