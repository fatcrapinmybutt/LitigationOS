#!/usr/bin/env python3
"""compute_communities.py — Leiden hierarchical clustering for THEMANBEARPIG v15.0.

Loads the full graph from mbp_brain.db (71K nodes, 235K edges), runs Leiden
community detection at multiple resolutions, builds a 4-level hierarchy
(Lane → Epoch → Community → Individual), computes DuckDB analytics, and
exports a Sigma.js-ready hierarchical JSON.

Usage:
    python -I scripts/compute_communities.py
    python -I scripts/compute_communities.py --prune-threshold 3000
    python -I scripts/compute_communities.py --resolutions 0.5 1.0 2.0
"""
import argparse
import json
import math
import os
import sqlite3
import sys
import time
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BRAIN_DB = REPO_ROOT / "mbp_brain.db"
LIT_DB = REPO_ROOT / "litigation_context.db"
OUTPUT_DIR = REPO_ROOT / "08_MEDIA" / "MANBEARPIG_V15"
GRAPH_JSON = OUTPUT_DIR / "graph_clusters.json"
SEPARATION_DATE = date(2025, 7, 29)

LANE_COLORS = {
    "A": "#4ecdc4", "B": "#ffd93d", "C": "#ff6b6b",
    "D": "#9b59b6", "E": "#ff4444", "F": "#4d96ff",
}
EDGE_TYPE_WEIGHT = {
    "PROVES": 5.0, "CONTRADICTS": 4.0, "GOVERNED_BY": 3.0,
    "CITES": 2.0, "RELATED": 1.0,
}


def get_conn(db_path):
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    conn.execute("PRAGMA mmap_size=268435456")
    return conn


def load_graph(conn, prune_threshold=5000):
    """Load full graph into igraph, pruning mega-hubs."""
    import igraph as ig

    t0 = time.time()
    print("[1/8] Loading nodes...")
    nodes_raw = conn.execute(
        "SELECT id, node_type, layer, label, lane, date_start, date_end, "
        "severity, confidence, readiness FROM nodes"
    ).fetchall()

    # Build node index
    node_map = {}  # id -> index
    node_attrs = []
    for i, r in enumerate(nodes_raw):
        node_map[r["id"]] = i
        node_attrs.append({
            "name": r["id"],
            "node_type": r["node_type"] or "",
            "layer": r["layer"] or "EVIDENCE",
            "label": (r["label"] or "")[:200],
            "lane": r["lane"] or "",
            "date_start": r["date_start"] or "",
            "date_end": r["date_end"] or "",
            "severity": r["severity"] or 0,
            "confidence": r["confidence"] or 0,
            "readiness": r["readiness"] or 0,
        })
    print(f"  {len(node_attrs):,} nodes loaded ({time.time()-t0:.1f}s)")

    # Compute edge counts for pruning
    print("[2/8] Computing edge counts for hub pruning...")
    edge_counts = Counter()
    for row in conn.execute(
        "SELECT source_id, target_id FROM edges WHERE source_id != '' AND target_id != ''"
    ):
        edge_counts[row["source_id"]] += 1
        edge_counts[row["target_id"]] += 1

    mega_hubs = {nid for nid, cnt in edge_counts.items() if cnt > prune_threshold}
    if mega_hubs:
        print(f"  Pruning {len(mega_hubs)} mega-hubs (>{prune_threshold} edges)")

    print("[3/8] Loading edges...")
    edges_raw = conn.execute(
        "SELECT source_id, target_id, edge_type, weight "
        "FROM edges WHERE source_id != '' AND target_id != ''"
    ).fetchall()

    edge_list = []
    edge_weights = []
    edge_types = []
    skipped = 0
    for r in edges_raw:
        sid, tid = r["source_id"], r["target_id"]
        if sid in mega_hubs or tid in mega_hubs:
            skipped += 1
            continue
        si = node_map.get(sid)
        ti = node_map.get(tid)
        if si is not None and ti is not None and si != ti:
            etype = r["edge_type"] or "RELATED"
            w = (r["weight"] or 0.5) * EDGE_TYPE_WEIGHT.get(etype, 1.0)
            edge_list.append((si, ti))
            edge_weights.append(min(w, 10.0))
            edge_types.append(etype)

    print(f"  {len(edge_list):,} edges loaded, {skipped:,} pruned ({time.time()-t0:.1f}s)")

    # Build igraph
    print("[4/8] Building igraph graph...")
    g = ig.Graph(n=len(node_attrs), edges=edge_list, directed=False)
    g.es["weight"] = edge_weights
    g.es["type"] = edge_types
    for attr_key in ("name", "node_type", "layer", "label", "lane",
                     "date_start", "date_end", "severity", "confidence", "readiness"):
        g.vs[attr_key] = [a[attr_key] for a in node_attrs]

    print(f"  igraph: {g.vcount():,} vertices, {g.ecount():,} edges ({time.time()-t0:.1f}s)")
    return g, node_map


