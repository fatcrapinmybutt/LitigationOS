"""LitigationOS MCP Server v4 Tools — Convergence & Combat Intelligence

Exposes convergence cycle outputs, EGCP scoring, gap tracking, emergence
detection, filing priority, impeachment lookup, and red team findings as
callable tool functions.

Each function returns a dict or list suitable for JSON serialization.
Integration with the FastMCP server is handled via tools_v4_bridge.py.
"""
import os
import sqlite3
from datetime import datetime

DB_PATH = os.environ.get(
    "LITIGATION_DB_PATH",
    r"C:\Users\andre\LitigationOS\litigation_context.db",
)


def get_db():
    """Open a WAL-mode connection with generous busy timeout."""
    conn = sqlite3.connect(DB_PATH, timeout=60)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    conn.row_factory = sqlite3.Row
    return conn


def _table_exists(conn, name: str) -> bool:
    return conn.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?",
        (name,),
    ).fetchone()[0] > 0


def _safe_count(conn, table: str, where: str = "1=1", params: tuple = ()) -> int:
    try:
        return conn.execute(
            f"SELECT COUNT(*) FROM [{table}] WHERE {where}", params
        ).fetchone()[0]
    except Exception:
        return 0


# ── TOOL 1: CONVERGENCE STATUS ──────────────────────────────────────

def litigation_convergence_status() -> dict:
    """Get current convergence quality score, lane scores, and cycle history.

    Returns the most recent convergence cycle results including overall
    quality score (0-100), per-lane EGCP scores, gap counts by type
    (BLOCKER/DNEW/NEXT_PATCH), emergence event count, and cycle mode.
    Use this to assess whether filings are ready to proceed.
    """
    conn = get_db()
    try:
        result = {
            "cycle_id": None,
            "quality_score": 0.0,
            "cycle_mode": "UNKNOWN",
            "lane_scores": {},
            "gaps": {"blockers": 0, "dnew": 0, "next_patch": 0},
            "emergence_count": 0,
            "regression_detected": False,
            "status": "no_cycles_run",
        }

        if not _table_exists(conn, "convergence_cycles"):
            return result

        cycle = conn.execute(
            "SELECT * FROM convergence_cycles ORDER BY created_at DESC LIMIT 1"
        ).fetchone()

        if not cycle:
            return result

        result["cycle_id"] = cycle["cycle_id"]
        result["quality_score"] = float(cycle["final_score"] or 0)
        result["cycle_mode"] = cycle["cycle_mode"]
        result["gaps"]["blockers"] = cycle["blocker_count"] or 0
        result["gaps"]["dnew"] = cycle["dnew_count"] or 0
        result["gaps"]["next_patch"] = cycle["next_patch_count"] or 0
        result["emergence_count"] = cycle["emergence_count"] or 0
        result["regression_detected"] = bool(cycle["regression_detected"])

        score = result["quality_score"]
        if score >= 95:
            result["status"] = "COURTROOM_READY"
        elif score >= 85:
            result["status"] = "NEAR_READY"
        elif score >= 70:
            result["status"] = "IN_PROGRESS"
        elif score >= 50:
            result["status"] = "SIGNIFICANT_GAPS"
        else:
            result["status"] = "CRITICAL"

        # Per-lane EGCP scores
        if _table_exists(conn, "analysis_results"):
            rows = conn.execute(
                "SELECT lane, CAST(value AS REAL) AS score "
                "FROM analysis_results WHERE metric = 'EGCP_TOTAL'"
            ).fetchall()
            for r in rows:
                result["lane_scores"][r["lane"]] = r["score"]

        return result
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()


# ── TOOL 2: EGCP SCORE ──────────────────────────────────────────────

