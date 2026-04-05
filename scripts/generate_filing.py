#!/usr/bin/env python3
"""THEMANBEARPIG Legal Brain Filing Generation Engine.

Generates court filing sections from the brain knowledge graph by tracing
evidence chains, extracting authorities, and producing IRAC-structured arguments.

Usage:
    python -I scripts/generate_filing.py --list
    python -I scripts/generate_filing.py --filing fi-F3 --facts
    python -I scripts/generate_filing.py --filing fi-F3 --argue
    python -I scripts/generate_filing.py --filing fi-F3 --brief
    python -I scripts/generate_filing.py --filing fi-F3 --exhibits
    python -I scripts/generate_filing.py --filing fi-F3 --gaps
    python -I scripts/generate_filing.py --actor ac-emily-watson --impeach
    python -I scripts/generate_filing.py --all
    python -I scripts/generate_filing.py --strongest
    python -I scripts/generate_filing.py --strongest --output brief.md
"""

import argparse
import json
import os
import re
import sqlite3
import sys
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path
from textwrap import dedent

# ── Constants ────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parent.parent
BRAIN_DB = REPO_ROOT / "mbp_brain.db"
LITIGATION_DB = REPO_ROOT / "litigation_context.db"
SEPARATION_ANCHOR = date(2025, 7, 29)

LANE_INFO = {
    "A": {
        "name": "Custody",
        "case_no": "2024-001507-DC",
        "court": "14th Circuit Court, Muskegon County",
        "judge": "Hon. Jenny L. McNeill",
        "jurisdiction": (
            "MCL 552.15 et seq. and MCR 3.201 et seq. (domestic relations)"
        ),
    },
    "B": {
        "name": "Housing",
        "case_no": "2025-002760-CZ",
        "court": "14th Circuit Court, Muskegon County",
        "judge": "Hon. Kenneth Hoopes",
        "jurisdiction": "MCL 600.605 (circuit court jurisdiction)",
    },
    "C": {
        "name": "Federal 1983",
        "case_no": "TBD",
        "court": "United States District Court, Western District of Michigan",
        "judge": "TBD",
        "jurisdiction": (
            "28 U.S.C. \u00a7 1331 (federal question), "
            "28 U.S.C. \u00a7 1343 (civil rights), and 42 U.S.C. \u00a7 1983"
        ),
    },
    "D": {
        "name": "PPO",
        "case_no": "2023-5907-PP",
        "court": "14th Circuit Court, Muskegon County",
        "judge": "Hon. Jenny L. McNeill",
        "jurisdiction": "MCL 600.2950 and MCR 3.701 et seq. (personal protection orders)",
    },
    "E": {
        "name": "Judicial Misconduct",
        "case_no": "MULTI",
        "court": "Michigan Supreme Court / Judicial Tenure Commission",
        "judge": "Various",
        "jurisdiction": (
            "Const 1963, art 6, \u00a7 4 and MCR 7.306 (superintending control)"
        ),
    },
    "F": {
        "name": "Appeal",
        "case_no": "COA 366810",
        "court": "Michigan Court of Appeals",
        "judge": "Panel TBD",
        "jurisdiction": "MCR 7.203 (appeal of right) and MCR 7.204 (claim of appeal)",
    },
}

MRE_AUTH_BASIS = {
    "court_order": "MRE 901(b)(7) \u2014 public record",
    "police_report": "MRE 803(8) \u2014 public records exception; MRE 901(b)(7)",
    "recording": (
        "MRE 901(b)(1) \u2014 witness with knowledge; "
        "MCL 750.539c (one-party consent); Sullivan v Gray, 117 Mich App 476 (1982)"
    ),
    "email": "MRE 901(b)(1) \u2014 testimony of witness with knowledge",
    "app_export": "MRE 901(b)(9) \u2014 system or process producing accurate result",
    "medical": "MRE 803(6) \u2014 business records exception",
    "financial": "MRE 803(6) \u2014 business records exception",
    "photograph": "MRE 901(b)(1) \u2014 testimony of witness with knowledge",
    "due_process": "MRE 901(b)(7) \u2014 public record",
    "witness": "MRE 901(b)(1) \u2014 testimony of witness with knowledge",
    "default": "MRE 901(b)(1) \u2014 testimony of witness with knowledge",
}

# Strings that must never appear in court-facing output
_BANNED_FILING_TERMS = [
    "LitigationOS", "MANBEARPIG", "THEMANBEARPIG", "EGCP", "SINGULARITY",
    "mbp_brain", "litigation_context.db", "evidence_quotes", "brain.db",
    "MEEK", "LOCUS score", "delta999", "nexus_fuse", "authority_chains_v2",
    "impeachment_matrix", "contradiction_map", "michigan_rules_extracted",
]


# ── Database Connections ─────────────────────────────────────────────────

def _connect(db_path: Path, text_factory=None) -> sqlite3.Connection:
    if not db_path.exists():
        sys.exit(f"ERROR: Database not found at {db_path}")
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    if text_factory:
        conn.text_factory = text_factory
    conn.execute("PRAGMA busy_timeout = 60000")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA cache_size = -32000")
    conn.execute("PRAGMA temp_store = MEMORY")
    return conn


def connect_brain() -> sqlite3.Connection:
    return _connect(BRAIN_DB)


def connect_litigation() -> sqlite3.Connection:
    return _connect(
        LITIGATION_DB,
        text_factory=lambda b: b.decode("utf-8", errors="replace"),
    )


# ── Utility Helpers ──────────────────────────────────────────────────────

def separation_days() -> int:
    return (date.today() - SEPARATION_ANCHOR).days


def _json_loads(text, default=None):
    if not text:
        return default if default is not None else []
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return default if default is not None else []


def _trunc(text: str, limit: int = 200) -> str:
    if not text:
        return ""
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 3] + "..."


def _clean(text: str) -> str:
    """Strip AI/DB references forbidden in court filings."""
    if not text:
        return ""
    result = text
    for term in _BANNED_FILING_TERMS:
        result = re.sub(re.escape(term), "[REDACTED]", result, flags=re.IGNORECASE)
    result = re.sub(r"C:\\Users\\[^\s,;)]+", "[file reference]", result)
    result = re.sub(r"00_SYSTEM[/\\]\S+", "[system reference]", result)
    return result


