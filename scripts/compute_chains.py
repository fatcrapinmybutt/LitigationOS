#!/usr/bin/env python3
"""
THEMANBEARPIG Legal Brain v5.0 — T2: Chain Computation Engine
=============================================================
Loads nodes/edges from mbp_brain.db into a NetworkX DiGraph, then:
  1. BFS from every violation node → all reachable filing nodes
  2. Score chain strength: Π(edge_weights) × max_severity × binding_strength
  3. Store top-K chains per filing
  4. Update gap table with violations that have no path to any filing

Usage:
    python -I scripts/compute_chains.py           # Compute chains
    python -I scripts/compute_chains.py --top 20   # Store top 20 per filing (default 10)
    python -I scripts/compute_chains.py --stats     # Print stats only (no recompute)
"""
import argparse
import json
import logging
import os
import sqlite3
import sys
import time
from collections import defaultdict
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("compute_chains")

BRAIN_DB = Path(__file__).resolve().parent.parent / "mbp_brain.db"

# Binding strength multipliers
BINDING_MULT = {
    "mandatory": 1.0,
    "persuasive": 0.7,
    "informative": 0.4,
    None: 0.5,
}


def connect_brain():
    if not BRAIN_DB.exists():
        log.error(f"Brain DB not found: {BRAIN_DB}")
        sys.exit(1)
    conn = sqlite3.connect(str(BRAIN_DB))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 60000")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA cache_size = -64000")
    conn.execute("PRAGMA temp_store = MEMORY")
    return conn


def load_graph(conn):
    """Load nodes and edges into a NetworkX DiGraph."""
    try:
        import networkx as nx
    except ImportError:
        log.error("networkx not installed. Run: pip install networkx")
        sys.exit(1)

    G = nx.DiGraph()

    # Load nodes
    log.info("Loading nodes...")
    t0 = time.time()
    node_count = 0
    cursor = conn.execute(
        "SELECT id, node_type, layer, label, severity, confidence, readiness, binding_strength, lane "
        "FROM nodes"
    )
    for r in cursor:
        G.add_node(
            r["id"],
            node_type=r["node_type"],
            layer=r["layer"],
            label=r["label"] or "",
            severity=r["severity"] or 0,
            confidence=r["confidence"] or 0,
            readiness=r["readiness"] or 0,
            binding_strength=r["binding_strength"],
            lane=r["lane"],
        )
        node_count += 1
    log.info(f"  Loaded {node_count:,} nodes in {time.time()-t0:.1f}s")

    # Load edges
    log.info("Loading edges...")
    t0 = time.time()
    edge_count = 0
    cursor = conn.execute(
        "SELECT source_id, target_id, edge_type, weight FROM edges"
    )
    for r in cursor:
        sid = r["source_id"]
        tid = r["target_id"]
        if sid in G and tid in G:
            w = r["weight"] or 0.5
            G.add_edge(sid, tid, edge_type=r["edge_type"], weight=max(0.01, min(1.0, w)))
            edge_count += 1
    log.info(f"  Loaded {edge_count:,} edges in {time.time()-t0:.1f}s")

    return G