def litigation_egcp_score(lane: str | None = None) -> dict:
    """Get EGCP (Evidence, Grounds, Citations, Presentation) scores.

    Returns per-lane EGCP component scores and totals. Each component
    is scored 0-25 for a maximum of 100. Scores above 65 indicate
    filing readiness; below 50 indicates critical gaps.

    Args:
        lane: Filter to a specific lane (e.g., 'A_CUSTODY'). Omit for all lanes.
    """
    conn = get_db()
    try:
        if not _table_exists(conn, "analysis_results"):
            return {"error": "analysis_results table not found — run analysis engine first"}

        where = "1=1"
        params: tuple = ()
        if lane:
            where = "lane = ?"
            params = (lane,)

        rows = conn.execute(
            f"SELECT lane, metric, CAST(value AS REAL) AS score "
            f"FROM analysis_results WHERE {where} ORDER BY lane, metric",
            params,
        ).fetchall()

        lanes: dict = {}
        for r in rows:
            ln = r["lane"]
            if ln not in lanes:
                lanes[ln] = {"lane": ln, "components": {}, "total": 0}
            if r["metric"] == "EGCP_TOTAL":
                lanes[ln]["total"] = r["score"]
            else:
                lanes[ln]["components"][r["metric"]] = r["score"]

        # Add filing readiness status
        for ln, data in lanes.items():
            t = data["total"]
            data["filing_ready"] = t >= 65
            data["status"] = (
                "READY" if t >= 65
                else "DEVELOPING" if t >= 50
                else "CRITICAL"
            )

        return {
            "lanes": list(lanes.values()),
            "lanes_ready": sum(1 for d in lanes.values() if d["filing_ready"]),
            "lanes_total": len(lanes),
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()


# ── TOOL 3: GAP TRACKER ─────────────────────────────────────────────

def litigation_gap_tracker(
    gap_type: str | None = None,
    lane: str | None = None,
    severity: str | None = None,
    status: str | None = None,
    limit: int = 50,
) -> dict:
    """Query convergence gaps — blockers, newly discovered issues, and deferred patches.

    Gaps are classified during convergence cycles as:
    - BLOCKER: Prevents filing progress (resolve immediately)
    - DNEW: Newly discovered this cycle (address before next filing)
    - NEXT_PATCH: Known gap, deferred to next cycle

    Args:
        gap_type: Filter by type: 'BLOCKER', 'DNEW', or 'NEXT_PATCH'. Omit for all.
        lane: Filter by case lane (e.g., 'A_CUSTODY', 'E_MISCONDUCT'). Omit for all.
        severity: Filter by severity: 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'. Omit for all.
        status: Filter by resolution status: 'OPEN', 'MITIGATED', 'RESOLVED'. Omit for all.
        limit: Maximum gaps to return (1-200).
    """
    conn = get_db()
    try:
        if not _table_exists(conn, "convergence_gaps"):
            return {"gaps": [], "summary": {"total": 0}, "status": "no_gaps_tracked"}

        conditions = ["1=1"]
        params: list = []

        if gap_type:
            conditions.append("gap_type = ?")
            params.append(gap_type)
        if lane:
            conditions.append("lane = ?")
            params.append(lane)
        if severity:
            conditions.append("severity = ?")
            params.append(severity)
        if status:
            conditions.append("status = ?")
            params.append(status)

        where = " AND ".join(conditions)

        rows = conn.execute(
            f"SELECT id, cycle_id, gap_type, lane, category, severity, "
            f"description, resolution, status, created_at "
            f"FROM convergence_gaps WHERE {where} "
            f"ORDER BY CASE severity WHEN 'CRITICAL' THEN 0 WHEN 'HIGH' THEN 1 "
            f"WHEN 'MEDIUM' THEN 2 ELSE 3 END, created_at DESC LIMIT ?",
            (*params, limit),
        ).fetchall()

        gaps = [dict(r) for r in rows]

        # Summary counts
        summary_rows = conn.execute(
            "SELECT gap_type, severity, COUNT(*) AS cnt FROM convergence_gaps "
            "WHERE status = 'OPEN' GROUP BY gap_type, severity"
        ).fetchall()
        summary = {}
        for r in summary_rows:
            key = f"{r['gap_type']}_{r['severity']}"
            summary[key] = r["cnt"]

        return {
            "gaps": gaps,
            "count": len(gaps),
            "summary": summary,
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()


# ── TOOL 4: EMERGENCE SCANNER ───────────────────────────────────────

def litigation_emergence_scan(
    signal_type: str | None = None,
    min_novelty: int = 1,
    limit: int = 30,
) -> dict:
    """Detect and retrieve cross-lane emergence patterns.

    Emergence events are patterns only visible when data from multiple
    case lanes converges. Signal types include:
    - CROSS_GRAPH: Entity/evidence overlap between lanes
    - CHAIN_COMPLETE: Authority chain reaches full support
    - CONTRADICTION: Incompatible facts across lanes
    - NOVEL_STRATEGY: New legal theory from combined data
    - WITNESS_OVERLAP: Same witness relevant to multiple lanes

    Args:
        signal_type: Filter by signal type. Omit for all types.
        min_novelty: Minimum novelty score 1-10 (higher = more significant).
        limit: Maximum events to return (1-100).
    """
    conn = get_db()
    try:
        if not _table_exists(conn, "convergence_emergence"):
            return {"events": [], "status": "no_emergence_data"}

        conditions = ["novelty_score >= ?"]
        params: list = [min_novelty]

        if signal_type:
            conditions.append("signal_type = ?")
            params.append(signal_type)

        where = " AND ".join(conditions)

        rows = conn.execute(
            f"SELECT id, cycle_id, signal_type, lanes_involved, description, "
            f"evidence_links, novelty_score, action_required, status, created_at "
            f"FROM convergence_emergence WHERE {where} "
            f"ORDER BY novelty_score DESC, created_at DESC LIMIT ?",
            (*params, limit),
        ).fetchall()

        events = [dict(r) for r in rows]
        high_novelty = sum(1 for e in events if e["novelty_score"] >= 7)

        return {
            "events": events,
            "count": len(events),
            "high_novelty_count": high_novelty,
            "signal_types_found": list(set(e["signal_type"] for e in events)),
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()


# ── TOOL 5: FILING PRIORITY ─────────────────────────────────────────

def litigation_filing_priority(lane: str | None = None, limit: int = 20) -> dict:
    """Get the current filing priority matrix ranked by strategic impact.

    Returns filings ranked by a composite score combining EGCP readiness,
    urgency, impeachment support strength, and court deadline proximity.
    Each filing includes its lane, EGCP score, draft status, and
    recommended filing sequence position.

    Args:
        lane: Filter to a specific lane. Omit for all lanes.
        limit: Maximum filings to return (1-50).
    """
    conn = get_db()
    try:
        result = {"filings": [], "lanes_ready": 0, "lanes_total": 0}

        # Get EGCP scores
        egcp = {}
        if _table_exists(conn, "analysis_results"):
            rows = conn.execute(
                "SELECT lane, CAST(value AS REAL) AS score "
                "FROM analysis_results WHERE metric = 'EGCP_TOTAL'"
            ).fetchall()
            egcp = {r["lane"]: r["score"] for r in rows}

        # Get impeachment counts per lane
        imp_counts = {}
        if _table_exists(conn, "impeachment_packages"):
            rows = conn.execute(
                "SELECT lane, COUNT(*) AS cnt FROM impeachment_packages GROUP BY lane"
            ).fetchall()
            imp_counts = {r["lane"]: r["cnt"] for r in rows}

        # Get red team critical findings per lane
        rt_counts = {}
        if _table_exists(conn, "red_team_findings"):
            rows = conn.execute(
                "SELECT affected_lane, COUNT(*) AS cnt FROM red_team_findings "
                "WHERE severity = 'CRITICAL' GROUP BY affected_lane"
            ).fetchall()
            rt_counts = {r["affected_lane"]: r["cnt"] for r in rows}

        # Build priority list
        filing_templates = [
            ("Emergency Motion to Restore Parenting Time", "A_CUSTODY", 10),
            ("Motion for Judicial Disqualification", "E_MISCONDUCT", 9),
            ("JTC Formal Complaint", "E_MISCONDUCT", 9),
            ("Application for Leave to Appeal", "F_APPELLATE", 8),
            ("Motion for Contempt", "A_CUSTODY", 8),
            ("Motion to Modify/Terminate PPO", "D_PPO", 7),
            ("§1983 Federal Complaint", "C_FEDERAL", 7),
            ("Housing Code Complaint", "B_HOUSING", 6),
        ]

        filings = []
        for name, fl, urgency in filing_templates:
            if lane and fl != lane:
                continue
            score = egcp.get(fl, 0)
            imps = imp_counts.get(fl, 0)
            rt_crit = rt_counts.get(fl, 0)
            priority = score + urgency * 10 + min(imps / 10, 20) - rt_crit * 5

            filings.append({
                "filing": name,
                "lane": fl,
                "egcp_score": score,
                "urgency": urgency,
                "impeachment_support": imps,
                "critical_vulnerabilities": rt_crit,
                "priority_score": round(priority, 1),
                "ready": score >= 65,
                "status": "READY" if score >= 65 else "DEVELOPING",
            })

        filings.sort(key=lambda x: x["priority_score"], reverse=True)
        filings = filings[:limit]

        result["filings"] = filings
        result["lanes_ready"] = sum(1 for f in filings if f["ready"])
        result["lanes_total"] = len(filings)

        return result
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()


# ── TOOL 6: IMPEACHMENT LOOKUP ──────────────────────────────────────

def litigation_impeachment_lookup(
    target: str | None = None,
    lane: str | None = None,
    severity: str | None = None,
    limit: int = 50,
) -> dict:
    """Query assembled impeachment packages by target, lane, or severity.

    Impeachment packages contain prior inconsistent statements, documented
    contradictions, and admissible evidence mapped to MRE rules for use
    in cross-examination or motion support.

    Args:
        target: Filter by impeachment target name (partial match). Omit for all.
        lane: Filter by case lane (e.g., 'A_CUSTODY'). Omit for all.
        severity: Filter by severity: 'critical', 'high', 'medium'. Omit for all.
        limit: Maximum packages to return (1-200).
    """
    conn = get_db()
    try:
        if not _table_exists(conn, "impeachment_packages"):
            return {"packages": [], "status": "no_impeachment_data"}

        cols = [r[1] for r in conn.execute("PRAGMA table_info(impeachment_packages)")]

        conditions = ["1=1"]
        params: list = []

        if target and "target" in cols:
            conditions.append("target LIKE ?")
            params.append(f"%{target}%")
        if lane and "lane" in cols:
            conditions.append("lane = ?")
            params.append(lane)
        if severity and "severity" in cols:
            conditions.append("severity = ?")
            params.append(severity)

        where = " AND ".join(conditions)
        col_list = ", ".join(cols)

        rows = conn.execute(
            f"SELECT {col_list} FROM impeachment_packages "
            f"WHERE {where} LIMIT ?",
            (*params, limit),
        ).fetchall()

        packages = [dict(r) for r in rows]

        # Summary
        summary = {}
        if "lane" in cols:
            for r in conn.execute(
                "SELECT lane, COUNT(*) AS cnt FROM impeachment_packages GROUP BY lane"
            ).fetchall():
                summary[r["lane"]] = r["cnt"]

        return {
            "packages": packages,
            "count": len(packages),
            "total_in_db": _safe_count(conn, "impeachment_packages"),
            "by_lane": summary,
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()


# ── TOOL 7: RED TEAM FINDINGS ───────────────────────────────────────

def litigation_red_team_findings(
    severity: str | None = None,
    lane: str | None = None,
    category: str | None = None,
    limit: int = 30,
) -> dict:
    """Get adversarial red team findings — vulnerabilities opposing counsel would exploit.

    Red team analysis identifies weaknesses in filings, evidence, and legal
    arguments that opposing counsel could attack. Each finding includes the
    vulnerability description, severity, affected lane, and recommended
    mitigation strategy.

    Args:
        severity: Filter by: 'CRITICAL', 'HIGH', 'MEDIUM'. Omit for all.
        lane: Filter by affected lane (e.g., 'A_CUSTODY', 'ALL'). Omit for all.
        category: Filter by category (e.g., 'Judicial Immunity', 'Hearsay'). Omit for all.
        limit: Maximum findings to return (1-100).
    """
    conn = get_db()
    try:
        if not _table_exists(conn, "red_team_findings"):
            return {"findings": [], "status": "no_red_team_data"}

        conditions = ["1=1"]
        params: list = []

        if severity:
            conditions.append("severity = ?")
            params.append(severity)
        if lane:
            conditions.append("(affected_lane = ? OR affected_lane = 'ALL')")
            params.append(lane)
        if category:
            conditions.append("category LIKE ?")
            params.append(f"%{category}%")

        where = " AND ".join(conditions)

        rows = conn.execute(
            f"SELECT id, category, vulnerability, severity, affected_lane, "
            f"mitigation, status, created_at "
            f"FROM red_team_findings WHERE {where} "
            f"ORDER BY CASE severity WHEN 'CRITICAL' THEN 0 WHEN 'HIGH' THEN 1 "
            f"WHEN 'MEDIUM' THEN 2 ELSE 3 END LIMIT ?",
            (*params, limit),
        ).fetchall()

        findings = [dict(r) for r in rows]

        # Severity distribution
        dist = {}
        for r in conn.execute(
            "SELECT severity, COUNT(*) AS cnt FROM red_team_findings GROUP BY severity"
        ).fetchall():
            dist[r["severity"]] = r["cnt"]

        return {
            "findings": findings,
            "count": len(findings),
            "total_in_db": _safe_count(conn, "red_team_findings"),
            "severity_distribution": dist,
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()


# ── TOOL 8: LEGAL KNOWLEDGE SEARCH ─────────────────────────────────


def litigation_legal_search(
    query: str,
    source_type: str | None = None,
    limit: int = 25,
) -> dict:
    """FTS5 full-text search across all Michigan legal knowledge.

    Searches MCR court rules, MCL statutes, MRE evidence rules, case law,
    and judicial canons using Porter-stemmed FTS5.

    Args:
        query: Search terms (e.g. "parenting time modification").
        source_type: Filter: 'MCR', 'MCL', 'MRE', 'CASE', 'CANON'. Omit for all.
        limit: Maximum results (1-100).
    """
    conn = get_db()
    try:
        if not _table_exists(conn, "legal_knowledge_fts"):
            return {"results": [], "status": "fts5_not_initialized", "count": 0}

        params: list = [query]
        type_filter = ""
        if source_type:
            type_filter = "AND source_type = ?"
            params.append(source_type)
        params.append(limit)

        rows = conn.execute(
            f"""
            SELECT source_type, source_id, rule_number, title,
                   snippet(legal_knowledge_fts, 4, '<b>', '</b>', '...', 40) AS snippet,
                   rank
            FROM legal_knowledge_fts
            WHERE legal_knowledge_fts MATCH ? {type_filter}
            ORDER BY rank LIMIT ?
            """,
            params,
        ).fetchall()

        total = conn.execute("SELECT COUNT(*) FROM legal_knowledge_fts").fetchone()[0]
        return {
            "results": [dict(r) for r in rows],
            "count": len(rows),
            "total_indexed": total,
            "query": query,
        }
    except Exception as e:
        return {"error": str(e), "results": [], "count": 0}
    finally:
        conn.close()


# ── TOOL 9: AUTHORITY LOOKUP ────────────────────────────────────────


def litigation_authority_lookup(
    authority_type: str,
    authority_number: str,
) -> dict:
    """Look up a specific Michigan legal authority by type and number.

    Args:
        authority_type: One of 'MCR', 'MCL', 'MRE', 'CASE'.
        authority_number: The identifier (e.g. 'MCR 2.119', 'MCL 722.23').
    """
    table_map = {
        "MCR": ("michigan_court_rules", "rule_number"),
        "MCL": ("michigan_statutes", "statute_number"),
        "MRE": ("michigan_evidence_rules", "rule_number"),
        "CASE": ("michigan_case_law", "citation"),
    }
    spec = table_map.get(authority_type.upper())
    if not spec:
        return {"error": f"Unknown authority_type '{authority_type}'."}

    table, col = spec
    conn = get_db()
    try:
        if not _table_exists(conn, table):
            return {"error": f"Table '{table}' not found", "authority": None}

        row = conn.execute(
            f"SELECT * FROM {table} WHERE {col} = ?", (authority_number,)
        ).fetchone()
        if not row:
            row = conn.execute(
                f"SELECT * FROM {table} WHERE {col} LIKE ?", (f"%{authority_number}%",)
            ).fetchone()

        if row:
            result = dict(row)
            xrefs = []
            if _table_exists(conn, "legal_cross_references"):
                xrows = conn.execute(
                    """
                    SELECT source_type, source_number, target_type, target_number, relationship
                    FROM legal_cross_references
                    WHERE (source_type = ? AND source_number = ?)
                       OR (target_type = ? AND target_number = ?)
                    """,
                    (authority_type, authority_number, authority_type, authority_number),
                ).fetchall()
                xrefs = [dict(x) for x in xrows]
            return {"authority": result, "cross_references": xrefs, "found": True}
        return {"authority": None, "found": False}
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()


# ── TOOL 10: FILING AUTHORITIES ─────────────────────────────────────


def litigation_filing_authorities(filing_id: str) -> dict:
    """Get all legal authorities required for a specific filing.

    Returns MCR rules, MCL statutes, MRE evidence rules grouped by type
    with full text and mandatory/optional status.

    Args:
        filing_id: Filing identifier (e.g. 'F1', 'F3', 'F5').
    """
    conn = get_db()
    try:
        if not _table_exists(conn, "filing_rule_map"):
            return {"error": "filing_rule_map not found", "authorities": {}}

        mappings = conn.execute(
            "SELECT authority_type, authority_number, requirement, mandatory "
            "FROM filing_rule_map WHERE filing_id = ? ORDER BY authority_type",
            (filing_id,),
        ).fetchall()

        if not mappings:
            return {"filing_id": filing_id, "authorities": {}, "count": 0, "found": False}

        result: dict = {"MCR": [], "MCL": [], "MRE": [], "CASE": []}
        table_map = {
            "MCR": ("michigan_court_rules", "rule_number"),
            "MCL": ("michigan_statutes", "statute_number"),
            "MRE": ("michigan_evidence_rules", "rule_number"),
        }

        for m in mappings:
            entry = {
                "authority_number": m["authority_number"],
                "requirement": m["requirement"],
                "mandatory": bool(m["mandatory"]),
            }
            spec = table_map.get(m["authority_type"])
            if spec:
                tbl, col = spec
                if _table_exists(conn, tbl):
                    detail = conn.execute(
                        f"SELECT title, category FROM {tbl} WHERE {col} = ?",
                        (m["authority_number"],),
                    ).fetchone()
                    if detail:
                        entry["title"] = detail["title"]
                        entry["category"] = detail["category"]
            result.setdefault(m["authority_type"], []).append(entry)

        total = sum(len(v) for v in result.values())
        return {"filing_id": filing_id, "authorities": result, "count": total, "found": True}
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()
