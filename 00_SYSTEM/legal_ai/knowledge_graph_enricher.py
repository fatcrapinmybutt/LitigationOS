"""
Knowledge Graph Enricher — LitigationOS Legal AI
==================================================
Enrich the legal authority knowledge graph with citation traversal,
PageRank-style authority scoring, cluster detection, and gap analysis.

Features:
  - Load/persist authority graph from litigation_context.db
  - Simplified PageRank (stdlib-only, no numpy)
  - Connected-component clustering with density scoring
  - Gap analysis per case lane
  - Seed graph from embedded Michigan family law authorities
  - Mermaid diagram and JSON export

Usage:
    from legal_ai.knowledge_graph_enricher import KnowledgeGraphEnricher
    enricher = KnowledgeGraphEnricher()
    enricher.enrich_from_seeds()
    enricher.compute_pagerank()
    report = enricher.generate_report()
"""
from __future__ import annotations

import hashlib
import json
import logging
import math
import re
import sqlite3
import time
from collections import defaultdict, deque
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger("legal_ai.knowledge_graph_enricher")

_HERE = Path(__file__).parent
_REPO = _HERE.parent.parent
_DB_PATH = _REPO / "litigation_context.db"

# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class AuthorityNode:
    """A single authority in the knowledge graph."""

    node_id: str
    citation: str
    authority_type: str  # case, statute, rule, regulation, constitution
    jurisdiction: str  # MI, 6th_Circuit, SCOTUS, WDMI, MCR, MCL
    year: Optional[int] = None
    court: Optional[str] = None
    relevance_score: float = 0.0
    pagerank_score: float = 0.0
    cited_by_count: int = 0
    cites_count: int = 0
    lanes: List[str] = field(default_factory=list)
    binding: bool = False

    def to_dict(self) -> dict:
        return {
            "node_id": self.node_id,
            "citation": self.citation,
            "authority_type": self.authority_type,
            "jurisdiction": self.jurisdiction,
            "year": self.year,
            "court": self.court,
            "relevance_score": round(self.relevance_score, 4),
            "pagerank_score": round(self.pagerank_score, 6),
            "cited_by_count": self.cited_by_count,
            "cites_count": self.cites_count,
            "lanes": list(self.lanes),
            "binding": self.binding,
        }


@dataclass
class AuthorityEdge:
    """A directed edge between two authorities."""

    source_id: str
    target_id: str
    relationship: str = "cites"  # cites, distinguishes, overrules, follows, extends
    weight: float = 1.0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class AuthorityCluster:
    """A group of related authorities."""

    cluster_id: str
    theme: str
    authorities: List[str] = field(default_factory=list)
    density: float = 0.0
    lanes: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "cluster_id": self.cluster_id,
            "theme": self.theme,
            "authorities": list(self.authorities),
            "density": round(self.density, 4),
            "lanes": list(self.lanes),
        }


@dataclass
class GraphReport:
    """Full enrichment report."""

    generated_at: str = ""
    total_nodes: int = 0
    total_edges: int = 0
    clusters: List[AuthorityCluster] = field(default_factory=list)
    top_authorities: List[AuthorityNode] = field(default_factory=list)
    gap_areas: List[Dict[str, Any]] = field(default_factory=list)
    orphan_authorities: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "generated_at": self.generated_at,
            "total_nodes": self.total_nodes,
            "total_edges": self.total_edges,
            "clusters": [c.to_dict() for c in self.clusters],
            "top_authorities": [a.to_dict() for a in self.top_authorities],
            "gap_areas": list(self.gap_areas),
            "orphan_authorities": list(self.orphan_authorities),
            "recommendations": list(self.recommendations),
        }


# ---------------------------------------------------------------------------
# Seed authorities — embedded domain knowledge for Pigors v. Watson
# ---------------------------------------------------------------------------

