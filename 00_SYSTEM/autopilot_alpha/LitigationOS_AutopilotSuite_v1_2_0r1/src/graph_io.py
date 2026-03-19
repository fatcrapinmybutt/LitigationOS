\
from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List


@dataclass(frozen=True)
class Node:
    uid: str
    node_type: str
    labels: List[str]
    props: Dict[str, Any]


@dataclass(frozen=True)
class Edge:
    uid: str
    rel_type: str
    from_uid: str
    to_uid: str
    props: Dict[str, Any]


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def write_nodes_csv(path: Path, nodes: List[Node]) -> None:
    ensure_dir(path.parent)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["uid:ID", "uid", "node_type", "labels:LABEL", "props_json"])
        for n in nodes:
            w.writerow([n.uid, n.uid, n.node_type, ";".join(n.labels), json.dumps(n.props, ensure_ascii=False, sort_keys=True)])


def write_edges_csv(path: Path, edges: List[Edge]) -> None:
    ensure_dir(path.parent)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["uid", "from_uid:START_ID", "to_uid:END_ID", "rel_type:TYPE", "props_json"])
        for e in edges:
            w.writerow([e.uid, e.from_uid, e.to_uid, e.rel_type, json.dumps(e.props, ensure_ascii=False, sort_keys=True)])
