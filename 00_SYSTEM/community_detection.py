#!/usr/bin/env python3
"""
community_detection.py -- NetworkX Community Detection + Node Analytics for mbp_brain.db

Populates:
  1. communities + community_members (Louvain community detection)
  2. node_analytics (PageRank, betweenness centrality, degree, hub/authority scores)
  3. chains (evidence -> authority -> remedy -> filing chains)
  4. detected_patterns (retaliation, escalation, conspiracy, coordination)

Requires: networkx, python-louvain (community)
Uses: ~774K edges, ~235K nodes from mbp_brain.db

Author: THEMANBEARPIG SINGULARITY v20.0.0
"""

import sqlite3
import sys
import time
import json
from pathlib import Path
from collections import defaultdict, Counter

BRAIN_DB = Path(r"C:\Users\andre\LitigationOS\mbp_brain.db")


def connect():
    conn = sqlite3.connect(str(BRAIN_DB))
    conn.execute("PRAGMA busy_timeout = 60000")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA cache_size = -64000")
    conn.execute("PRAGMA temp_store = MEMORY")
    conn.execute("PRAGMA synchronous = NORMAL")
    return conn


def create_tables(conn):
    """Create tables for communities, node_analytics, detected_patterns."""
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS communities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        community_id INTEGER NOT NULL,
        label TEXT,
        node_count INTEGER DEFAULT 0,
        dominant_type TEXT,
        dominant_lane TEXT,
        avg_severity REAL DEFAULT 0,
        density REAL DEFAULT 0,
        key_nodes TEXT,
        legal_significance TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS community_members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        community_id INTEGER NOT NULL,
        node_id TEXT NOT NULL,
        membership_score REAL DEFAULT 1.0,
        UNIQUE(community_id, node_id)
    );

    CREATE TABLE IF NOT EXISTS node_analytics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        node_id TEXT NOT NULL UNIQUE,
        pagerank REAL DEFAULT 0,
        betweenness REAL DEFAULT 0,
        degree_in INTEGER DEFAULT 0,
        degree_out INTEGER DEFAULT 0,
        degree_total INTEGER DEFAULT 0,
        hub_score REAL DEFAULT 0,
        authority_score REAL DEFAULT 0,
        community_id INTEGER,
        is_bridge INTEGER DEFAULT 0,
        is_keystone INTEGER DEFAULT 0,
        legal_centrality REAL DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS detected_patterns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pattern_type TEXT NOT NULL,
        description TEXT NOT NULL,
        actors TEXT,
        evidence_ids TEXT,
        confidence REAL DEFAULT 0,
        severity REAL DEFAULT 0,
        lane TEXT,
        start_date TEXT,
        end_date TEXT,
        node_ids TEXT,
        edge_ids TEXT,
        filing_relevance TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    );

    CREATE INDEX IF NOT EXISTS idx_community_members_cid ON community_members(community_id);
    CREATE INDEX IF NOT EXISTS idx_community_members_nid ON community_members(node_id);
    CREATE INDEX IF NOT EXISTS idx_node_analytics_pr ON node_analytics(pagerank DESC);
    CREATE INDEX IF NOT EXISTS idx_node_analytics_bc ON node_analytics(betweenness DESC);
    CREATE INDEX IF NOT EXISTS idx_node_analytics_lc ON node_analytics(legal_centrality DESC);
    CREATE INDEX IF NOT EXISTS idx_detected_patterns_type ON detected_patterns(pattern_type);
    CREATE INDEX IF NOT EXISTS idx_detected_patterns_conf ON detected_patterns(confidence DESC);
    """)
    conn.commit()
    print("[OK] Tables created: communities, community_members, node_analytics, detected_patterns")


def build_graph(conn):
    """Build NetworkX DiGraph from brain edges (sampled for performance)."""
    import networkx as nx

    t0 = time.perf_counter()
    G = nx.DiGraph()

    # Load all nodes with metadata
    print("  Loading nodes...")
    node_rows = conn.execute(
        "SELECT id, node_type, layer, label, lane, severity FROM nodes"
    ).fetchall()
    for nid, ntype, layer, label, lane, sev in node_rows:
        G.add_node(nid, node_type=ntype, layer=layer, label=label or "",
                   lane=lane or "", severity=sev or 0)
    print(f"  Loaded {G.number_of_nodes()} nodes")

    # Load edges -- for community detection we use all edges
    # but for centrality we'll subsample if needed
    print("  Loading edges...")
    edge_rows = conn.execute(
        "SELECT source_id, target_id, edge_type, weight FROM edges"
    ).fetchall()
    for src, tgt, etype, wt in edge_rows:
        if src in G and tgt in G:
            G.add_edge(src, tgt, edge_type=etype, weight=wt or 0.5)
    print(f"  Loaded {G.number_of_edges()} edges")

    elapsed = time.perf_counter() - t0
    print(f"  Graph built in {elapsed:.1f}s: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    return G


def run_community_detection(G, conn):
    """Louvain community detection on undirected projection."""
    try:
        import community as community_louvain
    except ImportError:
        try:
            from community import community_louvain
        except ImportError:
            print("  [WARN] python-louvain not available, using connected components instead")
            return run_component_communities(G, conn)

    import networkx as nx
    t0 = time.perf_counter()

    # Convert to undirected for Louvain
    print("  Converting to undirected for Louvain...")
    G_undirected = G.to_undirected()

    # For very large graphs, sample to avoid OOM
    node_count = G_undirected.number_of_nodes()
    if node_count > 50000:
        print(f"  Graph has {node_count} nodes -- sampling top 50K by degree for Louvain...")
        degrees = sorted(G_undirected.degree(), key=lambda x: x[1], reverse=True)
        keep_nodes = set(n for n, d in degrees[:50000])
        G_sample = G_undirected.subgraph(keep_nodes).copy()
    else:
        G_sample = G_undirected

    print(f"  Running Louvain on {G_sample.number_of_nodes()} nodes...")
    partition = community_louvain.best_partition(G_sample, resolution=1.0, random_state=42)

    # Gather communities
    comm_nodes = defaultdict(list)
    for node_id, comm_id in partition.items():
        comm_nodes[comm_id].append(node_id)

    # Filter to communities with >=3 members
    significant = {cid: members for cid, members in comm_nodes.items() if len(members) >= 3}
    print(f"  Found {len(significant)} communities (>= 3 members) from {len(comm_nodes)} total")

    # Clear old data
    conn.execute("DELETE FROM communities")
    conn.execute("DELETE FROM community_members")

    # Insert communities
    comm_rows = []
    member_rows = []
    for cid, members in significant.items():
        # Analyze community composition
        types = Counter()
        lanes = Counter()
        total_sev = 0
        for nid in members:
            if nid in G.nodes:
                nd = G.nodes[nid]
                types[nd.get('node_type', 'unknown')] += 1
                if nd.get('lane'):
                    lanes[nd['lane']] += 1
                total_sev += nd.get('severity', 0)

        dominant_type = types.most_common(1)[0][0] if types else 'unknown'
        dominant_lane = lanes.most_common(1)[0][0] if lanes else None
        avg_sev = total_sev / max(len(members), 1)

        # Key nodes (top 5 by degree in community subgraph)
        sub = G_sample.subgraph(members)
        top_nodes = sorted(sub.degree(), key=lambda x: x[1], reverse=True)[:5]
        key_nodes = json.dumps([n for n, d in top_nodes])

        # Density
        density = nx.density(sub) if len(members) > 1 else 0

        # Legal significance label
        if dominant_type == 'VIOLATION' and avg_sev > 3:
            sig = 'HIGH - Judicial misconduct cluster'
        elif dominant_type == 'EVIDENCE' and dominant_lane in ('A', 'D', 'E'):
            sig = f'MEDIUM - Evidence cluster for Lane {dominant_lane}'
        elif dominant_type == 'AUTHORITY':
            sig = 'MEDIUM - Authority chain cluster'
        elif len(members) > 100:
            sig = 'HIGH - Major entity cluster'
        else:
            sig = 'LOW - General cluster'

        label = f"C{cid}: {dominant_type} ({len(members)} nodes)"

        comm_rows.append((cid, label, len(members), dominant_type, dominant_lane,
                         round(avg_sev, 2), round(density, 4), key_nodes, sig))

        for nid in members:
            member_rows.append((cid, nid, 1.0))

    conn.executemany("""
        INSERT INTO communities (community_id, label, node_count, dominant_type, dominant_lane,
                                avg_severity, density, key_nodes, legal_significance)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, comm_rows)

    conn.executemany("""
        INSERT OR IGNORE INTO community_members (community_id, node_id, membership_score)
        VALUES (?, ?, ?)
    """, member_rows)

    conn.commit()
    elapsed = time.perf_counter() - t0
    print(f"  [OK] {len(comm_rows)} communities, {len(member_rows)} memberships in {elapsed:.1f}s")
    return partition