_SEED_AUTHORITIES: List[Dict[str, Any]] = [
    # SCOTUS — binding everywhere
    {
        "citation": "Troxel v. Granville, 530 U.S. 57 (2000)",
        "authority_type": "case", "jurisdiction": "SCOTUS", "year": 2000,
        "court": "U.S. Supreme Court", "binding": True,
        "lanes": ["A", "D"], "relevance_score": 0.85,
        "theme": "parental_rights",
    },
    {
        "citation": "Mathews v. Eldridge, 424 U.S. 319 (1976)",
        "authority_type": "case", "jurisdiction": "SCOTUS", "year": 1976,
        "court": "U.S. Supreme Court", "binding": True,
        "lanes": ["A", "D", "E"], "relevance_score": 0.90,
        "theme": "due_process",
    },
    {
        "citation": "Monell v. Dept. Social Services, 436 U.S. 658 (1978)",
        "authority_type": "case", "jurisdiction": "SCOTUS", "year": 1978,
        "court": "U.S. Supreme Court", "binding": True,
        "lanes": ["E", "C"], "relevance_score": 0.70,
        "theme": "municipal_liability",
    },
    {
        "citation": "Santosky v. Kramer, 455 U.S. 745 (1982)",
        "authority_type": "case", "jurisdiction": "SCOTUS", "year": 1982,
        "court": "U.S. Supreme Court", "binding": True,
        "lanes": ["A"], "relevance_score": 0.80,
        "theme": "parental_rights",
    },
    # Michigan Supreme Court / Court of Appeals — binding in MI
    {
        "citation": "Vodvarka v. Grasmeyer, 259 Mich App 499 (2003)",
        "authority_type": "case", "jurisdiction": "MI", "year": 2003,
        "court": "Michigan Court of Appeals", "binding": True,
        "lanes": ["A"], "relevance_score": 0.95,
        "theme": "custody_modification",
    },
    {
        "citation": "Shade v. Wright, 291 Mich App 17 (2010)",
        "authority_type": "case", "jurisdiction": "MI", "year": 2010,
        "court": "Michigan Court of Appeals", "binding": True,
        "lanes": ["A"], "relevance_score": 0.90,
        "theme": "custody_modification",
    },
    {
        "citation": "Harvey v. Harvey, 470 Mich 186 (2004)",
        "authority_type": "case", "jurisdiction": "MI", "year": 2004,
        "court": "Michigan Supreme Court", "binding": True,
        "lanes": ["A"], "relevance_score": 0.92,
        "theme": "best_interest",
    },
    {
        "citation": "Pickering v. Pickering, 253 Mich App 694 (2002)",
        "authority_type": "case", "jurisdiction": "MI", "year": 2002,
        "court": "Michigan Court of Appeals", "binding": True,
        "lanes": ["A"], "relevance_score": 0.80,
        "theme": "parental_alienation",
    },
    # MCR — Michigan Court Rules
    {
        "citation": "MCR 2.003",
        "authority_type": "rule", "jurisdiction": "MCR", "year": None,
        "court": "Michigan Courts", "binding": True,
        "lanes": ["E", "A", "F"], "relevance_score": 0.95,
        "theme": "judicial_disqualification",
    },
    {
        "citation": "MCR 2.119",
        "authority_type": "rule", "jurisdiction": "MCR", "year": None,
        "court": "Michigan Courts", "binding": True,
        "lanes": ["A", "B", "D", "F"], "relevance_score": 0.80,
        "theme": "motion_practice",
    },
    {
        "citation": "MCR 7.204",
        "authority_type": "rule", "jurisdiction": "MCR", "year": None,
        "court": "Michigan Courts", "binding": True,
        "lanes": ["F"], "relevance_score": 0.90,
        "theme": "appeals",
    },
    {
        "citation": "MCR 7.205",
        "authority_type": "rule", "jurisdiction": "MCR", "year": None,
        "court": "Michigan Courts", "binding": True,
        "lanes": ["F"], "relevance_score": 0.85,
        "theme": "appeals",
    },
    # MCL — Michigan Compiled Laws
    {
        "citation": "MCL 722.23",
        "authority_type": "statute", "jurisdiction": "MCL", "year": None,
        "court": "Michigan Legislature", "binding": True,
        "lanes": ["A"], "relevance_score": 0.98,
        "theme": "best_interest",
    },
    {
        "citation": "MCL 750.159i",
        "authority_type": "statute", "jurisdiction": "MCL", "year": None,
        "court": "Michigan Legislature", "binding": True,
        "lanes": ["B", "C"], "relevance_score": 0.65,
        "theme": "rico",
    },
    {
        "citation": "MCL 600.2919a",
        "authority_type": "statute", "jurisdiction": "MCL", "year": None,
        "court": "Michigan Legislature", "binding": True,
        "lanes": ["B"], "relevance_score": 0.70,
        "theme": "conversion",
    },
]

# Seed edges — known citation relationships
_SEED_EDGES: List[Dict[str, str]] = [
    # Custody modification chain
    {"source": "Shade v. Wright, 291 Mich App 17 (2010)",
     "target": "Vodvarka v. Grasmeyer, 259 Mich App 499 (2003)",
     "relationship": "follows"},
    {"source": "Vodvarka v. Grasmeyer, 259 Mich App 499 (2003)",
     "target": "MCL 722.23",
     "relationship": "cites"},
    {"source": "Harvey v. Harvey, 470 Mich 186 (2004)",
     "target": "MCL 722.23",
     "relationship": "cites"},
    # Parental rights chain
    {"source": "Troxel v. Granville, 530 U.S. 57 (2000)",
     "target": "Santosky v. Kramer, 455 U.S. 745 (1982)",
     "relationship": "follows"},
    # Due process chain
    {"source": "Santosky v. Kramer, 455 U.S. 745 (1982)",
     "target": "Mathews v. Eldridge, 424 U.S. 319 (1976)",
     "relationship": "cites"},
    # Disqualification ties
    {"source": "MCR 2.003",
     "target": "Mathews v. Eldridge, 424 U.S. 319 (1976)",
     "relationship": "cites"},
    # Appeals chain
    {"source": "MCR 7.205",
     "target": "MCR 7.204",
     "relationship": "extends"},
    # Motion practice
    {"source": "MCR 2.119",
     "target": "MCR 2.003",
     "relationship": "cites"},
    # Pickering → parental alienation in custody context
    {"source": "Pickering v. Pickering, 253 Mich App 694 (2002)",
     "target": "MCL 722.23",
     "relationship": "cites"},
    # RICO / housing
    {"source": "MCL 600.2919a",
     "target": "MCL 750.159i",
     "relationship": "cites"},
]