def run_leiden(g, resolution=1.0):
    """Run Leiden community detection."""
    import leidenalg

    t0 = time.time()
    print(f"[5/8] Running Leiden (resolution={resolution})...")
    partition = leidenalg.find_partition(
        g, leidenalg.RBConfigurationVertexPartition,
        weights="weight", resolution_parameter=resolution,
        n_iterations=10, seed=42,
    )
    quality = partition.quality()
    n_communities = len(partition)
    print(f"  {n_communities} communities, quality={quality:.2f} ({time.time()-t0:.1f}s)")
    return partition


def build_hierarchy(g, partition):
    """Build 4-level hierarchy: Lane → Epoch → Community → Individual.

    Level 0: Lane supernodes (A, B, C, D, E, F + unknown)
    Level 1: Epoch nodes (quarterly buckets within each lane)
    Level 2: Leiden community nodes
    Level 3: Individual nodes (loaded on demand)
    """
    t0 = time.time()
    print("[6/8] Building 4-level hierarchy...")

    membership = partition.membership
    communities = defaultdict(list)
    for vi, cid in enumerate(membership):
        communities[cid].append(vi)

    # --- Level 2: Leiden communities with metadata ---
    level2 = {}
    for cid, members in communities.items():
        if len(members) < 2:
            continue  # skip singletons

        lanes = Counter(g.vs[vi]["lane"] for vi in members if g.vs[vi]["lane"])
        types = Counter(g.vs[vi]["node_type"] for vi in members)
        primary_lane = lanes.most_common(1)[0][0] if lanes else "?"

        dates = []
        for vi in members:
            ds = g.vs[vi]["date_start"]
            if ds and len(ds) >= 7:
                try:
                    dates.append(ds[:7])  # YYYY-MM
                except (ValueError, IndexError):
                    pass
        dates.sort()
        date_start = dates[0] if dates else ""
        date_end = dates[-1] if dates else ""

        # Epoch bucket (quarterly)
        if date_start and len(date_start) >= 7:
            try:
                y, m = int(date_start[:4]), int(date_start[5:7])
                q = (m - 1) // 3 + 1
                epoch = f"{y}Q{q}"
            except (ValueError, IndexError):
                epoch = "undated"
        else:
            epoch = "undated"

        # Top labels for community summary
        label_candidates = []
        for vi in sorted(members, key=lambda v: g.vs[v]["severity"] + g.vs[v]["confidence"], reverse=True)[:5]:
            lbl = g.vs[vi]["label"]
            if lbl and len(lbl) > 5:
                label_candidates.append(lbl)
        summary = label_candidates[0] if label_candidates else f"Community {cid}"

        # Scores
        avg_severity = sum(g.vs[vi]["severity"] for vi in members) / len(members) if members else 0
        avg_confidence = sum(g.vs[vi]["confidence"] for vi in members) / len(members) if members else 0

        # Internal edge density
        member_set = set(members)
        internal_edges = sum(
            1 for vi in members
            for ni in g.neighbors(vi)
            if ni in member_set
        ) / 2

        level2[cid] = {
            "id": f"c_{cid}",
            "level": 2,
            "parent_epoch": f"{primary_lane}_{epoch}",
            "parent_lane": primary_lane,
            "label": summary[:120],
            "member_count": len(members),
            "node_type_dist": dict(types.most_common(5)),
            "lane": primary_lane,
            "date_start": date_start,
            "date_end": date_end,
            "epoch": epoch,
            "evidence_strength": round(avg_severity, 3),
            "authority_completeness": round(avg_confidence, 3),
            "internal_edges": int(internal_edges),
            "top_labels": label_candidates[:5],
            "members": members,  # vertex indices (for edge computation)
        }

    # --- Level 1: Epochs (quarterly buckets within lane) ---
    level1 = defaultdict(lambda: {
        "member_communities": [], "member_count": 0,
        "node_type_dist": Counter(), "evidence_strength": 0,
    })
    for cid, info in level2.items():
        eid = info["parent_epoch"]
        level1[eid]["member_communities"].append(cid)
        level1[eid]["member_count"] += info["member_count"]
        level1[eid]["node_type_dist"].update(info["node_type_dist"])
        level1[eid]["evidence_strength"] += info["evidence_strength"] * info["member_count"]

    epoch_nodes = {}
    for eid, edata in level1.items():
        parts = eid.split("_", 1)
        lane = parts[0] if len(parts) > 1 else "?"
        epoch = parts[1] if len(parts) > 1 else eid
        mc = edata["member_count"] or 1
        epoch_nodes[eid] = {
            "id": f"e_{eid}",
            "level": 1,
            "parent_lane": lane,
            "label": f"{lane} — {epoch}",
            "member_count": edata["member_count"],
            "community_count": len(edata["member_communities"]),
            "node_type_dist": dict(edata["node_type_dist"].most_common(5)),
            "lane": lane,
            "epoch": epoch,
            "evidence_strength": round(edata["evidence_strength"] / mc, 3),
        }

    # --- Level 0: Lane supernodes ---
    lane_nodes = {}
    for lane_code in set(info["lane"] for info in level2.values()):
        if not lane_code:
            continue
        lane_comms = [c for c in level2.values() if c["lane"] == lane_code]
        total_members = sum(c["member_count"] for c in lane_comms)
        types_agg = Counter()
        for c in lane_comms:
            types_agg.update(c["node_type_dist"])
        lane_nodes[lane_code] = {
            "id": f"lane_{lane_code}",
            "level": 0,
            "label": f"Lane {lane_code}",
            "member_count": total_members,
            "community_count": len(lane_comms),
            "node_type_dist": dict(types_agg.most_common(5)),
            "lane": lane_code,
            "color": LANE_COLORS.get(lane_code, "#888888"),
        }

    print(f"  Level 0 (lanes): {len(lane_nodes)}")
    print(f"  Level 1 (epochs): {len(epoch_nodes)}")
    print(f"  Level 2 (communities): {len(level2)}")
    print(f"  ({time.time()-t0:.1f}s)")

    return lane_nodes, epoch_nodes, level2


