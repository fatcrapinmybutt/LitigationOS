"""
LitigationOS DuckDB Analytics Dashboards
=========================================
Instant analytical dashboards over litigation_context.db via DuckDB.

DuckDB's columnar engine runs GROUP BY, window functions, and cross-table
JOINs 10-100x faster than SQLite on 175K+ row tables. Every dashboard
returns a structured dict with `summary`, `data`, and `generated_at`.

Usage:
    from analytics.dashboards import evidence_dashboard, full_dashboard

    result = evidence_dashboard()
    print(result["summary"])

CLI:
    python dashboards.py evidence
    python dashboards.py full
"""

from __future__ import annotations

import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any, Optional

import duckdb

DB_PATH = Path(__file__).resolve().parent.parent.parent.parent / "litigation_context.db"

# Lane labels for consistent display
LANE_MAP = {
    "A": "A_CUSTODY", "B": "B_HOUSING", "C": "C_FEDERAL",
    "D": "D_PPO", "E": "E_MISCONDUCT", "F": "F_APPELLATE",
}
LANES = list(LANE_MAP.values())
LANE_KEYS = list(LANE_MAP.keys())
SEPARATION_ANCHOR = date(2025, 7, 29)


# ---------------------------------------------------------------------------
# Connection management
# ---------------------------------------------------------------------------

def get_connection(db_path: Optional[str] = None) -> duckdb.DuckDBPyConnection:
    """Get a DuckDB in-memory connection with SQLite attached read-only.

    Uses DuckDB's SQLite scanner extension for zero-copy analytical queries
    over the litigation database without locking SQLite or risking BUSY errors.
    """
    path = db_path or str(DB_PATH)
    if not Path(path).exists():
        raise FileNotFoundError(f"Database not found: {path}")

    con = duckdb.connect(":memory:")
    con.execute("INSTALL sqlite; LOAD sqlite;")
    con.execute("SET sqlite_all_varchar = true;")
    con.execute(f"ATTACH '{path}' AS lit (TYPE SQLITE, READ_ONLY);")
    return con


def _run(con: duckdb.DuckDBPyConnection, sql: str, params: list | None = None) -> list[dict]:
    """Execute a query and return a list of dicts with column names as keys."""
    result = con.execute(sql, params or [])
    cols = [desc[0] for desc in result.description]
    return [dict(zip(cols, row)) for row in result.fetchall()]


def _stamp(summary: str, data: Any) -> dict:
    """Wrap dashboard output in the standard envelope."""
    return {
        "summary": summary,
        "data": data,
        "generated_at": datetime.now().isoformat(),
    }


def _safe_int(v: Any) -> int:
    """Coerce a DuckDB value to int, handling None and VARCHAR passthrough."""
    if v is None:
        return 0
    try:
        return int(v)
    except (ValueError, TypeError):
        return 0


def _safe_float(v: Any, decimals: int = 2) -> float:
    if v is None:
        return 0.0
    try:
        return round(float(v), decimals)
    except (ValueError, TypeError):
        return 0.0


# ---------------------------------------------------------------------------
# 1. Evidence Dashboard
# ---------------------------------------------------------------------------

