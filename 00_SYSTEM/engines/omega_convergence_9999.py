#!/usr/bin/env python3
"""
omega_convergence_9999.py — Iterative Convergence Cycle Runner
==============================================================
Runs improvement cycles across all filing lanes, checking convergence
criteria, detecting emergence patterns, and generating a prioritized
dashboard of next actions.

Connects to: litigation_context.db
Dependencies: sqlite3, standard library only
"""

import sys
import os
import sqlite3
import json
from datetime import datetime, timezone
from collections import defaultdict
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding='utf-8')
except (AttributeError, OSError):
    pass

DB = str(Path(__file__).resolve().parents[2] / "litigation_context.db")

LANES = ["A", "B", "C", "D", "E", "F"]
LANE_LABELS = {
    "A": "Custody/Family",
    "B": "Housing",
    "C": "Federal §1983/RICO",
    "D": "PPO",
    "E": "Judicial Misconduct",
    "F": "Appellate",
}

# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def _conn() -> sqlite3.Connection:
    """Open a WAL-mode connection with generous timeouts."""
    c = sqlite3.connect(DB, timeout=120)
    c.execute("PRAGMA busy_timeout=60000")
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA cache_size=-32000")
    c.row_factory = sqlite3.Row
    return c


def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone()
    return row is not None


def _safe_count(conn: sqlite3.Connection, table: str, where: str = "1=1",
                params: tuple = ()) -> int:
    """Return COUNT(*) from *table* with *where*, or 0 if table missing."""
    if not _table_exists(conn, table):
        return 0
    try:
        row = conn.execute(
            f"SELECT COUNT(*) FROM [{table}] WHERE {where}", params
        ).fetchone()
        return row[0] if row else 0
    except sqlite3.OperationalError:
        return 0


# ---------------------------------------------------------------------------
# 1. Convergence Criteria — per-lane metrics
# ---------------------------------------------------------------------------

def _lane_match_clause(col: str = "lane") -> str:
    """SQL fragment matching a lane value that may be multi-valued (e.g. 'A,D')."""
    return f"({col} = ? OR {col} LIKE ? || ',%' OR {col} LIKE '%,' || ? OR {col} LIKE '%,' || ? || ',%')"


def _lane_params(lane: str) -> tuple:
    return (lane, lane, lane, lane)


def count_evidence_per_lane(conn: sqlite3.Connection) -> Dict[str, int]:
    """Count evidence_quotes rows touching each lane."""
    out: Dict[str, int] = {}
    if not _table_exists(conn, "evidence_quotes"):
        return {l: 0 for l in LANES}
    for lane in LANES:
        clause = _lane_match_clause("lane")
        row = conn.execute(
            f"SELECT COUNT(*) FROM evidence_quotes WHERE {clause}",
            _lane_params(lane),
        ).fetchone()
        out[lane] = row[0] if row else 0
    return out


def count_authority_per_lane(conn: sqlite3.Connection) -> Dict[str, int]:
    """Count authority chain entries per lane from filing_readiness + filing_rule_map."""
    out: Dict[str, int] = {l: 0 for l in LANES}
    if _table_exists(conn, "filing_readiness"):
        for row in conn.execute(
            "SELECT lane, SUM(authority_count) AS total FROM filing_readiness GROUP BY lane"
        ).fetchall():
            lane_val = row["lane"] if row["lane"] else ""
            for l in LANES:
                if l in lane_val:
                    out[l] += int(row["total"] or 0)
    if _table_exists(conn, "strategic_filing_matrix"):
        for row in conn.execute(
            "SELECT lane, claim_count FROM strategic_filing_matrix"
        ).fetchall():
            lane_val = row["lane"] if row["lane"] else ""
            for l in LANES:
                if l in lane_val:
                    out[l] += int(row["claim_count"] or 0)
    return out


def count_impeachment_per_lane(conn: sqlite3.Connection) -> Dict[str, int]:
    """Count impeachment items from impeachment_matrix per lane."""
    out: Dict[str, int] = {l: 0 for l in LANES}
    if _table_exists(conn, "impeachment_matrix"):
        for row in conn.execute(
            "SELECT filing_relevance, COUNT(*) AS cnt "
            "FROM impeachment_matrix GROUP BY filing_relevance"
        ).fetchall():
            ref = str(row["filing_relevance"] or "")
            for l in LANES:
                if l in ref.upper():
                    out[l] += row["cnt"]
    # Also count chimera_impeachment via chimera_contradictions topic
    if _table_exists(conn, "chimera_impeachment"):
        total = _safe_count(conn, "chimera_impeachment")
        # Distribute proportionally to evidence per lane (best heuristic)
        ev = count_evidence_per_lane(conn)
        ev_total = max(sum(ev.values()), 1)
        for l in LANES:
            out[l] += int(total * ev[l] / ev_total)
    return out