def compute_inter_community_edges(g, level2):
    """Compute edges between communities (aggregated)."""
    t0 = time.time()
    print("[7/8] Computing inter-community edges...")

    # Build node → community map
    node_to_comm = {}
    for cid, info in level2.items():
        for vi in info["members"]:
            node_to_comm[vi] = cid

    inter_edges = defaultdict(lambda: {"weight": 0, "count": 0, "types": Counter()})
    for e in g.es:
        src_c = node_to_comm.get(e.source)
        tgt_c = node_to_comm.get(e.target)
        if src_c is not None and tgt_c is not None and src_c != tgt_c:
            key = (min(src_c, tgt_c), max(src_c, tgt_c))
            inter_edges[key]["weight"] += e["weight"]
            inter_edges[key]["count"] += 1
            inter_edges[key]["types"][e["type"]] += 1

    comm_edges = []
    for (s, t), data in inter_edges.items():
        top_type = data["types"].most_common(1)[0][0] if data["types"] else "RELATED"
        comm_edges.append({
            "source": f"c_{s}",
            "target": f"c_{t}",
            "weight": round(data["weight"], 2),
            "count": data["count"],
            "type": top_type,
        })

    # Also compute epoch-level and lane-level edges
    epoch_edges_map = defaultdict(lambda: {"weight": 0, "count": 0})
    lane_edges_map = defaultdict(lambda: {"weight": 0, "count": 0})
    for (s, t), data in inter_edges.items():
        se = level2[s]["parent_epoch"]
        te = level2[t]["parent_epoch"]
        if se != te:
            ek = (min(se, te), max(se, te))
            epoch_edges_map[ek]["weight"] += data["weight"]
            epoch_edges_map[ek]["count"] += data["count"]

        sl = level2[s]["parent_lane"]
        tl = level2[t]["parent_lane"]
        if sl != tl:
            lk = (min(sl, tl), max(sl, tl))
            lane_edges_map[lk]["weight"] += data["weight"]
            lane_edges_map[lk]["count"] += data["count"]

    epoch_edges = [
        {"source": f"e_{s}", "target": f"e_{t}",
         "weight": round(d["weight"], 2), "count": d["count"]}
        for (s, t), d in epoch_edges_map.items()
    ]
    lane_edges = [
        {"source": f"lane_{s}", "target": f"lane_{t}",
         "weight": round(d["weight"], 2), "count": d["count"]}
        for (s, t), d in lane_edges_map.items()
    ]

    print(f"  Community edges: {len(comm_edges):,}")
    print(f"  Epoch edges: {len(epoch_edges):,}")
    print(f"  Lane edges: {len(lane_edges):,}")
    print(f"  ({time.time()-t0:.1f}s)")

    return comm_edges, epoch_edges, lane_edges