def evidence_dashboard(db_path: Optional[str] = None) -> dict:
    """Evidence distribution: per-lane counts, categories, top sources, filing coverage."""
    con = get_connection(db_path)
    try:
        # Per-lane evidence counts
        lane_counts = _run(con, """
            SELECT
                COALESCE(lane, 'UNASSIGNED')  AS lane,
                COUNT(*)                       AS total,
                COUNT(DISTINCT source_file)    AS unique_sources,
                COUNT(DISTINCT category)       AS category_count,
                AVG(CAST(relevance_score AS DOUBLE)) AS avg_relevance
            FROM lit.evidence_quotes
            GROUP BY lane
            ORDER BY total DESC
        """)

        # Top 15 categories across all lanes
        top_categories = _run(con, """
            SELECT
                COALESCE(category, 'uncategorized') AS category,
                COUNT(*)                             AS total,
                COUNT(DISTINCT lane)                 AS lane_spread
            FROM lit.evidence_quotes
            GROUP BY category
            ORDER BY total DESC
            LIMIT 15
        """)

        # Top 10 source files by evidence volume
        top_sources = _run(con, """
            SELECT
                COALESCE(source_file, 'unknown') AS source,
                COUNT(*)                          AS quotes,
                COUNT(DISTINCT category)          AS categories,
                COUNT(DISTINCT lane)              AS lanes
            FROM lit.evidence_quotes
            GROUP BY source_file
            ORDER BY quotes DESC
            LIMIT 10
        """)

        # Filing coverage: how many quotes reference filings
        filing_coverage = _run(con, """
            SELECT
                COUNT(*)                                                  AS total_quotes,
                SUM(CASE WHEN filing_refs IS NOT NULL
                          AND CAST(filing_refs AS VARCHAR) != '' THEN 1 ELSE 0 END) AS with_filing_ref,
                SUM(CASE WHEN is_duplicate = '1' THEN 1 ELSE 0 END)     AS duplicates
            FROM lit.evidence_quotes
        """)

        total = _safe_int(filing_coverage[0]["total_quotes"]) if filing_coverage else 0
        with_ref = _safe_int(filing_coverage[0]["with_filing_ref"]) if filing_coverage else 0
        lane_count = len([l for l in lane_counts if l["lane"] != "UNASSIGNED"])

        summary = (
            f"{total:,} evidence quotes across {lane_count} lanes. "
            f"{with_ref:,} ({_safe_float(with_ref / total * 100 if total else 0, 1)}%) linked to filings."
        )

        return _stamp(summary, {
            "by_lane": lane_counts,
            "top_categories": top_categories,
            "top_sources": top_sources,
            "filing_coverage": filing_coverage[0] if filing_coverage else {},
        })
    finally:
        con.close()


# ---------------------------------------------------------------------------
# 2. Authority Dashboard
# ---------------------------------------------------------------------------

def authority_dashboard(db_path: Optional[str] = None) -> dict:
    """Authority chain health: coverage per lane, relationship types, orphans, strongest chains."""
    con = get_connection(db_path)
    try:
        # Coverage per lane
        lane_coverage = _run(con, """
            SELECT
                COALESCE(lane, 'NONE')                AS lane,
                COUNT(*)                               AS total_chains,
                COUNT(DISTINCT primary_citation)       AS unique_primary,
                COUNT(DISTINCT supporting_citation)    AS unique_supporting,
                COUNT(DISTINCT relationship)           AS relationship_types
            FROM lit.authority_chains_v2
            GROUP BY lane
            ORDER BY total_chains DESC
        """)

        # Relationship type distribution
        rel_types = _run(con, """
            SELECT
                COALESCE(relationship, 'unknown') AS relationship,
                COUNT(*)                           AS total,
                COUNT(DISTINCT lane)               AS lane_spread
            FROM lit.authority_chains_v2
            GROUP BY relationship
            ORDER BY total DESC
            LIMIT 15
        """)

        # Strongest chains: primary citations with the most supporting citations
        strongest = _run(con, """
            SELECT
                primary_citation,
                COUNT(DISTINCT supporting_citation) AS support_count,
                COUNT(DISTINCT lane)                AS lane_spread,
                GROUP_CONCAT(DISTINCT lane)         AS lanes
            FROM lit.authority_chains_v2
            WHERE primary_citation IS NOT NULL
            GROUP BY primary_citation
            ORDER BY support_count DESC
            LIMIT 10
        """)

        # Orphan primaries: cited as primary but never as supporting
        orphan_count = _run(con, """
            SELECT COUNT(*) AS orphans FROM (
                SELECT DISTINCT primary_citation FROM lit.authority_chains_v2
                EXCEPT
                SELECT DISTINCT supporting_citation FROM lit.authority_chains_v2
            )
        """)

        total_chains = sum(_safe_int(r["total_chains"]) for r in lane_coverage)
        primary_count = sum(_safe_int(r["unique_primary"]) for r in lane_coverage)

        summary = (
            f"{total_chains:,} authority chains linking {primary_count:,} unique primary citations. "
            f"Strongest: {strongest[0]['primary_citation'] if strongest else 'N/A'} "
            f"({_safe_int(strongest[0]['support_count']) if strongest else 0} supporting cites)."
        )

        return _stamp(summary, {
            "by_lane": lane_coverage,
            "relationship_types": rel_types,
            "strongest_chains": strongest,
            "orphan_primaries": _safe_int(orphan_count[0]["orphans"]) if orphan_count else 0,
        })
    finally:
        con.close()


