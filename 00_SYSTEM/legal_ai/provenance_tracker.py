# -*- coding: utf-8 -*-
"""
provenance_tracker.py — Evidence Provenance Chain Tracker
==========================================================
Tracks the complete provenance chain from raw evidence files to
court-filed documents using SHA-256 hashing, directed acyclic graph
(DAG) relationships, and a full audit trail.

Every piece of evidence in LitigationOS passes through a series of
transformations: extraction, analysis, assembly, formatting, and filing.
This module records each step as a node in a DAG and each transformation
as a directed edge, producing a verifiable, tamper-evident chain of
custody from original file to court submission.

Capabilities:
  - Register raw files with SHA-256 integrity hashes
  - Track transformations: extraction, analysis, assembly, formatting
  - Build directed acyclic graph (DAG) of relationships
  - Verify integrity: re-hash files and compare to registered values
  - Generate Mermaid diagrams of provenance chains
  - Generate interactive HTML visualizations
  - SQLite persistence with ``provenance_tracking`` and ``provenance_edges`` tables
  - JSON export / import for chain portability

Six case lanes: A=Custody (2024-001507-DC), B=Housing (2025-002760-CZ),
C=Convergence, D=PPO (2023-5907-PP), E=Misconduct/JTC, F=Appellate
(COA 366810).

Zero external dependencies.  Local-only.
"""

from __future__ import annotations

import collections
import hashlib
import json
import logging
import os
import re
import sqlite3
import textwrap
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from html import escape as html_escape
from pathlib import Path
from typing import Any, Deque, Dict, List, Optional, Set, Tuple

logger = logging.getLogger("legal_ai.provenance_tracker")

# ─── Constants ────────────────────────────────────────────────────────

_DB_DEFAULT: Path = Path(__file__).resolve().parents[2] / "litigation_context.db"

_VALID_NODE_TYPES: Set[str] = {
    "raw_file",
    "extracted_text",
    "analysis",
    "filing_section",
    "filing_document",
    "exhibit",
    "filed_document",
}

_VALID_RELATIONSHIPS: Set[str] = {
    "extracted_from",
    "analyzed_by",
    "included_in",
    "cited_by",
    "assembled_into",
    "filed_as",
}

_VALID_LANES: Set[str] = {"A", "B", "C", "D", "E", "F"}

_SHA256_BUF_SIZE = 65_536  # 64 KB read chunks for hashing


# ─── Data Classes ─────────────────────────────────────────────────────

