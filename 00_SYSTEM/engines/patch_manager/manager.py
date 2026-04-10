"""PatchManager — runtime patch/hot-reload engine for THEMANBEARPIG.

Reads external JSON patch files from a ``patches/`` directory and merges them
into the in-memory D3 graph data (``{"nodes": [...], "links": [...]}``)
without requiring a PyInstaller rebuild.

Patch lifecycle:
    1. ``create_patch()`` or ``generate_patch_from_db()`` writes a patch file.
    2. On next THEMANBEARPIG launch, ``apply_all_pending()`` detects and applies it.
    3. Manifest tracks which patches have been applied + version history.
"""

from __future__ import annotations

import copy
import logging
import re
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# --- JSON import: avoid repo-root shadow module --------------------------------
try:
    import orjson  # type: ignore[import-untyped]

    def _json_loads(data: bytes | str) -> Any:
        if isinstance(data, str):
            data = data.encode("utf-8")
        return orjson.loads(data)

    def _json_dumps(obj: Any, *, indent: bool = True) -> str:
        opts = orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS if indent else orjson.OPT_SORT_KEYS
        return orjson.dumps(obj, option=opts).decode("utf-8")

except ImportError:
    import json as _json

    def _json_loads(data: bytes | str) -> Any:  # type: ignore[misc]
        if isinstance(data, bytes):
            data = data.decode("utf-8")
        return _json.loads(data)

    def _json_dumps(obj: Any, *, indent: bool = True) -> str:  # type: ignore[misc]
        return _json.dumps(obj, indent=2 if indent else None, sort_keys=True, ensure_ascii=False)


log = logging.getLogger(__name__)

# --- Constants ----------------------------------------------------------------
_EMPTY_MANIFEST: dict[str, Any] = {
    "version": "22.0.0",
    "last_applied": None,
    "patches": [],
}

_VALID_OPS = frozenset({
    "add_nodes",
    "add_links",
    "update_nodes",
    "remove_nodes",
    "remove_links",
    "update_config",
})

_VALID_PATCH_TYPES = frozenset({"data", "config", "layer", "fix"})

_DB_PRAGMAS = (
    "PRAGMA busy_timeout = 60000",
    "PRAGMA journal_mode = WAL",
    "PRAGMA cache_size = -32000",
    "PRAGMA synchronous = NORMAL",
    "PRAGMA temp_store = MEMORY",
)


