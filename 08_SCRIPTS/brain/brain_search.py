#!/usr/bin/env python3
"""
MBP LitigationOS — Brain Graph + DB Integrated Search
======================================================
Loads all 5 brain nuclei graphs, builds a unified adjacency index,
then enriches graph traversals with full DB content from
litigation_context.db.

Nuclei:
  - evidence_nucleus.json   (200 nodes, 819 edges)
  - filing_nucleus.json     (150 nodes, 850 edges)
  - legal_nucleus.json      (200 nodes, 2745 edges)
  - party_nucleus.json      (150 nodes, 221 edges)
  - timeline_nucleus.json   (250 nodes, 767 edges)

Functions:
  brain_search(query, depth, limit)   → cross-nucleus search + DB enrichment
  get_node_context(node_id)           → single node + edges + DB content
  find_connections(node_id, depth)    → BFS traversal returning reachable nodes

Usage:
    python brain_search.py
"""

from __future__ import annotations

import json
import logging
import os
import re
import sqlite3
import sys
import time

logger = logging.getLogger(__name__)
from collections import deque
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from cycle_method import cycle_json, cycle_print
except ImportError:
    cycle_json = lambda obj, **kw: print(json.dumps(obj, default=str))
    cycle_print = print

DB_PATH = os.environ.get(
    "LITIGATION_DB_PATH",
    r"C:\Users\andre\litigation_context.db",
)
NUCLEI_DIR = Path(__file__).parent / "nuclei"

# ── Edge-type → DB table mapping ────────────────────────────────────
EDGE_TABLE_MAP: Dict[str, List[str]] = {
    "CITES":                ["auth_rules", "rules_text", "master_citations"],
    "SUPPORTS":             ["evidence_quotes", "claims"],
    "PRESERVES_ISSUES":     ["claims", "vehicles"],
    "APPEAL_OF_RIGHT":      ["vehicles", "docket_events"],
    "APPLICATION_FOR_LEAVE": ["vehicles", "docket_events"],
    "PREREQUISITE":         ["vehicles", "deadlines"],
}

# ── Reference-prefix → DB table + column mapping ────────────────────
REF_TABLE_MAP: List[Tuple[str, str, str]] = [
    # (prefix, table, column)
    ("MCR",  "auth_rules",  "rule_number"),
    ("MCL",  "auth_rules",  "rule_number"),
    ("MRE",  "auth_rules",  "rule_number"),
    ("MCR",  "rules_text",  "rule"),
    ("MCL",  "rules_text",  "rule"),
]


def _safe_text(val: Any, max_len: int = 500) -> str:
    """Safely convert DB value to string."""
    if val is None:
        return ""
    try:
        s = str(val).strip()
    except Exception:
        s = str(val).encode("utf-8", errors="replace").decode("utf-8", errors="replace").strip()
    return s[:max_len] if len(s) > max_len else s


def _extract_rule_number(ref: str) -> str:
    """Extract numeric portion from a reference like 'MCR 2.116' → '2.116'."""
    m = re.search(r'[\d]+[.\d]*', ref)
    return m.group(0) if m else ref


