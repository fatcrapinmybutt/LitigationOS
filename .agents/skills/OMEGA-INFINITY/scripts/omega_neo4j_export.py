#!/usr/bin/env python3
"""OMEGA-INFINITY Neo4j Graph Export.

Exports litigation graph data as CSV files for Neo4j import and generates
Cypher LOAD CSV statements and a Neo4j Bloom perspective configuration.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
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
DEFAULT_OUTPUT = REPO_ROOT / "Vault" / "90_REPORTS" / "neo4j_export"

# Michigan Litigation color palette
COLORS: dict[str, str] = {
    "A_Custody": "#1E3A5F",      # Royal Blue
    "B_Housing": "#2E7D32",      # Forest Green
    "C_Convergence": "#F9A825",  # Gold
    "D_PPO": "#C62828",          # Crimson
    "E_Misconduct": "#6A1B9A",   # Purple
    "F_Appellate": "#00838F",    # Teal
    "Party": "#37474F",          # Dark Gray
    "Judge": "#880E4F",          # Dark Pink
    "Evidence": "#1565C0",       # Blue
    "Rule": "#4E342E",           # Brown
    "Form": "#00695C",           # Dark Teal
    "Default": "#546E7A",        # Blue Gray
}

# Node type definitions: (label, source_table, id_column, property_columns)
NODE_TYPES: list[dict[str, Any]] = [
    {"label": "Case", "table": "claims", "id_col": None, "props": ["claim_id", "claim_name", "claim_type", "case_lane"]},
    {"label": "Lane", "table": None, "id_col": None, "props": []},  # static
    {"label": "Party", "table": None, "id_col": None, "props": []},  # static
    {"label": "Judge", "table": None, "id_col": None, "props": []},  # static
    {"label": "Attorney", "table": None, "id_col": None, "props": []},  # static
    {"label": "Claim", "table": "claims", "id_col": None, "props": ["claim_id", "claim_name", "tort_type", "status"]},
    {"label": "Evidence", "table": "evidence_quotes", "id_col": None, "props": ["category", "source_file", "case_lane"]},
    {"label": "Filing", "table": "filing_readiness", "id_col": None, "props": ["vehicle_name", "status"]},
    {"label": "Form", "table": "court_forms_complete", "id_col": None, "props": []},
    {"label": "Rule", "table": "authority_master_index", "id_col": None, "props": []},
    {"label": "Violation", "table": "judicial_violations", "id_col": None, "props": []},
    {"label": "Witness", "table": "witness_list", "id_col": None, "props": []},
    {"label": "Event", "table": "timeline_events", "id_col": None, "props": []},
]

# Edge type definitions
EDGE_TYPES: list[dict[str, str]] = [
    {"type": "BELONGS_TO_LANE", "from_label": "Case", "to_label": "Lane"},
    {"type": "FILED_IN", "from_label": "Filing", "to_label": "Case"},
    {"type": "SUPPORTS_CLAIM", "from_label": "Evidence", "to_label": "Claim"},
    {"type": "VIOLATES_RULE", "from_label": "Violation", "to_label": "Rule"},
    {"type": "CITES_AUTHORITY", "from_label": "Filing", "to_label": "Rule"},
    {"type": "INVOLVES_PARTY", "from_label": "Case", "to_label": "Party"},
    {"type": "PRESIDED_BY", "from_label": "Case", "to_label": "Judge"},
    {"type": "REPRESENTED_BY", "from_label": "Party", "to_label": "Attorney"},
    {"type": "USES_FORM", "from_label": "Filing", "to_label": "Form"},
    {"type": "TESTIFIED_IN", "from_label": "Witness", "to_label": "Case"},
    {"type": "OCCURRED_IN", "from_label": "Event", "to_label": "Case"},
    {"type": "HAS_VIOLATION", "from_label": "Judge", "to_label": "Violation"},
    {"type": "EVIDENCE_FOR_FILING", "from_label": "Evidence", "to_label": "Filing"},
    {"type": "COMMITTED_BY", "from_label": "Violation", "to_label": "Judge"},
    {"type": "NEXT_EVENT", "from_label": "Event", "to_label": "Event"},
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


def _get_columns(conn: sqlite3.Connection, table: str) -> list[str]:
    if not _table_exists(conn, table):
        return []
    return [r["name"] for r in conn.execute(f"PRAGMA table_info([{table}])").fetchall()]


def _write_csv(filepath: Path, headers: list[str], rows: list[list[Any]]) -> int:
    """Write CSV with proper quoting. Returns row count."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
        writer.writerow(headers)
        for row in rows:
            writer.writerow([str(v) if v is not None else "" for v in row])
    return len(rows)