def _slugify(text: str) -> str:
    """Convert text to a safe slug for IDs."""
    slug = re.sub(r"[^a-z0-9]+", "_", text.lower().strip())
    return slug.strip("_")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _connect_db(db_path: str | Path) -> sqlite3.Connection:
    """Open a DB connection with mandatory PRAGMAs."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    for pragma in _DB_PRAGMAS:
        conn.execute(pragma)
    return conn


# ===========================================================================
# PatchManager
# ===========================================================================
class PatchManager:
    """Manages external JSON patches for THEMANBEARPIG's D3 graph data."""

    def __init__(self, base_dir: str | Path | None = None) -> None:
        if base_dir is None:
            if getattr(sys, "frozen", False):
                base_dir = Path(sys.executable).resolve().parent
            else:
                base_dir = Path(__file__).resolve().parents[3]  # → LitigationOS/
        self._base = Path(base_dir)
        self._patches_dir = self._base / "patches"
        self._manifest_path = self._patches_dir / "manifest.json"

    # ----- directory / manifest -------------------------------------------

    def get_patches_dir(self) -> Path:
        """Return the ``patches/`` directory, creating it if absent."""
        self._patches_dir.mkdir(parents=True, exist_ok=True)
        return self._patches_dir

    def load_manifest(self) -> dict[str, Any]:
        """Load ``manifest.json`` or create a fresh empty one."""
        path = self._manifest_path
        if path.exists():
            try:
                return _json_loads(path.read_bytes())
            except Exception as exc:
                log.warning("Corrupt manifest — resetting: %s", exc)
        manifest = copy.deepcopy(_EMPTY_MANIFEST)
        self.save_manifest(manifest)
        return manifest

    def save_manifest(self, manifest: dict[str, Any]) -> None:
        """Persist *manifest* to ``manifest.json``."""
        self.get_patches_dir()  # ensure dir exists
        self._manifest_path.write_text(_json_dumps(manifest), encoding="utf-8")

    # ----- listing --------------------------------------------------------

    def list_applied_patches(self) -> list[dict[str, Any]]:
        """Return the list of applied-patch records from the manifest."""
        return self.load_manifest().get("patches", [])

    def list_available_patches(self) -> list[Path]:
        """Return sorted list of patch files that have *not* been applied yet."""
        patches_dir = self.get_patches_dir()
        applied_ids = {p["id"] for p in self.list_applied_patches()}

        available: list[Path] = []
        for f in sorted(patches_dir.glob("patch_*.json")):
            if f.name == "manifest.json":
                continue
            try:
                header = _json_loads(f.read_bytes())
                if header.get("patch_id") not in applied_ids:
                    available.append(f)
            except Exception:
                log.warning("Skipping unreadable patch file: %s", f.name)
        return available

    # ----- apply ----------------------------------------------------------

    def apply_patch(self, patch_file: str | Path, graph_data: dict[str, Any]) -> dict[str, Any]:
        """Apply a single patch file to *graph_data* (mutates in-place).

        ``graph_data`` must contain ``"nodes"`` (list) and ``"links"`` (list).
        Returns the modified ``graph_data``.
        """
        path = Path(patch_file)
        if not path.is_absolute():
            path = self.get_patches_dir() / path
        if not path.exists():
            raise FileNotFoundError(f"Patch file not found: {path}")

        patch = _json_loads(path.read_bytes())
        patch_id = patch["patch_id"]
        patch_type = patch.get("patch_type", "data")
        version = patch.get("version", "0.0.0")

        if patch_type not in _VALID_PATCH_TYPES:
            raise ValueError(f"Invalid patch_type '{patch_type}' in {patch_id}")

        nodes: list[dict] = graph_data.setdefault("nodes", [])
        links: list[dict] = graph_data.setdefault("links", [])

        # Build a lookup for fast node access by ID
        node_index: dict[str, int] = {n["id"]: i for i, n in enumerate(nodes)}

        operations = patch.get("operations", [])
        stats = {"nodes_added": 0, "links_added": 0, "nodes_updated": 0,
                 "nodes_removed": 0, "links_removed": 0, "configs_set": 0}

        for op_block in operations:
            op = op_block.get("op", "")
            if op not in _VALID_OPS:
                log.warning("Unknown op '%s' in patch %s — skipping", op, patch_id)
                continue

            if op == "add_nodes":
                for node in op_block.get("nodes", []):
                    nid = node.get("id")
                    if not nid:
                        continue
                    if nid in node_index:
                        # Merge into existing node instead of duplicating
                        existing = nodes[node_index[nid]]
                        existing.update(node)
                        stats["nodes_updated"] += 1
                    else:
                        node_index[nid] = len(nodes)
                        nodes.append(node)
                        stats["nodes_added"] += 1

            elif op == "add_links":
                existing_links = {(l.get("source"), l.get("target"), l.get("type"))
                                  for l in links}
                for link in op_block.get("links", []):
                    key = (link.get("source"), link.get("target"), link.get("type"))
                    if key not in existing_links:
                        links.append(link)
                        existing_links.add(key)
                        stats["links_added"] += 1

            elif op == "update_nodes":
                for update in op_block.get("updates", []):
                    nid = update.get("id")
                    merge = update.get("merge", {})
                    if nid and nid in node_index:
                        nodes[node_index[nid]].update(merge)
                        stats["nodes_updated"] += 1

            elif op == "remove_nodes":
                remove_ids = set(op_block.get("node_ids", []))
                if remove_ids:
                    graph_data["nodes"] = [n for n in nodes if n.get("id") not in remove_ids]
                    graph_data["links"] = [
                        l for l in links
                        if l.get("source") not in remove_ids and l.get("target") not in remove_ids
                    ]
                    stats["nodes_removed"] += len(remove_ids)
                    # Rebuild references
                    nodes = graph_data["nodes"]
                    links = graph_data["links"]
                    node_index = {n["id"]: i for i, n in enumerate(nodes)}

            elif op == "remove_links":
                remove_keys = {(r.get("source"), r.get("target"), r.get("type"))
                               for r in op_block.get("links", [])}
                if remove_keys:
                    before = len(links)
                    graph_data["links"] = [
                        l for l in links
                        if (l.get("source"), l.get("target"), l.get("type")) not in remove_keys
                    ]
                    links = graph_data["links"]
                    stats["links_removed"] += before - len(links)

            elif op == "update_config":
                cfg = op_block.get("config", {})
                graph_data.setdefault("config", {}).update(cfg)
                stats["configs_set"] += len(cfg)

        # Record in manifest
        manifest = self.load_manifest()
        manifest["patches"].append({
            "id": patch_id,
            "name": patch.get("description", patch_id),
            "type": patch_type,
            "file": path.name,
            "applied_at": _now_iso(),
            "version_bump": version,
            "stats": stats,
        })
        manifest["last_applied"] = patch_id
        manifest["version"] = version
        self.save_manifest(manifest)

        log.info("Applied patch %s: +%d nodes, +%d links, ~%d updates",
                 patch_id, stats["nodes_added"], stats["links_added"], stats["nodes_updated"])
        return graph_data

    def apply_all_pending(self, graph_data: dict[str, Any]) -> dict[str, Any]:
        """Apply every unapplied patch in sorted order. Returns modified *graph_data*."""
        pending = self.list_available_patches()
        if not pending:
            log.info("No pending patches.")
            return graph_data
        for patch_path in pending:
            try:
                graph_data = self.apply_patch(patch_path, graph_data)
            except Exception as exc:
                log.error("Failed to apply %s: %s", patch_path.name, exc)
        return graph_data

    # ----- create ---------------------------------------------------------

    def create_patch(
        self,
        patch_id: str,
        description: str,
        operations: list[dict[str, Any]],
        patch_type: str = "data",
        version: str | None = None,
    ) -> str:
        """Create a new patch file and return its absolute path."""
        if patch_type not in _VALID_PATCH_TYPES:
            raise ValueError(f"Invalid patch_type: {patch_type}")

        # Auto-version: bump last digit of current manifest version
        if version is None:
            manifest = self.load_manifest()
            parts = manifest["version"].split(".")
            parts[-1] = str(int(parts[-1]) + 1)
            version = ".".join(parts)

        patch = {
            "patch_id": patch_id,
            "patch_type": patch_type,
            "version": version,
            "created_at": _now_iso(),
            "description": description,
            "operations": operations,
        }

        filename = f"{patch_id}.json"
        path = self.get_patches_dir() / filename
        path.write_text(_json_dumps(patch), encoding="utf-8")
        log.info("Created patch: %s", path)
        return str(path)

    # ----- rollback -------------------------------------------------------

    def rollback_patch(self, patch_id: str, graph_data: dict[str, Any]) -> dict[str, Any]:
        """Rollback a patch by inverting its operations.

        Only ``add_nodes`` and ``add_links`` are reversible (remove what was added).
        ``update_nodes`` cannot be reversed without storing the original values.
        """
        patch_path = self.get_patches_dir() / f"{patch_id}.json"
        if not patch_path.exists():
            raise FileNotFoundError(f"Patch file not found for rollback: {patch_id}")

        patch = _json_loads(patch_path.read_bytes())
        nodes: list[dict] = graph_data.get("nodes", [])
        links: list[dict] = graph_data.get("links", [])

        for op_block in patch.get("operations", []):
            op = op_block.get("op", "")

            if op == "add_nodes":
                added_ids = {n["id"] for n in op_block.get("nodes", []) if "id" in n}
                graph_data["nodes"] = [n for n in nodes if n.get("id") not in added_ids]
                graph_data["links"] = [
                    l for l in links
                    if l.get("source") not in added_ids and l.get("target") not in added_ids
                ]
                nodes = graph_data["nodes"]
                links = graph_data["links"]

            elif op == "add_links":
                added_keys = {(l.get("source"), l.get("target"), l.get("type"))
                              for l in op_block.get("links", [])}
                graph_data["links"] = [
                    l for l in links
                    if (l.get("source"), l.get("target"), l.get("type")) not in added_keys
                ]
                links = graph_data["links"]

        # Remove from manifest
        manifest = self.load_manifest()
        manifest["patches"] = [p for p in manifest["patches"] if p["id"] != patch_id]
        if manifest["patches"]:
            manifest["last_applied"] = manifest["patches"][-1]["id"]
            manifest["version"] = manifest["patches"][-1]["version_bump"]
        else:
            manifest["last_applied"] = None
            manifest["version"] = "22.0.0"
        self.save_manifest(manifest)

        log.info("Rolled back patch: %s", patch_id)
        return graph_data

    # ----- DB-to-patch generation -----------------------------------------

    def generate_patch_from_db(
        self,
        db_path: str | Path,
        query: str,
        node_type: str,
        layer: str,
        patch_id: str | None = None,
        description: str | None = None,
        id_column: str = "id",
        label_column: str = "name",
        params: tuple[Any, ...] = (),
    ) -> str:
        """Generate a patch file from a database query.

        Each result row becomes a node. Column values become node data fields.
        Returns the path of the created patch file.
        """
        conn = _connect_db(db_path)
        try:
            rows = conn.execute(query, params).fetchall()
            columns = [desc[0] for desc in conn.execute(query, params).description] if rows else []
        finally:
            conn.close()

        if not rows:
            log.warning("Query returned 0 rows — empty patch generated.")

        nodes: list[dict[str, Any]] = []
        for row in rows:
            row_dict = dict(zip(columns, row))
            nid = f"{node_type}_{_slugify(str(row_dict.get(id_column, len(nodes))))}"
            label = str(row_dict.get(label_column, nid))

            node: dict[str, Any] = {
                "id": nid,
                "label": label,
                "type": node_type,
                "layer": layer,
                "data": {k: v for k, v in row_dict.items() if v is not None},
            }
            nodes.append(node)

        if patch_id is None:
            patch_id = f"patch_db_{node_type}_{int(time.time())}"
        if description is None:
            description = f"Auto-generated from DB: {len(nodes)} {node_type} nodes"

        return self.create_patch(
            patch_id=patch_id,
            description=description,
            operations=[{"op": "add_nodes", "nodes": nodes}],
            patch_type="data",
        )

    # ----- status ---------------------------------------------------------

    def get_status(self) -> dict[str, Any]:
        """Return patch system status summary."""
        manifest = self.load_manifest()
        pending = self.list_available_patches()
        return {
            "version": manifest["version"],
            "applied_count": len(manifest["patches"]),
            "pending_count": len(pending),
            "pending_files": [p.name for p in pending],
            "last_applied": manifest["last_applied"],
            "patches_dir": str(self.get_patches_dir()),
        }