def run_component_communities(G, conn):
    """Fallback: use weakly connected components as communities."""
    import networkx as nx
    t0 = time.perf_counter()

    components = list(nx.weakly_connected_components(G))
    # Sort by size descending
    components.sort(key=len, reverse=True)

    conn.execute("DELETE FROM communities")
    conn.execute("DELETE FROM community_members")

    partition = {}
    comm_rows = []
    member_rows = []

    for cid, component in enumerate(components[:500]):  # top 500 components
        if len(component) < 3:
            continue

        types = Counter()
        lanes = Counter()
        total_sev = 0
        for nid in component:
            partition[nid] = cid
            if nid in G.nodes:
                nd = G.nodes[nid]
                types[nd.get('node_type', 'unknown')] += 1
                if nd.get('lane'):
                    lanes[nd['lane']] += 1
                total_sev += nd.get('severity', 0)

        dominant_type = types.most_common(1)[0][0] if types else 'unknown'
        dominant_lane = lanes.most_common(1)[0][0] if lanes else None
        avg_sev = total_sev / max(len(component), 1)
        key_nodes = json.dumps(list(component)[:5])

        label = f"C{cid}: {dominant_type} ({len(component)} nodes)"
        sig = 'MEDIUM - Connected component'
        if len(component) > 100:
            sig = 'HIGH - Major connected component'

        comm_rows.append((cid, label, len(component), dominant_type, dominant_lane,
                         round(avg_sev, 2), 0, key_nodes, sig))
        for nid in component:
            member_rows.append((cid, nid, 1.0))

    conn.executemany("""
        INSERT INTO communities (community_id, label, node_count, dominant_type, dominant_lane,
                                avg_severity, density, key_nodes, legal_significance)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, comm_rows)

    conn.executemany("""
        INSERT OR IGNORE INTO community_members (community_id, node_id, membership_score)
        VALUES (?, ?, ?)
    """, member_rows)

    conn.commit()
    elapsed = time.perf_counter() - t0
    print(f"  [OK] {len(comm_rows)} component-communities, {len(member_rows)} memberships in {elapsed:.1f}s")
    return partition


def run_node_analytics(G, conn, partition=None):
    """Compute PageRank, betweenness centrality, degree, HITS, bridge detection."""
    import networkx as nx
    t0 = time.perf_counter()

    # Clear old analytics
    conn.execute("DELETE FROM node_analytics")

    n_nodes = G.number_of_nodes()
    n_edges = G.number_of_edges()
    print(f"  Computing analytics on {n_nodes} nodes, {n_edges} edges...")

    # ── PageRank ──
    print("  Computing PageRank...")
    pr_start = time.perf_counter()
    try:
        pagerank = nx.pagerank(G, alpha=0.85, max_iter=50, tol=1e-4)
    except Exception as e:
        print(f"  [WARN] PageRank failed: {e}, using degree-based approximation")
        pagerank = {}
        max_deg = max((d for _, d in G.degree()), default=1)
        for n, d in G.degree():
            pagerank[n] = d / max(max_deg, 1)
    print(f"  PageRank done in {time.perf_counter() - pr_start:.1f}s")

    # ── Betweenness Centrality (sampled for large graphs) ──
    print("  Computing betweenness centrality (sampled)...")
    bc_start = time.perf_counter()
    # For 235K nodes, full betweenness is O(VE) ~ impossible
    # Sample k nodes for approximation
    k_sample = min(500, n_nodes)
    try:
        betweenness = nx.betweenness_centrality(G, k=k_sample, normalized=True, seed=42)
    except Exception as e:
        print(f"  [WARN] Betweenness failed: {e}, using zeros")
        betweenness = {n: 0 for n in G.nodes}
    print(f"  Betweenness done in {time.perf_counter() - bc_start:.1f}s (k={k_sample})")

    # ── Degree ──
    print("  Computing degree centrality...")
    in_degree = dict(G.in_degree())
    out_degree = dict(G.out_degree())
    total_degree = dict(G.degree())

    # ── HITS (Hub/Authority) ──
    print("  Computing HITS (hub/authority scores)...")
    hits_start = time.perf_counter()
    try:
        hubs, authorities = nx.hits(G, max_iter=50, tol=1e-4, normalized=True)
    except Exception as e:
        print(f"  [WARN] HITS failed: {e}, using zeros")
        hubs = {n: 0 for n in G.nodes}
        authorities = {n: 0 for n in G.nodes}
    print(f"  HITS done in {time.perf_counter() - hits_start:.1f}s")

    # ── Bridge Detection ──
    # A node is a bridge if removing it increases the number of connected components
    # For directed graphs, approximate: nodes with high betweenness AND connecting different communities
    print("  Detecting bridge nodes...")
    bridges = set()
    if partition:
        # Nodes connecting different communities
        for u, v in G.edges():
            cu = partition.get(u, -1)
            cv = partition.get(v, -1)
            if cu != cv and cu >= 0 and cv >= 0:
                bridges.add(u)
                bridges.add(v)
        print(f"  Found {len(bridges)} cross-community bridge nodes")

    # ── Keystone Detection ──
    # Top 0.1% PageRank nodes whose removal would most impact graph
    pr_sorted = sorted(pagerank.items(), key=lambda x: x[1], reverse=True)
    keystone_threshold = max(1, int(n_nodes * 0.001))
    keystones = set(n for n, _ in pr_sorted[:keystone_threshold])
    print(f"  Found {len(keystones)} keystone nodes (top 0.1% PageRank)")

    # ── Legal Centrality (composite) ──
    # legal_centrality = 0.4*pagerank + 0.3*betweenness + 0.2*authority + 0.1*hub
    # Normalized to 0-1
    max_pr = max(pagerank.values()) if pagerank else 1
    max_bc = max(betweenness.values()) if betweenness else 1
    max_auth = max(authorities.values()) if authorities else 1
    max_hub = max(hubs.values()) if hubs else 1

    # ── Batch insert ──
    print("  Inserting analytics...")
    batch = []
    batch_size = 5000
    inserted = 0

    for nid in G.nodes:
        pr_val = pagerank.get(nid, 0)
        bc_val = betweenness.get(nid, 0)
        di = in_degree.get(nid, 0)
        do = out_degree.get(nid, 0)
        dt = total_degree.get(nid, 0)
        hub_val = hubs.get(nid, 0)
        auth_val = authorities.get(nid, 0)
        cid = partition.get(nid) if partition else None
        is_br = 1 if nid in bridges else 0
        is_ks = 1 if nid in keystones else 0

        # Composite legal centrality
        lc = (0.4 * (pr_val / max(max_pr, 1e-12)) +
              0.3 * (bc_val / max(max_bc, 1e-12)) +
              0.2 * (auth_val / max(max_auth, 1e-12)) +
              0.1 * (hub_val / max(max_hub, 1e-12)))

        batch.append((nid, pr_val, bc_val, di, do, dt, hub_val, auth_val,
                      cid, is_br, is_ks, round(lc, 6)))

        if len(batch) >= batch_size:
            conn.executemany("""
                INSERT OR REPLACE INTO node_analytics
                (node_id, pagerank, betweenness, degree_in, degree_out, degree_total,
                 hub_score, authority_score, community_id, is_bridge, is_keystone, legal_centrality)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, batch)
            inserted += len(batch)
            batch = []

    if batch:
        conn.executemany("""
            INSERT OR REPLACE INTO node_analytics
            (node_id, pagerank, betweenness, degree_in, degree_out, degree_total,
             hub_score, authority_score, community_id, is_bridge, is_keystone, legal_centrality)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, batch)
        inserted += len(batch)

    conn.commit()
    elapsed = time.perf_counter() - t0
    print(f"  [OK] {inserted} node analytics rows in {elapsed:.1f}s")

    # Report top 10 by legal centrality
    top10 = conn.execute("""
        SELECT na.node_id, na.legal_centrality, na.pagerank, na.betweenness,
               na.degree_total, na.is_keystone, n.label, n.node_type
        FROM node_analytics na
        JOIN nodes n ON n.id = na.node_id
        ORDER BY na.legal_centrality DESC LIMIT 10
    """).fetchall()

    print("\n  TOP 10 NODES BY LEGAL CENTRALITY:")
    print("  " + "-" * 80)
    for nid, lc, pr, bc, deg, ks, label, ntype in top10:
        ks_tag = " [KEYSTONE]" if ks else ""
        print(f"  {lc:.4f} | PR={pr:.6f} BC={bc:.6f} Deg={deg} | {ntype}: {label[:40]}{ks_tag}")

    return pagerank, betweenness


def build_chains(G, conn):
    """Build evidence chains: EVIDENCE -> VIOLATION -> AUTHORITY -> REMEDY -> FILING."""
    import networkx as nx
    t0 = time.perf_counter()

    # Clear existing chains
    conn.execute("DELETE FROM chains")

    # Chain types we're looking for
    CHAIN_TYPES = {
        'evidence_to_authority': ('EVIDENCE', 'AUTHORITY'),
        'evidence_to_violation': ('EVIDENCE', 'VIOLATION'),
        'violation_to_authority': ('VIOLATION', 'AUTHORITY'),
        'evidence_to_filing': ('EVIDENCE', 'FILING'),
        'authority_to_remedy': ('AUTHORITY', 'REMEDY'),
        'violation_to_remedy': ('VIOLATION', 'REMEDY'),
        'actor_to_violation': ('ACTOR', 'VIOLATION'),
    }

    chain_rows = []

    # Group nodes by type for efficient lookup
    nodes_by_type = defaultdict(set)
    for nid in G.nodes:
        ntype = G.nodes[nid].get('node_type', '')
        nodes_by_type[ntype].add(nid)

    print(f"  Node type distribution: {dict((k, len(v)) for k, v in nodes_by_type.items())}")

    for chain_name, (src_type, tgt_type) in CHAIN_TYPES.items():
        src_nodes = nodes_by_type.get(src_type, set())
        tgt_nodes = nodes_by_type.get(tgt_type, set())

        if not src_nodes or not tgt_nodes:
            print(f"  {chain_name}: skipped (no {src_type} or {tgt_type} nodes)")
            continue

        # Sample source nodes for large sets
        sample_size = min(len(src_nodes), 1000)
        import random
        random.seed(42)
        sampled = random.sample(list(src_nodes), sample_size)

        found = 0
        for src in sampled:
            # BFS to find shortest path to any target-type node (max depth 4)
            try:
                for tgt in tgt_nodes:
                    if src == tgt:
                        continue
                    if G.has_edge(src, tgt):
                        # Direct edge
                        wt = G.edges[src, tgt].get('weight', 0.5)
                        lane = G.nodes[src].get('lane', '') or G.nodes[tgt].get('lane', '')
                        chain_rows.append((
                            json.dumps([src, tgt]),
                            chain_name,
                            wt,
                            2,
                            lane,
                            None,
                            json.dumps([src]),
                            round(wt, 4)
                        ))
                        found += 1
                        if found >= 500:
                            break
                if found >= 500:
                    break
            except Exception:
                continue

        # Also find 2-hop chains via BFS (limited)
        hop2_found = 0
        for src in sampled[:200]:
            for mid in G.successors(src):
                if mid in tgt_nodes:
                    continue
                for tgt in G.successors(mid):
                    if tgt in tgt_nodes:
                        w1 = G.edges[src, mid].get('weight', 0.5)
                        w2 = G.edges[mid, tgt].get('weight', 0.5)
                        lane = G.nodes[src].get('lane', '') or G.nodes[tgt].get('lane', '')
                        chain_rows.append((
                            json.dumps([src, mid, tgt]),
                            chain_name,
                            (w1 + w2) / 2,
                            3,
                            lane,
                            None,
                            json.dumps([src]),
                            round((w1 * w2), 4)
                        ))
                        hop2_found += 1
                        if hop2_found >= 300:
                            break
                if hop2_found >= 300:
                    break
            if hop2_found >= 300:
                break

        print(f"  {chain_name}: {found} direct + {hop2_found} 2-hop chains")

    if chain_rows:
        conn.executemany("""
            INSERT INTO chains (chain_path, chain_type, total_weight, length, lane,
                               filing_id, evidence_ids, strength_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, chain_rows)
        conn.commit()

    elapsed = time.perf_counter() - t0
    print(f"  [OK] {len(chain_rows)} chains built in {elapsed:.1f}s")


def detect_patterns(G, conn):
    """Detect legal patterns: retaliation, escalation, conspiracy, coordination."""
    t0 = time.perf_counter()

    # Clear existing patterns
    conn.execute("DELETE FROM detected_patterns")

    patterns = []

    # ── Pattern 1: Retaliation (Action A -> Response B within timeframe) ──
    print("  Detecting retaliation patterns...")
    # Look for ACTOR nodes with many outgoing VIOLATION edges
    actor_violations = defaultdict(list)
    for u, v, data in G.edges(data=True):
        if (G.nodes.get(u, {}).get('node_type') == 'ACTOR' and
            G.nodes.get(v, {}).get('node_type') == 'VIOLATION'):
            actor_violations[G.nodes[u].get('label', u)].append(v)

    for actor, violations in actor_violations.items():
        if len(violations) >= 3:
            patterns.append((
                'RETALIATION',
                f'{actor} connected to {len(violations)} violations -- potential retaliation pattern',
                actor,
                json.dumps(violations[:10]),
                min(0.95, 0.5 + len(violations) * 0.05),
                min(10, len(violations)),
                None, None, None,
                json.dumps(violations[:20]),
                None,
                'MCR 2.003, MCL 722.23(j), 42 USC 1983'
            ))

    # ── Pattern 2: Conspiracy (multiple actors connected through shared violations) ──
    print("  Detecting conspiracy patterns...")
    # Find ACTOR pairs that share 3+ VIOLATION connections
    actor_nodes = [n for n in G.nodes if G.nodes[n].get('node_type') == 'ACTOR']
    actor_shared = defaultdict(set)

    for actor in actor_nodes:
        for neighbor in G.successors(actor):
            if G.nodes.get(neighbor, {}).get('node_type') == 'VIOLATION':
                actor_shared[neighbor].add(actor)

    # Violations connected to 2+ actors = potential conspiracy
    for violation, actors in actor_shared.items():
        if len(actors) >= 2:
            actor_labels = [G.nodes[a].get('label', a) for a in actors]
            patterns.append((
                'CONSPIRACY',
                f'{len(actors)} actors ({", ".join(actor_labels[:5])}) share violation: {G.nodes.get(violation, {}).get("label", violation)[:60]}',
                json.dumps(actor_labels),
                json.dumps(list(actors)[:10]),
                min(0.90, 0.4 + len(actors) * 0.15),
                min(10, len(actors) * 3),
                G.nodes.get(violation, {}).get('lane'),
                None, None,
                json.dumps([violation] + list(actors)[:10]),
                None,
                '42 USC 1983, 42 USC 1985(3)'
            ))

    # ── Pattern 3: Evidence Clusters (high-density evidence in specific lanes) ──
    print("  Detecting evidence concentration patterns...")
    lane_evidence = defaultdict(int)
    lane_violations = defaultdict(int)
    for n in G.nodes:
        nd = G.nodes[n]
        lane = nd.get('lane', '')
        if nd.get('node_type') == 'EVIDENCE' and lane:
            lane_evidence[lane] += 1
        elif nd.get('node_type') == 'VIOLATION' and lane:
            lane_violations[lane] += 1

    for lane, count in lane_evidence.items():
        if count >= 100:
            v_count = lane_violations.get(lane, 0)
            patterns.append((
                'EVIDENCE_CONCENTRATION',
                f'Lane {lane}: {count} evidence nodes + {v_count} violations -- strong evidentiary basis',
                None,
                None,
                min(0.95, 0.5 + count / 1000),
                min(10, count / 100),
                lane, None, None, None, None,
                'Evidence weight supports filing'
            ))

    # ── Pattern 4: Hub Detection (nodes connecting many different types) ──
    print("  Detecting hub patterns...")
    for n in G.nodes:
        neighbors = list(G.successors(n)) + list(G.predecessors(n))
        if len(neighbors) >= 20:
            neighbor_types = Counter(G.nodes[nb].get('node_type', '') for nb in neighbors if nb in G.nodes)
            if len(neighbor_types) >= 3:
                nd = G.nodes[n]
                patterns.append((
                    'HUB_NODE',
                    f'{nd.get("label", n)[:40]} connects {len(neighbors)} nodes across {len(neighbor_types)} types: {dict(neighbor_types)}',
                    nd.get('label', n),
                    None,
                    0.80,
                    min(10, len(neighbors) / 10),
                    nd.get('lane'),
                    None, None,
                    json.dumps([n]),
                    None,
                    'Strategic significance -- keystone entity'
                ))

    # ── Pattern 5: Cross-Lane Bridges ──
    print("  Detecting cross-lane bridge patterns...")
    cross_lane_edges = defaultdict(list)
    for u, v in G.edges():
        lu = G.nodes.get(u, {}).get('lane', '')
        lv = G.nodes.get(v, {}).get('lane', '')
        if lu and lv and lu != lv:
            cross_lane_edges[(lu, lv)].append((u, v))

    for (lane_a, lane_b), edges in cross_lane_edges.items():
        if len(edges) >= 5:
            patterns.append((
                'CROSS_LANE_BRIDGE',
                f'{len(edges)} connections between Lane {lane_a} and Lane {lane_b} -- potential multiplied damages',
                None,
                json.dumps([e[0] for e in edges[:10]]),
                min(0.90, 0.5 + len(edges) * 0.02),
                min(10, len(edges) / 5),
                f'{lane_a},{lane_b}',
                None, None,
                json.dumps([e[0] for e in edges[:20]]),
                None,
                'Cross-lane evidence strengthens federal 1983 claims'
            ))

    if patterns:
        conn.executemany("""
            INSERT INTO detected_patterns
            (pattern_type, description, actors, evidence_ids, confidence, severity,
             lane, start_date, end_date, node_ids, edge_ids, filing_relevance)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, patterns)
        conn.commit()

    elapsed = time.perf_counter() - t0

    # Summary
    type_counts = Counter(p[0] for p in patterns)
    print(f"  [OK] {len(patterns)} patterns detected in {elapsed:.1f}s:")
    for ptype, cnt in type_counts.most_common():
        print(f"    {ptype}: {cnt}")


def main():
    print("=" * 70)
    print("THEMANBEARPIG Community Detection + Node Analytics")
    print("=" * 70)

    if not BRAIN_DB.exists():
        print(f"ERROR: {BRAIN_DB} not found")
        return 1

    conn = connect()
    total_start = time.perf_counter()

    # Phase 0: Create tables
    print("\n--- Phase 0: Creating tables ---")
    create_tables(conn)

    # Phase 1: Build graph
    print("\n--- Phase 1: Building NetworkX graph ---")
    G = build_graph(conn)

    # Phase 2: Community detection
    print("\n--- Phase 2: Community detection ---")
    partition = run_community_detection(G, conn)

    # Phase 3: Node analytics
    print("\n--- Phase 3: Node analytics (PageRank, betweenness, HITS) ---")
    run_node_analytics(G, conn, partition)

    # Phase 4: Chain building
    print("\n--- Phase 4: Chain building ---")
    build_chains(G, conn)

    # Phase 5: Pattern detection
    print("\n--- Phase 5: Pattern detection ---")
    detect_patterns(G, conn)

    # Phase 6: ANALYZE for query optimization
    print("\n--- Phase 6: Optimization ---")
    conn.execute("ANALYZE communities")
    conn.execute("ANALYZE community_members")
    conn.execute("ANALYZE node_analytics")
    conn.execute("ANALYZE chains")
    conn.execute("ANALYZE detected_patterns")
    conn.commit()

    # Final summary
    total_elapsed = time.perf_counter() - total_start
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    for table in ['communities', 'community_members', 'node_analytics', 'chains', 'detected_patterns']:
        cnt = conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
        print(f"  {table}: {cnt:,} rows")
    print(f"\n  Total time: {total_elapsed:.1f}s")
    print(f"  Brain DB size: {BRAIN_DB.stat().st_size / 1024 / 1024:.1f} MB")

    conn.close()
    print("\n[OK] Community detection + analytics COMPLETE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
