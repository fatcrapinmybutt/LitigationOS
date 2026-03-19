#!/usr/bin/env python3
"""
DELTA 2: Authority PageRank Engine — MBP LitigationOS 2026
============================================================
Graph algorithms on the Michigan authority corpus.
Computes PageRank over 461K+ edges to rank citation weight.
Pure Python + numpy (no networkx).

Tables consumed:
  auth_authority_nodes  (12,409)  — id, label, node_type, properties
  auth_authority_edges  (461,769) — source_id, target_id, edge_type, weight
  graph_nodes           (31,565)  — id, label, node_type
  authorities_nodes     (8,427)   — node_id, label, node_group
  authorities_edges     (2,000)   — src, dst, relation, weight
"""

import json
import os
import pickle
import sqlite3
import sys
import time
from collections import defaultdict, deque
from pathlib import Path

import numpy as np

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"
CACHE_DIR = Path(r"C:\Users\andre\LitigationOS\00_SYSTEM\local_model\cache")
CACHE_FILE = CACHE_DIR / "authority_pagerank.pkl"


class AuthorityPageRank:
    """Graph‑analytic engine over the Michigan authority citation network."""

    # ── construction ────────────────────────────────────────────────
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.nodes: dict = {}           # node_id -> {label, node_type, pagerank}
        self.edges: dict = defaultdict(list)   # node_id -> [(target, edge_type, weight)]
        self.reverse_edges: dict = defaultdict(list)  # target -> [(source, weight)]
        self.pagerank_scores: dict = {}
        self._node_index: dict = {}     # int index -> node_id
        self._node_id_to_idx: dict = {} # node_id -> int index
        self._label_index: dict = {}    # lowercase label -> node_id (first match)
        self._built = False
        self._load_or_build()

    # ── persistence ─────────────────────────────────────────────────
    def _load_or_build(self):
        """Try loading cached PageRank; fall back to full build."""
        if CACHE_FILE.exists():
            try:
                with open(CACHE_FILE, "rb") as fh:
                    data = pickle.load(fh)
                self.nodes = data["nodes"]
                self.edges = data["edges"]
                self.reverse_edges = data["reverse_edges"]
                self.pagerank_scores = data["pagerank_scores"]
                self._rebuild_indexes()
                self._built = True
                return
            except Exception as exc:
                print(f"[WARN] Cache load failed ({exc}); rebuilding …")
        self._load_graph()
        self.compute_pagerank()
        self._save_cache()

    def _save_cache(self):
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        data = {
            "nodes": self.nodes,
            "edges": dict(self.edges),
            "reverse_edges": dict(self.reverse_edges),
            "pagerank_scores": self.pagerank_scores,
        }
        with open(CACHE_FILE, "wb") as fh:
            pickle.dump(data, fh, protocol=pickle.HIGHEST_PROTOCOL)

    def _rebuild_indexes(self):
        """Build fast‑lookup structures after load."""
        self._node_index = {}
        self._node_id_to_idx = {}
        self._label_index = {}  # lowercase label -> node_id (prefer nodes with edges)
        for idx, nid in enumerate(self.nodes):
            self._node_index[idx] = nid
            self._node_id_to_idx[nid] = idx
            lbl = self.nodes[nid].get("label", "").lower()
            if not lbl:
                continue
            existing = self._label_index.get(lbl)
            if existing is None:
                self._label_index[lbl] = nid
            else:
                # Prefer a node that participates in edges
                cur_has_edges = bool(self.edges.get(nid) or self.reverse_edges.get(nid))
                old_has_edges = bool(self.edges.get(existing) or self.reverse_edges.get(existing))
                if cur_has_edges and not old_has_edges:
                    self._label_index[lbl] = nid
        self._built = True

    # ── graph loading ───────────────────────────────────────────────
    def _load_graph(self):
        """Load the unified authority graph from all DB tables."""
        t0 = time.time()
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # 1. auth_authority_nodes (12,409) — primary
        cur.execute("SELECT id, label, node_type FROM auth_authority_nodes")
        for row in cur.fetchall():
            nid = row["id"]
            self.nodes[nid] = {
                "label": row["label"] or nid,
                "node_type": row["node_type"] or "unknown",
                "pagerank": 0.0,
            }

        # 2. graph_nodes (31,565) — merge, skip duplicates
        cur.execute("SELECT id, label, node_type FROM graph_nodes")
        for row in cur.fetchall():
            nid = row["id"]
            if nid not in self.nodes:
                self.nodes[nid] = {
                    "label": row["label"] or nid,
                    "node_type": row["node_type"] or "unknown",
                    "pagerank": 0.0,
                }

        # 3. authorities_nodes (8,427) — merge by node_id
        cur.execute("SELECT node_id, label, node_group FROM authorities_nodes")
        for row in cur.fetchall():
            nid = row["node_id"]
            if nid not in self.nodes:
                self.nodes[nid] = {
                    "label": row["label"] or nid,
                    "node_type": row["node_group"] or "unknown",
                    "pagerank": 0.0,
                }

        # 4. auth_authority_edges (461,769) — primary edges
        edge_count = 0
        cur.execute("SELECT source_id, target_id, edge_type, weight FROM auth_authority_edges")
        for row in cur.fetchall():
            src, tgt = row["source_id"], row["target_id"]
            w = float(row["weight"]) if row["weight"] else 1.0
            etype = row["edge_type"] or "cross_refs"
            # ensure nodes exist for any referenced IDs
            for n in (src, tgt):
                if n not in self.nodes:
                    self.nodes[n] = {"label": n, "node_type": "inferred", "pagerank": 0.0}
            self.edges[src].append((tgt, etype, w))
            self.reverse_edges[tgt].append((src, w))
            edge_count += 1

        # 5. authorities_edges (2,000) — additional edges
        cur.execute("SELECT src, dst, relation, weight FROM authorities_edges")
        for row in cur.fetchall():
            src, tgt = row["src"], row["dst"]
            w = float(row["weight"]) if row["weight"] else 1.0
            rel = row["relation"] or "cites"
            for n in (src, tgt):
                if n not in self.nodes:
                    self.nodes[n] = {"label": n, "node_type": "inferred", "pagerank": 0.0}
            # avoid exact duplicates (most already in auth_authority_edges)
            if not any(t == tgt for t, _, _ in self.edges.get(src, [])):
                self.edges[src].append((tgt, rel, w))
                self.reverse_edges[tgt].append((src, w))
                edge_count += 1

        conn.close()
        self._rebuild_indexes()
        elapsed = time.time() - t0
        print(f"[PageRank] Loaded {len(self.nodes):,} nodes, {edge_count:,} edges in {elapsed:.1f}s")

    # ── PageRank ────────────────────────────────────────────────────
    def compute_pagerank(self, damping: float = 0.85, max_iter: int = 100,
                         tol: float = 1e-6) -> dict:
        """
        Power‑iteration PageRank using numpy sparse CSR‑style arrays.
        For 461K edges / ~50K nodes, converges in ~25 iterations.
        """
        t0 = time.time()
        n = len(self.nodes)
        if n == 0:
            return {}

        # Build node ordering
        id_list = list(self.nodes.keys())
        id_to_idx = {nid: i for i, nid in enumerate(id_list)}

        # Build sparse adjacency: src -> [targets] with weights
        # CSR-style: row_ptr, col_idx, vals
        row_ptr = np.zeros(n + 1, dtype=np.int64)
        # Count out-degrees
        for i, nid in enumerate(id_list):
            row_ptr[i + 1] = row_ptr[i] + len(self.edges.get(nid, []))

        total_edges = int(row_ptr[n])
        col_idx = np.zeros(total_edges, dtype=np.int64)
        vals = np.zeros(total_edges, dtype=np.float64)

        for i, nid in enumerate(id_list):
            start = int(row_ptr[i])
            for k, (tgt, _, w) in enumerate(self.edges.get(nid, [])):
                j = id_to_idx.get(tgt)
                if j is not None:
                    col_idx[start + k] = j
                    vals[start + k] = w

        # Normalise outgoing weights per node
        out_weight = np.zeros(n, dtype=np.float64)
        for i in range(n):
            s, e = int(row_ptr[i]), int(row_ptr[i + 1])
            out_weight[i] = vals[s:e].sum()

        # Initialise rank vector
        rank = np.full(n, 1.0 / n, dtype=np.float64)
        teleport = (1.0 - damping) / n

        # Identify dangling nodes (no outgoing edges)
        dangling_mask = out_weight == 0.0

        for iteration in range(max_iter):
            new_rank = np.full(n, teleport, dtype=np.float64)
            # Distribute dangling mass equally
            dangling_sum = damping * rank[dangling_mask].sum() / n
            new_rank += dangling_sum

            # Accumulate weighted contributions via reverse edges
            for j in range(n):
                # For each node j, sum contributions from its in-links
                # Using reverse_edges for efficiency
                pass  # (handled in vectorised loop below)

            # Vectorised: iterate over source nodes, distribute rank to targets
            for i in range(n):
                s, e = int(row_ptr[i]), int(row_ptr[i + 1])
                if s == e:
                    continue
                ow = out_weight[i]
                if ow == 0.0:
                    continue
                contribution = damping * rank[i] / ow
                for k in range(s, e):
                    new_rank[col_idx[k]] += contribution * vals[k]

            # Check convergence
            diff = np.abs(new_rank - rank).sum()
            rank = new_rank
            if diff < tol:
                print(f"[PageRank] Converged in {iteration + 1} iterations (Δ={diff:.2e})")
                break
        else:
            print(f"[PageRank] Reached max {max_iter} iterations (Δ={diff:.2e})")

        # Store scores
        self.pagerank_scores = {}
        for i, nid in enumerate(id_list):
            score = float(rank[i])
            self.pagerank_scores[nid] = score
            self.nodes[nid]["pagerank"] = score

        elapsed = time.time() - t0
        print(f"[PageRank] Computed in {elapsed:.1f}s over {n:,} nodes")
        self._save_cache()
        return self.pagerank_scores

    # ── queries ─────────────────────────────────────────────────────
    def get_top_authorities(self, n: int = 50, node_type: str = None) -> list:
        """Top-N authorities by PageRank. Optional type filter."""
        items = self.pagerank_scores.items()
        if node_type:
            nt = node_type.upper()
            items = [(k, v) for k, v in items if self.nodes.get(k, {}).get("node_type", "").upper() == nt]
        ranked = sorted(items, key=lambda x: x[1], reverse=True)[:n]
        result = []
        for rank_pos, (nid, score) in enumerate(ranked, 1):
            nd = self.nodes.get(nid, {})
            result.append({
                "rank": rank_pos,
                "node_id": nid,
                "label": nd.get("label", nid),
                "node_type": nd.get("node_type", "unknown"),
                "pagerank": round(score, 8),
                "in_degree": len(self.reverse_edges.get(nid, [])),
                "out_degree": len(self.edges.get(nid, [])),
            })
        return result

    def get_authority_score(self, rule_or_statute: str) -> dict:
        """Look up PageRank score for a rule/statute by label substring match."""
        query = rule_or_statute.lower().replace(" ", "")
        matches = []
        for nid, nd in self.nodes.items():
            lbl = nd.get("label", "").lower().replace(" ", "")
            if query in lbl or lbl in query:
                matches.append(nid)
        if not matches:
            # fuzzy: try partial match
            for nid, nd in self.nodes.items():
                lbl = nd.get("label", "").lower()
                if any(tok in lbl for tok in rule_or_statute.lower().split()):
                    matches.append(nid)
                    if len(matches) >= 20:
                        break

        # Sort matches by PageRank
        scored = sorted(matches, key=lambda x: self.pagerank_scores.get(x, 0), reverse=True)

        # Compute global rank for top match
        all_ranked = sorted(self.pagerank_scores.items(), key=lambda x: x[1], reverse=True)
        rank_map = {nid: i + 1 for i, (nid, _) in enumerate(all_ranked)}

        results = []
        for nid in scored[:10]:
            nd = self.nodes[nid]
            results.append({
                "node_id": nid,
                "label": nd.get("label", nid),
                "node_type": nd.get("node_type"),
                "pagerank": round(self.pagerank_scores.get(nid, 0), 8),
                "global_rank": rank_map.get(nid, -1),
                "in_degree": len(self.reverse_edges.get(nid, [])),
                "out_degree": len(self.edges.get(nid, [])),
            })
        return {"query": rule_or_statute, "matches": results}

    # ── BFS shortest path ───────────────────────────────────────────
    def _resolve_label(self, label: str) -> str | None:
        """Resolve a human label to a node_id. Prefers nodes with edges."""
        lbl = label.lower().strip()
        if lbl in self._label_index:
            return self._label_index[lbl]
        # substring match — collect candidates, prefer those with edges
        candidates = []
        for key, nid in self._label_index.items():
            if lbl.replace(" ", "") in key.replace(" ", ""):
                has_edges = bool(self.edges.get(nid) or self.reverse_edges.get(nid))
                candidates.append((nid, has_edges))
        if candidates:
            candidates.sort(key=lambda x: (x[1], -len(self.nodes.get(x[0], {}).get("label", ""))), reverse=True)
            return candidates[0][0]
        # broader fallback
        for nid, nd in self.nodes.items():
            if lbl.replace(" ", "") in nd.get("label", "").lower().replace(" ", ""):
                if self.edges.get(nid) or self.reverse_edges.get(nid):
                    return nid
        # last resort: any match
        for nid, nd in self.nodes.items():
            if lbl.replace(" ", "") in nd.get("label", "").lower().replace(" ", ""):
                return nid
        return None

    def shortest_path(self, source_label: str, target_label: str) -> list:
        """BFS shortest path between two authority nodes by label."""
        src = self._resolve_label(source_label)
        tgt = self._resolve_label(target_label)
        if src is None:
            return [{"error": f"Source node not found: {source_label}"}]
        if tgt is None:
            return [{"error": f"Target node not found: {target_label}"}]
        if src == tgt:
            return [self._node_summary(src)]

        # BFS on undirected version of graph
        visited = {src}
        parent = {src: None}
        queue = deque([src])
        found = False

        while queue:
            cur = queue.popleft()
            # outgoing edges
            neighbors = [t for t, _, _ in self.edges.get(cur, [])]
            # incoming edges (treat as undirected)
            neighbors += [s for s, _ in self.reverse_edges.get(cur, [])]
            for nbr in neighbors:
                if nbr not in visited:
                    visited.add(nbr)
                    parent[nbr] = cur
                    if nbr == tgt:
                        found = True
                        break
                    queue.append(nbr)
            if found:
                break

        if not found:
            return [{"error": f"No path between {source_label} and {target_label}"}]

        # Reconstruct path
        path = []
        cur = tgt
        while cur is not None:
            path.append(self._node_summary(cur))
            cur = parent[cur]
        path.reverse()
        return path

    def _node_summary(self, nid: str) -> dict:
        nd = self.nodes.get(nid, {})
        return {
            "node_id": nid,
            "label": nd.get("label", nid),
            "node_type": nd.get("node_type", "unknown"),
            "pagerank": round(self.pagerank_scores.get(nid, 0), 8),
        }

    # ── neighbourhood ───────────────────────────────────────────────
    def get_authority_neighborhood(self, node_label: str, depth: int = 2) -> dict:
        """All nodes within N hops of a given authority."""
        root = self._resolve_label(node_label)
        if root is None:
            return {"error": f"Node not found: {node_label}"}

        visited = {root: 0}
        queue = deque([(root, 0)])
        edge_list = []

        while queue:
            cur, d = queue.popleft()
            if d >= depth:
                continue
            for tgt, etype, w in self.edges.get(cur, []):
                edge_list.append({"source": cur, "target": tgt, "type": etype})
                if tgt not in visited:
                    visited[tgt] = d + 1
                    queue.append((tgt, d + 1))
            for src, w in self.reverse_edges.get(cur, []):
                edge_list.append({"source": src, "target": cur, "type": "incoming"})
                if src not in visited:
                    visited[src] = d + 1
                    queue.append((src, d + 1))

        node_list = [
            {**self._node_summary(nid), "hop_distance": dist}
            for nid, dist in sorted(visited.items(), key=lambda x: x[1])
        ]
        return {"root": node_label, "depth": depth, "nodes": node_list,
                "edges": edge_list[:500], "node_count": len(node_list),
                "edge_count": len(edge_list)}

    # ── community detection (label propagation) ─────────────────────
    def detect_communities(self, max_iter: int = 20) -> dict:
        """Label propagation community detection. Pure Python."""
        import random
        # Only run on nodes that have edges
        active_nodes = set()
        for nid in self.edges:
            active_nodes.add(nid)
            for tgt, _, _ in self.edges[nid]:
                active_nodes.add(tgt)
        active_list = list(active_nodes)

        # Initialise: each node is its own community
        community = {nid: i for i, nid in enumerate(active_list)}

        for iteration in range(max_iter):
            changed = 0
            random.shuffle(active_list)
            for nid in active_list:
                # Collect neighbour community labels with weights
                label_weights = defaultdict(float)
                for tgt, _, w in self.edges.get(nid, []):
                    if tgt in community:
                        label_weights[community[tgt]] += w
                for src, w in self.reverse_edges.get(nid, []):
                    if src in community:
                        label_weights[community[src]] += w
                if not label_weights:
                    continue
                # Pick the label with highest total weight
                best_label = max(label_weights, key=label_weights.get)
                if community[nid] != best_label:
                    community[nid] = best_label
                    changed += 1
            if changed == 0:
                print(f"[Communities] Converged in {iteration + 1} iterations")
                break

        # Group by community
        groups = defaultdict(list)
        for nid, cid in community.items():
            groups[cid].append(self.nodes.get(nid, {}).get("label", nid))

        # Sort communities by size descending
        sorted_communities = {}
        for i, (cid, members) in enumerate(
            sorted(groups.items(), key=lambda x: len(x[1]), reverse=True)
        ):
            sorted_communities[f"community_{i}"] = {
                "size": len(members),
                "members": sorted(members)[:100],  # cap display at 100
            }
        return {
            "total_communities": len(sorted_communities),
            "active_nodes": len(active_list),
            "communities": sorted_communities,
        }

    # ── strongest authority chain ───────────────────────────────────
    def get_strongest_chain(self, topic: str, depth: int = 3) -> list:
        """
        Starting from nodes matching *topic*, greedily follow the
        highest‑PageRank outgoing edge for *depth* hops.
        """
        query = topic.lower()
        seeds = []
        for nid, nd in self.nodes.items():
            lbl = nd.get("label", "").lower()
            if query in lbl:
                seeds.append(nid)
        if not seeds:
            return [{"error": f"No nodes match topic: {topic}"}]

        # Pick the seed with highest PageRank
        seeds.sort(key=lambda x: self.pagerank_scores.get(x, 0), reverse=True)
        start = seeds[0]

        chain = [self._node_summary(start)]
        visited = {start}
        cur = start
        for _ in range(depth):
            neighbors = self.edges.get(cur, [])
            if not neighbors:
                break
            # Pick the neighbour with highest PageRank (not yet visited)
            candidates = [
                (tgt, self.pagerank_scores.get(tgt, 0))
                for tgt, _, _ in neighbors if tgt not in visited
            ]
            if not candidates:
                break
            candidates.sort(key=lambda x: x[1], reverse=True)
            best = candidates[0][0]
            chain.append(self._node_summary(best))
            visited.add(best)
            cur = best
        return chain

    # ── filing authority ranker ─────────────────────────────────────
    def rank_filing_authorities(self, filing_type: str) -> list:
        """
        For a filing type (e.g. 'motion', 'appeal', 'custody'),
        find relevant authorities ranked by PageRank.
        Cross-references auth_rules for full rule text.
        """
        query = filing_type.lower()
        # Find matching nodes
        matched = []
        for nid, nd in self.nodes.items():
            lbl = nd.get("label", "").lower()
            ntype = nd.get("node_type", "").lower()
            if query in lbl or query in ntype:
                matched.append(nid)

        # If no direct label match, search auth_rules table
        if len(matched) < 5:
            try:
                conn = sqlite3.connect(self.db_path)
                cur = conn.cursor()
                cur.execute(
                    "SELECT rule_number FROM auth_rules WHERE full_text LIKE ? LIMIT 50",
                    (f"%{filing_type}%",),
                )
                rule_nums = [r[0] for r in cur.fetchall()]
                conn.close()
                # Match rule numbers to nodes
                for rn in rule_nums:
                    rn_clean = rn.lower().replace(" ", "")
                    for nid, nd in self.nodes.items():
                        if rn_clean in nd.get("label", "").lower().replace(" ", ""):
                            if nid not in matched:
                                matched.append(nid)
            except Exception:
                pass

        # Rank by PageRank
        results = []
        for nid in matched:
            nd = self.nodes[nid]
            results.append({
                "node_id": nid,
                "label": nd.get("label", nid),
                "node_type": nd.get("node_type"),
                "pagerank": round(self.pagerank_scores.get(nid, 0), 8),
                "in_degree": len(self.reverse_edges.get(nid, [])),
            })
        results.sort(key=lambda x: x["pagerank"], reverse=True)
        return results[:50]

    # ── status ──────────────────────────────────────────────────────
    def status(self) -> dict:
        """System health: node count, edge count, top authorities."""
        total_edges = sum(len(v) for v in self.edges.values())
        top5 = self.get_top_authorities(n=5)
        nodes_with_edges = len([n for n in self.nodes if self.edges.get(n) or self.reverse_edges.get(n)])
        return {
            "node_count": len(self.nodes),
            "nodes_with_edges": nodes_with_edges,
            "edge_count": total_edges,
            "pagerank_computed": len(self.pagerank_scores) > 0,
            "cache_file": str(CACHE_FILE),
            "cache_exists": CACHE_FILE.exists(),
            "top_5_authorities": top5,
        }

    # ── self test ───────────────────────────────────────────────────
    def self_test(self) -> dict:
        """Validate engine integrity."""
        results = {"tests": [], "passed": 0, "failed": 0}

        def _check(name, condition, detail=""):
            ok = bool(condition)
            results["tests"].append({"name": name, "passed": ok, "detail": detail})
            if ok:
                results["passed"] += 1
            else:
                results["failed"] += 1

        _check("nodes_loaded", len(self.nodes) > 10000,
               f"{len(self.nodes):,} nodes loaded")
        _check("edges_loaded", sum(len(v) for v in self.edges.values()) > 100000,
               f"{sum(len(v) for v in self.edges.values()):,} edges loaded")
        _check("pagerank_computed", len(self.pagerank_scores) > 0,
               f"{len(self.pagerank_scores):,} scores")
        _check("pagerank_sums_to_1",
               abs(sum(self.pagerank_scores.values()) - 1.0) < 0.01,
               f"sum = {sum(self.pagerank_scores.values()):.6f}")

        # Top authority should be a real MCR rule
        top = self.get_top_authorities(n=1)
        if top:
            _check("top_authority_is_rule",
                   any(x in top[0]["label"].upper() for x in ("MCR", "MCL", "MRE")),
                   f"top = {top[0]['label']}")
        else:
            _check("top_authority_is_rule", False, "no top authority")

        # Score lookup works
        score_res = self.get_authority_score("MCR 2.003")
        _check("score_lookup_works", len(score_res.get("matches", [])) > 0,
               f"{len(score_res.get('matches',[]))} matches for MCR 2.003")

        # BFS works
        path = self.shortest_path("MCR 2.003", "MCR 7.204")
        _check("bfs_path_found",
               len(path) > 0 and "error" not in path[0],
               f"path length = {len(path)}")

        # Community detection runs
        comms = self.detect_communities(max_iter=5)
        _check("communities_detected", comms.get("total_communities", 0) > 0,
               f"{comms.get('total_communities', 0)} communities")

        # Neighbourhood query works
        nbr = self.get_authority_neighborhood("MCR 2.003", depth=1)
        _check("neighborhood_works",
               nbr.get("node_count", 0) > 0,
               f"{nbr.get('node_count', 0)} nodes in 1-hop neighborhood")

        results["all_passed"] = results["failed"] == 0
        return results