# ── Brain Search Engine ─────────────────────────────────────────────
class BrainSearch:
    """
    Unified brain-graph + DB search engine.

    Loads all nuclei into a single node index and adjacency list, then
    provides three search primitives that combine graph traversal with
    DB content retrieval.
    """

    def __init__(self, db_path: str = DB_PATH, nuclei_dir: Path = NUCLEI_DIR):
        self.db_path = db_path
        self.nuclei_dir = nuclei_dir
        self._conn: Optional[sqlite3.Connection] = None

        # Unified indexes
        self.nodes: Dict[str, Dict] = {}          # node_id → node dict
        self.node_nucleus: Dict[str, str] = {}     # node_id → nucleus_id
        self.adj: Dict[str, List[Dict]] = {}       # node_id → [{to, type, brain}]
        self.rev_adj: Dict[str, List[Dict]] = {}   # target → [{from, type, brain}]

        self._load_nuclei()

    # ── Nucleus loading ─────────────────────────────────────────────

    def _load_nuclei(self) -> None:
        """Load all nucleus JSON files and build unified indexes.

        Node IDs are namespaced as ``{nucleus_id}:{original_id}`` to
        avoid collisions (all nuclei use e0001-e0250).
        """
        if not self.nuclei_dir.exists():
            cycle_print(f"  [WARN] Nuclei directory not found: {self.nuclei_dir}")
            return

        total_nodes = 0
        total_edges = 0
        nuclei_loaded: Set[str] = set()

        for json_file in sorted(self.nuclei_dir.glob("*.json")):
            try:
                with open(json_file, "r", encoding="utf-8", errors="replace") as f:
                    data = json.load(f)
            except Exception as e:
                cycle_print(f"  [WARN] Failed to load {json_file.name}: {e}")
                continue

            nucleus_id = data.get("nucleus_id", json_file.stem)
            nuclei_loaded.add(nucleus_id)

            # Index nodes with namespaced key
            for node in data.get("nodes", []):
                raw_id = node.get("id", "")
                if not raw_id:
                    continue
                ns_id = f"{nucleus_id}:{raw_id}"
                self.nodes[ns_id] = node
                self.node_nucleus[ns_id] = nucleus_id
                total_nodes += 1

            # Index edges — namespace source IDs; targets are typically
            # external refs (e.g. "MCR 2.116") so leave them as-is.
            for edge in data.get("edges", []):
                src_raw = edge.get("from", "")
                tgt = edge.get("to", "")
                if not src_raw or not tgt:
                    continue

                ns_src = f"{nucleus_id}:{src_raw}"

                edge_rec = {
                    "to": tgt,
                    "type": edge.get("type", "RELATED"),
                    "brain": edge.get("brain", ""),
                }
                self.adj.setdefault(ns_src, []).append(edge_rec)

                rev_rec = {
                    "from": ns_src,
                    "type": edge.get("type", "RELATED"),
                    "brain": edge.get("brain", ""),
                }
                self.rev_adj.setdefault(tgt, []).append(rev_rec)
                total_edges += 1

        cycle_print(f"  Loaded {total_nodes} nodes, {total_edges} edges from {len(nuclei_loaded)} nuclei")

    # ── DB connection ───────────────────────────────────────────────

    def _get_db(self) -> sqlite3.Connection:
        """Get or create a read-only DB connection with retry."""
        if self._conn is not None:
            try:
                self._conn.execute("SELECT 1")
                return self._conn
            except Exception:
                self._conn = None

        retries = 3
        for attempt in range(retries):
            try:
                self._conn = sqlite3.connect(self.db_path, timeout=30)
                self._conn.execute("PRAGMA journal_mode=WAL")
                self._conn.execute("PRAGMA cache_size=-65536")
                self._conn.execute("PRAGMA query_only=ON")
                return self._conn
            except Exception as e:
                if attempt < retries - 1:
                    time.sleep(1 * (2 ** attempt))
                else:
                    raise RuntimeError(f"DB connection failed after {retries} attempts: {e}")

    # ── DB lookup helpers ───────────────────────────────────────────

    def _lookup_reference(self, ref: str) -> List[Dict]:
        """
        Look up a graph reference (e.g. 'MCR 2.116') in DB tables.
        Returns list of matching rows as dicts.
        """
        conn = self._get_db()
        results: List[Dict] = []
        ref_upper = ref.upper().strip()
        rule_num = _extract_rule_number(ref)

        for prefix, table, column in REF_TABLE_MAP:
            if not ref_upper.startswith(prefix):
                continue
            try:
                col_info = conn.execute(f"PRAGMA table_info([{table}])").fetchall()
                col_names = [c[1] for c in col_info]
                rows = conn.execute(
                    f"SELECT * FROM [{table}] WHERE [{column}] LIKE ? LIMIT 5",
                    (f"%{rule_num}%",),
                ).fetchall()
                for row in rows:
                    results.append({
                        "_table": table,
                        **{col_names[i]: _safe_text(row[i], 400) for i in range(len(col_names))},
                    })
            except Exception as e:
                logger.warning(f"DB lookup failed for ref '{ref}' in table '{table}': {e}")
                continue

        return results

    def _search_fts(self, fts_table: str, query: str, limit: int = 10) -> List[Dict]:
        """Search an FTS5 table, returning ranked results."""
        conn = self._get_db()
        sanitized = re.sub(r'[^\w\s]', ' ', query)
        terms = [w for w in sanitized.split() if len(w) >= 3]
        if not terms:
            return []

        fts_query = " OR ".join(terms)
        results: List[Dict] = []

        try:
            rows = conn.execute(
                f"SELECT rowid, rank, * FROM [{fts_table}] "
                f"WHERE [{fts_table}] MATCH ? ORDER BY rank LIMIT ?",
                (fts_query, limit),
            ).fetchall()
            for row in rows:
                row_dict = {"_table": fts_table, "rowid": row[0], "rank": row[1]}
                for i, val in enumerate(row[2:], 2):
                    row_dict[f"col_{i - 2}"] = _safe_text(val, 400)
                results.append(row_dict)
        except Exception as e:
            logger.warning(f"FTS search failed on '{fts_table}': {e}")

        return results

    def _search_table_like(self, table: str, query: str, limit: int = 10) -> List[Dict]:
        """Fallback LIKE search across text columns of a table."""
        conn = self._get_db()
        try:
            col_info = conn.execute(f"PRAGMA table_info([{table}])").fetchall()
        except Exception as e:
            logger.warning(f"PRAGMA table_info failed for table '{table}': {e}")
            return []

        col_names = [c[1] for c in col_info]
        text_cols = [c[1] for c in col_info if c[2].upper() in ("TEXT", "")]
        if not text_cols:
            return []

        words = [w for w in query.split() if len(w) >= 3]
        if not words:
            return []

        where_parts = []
        params = []
        for word in words[:5]:
            col_checks = " OR ".join(f"[{c}] LIKE ?" for c in text_cols[:5])
            where_parts.append(f"({col_checks})")
            params.extend([f"%{word}%"] * min(len(text_cols), 5))

        sql = f"SELECT * FROM [{table}] WHERE {' AND '.join(where_parts)} LIMIT {limit}"

        results: List[Dict] = []
        try:
            rows = conn.execute(sql, params).fetchall()
            for row in rows:
                results.append({
                    "_table": table,
                    **{col_names[i]: _safe_text(row[i], 400) for i in range(len(col_names))},
                })
        except Exception as e:
            logger.warning(f"LIKE search failed on table '{table}': {e}")

        return results

    def _enrich_node_from_db(self, node: Dict, query: str = "") -> List[Dict]:
        """
        Given a node, follow its edges and look up referenced content in DB.
        Optionally also searches DB tables with ``query`` text.
        """
        nid = node.get("id", "")
        db_content: List[Dict] = []
        seen_refs: Set[str] = set()

        # Follow outgoing edges and look up each target
        for edge in self.adj.get(nid, []):
            target = edge["to"]
            if target in seen_refs:
                continue
            seen_refs.add(target)

            ref_results = self._lookup_reference(target)
            for r in ref_results:
                r["_edge_type"] = edge["type"]
                r["_edge_target"] = target
            db_content.extend(ref_results)

        # If a query was provided, also do FTS/LIKE search on relevant tables
        if query:
            edge_types = {e["type"] for e in self.adj.get(nid, [])}
            tables_to_search: Set[str] = set()
            for et in edge_types:
                tables_to_search.update(EDGE_TABLE_MAP.get(et, []))
            if not tables_to_search:
                tables_to_search = {"auth_rules", "evidence_quotes"}

            fts_map = {
                "auth_rules": "auth_rules_fts",
                "evidence_quotes": "evidence_quotes_fts",
                "rules_text": "rules_text_fts",
                "md_sections": "md_sections_fts",
                "pages": "pages_fts",
            }
            for tbl in tables_to_search:
                fts = fts_map.get(tbl)
                if fts:
                    db_content.extend(self._search_fts(fts, query, limit=5))
                else:
                    db_content.extend(self._search_table_like(tbl, query, limit=5))

        return db_content

    # ── Public API ──────────────────────────────────────────────────

    def brain_search(self, query: str, depth: int = 2, limit: int = 20) -> List[Dict]:
        """
        Cross-nucleus search: find matching nodes, follow edges up to
        ``depth`` hops, and enrich every result with DB content.

        Args:
            query: Natural language search string.
            depth: Max edge hops from each matching node.
            limit: Max top-level results to return.

        Returns:
            List of ``{node, related_nodes, db_content}`` dicts.
        """
        start = time.time()
        query_lower = query.lower()
        query_words = [w for w in query_lower.split() if len(w) >= 3]
        if not query_words:
            return []

        # Step 1 — Score every node against the query
        scored: List[Tuple[float, str]] = []
        for nid, node in self.nodes.items():
            text = _safe_text(node.get("text", "")).lower()
            score = sum(1 for w in query_words if w in text)
            if score > 0:
                # Boost by node's own score if present
                node_score = float(node.get("score", 0))
                score += node_score * 0.01
                scored.append((score, nid))

        scored.sort(key=lambda x: x[0], reverse=True)
        top_ids = [nid for _, nid in scored[:limit]]

        # Step 2 — For each match, collect related nodes via BFS
        results: List[Dict] = []
        for nid in top_ids:
            node = self.nodes[nid]
            related = self._bfs(nid, depth)

            # Step 3 — Enrich with DB content
            db_content = self._enrich_node_from_db(node, query)

            results.append({
                "node": {
                    "id": nid,
                    "text": _safe_text(node.get("text", ""), 300),
                    "score": node.get("score", 0),
                    "source": node.get("source", ""),
                    "brain": node.get("brain", ""),
                    "tags": node.get("tags", []),
                    "nucleus": self.node_nucleus.get(nid, ""),
                },
                "related_nodes": related[:20],
                "db_content": db_content,
            })

        elapsed = time.time() - start
        cycle_print(f"  brain_search completed in {elapsed:.3f}s — {len(results)} results")
        return results

    def _resolve_id(self, node_id: str) -> str:
        """Resolve a node_id to its namespaced form.

        Accepts ``'evidence:e0001'`` (already namespaced) or ``'e0001'``
        (returns first match across nuclei).
        """
        if node_id in self.nodes:
            return node_id
        # Try each nucleus prefix
        for ns_id in self.nodes:
            if ns_id.endswith(f":{node_id}"):
                return ns_id
        return node_id

    def get_node_context(self, node_id: str) -> Dict[str, Any]:
        """
        Full context for a single node: its data, all outgoing edges,
        and DB content for every edge target.

        Args:
            node_id: Node identifier — accepts ``'e0001'`` (searches all
                     nuclei) or ``'evidence:e0001'`` (exact).

        Returns:
            ``{node, edges, db_content}`` dict. Returns empty node if
            the id is not found.
        """
        node_id = self._resolve_id(node_id)
        node = self.nodes.get(node_id)
        if node is None:
            return {"node": {}, "edges": [], "db_content": {}}

        edges_out = self.adj.get(node_id, [])
        edges_in = self.rev_adj.get(node_id, [])

        # Collect all edges in a uniform format
        all_edges: List[Dict] = []
        for e in edges_out:
            all_edges.append({
                "direction": "out",
                "target": e["to"],
                "type": e["type"],
                "brain": e["brain"],
            })
        for e in edges_in:
            all_edges.append({
                "direction": "in",
                "source": e["from"],
                "type": e["type"],
                "brain": e["brain"],
            })

        # Look up DB content for each unique outgoing target
        db_content: Dict[str, List[Dict]] = {}
        for e in edges_out:
            target = e["to"]
            if target in db_content:
                continue
            rows = self._lookup_reference(target)
            if rows:
                db_content[target] = rows

        return {
            "node": {
                "id": node_id,
                "text": _safe_text(node.get("text", ""), 500),
                "score": node.get("score", 0),
                "source": node.get("source", ""),
                "brain": node.get("brain", ""),
                "tags": node.get("tags", []),
                "nucleus": self.node_nucleus.get(node_id, ""),
            },
            "edges": all_edges,
            "db_content": db_content,
        }

    def find_connections(self, node_id: str, depth: int = 2) -> List[Dict]:
        """
        BFS traversal from ``node_id`` up to ``depth`` hops.

        Args:
            node_id: Starting node identifier — accepts ``'e0001'``
                     (searches all nuclei) or ``'evidence:e0001'`` (exact).
            depth:   Maximum number of hops.

        Returns:
            List of ``{node_id, text, distance, path}`` dicts for every
            reachable node (excluding the start node itself).
        """
        node_id = self._resolve_id(node_id)
        return self._bfs(node_id, depth)

    # ── Internal BFS ────────────────────────────────────────────────

    def _bfs(self, start_id: str, max_depth: int) -> List[Dict]:
        """BFS from start_id, returning nodes within max_depth hops."""
        visited: Dict[str, int] = {start_id: 0}
        parent: Dict[str, Optional[str]] = {start_id: None}
        queue: deque = deque([(start_id, 0)])
        results: List[Dict] = []

        while queue:
            current, dist = queue.popleft()
            if dist >= max_depth:
                continue

            # Follow outgoing edges
            for edge in self.adj.get(current, []):
                neighbor = edge["to"]
                if neighbor not in visited:
                    visited[neighbor] = dist + 1
                    parent[neighbor] = current
                    queue.append((neighbor, dist + 1))

            # Follow incoming edges (reverse)
            for edge in self.rev_adj.get(current, []):
                neighbor = edge["from"]
                if neighbor not in visited:
                    visited[neighbor] = dist + 1
                    parent[neighbor] = current
                    queue.append((neighbor, dist + 1))

        # Build results (skip start node)
        for nid, dist in sorted(visited.items(), key=lambda x: x[1]):
            if nid == start_id:
                continue

            # Reconstruct path
            path = []
            cur = nid
            while cur is not None:
                path.append(cur)
                cur = parent.get(cur)
            path.reverse()

            node = self.nodes.get(nid)
            text = _safe_text(node.get("text", ""), 200) if node else nid

            results.append({
                "node_id": nid,
                "text": text,
                "distance": dist,
                "path": path,
            })

        return results

    # ── Cleanup ─────────────────────────────────────────────────────

    def close(self) -> None:
        """Close the database connection."""
        if self._conn:
            try:
                self._conn.close()
            except Exception as e:
                logger.warning(f"Error closing DB connection: {e}")
            self._conn = None


# ── Self-test ───────────────────────────────────────────────────────
if __name__ == "__main__":
    searcher = BrainSearch()

    # brain_search test
    results = searcher.brain_search("parental alienation evidence")
    cycle_print(f"brain_search: {len(results)} results")

    # get_node_context test
    ctx = searcher.get_node_context("e0001")
    cycle_print(f"get_node_context: {len(ctx.get('edges', []))} edges")

    # find_connections test
    conns = searcher.find_connections("e0001", depth=2)
    cycle_print(f"find_connections: {len(conns)} nodes within 2 hops")

    searcher.close()
    cycle_print("[brain_search] All tests passed")