def _sanitize(val: Any, max_len: int = 500) -> str:
    """Sanitize a value for CSV export."""
    if val is None:
        return ""
    s = str(val).replace("\n", " ").replace("\r", "")
    return s[:max_len]


# ---------------------------------------------------------------------------
# Static nodes (parties, judges, lanes, attorneys)
# ---------------------------------------------------------------------------
def _static_lane_nodes() -> list[list[str]]:
    lanes = [
        ["LANE_A", "Lane", "A", "Custody", "2024-001507-DC"],
        ["LANE_B", "Lane", "B", "Housing", "2025-002760-CZ"],
        ["LANE_C", "Lane", "C", "Convergence", "Multi-lane"],
        ["LANE_D", "Lane", "D", "PPO", "2023-5907-PP"],
        ["LANE_E", "Lane", "E", "Misconduct", "JTC"],
        ["LANE_F", "Lane", "F", "Appellate", "COA 366810"],
    ]
    return lanes


def _static_party_nodes() -> list[list[str]]:
    return [
        ["PARTY_PIGORS", "Party", "Andrew James Pigors", "Plaintiff"],
        ["PARTY_WATSON", "Party", "Emily A. Watson", "Defendant"],
        ["PARTY_LDW", "Party", "L.D.W.", "Child"],
    ]


def _static_judge_nodes() -> list[list[str]]:
    return [
        ["JUDGE_MCNEILL", "Judge", "Hon. Jenny L. McNeill", "14th Circuit Court"],
    ]


def _static_attorney_nodes() -> list[list[str]]:
    return [
        ["ATTY_BARNES", "Attorney", "Jennifer Barnes", "P55406", "Barnes Law Firm PLLC", "WITHDRAWN"],
    ]


