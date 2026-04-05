#!/usr/bin/env python3
"""Compute HITS (hub/authority) scores via igraph and store in node_analytics.

Completes the graph analytics pipeline:
- PageRank: already computed by compute_communities.py
- HITS hub/authority: computed here
- Degree centrality: computed here

Uses igraph C library — 10-100× faster than NetworkX Python.
"""
import sqlite3
import sys
import time
from pathlib import Path

BRAIN_DB = Path(__file__).resolve().parent.parent / "mbp_brain.db"
PRAGMAS = [
    "PRAGMA busy_timeout=60000",
    "PRAGMA journal_mode=WAL",
    "PRAGMA cache_size=-32000",
    "PRAGMA synchronous=NORMAL",
    "PRAGMA temp_store=MEMORY",
]


def main():
    t0 = time.perf_counter()
    print("=== HITS + Degree Centrality via igraph ===")

    try:
        import igraph as ig
    except ImportError:
        print("ERROR: igraph not installed. Run: pip install igraph")
        sys.exit(1)

    conn = sqlite3.connect(str(BRAIN_DB))
    for p in PRAGMAS:
        conn.execute(p)

    # Load nodes and edges
    print("Loading graph from brain DB...")
    nodes = conn.execute("SELECT id FROM nodes").fetchall()
    node_ids = [r[0] for r in nodes]
    node_idx = {nid: i for i, nid in enumerate(node_ids)}
    N = len(node_ids)
    print(f"  {N:,} nodes loaded")

    edges = conn.execute("SELECT source_id, target_id, weight FROM edges").fetchall()
    edge_list = []
    weights = []
    for src, tgt, w in edges:
        si = node_idx.get(src)
        ti = node_idx.get(tgt)
        if si is not None and ti is not None:
            edge_list.append((si, ti))
            weights.append(w if w else 1.0)
    print(f"  {len(edge_list):,} edges loaded")

    # Build igraph graph
    g = ig.Graph(n=N, edges=edge_list, directed=True)
    g.es["weight"] = weights

    # Compute HITS (hub_score, authority_score)
    print("Computing HITS scores...")
    t1 = time.perf_counter()
    auth_scores = g.authority_score(weights="weight")
    hub_scores = g.hub_score(weights="weight")
    print(f"  HITS computed in {time.perf_counter()-t1:.2f}s")

    # Compute degree centrality (in-degree + out-degree normalized)
    print("Computing degree centrality...")
    in_deg = g.indegree()
    out_deg = g.outdegree()
    max_deg = max(max(in_deg), max(out_deg), 1)
    degree_cent = [(ind + outd) / (2 * max_deg) for ind, outd in zip(in_deg, out_deg)]

    # Update node_analytics table — add missing columns
    print("Updating node_analytics table...")
    cols = {r[1] for r in conn.execute("PRAGMA table_info(node_analytics)")}
    for col in ["hub_score", "authority_score", "betweenness_centrality"]:
        if col not in cols:
            conn.execute(f"ALTER TABLE node_analytics ADD COLUMN {col} REAL DEFAULT 0")
            print(f"  Added column: {col}")

    batch = []
    for i, nid in enumerate(node_ids):
        batch.append((hub_scores[i], auth_scores[i], degree_cent[i], nid))

    conn.execute("BEGIN")
    conn.executemany("""
        UPDATE node_analytics
        SET hub_score = ?, authority_score = ?, betweenness_centrality = ?
        WHERE node_id = ?
    """, batch)
    updated = conn.execute("SELECT changes()").fetchone()[0]

    # Insert any nodes not yet in the table
    if updated < N:
        existing = {r[0] for r in conn.execute("SELECT node_id FROM node_analytics")}
        inserts = []
        for i, nid in enumerate(node_ids):
            if nid not in existing:
                inserts.append((nid, 0.0, degree_cent[i], hub_scores[i], auth_scores[i]))
        if inserts:
            conn.executemany("""
                INSERT INTO node_analytics (node_id, pagerank, betweenness_centrality, hub_score, authority_score)
                VALUES (?, ?, ?, ?, ?)
            """, inserts)
            print(f"  Inserted {len(inserts)} new rows")

    conn.commit()
    final = conn.execute("SELECT COUNT(*) FROM node_analytics WHERE hub_score > 0").fetchone()[0]
    print(f"  {final:,} nodes with HITS scores")

    # Quick stats
    top_hubs = conn.execute("""
        SELECT na.node_id, n.label, na.hub_score
        FROM node_analytics na JOIN nodes n ON na.node_id = n.id
        ORDER BY na.hub_score DESC LIMIT 5
    """).fetchall()
    print("\nTop 5 Hub Nodes:")
    for nid, label, score in top_hubs:
        print(f"  {score:.6f} | {label[:80]}")

    top_auth = conn.execute("""
        SELECT na.node_id, n.label, na.authority_score
        FROM node_analytics na JOIN nodes n ON na.node_id = n.id
        ORDER BY na.authority_score DESC LIMIT 5
    """).fetchall()
    print("\nTop 5 Authority Nodes:")
    for nid, label, score in top_auth:
        print(f"  {score:.6f} | {label[:80]}")

    conn.close()
    print(f"\n=== Done in {time.perf_counter()-t0:.2f}s ===")


if __name__ == "__main__":
    main()