# Theme labels for cluster detection
_THEME_LABELS: Dict[str, str] = {
    "custody_modification": "Custody Modification Standards",
    "best_interest": "Best Interest of the Child",
    "parental_rights": "Fundamental Parental Rights",
    "parental_alienation": "Parental Alienation Doctrine",
    "due_process": "Due Process Protections",
    "judicial_disqualification": "Judicial Disqualification",
    "municipal_liability": "Municipal / Official Liability",
    "motion_practice": "Motion Practice & Procedure",
    "appeals": "Appellate Procedure",
    "rico": "RICO & Criminal Enterprise",
    "conversion": "Property Conversion / Treble Damages",
}

# Expected legal topics per lane for gap analysis
_LANE_EXPECTED_THEMES: Dict[str, List[str]] = {
    "A": [
        "custody_modification", "best_interest", "parental_rights",
        "parental_alienation", "due_process",
    ],
    "B": ["conversion", "rico", "due_process"],
    "C": ["municipal_liability", "due_process", "rico"],
    "D": ["parental_rights", "due_process"],
    "E": ["judicial_disqualification", "due_process", "municipal_liability"],
    "F": ["appeals", "motion_practice"],
}


# ---------------------------------------------------------------------------
# Helper — deterministic node ID from citation text
# ---------------------------------------------------------------------------

def _make_node_id(citation: str) -> str:
    """Generate a deterministic node ID from citation text."""
    normalized = re.sub(r"\s+", " ", citation.strip().lower())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------