# ---------------------------------------------------------------------------
# Dynamic node export
# ---------------------------------------------------------------------------
def export_nodes(conn: sqlite3.Connection, output_dir: Path) -> dict[str, int]:
    """Export all node types as CSV files. Returns counts per type."""
    counts: dict[str, int] = {}

    # --- Static nodes ---
    # Lanes
    cnt = _write_csv(
        output_dir / "nodes_Lane.csv",
        [":ID", ":LABEL", "code", "name", "case_number"],
        _static_lane_nodes(),
    )
    counts["Lane"] = cnt

    # Parties
    cnt = _write_csv(
        output_dir / "nodes_Party.csv",
        [":ID", ":LABEL", "name", "role"],
        _static_party_nodes(),
    )
    counts["Party"] = cnt

    # Judges
    cnt = _write_csv(
        output_dir / "nodes_Judge.csv",
        [":ID", ":LABEL", "name", "court"],
        _static_judge_nodes(),
    )
    counts["Judge"] = cnt

    # Attorneys
    cnt = _write_csv(
        output_dir / "nodes_Attorney.csv",
        [":ID", ":LABEL", "name", "bar_number", "firm", "status"],
        _static_attorney_nodes(),
    )
    counts["Attorney"] = cnt

    # --- Dynamic nodes from DB ---

    # Claims
    if _table_exists(conn, "claims"):
        cols = _get_columns(conn, "claims")
        id_col = next((c for c in cols if "id" in c.lower()), cols[0] if cols else "rowid")
        rows = conn.execute(f"SELECT rowid, * FROM claims LIMIT 5000").fetchall()
        csv_rows: list[list[str]] = []
        for r in rows:
            rd = dict(r)
            node_id = f"CLAIM_{rd.get('rowid', rd.get(id_col, ''))}"
            csv_rows.append([
                node_id, "Claim",
                _sanitize(rd.get("claim_name", rd.get("claim_id", ""))),
                _sanitize(rd.get("claim_type", rd.get("tort_type", ""))),
                _sanitize(rd.get("case_lane", "")),
                _sanitize(rd.get("status", "")),
            ])
        counts["Claim"] = _write_csv(
            output_dir / "nodes_Claim.csv",
            [":ID", ":LABEL", "name", "type", "lane", "status"],
            csv_rows,
        )

    # Evidence
    if _table_exists(conn, "evidence_quotes"):
        cols = _get_columns(conn, "evidence_quotes")
        text_col = next((c for c in cols if "quote" in c.lower() or "text" in c.lower()), None)
        rows = conn.execute("SELECT rowid, * FROM evidence_quotes LIMIT 10000").fetchall()
        csv_rows = []
        for r in rows:
            rd = dict(r)
            node_id = f"EV_{rd.get('rowid', '')}"
            csv_rows.append([
                node_id, "Evidence",
                _sanitize(rd.get(text_col, "") if text_col else "", 200),
                _sanitize(rd.get("category", "")),
                _sanitize(rd.get("source_file", "")),
                _sanitize(rd.get("case_lane", rd.get("lane", ""))),
            ])
        counts["Evidence"] = _write_csv(
            output_dir / "nodes_Evidence.csv",
            [":ID", ":LABEL", "text", "category", "source_file", "lane"],
            csv_rows,
        )

    # Filings
    if _table_exists(conn, "filing_readiness"):
        cols = _get_columns(conn, "filing_readiness")
        rows = conn.execute("SELECT rowid, * FROM filing_readiness").fetchall()
        csv_rows = []
        for r in rows:
            rd = dict(r)
            name = rd.get("vehicle_name", rd.get("name", rd.get("filing", f"FILING_{rd.get('rowid', '')}")))
            node_id = f"FILING_{rd.get('rowid', '')}"
            csv_rows.append([
                node_id, "Filing",
                _sanitize(name),
                _sanitize(rd.get("status", "")),
            ])
        counts["Filing"] = _write_csv(
            output_dir / "nodes_Filing.csv",
            [":ID", ":LABEL", "name", "status"],
            csv_rows,
        )

    # Forms
    if _table_exists(conn, "court_forms_complete"):
        cols = _get_columns(conn, "court_forms_complete")
        name_col = next((c for c in cols if "name" in c.lower() or "form" in c.lower() or "title" in c.lower()), cols[0] if cols else None)
        rows = conn.execute("SELECT rowid, * FROM court_forms_complete LIMIT 500").fetchall()
        csv_rows = []
        for r in rows:
            rd = dict(r)
            node_id = f"FORM_{rd.get('rowid', '')}"
            csv_rows.append([
                node_id, "Form",
                _sanitize(rd.get(name_col, "") if name_col else ""),
            ])
        counts["Form"] = _write_csv(
            output_dir / "nodes_Form.csv",
            [":ID", ":LABEL", "name"],
            csv_rows,
        )

    # Rules / Authorities
    if _table_exists(conn, "authority_master_index"):
        cols = _get_columns(conn, "authority_master_index")
        name_col = next((c for c in cols if "rule" in c.lower() or "citation" in c.lower() or "name" in c.lower() or "authority" in c.lower()), cols[0] if cols else None)
        rows = conn.execute("SELECT rowid, * FROM authority_master_index LIMIT 2000").fetchall()
        csv_rows = []
        for r in rows:
            rd = dict(r)
            node_id = f"RULE_{rd.get('rowid', '')}"
            csv_rows.append([
                node_id, "Rule",
                _sanitize(rd.get(name_col, "") if name_col else ""),
            ])
        counts["Rule"] = _write_csv(
            output_dir / "nodes_Rule.csv",
            [":ID", ":LABEL", "citation"],
            csv_rows,
        )

    # Violations
    if _table_exists(conn, "judicial_violations"):
        cols = _get_columns(conn, "judicial_violations")
        desc_col = next((c for c in cols if "desc" in c.lower() or "type" in c.lower() or "violation" in c.lower()), None)
        rows = conn.execute("SELECT rowid, * FROM judicial_violations LIMIT 2000").fetchall()
        csv_rows = []
        for r in rows:
            rd = dict(r)
            node_id = f"VIOL_{rd.get('rowid', '')}"
            csv_rows.append([
                node_id, "Violation",
                _sanitize(rd.get(desc_col, "") if desc_col else ""),
            ])
        counts["Violation"] = _write_csv(
            output_dir / "nodes_Violation.csv",
            [":ID", ":LABEL", "description"],
            csv_rows,
        )

    # Witnesses
    if _table_exists(conn, "witness_list"):
        cols = _get_columns(conn, "witness_list")
        name_col = next((c for c in cols if "name" in c.lower()), cols[0] if cols else None)
        rows = conn.execute("SELECT rowid, * FROM witness_list LIMIT 500").fetchall()
        csv_rows = []
        for r in rows:
            rd = dict(r)
            node_id = f"WIT_{rd.get('rowid', '')}"
            csv_rows.append([
                node_id, "Witness",
                _sanitize(rd.get(name_col, "") if name_col else ""),
            ])
        counts["Witness"] = _write_csv(
            output_dir / "nodes_Witness.csv",
            [":ID", ":LABEL", "name"],
            csv_rows,
        )

    # Events
    if _table_exists(conn, "timeline_events"):
        cols = _get_columns(conn, "timeline_events")
        date_col = next((c for c in cols if "date" in c.lower()), None)
        desc_col = next((c for c in cols if any(h in c.lower() for h in ("desc", "event", "title", "summary"))), None)
        rows = conn.execute("SELECT rowid, * FROM timeline_events LIMIT 5000").fetchall()
        csv_rows = []
        for r in rows:
            rd = dict(r)
            node_id = f"EVT_{rd.get('rowid', '')}"
            csv_rows.append([
                node_id, "Event",
                _sanitize(rd.get(date_col, "") if date_col else ""),
                _sanitize(rd.get(desc_col, "") if desc_col else "", 200),
            ])
        counts["Event"] = _write_csv(
            output_dir / "nodes_Event.csv",
            [":ID", ":LABEL", "date", "description"],
            csv_rows,
        )

    return counts


