#!/usr/bin/env python
"""export_brain_d3.py — Export mbp_brain.db to optimized D3.js JSON.

Intelligently samples 232K+ nodes down to 3-5K for WebGL canvas rendering.
Three-tier sampling: skeleton + top-connected + chain-support.

Usage:
    python -I scripts/export_brain_d3.py                    # Export with defaults
    python -I scripts/export_brain_d3.py --max-nodes 5000   # Cap node count
    python -I scripts/export_brain_d3.py --full              # Export ALL (huge)
    python -I scripts/export_brain_d3.py --chains-only       # Only chain paths
    python -I scripts/export_brain_d3.py --output path.json  # Custom output path
"""

import argparse
import json
import sqlite3
import sys
from datetime import date, datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "mbp_brain.db"
DEFAULT_OUTPUT = (
    Path(__file__).resolve().parent.parent
    / "08_MEDIA"
    / "MANBEARPIG_V5"
    / "graph_data.json"
)
SEPARATION_ANCHOR = date(2025, 7, 29)

LAYER_CONFIG = {
    "EVIDENCE": {"color": "#4ecdc4", "shape": "circle", "y_band": 0.1},
    "ACTOR": {"color": "#ff6b6b", "shape": "diamond", "y_band": 0.25},
    "VIOLATION": {"color": "#ff4444", "shape": "triangle", "y_band": 0.4},
    "AUTHORITY": {"color": "#ffd93d", "shape": "hexagon", "y_band": 0.55},
    "REMEDY": {"color": "#6bcb77", "shape": "star", "y_band": 0.7},
    "FILING": {"color": "#4d96ff", "shape": "rect", "y_band": 0.85},
    "LANE": {"color": "#9b59b6", "shape": "ring", "y_band": 0.95},
}

SKELETON_LAYERS = ("FILING", "REMEDY", "LANE", "ACTOR", "VIOLATION")


def get_connection():
    if not DB_PATH.exists():
        print(f"ERROR: Database not found at {DB_PATH}", file=sys.stderr)
        sys.exit(1)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    return conn


def compute_edge_counts(conn):
    """Return {node_id: total_edge_count} for every node with at least one edge."""
    edge_counts = {}
    rows = conn.execute(
        """
        SELECT nid, SUM(cnt) AS total FROM (
            SELECT source_id AS nid, COUNT(*) AS cnt
            FROM edges WHERE source_id != '' GROUP BY source_id
            UNION ALL
            SELECT target_id AS nid, COUNT(*) AS cnt
            FROM edges WHERE target_id != '' GROUP BY target_id
        ) GROUP BY nid
        """
    ).fetchall()
    for r in rows:
        edge_counts[r["nid"]] = r["total"]
    return edge_counts


def collect_chain_nodes(conn):
    """Return set of all node IDs that appear in any chain path."""
    chain_nodes = set()
    for row in conn.execute("SELECT chain_path FROM chains"):
        try:
            path = json.loads(row["chain_path"])
            if isinstance(path, list):
                chain_nodes.update(path)
        except (json.JSONDecodeError, TypeError):
            pass
    return chain_nodes


def get_one_hop_neighbors(conn, node_ids):
    """Return the set of immediate neighbors (1-hop) of the given node IDs."""
    if not node_ids:
        return set()
    neighbors = set()
    node_list = list(node_ids)
    batch_size = 500
    for i in range(0, len(node_list), batch_size):
        batch = node_list[i : i + batch_size]
        ph = ",".join("?" * len(batch))
        for row in conn.execute(
            f"SELECT DISTINCT target_id AS nid FROM edges "
            f"WHERE source_id IN ({ph}) AND target_id != ''",
            batch,
        ):
            neighbors.add(row["nid"])
        for row in conn.execute(
            f"SELECT DISTINCT source_id AS nid FROM edges "
            f"WHERE target_id IN ({ph}) AND source_id != ''",
            batch,
        ):
            neighbors.add(row["nid"])
    return neighbors