def count_contradictions_per_lane(conn: sqlite3.Connection) -> Dict[str, int]:
    """Count contradictions — from chimera_contradictions and contradiction_map."""
    out: Dict[str, int] = {l: 0 for l in LANES}
    if _table_exists(conn, "contradiction_map"):
        for row in conn.execute(
            "SELECT lane, COUNT(*) AS cnt FROM contradiction_map GROUP BY lane"
        ).fetchall():
            lane_val = str(row["lane"] or "")
            for l in LANES:
                if l in lane_val:
                    out[l] += row["cnt"]
    if _table_exists(conn, "chimera_contradictions"):
        total = _safe_count(conn, "chimera_contradictions")
        # Distribute by evidence weight
        ev = count_evidence_per_lane(conn)
        ev_total = max(sum(ev.values()), 1)
        for l in LANES:
            out[l] += int(total * ev[l] / ev_total)
    return out


def check_open_gaps(conn: sqlite3.Connection) -> Dict[str, int]:
    """Count placeholder / gap items per lane."""
    out: Dict[str, int] = {l: 0 for l in LANES}
    # filing_readiness.placeholder_count
    if _table_exists(conn, "filing_readiness"):
        for row in conn.execute(
            "SELECT lane, SUM(placeholder_count) AS total "
            "FROM filing_readiness GROUP BY lane"
        ).fetchall():
            lane_val = str(row["lane"] or "")
            for l in LANES:
                if l in lane_val:
                    out[l] += int(row["total"] or 0)
    # Scan filing_documents for [REQUIRED], [TODO], [PLACEHOLDER] text
    if _table_exists(conn, "filing_documents") and _table_exists(conn, "filing_packages"):
        for row in conn.execute(
            "SELECT fp.lane, COUNT(*) AS cnt "
            "FROM filing_documents fd "
            "JOIN filing_packages fp ON fd.filing_id = fp.filing_id "
            "WHERE fd.content LIKE '%[REQUIRED]%' "
            "   OR fd.content LIKE '%[TODO]%' "
            "   OR fd.content LIKE '%[PLACEHOLDER]%' "
            "   OR fd.content LIKE '%[INSERT%' "
            "GROUP BY fp.lane"
        ).fetchall():
            lane_val = str(row["lane"] or "")
            for l in LANES:
                if l in lane_val:
                    out[l] += row["cnt"]
    return out


def calc_egcp_scores(conn: sqlite3.Connection) -> Dict[str, Dict[str, float]]:
    """
    Calculate EGCP-style readiness scores per lane (0-100).
    E = Evidence (0-25), G = Grounds/Authority (0-25),
    C = Citations/Impeachment (0-25), P = Presentation/Gaps (0-25).
    """
    evidence = count_evidence_per_lane(conn)
    authority = count_authority_per_lane(conn)
    impeach = count_impeachment_per_lane(conn)
    gaps = check_open_gaps(conn)

    # Thresholds for max score per component
    E_THRESHOLD = 5000   # 5000+ evidence items → 25/25
    G_THRESHOLD = 20     # 20+ authority chains → 25/25
    C_THRESHOLD = 100    # 100+ impeachment items → 25/25
    GAP_PENALTY_MAX = 25 # 0 gaps → 25/25, each gap costs points

    scores: Dict[str, Dict[str, float]] = {}
    for lane in LANES:
        e_score = min(25.0, 25.0 * evidence[lane] / max(E_THRESHOLD, 1))
        g_score = min(25.0, 25.0 * authority[lane] / max(G_THRESHOLD, 1))
        c_score = min(25.0, 25.0 * impeach[lane] / max(C_THRESHOLD, 1))
        gap_count = gaps[lane]
        p_score = max(0.0, 25.0 - gap_count * 5.0)
        total = round(e_score + g_score + c_score + p_score, 1)
        scores[lane] = {
            "evidence": round(e_score, 1),
            "grounds": round(g_score, 1),
            "citations": round(c_score, 1),
            "presentation": round(p_score, 1),
            "total": total,
        }
    return scores


# ---------------------------------------------------------------------------
# 2. Improvement Cycle
# ---------------------------------------------------------------------------

class ImprovementItem:
    """A single actionable improvement."""
    __slots__ = ("lane", "category", "priority", "description")

    def __init__(self, lane: str, category: str, priority: int, description: str):
        self.lane = lane
        self.category = category
        self.priority = priority  # 1 = highest
        self.description = description

    def __repr__(self) -> str:
        return f"[P{self.priority}][{self.lane}][{self.category}] {self.description}"


