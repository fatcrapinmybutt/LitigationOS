#!/usr/bin/env python3
\"\"\"
graph_export_evidence_authority.py

Builds a simple combined graph JSON from:
- RUN_MANIFEST_EVIDENCE_RAG_<run_id>.json
- ASSERTION_EVIDENCE_LINKS_<run_id>.jsonl
\"\"\"

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List

DEFAULT_BASE_DIR = r"F:\\LitigationOS"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Export assertion-evidence graph.")
    p.add_argument(
        "--base-dir",
        type=str,
        default=DEFAULT_BASE_DIR,
        help="Base LitigationOS directory.",
    )
    p.add_argument(
        "--manifest-path",
        type=str,
        default=None,
        help="Optional explicit RUN_MANIFEST_EVIDENCE_RAG_*.json path.",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate; do not write graph.",
    )
    return p.parse_args()


def setup_logging(log_path: Path) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(fmt)
    logger.addHandler(ch)
    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setFormatter(fmt)
    logger.addHandler(fh)


def find_latest_manifest(runs_dir: Path) -> Path:
    candidates = list(runs_dir.rglob("RUN_MANIFEST_EVIDENCE_RAG_*.json"))
    if not candidates:
        raise FileNotFoundError(f"No RUN_MANIFEST_EVIDENCE_RAG_*.json under {runs_dir}")
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0]


def load_manifest(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_links(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def build_graph(links: List[Dict[str, Any]]) -> Dict[str, Any]:
    nodes = {}
    edges = []
    for row in links:
        a_id = row["assertion_id"]
        e_id = row["evidence_id"]

        if a_id not in nodes:
            nodes[a_id] = {
                "id": a_id,
                "type": "assertion",
                "label": a_id,
                "text": row.get("assertion_text", ""),
            }
        if e_id not in nodes:
            nodes[e_id] = {
                "id": e_id,
                "type": "evidence",
                "label": e_id,
                "path": row.get("evidence_path", ""),
                "snippet": row.get("evidence_snippet", ""),
            }
        edges.append(
            {
                "id": f"{a_id}__HAS_EVIDENCE__{e_id}",
                "source": a_id,
                "target": e_id,
                "type": "HAS_EVIDENCE",
                "score": row.get("score", 0),
                "rank": row.get("rank", 0),
            }
        )

    return {
        "nodes": list(nodes.values()),
        "edges": edges,
        "meta": {
            "type": "ASSERTION_EVIDENCE_GRAPH",
            "node_types": ["assertion", "evidence"],
            "edge_types": ["HAS_EVIDENCE"],
        },
    }


def main() -> None:
    args = parse_args()
    base_dir = Path(args.base_dir)
    runs_dir = base_dir / "runs"
    logs_dir = base_dir / "logs"
    setup_logging(logs_dir / "graph_export_evidence_authority.log")

    if args.manifest_path:
        manifest_path = Path(args.manifest_path)
    else:
        manifest_path = find_latest_manifest(runs_dir)

    logging.info("Using manifest: %s", manifest_path)
    manifest = load_manifest(manifest_path)
    links_path = Path(manifest["links_path"])
    links = load_links(links_path)
    logging.info("Loaded %d links from %s", len(links), links_path)

    graph = build_graph(links)
    run_id = manifest["run_id"]
    graph_path = Path(manifest_path).parent / f"ASSERTION_EVIDENCE_GRAPH_{run_id}.json"

    if args.dry_run:
        logging.info("[DRY-RUN] Would write graph JSON to %s", graph_path)
    else:
        graph_path.write_text(json.dumps(graph, indent=2), encoding="utf-8")
        logging.info("Wrote graph JSON: %s", graph_path)

    # Update manifest graphs
    if not args.dry_run:
        graphs = manifest.get("graphs", [])
        graphs.append({"role": "combined_assertion_evidence_graph", "path": str(graph_path)})
        manifest["graphs"] = graphs
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        logging.info("Updated manifest graphs list.")

    print(str(graph_path))


if __name__ == "__main__":
    main()