def sample_nodes(conn, max_nodes, chains_only, full):
    """Three-tier intelligent node sampling.

    Tier 1 — skeleton: all non-EVIDENCE/AUTHORITY layers + chain nodes
    Tier 2 — top evidence + authority by edge connectivity
    Tier 3 — 1-hop neighbors of chain nodes, ranked by connectivity
    """
    edge_counts = compute_edge_counts(conn)
    chain_node_ids = collect_chain_nodes(conn)
    selected = set()

    if chains_only:
        selected = chain_node_ids.copy()
        print(f"  Chains-only mode: {len(selected)} chain nodes")

    elif full:
        for row in conn.execute("SELECT id FROM nodes"):
            selected.add(row["id"])
        print(f"  Full export: {len(selected)} nodes (WARNING: very large)")

    else:
        # --- Tier 1: skeleton layers + chain participants ---
        for row in conn.execute(
            "SELECT id FROM nodes WHERE layer IN (?,?,?,?,?)", SKELETON_LAYERS
        ):
            selected.add(row["id"])
        selected.update(chain_node_ids)
        tier1 = len(selected)
        print(f"  Tier 1 (skeleton + chains): {tier1} nodes")

        # --- Tier 2: top EVIDENCE and AUTHORITY by connectivity ---
        remaining = max_nodes - len(selected)
        if remaining > 0:
            ev_budget = remaining // 2
            au_budget = remaining - ev_budget

            ev_candidates = []
            for row in conn.execute("SELECT id FROM nodes WHERE layer = 'EVIDENCE'"):
                nid = row["id"]
                if nid not in selected:
                    ev_candidates.append((nid, edge_counts.get(nid, 0)))
            ev_candidates.sort(key=lambda x: x[1], reverse=True)
            for nid, _ in ev_candidates[:ev_budget]:
                selected.add(nid)

            au_candidates = []
            for row in conn.execute("SELECT id FROM nodes WHERE layer = 'AUTHORITY'"):
                nid = row["id"]
                if nid not in selected:
                    au_candidates.append((nid, edge_counts.get(nid, 0)))
            au_candidates.sort(key=lambda x: x[1], reverse=True)
            for nid, _ in au_candidates[:au_budget]:
                selected.add(nid)

            tier2_added = len(selected) - tier1
            print(f"  Tier 2 (top connected): +{tier2_added} nodes")

        # --- Tier 3: 1-hop neighbors of chain nodes ---
        remaining = max_nodes - len(selected)
        if remaining > 0:
            before = len(selected)
            neighbors = get_one_hop_neighbors(conn, chain_node_ids) - selected
            ranked = sorted(neighbors, key=lambda n: edge_counts.get(n, 0), reverse=True)
            for nid in ranked[:remaining]:
                selected.add(nid)
            print(f"  Tier 3 (chain neighbors): +{len(selected) - before} nodes")

    print(f"  Total selected: {len(selected):,} nodes")
    return selected, edge_counts, chain_node_ids


def load_nodes(conn, selected_ids, edge_counts, chain_node_ids):
    """Fetch node rows for all selected IDs."""
    nodes = []
    nodes_by_id = {}
    selected_list = list(selected_ids)
    batch_size = 500
    for i in range(0, len(selected_list), batch_size):
        batch = selected_list[i : i + batch_size]
        ph = ",".join("?" * len(batch))
        for row in conn.execute(
            f"SELECT id, node_type, layer, label, severity, confidence, "
            f"readiness, lane FROM nodes WHERE id IN ({ph})",
            batch,
        ):
            nid = row["id"]
            node = {
                "id": nid,
                "type": row["node_type"] or "",
                "layer": row["layer"] or "EVIDENCE",
                "label": (row["label"] or "")[:200],
                "severity": round(row["severity"] or 0, 3),
                "confidence": round(row["confidence"] or 0, 3),
                "readiness": round(row["readiness"] or 0, 3),
                "lane": row["lane"] or "",
                "chain_count": 0,
                "edge_count": edge_counts.get(nid, 0),
                "in_chain": nid in chain_node_ids,
                "gap": False,
            }
            nodes.append(node)
            nodes_by_id[nid] = node
    return nodes, nodes_by_id


def annotate_gaps(conn, nodes_by_id):
    """Mark nodes that appear in unresolved gaps."""
    for row in conn.execute("SELECT DISTINCT node_id FROM gaps WHERE resolved = 0"):
        nid = row["node_id"]
        if nid in nodes_by_id:
            nodes_by_id[nid]["gap"] = True


def annotate_chain_counts(conn, nodes_by_id):
    """Count how many chains each node participates in."""
    for row in conn.execute("SELECT chain_path FROM chains"):
        try:
            path = json.loads(row["chain_path"])
            if isinstance(path, list):
                for nid in path:
                    if nid in nodes_by_id:
                        nodes_by_id[nid]["chain_count"] += 1
        except (json.JSONDecodeError, TypeError):
            pass


EDGE_PRIORITY = {
    "PROVES": 0, "EXECUTED_VIA": 0, "CONTRADICTS": 0,
    "GOVERNED_BY": 1, "AUTHORIZES": 1,
    "CITES": 2,
    "ASSIGNED_TO": 3, "RELATED": 3,
}