def compute_pagerank(g):
    """Compute PageRank via igraph (much faster than DuckDB CTE for this)."""
    print("  Computing PageRank...")
    pr = g.pagerank(weights="weight")
    return pr


def export_sigma_json(lane_nodes, epoch_nodes, level2, comm_edges, epoch_edges,
                      lane_edges, g, pagerank):
    """Export hierarchical Sigma.js-ready JSON."""
    t0 = time.time()
    print("[8/8] Exporting Sigma.js JSON...")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Build sigma nodes — community supernodes for default view
    sigma_nodes = []

    # Lane supernodes
    for lane_code, info in lane_nodes.items():
        sigma_nodes.append({
            "key": info["id"],
            "attributes": {
                "label": info["label"],
                "x": hash(lane_code) % 1000 / 100,
                "y": hash(lane_code + "y") % 1000 / 100,
                "size": math.sqrt(info["member_count"]) * 0.5,
                "color": info.get("color", "#888"),
                "level": 0,
                "lane": lane_code,
                "member_count": info["member_count"],
                "community_count": info["community_count"],
                "node_type_dist": info["node_type_dist"],
                "type": "lane",
            }
        })

    # Epoch supernodes
    for eid, info in epoch_nodes.items():
        lane = info["lane"]
        sigma_nodes.append({
            "key": info["id"],
            "attributes": {
                "label": info["label"],
                "x": hash(eid) % 2000 / 100,
                "y": hash(eid + "y") % 2000 / 100,
                "size": math.sqrt(info["member_count"]) * 0.3,
                "color": LANE_COLORS.get(lane, "#888"),
                "level": 1,
                "lane": lane,
                "epoch": info["epoch"],
                "member_count": info["member_count"],
                "community_count": info["community_count"],
                "parent": f"lane_{lane}",
                "type": "epoch",
            }
        })

    # Community supernodes
    for cid, info in level2.items():
        lane = info["lane"]
        # Aggregate PageRank for community
        pr_sum = sum(pagerank[vi] for vi in info["members"]) if pagerank else 0

        sigma_nodes.append({
            "key": info["id"],
            "attributes": {
                "label": info["label"],
                "x": hash(str(cid)) % 3000 / 100,
                "y": hash(str(cid) + "y") % 3000 / 100,
                "size": math.sqrt(info["member_count"]) * 0.2 + 1,
                "color": LANE_COLORS.get(lane, "#888"),
                "level": 2,
                "lane": lane,
                "date_start": info["date_start"],
                "date_end": info["date_end"],
                "epoch": info["epoch"],
                "member_count": info["member_count"],
                "node_type_dist": info["node_type_dist"],
                "evidence_strength": info["evidence_strength"],
                "authority_completeness": info["authority_completeness"],
                "internal_edges": info["internal_edges"],
                "pagerank_sum": round(pr_sum, 6),
                "top_labels": info["top_labels"],
                "parent": f"e_{info['parent_epoch']}",
                "type": "community",
            }
        })

    # Build sigma edges for all levels
    sigma_edges = []
    edge_id = 0
    for e in lane_edges:
        sigma_edges.append({
            "key": f"le_{edge_id}",
            "source": e["source"], "target": e["target"],
            "attributes": {"weight": e["weight"], "count": e["count"], "level": 0}
        })
        edge_id += 1
    for e in epoch_edges:
        sigma_edges.append({
            "key": f"ee_{edge_id}",
            "source": e["source"], "target": e["target"],
            "attributes": {"weight": e["weight"], "count": e["count"], "level": 1}
        })
        edge_id += 1
    for e in comm_edges:
        sigma_edges.append({
            "key": f"ce_{edge_id}",
            "source": e["source"], "target": e["target"],
            "attributes": {
                "weight": e["weight"], "count": e["count"],
                "type": e.get("type", "RELATED"), "level": 2,
            }
        })
        edge_id += 1

    # Build detail_nodes: individual nodes per community (loaded on demand)
    detail_nodes = {}
    for cid, info in level2.items():
        comm_members = []
        for vi in info["members"]:
            comm_members.append({
                "key": g.vs[vi]["name"],
                "label": g.vs[vi]["label"][:120],
                "type": g.vs[vi]["node_type"],
                "lane": g.vs[vi]["lane"],
                "severity": round(g.vs[vi]["severity"], 3),
                "confidence": round(g.vs[vi]["confidence"], 3),
                "date": g.vs[vi]["date_start"] or "",
                "pagerank": round(pagerank[vi], 8) if pagerank else 0,
            })
        comm_members.sort(key=lambda x: x.get("pagerank", 0), reverse=True)
        detail_nodes[f"c_{cid}"] = comm_members[:200]  # cap per community

    # Compute stats
    sep_days = (date.today() - SEPARATION_DATE).days

    output = {
        "version": "15.0.0",
        "generated": datetime.now().isoformat(),
        "separation_days": sep_days,
        "stats": {
            "total_nodes": g.vcount(),
            "total_edges": g.ecount(),
            "lanes": len(lane_nodes),
            "epochs": len(epoch_nodes),
            "communities": len(level2),
            "sigma_nodes": len(sigma_nodes),
            "sigma_edges": len(sigma_edges),
        },
        "nodes": sigma_nodes,
        "edges": sigma_edges,
        "detail_nodes": detail_nodes,
    }

    with open(str(GRAPH_JSON), "w", encoding="utf-8") as f:
        json.dump(output, f, separators=(",", ":"))

    size_mb = GRAPH_JSON.stat().st_size / 1024 / 1024
    print(f"  Output: {GRAPH_JSON}")
    print(f"  Size: {size_mb:.1f} MB")
    print(f"  Sigma nodes: {len(sigma_nodes):,} (L0={len(lane_nodes)}, L1={len(epoch_nodes)}, L2={len(level2)})")
    print(f"  Sigma edges: {len(sigma_edges):,}")
    print(f"  Detail communities: {len(detail_nodes):,}")
    total_detail = sum(len(v) for v in detail_nodes.values())
    print(f"  Detail nodes: {total_detail:,}")
    print(f"  ({time.time()-t0:.1f}s)")

    return output