class KnowledgeGraphEnricher:
    """Enrich the legal authority knowledge graph."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self._db_path = Path(db_path) if db_path else _DB_PATH
        self._nodes: Dict[str, AuthorityNode] = {}
        self._edges: Dict[Tuple[str, str], AuthorityEdge] = {}
        self._citation_to_id: Dict[str, str] = {}
        self._adjacency: Dict[str, Set[str]] = defaultdict(set)  # outgoing
        self._reverse_adj: Dict[str, Set[str]] = defaultdict(set)  # incoming
        self._clusters: List[AuthorityCluster] = []
        self._last_report: Optional[GraphReport] = None
        logger.info("KnowledgeGraphEnricher initialized (db=%s)", self._db_path)

    # ------------------------------------------------------------------
    # DB helpers
    # ------------------------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        """Open a connection with standard PRAGMAs."""
        conn = sqlite3.connect(str(self._db_path), timeout=30)
        conn.execute("PRAGMA busy_timeout = 60000")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA cache_size = -32000")
        conn.execute("PRAGMA temp_store = MEMORY")
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_tables(self, conn: sqlite3.Connection) -> None:
        """Create graph tables if they do not exist."""
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS authority_graph_nodes (
                node_id     TEXT PRIMARY KEY,
                citation    TEXT,
                authority_type TEXT,
                jurisdiction TEXT,
                year        INTEGER,
                court       TEXT,
                pagerank    REAL DEFAULT 0,
                relevance   REAL DEFAULT 0,
                cited_by_count INTEGER DEFAULT 0,
                cites_count INTEGER DEFAULT 0,
                lanes       TEXT DEFAULT '[]',
                binding     INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS authority_graph_edges (
                source_id    TEXT,
                target_id    TEXT,
                relationship TEXT DEFAULT 'cites',
                weight       REAL DEFAULT 1.0,
                PRIMARY KEY (source_id, target_id)
            );
        """)

    # ------------------------------------------------------------------
    # Graph mutation
    # ------------------------------------------------------------------

    def add_authority(self, node: AuthorityNode) -> None:
        """Add or update an authority node."""
        self._nodes[node.node_id] = node
        self._citation_to_id[node.citation.lower().strip()] = node.node_id

    def add_edge(self, edge: AuthorityEdge) -> None:
        """Add or update a directed edge."""
        key = (edge.source_id, edge.target_id)
        self._edges[key] = edge
        self._adjacency[edge.source_id].add(edge.target_id)
        self._reverse_adj[edge.target_id].add(edge.source_id)

    def _resolve_citation(self, citation: str) -> Optional[str]:
        """Resolve a citation string to a node_id."""
        return self._citation_to_id.get(citation.lower().strip())

    # ------------------------------------------------------------------
    # Load from DB
    # ------------------------------------------------------------------

    def load_from_db(self) -> int:
        """Load existing authorities from DB tables. Returns count loaded."""
        if not self._db_path.exists():
            logger.warning("DB not found at %s — starting with empty graph", self._db_path)
            return 0

        loaded = 0
        try:
            conn = self._connect()
            self._ensure_tables(conn)

            # Check which tables have data
            tables = {
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            }

            # Load from authority_graph_nodes
            if "authority_graph_nodes" in tables:
                rows = conn.execute(
                    "SELECT node_id, citation, authority_type, jurisdiction, "
                    "year, court, pagerank, relevance, cited_by_count, "
                    "cites_count, lanes, binding "
                    "FROM authority_graph_nodes"
                ).fetchall()
                for r in rows:
                    lanes_raw = r["lanes"] or "[]"
                    try:
                        lanes = json.loads(lanes_raw)
                    except (json.JSONDecodeError, TypeError):
                        lanes = []
                    node = AuthorityNode(
                        node_id=r["node_id"],
                        citation=r["citation"] or "",
                        authority_type=r["authority_type"] or "case",
                        jurisdiction=r["jurisdiction"] or "",
                        year=r["year"],
                        court=r["court"],
                        relevance_score=r["relevance"] or 0.0,
                        pagerank_score=r["pagerank"] or 0.0,
                        cited_by_count=r["cited_by_count"] or 0,
                        cites_count=r["cites_count"] or 0,
                        lanes=lanes,
                        binding=bool(r["binding"]),
                    )
                    self.add_authority(node)
                    loaded += 1

            # Load from authority_graph_edges
            if "authority_graph_edges" in tables:
                rows = conn.execute(
                    "SELECT source_id, target_id, relationship, weight "
                    "FROM authority_graph_edges"
                ).fetchall()
                for r in rows:
                    edge = AuthorityEdge(
                        source_id=r["source_id"],
                        target_id=r["target_id"],
                        relationship=r["relationship"] or "cites",
                        weight=r["weight"] or 1.0,
                    )
                    self.add_edge(edge)

            # Also pull from existing authority_chains / master_citations
            if "authority_chains" in tables:
                try:
                    cols = {
                        row[1]
                        for row in conn.execute(
                            "PRAGMA table_info(authority_chains)"
                        ).fetchall()
                    }
                    citation_col = "citation" if "citation" in cols else None
                    type_col = "authority_type" if "authority_type" in cols else None
                    if citation_col:
                        query = f"SELECT DISTINCT {citation_col}"
                        if type_col:
                            query += f", {type_col}"
                        query += " FROM authority_chains LIMIT 5000"
                        for r in conn.execute(query).fetchall():
                            cit = r[0] or ""
                            if not cit:
                                continue
                            nid = _make_node_id(cit)
                            if nid not in self._nodes:
                                atype = r[1] if type_col and len(r) > 1 else "case"
                                node = AuthorityNode(
                                    node_id=nid,
                                    citation=cit,
                                    authority_type=atype or "case",
                                    jurisdiction=self._infer_jurisdiction(cit),
                                )
                                self.add_authority(node)
                                loaded += 1
                except sqlite3.Error as exc:
                    logger.warning("Could not read authority_chains: %s", exc)

            conn.close()
        except sqlite3.Error as exc:
            logger.error("DB load failed: %s", exc)

        logger.info("Loaded %d authorities from DB", loaded)
        return loaded

    # ------------------------------------------------------------------
    # Save to DB
    # ------------------------------------------------------------------

    def save_to_db(self) -> int:
        """Persist current graph to DB. Returns count saved."""
        saved = 0
        try:
            conn = self._connect()
            self._ensure_tables(conn)

            node_rows = [
                (
                    n.node_id, n.citation, n.authority_type, n.jurisdiction,
                    n.year, n.court, n.pagerank_score, n.relevance_score,
                    n.cited_by_count, n.cites_count, json.dumps(n.lanes),
                    int(n.binding),
                )
                for n in self._nodes.values()
            ]
            conn.executemany(
                "INSERT OR REPLACE INTO authority_graph_nodes "
                "(node_id, citation, authority_type, jurisdiction, year, court, "
                "pagerank, relevance, cited_by_count, cites_count, lanes, binding) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                node_rows,
            )

            edge_rows = [
                (e.source_id, e.target_id, e.relationship, e.weight)
                for e in self._edges.values()
            ]
            conn.executemany(
                "INSERT OR REPLACE INTO authority_graph_edges "
                "(source_id, target_id, relationship, weight) "
                "VALUES (?, ?, ?, ?)",
                edge_rows,
            )

            conn.commit()
            saved = len(node_rows) + len(edge_rows)
            conn.close()
            logger.info("Saved %d nodes + %d edges to DB", len(node_rows), len(edge_rows))
        except sqlite3.Error as exc:
            logger.error("DB save failed: %s", exc)

        return saved

    # ------------------------------------------------------------------
    # Seed from embedded knowledge
    # ------------------------------------------------------------------

    def enrich_from_seeds(self) -> int:
        """Add seed authorities from embedded domain knowledge. Returns count added."""
        added = 0

        for seed in _SEED_AUTHORITIES:
            nid = _make_node_id(seed["citation"])
            if nid in self._nodes:
                # Merge lanes if node already exists
                existing = self._nodes[nid]
                for lane in seed.get("lanes", []):
                    if lane not in existing.lanes:
                        existing.lanes.append(lane)
                continue

            node = AuthorityNode(
                node_id=nid,
                citation=seed["citation"],
                authority_type=seed["authority_type"],
                jurisdiction=seed["jurisdiction"],
                year=seed.get("year"),
                court=seed.get("court"),
                relevance_score=seed.get("relevance_score", 0.5),
                lanes=list(seed.get("lanes", [])),
                binding=seed.get("binding", False),
            )
            self.add_authority(node)
            added += 1

        for se in _SEED_EDGES:
            src_id = self._resolve_citation(se["source"])
            tgt_id = self._resolve_citation(se["target"])
            if src_id and tgt_id:
                edge = AuthorityEdge(
                    source_id=src_id,
                    target_id=tgt_id,
                    relationship=se.get("relationship", "cites"),
                    weight=1.0,
                )
                self.add_edge(edge)

        # Update citation counts
        self._update_citation_counts()

        logger.info("Seeded %d new authorities, %d total edges", added, len(self._edges))
        return added

    # ------------------------------------------------------------------
    # Citation count maintenance
    # ------------------------------------------------------------------

    def _update_citation_counts(self) -> None:
        """Recompute cited_by_count and cites_count for all nodes."""
        for node in self._nodes.values():
            node.cited_by_count = len(self._reverse_adj.get(node.node_id, set()))
            node.cites_count = len(self._adjacency.get(node.node_id, set()))

    # ------------------------------------------------------------------
    # PageRank
    # ------------------------------------------------------------------

    def compute_pagerank(
        self,
        iterations: int = 100,
        damping: float = 0.85,
        tolerance: float = 0.0001,
    ) -> Dict[str, float]:
        """Compute simplified PageRank over the authority graph.

        Returns mapping of node_id → pagerank score.
        """
        t0 = time.perf_counter()
        node_ids = list(self._nodes.keys())
        n = len(node_ids)
        if n == 0:
            return {}

        # Initialize scores uniformly
        scores: Dict[str, float] = {nid: 1.0 / n for nid in node_ids}
        base = (1.0 - damping) / n

        for iteration in range(iterations):
            new_scores: Dict[str, float] = {}
            max_delta = 0.0

            for nid in node_ids:
                # Sum contributions from all nodes that link TO this node
                incoming = self._reverse_adj.get(nid, set())
                rank_sum = 0.0
                for src in incoming:
                    out_count = len(self._adjacency.get(src, set()))
                    if out_count > 0:
                        rank_sum += scores.get(src, 0.0) / out_count

                new_score = base + damping * rank_sum
                new_scores[nid] = new_score
                max_delta = max(max_delta, abs(new_score - scores[nid]))

            scores = new_scores

            if max_delta < tolerance:
                logger.info(
                    "PageRank converged after %d iterations (delta=%.6f)",
                    iteration + 1, max_delta,
                )
                break

        # Normalize to 0–1 range
        max_score = max(scores.values()) if scores else 1.0
        if max_score > 0:
            scores = {nid: s / max_score for nid, s in scores.items()}

        # Apply to nodes
        for nid, score in scores.items():
            if nid in self._nodes:
                self._nodes[nid].pagerank_score = score

        elapsed = (time.perf_counter() - t0) * 1000
        logger.info(
            "PageRank computed for %d nodes in %.1fms", n, elapsed,
        )
        return scores

    # ------------------------------------------------------------------
    # Cluster detection (connected components via BFS)
    # ------------------------------------------------------------------

    def detect_clusters(self) -> List[AuthorityCluster]:
        """Detect clusters using connected-component BFS on undirected view."""
        t0 = time.perf_counter()

        # Build undirected adjacency
        undirected: Dict[str, Set[str]] = defaultdict(set)
        for (src, tgt) in self._edges:
            undirected[src].add(tgt)
            undirected[tgt].add(src)

        visited: Set[str] = set()
        components: List[List[str]] = []

        for nid in self._nodes:
            if nid in visited:
                continue
            # BFS
            component: List[str] = []
            queue: deque[str] = deque([nid])
            while queue:
                current = queue.popleft()
                if current in visited:
                    continue
                visited.add(current)
                component.append(current)
                for neighbor in undirected.get(current, set()):
                    if neighbor not in visited:
                        queue.append(neighbor)
            components.append(component)

        # Build cluster objects
        self._clusters = []
        for idx, comp in enumerate(components):
            if len(comp) < 1:
                continue

            # Calculate density
            num_nodes = len(comp)
            comp_set = set(comp)
            num_edges = sum(
                1 for (s, t) in self._edges
                if s in comp_set and t in comp_set
            )
            max_edges = num_nodes * (num_nodes - 1) / 2 if num_nodes > 1 else 1
            density = num_edges / max_edges if max_edges > 0 else 0.0

            # Determine theme from dominant node themes
            theme = self._infer_cluster_theme(comp)

            # Collect lanes
            all_lanes: Set[str] = set()
            for nid in comp:
                if nid in self._nodes:
                    all_lanes.update(self._nodes[nid].lanes)

            cluster = AuthorityCluster(
                cluster_id=f"cluster_{idx:03d}",
                theme=theme,
                authorities=comp,
                density=density,
                lanes=sorted(all_lanes),
            )
            self._clusters.append(cluster)

        # Sort by size descending
        self._clusters.sort(key=lambda c: len(c.authorities), reverse=True)

        elapsed = (time.perf_counter() - t0) * 1000
        logger.info(
            "Detected %d clusters in %.1fms", len(self._clusters), elapsed,
        )
        return self._clusters

    def _infer_cluster_theme(self, component: List[str]) -> str:
        """Infer a theme label for a cluster from seed metadata."""
        # Count theme mentions across seed authorities in this component
        theme_counts: Dict[str, int] = defaultdict(int)
        for nid in component:
            node = self._nodes.get(nid)
            if not node:
                continue
            # Match citation to seed for theme
            for seed in _SEED_AUTHORITIES:
                if _make_node_id(seed["citation"]) == nid:
                    theme_counts[seed.get("theme", "general")] += 1
                    break
            else:
                # Infer from authority_type
                if node.authority_type == "rule":
                    theme_counts["procedural"] += 1
                elif node.authority_type == "statute":
                    theme_counts["statutory"] += 1
                else:
                    theme_counts["case_law"] += 1

        if not theme_counts:
            return "general"

        top_theme = max(theme_counts, key=theme_counts.get)  # type: ignore[arg-type]
        return _THEME_LABELS.get(top_theme, top_theme)

    # ------------------------------------------------------------------
    # Gap analysis
    # ------------------------------------------------------------------

    def find_gaps(self, lane: Optional[str] = None) -> List[Dict[str, Any]]:
        """Identify areas needing more authority support."""
        gaps: List[Dict[str, Any]] = []
        lanes_to_check = [lane] if lane else list(_LANE_EXPECTED_THEMES.keys())

        for ln in lanes_to_check:
            expected = _LANE_EXPECTED_THEMES.get(ln, [])
            # Collect themes present in this lane
            present_themes: Set[str] = set()
            for node in self._nodes.values():
                if ln in node.lanes:
                    for seed in _SEED_AUTHORITIES:
                        if _make_node_id(seed["citation"]) == node.node_id:
                            present_themes.add(seed.get("theme", ""))
                            break

            for theme in expected:
                if theme not in present_themes:
                    gaps.append({
                        "lane": ln,
                        "missing_theme": theme,
                        "label": _THEME_LABELS.get(theme, theme),
                        "severity": "high" if theme in ("due_process", "best_interest") else "medium",
                        "recommendation": f"Add authority for '{_THEME_LABELS.get(theme, theme)}' in Lane {ln}",
                    })

            # Check if lane has < 3 authorities
            lane_count = sum(1 for n in self._nodes.values() if ln in n.lanes)
            if lane_count < 3:
                gaps.append({
                    "lane": ln,
                    "missing_theme": "coverage",
                    "label": "Insufficient authority coverage",
                    "severity": "high",
                    "recommendation": f"Lane {ln} has only {lane_count} authorities — need at least 3",
                })

        return gaps

    # ------------------------------------------------------------------
    # Orphan detection
    # ------------------------------------------------------------------

    def find_orphans(self) -> List[str]:
        """Find authorities not connected to any other node."""
        connected: Set[str] = set()
        for src, tgt in self._edges:
            connected.add(src)
            connected.add(tgt)

        orphans = [
            nid for nid in self._nodes
            if nid not in connected
        ]
        return orphans

    # ------------------------------------------------------------------
    # Authority chain for filings
    # ------------------------------------------------------------------

    def get_authority_chain(
        self,
        filing_type: str,
        lane: Optional[str] = None,
    ) -> List[AuthorityNode]:
        """Get best authorities for a filing type and lane, ranked by PageRank."""
        # Map filing types to relevant themes
        filing_themes: Dict[str, List[str]] = {
            "motion": ["motion_practice", "due_process"],
            "brief": ["case_law", "due_process", "best_interest"],
            "complaint": ["due_process", "municipal_liability", "rico"],
            "appeal": ["appeals", "motion_practice"],
            "custody": ["custody_modification", "best_interest", "parental_rights"],
            "disqualification": ["judicial_disqualification", "due_process"],
            "ppo": ["parental_rights", "due_process"],
        }
        target_themes = filing_themes.get(
            filing_type.lower(), ["due_process", "case_law"]
        )

        candidates: List[AuthorityNode] = []
        for node in self._nodes.values():
            # Filter by lane if specified
            if lane and lane not in node.lanes:
                continue

            # Check theme relevance via seeds
            node_theme = ""
            for seed in _SEED_AUTHORITIES:
                if _make_node_id(seed["citation"]) == node.node_id:
                    node_theme = seed.get("theme", "")
                    break

            # Include if theme matches or if it's a high-PageRank binding authority
            if node_theme in target_themes or (node.binding and node.pagerank_score > 0.3):
                candidates.append(node)

        # Sort by PageRank descending, then relevance
        candidates.sort(
            key=lambda n: (n.pagerank_score, n.relevance_score),
            reverse=True,
        )
        return candidates[:20]

    # ------------------------------------------------------------------
    # Jurisdiction inference
    # ------------------------------------------------------------------

    @staticmethod
    def _infer_jurisdiction(citation: str) -> str:
        """Infer jurisdiction from citation text."""
        cit = citation.upper()
        if "MCR" in cit:
            return "MCR"
        if "MCL" in cit:
            return "MCL"
        if "MICH APP" in cit or "MICH. APP" in cit:
            return "MI"
        if "MICH" in cit:
            return "MI"
        if "U.S." in cit or "S. CT." in cit or "S.CT." in cit:
            return "SCOTUS"
        if "F.3D" in cit or "F.2D" in cit or "F. SUPP" in cit:
            return "6th_Circuit"
        if "N.W.2D" in cit or "N.W. 2D" in cit:
            return "MI"
        return "unknown"

    # ------------------------------------------------------------------
    # Report generation
    # ------------------------------------------------------------------

    def generate_report(self) -> GraphReport:
        """Generate a full enrichment report."""
        t0 = time.perf_counter()

        # Ensure data is up-to-date
        self._update_citation_counts()

        # If PageRank hasn't been run, compute it
        if all(n.pagerank_score == 0.0 for n in self._nodes.values()):
            self.compute_pagerank()

        # Detect clusters if not already done
        if not self._clusters:
            self.detect_clusters()

        # Top authorities by PageRank
        top_auth = sorted(
            self._nodes.values(),
            key=lambda n: n.pagerank_score,
            reverse=True,
        )[:15]

        # Gaps and orphans
        gaps = self.find_gaps()
        orphans = self.find_orphans()

        # Build recommendations
        recommendations = self._build_recommendations(gaps, orphans)

        report = GraphReport(
            generated_at=datetime.now(timezone.utc).isoformat(),
            total_nodes=len(self._nodes),
            total_edges=len(self._edges),
            clusters=list(self._clusters),
            top_authorities=list(top_auth),
            gap_areas=gaps,
            orphan_authorities=orphans,
            recommendations=recommendations,
        )
        self._last_report = report

        elapsed = (time.perf_counter() - t0) * 1000
        logger.info("Report generated in %.1fms", elapsed)
        return report

    def _build_recommendations(
        self,
        gaps: List[Dict[str, Any]],
        orphans: List[str],
    ) -> List[str]:
        """Build actionable recommendations."""
        recs: List[str] = []

        if not self._nodes:
            recs.append("Graph is empty — run enrich_from_seeds() to populate base authorities.")
            return recs

        # Gap-based recommendations
        high_gaps = [g for g in gaps if g.get("severity") == "high"]
        if high_gaps:
            lanes_affected = sorted({g["lane"] for g in high_gaps})
            recs.append(
                f"HIGH PRIORITY: {len(high_gaps)} critical gaps in lanes "
                f"{', '.join(lanes_affected)} — add authority coverage."
            )

        for gap in gaps[:5]:
            recs.append(gap.get("recommendation", ""))

        # Orphan-based
        if orphans:
            recs.append(
                f"{len(orphans)} orphan authorities not connected to the graph — "
                f"add citation edges to integrate them."
            )

        # Cluster-based
        singleton_clusters = [c for c in self._clusters if len(c.authorities) == 1]
        if singleton_clusters:
            recs.append(
                f"{len(singleton_clusters)} isolated authorities "
                f"form singleton clusters — connect them to related authorities."
            )

        # Binding authority coverage
        binding_count = sum(1 for n in self._nodes.values() if n.binding)
        if binding_count < 5:
            recs.append(
                f"Only {binding_count} binding authorities — "
                f"consider adding more Michigan/SCOTUS binding case law."
            )

        # PageRank concentration
        if self._nodes:
            top_pr = max(n.pagerank_score for n in self._nodes.values())
            if top_pr > 0.5:
                recs.append(
                    "Authority graph is highly concentrated — "
                    "diversify citations to reduce single-point dependency."
                )

        return [r for r in recs if r]

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def export_graph(self, output_path: Optional[str] = None) -> str:
        """Export full graph as JSON. Returns JSON string."""
        data = {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "nodes": [n.to_dict() for n in self._nodes.values()],
            "edges": [e.to_dict() for e in self._edges.values()],
            "clusters": [c.to_dict() for c in self._clusters],
        }
        json_str = json.dumps(data, indent=2)

        if output_path:
            out = Path(output_path)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json_str, encoding="utf-8")
            logger.info("Graph exported to %s", out)

        return json_str

    def export_mermaid(self) -> str:
        """Generate a Mermaid diagram of top authorities."""
        lines: List[str] = ["graph TD"]

        # Select top 20 nodes by PageRank
        top_nodes = sorted(
            self._nodes.values(),
            key=lambda n: n.pagerank_score,
            reverse=True,
        )[:20]
        top_ids = {n.node_id for n in top_nodes}

        # Sanitize label for Mermaid
        def _label(node: AuthorityNode) -> str:
            short = node.citation
            if len(short) > 50:
                short = short[:47] + "..."
            # Escape special Mermaid chars
            safe = short.replace('"', "'").replace("(", "[").replace(")", "]")
            return safe

        # Shape by authority type
        type_shapes = {
            "case": ('["', '"]'),        # rectangle
            "statute": ('(["', '"])'),    # stadium
            "rule": ('(["', '"])'),       # stadium
            "regulation": ('{"', '"}'),   # rhombus
            "constitution": ('(("', '"))'),  # circle
        }

        for node in top_nodes:
            shape = type_shapes.get(node.authority_type, ('["', '"]'))
            label = _label(node)
            pr = f" PR:{node.pagerank_score:.2f}" if node.pagerank_score > 0 else ""
            lines.append(f"    {node.node_id}{shape[0]}{label}{pr}{shape[1]}")

        # Add edges between top nodes
        rel_arrows = {
            "cites": "-->",
            "follows": "-.->",
            "extends": "==>",
            "distinguishes": "--x",
            "overrules": "--x",
        }
        for (src, tgt), edge in self._edges.items():
            if src in top_ids and tgt in top_ids:
                arrow = rel_arrows.get(edge.relationship, "-->")
                label = edge.relationship
                lines.append(f"    {src} {arrow}|{label}| {tgt}")

        # Style classes
        lines.append("")
        lines.append("    classDef scotus fill:#e74c3c,stroke:#c0392b,color:#fff")
        lines.append("    classDef michigan fill:#3498db,stroke:#2980b9,color:#fff")
        lines.append("    classDef statute fill:#2ecc71,stroke:#27ae60,color:#fff")
        lines.append("    classDef rule fill:#f39c12,stroke:#e67e22,color:#fff")

        for node in top_nodes:
            if node.jurisdiction == "SCOTUS":
                lines.append(f"    class {node.node_id} scotus")
            elif node.jurisdiction in ("MI",):
                lines.append(f"    class {node.node_id} michigan")
            elif node.jurisdiction in ("MCL",):
                lines.append(f"    class {node.node_id} statute")
            elif node.jurisdiction in ("MCR",):
                lines.append(f"    class {node.node_id} rule")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        """Return engine status."""
        binding_count = sum(1 for n in self._nodes.values() if n.binding)
        type_dist: Dict[str, int] = defaultdict(int)
        for n in self._nodes.values():
            type_dist[n.authority_type] += 1
        jurisdiction_dist: Dict[str, int] = defaultdict(int)
        for n in self._nodes.values():
            jurisdiction_dist[n.jurisdiction] += 1

        return {
            "version": "1.0.0",
            "db_path": str(self._db_path),
            "db_exists": self._db_path.exists(),
            "total_nodes": len(self._nodes),
            "total_edges": len(self._edges),
            "total_clusters": len(self._clusters),
            "binding_authorities": binding_count,
            "authority_types": dict(type_dist),
            "jurisdictions": dict(jurisdiction_dist),
            "seed_authorities": len(_SEED_AUTHORITIES),
            "seed_edges": len(_SEED_EDGES),
            "pagerank_computed": any(
                n.pagerank_score > 0 for n in self._nodes.values()
            ),
        }