def load_edges(conn, nodes_by_id, chain_node_ids, max_edges=20000):
    """Load edges with budget management — prioritize chain and high-value edges."""
    chain_edge_keys = set()
    for row in conn.execute("SELECT chain_path FROM chains"):
        try:
            path = json.loads(row["chain_path"])
            if isinstance(path, list):
                for i in range(len(path) - 1):
                    chain_edge_keys.add((path[i], path[i + 1]))
                    chain_edge_keys.add((path[i + 1], path[i]))
        except (json.JSONDecodeError, TypeError):
            pass

    buckets = {0: [], 1: [], 2: [], 3: []}
    chain_edges = []

    cursor = conn.execute(
        "SELECT source_id, target_id, edge_type, weight "
        "FROM edges WHERE source_id != '' AND target_id != ''"
    )
    for row in cursor:
        sid, tid = row["source_id"], row["target_id"]
        if sid not in nodes_by_id or tid not in nodes_by_id:
            continue
        w = row["weight"] or 0.5
        etype = row["edge_type"] or "RELATED"
        if etype == "PROVES" and w > 1.0:
            w = min(w / 100.0, 1.0)
        edge = {"source": sid, "target": tid, "type": etype, "weight": round(w, 3)}

        if (sid, tid) in chain_edge_keys:
            chain_edges.append(edge)
        else:
            prio = EDGE_PRIORITY.get(etype, 3)
            buckets[prio].append(edge)

    edges = list(chain_edges)
    remaining = max_edges - len(edges)
    for prio in sorted(buckets.keys()):
        bucket = buckets[prio]
        bucket.sort(key=lambda e: e["weight"], reverse=True)
        take = min(len(bucket), remaining)
        edges.extend(bucket[:take])
        remaining -= take
        if remaining <= 0:
            break

    return edges


def load_chains(conn, nodes_by_id):
    """Load all computed chains with filing labels."""
    chains = []
    for row in conn.execute(
        "SELECT id, chain_path, strength_score, lane, filing_id "
        "FROM chains ORDER BY strength_score DESC"
    ):
        try:
            path = json.loads(row["chain_path"])
            if not isinstance(path, list):
                path = []
        except (json.JSONDecodeError, TypeError):
            path = []
        filing_label = ""
        fid = row["filing_id"]
        if fid and fid in nodes_by_id:
            filing_label = nodes_by_id[fid]["label"]
        chains.append(
            {
                "id": row["id"],
                "path": path,
                "strength": round(row["strength_score"] or 0, 4),
                "lane": row["lane"] or "",
                "filing": filing_label,
            }
        )
    return chains


def load_gaps(conn, limit=500):
    """Load top unresolved gaps."""
    gaps = []
    for row in conn.execute(
        "SELECT gap_type, node_id, description, priority "
        "FROM gaps WHERE resolved = 0 "
        "ORDER BY CASE priority WHEN 'HIGH' THEN 1 WHEN 'MEDIUM' THEN 2 ELSE 3 END "
        "LIMIT ?",
        (limit,),
    ):
        gaps.append(
            {
                "type": row["gap_type"] or "",
                "node_id": row["node_id"] or "",
                "description": (row["description"] or "")[:200],
                "priority": row["priority"] or "MEDIUM",
            }
        )
    return gaps


def compute_stats(conn, nodes_by_id):
    """Compute aggregate statistics."""
    nodes_per_layer = {}
    for row in conn.execute("SELECT layer, COUNT(*) AS cnt FROM nodes GROUP BY layer"):
        nodes_per_layer[row["layer"]] = row["cnt"]

    edges_per_type = {}
    for row in conn.execute(
        "SELECT edge_type, COUNT(*) AS cnt FROM edges GROUP BY edge_type"
    ):
        edges_per_type[row["edge_type"]] = row["cnt"]

    chains_per_filing = {}
    for row in conn.execute(
        "SELECT filing_id, COUNT(*) AS cnt FROM chains GROUP BY filing_id"
    ):
        chains_per_filing[row["filing_id"]] = row["cnt"]

    gaps_per_type = {}
    for row in conn.execute(
        "SELECT gap_type, COUNT(*) AS cnt FROM gaps WHERE resolved = 0 GROUP BY gap_type"
    ):
        gaps_per_type[row["gap_type"]] = row["cnt"]

    filing_strengths = {}
    for row in conn.execute(
        "SELECT filing_id, AVG(strength_score) AS avg_s FROM chains GROUP BY filing_id"
    ):
        fid = row["filing_id"]
        label = nodes_by_id.get(fid, {}).get("label", fid or "unknown")
        filing_strengths[label] = row["avg_s"] or 0

    strongest = max(filing_strengths, key=filing_strengths.get) if filing_strengths else ""
    weakest = min(filing_strengths, key=filing_strengths.get) if filing_strengths else ""

    return {
        "nodes_per_layer": nodes_per_layer,
        "edges_per_type": edges_per_type,
        "chains_per_filing": chains_per_filing,
        "gaps_per_type": gaps_per_type,
        "strongest_filing": strongest,
        "weakest_filing": weakest,
    }