def find_chains(G, top_k=10):
    """
    Find strongest evidence chains: VIOLATION → ... → FILING
    Strategy: reverse-Dijkstra from each of 17 filings (instead of 33K calls).
    Cost = -log(weight) so Dijkstra minimizing cost = maximizing product of weights.
    """
    import math
    import networkx as nx

    violation_nodes = [n for n, d in G.nodes(data=True) if d.get("layer") == "VIOLATION"]
    filing_nodes = [n for n, d in G.nodes(data=True) if d.get("layer") == "FILING"]
    evidence_nodes = set(n for n, d in G.nodes(data=True) if d.get("layer") == "EVIDENCE")

    log.info(f"Chain search: {len(violation_nodes)} violations → {len(filing_nodes)} filings")
    log.info(f"  ({len(evidence_nodes)} evidence nodes for path support)")

    if not violation_nodes or not filing_nodes:
        log.warning("No violation or filing nodes — cannot compute chains")
        return [], set()

    # Build reverse graph for backward Dijkstra from filings
    R = G.reverse(copy=False)

    # Precompute cost on forward graph edges: -log(weight) (always >= 0)
    for u, v, d in G.edges(data=True):
        w = d.get("weight", 0.5)
        d["cost"] = -math.log(max(w, 0.001))

    # Also set cost on reverse edges (they reference the same data dicts)
    # Actually since R is a view, edge data is shared — cost is already set.

    chains = []
    reachable_violations = set()
    filing_chain_counts = defaultdict(int)

    t0 = time.time()

    for fi, fn in enumerate(filing_nodes):
        fdata = G.nodes[fn]
        f_label = fdata.get("label", fn)[:60]
        log.info(f"  [{fi+1}/{len(filing_nodes)}] Reverse Dijkstra from: {f_label}")

        # Single-source shortest paths from filing in reverse graph = all-to-filing in forward graph
        try:
            lengths, paths = nx.single_source_dijkstra(R, fn, weight="cost", cutoff=20.0)
        except Exception as e:
            log.warning(f"    Dijkstra failed for {fn}: {e}")
            continue

        v_count = 0
        for vn in violation_nodes:
            if vn not in paths:
                continue

            rev_path = paths[vn]
            path = list(reversed(rev_path))  # violation → ... → filing

            if len(path) < 2:
                continue

            # Score the path
            path_weight = 1.0
            edge_types = []
            for i in range(len(path) - 1):
                if G.has_edge(path[i], path[i + 1]):
                    edata = G.edges[path[i], path[i + 1]]
                    path_weight *= edata.get("weight", 0.5)
                    edge_types.append(edata.get("edge_type", "UNKNOWN"))
                else:
                    edge_types.append("UNKNOWN")
                    path_weight *= 0.3

            vdata = G.nodes[vn]
            severity = (vdata.get("severity", 0) or 0) / 10.0
            confidence = vdata.get("confidence", 0) or 0.5

            max_binding = 0.5
            for node_id in path:
                ndata = G.nodes[node_id]
                if ndata.get("layer") == "AUTHORITY":
                    bs = ndata.get("binding_strength")
                    max_binding = max(max_binding, BINDING_MULT.get(bs, 0.5))

            strength = path_weight * max(severity, 0.1) * max_binding * (0.5 + 0.5 * confidence)

            ev_in_path = [p for p in path if G.nodes[p].get("layer") == "EVIDENCE"]
            lane = vdata.get("lane") or fdata.get("lane") or ""

            chains.append({
                "path": path,
                "edge_types": edge_types,
                "length": len(path),
                "path_weight": path_weight,
                "severity": severity,
                "binding": max_binding,
                "confidence": confidence,
                "strength": strength,
                "violation_id": vn,
                "filing_id": fn,
                "lane": lane,
                "evidence_count": len(ev_in_path),
                "evidence_ids": ev_in_path,
            })
            reachable_violations.add(vn)
            filing_chain_counts[fn] += 1
            v_count += 1

        log.info(f"    → {v_count} violations reached this filing")

    unreachable = set(violation_nodes) - reachable_violations

    elapsed = time.time() - t0
    log.info(f"  Chain search complete in {elapsed:.1f}s")
    log.info(f"  Found {len(chains):,} raw chains")
    log.info(f"  Reachable: {len(reachable_violations)}, Unreachable: {len(unreachable)}")

    # Sort by strength, keep top-K per filing
    chains.sort(key=lambda c: c["strength"], reverse=True)

    top_chains = []
    filing_counts = defaultdict(int)
    for c in chains:
        if filing_counts[c["filing_id"]] < top_k:
            top_chains.append(c)
            filing_counts[c["filing_id"]] += 1

    log.info(f"  Kept {len(top_chains)} top chains (top-{top_k} per filing)")

    for fn, count in sorted(filing_chain_counts.items(), key=lambda x: -x[1])[:20]:
        label = G.nodes[fn].get("label", fn)[:60]
        best = max((c["strength"] for c in top_chains if c["filing_id"] == fn), default=0)
        log.info(f"    {label}: {count} chains, best={best:.4f}")

    return top_chains, unreachable