# ═══════════════════════════════════════════════════════════════════
#  CLI
# ═══════════════════════════════════════════════════════════════════
def _print_json(obj):
    print(json.dumps(obj, indent=2, default=str))


def main():
    args = sys.argv[1:]
    if not args:
        print("Authority PageRank Engine — MBP LitigationOS 2026")
        print("Commands: build, top [N] [type], score <rule>, path <src> <tgt>,")
        print("          neighborhood <rule> [depth], communities, chain <topic> [depth],")
        print("          filing <type>, status, self-test")
        return

    cmd = args[0].lower()

    if cmd == "build":
        # Force rebuild (delete cache)
        if CACHE_FILE.exists():
            CACHE_FILE.unlink()
            print("[build] Cache deleted; rebuilding …")
        engine = AuthorityPageRank()
        _print_json(engine.status())

    elif cmd == "top":
        engine = AuthorityPageRank()
        n = int(args[1]) if len(args) > 1 else 50
        ntype = args[2] if len(args) > 2 else None
        _print_json(engine.get_top_authorities(n, ntype))

    elif cmd == "score":
        engine = AuthorityPageRank()
        rule = " ".join(args[1:])
        _print_json(engine.get_authority_score(rule))

    elif cmd == "path":
        engine = AuthorityPageRank()
        if len(args) < 3:
            print("Usage: path <source_label> <target_label>")
            return
        _print_json(engine.shortest_path(args[1], args[2]))

    elif cmd == "neighborhood":
        engine = AuthorityPageRank()
        label = args[1] if len(args) > 1 else "MCR 2.003"
        depth = int(args[2]) if len(args) > 2 else 2
        result = engine.get_authority_neighborhood(label, depth)
        # summarise instead of dumping all edges
        print(f"Neighborhood of '{label}' (depth={depth}):")
        print(f"  Nodes: {result.get('node_count', 0)}")
        print(f"  Edges: {result.get('edge_count', 0)}")
        for nd in result.get("nodes", [])[:20]:
            print(f"  [{nd['hop_distance']}] {nd['label']} (PR={nd['pagerank']:.6f})")

    elif cmd == "communities":
        engine = AuthorityPageRank()
        result = engine.detect_communities()
        print(f"Total communities: {result['total_communities']}")
        print(f"Active nodes: {result['active_nodes']}")
        for cid, data in list(result["communities"].items())[:10]:
            print(f"\n{cid} ({data['size']} members):")
            for m in data["members"][:10]:
                print(f"  - {m}")

    elif cmd == "chain":
        engine = AuthorityPageRank()
        topic = args[1] if len(args) > 1 else "custody"
        depth = int(args[2]) if len(args) > 2 else 3
        _print_json(engine.get_strongest_chain(topic, depth))

    elif cmd == "filing":
        engine = AuthorityPageRank()
        ftype = " ".join(args[1:]) if len(args) > 1 else "motion"
        _print_json(engine.rank_filing_authorities(ftype))

    elif cmd == "status":
        engine = AuthorityPageRank()
        _print_json(engine.status())

    elif cmd in ("self-test", "selftest", "test"):
        engine = AuthorityPageRank()
        results = engine.self_test()
        for t in results["tests"]:
            icon = "✓" if t["passed"] else "✗"
            print(f"  {icon} {t['name']}: {t['detail']}")
        print(f"\n{'ALL PASSED' if results['all_passed'] else 'FAILURES DETECTED'}: "
              f"{results['passed']}/{results['passed']+results['failed']}")

    else:
        print(f"Unknown command: {cmd}")


if __name__ == "__main__":
    main()