# ---------------------------------------------------------------------------
# Edge export
# ---------------------------------------------------------------------------
def export_edges(conn: sqlite3.Connection, output_dir: Path) -> dict[str, int]:
    """Export relationship edges as CSV. Returns counts per type."""
    counts: dict[str, int] = {}

    # BELONGS_TO_LANE: Claims → Lanes (via case_lane column)
    if _table_exists(conn, "claims"):
        cols = _get_columns(conn, "claims")
        lane_col = next((c for c in cols if "lane" in c.lower()), None)
        if lane_col:
            rows = conn.execute(f"SELECT rowid, [{lane_col}] FROM claims WHERE [{lane_col}] IS NOT NULL").fetchall()
            csv_rows: list[list[str]] = []
            for r in rows:
                lane_val = str(r[1]).strip().upper()
                lane_code = lane_val[0] if lane_val else ""
                if lane_code in "ABCDEF":
                    csv_rows.append([f"CLAIM_{r[0]}", f"LANE_{lane_code}", "BELONGS_TO_LANE"])
            counts["BELONGS_TO_LANE"] = _write_csv(
                output_dir / "edges_BELONGS_TO_LANE.csv",
                [":START_ID", ":END_ID", ":TYPE"],
                csv_rows,
            )

    # SUPPORTS_CLAIM: Evidence → Claims (via claim_id or similar)
    if _table_exists(conn, "evidence_quotes") and _table_exists(conn, "claims"):
        ev_cols = _get_columns(conn, "evidence_quotes")
        claim_ref = next((c for c in ev_cols if "claim" in c.lower()), None)
        if claim_ref:
            rows = conn.execute(
                f"SELECT eq.rowid as ev_rowid, c.rowid as c_rowid "
                f"FROM evidence_quotes eq JOIN claims c ON eq.[{claim_ref}] = c.claim_id "
                f"LIMIT 10000"
            ).fetchall()
            csv_rows = [[f"EV_{r[0]}", f"CLAIM_{r[1]}", "SUPPORTS_CLAIM"] for r in rows]
            counts["SUPPORTS_CLAIM"] = _write_csv(
                output_dir / "edges_SUPPORTS_CLAIM.csv",
                [":START_ID", ":END_ID", ":TYPE"],
                csv_rows,
            )

    # HAS_VIOLATION: Judge → Violations
    if _table_exists(conn, "judicial_violations"):
        rows = conn.execute("SELECT rowid FROM judicial_violations LIMIT 2000").fetchall()
        csv_rows = [[f"JUDGE_MCNEILL", f"VIOL_{r[0]}", "HAS_VIOLATION"] for r in rows]
        counts["HAS_VIOLATION"] = _write_csv(
            output_dir / "edges_HAS_VIOLATION.csv",
            [":START_ID", ":END_ID", ":TYPE"],
            csv_rows,
        )

    # COMMITTED_BY: Violations → Judge (reverse of above)
    if "HAS_VIOLATION" in counts:
        rows = conn.execute("SELECT rowid FROM judicial_violations LIMIT 2000").fetchall()
        csv_rows = [[f"VIOL_{r[0]}", f"JUDGE_MCNEILL", "COMMITTED_BY"] for r in rows]
        counts["COMMITTED_BY"] = _write_csv(
            output_dir / "edges_COMMITTED_BY.csv",
            [":START_ID", ":END_ID", ":TYPE"],
            csv_rows,
        )

    # Static relationship edges
    static_edges: list[tuple[str, list[list[str]]]] = [
        ("INVOLVES_PARTY", [
            ["CLAIM_1", "PARTY_PIGORS", "INVOLVES_PARTY"],
            ["CLAIM_1", "PARTY_WATSON", "INVOLVES_PARTY"],
        ]),
        ("PRESIDED_BY", [
            ["CLAIM_1", "JUDGE_MCNEILL", "PRESIDED_BY"],
        ]),
        ("REPRESENTED_BY", [
            ["PARTY_WATSON", "ATTY_BARNES", "REPRESENTED_BY"],
        ]),
    ]
    for edge_type, edge_rows in static_edges:
        counts[edge_type] = _write_csv(
            output_dir / f"edges_{edge_type}.csv",
            [":START_ID", ":END_ID", ":TYPE"],
            edge_rows,
        )

    return counts