def _fmt_date(raw: str) -> str:
    if not raw:
        return "[date unknown]"
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%m/%d/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(raw.strip()[:10], fmt).strftime("%B %d, %Y")
        except (ValueError, TypeError):
            continue
    return raw.strip()[:10]


def _sort_key_date(raw: str) -> str:
    if not raw:
        return "9999-99-99"
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%m/%d/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(raw.strip()[:10], fmt).strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            continue
    return "9999-99-99"


def _cite(source_file: str = "", page=None) -> str:
    parts = []
    if source_file:
        parts.append(os.path.basename(source_file))
    if page:
        parts.append(f"p. {page}")
    return f"(Ex. {', '.join(parts)}.)" if parts else ""


def _placeholders(ids):
    return ",".join("?" for _ in ids)


# ── Graph Traversal ──────────────────────────────────────────────────────

def list_filing_ids(brain: sqlite3.Connection) -> list[dict]:
    """Return all filings with chain statistics, ordered by avg strength."""
    rows = brain.execute("""
        SELECT c.filing_id,
               n.label, n.description, n.lane, n.readiness,
               COUNT(c.id)          AS chain_count,
               AVG(c.strength_score) AS avg_strength,
               MAX(c.strength_score) AS max_strength
        FROM chains c
        LEFT JOIN nodes n ON n.id = c.filing_id
        GROUP BY c.filing_id
        ORDER BY avg_strength DESC
    """).fetchall()
    return [
        {
            "id": r["filing_id"],
            "label": r["label"] or r["filing_id"],
            "description": r["description"] or "",
            "lane": r["lane"] or "",
            "readiness": r["readiness"] or 0.0,
            "chain_count": r["chain_count"],
            "avg_strength": r["avg_strength"] or 0.0,
            "max_strength": r["max_strength"] or 0.0,
        }
        for r in rows
    ]