def store_chains(conn, chains, unreachable):
    """Persist chains and update gaps."""
    log.info("Storing chains...")

    # Clear existing chains
    conn.execute("DELETE FROM chains")

    rows = []
    for c in chains:
        rows.append((
            json.dumps(c["path"]),
            "VIOLATION_TO_FILING",
            c["path_weight"],
            c["length"],
            c["lane"],
            c["filing_id"],
            json.dumps(c["evidence_ids"]),
            c["strength"],
        ))

    conn.executemany(
        """INSERT INTO chains (chain_path, chain_type, total_weight, length, lane, filing_id, evidence_ids, strength_score)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        rows,
    )
    conn.commit()
    log.info(f"  Stored {len(rows)} chains")

    # Update gaps: violations with no path to any filing
    new_gaps = 0
    for vn in unreachable:
        conn.execute(
            """INSERT OR IGNORE INTO gaps (gap_type, node_id, description, priority)
               VALUES ('VIOLATION_UNREACHABLE', ?, 'Violation has no path to any filing', 'HIGH')""",
            (vn,),
        )
        new_gaps += 1
    conn.commit()
    log.info(f"  Added {new_gaps} VIOLATION_UNREACHABLE gaps")

    # Update version
    counts = conn.execute(
        """SELECT
            (SELECT COUNT(*) FROM nodes) as nc,
            (SELECT COUNT(*) FROM edges) as ec,
            (SELECT COUNT(*) FROM chains) as cc,
            (SELECT COUNT(*) FROM gaps) as gc"""
    ).fetchone()
    conn.execute(
        """INSERT INTO versions (node_count, edge_count, chain_count, mutations)
           VALUES (?, ?, ?, ?)""",
        (counts["nc"], counts["ec"], counts["cc"],
         json.dumps({"operation": "compute_chains", "chains_stored": len(rows), "unreachable": len(unreachable)})),
    )
    conn.commit()

    return len(rows)


def print_stats(conn):
    """Print current brain statistics."""
    stats = conn.execute(
        """SELECT
            (SELECT COUNT(*) FROM nodes) as nodes,
            (SELECT COUNT(*) FROM edges) as edges,
            (SELECT COUNT(*) FROM chains) as chains,
            (SELECT COUNT(*) FROM gaps WHERE resolved=0) as gaps"""
    ).fetchone()

    print(f"\n{'='*60}")
    print(f"  THEMANBEARPIG LEGAL BRAIN — STATISTICS")
    print(f"{'='*60}")
    print(f"  Nodes:  {stats['nodes']:>10,}")
    print(f"  Edges:  {stats['edges']:>10,}")
    print(f"  Chains: {stats['chains']:>10,}")
    print(f"  Gaps:   {stats['gaps']:>10,}")

    # Chain strength distribution
    if stats["chains"] > 0:
        dist = conn.execute(
            """SELECT
                COUNT(*) as total,
                AVG(strength_score) as avg_str,
                MAX(strength_score) as max_str,
                MIN(strength_score) as min_str
               FROM chains"""
        ).fetchone()
        print(f"\n  Chain Strength: avg={dist['avg_str']:.4f}, max={dist['max_str']:.4f}, min={dist['min_str']:.6f}")

        # Per-lane breakdown
        print(f"\n  Chains per Lane:")
        for r in conn.execute("SELECT lane, COUNT(*) as cnt, AVG(strength_score) as avg_s FROM chains WHERE lane IS NOT NULL GROUP BY lane ORDER BY cnt DESC"):
            print(f"    Lane {r['lane'] or '?'}: {r['cnt']} chains (avg strength {r['avg_s']:.4f})")

        # Per-filing breakdown
        print(f"\n  Chains per Filing (top 10):")
        for r in conn.execute(
            """SELECT c.filing_id, n.label, COUNT(*) as cnt, MAX(c.strength_score) as best
               FROM chains c LEFT JOIN nodes n ON c.filing_id = n.id
               GROUP BY c.filing_id ORDER BY best DESC LIMIT 10"""
        ):
            label = (r["label"] or r["filing_id"])[:50]
            print(f"    {label}: {r['cnt']} chains, best={r['best']:.4f}")

    # Gap breakdown
    print(f"\n  Gaps by Type:")
    for r in conn.execute("SELECT gap_type, COUNT(*) as cnt FROM gaps WHERE resolved=0 GROUP BY gap_type ORDER BY cnt DESC"):
        print(f"    {r['gap_type']}: {r['cnt']}")

    # Top 5 strongest chains
    if stats["chains"] > 0:
        print(f"\n  Top 5 Strongest Chains:")
        for r in conn.execute(
            """SELECT c.chain_path, c.strength_score, c.length, c.lane, c.filing_id, n.label as filing_label
               FROM chains c LEFT JOIN nodes n ON c.filing_id = n.id
               ORDER BY c.strength_score DESC LIMIT 5"""
        ):
            path = json.loads(r["chain_path"])
            label = (r["filing_label"] or r["filing_id"])[:40]
            print(f"    [{r['lane'] or '?'}] → {label}: strength={r['strength_score']:.4f}, "
                  f"len={r['length']}, path={path[0]}→...→{path[-1]}")

    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(description="Compute legal reasoning chains in mbp_brain.db")
    parser.add_argument("--top", type=int, default=10, help="Top-K chains per filing (default: 10)")
    parser.add_argument("--stats", action="store_true", help="Print stats only, no recompute")
    args = parser.parse_args()

    conn = connect_brain()

    if args.stats:
        print_stats(conn)
        conn.close()
        return

    t_start = time.time()

    # Load into NetworkX
    G = load_graph(conn)

    # Find chains
    chains, unreachable = find_chains(G, top_k=args.top)

    # Store results
    stored = store_chains(conn, chains, unreachable)

    elapsed = time.time() - t_start
    log.info(f"\nChain computation complete in {elapsed:.1f}s")
    log.info(f"  Stored {stored} chains, {len(unreachable)} unreachable violations")

    # Print stats
    print_stats(conn)

    conn.close()


if __name__ == "__main__":
    main()