def store_in_brain_db(conn, lane_nodes, epoch_nodes, level2, pagerank, g):
    """Persist communities and analytics back to mbp_brain.db."""
    print("  Storing communities in brain DB...")
    conn.execute("DROP TABLE IF EXISTS communities")
    conn.execute("""
        CREATE TABLE communities (
            id TEXT PRIMARY KEY, parent_id TEXT, level INTEGER NOT NULL,
            lane TEXT, date_start TEXT, date_end TEXT, label TEXT NOT NULL,
            member_count INTEGER DEFAULT 0, node_type_dist TEXT,
            evidence_strength REAL DEFAULT 0, authority_completeness REAL DEFAULT 0,
            pagerank_sum REAL DEFAULT 0, epoch TEXT, top_labels TEXT
        )
    """)
    conn.execute("DROP TABLE IF EXISTS community_edges")
    conn.execute("""
        CREATE TABLE community_edges (
            source_id TEXT, target_id TEXT, edge_type TEXT,
            total_weight REAL DEFAULT 0, edge_count INTEGER DEFAULT 0,
            PRIMARY KEY (source_id, target_id, edge_type)
        )
    """)
    conn.execute("DROP TABLE IF EXISTS community_members")
    conn.execute("""
        CREATE TABLE community_members (
            node_id TEXT, community_id TEXT,
            PRIMARY KEY (node_id, community_id)
        )
    """)
    conn.execute("DROP TABLE IF EXISTS node_analytics")
    conn.execute("""
        CREATE TABLE node_analytics (
            node_id TEXT PRIMARY KEY, pagerank REAL DEFAULT 0
        )
    """)

    # Insert lane nodes
    for lc, info in lane_nodes.items():
        conn.execute(
            "INSERT INTO communities (id, parent_id, level, lane, label, member_count, node_type_dist) "
            "VALUES (?,?,?,?,?,?,?)",
            (info["id"], None, 0, lc, info["label"], info["member_count"],
             json.dumps(info["node_type_dist"]))
        )
    # Insert epoch nodes
    for eid, info in epoch_nodes.items():
        conn.execute(
            "INSERT INTO communities (id, parent_id, level, lane, label, member_count, "
            "node_type_dist, epoch, evidence_strength) VALUES (?,?,?,?,?,?,?,?,?)",
            (info["id"], f"lane_{info['lane']}", 1, info["lane"], info["label"],
             info["member_count"], json.dumps(info["node_type_dist"]),
             info["epoch"], info["evidence_strength"])
        )
    # Insert community nodes
    for cid, info in level2.items():
        pr_sum = sum(pagerank[vi] for vi in info["members"]) if pagerank else 0
        conn.execute(
            "INSERT INTO communities (id, parent_id, level, lane, date_start, date_end, "
            "label, member_count, node_type_dist, evidence_strength, authority_completeness, "
            "pagerank_sum, epoch, top_labels) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (info["id"], f"e_{info['parent_epoch']}", 2, info["lane"],
             info["date_start"], info["date_end"], info["label"],
             info["member_count"], json.dumps(info["node_type_dist"]),
             info["evidence_strength"], info["authority_completeness"],
             round(pr_sum, 6), info["epoch"], json.dumps(info["top_labels"]))
        )
    # Insert community members
    member_rows = []
    for cid, info in level2.items():
        for vi in info["members"]:
            member_rows.append((g.vs[vi]["name"], info["id"]))
    conn.executemany(
        "INSERT OR IGNORE INTO community_members (node_id, community_id) VALUES (?,?)",
        member_rows
    )
    # Insert PageRank
    pr_rows = [(g.vs[vi]["name"], round(pagerank[vi], 10)) for vi in range(g.vcount())]
    conn.executemany(
        "INSERT OR IGNORE INTO node_analytics (node_id, pagerank) VALUES (?,?)",
        pr_rows
    )
    conn.commit()
    print(f"  Stored: {len(lane_nodes)} lanes, {len(epoch_nodes)} epochs, "
          f"{len(level2)} communities, {len(member_rows):,} memberships, "
          f"{len(pr_rows):,} PageRank scores")