# ---------------------------------------------------------------------------
# Cypher generation
# ---------------------------------------------------------------------------
def generate_cypher(output_dir: Path) -> str:
    """Generate Cypher LOAD CSV statements for Neo4j import."""
    lines: list[str] = [
        "// OMEGA-INFINITY Neo4j Import Script",
        "// Generated by omega_neo4j_export.py",
        "// Run in Neo4j Browser or cypher-shell",
        "",
        "// --- Constraints ---",
    ]

    node_labels = ["Lane", "Party", "Judge", "Attorney", "Claim", "Evidence", "Filing", "Form", "Rule", "Violation", "Witness", "Event"]

    for label in node_labels:
        lines.append(f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{label}) REQUIRE n.id IS UNIQUE;")

    lines.append("")
    lines.append("// --- Node imports ---")

    csv_prefix = "file:///neo4j_export/"

    for label in node_labels:
        csv_file = f"nodes_{label}.csv"
        csv_path = output_dir / csv_file
        if csv_path.is_file():
            lines.append(f"""
LOAD CSV WITH HEADERS FROM '{csv_prefix}{csv_file}' AS row
MERGE (n:{label} {{id: row.`:ID`}})
SET n += row;""")

    lines.append("")
    lines.append("// --- Edge imports ---")

    for edge_file in sorted(output_dir.glob("edges_*.csv")):
        edge_type = edge_file.stem.replace("edges_", "")
        lines.append(f"""
LOAD CSV WITH HEADERS FROM '{csv_prefix}{edge_file.name}' AS row
MATCH (a {{id: row.`:START_ID`}})
MATCH (b {{id: row.`:END_ID`}})
MERGE (a)-[:{edge_type}]->(b);""")

    cypher_text = "\n".join(lines)

    cypher_path = output_dir / "import.cypher"
    cypher_path.write_text(cypher_text, encoding="utf-8")

    return str(cypher_path)


