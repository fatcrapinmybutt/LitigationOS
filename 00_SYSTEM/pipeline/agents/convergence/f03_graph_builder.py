"""
DELTA9 — F03 Graph Builder
Convergence Tier · MAX LEVEL 9999++

Merges all atoms into knowledge graph deltas (Neo4j-compatible CSV).
Runs AFTER both lanes complete.
"""
import csv
import hashlib
import io
from typing import Any

from ..agent_base import Agent9999
from ..agent_models import (
    SkipItemError, FatalAgentError, MASTER_INDEX_DB,
    LANE_A_SIGNALS, LANE_B_SIGNALS, LANE_C_SIGNALS,
)
from ..agent_models import CHECKPOINT_DIR

# Node type mapping from atom_type
_NODE_TYPES = {
    "citation": "Authority",
    "person": "Person",
    "fact": "Evidence",
    "event": "Event",
    "judicial_finding": "Evidence",
    "document": "Evidence",
}

# Edge type mapping for relationships between atom types
_EDGE_RULES = {
    "citation": "CITES",
    "person": "MENTIONS",
    "fact": "DOCUMENTS",
    "event": "DOCUMENTS",
}


class GraphBuilder(Agent9999):
    """Merges all atoms into knowledge graph deltas."""

    def __init__(self):
        super().__init__(agent_id="F03-GRAPH")
        self._nodes: list[dict] = []
        self._edges: list[dict] = []
        self._seen_node_ids: set[str] = set()

    # ------------------------------------------------------------------
    # Abstract implementations
    # ------------------------------------------------------------------
    def _validate_preconditions(self) -> None:
        cursor = self._db_execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='atoms'"
        )
        if not cursor.fetchone():
            raise FatalAgentError("atoms table missing — run Lane 2 first")

    def _get_work_items(self) -> list:
        cursor = self._db_execute("SELECT DISTINCT atom_type FROM atoms")
        rows = cursor.fetchall()
        return [r[0] for r in rows]

    def _process_item(self, atom_type: Any) -> None:
        cursor = self._db_execute("SELECT * FROM atoms WHERE atom_type = ?", (atom_type,))
        atoms = cursor.fetchall()
        if not atoms:
            raise SkipItemError(f"No atoms for type={atom_type}")

        node_label = _NODE_TYPES.get(atom_type, "Entity")
        edge_label = _EDGE_RULES.get(atom_type, "RELATED_TO")

        for atom in atoms:
            atom_id = atom["id"] if isinstance(atom, dict) else atom[0]
            content = atom["content"] if isinstance(atom, dict) else atom[3]
            source = atom["source_file"] if isinstance(atom, dict) else atom[4] if len(atom) > 4 else ""

            # Deterministic node ID
            node_id = self._make_node_id(node_label, str(atom_id))
            if node_id not in self._seen_node_ids:
                self._nodes.append({
                    "nodeId": node_id,
                    "label": node_label,
                    "atom_id": str(atom_id),
                    "atom_type": atom_type,
                    "content": (content or "")[:500],
                })
                self._seen_node_ids.add(node_id)

            # Generate edges to source document
            if source:
                source_node_id = self._make_node_id("Document", str(source))
                if source_node_id not in self._seen_node_ids:
                    self._nodes.append({
                        "nodeId": source_node_id,
                        "label": "Document",
                        "atom_id": "",
                        "atom_type": "source",
                        "content": str(source)[:500],
                    })
                    self._seen_node_ids.add(source_node_id)

                self._edges.append({
                    "sourceId": source_node_id,
                    "targetId": node_id,
                    "type": edge_label,
                })

        self._log("GRAPH", f"type={atom_type}: {len(atoms)} atoms → nodes/edges generated")

    def _finalize(self) -> None:
        CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)

        # Write nodes CSV
        nodes_path = CHECKPOINT_DIR / "neo4j_nodes_delta.csv"
        with open(nodes_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["nodeId", "label", "atom_id", "atom_type", "content"])
            writer.writeheader()
            writer.writerows(self._nodes)

        # Write edges CSV
        edges_path = CHECKPOINT_DIR / "neo4j_edges_delta.csv"
        with open(edges_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["sourceId", "targetId", "type"])
            writer.writeheader()
            writer.writerows(self._edges)

        self._log("DONE", f"Graph: {len(self._nodes)} nodes, {len(self._edges)} edges written")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _make_node_id(node_type: str, key_fields: str) -> str:
        """Deterministic node ID: sha1(type|key_fields)."""
        raw = f"{node_type}|{key_fields}"
        return hashlib.sha1(raw.encode("utf-8")).hexdigest()