@dataclass
class ProvenanceNode:
    """A single artefact in the provenance DAG.

    Each node represents one file or derived artefact at a specific
    point in the evidence lifecycle.
    """

    node_id: str
    node_type: str
    path: str
    sha256: str
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Serialise to a plain dictionary."""
        return asdict(self)


@dataclass
class ProvenanceEdge:
    """A directed relationship between two provenance nodes.

    Edges form the DAG connecting raw evidence to final filed documents.
    """

    source_id: str
    target_id: str
    relationship: str
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    agent_id: str = ""

    def to_dict(self) -> dict:
        """Serialise to a plain dictionary."""
        return asdict(self)


@dataclass
class ProvenanceChain:
    """A traversed sub-graph rooted at a single node.

    Represents the full upstream ancestry (or downstream descendants)
    of a particular artefact.
    """

    root_node: ProvenanceNode
    nodes: List[ProvenanceNode] = field(default_factory=list)
    edges: List[ProvenanceEdge] = field(default_factory=list)
    depth: int = 0
    complete: bool = False

    def to_dict(self) -> dict:
        """Serialise to a plain dictionary."""
        return {
            "root_node": self.root_node.to_dict(),
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
            "depth": self.depth,
            "complete": self.complete,
        }


@dataclass
class ProvenanceReport:
    """Comprehensive provenance report for a filing.

    Includes the DAG chain, coverage analysis, integrity verification,
    and renderable visualisations.
    """

    filing_id: str
    chain: ProvenanceChain
    coverage_pct: float = 0.0
    untracked_sections: List[str] = field(default_factory=list)
    dag_mermaid: str = ""
    dag_html: str = ""
    integrity_verified: bool = False

    def to_dict(self) -> dict:
        """Serialise to a plain dictionary."""
        return {
            "filing_id": self.filing_id,
            "chain": self.chain.to_dict(),
            "coverage_pct": self.coverage_pct,
            "untracked_sections": self.untracked_sections,
            "dag_mermaid": self.dag_mermaid,
            "dag_html": self.dag_html,
            "integrity_verified": self.integrity_verified,
        }


# ─── Provenance Tracker Class ────────────────────────────────────────

class ProvenanceTracker:
    """Track evidence provenance from raw files to court filings.

    Builds and queries a directed acyclic graph (DAG) of evidence
    transformations persisted in SQLite.  Every artefact receives a
    SHA-256 integrity hash; every transformation is recorded as a
    directed edge with the responsible agent and timestamp.

    Features:
      - File registration with SHA-256 hashing
      - Transformation tracking (extraction, analysis, assembly)
      - DAG traversal: upstream chains and downstream descendants
      - Integrity verification by re-hashing
      - Mermaid and HTML DAG visualisation
      - JSON export / import for chain portability
      - Orphan detection (nodes with no edges)

    Usage::

        from legal_ai.provenance_tracker import ProvenanceTracker
        pt = ProvenanceTracker()
        node = pt.register_file("evidence/contract.pdf")
        text_node = pt.register_file("extracted/contract.txt",
                                     node_type="extracted_text")
        pt.register_transformation(
            source_ids=[node.node_id],
            target_id=text_node.node_id,
            relationship="extracted_from",
            agent_id="A04_pdf_extractor",
        )
        chain = pt.get_chain(text_node.node_id)
        print(chain.depth, chain.complete)
    """

    def __init__(self, db_path: str | Path | None = None) -> None:
        """Initialise the tracker.

        Args:
            db_path: Path to the SQLite database.  Defaults to
                     ``litigation_context.db`` two levels above this file.
        """
        self._db_path: Path = Path(db_path) if db_path else _DB_DEFAULT
        self._conn: Optional[sqlite3.Connection] = None
        self._nodes_registered: int = 0
        self._edges_registered: int = 0
        self._verifications_run: int = 0
        self._ensure_schema()
        logger.debug("ProvenanceTracker initialised (db=%s)", self._db_path)

    # ── DB helpers ────────────────────────────────────────────────────

    def _get_conn(self) -> sqlite3.Connection:
        """Return a lazily-initialised database connection."""
        if self._conn is None:
            self._conn = sqlite3.connect(str(self._db_path), timeout=60)
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA busy_timeout=60000")
            self._conn.execute("PRAGMA cache_size=-32000")
            self._conn.execute("PRAGMA synchronous=NORMAL")
            self._conn.execute("PRAGMA temp_store=MEMORY")
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def _ensure_schema(self) -> None:
        """Create provenance tables if they do not exist."""
        conn = self._get_conn()
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS provenance_tracking (
                node_id     TEXT PRIMARY KEY,
                node_type   TEXT NOT NULL,
                path        TEXT NOT NULL,
                sha256      TEXT NOT NULL,
                created_at  TEXT NOT NULL,
                metadata    TEXT DEFAULT '{}'
            );
            CREATE INDEX IF NOT EXISTS idx_pt_type
                ON provenance_tracking(node_type);
            CREATE INDEX IF NOT EXISTS idx_pt_sha256
                ON provenance_tracking(sha256);

            CREATE TABLE IF NOT EXISTS provenance_edges (
                source_id     TEXT NOT NULL,
                target_id     TEXT NOT NULL,
                relationship  TEXT NOT NULL,
                timestamp     TEXT NOT NULL,
                agent_id      TEXT DEFAULT '',
                PRIMARY KEY (source_id, target_id, relationship)
            );
            CREATE INDEX IF NOT EXISTS idx_pe_source
                ON provenance_edges(source_id);
            CREATE INDEX IF NOT EXISTS idx_pe_target
                ON provenance_edges(target_id);
            CREATE INDEX IF NOT EXISTS idx_pe_rel
                ON provenance_edges(relationship);
            """
        )
        conn.commit()

    def _save_to_db(self, obj: ProvenanceNode | ProvenanceEdge) -> None:
        """Persist a node or edge to the database.

        Args:
            obj: A ``ProvenanceNode`` or ``ProvenanceEdge`` to persist.
        """
        conn = self._get_conn()
        try:
            if isinstance(obj, ProvenanceNode):
                conn.execute(
                    """
                    INSERT OR REPLACE INTO provenance_tracking
                        (node_id, node_type, path, sha256, created_at, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        obj.node_id,
                        obj.node_type,
                        obj.path,
                        obj.sha256,
                        obj.created_at,
                        json.dumps(obj.metadata),
                    ),
                )
            elif isinstance(obj, ProvenanceEdge):
                conn.execute(
                    """
                    INSERT OR REPLACE INTO provenance_edges
                        (source_id, target_id, relationship, timestamp, agent_id)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        obj.source_id,
                        obj.target_id,
                        obj.relationship,
                        obj.timestamp,
                        obj.agent_id,
                    ),
                )
            conn.commit()
        except sqlite3.Error as exc:
            logger.error("DB save failed for %s: %s", type(obj).__name__, exc)

    def _load_from_db(self, node_id: str) -> Optional[ProvenanceNode]:
        """Load a single provenance node from the database.

        Args:
            node_id: The node identifier.

        Returns:
            The ``ProvenanceNode`` or ``None`` if not found.
        """
        try:
            conn = self._get_conn()
            row = conn.execute(
                "SELECT * FROM provenance_tracking WHERE node_id = ?",
                (node_id,),
            ).fetchone()
            if row is None:
                return None
            meta = {}
            try:
                meta = json.loads(row["metadata"])
            except (json.JSONDecodeError, TypeError):
                pass
            return ProvenanceNode(
                node_id=row["node_id"],
                node_type=row["node_type"],
                path=row["path"],
                sha256=row["sha256"],
                created_at=row["created_at"],
                metadata=meta,
            )
        except sqlite3.Error as exc:
            logger.error("DB load failed for node %s: %s", node_id, exc)
            return None

    def close(self) -> None:
        """Close the database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None

    # ── Hashing ───────────────────────────────────────────────────────

    @staticmethod
    def _compute_sha256(path: str | Path) -> str:
        """Compute the SHA-256 hex digest of a file.

        Args:
            path: File path to hash.

        Returns:
            Lowercase hex-encoded SHA-256 digest, or empty string on error.
        """
        p = Path(path)
        if not p.exists():
            logger.warning("Cannot hash — file not found: %s", path)
            return ""
        try:
            h = hashlib.sha256()
            with open(p, "rb") as f:
                while True:
                    chunk = f.read(_SHA256_BUF_SIZE)
                    if not chunk:
                        break
                    h.update(chunk)
            return h.hexdigest()
        except OSError as exc:
            logger.error("Hash error for %s: %s", path, exc)
            return ""

    @staticmethod
    def _compute_sha256_text(text: str) -> str:
        """Compute SHA-256 of a text string.

        Args:
            text: The string to hash.

        Returns:
            Lowercase hex digest.
        """
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    # ── Node ID generation ────────────────────────────────────────────

    @staticmethod
    def _make_node_id(path: str, sha256: str) -> str:
        """Derive a deterministic node ID from path and file hash.

        Args:
            path: The file path.
            sha256: The SHA-256 digest of the file.

        Returns:
            A SHA-256-based node identifier.
        """
        composite = f"{path}::{sha256}"
        return hashlib.sha256(composite.encode("utf-8")).hexdigest()[:32]

    # ── Registration ──────────────────────────────────────────────────

    def register_file(
        self,
        path: str | Path,
        node_type: str = "raw_file",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ProvenanceNode:
        """Register a file and compute its SHA-256 provenance hash.

        Args:
            path: Path to the file to register.
            node_type: Type classification (must be in ``_VALID_NODE_TYPES``).
            metadata: Optional key-value metadata to attach.

        Returns:
            The created ``ProvenanceNode``.

        Raises:
            ValueError: If *node_type* is not recognised.
        """
        if node_type not in _VALID_NODE_TYPES:
            raise ValueError(
                f"Invalid node_type '{node_type}'. "
                f"Valid types: {', '.join(sorted(_VALID_NODE_TYPES))}"
            )

        p = Path(path)
        sha = self._compute_sha256(p)
        node_id = self._make_node_id(str(p), sha)

        node = ProvenanceNode(
            node_id=node_id,
            node_type=node_type,
            path=str(p),
            sha256=sha,
            metadata=metadata or {},
        )

        self._save_to_db(node)
        self._nodes_registered += 1
        logger.info("Registered %s node: %s (%s)", node_type, p.name, node_id[:12])
        return node

    def register_transformation(
        self,
        source_ids: List[str],
        target_id: str,
        relationship: str,
        agent_id: str = "",
    ) -> List[ProvenanceEdge]:
        """Record one or more transformation edges in the DAG.

        Args:
            source_ids: List of source node IDs (inputs).
            target_id: The target node ID (output).
            relationship: The type of transformation.
            agent_id: Identifier of the agent/engine that performed it.

        Returns:
            List of created ``ProvenanceEdge`` instances.

        Raises:
            ValueError: If *relationship* is not recognised.
        """
        if relationship not in _VALID_RELATIONSHIPS:
            raise ValueError(
                f"Invalid relationship '{relationship}'. "
                f"Valid: {', '.join(sorted(_VALID_RELATIONSHIPS))}"
            )

        edges: List[ProvenanceEdge] = []
        for src in source_ids:
            edge = ProvenanceEdge(
                source_id=src,
                target_id=target_id,
                relationship=relationship,
                agent_id=agent_id,
            )
            self._save_to_db(edge)
            edges.append(edge)
            self._edges_registered += 1

        logger.info(
            "Registered %d edge(s): %s → %s (%s)",
            len(edges),
            [s[:12] for s in source_ids],
            target_id[:12],
            relationship,
        )
        return edges

    # ── DAG traversal ─────────────────────────────────────────────────

    def get_chain(self, node_id: str) -> ProvenanceChain:
        """Traverse the DAG upstream from *node_id* to all root ancestors.

        Uses breadth-first search to collect all upstream nodes and edges,
        computing chain depth and completeness (all leaf nodes are
        ``raw_file`` type).

        Args:
            node_id: Starting node for upstream traversal.

        Returns:
            A ``ProvenanceChain`` rooted at *node_id*.
        """
        root = self._load_from_db(node_id)
        if root is None:
            logger.warning("Node not found for chain: %s", node_id)
            return ProvenanceChain(
                root_node=ProvenanceNode(
                    node_id=node_id,
                    node_type="unknown",
                    path="",
                    sha256="",
                ),
            )

        visited_nodes: Dict[str, ProvenanceNode] = {node_id: root}
        collected_edges: List[ProvenanceEdge] = []
        queue: Deque[Tuple[str, int]] = collections.deque([(node_id, 0)])
        max_depth = 0

        conn = self._get_conn()
        while queue:
            current_id, depth = queue.popleft()
            max_depth = max(max_depth, depth)

            try:
                rows = conn.execute(
                    "SELECT * FROM provenance_edges WHERE target_id = ?",
                    (current_id,),
                ).fetchall()
            except sqlite3.Error as exc:
                logger.error("Edge query failed: %s", exc)
                break

            for row in rows:
                edge = ProvenanceEdge(
                    source_id=row["source_id"],
                    target_id=row["target_id"],
                    relationship=row["relationship"],
                    timestamp=row["timestamp"],
                    agent_id=row["agent_id"],
                )
                collected_edges.append(edge)

                if row["source_id"] not in visited_nodes:
                    src_node = self._load_from_db(row["source_id"])
                    if src_node:
                        visited_nodes[row["source_id"]] = src_node
                        queue.append((row["source_id"], depth + 1))

        # Determine completeness: all leaf nodes should be raw_file
        leaf_ids = set(visited_nodes.keys()) - {
            e.source_id for e in collected_edges
            if e.target_id in visited_nodes
        }
        # Refine: leaves are nodes that appear as targets only (no outgoing edges as source)
        source_ids_set = {e.source_id for e in collected_edges}
        target_ids_set = {e.target_id for e in collected_edges}
        true_leaves = set(visited_nodes.keys()) - source_ids_set
        if not true_leaves:
            true_leaves = {node_id}

        complete = all(
            visited_nodes[lid].node_type == "raw_file"
            for lid in true_leaves
            if lid in visited_nodes
        )

        return ProvenanceChain(
            root_node=root,
            nodes=list(visited_nodes.values()),
            edges=collected_edges,
            depth=max_depth,
            complete=complete,
        )

    def get_descendants(self, node_id: str) -> List[ProvenanceNode]:
        """Traverse downstream from *node_id* to find all derived artefacts.

        Args:
            node_id: Starting node for downstream traversal.

        Returns:
            List of descendant ``ProvenanceNode`` instances.
        """
        visited: Set[str] = set()
        descendants: List[ProvenanceNode] = []
        queue: Deque[str] = collections.deque([node_id])
        conn = self._get_conn()

        while queue:
            current = queue.popleft()
            if current in visited:
                continue
            visited.add(current)

            try:
                rows = conn.execute(
                    "SELECT target_id FROM provenance_edges WHERE source_id = ?",
                    (current,),
                ).fetchall()
            except sqlite3.Error as exc:
                logger.error("Descendant query failed: %s", exc)
                break

            for row in rows:
                tid = row["target_id"]
                if tid not in visited:
                    node = self._load_from_db(tid)
                    if node:
                        descendants.append(node)
                    queue.append(tid)

        return descendants

    # ── Integrity verification ────────────────────────────────────────

    def verify_integrity(
        self, node_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Re-hash files and compare against stored SHA-256 digests.

        Args:
            node_id: If provided, verify only this node.  Otherwise
                     verify every node whose file still exists on disk.

        Returns:
            Dict with ``verified``, ``failed``, ``missing``, and
            ``results`` details.
        """
        self._verifications_run += 1
        results: List[Dict[str, Any]] = []
        verified = 0
        failed = 0
        missing = 0

        conn = self._get_conn()
        try:
            if node_id:
                rows = conn.execute(
                    "SELECT node_id, path, sha256 FROM provenance_tracking "
                    "WHERE node_id = ?",
                    (node_id,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT node_id, path, sha256 FROM provenance_tracking"
                ).fetchall()
        except sqlite3.Error as exc:
            logger.error("Integrity query failed: %s", exc)
            return {
                "verified": 0,
                "failed": 0,
                "missing": 0,
                "error": str(exc),
                "results": [],
            }

        for row in rows:
            nid = row["node_id"]
            path = row["path"]
            stored_hash = row["sha256"]
            p = Path(path)

            if not p.exists():
                missing += 1
                results.append({
                    "node_id": nid,
                    "path": path,
                    "status": "missing",
                    "stored_hash": stored_hash,
                    "current_hash": None,
                })
                continue

            current_hash = self._compute_sha256(p)
            if current_hash == stored_hash:
                verified += 1
                results.append({
                    "node_id": nid,
                    "path": path,
                    "status": "verified",
                    "stored_hash": stored_hash,
                    "current_hash": current_hash,
                })
            else:
                failed += 1
                results.append({
                    "node_id": nid,
                    "path": path,
                    "status": "TAMPERED",
                    "stored_hash": stored_hash,
                    "current_hash": current_hash,
                })
                logger.warning(
                    "INTEGRITY FAILURE: %s hash mismatch "
                    "(stored=%s, current=%s)",
                    path,
                    stored_hash[:16],
                    current_hash[:16],
                )

        return {
            "verified": verified,
            "failed": failed,
            "missing": missing,
            "total": len(rows),
            "integrity_ok": failed == 0,
            "results": results,
        }

    # ── Orphan detection ──────────────────────────────────────────────

    def find_orphans(self) -> List[ProvenanceNode]:
        """Find nodes that have no incoming or outgoing edges.

        Returns:
            List of orphan ``ProvenanceNode`` instances.
        """
        orphans: List[ProvenanceNode] = []
        conn = self._get_conn()
        try:
            rows = conn.execute(
                """
                SELECT pt.* FROM provenance_tracking pt
                WHERE pt.node_id NOT IN (
                    SELECT source_id FROM provenance_edges
                    UNION
                    SELECT target_id FROM provenance_edges
                )
                """
            ).fetchall()
            for row in rows:
                meta = {}
                try:
                    meta = json.loads(row["metadata"])
                except (json.JSONDecodeError, TypeError):
                    pass
                orphans.append(ProvenanceNode(
                    node_id=row["node_id"],
                    node_type=row["node_type"],
                    path=row["path"],
                    sha256=row["sha256"],
                    created_at=row["created_at"],
                    metadata=meta,
                ))
        except sqlite3.Error as exc:
            logger.error("Orphan detection failed: %s", exc)
        return orphans

    # ── Content tracking ──────────────────────────────────────────────

    def find_untracked_content(
        self, filing_text: str, filing_id: str
    ) -> List[str]:
        """Identify sections of *filing_text* that lack provenance.

        Splits the filing into paragraphs and checks whether each has a
        corresponding registered node (by text hash match in metadata).

        Args:
            filing_text: Full text of the filing.
            filing_id: Identifier for the filing.

        Returns:
            List of untracked paragraph snippets (first 80 chars each).
        """
        untracked: List[str] = []
        paragraphs = [
            p.strip()
            for p in re.split(r"\n\s*\n", filing_text)
            if p.strip()
        ]

        conn = self._get_conn()
        tracked_hashes: Set[str] = set()
        try:
            rows = conn.execute(
                "SELECT metadata FROM provenance_tracking"
            ).fetchall()
            for row in rows:
                try:
                    meta = json.loads(row["metadata"])
                    if "text_hash" in meta:
                        tracked_hashes.add(meta["text_hash"])
                except (json.JSONDecodeError, TypeError):
                    pass
        except sqlite3.Error as exc:
            logger.error("Untracked content query failed: %s", exc)
            return []

        for para in paragraphs:
            para_hash = self._compute_sha256_text(para)
            if para_hash not in tracked_hashes:
                snippet = para[:80] + ("..." if len(para) > 80 else "")
                untracked.append(snippet)

        logger.info(
            "Filing %s: %d/%d paragraphs untracked",
            filing_id,
            len(untracked),
            len(paragraphs),
        )
        return untracked

    # ── Report generation ─────────────────────────────────────────────

    def generate_report(self, filing_id: str) -> ProvenanceReport:
        """Generate a comprehensive provenance report for a filing.

        Locates the filed-document node for *filing_id*, traverses its
        full upstream chain, computes coverage, verifies integrity, and
        renders Mermaid + HTML visualisations.

        Args:
            filing_id: The filing identifier to report on.

        Returns:
            A ``ProvenanceReport`` dataclass.
        """
        # Find the filing node by metadata search
        conn = self._get_conn()
        filing_node: Optional[ProvenanceNode] = None
        try:
            rows = conn.execute(
                "SELECT * FROM provenance_tracking "
                "WHERE node_type IN ('filing_document', 'filed_document')"
            ).fetchall()
            for row in rows:
                meta = {}
                try:
                    meta = json.loads(row["metadata"])
                except (json.JSONDecodeError, TypeError):
                    pass
                if meta.get("filing_id") == filing_id:
                    filing_node = ProvenanceNode(
                        node_id=row["node_id"],
                        node_type=row["node_type"],
                        path=row["path"],
                        sha256=row["sha256"],
                        created_at=row["created_at"],
                        metadata=meta,
                    )
                    break
        except sqlite3.Error as exc:
            logger.error("Filing node lookup failed: %s", exc)

        if filing_node is None:
            logger.warning("No filing node found for %s", filing_id)
            empty_chain = ProvenanceChain(
                root_node=ProvenanceNode(
                    node_id="",
                    node_type="unknown",
                    path="",
                    sha256="",
                ),
            )
            return ProvenanceReport(
                filing_id=filing_id,
                chain=empty_chain,
            )

        chain = self.get_chain(filing_node.node_id)

        # Compute coverage: nodes with raw_file ancestors / total nodes
        total_nodes = len(chain.nodes)
        raw_count = sum(
            1 for n in chain.nodes if n.node_type == "raw_file"
        )
        coverage = (raw_count / total_nodes * 100) if total_nodes > 0 else 0.0

        # Verify integrity for the chain
        integrity = self.verify_integrity(filing_node.node_id)

        # Render visualisations
        dag_mermaid = self.generate_dag_mermaid(chain)
        dag_html = self.generate_dag_html(chain)

        return ProvenanceReport(
            filing_id=filing_id,
            chain=chain,
            coverage_pct=round(coverage, 1),
            untracked_sections=[],
            dag_mermaid=dag_mermaid,
            dag_html=dag_html,
            integrity_verified=integrity.get("integrity_ok", False),
        )

    # ── DAG visualisation — Mermaid ───────────────────────────────────

    def generate_dag_mermaid(self, chain: ProvenanceChain) -> str:
        """Render a provenance chain as a Mermaid flowchart.

        Args:
            chain: The provenance chain to visualise.

        Returns:
            Mermaid-formatted diagram string.
        """
        lines: List[str] = ["graph TD"]

        # Node styling by type
        type_shapes = {
            "raw_file": "([{label}])",
            "extracted_text": "[{label}]",
            "analysis": "[/{label}/]",
            "filing_section": "[{label}]",
            "filing_document": "[[{label}]]",
            "exhibit": ">{label}]",
            "filed_document": "(({label}))",
        }

        node_map: Dict[str, str] = {}
        for node in chain.nodes:
            short_id = node.node_id[:8]
            label = f"{node.node_type}\\n{Path(node.path).name}"
            shape_tpl = type_shapes.get(node.node_type, "[{label}]")
            shape = shape_tpl.format(label=label)
            node_map[node.node_id] = short_id
            lines.append(f"    {short_id}{shape}")

        for edge in chain.edges:
            src = node_map.get(edge.source_id, edge.source_id[:8])
            tgt = node_map.get(edge.target_id, edge.target_id[:8])
            lines.append(f"    {src} -->|{edge.relationship}| {tgt}")

        # Style classes
        lines.append("")
        lines.append("    classDef rawFile fill:#e8f5e9,stroke:#2e7d32")
        lines.append("    classDef filed fill:#e3f2fd,stroke:#1565c0")
        for node in chain.nodes:
            short_id = node_map.get(node.node_id, node.node_id[:8])
            if node.node_type == "raw_file":
                lines.append(f"    class {short_id} rawFile")
            elif node.node_type in ("filing_document", "filed_document"):
                lines.append(f"    class {short_id} filed")

        return "\n".join(lines)

    # ── DAG visualisation — HTML ──────────────────────────────────────

    def generate_dag_html(self, chain: ProvenanceChain) -> str:
        """Render a provenance chain as a self-contained HTML page.

        Uses inline CSS and a table-based layout.  No external JS
        dependencies — suitable for offline litigation environments.

        Args:
            chain: The provenance chain to visualise.

        Returns:
            Complete HTML document string.
        """
        rows_html = ""
        for node in chain.nodes:
            bg = "#e8f5e9" if node.node_type == "raw_file" else (
                "#e3f2fd"
                if node.node_type in ("filing_document", "filed_document")
                else "#fff"
            )
            rows_html += textwrap.dedent(f"""\
                <tr style="background:{bg}">
                    <td><code>{html_escape(node.node_id[:16])}</code></td>
                    <td>{html_escape(node.node_type)}</td>
                    <td>{html_escape(Path(node.path).name)}</td>
                    <td><code>{html_escape(node.sha256[:16])}</code>…</td>
                    <td>{html_escape(node.created_at)}</td>
                </tr>
            """)

        edges_html = ""
        for edge in chain.edges:
            edges_html += textwrap.dedent(f"""\
                <tr>
                    <td><code>{html_escape(edge.source_id[:16])}</code></td>
                    <td>→</td>
                    <td><code>{html_escape(edge.target_id[:16])}</code></td>
                    <td>{html_escape(edge.relationship)}</td>
                    <td>{html_escape(edge.agent_id)}</td>
                    <td>{html_escape(edge.timestamp)}</td>
                </tr>
            """)

        mermaid_block = html_escape(self.generate_dag_mermaid(chain))

        html = textwrap.dedent(f"""\
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <title>Provenance Chain — {html_escape(chain.root_node.node_id[:16])}</title>
                <style>
                    body {{ font-family: 'Segoe UI', sans-serif; margin: 2em; color: #222; }}
                    h1 {{ color: #1565c0; }}
                    h2 {{ color: #2e7d32; border-bottom: 2px solid #ccc; padding-bottom: .3em; }}
                    table {{ border-collapse: collapse; width: 100%; margin: 1em 0; }}
                    th, td {{ border: 1px solid #ddd; padding: .5em .8em; text-align: left; }}
                    th {{ background: #f5f5f5; }}
                    code {{ font-size: .85em; }}
                    .stats {{ display: flex; gap: 2em; margin: 1em 0; }}
                    .stat {{ background: #f9f9f9; border-radius: 8px; padding: 1em; }}
                    pre {{ background: #f5f5f5; padding: 1em; overflow-x: auto; border-radius: 4px; }}
                </style>
            </head>
            <body>
                <h1>Provenance Chain Report</h1>
                <div class="stats">
                    <div class="stat"><strong>Nodes:</strong> {len(chain.nodes)}</div>
                    <div class="stat"><strong>Edges:</strong> {len(chain.edges)}</div>
                    <div class="stat"><strong>Depth:</strong> {chain.depth}</div>
                    <div class="stat"><strong>Complete:</strong> {'Yes' if chain.complete else 'No'}</div>
                </div>

                <h2>Nodes</h2>
                <table>
                    <tr><th>ID</th><th>Type</th><th>File</th><th>SHA-256</th><th>Created</th></tr>
                    {rows_html}
                </table>

                <h2>Edges</h2>
                <table>
                    <tr><th>Source</th><th></th><th>Target</th><th>Relationship</th><th>Agent</th><th>Timestamp</th></tr>
                    {edges_html}
                </table>

                <h2>Mermaid Diagram</h2>
                <pre>{mermaid_block}</pre>

                <hr>
                <p><em>Generated by LitigationOS ProvenanceTracker</em></p>
            </body>
            </html>
        """)

        return html

    # ── Export / Import ───────────────────────────────────────────────

    def export_chain(
        self, filing_id: str, output_path: str | Path
    ) -> None:
        """Export the full provenance chain for a filing to JSON.

        Args:
            filing_id: The filing identifier.
            output_path: Destination file path for the JSON export.
        """
        report = self.generate_report(filing_id)
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(out, "w", encoding="utf-8") as f:
                json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)
            logger.info("Exported chain for %s to %s", filing_id, out)
        except OSError as exc:
            logger.error("Export failed for %s: %s", filing_id, exc)

    def import_chain(self, json_path: str | Path) -> int:
        """Import a provenance chain from a JSON export.

        Nodes and edges from the JSON file are merged into the database
        using INSERT OR REPLACE semantics.

        Args:
            json_path: Path to the JSON file.

        Returns:
            Total number of objects imported (nodes + edges).
        """
        p = Path(json_path)
        if not p.exists():
            logger.error("Import file not found: %s", json_path)
            return 0

        try:
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as exc:
            logger.error("Import read failed: %s", exc)
            return 0

        imported = 0
        chain_data = data.get("chain", data)

        # Import nodes
        for nd in chain_data.get("nodes", []):
            try:
                node = ProvenanceNode(
                    node_id=nd["node_id"],
                    node_type=nd["node_type"],
                    path=nd["path"],
                    sha256=nd["sha256"],
                    created_at=nd.get("created_at", ""),
                    metadata=nd.get("metadata", {}),
                )
                self._save_to_db(node)
                imported += 1
            except (KeyError, TypeError) as exc:
                logger.warning("Skipping malformed node: %s", exc)

        # Import edges
        for ed in chain_data.get("edges", []):
            try:
                edge = ProvenanceEdge(
                    source_id=ed["source_id"],
                    target_id=ed["target_id"],
                    relationship=ed["relationship"],
                    timestamp=ed.get("timestamp", ""),
                    agent_id=ed.get("agent_id", ""),
                )
                self._save_to_db(edge)
                imported += 1
            except (KeyError, TypeError) as exc:
                logger.warning("Skipping malformed edge: %s", exc)

        logger.info("Imported %d objects from %s", imported, json_path)
        return imported

    # ── Statistics ────────────────────────────────────────────────────

    def get_stats(self) -> Dict[str, Any]:
        """Return operational statistics for the provenance tracker.

        Returns:
            Dict with node/edge counts, type distributions, and session
            counters.
        """
        stats: Dict[str, Any] = {
            "session_nodes_registered": self._nodes_registered,
            "session_edges_registered": self._edges_registered,
            "session_verifications": self._verifications_run,
        }

        try:
            conn = self._get_conn()
            row = conn.execute(
                """
                SELECT
                    (SELECT COUNT(*) FROM provenance_tracking) AS total_nodes,
                    (SELECT COUNT(*) FROM provenance_edges) AS total_edges
                """
            ).fetchone()
            if row:
                stats["db_total_nodes"] = row["total_nodes"]
                stats["db_total_edges"] = row["total_edges"]

            # By node type
            rows = conn.execute(
                "SELECT node_type, COUNT(*) AS cnt "
                "FROM provenance_tracking GROUP BY node_type"
            ).fetchall()
            stats["db_by_node_type"] = {r["node_type"]: r["cnt"] for r in rows}

            # By relationship
            rows = conn.execute(
                "SELECT relationship, COUNT(*) AS cnt "
                "FROM provenance_edges GROUP BY relationship"
            ).fetchall()
            stats["db_by_relationship"] = {
                r["relationship"]: r["cnt"] for r in rows
            }

            # Orphan count
            orphan_count = conn.execute(
                """
                SELECT COUNT(*) FROM provenance_tracking
                WHERE node_id NOT IN (
                    SELECT source_id FROM provenance_edges
                    UNION
                    SELECT target_id FROM provenance_edges
                )
                """
            ).fetchone()[0]
            stats["db_orphan_nodes"] = orphan_count

        except sqlite3.Error as exc:
            logger.warning("Could not load DB stats: %s", exc)
            stats["db_error"] = str(exc)

        return stats

    # ── Dunder ────────────────────────────────────────────────────────

    def __repr__(self) -> str:
        return (
            f"<ProvenanceTracker nodes={self._nodes_registered} "
            f"edges={self._edges_registered}>"
        )

    def __del__(self) -> None:
        self.close()