# ---------------------------------------------------------------------------
# Bloom configuration
# ---------------------------------------------------------------------------
def generate_bloom_config(output_dir: Path, node_counts: dict[str, int]) -> str:
    """Generate Neo4j Bloom perspective JSON."""
    categories: list[dict[str, Any]] = []

    label_colors: dict[str, str] = {
        "Lane": COLORS["C_Convergence"],
        "Party": COLORS["Party"],
        "Judge": COLORS["Judge"],
        "Attorney": COLORS["Default"],
        "Claim": COLORS["A_Custody"],
        "Evidence": COLORS["Evidence"],
        "Filing": COLORS["B_Housing"],
        "Form": COLORS["Form"],
        "Rule": COLORS["Rule"],
        "Violation": COLORS["D_PPO"],
        "Witness": COLORS["Default"],
        "Event": COLORS["F_Appellate"],
    }

    for label, color in label_colors.items():
        count = node_counts.get(label, 0)
        # Size based on connection count (proxy: node count)
        size = 1.0 if count < 10 else 1.5 if count < 100 else 2.0 if count < 1000 else 3.0

        categories.append({
            "label": label,
            "color": color,
            "size": size,
            "caption": "{name}" if label in ("Party", "Judge", "Attorney", "Witness") else "{id}",
        })

    perspective: dict[str, Any] = {
        "name": "Michigan Litigation — OMEGA-INFINITY",
        "version": "1.0",
        "categories": categories,
        "relationshipTypes": [et["type"] for et in EDGE_TYPES],
        "palette": COLORS,
        "searchPhrases": [
            {"name": "All evidence for a lane", "cypher": "MATCH (e:Evidence)-[:BELONGS_TO_LANE]->(l:Lane {code: $lane}) RETURN e, l"},
            {"name": "Judicial violations", "cypher": "MATCH (j:Judge)-[:HAS_VIOLATION]->(v:Violation) RETURN j, v"},
            {"name": "Filing dependencies", "cypher": "MATCH (f:Filing)-[:CITES_AUTHORITY]->(r:Rule) RETURN f, r"},
            {"name": "Evidence supporting claims", "cypher": "MATCH (e:Evidence)-[:SUPPORTS_CLAIM]->(c:Claim) RETURN e, c LIMIT 100"},
            {"name": "Full case graph", "cypher": "MATCH path = (n)-[r]->(m) RETURN path LIMIT 500"},
        ],
    }

    bloom_path = output_dir / "bloom_perspective.json"
    bloom_path.write_text(json.dumps(perspective, indent=2), encoding="utf-8")

    return str(bloom_path)


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------
def print_export_summary(
    node_counts: dict[str, int],
    edge_counts: dict[str, int],
    cypher_path: str,
    bloom_path: str,
    output_dir: Path,
    as_json: bool = False,
) -> None:
    report = {
        "output_dir": str(output_dir),
        "node_counts": node_counts,
        "edge_counts": edge_counts,
        "total_nodes": sum(node_counts.values()),
        "total_edges": sum(edge_counts.values()),
        "cypher_script": cypher_path,
        "bloom_config": bloom_path,
    }

    if as_json:
        print(json.dumps(report, indent=2, default=str))
        return

    print("=" * 70)
    print("  OMEGA-INFINITY NEO4J GRAPH EXPORT")
    print("=" * 70)

    print(f"\n  Output: {output_dir}")

    print(f"\n  📊 NODES ({sum(node_counts.values()):,} total)")
    print("  " + "-" * 40)
    for label, count in sorted(node_counts.items()):
        print(f"    {label:<15} {count:>8,}")

    print(f"\n  🔗 EDGES ({sum(edge_counts.values()):,} total)")
    print("  " + "-" * 40)
    for etype, count in sorted(edge_counts.items()):
        print(f"    {etype:<25} {count:>8,}")

    print(f"\n  📄 Generated files:")
    print(f"    Cypher script: {cypher_path}")
    print(f"    Bloom config:  {bloom_path}")

    # List all CSV files
    csv_files = sorted(output_dir.glob("*.csv"))
    print(f"    CSV files:     {len(csv_files)}")
    for cf in csv_files:
        size_kb = cf.stat().st_size / 1024
        print(f"      {cf.name} ({size_kb:.1f} KB)")

    print("\n" + "=" * 70)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    parser = argparse.ArgumentParser(description="OMEGA-INFINITY Neo4j Graph Export")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help="Path to primary DB")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT, help="Output directory for exports")
    parser.add_argument("--format", choices=["csv", "cypher"], default="csv", help="Export format (csv also generates cypher)")
    parser.add_argument("--json", action="store_true", help="Output summary as JSON")
    args = parser.parse_args()

    if not args.db.is_file():
        msg = f"DB not found: {args.db}"
        print(json.dumps({"error": msg}) if args.json else f"❌ {msg}")
        return 1

    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        conn = _connect(args.db)

        node_counts = export_nodes(conn, output_dir)
        edge_counts = export_edges(conn, output_dir)
        cypher_path = generate_cypher(output_dir)
        bloom_path = generate_bloom_config(output_dir, node_counts)

        conn.close()

        print_export_summary(node_counts, edge_counts, cypher_path, bloom_path, output_dir, as_json=args.json)
    except Exception as exc:
        msg = str(exc)
        print(json.dumps({"error": msg}) if args.json else f"❌ Error: {msg}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