def identify_weakest_lane(evidence: Dict[str, int]) -> Tuple[str, int]:
    """Return (lane, count) with lowest evidence."""
    return min(evidence.items(), key=lambda kv: kv[1])


def identify_missing_authorities(conn: sqlite3.Connection) -> List[ImprovementItem]:
    """Find filings whose authority_count is 0 or vehicle has no rule mapping."""
    items: List[ImprovementItem] = []
    if not _table_exists(conn, "filing_readiness"):
        return items
    for row in conn.execute(
        "SELECT vehicle_name, lane, authority_count, readiness_score "
        "FROM filing_readiness WHERE authority_count = 0 OR authority_count IS NULL"
    ).fetchall():
        items.append(ImprovementItem(
            lane=row["lane"] or "?",
            category="authority",
            priority=2,
            description=f"Missing authority chain for vehicle '{row['vehicle_name']}'"
        ))
    return items


def identify_unresolved_contradictions(conn: sqlite3.Connection) -> List[ImprovementItem]:
    """Contradictions with high severity but no impeachment package."""
    items: List[ImprovementItem] = []
    if not (_table_exists(conn, "chimera_contradictions")
            and _table_exists(conn, "chimera_impeachment")):
        return items
    rows = conn.execute(
        "SELECT cc.id, cc.topic, cc.severity, cc.description "
        "FROM chimera_contradictions cc "
        "LEFT JOIN chimera_impeachment ci ON ci.contradiction_id = cc.id "
        "WHERE ci.id IS NULL AND cc.severity >= 7 "
        "ORDER BY cc.severity DESC LIMIT 20"
    ).fetchall()
    for row in rows:
        items.append(ImprovementItem(
            lane="ALL",
            category="contradiction",
            priority=3,
            description=(
                f"Unresolved contradiction (sev={row['severity']}): "
                f"{(row['description'] or row['topic'] or 'N/A')[:80]}"
            ),
        ))
    return items


def identify_placeholder_gaps(conn: sqlite3.Connection) -> List[ImprovementItem]:
    """Documents still containing placeholder text."""
    items: List[ImprovementItem] = []
    if not (_table_exists(conn, "filing_documents")
            and _table_exists(conn, "filing_packages")):
        return items
    rows = conn.execute(
        "SELECT fp.lane, fd.filename, fp.filing_id "
        "FROM filing_documents fd "
        "JOIN filing_packages fp ON fd.filing_id = fp.filing_id "
        "WHERE fd.content LIKE '%[REQUIRED]%' "
        "   OR fd.content LIKE '%[TODO]%' "
        "   OR fd.content LIKE '%[PLACEHOLDER]%' "
        "   OR fd.content LIKE '%[INSERT%' "
        "LIMIT 20"
    ).fetchall()
    for row in rows:
        items.append(ImprovementItem(
            lane=row["lane"] or "?",
            category="placeholder",
            priority=1,
            description=f"Placeholder text in {row['filename']} (filing {row['filing_id']})",
        ))
    return items


def run_improvement_cycle(conn: sqlite3.Connection) -> Dict[str, Any]:
    """
    Execute one full improvement cycle. Returns a dict with:
      - weakest_lane, todos, convergence_score, lane_scores
    """
    evidence = count_evidence_per_lane(conn)
    egcp = calc_egcp_scores(conn)

    weakest_lane, weakest_count = identify_weakest_lane(evidence)

    todos: List[ImprovementItem] = []

    # P1: placeholder gaps (highest priority — blocks filing)
    todos.extend(identify_placeholder_gaps(conn))

    # P2: missing authority chains
    todos.extend(identify_missing_authorities(conn))

    # P3: high-severity unresolved contradictions
    todos.extend(identify_unresolved_contradictions(conn))

    # P4: weak evidence for the weakest lane
    if weakest_count < 500:
        todos.append(ImprovementItem(
            lane=weakest_lane,
            category="evidence",
            priority=4,
            description=(
                f"Lane {weakest_lane} ({LANE_LABELS.get(weakest_lane, '?')}) has only "
                f"{weakest_count} evidence items — needs enrichment"
            ),
        ))

    # Sort by priority
    todos.sort(key=lambda t: t.priority)

    # Overall convergence score = mean of lane EGCP totals
    lane_totals = [egcp[l]["total"] for l in LANES]
    convergence_score = round(sum(lane_totals) / max(len(lane_totals), 1), 1)

    return {
        "weakest_lane": weakest_lane,
        "weakest_count": weakest_count,
        "todos": todos,
        "convergence_score": convergence_score,
        "lane_scores": egcp,
        "evidence": evidence,
    }