# ---------------------------------------------------------------------------
# 3. Impeachment Dashboard
# ---------------------------------------------------------------------------

def impeachment_dashboard(db_path: Optional[str] = None) -> dict:
    """Impeachment density: per-target severity, category spread, top 10 kill shots."""
    con = get_connection(db_path)
    try:
        # Per-category breakdown with severity stats
        by_category = _run(con, """
            SELECT
                COALESCE(category, 'unknown')                 AS category,
                COUNT(*)                                       AS total,
                AVG(CAST(impeachment_value AS DOUBLE))         AS avg_value,
                MAX(CAST(impeachment_value AS INTEGER))        AS max_value,
                MIN(CAST(impeachment_value AS INTEGER))        AS min_value,
                COUNT(DISTINCT source_file)                    AS unique_sources,
                SUM(CASE WHEN CAST(impeachment_value AS INTEGER) >= 8
                         THEN 1 ELSE 0 END)                   AS critical_count
            FROM lit.impeachment_matrix
            GROUP BY category
            ORDER BY total DESC
        """)

        # Top 10 highest-value impeachment items (kill shots)
        kill_shots = _run(con, """
            SELECT
                category,
                CAST(impeachment_value AS INTEGER) AS value,
                SUBSTR(CAST(evidence_summary AS VARCHAR), 1, 200) AS evidence_preview,
                SUBSTR(CAST(cross_exam_question AS VARCHAR), 1, 200) AS question_preview,
                event_date
            FROM lit.impeachment_matrix
            WHERE impeachment_value IS NOT NULL
            ORDER BY CAST(impeachment_value AS INTEGER) DESC
            LIMIT 10
        """)

        # Cross-exam question coverage
        question_stats = _run(con, """
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN cross_exam_question IS NOT NULL
                          AND CAST(cross_exam_question AS VARCHAR) != ''
                         THEN 1 ELSE 0 END) AS with_questions
            FROM lit.impeachment_matrix
        """)

        total = _safe_int(question_stats[0]["total"]) if question_stats else 0
        with_q = _safe_int(question_stats[0]["with_questions"]) if question_stats else 0
        critical = sum(_safe_int(r["critical_count"]) for r in by_category)

        summary = (
            f"{total:,} impeachment items across {len(by_category)} categories. "
            f"{critical:,} critical (value ≥ 8). "
            f"{with_q:,} have cross-exam questions ready."
        )

        return _stamp(summary, {
            "by_category": by_category,
            "kill_shots": kill_shots,
            "question_coverage": {
                "total": total,
                "with_questions": with_q,
                "coverage_pct": _safe_float(with_q / total * 100 if total else 0, 1),
            },
        })
    finally:
        con.close()


# ---------------------------------------------------------------------------
# 4. Timeline Dashboard
# ---------------------------------------------------------------------------

def timeline_dashboard(db_path: Optional[str] = None) -> dict:
    """Timeline analysis: events per month, gaps, actor frequency, severity distribution."""
    con = get_connection(db_path)
    try:
        # Events per month (using string slicing since dates are TEXT)
        by_month = _run(con, """
            SELECT
                SUBSTR(CAST(event_date AS VARCHAR), 1, 7) AS month,
                COUNT(*)                                   AS events,
                COUNT(DISTINCT actors)                     AS unique_actors,
                COUNT(DISTINCT lane)                       AS lanes_active
            FROM lit.timeline_events
            WHERE event_date IS NOT NULL
              AND LENGTH(CAST(event_date AS VARCHAR)) >= 7
            GROUP BY month
            ORDER BY month
        """)

        # Gap months (fewer than 5 events)
        gaps = [m for m in by_month if _safe_int(m["events"]) < 5 and m["month"] is not None]

        # Actor frequency (top 15)
        top_actors = _run(con, """
            SELECT
                COALESCE(actors, 'unknown') AS actor,
                COUNT(*)                     AS appearances,
                COUNT(DISTINCT lane)         AS lanes,
                COUNT(DISTINCT category)     AS categories
            FROM lit.timeline_events
            WHERE actors IS NOT NULL AND CAST(actors AS VARCHAR) != ''
            GROUP BY actors
            ORDER BY appearances DESC
            LIMIT 15
        """)

        # Severity distribution
        severity_dist = _run(con, """
            SELECT
                COALESCE(severity, 'unrated') AS severity,
                COUNT(*)                       AS total
            FROM lit.timeline_events
            GROUP BY severity
            ORDER BY total DESC
        """)

        total_events = sum(_safe_int(m["events"]) for m in by_month)
        months_covered = len(by_month)

        summary = (
            f"{total_events:,} timeline events across {months_covered} months. "
            f"{len(gaps)} gap months (<5 events). "
            f"Top actor: {top_actors[0]['actor'] if top_actors else 'N/A'}."
        )

        return _stamp(summary, {
            "by_month": by_month,
            "gap_months": gaps,
            "top_actors": top_actors,
            "severity_distribution": severity_dist,
        })
    finally:
        con.close()