def export(args):
    conn = get_connection()

    sep_days = (date.today() - SEPARATION_ANCHOR).days
    print("THEMANBEARPIG V5 — Brain Export")
    print(f"Database: {DB_PATH}")
    print(f"Separation: {sep_days} days")
    print()

    row = conn.execute(
        "SELECT "
        "(SELECT COUNT(*) FROM nodes) AS n, "
        "(SELECT COUNT(*) FROM edges) AS e, "
        "(SELECT COUNT(*) FROM chains) AS c, "
        "(SELECT COUNT(*) FROM gaps WHERE resolved=0) AS g"
    ).fetchone()
    total_nodes, total_edges, total_chains, total_gaps = (
        row["n"],
        row["e"],
        row["c"],
        row["g"],
    )
    print(
        f"Brain: {total_nodes:,} nodes, {total_edges:,} edges, "
        f"{total_chains} chains, {total_gaps:,} gaps"
    )
    print()

    # Sample
    print("Sampling nodes...")
    selected_ids, edge_counts, chain_node_ids = sample_nodes(
        conn, args.max_nodes, args.chains_only, args.full
    )

    # Load data
    print("Loading nodes...")
    nodes, nodes_by_id = load_nodes(conn, selected_ids, edge_counts, chain_node_ids)
    annotate_gaps(conn, nodes_by_id)
    annotate_chain_counts(conn, nodes_by_id)
    print(f"  {len(nodes):,} nodes loaded")

    print("Loading edges...")
    edge_budget = 999_999_999 if args.full else args.max_edges
    edges = load_edges(conn, nodes_by_id, chain_node_ids, edge_budget)
    print(f"  {len(edges):,} edges loaded")

    print("Loading chains...")
    chains = load_chains(conn, nodes_by_id)
    print(f"  {len(chains)} chains loaded")

    print("Loading gaps...")
    gaps = load_gaps(conn)
    print(f"  {len(gaps)} gaps loaded")

    print("Computing stats...")
    stats = compute_stats(conn, nodes_by_id)

    version_row = conn.execute(
        "SELECT version FROM versions ORDER BY version DESC LIMIT 1"
    ).fetchone()
    brain_version = version_row["version"] if version_row else 0

    sampling_desc = "tiered: skeleton + top-connected + chain-support"
    if args.chains_only:
        sampling_desc = "chains-only: nodes in chain paths"
    elif args.full:
        sampling_desc = "full: all nodes (unsampled)"

    output = {
        "metadata": {
            "generated": datetime.now(timezone.utc).isoformat(),
            "total_nodes": total_nodes,
            "total_edges": total_edges,
            "exported_nodes": len(nodes),
            "exported_edges": len(edges),
            "sampling": sampling_desc,
            "separation_days": sep_days,
            "brain_version": brain_version,
        },
        "nodes": nodes,
        "edges": edges,
        "chains": chains,
        "gaps": gaps,
        "stats": stats,
        "layer_config": LAYER_CONFIG,
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        import orjson

        raw = orjson.dumps(output, option=orjson.OPT_INDENT_2)
        output_path.write_bytes(raw)
    except ImportError:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

    size_mb = output_path.stat().st_size / (1024 * 1024)
    print()
    print(f"Exported to {output_path}")
    print(
        f"  {len(nodes):,} nodes, {len(edges):,} edges, "
        f"{len(chains)} chains, {len(gaps)} gaps"
    )
    print(f"  File size: {size_mb:.1f} MB")

    conn.close()
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Export mbp_brain.db to D3.js JSON for THEMANBEARPIG V5",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--max-nodes",
        type=int,
        default=5000,
        help="Maximum number of nodes to export (default: 5000)",
    )
    parser.add_argument(
        "--max-edges",
        type=int,
        default=20000,
        help="Maximum number of edges to export (default: 20000)",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Export ALL nodes (warning: 232K+ nodes, huge file)",
    )
    parser.add_argument(
        "--chains-only",
        action="store_true",
        help="Only export nodes that appear in chain paths",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(DEFAULT_OUTPUT),
        help=f"Output JSON path (default: {DEFAULT_OUTPUT})",
    )
    args = parser.parse_args()
    sys.exit(export(args))


if __name__ == "__main__":
    main()