def get_chains(brain: sqlite3.Connection, filing_id: str) -> list[dict]:
    rows = brain.execute(
        """
        SELECT id, chain_path, chain_type, total_weight, length,
               lane, filing_id, evidence_ids, strength_score
        FROM chains WHERE filing_id = ?
        ORDER BY strength_score DESC
        """,
        (filing_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def _ids_from_chains(chains: list[dict]) -> dict[str, set]:
    """Parse chain_path + evidence_ids → dict keyed by id-prefix."""
    by_prefix: dict[str, set] = defaultdict(set)
    for ch in chains:
        for nid in _json_loads(ch.get("chain_path")):
            if isinstance(nid, str) and "-" in nid:
                by_prefix[nid.split("-")[0]].add(nid)
        for eid in _json_loads(ch.get("evidence_ids")):
            if isinstance(eid, str):
                pfx = eid.split("-")[0] if "-" in eid else "ev"
                by_prefix[pfx].add(eid)
    return dict(by_prefix)


def _nodes_by_ids(brain: sqlite3.Connection, ids: set) -> list[dict]:
    if not ids:
        return []
    rows = brain.execute(
        f"""
        SELECT id, node_type, layer, label, description,
               date_start, date_end, severity, confidence,
               readiness, source_table, source_id, lane
        FROM nodes WHERE id IN ({_placeholders(ids)})
        """,
        list(ids),
    ).fetchall()
    return [dict(r) for r in rows]


def _evidence_proving(brain: sqlite3.Connection, target_ids: set) -> list[dict]:
    """Evidence nodes connected via PROVES edges to the given targets."""
    if not target_ids:
        return []
    rows = brain.execute(
        f"""
        SELECT DISTINCT n.id, n.node_type, n.layer, n.label, n.description,
               n.date_start, n.source_table, n.source_id, n.lane,
               e.target_id AS proves_target, e.weight
        FROM edges e
        JOIN nodes n ON n.id = e.source_id
        WHERE e.edge_type = 'PROVES' AND e.target_id IN ({_placeholders(target_ids)})
        ORDER BY e.weight DESC
        """,
        list(target_ids),
    ).fetchall()
    return [dict(r) for r in rows]


def _edges_from(brain: sqlite3.Connection, node_id: str, edge_type: str) -> list[dict]:
    rows = brain.execute(
        """
        SELECT e.source_id, e.target_id, e.edge_type, e.weight,
               n.label  AS target_label,
               n.description AS target_desc,
               n.node_type   AS target_type,
               n.layer       AS target_layer
        FROM edges e
        JOIN nodes n ON n.id = e.target_id
        WHERE e.source_id = ? AND e.edge_type = ?
        ORDER BY e.weight DESC
        """,
        (node_id, edge_type),
    ).fetchall()
    return [dict(r) for r in rows]


def _contradictions_for_actor(brain: sqlite3.Connection, actor_id: str) -> list[dict]:
    """Contradiction nodes reachable from an actor through any path."""
    direct = brain.execute(
        """
        SELECT DISTINCT n.id, n.label, n.description, n.severity, n.node_type
        FROM edges e
        JOIN nodes n ON n.id = CASE
            WHEN e.source_id = ? THEN e.target_id
            ELSE e.source_id END
        WHERE e.edge_type = 'CONTRADICTS'
          AND (e.source_id = ? OR e.target_id = ?)
        ORDER BY n.severity DESC
        """,
        (actor_id, actor_id, actor_id),
    ).fetchall()

    ct_ids = {r["id"] for r in direct}

    indirect = brain.execute(
        """
        SELECT DISTINCT e2.source_id, e2.target_id
        FROM edges e1
        JOIN edges e2
          ON (e2.source_id = e1.source_id OR e2.target_id = e1.source_id)
        WHERE e1.target_id = ?
          AND e1.edge_type IN ('COMMITTED_BY', 'ASSIGNED_TO')
          AND e2.edge_type = 'CONTRADICTS'
        LIMIT 200
        """,
        (actor_id,),
    ).fetchall()
    for r in indirect:
        ct_ids.add(r["source_id"])
        ct_ids.add(r["target_id"])

    if not ct_ids:
        return [dict(r) for r in direct]

    rows = brain.execute(
        f"""
        SELECT id, label, description, severity, node_type
        FROM nodes
        WHERE id IN ({_placeholders(ct_ids)})
          AND node_type = 'Contradiction'
        ORDER BY severity DESC
        """,
        list(ct_ids),
    ).fetchall()
    return [dict(r) for r in rows] if rows else [dict(r) for r in direct]


# ── Litigation-Context Lookups ───────────────────────────────────────────

_SOURCE_TABLE_SQL = {
    "evidence_quotes": (
        "SELECT id, source_file, quote_text, page_number, "
        "category, lane, relevance_score "
        "FROM evidence_quotes WHERE id = ?"
    ),
    "timeline_events": (
        "SELECT id, event_date, event_description, actors, "
        "lane, category, severity "
        "FROM timeline_events WHERE id = ?"
    ),
    "impeachment_matrix": (
        "SELECT id, category, evidence_summary, source_file, "
        "quote_text, impeachment_value, cross_exam_question "
        "FROM impeachment_matrix WHERE id = ?"
    ),
    "judicial_violations": (
        "SELECT id, violation_type AS category, description AS quote_text, "
        "date_occurred AS event_date, mcr_rule, canon, "
        "source_file, source_quote, severity, lane "
        "FROM judicial_violations WHERE id = ?"
    ),
}


def _lookup_evidence(lit: sqlite3.Connection, source_table: str, source_id) -> dict:
    if not source_table or source_id is None:
        return {}
    sql = _SOURCE_TABLE_SQL.get(source_table)
    if not sql:
        return {}
    try:
        row = lit.execute(sql, (source_id,)).fetchone()
        return dict(row) if row else {}
    except sqlite3.OperationalError:
        return {}


def _lookup_rule(lit: sqlite3.Connection, label: str) -> dict:
    if not label:
        return {}
    ref = re.search(r"(MCR|MCL|MRE)\s*[\d.]+[a-z]?", label, re.IGNORECASE)
    if ref:
        row = lit.execute(
            "SELECT rule_number, rule_type, title, full_text "
            "FROM michigan_rules_extracted "
            "WHERE rule_number LIKE ? LIMIT 1",
            (f"%{ref.group()}%",),
        ).fetchone()
        if row:
            return dict(row)

    row = lit.execute(
        "SELECT rule_number, rule_type, title, full_text "
        "FROM michigan_rules_extracted "
        "WHERE title LIKE ? OR rule_number LIKE ? LIMIT 1",
        (f"%{label[:50]}%", f"%{label[:50]}%"),
    ).fetchone()
    return dict(row) if row else {}


def _lookup_authority(lit: sqlite3.Connection, citation: str, lane: str = "") -> list[dict]:
    if not citation:
        return []
    params: list = [f"%{citation[:60]}%", f"%{citation[:60]}%"]
    where = "WHERE (primary_citation LIKE ? OR supporting_citation LIKE ?)"
    if lane:
        where += " AND lane = ?"
        params.append(lane)
    rows = lit.execute(
        f"SELECT primary_citation, supporting_citation, relationship, lane "
        f"FROM authority_chains_v2 {where} LIMIT 20",
        params,
    ).fetchall()
    return [dict(r) for r in rows]


def _impeachment_rows(lit: sqlite3.Connection, category: str = "") -> list[dict]:
    if category:
        rows = lit.execute(
            "SELECT id, category, evidence_summary, source_file, quote_text, "
            "impeachment_value, cross_exam_question, event_date "
            "FROM impeachment_matrix WHERE category LIKE ? "
            "ORDER BY impeachment_value DESC LIMIT 30",
            (f"%{category}%",),
        ).fetchall()
    else:
        rows = lit.execute(
            "SELECT id, category, evidence_summary, source_file, quote_text, "
            "impeachment_value, cross_exam_question, event_date "
            "FROM impeachment_matrix ORDER BY impeachment_value DESC LIMIT 50",
        ).fetchall()
    return [dict(r) for r in rows]


def _contradiction_rows(lit: sqlite3.Connection, lane: str = "") -> list[dict]:
    order = (
        "ORDER BY CASE severity "
        "WHEN 'critical' THEN 0 WHEN 'high' THEN 1 "
        "WHEN 'medium' THEN 2 ELSE 3 END"
    )
    if lane:
        rows = lit.execute(
            "SELECT id, claim_id, source_a, source_b, contradiction_text, "
            f"severity, lane FROM contradiction_map WHERE lane = ? {order} LIMIT 30",
            (lane,),
        ).fetchall()
    else:
        rows = lit.execute(
            "SELECT id, claim_id, source_a, source_b, contradiction_text, "
            f"severity, lane FROM contradiction_map {order} LIMIT 50",
        ).fetchall()
    return [dict(r) for r in rows]


# ── Shared chain-to-evidence resolver ────────────────────────────────────

def _collect_evidence_nodes(
    brain: sqlite3.Connection,
    chains: list[dict],
) -> tuple[list[dict], dict[str, set]]:
    """Return (evidence_nodes, ids_by_prefix) for the given chains.

    Evidence is collected from multiple paths:
    1. Direct evidence_ids in chains
    2. PROVES edges from evidence → claim nodes
    3. Lane-matched evidence (top by relevance) when direct links are sparse
    4. Violation nodes themselves (they carry factual descriptions with dates)
    """
    ids_map = _ids_from_chains(chains)
    violation_ids = ids_map.get("vl", set())
    evidence_ids = ids_map.get("ev", set()) | ids_map.get("tl", set())

    # PROVES edges: ev→claim, not ev→violation, so widen to claim nodes too
    claim_ids = ids_map.get("claim", set())
    for ev in _evidence_proving(brain, violation_ids | claim_ids):
        evidence_ids.add(ev["id"])

    # When direct evidence is sparse, get lane-matched evidence
    if len(evidence_ids) < 10:
        lanes = {ch.get("lane", "") for ch in chains if ch.get("lane")}
        if lanes:
            lane_ev = brain.execute(
                f"""
                SELECT id FROM nodes
                WHERE id LIKE 'ev-%'
                  AND lane IN ({_placeholders(lanes)})
                  AND date_start IS NOT NULL
                ORDER BY date_start
                LIMIT 50
                """,
                list(lanes),
            ).fetchall()
            for r in lane_ev:
                evidence_ids.add(r["id"])

        # Timeline events from same lanes
        if lanes:
            lane_tl = brain.execute(
                f"""
                SELECT id FROM nodes
                WHERE id LIKE 'tl-%'
                  AND lane IN ({_placeholders(lanes)})
                  AND date_start IS NOT NULL
                ORDER BY date_start
                LIMIT 30
                """,
                list(lanes),
            ).fetchall()
            for r in lane_tl:
                evidence_ids.add(r["id"])

    ev_nodes = _nodes_by_ids(brain, evidence_ids)
    return ev_nodes, ids_map


def _collect_violation_facts(
    brain: sqlite3.Connection,
    lit: sqlite3.Connection,
    chains: list[dict],
) -> list[dict]:
    """Get violations as factual paragraphs with source details.

    Violations with source_table='judicial_violations' carry rich factual
    data (date_occurred, source_quote, source_file) that makes excellent
    Statement of Facts material.
    """
    ids_map = _ids_from_chains(chains)
    violation_ids = ids_map.get("vl", set())
    if not violation_ids:
        return []

    viol_nodes = _nodes_by_ids(brain, violation_ids)
    facts = []
    seen_descriptions: set[str] = set()

    for node in viol_nodes:
        detail = _lookup_evidence(lit, node.get("source_table"), node.get("source_id"))
        desc = (
            detail.get("source_quote")
            or detail.get("quote_text")
            or node.get("description")
            or node.get("label", "")
        )
        # Deduplicate by first 100 chars
        key = desc[:100]
        if key in seen_descriptions:
            continue
        seen_descriptions.add(key)

        date_raw = (
            detail.get("event_date")
            or detail.get("date_occurred")
            or node.get("date_start", "")
        )
        source = detail.get("source_file", "")
        mcr = detail.get("mcr_rule", "")
        canon = detail.get("canon", "")
        category = detail.get("category") or node.get("node_type", "")

        facts.append(
            {
                "sort": _sort_key_date(date_raw),
                "date": _fmt_date(date_raw),
                "text": _clean(_trunc(desc, 500)),
                "source": source,
                "page": detail.get("page_number"),
                "category": category,
                "mcr_rule": mcr,
                "canon": canon,
                "nid": node["id"],
                "lane": node.get("lane", ""),
                "severity": node.get("severity", 0) or 0,
            }
        )
    return facts


# ═══════════════════════════════════════════════════════════════════════
#  1. TRACE  —  Statement of Facts Generator
# ═══════════════════════════════════════════════════════════════════════

def generate_statement_of_facts(
    brain: sqlite3.Connection,
    lit: sqlite3.Connection,
    filing_id: str,
) -> str:
    chains = get_chains(brain, filing_id)
    if not chains:
        return f"## STATEMENT OF FACTS\n\nNo chains found for filing `{filing_id}`.\n"

    # Collect facts from TWO sources:
    # 1. Violation nodes (the factual spine — describe what happened)
    # 2. Evidence nodes (supporting quotes with dates and sources)
    viol_facts = _collect_violation_facts(brain, lit, chains)
    ev_nodes, _ = _collect_evidence_nodes(brain, chains)

    # Build evidence-based facts
    ev_facts: list[dict] = []
    seen_texts: set[str] = set()
    for node in ev_nodes:
        detail = _lookup_evidence(lit, node.get("source_table"), node.get("source_id"))
        date_raw = node.get("date_start") or detail.get("event_date", "")
        quote = (
            detail.get("quote_text")
            or detail.get("event_description")
            or node.get("description")
            or node.get("label", "")
        )
        key = quote[:100]
        if key in seen_texts:
            continue
        seen_texts.add(key)
        source = detail.get("source_file", "")
        ev_facts.append(
            {
                "sort": _sort_key_date(date_raw),
                "date": _fmt_date(date_raw),
                "text": _clean(_trunc(quote, 500)),
                "source": source,
                "page": detail.get("page_number"),
                "category": detail.get("category") or node.get("node_type", ""),
                "nid": node["id"],
                "lane": node.get("lane", ""),
                "severity": 0,
            }
        )

    # Merge and deduplicate: violations first (higher severity), then evidence
    all_facts = viol_facts + ev_facts
    all_facts.sort(key=lambda f: (f["sort"], -f.get("severity", 0)))

    # Limit to reasonable filing length
    if len(all_facts) > 60:
        # Keep top items by severity, then chronological
        all_facts.sort(key=lambda f: -f.get("severity", 0))
        all_facts = all_facts[:60]
        all_facts.sort(key=lambda f: f["sort"])

    lane = chains[0].get("lane", "")
    info = LANE_INFO.get(lane, {})
    sep = separation_days()

    lines = [
        "## STATEMENT OF FACTS\n",
        f"*Case: {info.get('case_no', filing_id)} "
        f"\u2014 {info.get('court', '')}*\n",
        f"As of the date of this filing, Plaintiff\u2019s minor child, L.D.W., "
        f"has been separated from Plaintiff for {sep} consecutive days "
        f"since July 29, 2025.\n",
    ]

    if len(all_facts) > 20:
        grouped: dict[str, list[dict]] = defaultdict(list)
        for f in all_facts:
            grouped[f["category"] or "General"].append(f)
        para = 1
        for cat, items in sorted(grouped.items()):
            lines.append(f"\n### {cat.replace('_', ' ').title()}\n")
            for f in items:
                cite = _cite(f["source"], f["page"])
                rule_note = ""
                if f.get("mcr_rule"):
                    rule_note = f" See {f['mcr_rule']}."
                if f.get("canon"):
                    rule_note += f" (Canon {f['canon']})"
                lines.append(
                    f"{para}. On {f['date']}, {f['text']}{rule_note} {cite}\n"
                )
                para += 1
    else:
        for i, f in enumerate(all_facts, 1):
            cite = _cite(f["source"], f["page"])
            rule_note = ""
            if f.get("mcr_rule"):
                rule_note = f" See {f['mcr_rule']}."
            if f.get("canon"):
                rule_note += f" (Canon {f['canon']})"
            lines.append(
                f"{i}. On {f['date']}, {f['text']}{rule_note} {cite}\n"
            )

    lines.append(
        f"\n*({len(all_facts)} factual paragraphs from {len(chains)} evidence chains, "
        f"{len(viol_facts)} violations, {len(ev_facts)} evidence items.)*\n"
    )
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════
#  2. ARGUE  —  IRAC Argument Generator
# ═══════════════════════════════════════════════════════════════════════

def generate_irac_argument(
    brain: sqlite3.Connection,
    lit: sqlite3.Connection,
    filing_id: str,
    violation_id: str = None,
) -> str:
    chains = get_chains(brain, filing_id)
    if not chains:
        return f"## ARGUMENT\n\nNo chains found for filing `{filing_id}`.\n"

    _, ids_map = _collect_evidence_nodes(brain, chains)
    violation_ids = ids_map.get("vl", set())
    if violation_id:
        violation_ids = {violation_id}

    violation_nodes = _nodes_by_ids(brain, violation_ids)
    if not violation_nodes:
        return f"## ARGUMENT\n\nNo violation nodes found for filing `{filing_id}`.\n"

    # Deduplicate by first 100 chars of description
    seen: set[str] = set()
    unique: list[dict] = []
    for v in violation_nodes:
        key = (v.get("description") or v.get("label", ""))[:100]
        if key not in seen:
            seen.add(key)
            unique.append(v)
    unique.sort(key=lambda v: v.get("severity", 0) or 0, reverse=True)

    if len(unique) > 15 and not violation_id:
        unique = unique[:15]

    remedy_ids = ids_map.get("rem", set())
    remedy_nodes = _nodes_by_ids(brain, remedy_ids)
    remedy_labels = {
        _clean(rn.get("label") or rn.get("description", ""))
        for rn in remedy_nodes
        if rn.get("label")
    }

    lane = chains[0].get("lane", "")
    lines = ["## ARGUMENT\n"]

    for idx, viol in enumerate(unique, 1):
        vid = viol["id"]
        desc = _clean(viol.get("description") or viol.get("label", ""))

        lines.append(f"### {idx}. {_trunc(desc, 120)}\n")
        lines.append(f"**ISSUE:** Whether {_trunc(desc, 300)}\n")

        # ── RULE ──
        gov_edges = _edges_from(brain, vid, "GOVERNED_BY")
        rule_parts: list[str] = []
        auth_targets: list[str] = []
        seen_rules: set[str] = set()
        for edge in gov_edges[:5]:
            tgt_label = edge.get("target_label", "")
            tgt_id = edge["target_id"]
            if tgt_id in seen_rules:
                continue
            seen_rules.add(tgt_id)
            auth_targets.append(tgt_id)
            rule_detail = _lookup_rule(lit, tgt_label)
            if rule_detail and rule_detail.get("full_text"):
                rule_num = rule_detail.get("rule_number", tgt_label)
                if rule_num in seen_rules:
                    continue
                seen_rules.add(rule_num)
                rule_parts.append(
                    f"- **{rule_num}** "
                    f"({rule_detail.get('title', '')}): "
                    f"{_trunc(rule_detail['full_text'], 300)}"
                )
            elif tgt_label:
                auth_chain = _lookup_authority(lit, tgt_label, lane)
                if auth_chain:
                    for ac in auth_chain[:3]:
                        rule_parts.append(
                            f"- {ac.get('primary_citation', '')} "
                            f"({ac.get('relationship', 'supports')} "
                            f"{ac.get('supporting_citation', '')})"
                        )
                else:
                    rule_parts.append(f"- {_clean(tgt_label)}")

        lines.append("**RULE:**\n")
        if rule_parts:
            lines.extend(rule_parts)
            lines.append("")
        else:
            lines.append("[Authority to be verified — see gap report]\n")

        # ── APPLICATION ──
        # Evidence doesn't link to violations via PROVES; use lane + detail
        viol_detail = _lookup_evidence(
            lit, viol.get("source_table"), viol.get("source_id")
        )
        lines.append("**APPLICATION:**\n")

        # First: violation's own source_quote is direct evidence
        own_quote = viol_detail.get("source_quote") or viol_detail.get("quote_text")
        if own_quote:
            viol_source = viol_detail.get("source_file", "")
            lines.append(
                f"- {_clean(_trunc(own_quote, 300))} "
                f"{_cite(viol_source, viol_detail.get('page_number'))}"
            )

        # Second: lane-matched evidence from brain graph
        viol_lane = viol.get("lane", lane)
        if viol_lane:
            lane_ev = brain.execute(
                """SELECT id, description, label, source_table, source_id,
                          date_start
                   FROM nodes
                   WHERE id LIKE 'ev-%' AND lane = ?
                     AND date_start IS NOT NULL
                   ORDER BY date_start DESC LIMIT 5""",
                (viol_lane,),
            ).fetchall()
            for ev in lane_ev:
                ev_detail = _lookup_evidence(
                    lit, ev["source_table"], ev["source_id"]
                )
                quote = (
                    ev_detail.get("quote_text")
                    or ev_detail.get("event_description")
                    or ev["description"]
                    or ""
                )
                source = ev_detail.get("source_file", "")
                page = ev_detail.get("page_number")
                if quote:
                    lines.append(
                        f"- {_clean(_trunc(quote, 300))} {_cite(source, page)}"
                    )

        if not own_quote and not viol_lane:
            lines.append("[Evidence to be linked \u2014 see gap report]\n")
        else:
            lines.append("")

        # ── CONCLUSION ──
        local_remedies: set[str] = set()
        for tgt_id in auth_targets:
            for ae in _edges_from(brain, tgt_id, "AUTHORIZES"):
                local_remedies.add(_clean(ae.get("target_label", "")))
        all_remedies = local_remedies | remedy_labels
        if all_remedies:
            joined = ", ".join(r for r in all_remedies if r)
            lines.append(f"**CONCLUSION:** This Court should grant {joined}.\n")
        else:
            lines.append("**CONCLUSION:** This Court should grant the requested relief.\n")

        lines.append("---\n")

    lines.append(
        f"\n*({len(unique)} IRAC argument sections from {len(chains)} chains.)*\n"
    )
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════
#  3. IMPEACH  —  Cross-Examination Generator
# ═══════════════════════════════════════════════════════════════════════

def generate_cross_exam(
    brain: sqlite3.Connection,
    lit: sqlite3.Connection,
    actor_id: str,
) -> str:
    actor_nodes = _nodes_by_ids(brain, {actor_id})
    actor_label = _clean(actor_nodes[0]["label"]) if actor_nodes else actor_id

    ct_nodes = _contradictions_for_actor(brain, actor_id)
    impeachment = _impeachment_rows(lit)
    contradictions = _contradiction_rows(lit)

    lines = [
        f"## CROSS-EXAMINATION OUTLINE: {actor_label}\n",
        f"*Prepared for Plaintiff, appearing pro se*\n",
        f"*Target witness: {actor_label}*\n",
    ]

    qnum = 1

    # I. Graph contradictions
    if ct_nodes:
        lines.append("### I. Contradictions (Graph Analysis)\n")
        for ct in ct_nodes[:20]:
            desc = _clean(ct.get("description") or ct.get("label", ""))
            sev = ct.get("severity", 0)
            lines.append(f"**Contradiction {qnum}** (severity: {sev})\n")
            lines.append(f'  **COMMIT:** "You previously stated that {_trunc(desc, 150)}, correct?"\n')
            lines.append(f'  **PIN:** "And that was your statement under oath?"\n')
            lines.append(f'  **CONFRONT:** "But the record shows otherwise, doesn\'t it?"\n')
            lines.append(
                f'  **EXHIBIT:** "I direct your attention to this exhibit '
                f'showing {_trunc(desc, 100)}."\n'
            )
            lines.append("")
            qnum += 1

    # II. Impeachment matrix
    if impeachment:
        lines.append("### II. Impeachment Material\n")
        for imp in impeachment[:20]:
            summary = _clean(imp.get("evidence_summary", ""))
            cross_q = _clean(imp.get("cross_exam_question", ""))
            source = (
                os.path.basename(imp["source_file"])
                if imp.get("source_file")
                else ""
            )
            cat = imp.get("category", "")
            val = imp.get("impeachment_value", 0)

            lines.append(f"**Item {qnum}** [{cat}] (value: {val}/5)\n")
            if cross_q:
                lines.append(f"  **Q:** {cross_q}\n")
            else:
                lines.append(f'  **COMMIT:** "{_trunc(summary, 200)}, correct?"\n')
                lines.append(f'  **CONFRONT:** "But the evidence shows otherwise, doesn\'t it?"\n')
            if source:
                lines.append(f"  **EXHIBIT:** {source}\n")
            lines.append("")
            qnum += 1

    # III. Contradiction map
    if contradictions:
        lines.append("### III. Documented Contradictions\n")
        for ct in contradictions[:15]:
            text = _clean(ct.get("contradiction_text", ""))
            sev = ct.get("severity", "unknown")
            src_a = ct.get("source_a", "")
            src_b = ct.get("source_b", "")
            lines.append(f"**Contradiction {qnum}** (severity: {sev})\n")
            lines.append(f"  {_trunc(text, 300)}\n")
            if src_a:
                lines.append(f"  Source A: {_clean(_trunc(src_a, 100))}\n")
            if src_b:
                lines.append(f"  Source B: {_clean(_trunc(src_b, 100))}\n")
            lines.append("")
            qnum += 1

    total = qnum - 1
    if total == 0:
        lines.append(f"\nNo contradiction or impeachment material found for `{actor_id}`.\n")
        lines.append("Use `--list` to see available actor IDs.\n")
    else:
        lines.append(f"\n*({total} cross-examination items generated.)*\n")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════
#  4. EXHIBIT  —  Exhibit List Generator
# ═══════════════════════════════════════════════════════════════════════

def generate_exhibit_list(
    brain: sqlite3.Connection,
    lit: sqlite3.Connection,
    filing_id: str,
) -> str:
    chains = get_chains(brain, filing_id)
    if not chains:
        return f"## EXHIBIT INDEX\n\nNo chains found for filing `{filing_id}`.\n"

    ev_nodes, _ = _collect_evidence_nodes(brain, chains)
    ev_nodes.sort(key=lambda n: _sort_key_date(n.get("date_start")))

    lane = chains[0].get("lane", "") or "X"
    info = LANE_INFO.get(lane, {})

    letters = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    extended = letters + [f"A{c}" for c in letters] + [f"B{c}" for c in letters]

    lines = [
        "## EXHIBIT INDEX\n",
        f"*Filing: {filing_id} \u2014 {info.get('name', '')} "
        f"(Case {info.get('case_no', '')})*\n",
        "| Ex. | Bates No. | Description | Source | Authentication |",
        "|-----|-----------|-------------|--------|----------------|",
    ]

    for idx, node in enumerate(ev_nodes[:78]):
        ex_label = extended[idx] if idx < len(extended) else str(idx + 1)
        bates = f"PIGORS-{lane}-{idx + 1:06d}"

        detail = _lookup_evidence(lit, node.get("source_table"), node.get("source_id"))
        src_file = detail.get("source_file", "")
        src_base = os.path.basename(src_file) if src_file else _trunc(node.get("label", ""), 40)
        desc = _clean(
            _trunc(
                detail.get("quote_text")
                or detail.get("event_description")
                or node.get("description")
                or node.get("label", ""),
                80,
            )
        )
        cat = detail.get("category") or node.get("node_type", "")
        auth = MRE_AUTH_BASIS.get(cat, MRE_AUTH_BASIS["default"])

        lines.append(
            f"| {ex_label} | {bates} | {desc} | {_trunc(src_base, 40)} | {auth} |"
        )

    lines.append(
        f"\n*({len(ev_nodes)} exhibits cataloged from {len(chains)} evidence chains.)*\n"
    )
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════
#  5. BRIEF  —  Complete Brief Generator
# ═══════════════════════════════════════════════════════════════════════

def generate_brief(
    brain: sqlite3.Connection,
    lit: sqlite3.Connection,
    filing_id: str,
) -> str:
    filing_nodes = _nodes_by_ids(brain, {filing_id})
    filing = filing_nodes[0] if filing_nodes else {}
    chains = get_chains(brain, filing_id)
    lane = (chains[0].get("lane", "") if chains else filing.get("lane", "")) or ""
    info = LANE_INFO.get(lane, {})
    sep = separation_days()

    lines = [
        f"# {'=' * 60}",
        f"# BRIEF IN SUPPORT",
        f"# Filing: {filing_id} \u2014 {_clean(filing.get('label', filing_id))}",
        f"# Lane {lane}: {info.get('name', '')}",
        f"# Case: {info.get('case_no', '')}",
        f"# Court: {info.get('court', '')}",
        f"# Generated: {date.today().strftime('%B %d, %Y')}",
        f"# {'=' * 60}\n",
    ]

    # I. JURISDICTIONAL STATEMENT
    lines.append("## I. JURISDICTIONAL STATEMENT\n")
    lines.append(
        f"This Court has jurisdiction over this matter pursuant to "
        f"{info.get('jurisdiction', 'applicable Michigan statutes and court rules')}.\n"
    )

    # II. QUESTIONS PRESENTED
    _, ids_map = _collect_evidence_nodes(brain, chains)
    violation_ids = ids_map.get("vl", set())
    violation_nodes = _nodes_by_ids(brain, violation_ids)

    seen: set[str] = set()
    unique_viols: list[dict] = []
    for v in violation_nodes:
        key = (v.get("description") or v.get("label", ""))[:80]
        if key not in seen:
            seen.add(key)
            unique_viols.append(v)
    unique_viols.sort(key=lambda v: v.get("severity", 0) or 0, reverse=True)
    if len(unique_viols) > 10:
        unique_viols = unique_viols[:10]

    lines.append("## II. STATEMENT OF QUESTIONS PRESENTED\n")
    for i, v in enumerate(unique_viols, 1):
        desc = _clean(v.get("description") or v.get("label", ""))
        lines.append(f"{i}. Whether {_trunc(desc, 200)}\n")
        lines.append("   *Plaintiff answers: Yes.*\n")
    lines.append("")

    # III. STATEMENT OF FACTS
    lines.append(generate_statement_of_facts(brain, lit, filing_id))
    lines.append("")

    # IV. ARGUMENT
    lines.append(generate_irac_argument(brain, lit, filing_id))
    lines.append("")

    # V. RELIEF REQUESTED
    remedy_ids = ids_map.get("rem", set())
    remedy_nodes = _nodes_by_ids(brain, remedy_ids)

    lines.append("## V. RELIEF REQUESTED\n")
    lines.append(
        "WHEREFORE, Plaintiff, appearing pro se, respectfully requests "
        "that this Honorable Court:\n"
    )
    if remedy_nodes:
        for i, rem in enumerate(remedy_nodes, 1):
            label = _clean(rem.get("label") or rem.get("description", ""))
            lines.append(f"{i}. Grant {label};\n")
        lines.append(
            f"{len(remedy_nodes) + 1}. Grant such other and further relief "
            f"as this Court deems just and equitable.\n"
        )
    else:
        lines.append("1. Grant the relief described herein;\n")
        lines.append(
            "2. Grant such other and further relief "
            "as this Court deems just and equitable.\n"
        )

    lines.append("\nRespectfully submitted,\n")
    lines.append(f"\n{'_' * 40}")
    lines.append("Andrew James Pigors")
    lines.append("Plaintiff, appearing pro se")
    lines.append("1977 Whitehall Rd, Lot 17")
    lines.append("North Muskegon, MI 49445")
    lines.append("(231) 903-5690")
    lines.append("andrewjpigors@gmail.com")
    lines.append(f"\nDated: {date.today().strftime('%B %d, %Y')}\n")

    # VI. EXHIBIT INDEX
    lines.append(generate_exhibit_list(brain, lit, filing_id))

    # Dev footer
    avg_s = (
        sum(c.get("strength_score", 0) or 0 for c in chains) / len(chains)
        if chains
        else 0
    )
    lines.append(f"\n---\n*[Development reference \u2014 remove before filing]*")
    lines.append(
        f"*Chains: {len(chains)} | Violations: {len(unique_viols)} | "
        f"Avg strength: {avg_s:.4f} | Separation: {sep} days*\n"
    )
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════
#  6. GAP REPORT  —  What's Missing
# ═══════════════════════════════════════════════════════════════════════

def generate_gap_report(brain: sqlite3.Connection, filing_id: str = None) -> str:
    if filing_id:
        chains = get_chains(brain, filing_id)
        node_ids_map = _ids_from_chains(chains)
        viol_ids = node_ids_map.get("vl", set())
        all_chain_ids = set()
        for prefix_ids in node_ids_map.values():
            all_chain_ids.update(prefix_ids)
        all_chain_ids.add(filing_id)

        if all_chain_ids:
            gaps = brain.execute(
                f"""
                SELECT gap_type, node_id, description, priority,
                       acquisition_task, resolved
                FROM gaps
                WHERE resolved = 0 AND node_id IN ({_placeholders(all_chain_ids)})
                ORDER BY CASE priority
                    WHEN 'CRITICAL' THEN 0 WHEN 'HIGH' THEN 1
                    WHEN 'MEDIUM' THEN 2 ELSE 3 END
                """,
                list(all_chain_ids),
            ).fetchall()
        else:
            gaps = []
        all_gaps = [dict(g) for g in gaps]
    else:
        rows = brain.execute(
            """
            SELECT gap_type, node_id, description, priority,
                   acquisition_task, resolved
            FROM gaps WHERE resolved = 0
            ORDER BY CASE priority
                WHEN 'CRITICAL' THEN 0 WHEN 'HIGH' THEN 1
                WHEN 'MEDIUM' THEN 2 ELSE 3 END
            """,
        ).fetchall()
        all_gaps = [dict(r) for r in rows]

    lines = [
        "## GAP ANALYSIS REPORT\n",
        f"*Filing: {filing_id or 'ALL'}*\n",
    ]

    if not all_gaps:
        lines.append("No unresolved gaps found.\n")
        return "\n".join(lines)

    by_priority: dict[str, list[dict]] = defaultdict(list)
    for g in all_gaps:
        by_priority[g.get("priority", "MEDIUM")].append(g)

    for priority in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
        bucket = by_priority.get(priority, [])
        if not bucket:
            continue
        lines.append(f"### {priority} Priority ({len(bucket)} gaps)\n")
        for g in bucket[:30]:
            desc = _trunc(g.get("description", ""), 200)
            node_id = g.get("node_id", "")
            gap_type = g.get("gap_type", "")
            task = g.get("acquisition_task", "")
            lines.append(f"- **[{gap_type}]** `{node_id}`: {desc}")
            if task:
                lines.append(f"  - *Action:* {_trunc(task, 150)}")
            lines.append("")

    lines.append(f"\n*({len(all_gaps)} unresolved gaps total.)*\n")
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════
#  Summaries and List Commands
# ═══════════════════════════════════════════════════════════════════════

def generate_all_summary(brain: sqlite3.Connection, lit: sqlite3.Connection) -> str:
    filings = list_filing_ids(brain)
    sep = separation_days()

    lines = [
        "# THEMANBEARPIG Legal Brain \u2014 Filing Summary\n",
        f"*Generated: {date.today().strftime('%B %d, %Y')} | "
        f"Separation: {sep} days since July 29, 2025*\n",
        "| Filing ID | Label | Lane | Chains | Avg Str | Max Str | Readiness |",
        "|-----------|-------|------|--------|---------|---------|-----------|",
    ]

    for f in filings:
        lines.append(
            f"| `{f['id']}` "
            f"| {_trunc(_clean(f['label']), 50)} "
            f"| {f['lane']} "
            f"| {f['chain_count']} "
            f"| {f['avg_strength']:.4f} "
            f"| {f['max_strength']:.4f} "
            f"| {f['readiness']:.0%} |"
        )

    total_chains = sum(f["chain_count"] for f in filings)
    strongest = filings[0] if filings else None
    gap_count = brain.execute(
        "SELECT COUNT(*) FROM gaps WHERE resolved = 0"
    ).fetchone()[0]

    lines.append(f"\n**Total filings:** {len(filings)}")
    lines.append(f"**Total chains:** {total_chains}")
    if strongest:
        lines.append(
            f"**Strongest filing:** `{strongest['id']}` "
            f"({strongest['avg_strength']:.4f} avg strength)"
        )
    lines.append(f"**Unresolved gaps:** {gap_count}\n")
    return "\n".join(lines)


def generate_strongest_brief(brain: sqlite3.Connection, lit: sqlite3.Connection) -> str:
    filings = list_filing_ids(brain)
    if not filings:
        return "No filings found in the brain graph.\n"
    best = filings[0]
    header = (
        f"# Strongest filing: `{best['id']}`\n"
        f"# Avg strength: {best['avg_strength']:.4f} | "
        f"Chains: {best['chain_count']} | Lane: {best['lane']}\n\n"
    )
    return header + generate_brief(brain, lit, best["id"])


def format_filing_list(brain: sqlite3.Connection) -> str:
    filings = list_filing_ids(brain)
    lines = ["# Available Filing IDs\n"]
    for f in filings:
        lines.append(
            f"  {f['id']:20s}  {_trunc(_clean(f['label']), 55):55s}  "
            f"Lane {f['lane']:2s}  chains={f['chain_count']:3d}  "
            f"strength={f['avg_strength']:.4f}"
        )
    lines.append(f"\n  {len(filings)} filings total.\n")

    actors = brain.execute(
        "SELECT id, label FROM nodes WHERE node_type = 'Person' ORDER BY label"
    ).fetchall()
    if actors:
        lines.append("# Available Actor IDs (for --impeach)\n")
        for a in actors:
            lines.append(f"  {a['id']:30s}  {a['label']}")
        lines.append(f"\n  {len(actors)} actors total.")
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════
#  CLI Entry Point
# ═══════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="THEMANBEARPIG Legal Brain \u2014 Filing Generation Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=dedent("""\
        examples:
          python -I scripts/generate_filing.py --list
          python -I scripts/generate_filing.py --filing fi-F3 --facts
          python -I scripts/generate_filing.py --filing fi-F3 --argue
          python -I scripts/generate_filing.py --filing fi-F3 --brief
          python -I scripts/generate_filing.py --filing fi-F3 --exhibits
          python -I scripts/generate_filing.py --filing fi-F3 --gaps
          python -I scripts/generate_filing.py --actor ac-emily-watson --impeach
          python -I scripts/generate_filing.py --all
          python -I scripts/generate_filing.py --strongest
          python -I scripts/generate_filing.py --strongest --output brief.md
        """),
    )
    parser.add_argument("--filing", help="Filing node ID (e.g. fi-F3)")
    parser.add_argument("--actor", help="Actor node ID for cross-exam")
    parser.add_argument("--violation", help="Single violation ID for --argue")
    parser.add_argument("--facts", action="store_true", help="Generate Statement of Facts")
    parser.add_argument("--argue", action="store_true", help="Generate IRAC arguments")
    parser.add_argument("--brief", action="store_true", help="Generate complete brief")
    parser.add_argument("--exhibits", action="store_true", help="Generate exhibit index")
    parser.add_argument("--impeach", action="store_true", help="Cross-examination outline")
    parser.add_argument("--gaps", action="store_true", help="Gap analysis report")
    parser.add_argument("--all", action="store_true", help="Summary of all filings")
    parser.add_argument("--strongest", action="store_true", help="Full brief for strongest")
    parser.add_argument("--list", action="store_true", help="List filing and actor IDs")
    parser.add_argument("--output", help="Write output to file instead of stdout")

    args = parser.parse_args()

    actions = [
        args.facts, args.argue, args.brief, args.exhibits,
        args.impeach, args.gaps, args.all, args.strongest, args.list,
    ]
    if not any(actions):
        parser.print_help()
        sys.exit(1)

    if args.impeach and not args.actor:
        print("ERROR: --impeach requires --actor <actor_id>", file=sys.stderr)
        sys.exit(1)

    needs_filing = args.facts or args.argue or args.brief or args.exhibits
    if needs_filing and not args.filing:
        print(
            "ERROR: --facts/--argue/--brief/--exhibits require --filing <id>",
            file=sys.stderr,
        )
        sys.exit(1)

    brain = connect_brain()
    lit = connect_litigation()

    try:
        parts: list[str] = []

        if args.list:
            parts.append(format_filing_list(brain))

        if args.all:
            parts.append(generate_all_summary(brain, lit))
            if args.filing:
                parts.append(generate_brief(brain, lit, args.filing))
                parts.append(generate_gap_report(brain, args.filing))

        if args.strongest:
            parts.append(generate_strongest_brief(brain, lit))

        if args.facts:
            parts.append(generate_statement_of_facts(brain, lit, args.filing))

        if args.argue:
            parts.append(
                generate_irac_argument(brain, lit, args.filing, args.violation)
            )

        if args.exhibits:
            parts.append(generate_exhibit_list(brain, lit, args.filing))

        if args.brief:
            parts.append(generate_brief(brain, lit, args.filing))

        if args.impeach:
            parts.append(generate_cross_exam(brain, lit, args.actor))

        if args.gaps:
            parts.append(generate_gap_report(brain, args.filing))

        result = "\n\n".join(parts)

        if args.output:
            out_path = Path(args.output)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(result, encoding="utf-8")
            print(
                f"Written to {out_path} ({len(result):,} bytes)",
                file=sys.stderr,
            )
        else:
            sys.stdout.buffer.write(result.encode("utf-8", errors="replace"))
            sys.stdout.buffer.write(b"\n")

    finally:
        brain.close()
        lit.close()


if __name__ == "__main__":
    main()