# ---------------------------------------------------------------------------
# 5. Filing Readiness Dashboard
# ---------------------------------------------------------------------------

def filing_readiness_dashboard(db_path: Optional[str] = None) -> dict:
    """Filing readiness: per-lane evidence, authority, impeachment, and contradiction counts."""
    con = get_connection(db_path)
    try:
        # Evidence counts per lane
        ev = {r["lane"]: r for r in _run(con, """
            SELECT
                COALESCE(lane, 'UNASSIGNED') AS lane,
                COUNT(*)                      AS evidence_count,
                COUNT(DISTINCT source_file)   AS source_count,
                AVG(CAST(relevance_score AS DOUBLE)) AS avg_relevance
            FROM lit.evidence_quotes
            GROUP BY lane
        """)}

        # Authority counts per lane
        auth = {r["lane"]: r for r in _run(con, """
            SELECT
                COALESCE(lane, 'NONE') AS lane,
                COUNT(*)                AS authority_count,
                COUNT(DISTINCT primary_citation)    AS unique_citations,
                COUNT(DISTINCT relationship)        AS relationship_types
            FROM lit.authority_chains_v2
            GROUP BY lane
        """)}

        # Contradiction counts per lane
        contra = {r["lane"]: r for r in _run(con, """
            SELECT
                COALESCE(lane, 'NONE') AS lane,
                COUNT(*)                AS contradiction_count,
                SUM(CASE WHEN LOWER(CAST(severity AS VARCHAR)) IN ('high', 'critical')
                         THEN 1 ELSE 0 END) AS high_severity
            FROM lit.contradiction_map
            GROUP BY lane
        """)}

        # Timeline events per lane
        tl = {r["lane"]: r for r in _run(con, """
            SELECT
                COALESCE(lane, 'NONE') AS lane,
                COUNT(*)                AS timeline_count
            FROM lit.timeline_events
            GROUP BY lane
        """)}

        # Build unified readiness per lane
        readiness = []
        for db_key, display_name in LANE_MAP.items():
            e = ev.get(db_key, {})
            a = auth.get(db_key, {})
            c = contra.get(db_key, {})
            t = tl.get(db_key, {})

            ev_count = _safe_int(e.get("evidence_count"))
            auth_count = _safe_int(a.get("authority_count"))
            contra_count = _safe_int(c.get("contradiction_count"))
            tl_count = _safe_int(t.get("timeline_count"))

            # EGCP-style scoring: Evidence (25) + Grounds/Auth (25) +
            # Citations/Contradictions (25) + Presentation/Timeline (25)
            e_score = min(25, ev_count // 40)           # 1000 quotes = 25
            g_score = min(25, auth_count // 40)         # 1000 chains = 25
            c_score = min(25, contra_count * 2)         # 12 contradictions = 24
            p_score = min(25, tl_count // 4)            # 100 events = 25
            total_score = e_score + g_score + c_score + p_score

            readiness.append({
                "lane": display_name,
                "evidence_count": ev_count,
                "authority_count": auth_count,
                "contradiction_count": contra_count,
                "timeline_count": tl_count,
                "egcp_score": total_score,
                "e_score": e_score,
                "g_score": g_score,
                "c_score": c_score,
                "p_score": p_score,
                "status": "READY" if total_score >= 65 else "DEVELOPING",
                "unique_citations": _safe_int(a.get("unique_citations")),
                "avg_relevance": _safe_float(e.get("avg_relevance")),
            })

        readiness.sort(key=lambda r: r["egcp_score"], reverse=True)
        ready_count = sum(1 for r in readiness if r["status"] == "READY")

        summary = (
            f"{ready_count}/{len(LANES)} lanes READY (EGCP ≥ 65). "
            f"Top lane: {readiness[0]['lane']} (score {readiness[0]['egcp_score']})."
        )

        return _stamp(summary, {"lanes": readiness})
    finally:
        con.close()


# ---------------------------------------------------------------------------
# 6. Judicial Dashboard
# ---------------------------------------------------------------------------

def judicial_dashboard(db_path: Optional[str] = None) -> dict:
    """Judicial violations: per-type counts, severity distribution, MCR citations, timeline."""
    con = get_connection(db_path)
    try:
        # Violation type breakdown (severity is mixed text/int — use CASE mapping)
        by_type = _run(con, """
            SELECT
                COALESCE(violation_type, 'unknown') AS violation_type,
                COUNT(*)                             AS total,
                AVG(CASE
                    WHEN CAST(severity AS VARCHAR) IN ('critical','CRITICAL') THEN 10
                    WHEN CAST(severity AS VARCHAR) IN ('high','HIGH')         THEN 8
                    WHEN CAST(severity AS VARCHAR) IN ('medium','MEDIUM')     THEN 5
                    WHEN CAST(severity AS VARCHAR) IN ('low','LOW')           THEN 3
                    ELSE TRY_CAST(severity AS DOUBLE)
                END)                                 AS avg_severity,
                COUNT(DISTINCT mcr_rule)             AS unique_rules
            FROM lit.judicial_violations
            GROUP BY violation_type
            ORDER BY total DESC
        """)

        # Severity distribution
        severity_dist = _run(con, """
            SELECT
                CAST(severity AS VARCHAR) AS severity_level,
                COUNT(*)                   AS total
            FROM lit.judicial_violations
            WHERE severity IS NOT NULL
            GROUP BY CAST(severity AS VARCHAR)
            ORDER BY total DESC
        """)

        # MCR rules most frequently violated
        top_rules = _run(con, """
            SELECT
                COALESCE(mcr_rule, 'none_cited') AS rule,
                COUNT(*)                          AS violations,
                COUNT(DISTINCT violation_type)    AS violation_types
            FROM lit.judicial_violations
            WHERE mcr_rule IS NOT NULL AND CAST(mcr_rule AS VARCHAR) != ''
            GROUP BY mcr_rule
            ORDER BY violations DESC
            LIMIT 10
        """)

        # Canon violations
        canon_dist = _run(con, """
            SELECT
                COALESCE(canon, 'none') AS canon,
                COUNT(*)                 AS total
            FROM lit.judicial_violations
            WHERE canon IS NOT NULL AND CAST(canon AS VARCHAR) != ''
            GROUP BY canon
            ORDER BY total DESC
            LIMIT 10
        """)

        # Timeline: violations per month
        by_month = _run(con, """
            SELECT
                SUBSTR(CAST(date_occurred AS VARCHAR), 1, 7) AS month,
                COUNT(*)                                      AS violations
            FROM lit.judicial_violations
            WHERE date_occurred IS NOT NULL
              AND LENGTH(CAST(date_occurred AS VARCHAR)) >= 7
            GROUP BY month
            ORDER BY month
        """)

        # Berry-McNeill intelligence crossover
        cartel_intel = _run(con, """
            SELECT
                COALESCE(connection_type, 'unknown') AS connection_type,
                COUNT(*)                              AS entries,
                COUNT(DISTINCT person_a)              AS unique_person_a,
                COUNT(DISTINCT person_b)              AS unique_person_b
            FROM lit.berry_mcneill_intelligence
            GROUP BY connection_type
            ORDER BY entries DESC
        """)

        total_violations = sum(_safe_int(r["total"]) for r in by_type)
        high_sev = sum(
            _safe_int(r["total"]) for r in severity_dist
            if str(r["severity_level"]).lower() in ("critical", "high", "8", "9", "10")
        )

        summary = (
            f"{total_violations:,} judicial violations documented across "
            f"{len(by_type)} types. {high_sev} high-severity (≥8). "
            f"{sum(_safe_int(r['entries']) for r in cartel_intel)} cartel intelligence entries."
        )

        return _stamp(summary, {
            "by_type": by_type,
            "severity_distribution": severity_dist,
            "top_rules_violated": top_rules,
            "canon_violations": canon_dist,
            "by_month": by_month,
            "cartel_intelligence": cartel_intel,
        })
    finally:
        con.close()


# ---------------------------------------------------------------------------
# 7. Separation Dashboard
# ---------------------------------------------------------------------------

def separation_dashboard(db_path: Optional[str] = None) -> dict:
    """Separation tracking: days since July 29 2025, harm rate, milestone dates."""
    today = date.today()
    days = (today - SEPARATION_ANCHOR).days
    weeks = days // 7
    months = round(days / 30.44, 1)

    # Milestone tracking
    milestones = [
        {"days": 30, "label": "1 month", "reached": days >= 30},
        {"days": 90, "label": "3 months", "reached": days >= 90},
        {"days": 180, "label": "6 months", "reached": days >= 180},
        {"days": 270, "label": "9 months", "reached": days >= 270},
        {"days": 365, "label": "1 year", "reached": days >= 365},
    ]

    result = {
        "anchor_date": str(SEPARATION_ANCHOR),
        "current_date": str(today),
        "days_separated": days,
        "weeks": weeks,
        "months_approx": months,
        "milestones": milestones,
        "constitutional_basis": [
            "Troxel v. Granville, 530 U.S. 57 (2000) — fundamental right to parent",
            "Mathews v. Eldridge, 424 U.S. 319 (1976) — due process balancing",
            "US Const. Amend. XIV — substantive due process",
        ],
    }

    # If DB is available, pull harm accumulation data
    con = None
    try:
        con = get_connection(db_path)
        harm_data = _run(con, """
            SELECT
                COUNT(*) AS total_events,
                COUNT(DISTINCT category) AS harm_categories,
                COUNT(DISTINCT actors) AS actors_involved
            FROM lit.timeline_events
            WHERE event_date >= '2025-07-29'
        """)
        if harm_data:
            hd = harm_data[0]
            events_since = _safe_int(hd["total_events"])
            result["events_since_separation"] = events_since
            result["harm_rate_per_day"] = _safe_float(events_since / days if days > 0 else 0)
            result["harm_categories"] = _safe_int(hd["harm_categories"])
    except Exception:
        result["events_since_separation"] = "DB unavailable"
    finally:
        if con:
            con.close()

    summary = (
        f"L.D.W. separated from father for {days} days ({months} months) since July 29, 2025. "
        f"Constitutional harm accruing daily under Troxel and 14th Amendment."
    )

    return _stamp(summary, result)


# ---------------------------------------------------------------------------
# 8. Full Dashboard
# ---------------------------------------------------------------------------

def full_dashboard(db_path: Optional[str] = None) -> dict:
    """Run ALL dashboards and return a unified report."""
    dashboards = {
        "evidence": evidence_dashboard,
        "authority": authority_dashboard,
        "impeachment": impeachment_dashboard,
        "timeline": timeline_dashboard,
        "filing_readiness": filing_readiness_dashboard,
        "judicial": judicial_dashboard,
        "separation": separation_dashboard,
    }

    results = {}
    errors = []
    for name, fn in dashboards.items():
        try:
            results[name] = fn(db_path)
        except Exception as e:
            errors.append({"dashboard": name, "error": str(e)})
            results[name] = _stamp(f"ERROR: {e}", {})

    summary_lines = [results[k].get("summary", "") for k in dashboards if k in results]

    return _stamp(
        " | ".join(line for line in summary_lines if line and not line.startswith("ERROR")),
        {"dashboards": results, "errors": errors},
    )


# ---------------------------------------------------------------------------
# CLI runner
# ---------------------------------------------------------------------------

DASHBOARD_REGISTRY = {
    "evidence": evidence_dashboard,
    "authority": authority_dashboard,
    "impeachment": impeachment_dashboard,
    "timeline": timeline_dashboard,
    "filing_readiness": filing_readiness_dashboard,
    "filing": filing_readiness_dashboard,
    "judicial": judicial_dashboard,
    "separation": separation_dashboard,
    "full": full_dashboard,
}


def main():
    import json

    name = sys.argv[1] if len(sys.argv) > 1 else "full"
    fn = DASHBOARD_REGISTRY.get(name)

    if fn is None:
        print(f"Unknown dashboard: {name}")
        print(f"Available: {', '.join(sorted(DASHBOARD_REGISTRY))}")
        sys.exit(1)

    result = fn()
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
