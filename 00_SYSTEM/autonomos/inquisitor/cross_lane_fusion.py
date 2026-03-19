"""
DELTA99 Ω∞ — Cross-Lane Intelligence Fusion
=============================================
Fuses intelligence across all 6 case lanes (A-F) to find cross-cutting patterns.
Evidence in Lane A (custody) that strengthens Lane E (misconduct), Lane D (PPO)
evidence that feeds Lane F (appellate), etc. Bridges the lane isolation boundary
for strategic advantage while maintaining provenance.

Feeds: d99-auto-impeach, d99-nuclear-assembler
"""
import sys
import sqlite3
import json
import time
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from collections import defaultdict

_shared = Path(__file__).parent.parent / "shared"
if str(_shared) not in sys.path:
    sys.path.insert(0, str(_shared))

from autonomos_config import CENTRAL_DB

FUSION_DB = Path(__file__).parent / "cross_lane_fusion.db"

# ── Lane Definitions ───────────────────────────────────────────────
LANES = {
    "A": {"name": "Custody", "case": "2024-001507-DC",
           "keywords": ["custody", "parenting time", "best interest", "722.23",
                        "child", "visitation", "placement", "lincoln"]},
    "B": {"name": "Housing", "case": "2025-002760-CZ",
           "keywords": ["housing", "shady oaks", "lease", "eviction", "MCL 554",
                        "habitability", "mold", "rent"]},
    "D": {"name": "PPO", "case": "2023-5907-PP",
           "keywords": ["ppo", "protection order", "personal protection",
                        "MCL 600.2950", "stalking", "harassment"]},
    "E": {"name": "Misconduct", "case": "2024-001507-DC",
           "keywords": ["misconduct", "judicial", "JTC", "canon", "bias",
                        "ex parte", "recusal", "disqualif", "McNeill"]},
    "F": {"name": "Appellate", "case": "COA 366810",
           "keywords": ["appeal", "appellate", "COA", "MSC", "plain error",
                        "Carines", "MCR 7.212", "brief"]},
    "C": {"name": "Convergence", "case": "multi-lane",
           "keywords": ["convergence", "cross-lane", "multi-case"]},
}

# ── Cross-Lane Bridge Definitions ──────────────────────────────────
BRIDGE_RULES = [
    {"from": "A", "to": "E", "trigger": "ex parte order affecting custody",
     "description": "Custody orders entered ex parte → judicial misconduct evidence"},
    {"from": "A", "to": "F", "trigger": "best interest factor violation",
     "description": "Trial court errors in BIF analysis → appellate issues"},
    {"from": "D", "to": "E", "trigger": "PPO weaponization pattern",
     "description": "PPO used to restrict parenting time → misconduct pattern"},
    {"from": "D", "to": "A", "trigger": "PPO affecting custody",
     "description": "PPO restrictions feed into custody modification arguments"},
    {"from": "E", "to": "F", "trigger": "judicial misconduct → appeal",
     "description": "Documented misconduct strengthens appellate arguments"},
    {"from": "A", "to": "D", "trigger": "custody evidence shows false allegations",
     "description": "False allegations in custody → PPO defense evidence"},
    {"from": "B", "to": "A", "trigger": "housing instability",
     "description": "Housing issues affect custody stability argument"},
]


def _init_db() -> sqlite3.Connection:
    FUSION_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(FUSION_DB), timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS cross_lane_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_lane TEXT NOT NULL,
            to_lane TEXT NOT NULL,
            bridge_rule TEXT DEFAULT '',
            evidence_id TEXT DEFAULT '',
            evidence_text TEXT DEFAULT '',
            evidence_source TEXT DEFAULT '',
            relevance_score REAL DEFAULT 0.0,
            detected_at TEXT DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_cll_from ON cross_lane_links(from_lane);
        CREATE INDEX IF NOT EXISTS idx_cll_to ON cross_lane_links(to_lane);

        CREATE TABLE IF NOT EXISTS fusion_insights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            insight_type TEXT NOT NULL,
            lanes_involved TEXT NOT NULL,
            description TEXT DEFAULT '',
            evidence_count INTEGER DEFAULT 0,
            strategic_value TEXT DEFAULT 'MEDIUM',
            filing_impact TEXT DEFAULT '',
            detected_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS scan_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            evidence_scanned INTEGER DEFAULT 0,
            cross_links_found INTEGER DEFAULT 0,
            insights_generated INTEGER DEFAULT 0,
            duration_s REAL DEFAULT 0.0,
            run_at TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.commit()
    return conn


def _classify_lane(text: str) -> list[str]:
    """Identify which lanes a piece of evidence is relevant to."""
    text_lower = text.lower()
    relevant_lanes = []
    for lane_id, info in LANES.items():
        score = sum(1 for kw in info["keywords"] if kw.lower() in text_lower)
        if score >= 2:  # At least 2 keyword matches
            relevant_lanes.append(lane_id)
    return relevant_lanes


