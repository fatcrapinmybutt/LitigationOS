"""
MBP LitigationOS — Knowledge Graph Engine
==========================================
Uses python-igraph to build, cache, and analyze the authority knowledge graph
from litigation_context.db (auth_authority_nodes / auth_authority_edges).

Capabilities:
  - Community detection (Louvain)
  - Centrality analysis (degree, betweenness, eigenvector)
  - Shortest-path finding between authorities
  - Ego-subgraph extraction
  - Query-driven related-authority discovery
"""

import igraph
import sqlite3
import json
import os
import pickle
import time
import numpy as np
from typing import Dict, List, Optional, Any, Tuple


class KnowledgeGraphEngine:
    """Knowledge graph over the Michigan litigation authority corpus."""

    DEFAULT_DB = r"C:\Users\andre\LitigationOS\litigation_context.db"
    DEFAULT_CACHE_DIR = os.path.join(
        r"C:\Users\andre\LitigationOS\00_SYSTEM\local_model", "cache"
    )
    CACHE_FILENAME = "knowledge_graph.pkl"

    def __init__(
        self,
        db_path: str = DEFAULT_DB,
        cache_dir: Optional[str] = None,
    ):
        self.db_path = db_path
        self.cache_dir = cache_dir or self.DEFAULT_CACHE_DIR
        self.cache_path = os.path.join(self.cache_dir, self.CACHE_FILENAME)
        self.graph: Optional[igraph.Graph] = None
        # label -> vertex index for O(1) lookup
        self._label_index: Dict[str, int] = {}
        self._node_id_index: Dict[str, int] = {}

    # ------------------------------------------------------------------
    # Graph construction
    # ------------------------------------------------------------------

    def build_graph(self) -> igraph.Graph:
        """Pull nodes/edges from the DB and build an igraph.Graph."""
        t0 = time.time()
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # --- nodes ---
        cur.execute("SELECT id, label, node_type FROM auth_authority_nodes")
        rows = cur.fetchall()
        node_ids: List[str] = []
        labels: List[str] = []
        node_types: List[str] = []
        id_to_idx: Dict[str, int] = {}

        for idx, r in enumerate(rows):
            nid = r["id"]
            node_ids.append(nid)
            labels.append(r["label"] or "")
            node_types.append(r["node_type"] or "")
            id_to_idx[nid] = idx

        n_vertices = len(node_ids)

        # --- edges (batch fetch) ---
        cur.execute("SELECT source_id, target_id, edge_type, weight FROM auth_authority_edges")
        edge_src: List[int] = []
        edge_tgt: List[int] = []
        edge_types: List[str] = []
        edge_weights: List[float] = []
        skipped = 0

        for r in cur:
            sid = id_to_idx.get(r["source_id"])
            tid = id_to_idx.get(r["target_id"])
            if sid is None or tid is None:
                skipped += 1
                continue
            edge_src.append(sid)
            edge_tgt.append(tid)
            edge_types.append(r["edge_type"] or "")
            edge_weights.append(r["weight"] if r["weight"] is not None else 1.0)

        conn.close()

        # --- build graph ---
        g = igraph.Graph(directed=True)
        g.add_vertices(n_vertices)
        g.vs["name"] = node_ids
        g.vs["label"] = labels
        g.vs["node_type"] = node_types

        edges = list(zip(edge_src, edge_tgt))
        g.add_edges(edges)
        g.es["edge_type"] = edge_types
        g.es["weight"] = edge_weights

        self.graph = g
        self._rebuild_indexes()

        # --- cache ---
        self._save_cache()

        elapsed = time.time() - t0
        print(
            f"[KnowledgeGraph] Built graph: {g.vcount()} nodes, "
            f"{g.ecount()} edges ({skipped} orphan edges skipped) "
            f"in {elapsed:.1f}s"
        )
        return g

    def load_graph(self) -> igraph.Graph:
        """Load a previously cached graph from disk."""
        if not os.path.exists(self.cache_path):
            raise FileNotFoundError(
                f"No cached graph at {self.cache_path}. Run build_graph() first."
            )
        t0 = time.time()
        with open(self.cache_path, "rb") as f:
            self.graph = pickle.load(f)
        self._rebuild_indexes()
        elapsed = time.time() - t0
        print(
            f"[KnowledgeGraph] Loaded cached graph: {self.graph.vcount()} nodes, "
            f"{self.graph.ecount()} edges in {elapsed:.1f}s"
        )
        return self.graph

    def _ensure_graph(self):
        """Load or build the graph if not already in memory."""
        if self.graph is not None:
            return
        if os.path.exists(self.cache_path):
            self.load_graph()
        else:
            self.build_graph()

    def _rebuild_indexes(self):
        """Build fast lookup dicts from vertex attributes."""
        self._label_index = {}
        self._node_id_index = {}
        for v in self.graph.vs:
            lbl = v["label"]
            if lbl:
                self._label_index[lbl] = v.index
            nid = v["name"]
            if nid:
                self._node_id_index[nid] = v.index

    def _save_cache(self):
        os.makedirs(self.cache_dir, exist_ok=True)
        with open(self.cache_path, "wb") as f:
            pickle.dump(self.graph, f, protocol=pickle.HIGHEST_PROTOCOL)

    # ------------------------------------------------------------------
    # Community detection
    # ------------------------------------------------------------------

    def community_detection(self) -> Dict[str, Any]:
        """Run Louvain community detection. Returns top-20 communities."""
        self._ensure_graph()
        t0 = time.time()

        # Louvain works on undirected graphs
        g_undirected = self.graph.as_undirected(combine_edges="first")
        membership = g_undirected.community_multilevel(
            weights="weight", return_levels=False
        )

        # membership is a VertexClustering object
        n_communities = len(membership)
        sizes = membership.sizes()

        # Sort communities by size descending; keep top 20
        indexed_sizes = sorted(enumerate(sizes), key=lambda x: -x[1])[:20]

        top_communities = []
        for comm_id, size in indexed_sizes:
            members = membership[comm_id]
            # Pick top-5 nodes by degree within the community subgraph
            degs = [(m, self.graph.degree(m, mode="all")) for m in members]
            degs.sort(key=lambda x: -x[1])
            top_nodes = [
                {
                    "label": self.graph.vs[m]["label"],
                    "node_type": self.graph.vs[m]["node_type"],
                    "degree": d,
                }
                for m, d in degs[:5]
            ]
            top_communities.append(
                {"community_id": comm_id, "size": size, "top_nodes": top_nodes}
            )

        elapsed = time.time() - t0
        return {
            "community_count": n_communities,
            "top_20_communities": top_communities,
            "modularity": membership.modularity,
            "elapsed_seconds": round(elapsed, 2),
        }

    # ------------------------------------------------------------------
    # Centrality analysis
    # ------------------------------------------------------------------

    def centrality_analysis(self, top_k: int = 50) -> Dict[str, List[Dict]]:
        """Compute degree / betweenness / eigenvector centrality; return top-K."""
        self._ensure_graph()
        t0 = time.time()

        n = self.graph.vcount()
        k = min(top_k, n)

        # Degree centrality (total = in + out for directed)
        deg = self.graph.degree(mode="all")
        deg_top = np.argsort(deg)[::-1][:k]
        degree_results = [
            {
                "label": self.graph.vs[int(i)]["label"],
                "node_type": self.graph.vs[int(i)]["node_type"],
                "degree": deg[int(i)],
            }
            for i in deg_top
        ]

        # Betweenness (directed, sample for speed on large graphs)
        if n > 5000:
            # Use cutoff to limit computation on large graphs
            btwn = self.graph.betweenness(directed=True, cutoff=4, weights=None)
        else:
            btwn = self.graph.betweenness(directed=True, weights=None)
        btwn_top = np.argsort(btwn)[::-1][:k]
        betweenness_results = [
            {
                "label": self.graph.vs[int(i)]["label"],
                "node_type": self.graph.vs[int(i)]["node_type"],
                "betweenness": round(btwn[int(i)], 2),
            }
            for i in btwn_top
        ]

        # Eigenvector centrality (undirected version for stability)
        g_und = self.graph.as_undirected(combine_edges="first")
        try:
            eig = g_und.eigenvector_centrality(weights="weight")
        except Exception:
            try:
                eig = g_und.eigenvector_centrality(weights=None)
            except Exception:
                # Final fallback: use PageRank as proxy
                eig = g_und.pagerank(weights="weight")
        eig_top = np.argsort(eig)[::-1][:k]
        eigenvector_results = [
            {
                "label": self.graph.vs[int(i)]["label"],
                "node_type": self.graph.vs[int(i)]["node_type"],
                "eigenvector": round(eig[int(i)], 6),
            }
            for i in eig_top
        ]

        elapsed = time.time() - t0
        return {
            "degree": degree_results,
            "betweenness": betweenness_results,
            "eigenvector": eigenvector_results,
            "elapsed_seconds": round(elapsed, 2),
        }

    # ------------------------------------------------------------------
    # Path finding
    # ------------------------------------------------------------------

    def find_path(
        self, source_label: str, target_label: str
    ) -> Dict[str, Any]:
        """Find shortest path between two nodes identified by label."""
        self._ensure_graph()

        src_idx = self._label_index.get(source_label)
        tgt_idx = self._label_index.get(target_label)

        if src_idx is None:
            return {"error": f"Source node not found: '{source_label}'"}
        if tgt_idx is None:
            return {"error": f"Target node not found: '{target_label}'"}

        try:
            path_ids = self.graph.get_shortest_paths(
                src_idx, to=tgt_idx, mode="all", output="vpath"
            )[0]
        except Exception as e:
            return {"error": str(e)}

        if not path_ids:
            return {
                "source": source_label,
                "target": target_label,
                "reachable": False,
                "path": [],
            }

        path_labels = [
            {
                "label": self.graph.vs[i]["label"],
                "node_type": self.graph.vs[i]["node_type"],
            }
            for i in path_ids
        ]
        return {
            "source": source_label,
            "target": target_label,
            "reachable": True,
            "length": len(path_ids) - 1,
            "path": path_labels,
        }

    # ------------------------------------------------------------------
    # Subgraph extraction
    # ------------------------------------------------------------------

    def subgraph_around(
        self, node_label: str, depth: int = 2
    ) -> Dict[str, Any]:
        """Extract ego subgraph around a node up to *depth* hops."""
        self._ensure_graph()

        center = self._label_index.get(node_label)
        if center is None:
            return {"error": f"Node not found: '{node_label}'"}

        # BFS neighborhood
        neighbors = self.graph.neighborhood(
            vertices=center, order=depth, mode="all"
        )

        sub = self.graph.subgraph(neighbors)

        nodes_out = [
            {
                "label": v["label"],
                "node_type": v["node_type"],
            }
            for v in sub.vs
        ]
        edges_out = [
            {
                "source": sub.vs[e.source]["label"],
                "target": sub.vs[e.target]["label"],
                "edge_type": e["edge_type"],
            }
            for e in sub.es
        ]

        return {
            "center": node_label,
            "depth": depth,
            "node_count": sub.vcount(),
            "edge_count": sub.ecount(),
            "nodes": nodes_out,
            "edges": edges_out,
        }

    # ------------------------------------------------------------------
    # Related authority discovery
    # ------------------------------------------------------------------

    def find_related_authorities(
        self, query_text: str, top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """Find authorities related to *query_text* via label matching + graph expansion."""
        self._ensure_graph()

        terms = [t.lower().strip() for t in query_text.split() if len(t) > 2]
        if not terms:
            return []

        # Phase 1: find seed nodes whose labels contain any query term
        seed_scores: Dict[int, int] = {}
        for v in self.graph.vs:
            lbl_lower = (v["label"] or "").lower()
            hits = sum(1 for t in terms if t in lbl_lower)
            if hits > 0:
                seed_scores[v.index] = hits

        if not seed_scores:
            return []

        # Phase 2: expand seeds by 1-hop neighbors, accumulate scores
        expanded: Dict[int, float] = {}
        for idx, score in seed_scores.items():
            expanded[idx] = expanded.get(idx, 0) + score * 2.0  # direct match bonus
            for nb in self.graph.neighbors(idx, mode="all"):
                expanded[nb] = expanded.get(nb, 0) + score * 0.5

        # Rank and return top-K
        ranked = sorted(expanded.items(), key=lambda x: -x[1])[:top_k]
        results = []
        for idx, score in ranked:
            v = self.graph.vs[idx]
            results.append(
                {
                    "label": v["label"],
                    "node_type": v["node_type"],
                    "relevance_score": round(score, 2),
                    "degree": self.graph.degree(idx, mode="all"),
                }
            )
        return results

    # ------------------------------------------------------------------
    # Statistics
    # ------------------------------------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        """Return summary statistics of the knowledge graph."""
        self._ensure_graph()
        g = self.graph
        n = g.vcount()
        m = g.ecount()
        density = g.density()

        # Approximate diameter and avg path length on a sample (expensive on full graph)
        sample_size = min(500, n)
        rng = np.random.default_rng(42)
        sample_ids = rng.choice(n, size=sample_size, replace=False).tolist()

        path_lengths = []
        for s in sample_ids[:100]:
            dists = g.distances(source=int(s), target=sample_ids, mode="all")[0]
            for d in dists:
                if 0 < d < float("inf"):
                    path_lengths.append(d)

        approx_diameter = max(path_lengths) if path_lengths else -1
        avg_path = float(np.mean(path_lengths)) if path_lengths else -1

        # Community count (reuse Louvain)
        g_und = g.as_undirected(combine_edges="first")
        membership = g_und.community_multilevel(weights="weight", return_levels=False)

        # Node-type distribution
        type_counts: Dict[str, int] = {}
        for v in g.vs:
            nt = v["node_type"] or "unknown"
            type_counts[nt] = type_counts.get(nt, 0) + 1

        return {
            "node_count": n,
            "edge_count": m,
            "density": round(density, 6),
            "approx_diameter": approx_diameter,
            "avg_path_length_sample": round(avg_path, 2) if avg_path > 0 else None,
            "community_count": len(membership),
            "modularity": round(membership.modularity, 4),
            "node_type_distribution": dict(
                sorted(type_counts.items(), key=lambda x: -x[1])
            ),
        }

    # ------------------------------------------------------------------
    # Self-test
    # ------------------------------------------------------------------

    @staticmethod
    def self_test():
        """Build/load graph, run community detection, centrality, and path finding."""
        print("=" * 60)
        print("  KnowledgeGraphEngine — Self-Test")
        print("=" * 60)

        engine = KnowledgeGraphEngine()

        # Build or load
        if os.path.exists(engine.cache_path):
            engine.load_graph()
        else:
            engine.build_graph()

        g = engine.graph
        print(f"\nGraph loaded: {g.vcount()} vertices, {g.ecount()} edges")

        # Stats
        print("\n--- Statistics ---")
        stats = engine.get_stats()
        for k, v in stats.items():
            if k != "node_type_distribution":
                print(f"  {k}: {v}")
        print("  node_type_distribution (top 10):")
        for nt, cnt in list(stats["node_type_distribution"].items())[:10]:
            print(f"    {nt}: {cnt}")

        # Community detection
        print("\n--- Community Detection (Louvain) ---")
        comm = engine.community_detection()
        print(f"  Communities: {comm['community_count']}")
        print(f"  Modularity:  {comm['modularity']:.4f}")
        print(f"  Elapsed:     {comm['elapsed_seconds']}s")
        for c in comm["top_20_communities"][:5]:
            top_lbl = c["top_nodes"][0]["label"] if c["top_nodes"] else "?"
            print(f"  Comm {c['community_id']}: size={c['size']}, top='{top_lbl}'")

        # Centrality
        print("\n--- Centrality Analysis (top 10) ---")
        cent = engine.centrality_analysis(top_k=10)
        print(f"  Elapsed: {cent['elapsed_seconds']}s")
        print("  Degree:")
        for r in cent["degree"][:5]:
            print(f"    {r['label']} ({r['node_type']}): {r['degree']}")
        print("  Betweenness:")
        for r in cent["betweenness"][:5]:
            print(f"    {r['label']} ({r['node_type']}): {r['betweenness']}")
        print("  Eigenvector:")
        for r in cent["eigenvector"][:5]:
            print(f"    {r['label']} ({r['node_type']}): {r['eigenvector']}")

        # Path finding — pick two high-degree nodes
        print("\n--- Path Finding ---")
        if cent["degree"] and len(cent["degree"]) >= 2:
            src = cent["degree"][0]["label"]
            tgt = cent["degree"][-1]["label"]
            result = engine.find_path(src, tgt)
            if result.get("reachable"):
                labels = " -> ".join(p["label"] for p in result["path"])
                print(f"  {src}  -->  {tgt}")
                print(f"  Length: {result['length']}")
                print(f"  Path:   {labels}")
            else:
                print(f"  No path between '{src}' and '{tgt}'")

        # Related authorities
        print("\n--- Related Authorities (query: 'custody best interest') ---")
        related = engine.find_related_authorities("custody best interest", top_k=10)
        for r in related:
            print(
                f"  {r['label']} ({r['node_type']}) "
                f"score={r['relevance_score']} deg={r['degree']}"
            )

        print("\n" + "=" * 60)
        print("  Self-test complete.")
        print("=" * 60)


if __name__ == "__main__":
    KnowledgeGraphEngine.self_test()