# ---------------------------------------------------------------------------
# 3. Emergence Detection
# ---------------------------------------------------------------------------

def detect_cross_lane_entities(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    """Find persons/speakers appearing in multiple lanes."""
    signals: List[Dict[str, Any]] = []
    if _table_exists(conn, "chimera_statements"):
        rows = conn.execute(
            "SELECT speaker, GROUP_CONCAT(DISTINCT topic) AS topics, "
            "       COUNT(*) AS stmt_count "
            "FROM chimera_statements "
            "WHERE speaker IS NOT NULL AND speaker != '' "
            "GROUP BY speaker "
            "HAVING COUNT(DISTINCT topic) >= 3 "
            "ORDER BY stmt_count DESC LIMIT 20"
        ).fetchall()
        for row in rows:
            novelty = min(10, max(1, row["stmt_count"] // 50))
            signals.append({
                "type": "CROSS_LANE_ENTITY",
                "entity": row["speaker"],
                "topics": row["topics"],
                "count": row["stmt_count"],
                "novelty": novelty,
            })
    return signals


def detect_authority_completion(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    """Find filings where all required authorities are present."""
    signals: List[Dict[str, Any]] = []
    if not _table_exists(conn, "filing_readiness"):
        return signals
    rows = conn.execute(
        "SELECT vehicle_name, lane, authority_count, readiness_score, status "
        "FROM filing_readiness "
        "WHERE authority_count > 0 AND readiness_score >= 80 "
        "ORDER BY readiness_score DESC"
    ).fetchall()
    for row in rows:
        novelty = 8 if row["status"] in ("complete", "final_review") else 5
        signals.append({
            "type": "AUTHORITY_COMPLETE",
            "vehicle": row["vehicle_name"],
            "lane": row["lane"],
            "authority_count": row["authority_count"],
            "readiness": row["readiness_score"],
            "novelty": novelty,
        })
    return signals


def detect_contradiction_cascades(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    """
    Find contradiction clusters where one speaker has many contradictions,
    suggesting cascade potential — proving one disproves many claims.
    """
    signals: List[Dict[str, Any]] = []
    if not (_table_exists(conn, "chimera_contradictions")
            and _table_exists(conn, "chimera_statements")):
        return signals
    # Speakers with the most contradictions
    rows = conn.execute(
        "SELECT cs.speaker, COUNT(DISTINCT cc.id) AS contra_count, "
        "       AVG(cc.severity) AS avg_severity "
        "FROM chimera_contradictions cc "
        "JOIN chimera_statements cs ON cs.id = cc.statement_id_a "
        "WHERE cs.speaker IS NOT NULL AND cs.speaker != '' "
        "GROUP BY cs.speaker "
        "HAVING COUNT(DISTINCT cc.id) >= 5 "
        "ORDER BY contra_count DESC LIMIT 10"
    ).fetchall()
    for row in rows:
        novelty = min(10, max(1, int(row["avg_severity"])))
        signals.append({
            "type": "CONTRADICTION_CASCADE",
            "speaker": row["speaker"],
            "contradiction_count": row["contra_count"],
            "avg_severity": round(row["avg_severity"], 2),
            "novelty": novelty,
        })
    return signals


def detect_existing_emergence(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    """Pull pre-computed emergence events from emergence_events table."""
    signals: List[Dict[str, Any]] = []
    if not _table_exists(conn, "emergence_events"):
        return signals
    for row in conn.execute(
        "SELECT signal_type, lanes_involved, novelty, description "
        "FROM emergence_events ORDER BY novelty DESC"
    ).fetchall():
        signals.append({
            "type": row["signal_type"],
            "lanes": row["lanes_involved"],
            "novelty": row["novelty"],
            "description": (row["description"] or "")[:120],
        })
    return signals


def run_emergence_detection(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    """Run all emergence detectors and return sorted by novelty desc."""
    all_signals: List[Dict[str, Any]] = []
    all_signals.extend(detect_cross_lane_entities(conn))
    all_signals.extend(detect_authority_completion(conn))
    all_signals.extend(detect_contradiction_cascades(conn))
    all_signals.extend(detect_existing_emergence(conn))
    all_signals.sort(key=lambda s: s.get("novelty", 0), reverse=True)
    return all_signals


# ---------------------------------------------------------------------------
# 4. Report Generation
# ---------------------------------------------------------------------------

def determine_status(score: float, blockers: int) -> str:
    if blockers > 0:
        return "NOT CONVERGED"
    if score >= 85:
        return "CONVERGED"
    if score >= 50:
        return "CONVERGING"
    return "NOT CONVERGED"


def determine_next_action(todos: List[ImprovementItem],
                          weakest_lane: str) -> str:
    """Pick the single most impactful next action."""
    if not todos:
        return "All lanes converged — review and file."
    top = todos[0]
    if top.category == "placeholder":
        return f"URGENT: Resolve placeholder text in {top.description.split('in ')[-1]}"
    if top.category == "authority":
        return f"Add authority chain: {top.description}"
    if top.category == "contradiction":
        return f"Build impeachment package for high-severity contradiction"
    if top.category == "evidence":
        return (
            f"Enrich evidence for Lane {weakest_lane} "
            f"({LANE_LABELS.get(weakest_lane, '?')})"
        )
    return top.description


def generate_dashboard(cycle_result: Dict[str, Any],
                       emergence: List[Dict[str, Any]],
                       cycle_number: int = 1) -> str:
    """Build the convergence dashboard string."""
    score = cycle_result["convergence_score"]
    todos = cycle_result["todos"]
    egcp = cycle_result["lane_scores"]
    evidence = cycle_result["evidence"]
    weakest = cycle_result["weakest_lane"]

    blocker_count = sum(1 for t in todos if t.priority == 1)
    high_novelty = [s for s in emergence if s.get("novelty", 0) >= 7]

    status = determine_status(score, blocker_count)
    next_action = determine_next_action(todos, weakest)

    lines: List[str] = []
    sep = "=" * 64
    lines.append(sep)
    lines.append(f"  OMEGA CONVERGENCE DASHBOARD  —  {datetime.now():%Y-%m-%d %H:%M:%S}")
    lines.append(sep)
    lines.append("")
    lines.append(f"  CONVERGENCE STATUS: {status}")
    lines.append(f"  Overall Score:      {score}/100")
    lines.append(f"  Cycles Run:         {cycle_number}")
    lines.append("")

    # Per-lane table
    lines.append("  Per-Lane Scores:")
    lines.append(f"  {'Lane':<8} {'Score':>6} {'Evid':>7} {'Auth':>6} {'Imp':>6} {'Pres':>6}   Label")
    lines.append(f"  {'─' * 60}")

    auth = count_authority_per_lane(
        _conn()  # Rule 18: use compliant helper instead of bare connect
    ) if False else {}  # avoid extra connection; compute from egcp
    for lane in LANES:
        ls = egcp[lane]
        ev_count = evidence.get(lane, 0)
        lines.append(
            f"  {lane:<8} {ls['total']:>5.1f} {ev_count:>7,} "
            f"{ls['grounds']:>5.1f} {ls['citations']:>5.1f} {ls['presentation']:>5.1f}"
            f"   {LANE_LABELS.get(lane, '')}"
        )

    lines.append("")

    # Emergence signals
    lines.append(f"  Emergence Signals:  {len(emergence)} total, "
                 f"{len(high_novelty)} high-novelty (≥7)")
    if high_novelty:
        for sig in high_novelty[:5]:
            desc = sig.get("description") or sig.get("entity") or sig.get("vehicle") or sig.get("speaker") or "—"
            lines.append(f"    ★ [{sig['type']}] novelty={sig['novelty']}  {str(desc)[:60]}")

    lines.append("")

    # Blockers
    lines.append(f"  Blockers:           {blocker_count} critical items")
    if blocker_count:
        for t in todos:
            if t.priority == 1:
                lines.append(f"    ✖ {t}")

    lines.append("")

    # TODO summary
    lines.append(f"  Improvement TODO:   {len(todos)} items")
    for t in todos[:8]:
        lines.append(f"    {'→'} {t}")
    if len(todos) > 8:
        lines.append(f"    ... and {len(todos) - 8} more")

    lines.append("")
    lines.append(f"  Next Action:        {next_action}")
    lines.append("")
    lines.append(sep)

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run_full_cycle(cycle_number: int = 1) -> str:
    """Run one complete convergence cycle and return the dashboard."""
    conn = _conn()
    try:
        cycle_result = run_improvement_cycle(conn)
        emergence = run_emergence_detection(conn)
        dashboard = generate_dashboard(cycle_result, emergence, cycle_number)
        return dashboard
    finally:
        conn.close()


def main() -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] Omega Convergence 9999 — starting cycle ...\n")

    if not os.path.exists(DB):
        print(f"ERROR: Database not found at {DB}")
        sys.exit(1)

    dashboard = run_full_cycle(cycle_number=1)
    print(dashboard)

    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] Cycle complete.")


if __name__ == "__main__":
    main()