def main():
    parser = argparse.ArgumentParser(description="THEMANBEARPIG v15.0 Leiden clustering")
    parser.add_argument("--prune-threshold", type=int, default=5000,
                        help="Prune nodes with more edges than this (default: 5000)")
    parser.add_argument("--resolution", type=float, default=1.0,
                        help="Leiden resolution parameter (default: 1.0)")
    args = parser.parse_args()

    print("=" * 70)
    print("THEMANBEARPIG v15.0 — Leiden Hierarchical Intelligence Graph")
    print("=" * 70)
    total_t0 = time.time()

    conn = get_conn(BRAIN_DB)

    # Load and build igraph
    g, node_map = load_graph(conn, prune_threshold=args.prune_threshold)

    # Leiden clustering
    partition = run_leiden(g, resolution=args.resolution)

    # Build hierarchy
    lane_nodes, epoch_nodes, level2 = build_hierarchy(g, partition)

    # Compute inter-community edges
    comm_edges, epoch_edges, lane_edges = compute_inter_community_edges(g, level2)

    # PageRank
    pagerank = compute_pagerank(g)

    # Export Sigma.js JSON
    export_sigma_json(lane_nodes, epoch_nodes, level2, comm_edges, epoch_edges,
                      lane_edges, g, pagerank)

    # Store in brain DB
    store_in_brain_db(conn, lane_nodes, epoch_nodes, level2, pagerank, g)

    conn.close()

    elapsed = time.time() - total_t0
    print(f"\n✅ Complete in {elapsed:.1f}s")
    print(f"Output: {GRAPH_JSON}")


if __name__ == "__main__":
    main()