def _find_cross_lane_evidence(central: sqlite3.Connection) -> list[dict]:
    """Find evidence that bridges multiple lanes."""
    links = []

    # Scan evidence_quotes for multi-lane relevance
    try:
        rows = central.execute("""
            SELECT rowid, quote_text, source_file FROM evidence_quotes
            LIMIT 20000
        """).fetchall()
    except sqlite3.Error:
        rows = []

    for row in rows:
        text = str(row[1] or "")
        if len(text) < 30:
            continue

        lanes = _classify_lane(text)
        if len(lanes) >= 2:
            # This evidence bridges multiple lanes
            for i, lane_from in enumerate(lanes):
                for lane_to in lanes[i+1:]:
                    # Find matching bridge rule
                    rule = ""
                    for br in BRIDGE_RULES:
                        if (br["from"] == lane_from and br["to"] == lane_to) or \
                           (br["from"] == lane_to and br["to"] == lane_from):
                            rule = br["description"]
                            break

                    links.append({
                        "from_lane": lane_from,
                        "to_lane": lane_to,
                        "bridge_rule": rule,
                        "evidence_id": str(row[0]),
                        "evidence_text": text[:300],
                        "evidence_source": str(row[2] or ""),
                        "relevance_score": min(len(lanes) * 0.3, 1.0),
                    })

    # Scan judicial_violations for A→E and E→F bridges
    try:
        rows = central.execute("""
            SELECT rowid, violation_type, source_text
            FROM judicial_violations LIMIT 2000
        """).fetchall()
        for row in rows:
            text = str(row[2] or "")
            # Judicial violations always relevant to Lane E
            other_lanes = _classify_lane(text)
            for other in other_lanes:
                if other != "E":
                    links.append({
                        "from_lane": other,
                        "to_lane": "E",
                        "bridge_rule": f"Judicial violation related to {LANES.get(other, {}).get('name', other)}",
                        "evidence_id": f"jv_{row[0]}",
                        "evidence_text": text[:300],
                        "evidence_source": "judicial_violations",
                        "relevance_score": 0.8,
                    })
    except sqlite3.Error:
        pass

    return links


def _generate_insights(links: list[dict]) -> list[dict]:
    """Generate strategic insights from cross-lane patterns."""
    insights = []

    # Group by lane pair
    pair_counts = defaultdict(int)
    for link in links:
        key = f"{link['from_lane']}→{link['to_lane']}"
        pair_counts[key] += 1

    for pair, count in sorted(pair_counts.items(), key=lambda x: -x[1]):
        from_lane, to_lane = pair.split("→")
        from_name = LANES.get(from_lane, {}).get("name", from_lane)
        to_name = LANES.get(to_lane, {}).get("name", to_lane)

        value = "HIGH" if count > 20 else "MEDIUM" if count > 5 else "LOW"

        insights.append({
            "type": "CROSS_LANE_DENSITY",
            "lanes": pair,
            "description": f"{count} evidence items bridge {from_name} (Lane {from_lane}) → {to_name} (Lane {to_lane})",
            "count": count,
            "value": value,
            "filing_impact": f"Strengthen Lane {to_lane} filings with Lane {from_lane} evidence",
        })

    # Identify convergence patterns (evidence touching 3+ lanes)
    evidence_lane_count = defaultdict(set)
    for link in links:
        evidence_lane_count[link["evidence_id"]].add(link["from_lane"])
        evidence_lane_count[link["evidence_id"]].add(link["to_lane"])

    convergence_items = {eid: lanes for eid, lanes in evidence_lane_count.items()
                         if len(lanes) >= 3}
    if convergence_items:
        insights.append({
            "type": "CONVERGENCE_EVIDENCE",
            "lanes": "multiple",
            "description": f"{len(convergence_items)} evidence items touch 3+ lanes — high strategic value",
            "count": len(convergence_items),
            "value": "CRITICAL",
            "filing_impact": "Use as centerpiece evidence in MSC superintending control filing",
        })

    return insights


def run_full_fusion() -> dict:
    """Execute complete cross-lane intelligence fusion."""
    start = time.time()
    fdb = _init_db()

    central = sqlite3.connect(str(CENTRAL_DB), timeout=30)
    central.execute("PRAGMA busy_timeout=120000")

    links = _find_cross_lane_evidence(central)
    central.close()

    insights = _generate_insights(links)

    # Persist links
    for link in links:
        fdb.execute("""
            INSERT INTO cross_lane_links
            (from_lane, to_lane, bridge_rule, evidence_id, evidence_text,
             evidence_source, relevance_score)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (link["from_lane"], link["to_lane"], link["bridge_rule"],
              link["evidence_id"], link["evidence_text"],
              link["evidence_source"], link["relevance_score"]))

    # Persist insights
    for ins in insights:
        fdb.execute("""
            INSERT INTO fusion_insights
            (insight_type, lanes_involved, description, evidence_count,
             strategic_value, filing_impact)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (ins["type"], ins["lanes"], ins["description"],
              ins["count"], ins["value"], ins.get("filing_impact", "")))

    duration = round(time.time() - start, 2)
    fdb.execute("""
        INSERT INTO scan_runs (evidence_scanned, cross_links_found, insights_generated, duration_s)
        VALUES (?, ?, ?, ?)
    """, (20000 + 2000, len(links), len(insights), duration))
    fdb.commit()
    fdb.close()

    return {
        "cross_lane_links": len(links),
        "insights_generated": len(insights),
        "insights": insights[:10],
        "top_bridges": sorted(
            [{"pair": f"{l['from_lane']}→{l['to_lane']}", "text": l["evidence_text"][:150]}
             for l in links], key=lambda x: x["pair"]
        )[:10],
        "duration_s": duration,
    }


if __name__ == "__main__":
    result = run_full_fusion()
    print(json.dumps(result, indent=2, default=str))
