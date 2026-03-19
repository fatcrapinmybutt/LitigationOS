#!/usr/bin/env python3
"""
LitigationOS Compiler Runtime v1.0.0
- Ingests the user's current attachment set (nodes_merged.csv, nodes_neo4j_admin.csv,
  CONTRADICTION_MAP*.csv, optional graph_contract.yml + litigationos_constraints.yml)
- Emits:
    out/neo4j_nodes.csv
    out/neo4j_edges.csv
    out/graph.graphml
    out/violations.json
    out/action_report.md  (violation/gap -> (procedural) remedy -> vehicle -> authority candidates -> action)
- Deterministic ordering + idempotent outputs.

DRAFT / fail-soft: will not invent legal facts; all "linking" beyond explicit data is labeled as CANDIDATE/HEURISTIC.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import pandas as pd

try:
    import yaml  # PyYAML
except Exception:
    yaml = None

try:
    import networkx as nx
except Exception:
    nx = None


VERSION = "1.0.0"


# ---------------------------
# Utilities
# ---------------------------

def iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def die(msg: str, code: int = 2) -> None:
    print(f"[FATAL] {msg}", file=sys.stderr)
    raise SystemExit(code)


def read_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    if yaml is None:
        die("PyYAML is not available but a .yml file was provided/required.")
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def safe_json_loads(s: Any) -> Any:
    if s is None or (isinstance(s, float) and pd.isna(s)):
        return None
    if isinstance(s, (dict, list)):
        return s
    if not isinstance(s, str):
        return None
    s2 = s.strip()
    if not s2:
        return None
    try:
        return json.loads(s2)
    except Exception:
        return None


def normalize_labels(label_cell: Any) -> List[str]:
    if label_cell is None or (isinstance(label_cell, float) and pd.isna(label_cell)):
        return []
    if isinstance(label_cell, list):
        return [str(x).strip() for x in label_cell if str(x).strip()]
    s = str(label_cell).strip()
    if not s:
        return []
    # input uses "A;B;C"
    return [p.strip() for p in s.split(";") if p.strip()]


def clamp01(x: float) -> float:
    if x < 0:
        return 0.0
    if x > 1:
        return 1.0
    return float(x)


def stable_hash_id(*parts: str) -> str:
    import hashlib
    h = hashlib.sha1("||".join(parts).encode("utf-8")).hexdigest()
    return h[:24]


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


# ---------------------------
# Core data structures
# ---------------------------

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


# ---------------------------
# Loaders
# ---------------------------

def load_nodes_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    # Use dtype=str for stability; some columns contain JSON strings.
    df = pd.read_csv(path, dtype=str, low_memory=False)
    return df


def parse_props_json_cell(cell: Any) -> Dict[str, Any]:
    """
    nodes_merged.csv uses a nested structure:
      props_json = {"props": "<json-string>" , ...}
    We try to unwrap safely.
    """
    outer = safe_json_loads(cell)
    if isinstance(outer, dict):
        if "props" in outer and isinstance(outer["props"], str):
            inner = safe_json_loads(outer["props"])
            if isinstance(inner, dict):
                # merge outer metadata but keep inner under 'props'
                out = dict(outer)
                out["props"] = inner
                return out
        return outer
    return {}


def node_type_from_row(kind: str, labels: List[str], name: str) -> str:
    k = (kind or "").strip().lower()

    # Prefer explicit label signals
    if "Authority" in labels or k in {"authority", "benchbook", "statute", "canon"}:
        return "Authority"
    if k == "authority_hub":
        return "AuthorityHub"
    if k == "violation":
        return "Violation"
    if k == "remedy":
        return "Remedy"
    if k == "defense":
        return "Defense"
    if k == "element":
        return "Element"
    if k == "complaint":
        return "Complaint"
    if k == "fact":
        return "Fact"
    if k == "module":
        return "Module"

    # fallback by name heuristics
    n = (name or "").upper()
    if n.startswith("MCR ") or n.startswith("MCL ") or n.startswith("MRE "):
        return "Authority"
    return "Node"


def build_nodes_from_df(df: pd.DataFrame, source_tag: str) -> List[Node]:
    nodes: List[Node] = []
    if df.empty:
        return nodes

    cols = set(df.columns)
    # required columns expected: :ID, :LABEL, kind, name, props_json, tags, tokens
    for _, r in df.iterrows():
        uid = str(r.get(":ID") or r.get("id") or "").strip()
        if not uid:
            continue

        labels = normalize_labels(r.get(":LABEL"))
        kind = (r.get("kind") or "").strip()
        name = (r.get("name") or r.get("label") or "").strip()
        props_json = parse_props_json_cell(r.get("props_json"))

        props: Dict[str, Any] = {
            "source": source_tag,
            "id": (r.get("id") or uid),
            "name": name,
            "kind": kind,
            "group": (r.get("group") or ""),
            "eff_date": (r.get("eff_date") or ""),
            "prefix": (r.get("prefix") or ""),
            "tags_raw": (r.get("tags") or ""),
            "tokens_raw": (r.get("tokens") or ""),
        }
        if props_json:
            props["props_json"] = props_json

        nt = node_type_from_row(kind, labels, name)

        # ensure node_type label is present for Neo4j import convenience
        if nt not in labels:
            labels2 = labels + [nt]
        else:
            labels2 = labels

        nodes.append(Node(uid=uid, node_type=nt, labels=sorted(set(labels2)), props=props))

    # Deterministic sort
    nodes.sort(key=lambda n: (n.node_type, n.uid))
    return nodes


def load_contradiction_map(paths: List[Path]) -> pd.DataFrame:
    dfs = []
    for p in paths:
        if p.exists():
            dfs.append(pd.read_csv(p, dtype=str, low_memory=False))
    if not dfs:
        return pd.DataFrame(columns=["cm_id", "type", "description", "src_id", "pin", "status", "notes"])
    df = pd.concat(dfs, ignore_index=True)
    # Deduplicate exact row duplicates (your uploaded 3 copies are identical)
    df = df.drop_duplicates()
    # Stable ordering
    if "cm_id" in df.columns:
        df = df.sort_values(["cm_id"], kind="mergesort")
    return df


# ---------------------------
# Graph assembly
# ---------------------------

def make_contradiction_nodes_and_edges(cm: pd.DataFrame) -> Tuple[List[Node], List[Edge]]:
    nodes: List[Node] = []
    edges: List[Edge] = []
    if cm.empty:
        return nodes, edges

    # Create a SourceRef-like node for each src_id
    src_ids = sorted(set([str(x).strip() for x in cm.get("src_id", pd.Series(dtype=str)).fillna("").tolist() if str(x).strip()]))
    for sid in src_ids:
        uid = f"SourceRef:{sid}"
        nodes.append(Node(uid=uid, node_type="SourceRef", labels=["SourceRef"], props={"src_id": sid}))

    for _, r in cm.iterrows():
        cm_id = str(r.get("cm_id") or "").strip()
        if not cm_id:
            continue
        c_uid = f"Contradiction:{cm_id}"
        nprops = {
            "cm_id": cm_id,
            "type": (r.get("type") or ""),
            "description": (r.get("description") or ""),
            "src_id": (r.get("src_id") or ""),
            "pin": (r.get("pin") or ""),
            "status": (r.get("status") or ""),
            "notes": (r.get("notes") or ""),
        }
        nodes.append(Node(uid=c_uid, node_type="ContradictionItem", labels=["ContradictionItem"], props=nprops))

        # Link to SourceRef node
        sid = str(r.get("src_id") or "").strip()
        if sid:
            euid = f"Edge:{stable_hash_id('CONTRADICTION_FROM', c_uid, sid)}"
            edges.append(Edge(uid=euid, rel_type="CONTRADICTION_FROM_SOURCE", from_uid=c_uid, to_uid=f"SourceRef:{sid}", props={"pin": nprops["pin"]}))

        # Extract exhibit name (if present)
        desc = nprops["description"]
        m = re.match(r"^\s*(Exhibit\s+[A-Z0-9\-]+)\s*—\s*(.+?)\s*(?:\[|$)", desc, flags=re.IGNORECASE)
        if m:
            exhibit_id = m.group(1).strip()
            ex_uid = f"Exhibit:{exhibit_id}"
            nodes.append(Node(uid=ex_uid, node_type="ExhibitPlaceholder", labels=["ExhibitPlaceholder", "Exhibit"], props={"exhibit_id": exhibit_id, "title": m.group(2).strip()}))
            euid2 = f"Edge:{stable_hash_id('NEEDS_EXHIBIT', c_uid, ex_uid)}"
            edges.append(Edge(uid=euid2, rel_type="NEEDS_EXHIBIT", from_uid=c_uid, to_uid=ex_uid, props={"status": nprops["status"]}))
        else:
            # still create a procedural remedy node: AcquireEvidence
            pass

        # Always create a procedural remedy suggestion node (not a legal remedy)
        remedy_uid = f"ProcRemedy:Acquire:{cm_id}"
        nodes.append(Node(uid=remedy_uid, node_type="ProceduralRemedy", labels=["ProceduralRemedy", "Remedy"], props={
            "remedy_kind": "acquire_and_ingest_exhibit",
            "cm_id": cm_id
        }))
        edges.append(Edge(
            uid=f"Edge:{stable_hash_id('REMEDY_FOR', c_uid, remedy_uid)}",
            rel_type="REMEDY_FOR_GAP",
            from_uid=c_uid,
            to_uid=remedy_uid,
            props={}
        ))

    # Deduplicate nodes by uid (keep first)
    seen = set()
    uniq_nodes = []
    for n in nodes:
        if n.uid not in seen:
            seen.add(n.uid)
            uniq_nodes.append(n)
    uniq_nodes.sort(key=lambda n: (n.node_type, n.uid))

    # Deduplicate edges by uid
    eseen = set()
    uniq_edges = []
    for e in edges:
        if e.uid not in eseen:
            eseen.add(e.uid)
            uniq_edges.append(e)
    uniq_edges.sort(key=lambda e: (e.rel_type, e.from_uid, e.to_uid, e.uid))
    return uniq_nodes, uniq_edges


def keyword_match_candidates(
    nodes: List[Node],
    query: str,
    allowed_node_types: Optional[set] = None,
    max_hits: int = 10
) -> List[Tuple[Node, float, str]]:
    """
    Heuristic candidate matching against node name/tokens.
    Returns [(node, score, why)] sorted desc by score.
    """
    q = (query or "").strip()
    if not q:
        return []
    q_terms = [t for t in re.split(r"[\s\W]+", q.lower()) if t]
    if not q_terms:
        return []

    hits = []
    for n in nodes:
        if allowed_node_types and n.node_type not in allowed_node_types:
            continue
        name = str(n.props.get("name") or "")
        tokens = str(n.props.get("tokens_raw") or "")
        blob = (name + " " + tokens).lower()
        if not blob:
            continue
        match_count = sum(1 for t in q_terms if t in blob)
        if match_count <= 0:
            continue
        score = clamp01(match_count / max(3, len(q_terms)))
        why = f"matched_terms={match_count}/{len(q_terms)}"
        hits.append((n, score, why))

    hits.sort(key=lambda x: (-x[1], x[0].node_type, x[0].uid))
    return hits[:max_hits]


def build_action_report(
    out_path: Path,
    cm: pd.DataFrame,
    base_nodes: List[Node],
    contradiction_nodes: List[Node],
    contradiction_edges: List[Edge]
) -> None:
    """
    Produces a DRAFT action report:
    gap/violation -> procedural remedy -> candidate vehicle -> candidate authority/caselaw -> next action
    All non-explicit links labeled as CANDIDATE/HEURISTIC.
    """
    lines: List[str] = []
    lines.append(f"# LitigationOS Action Report (DRAFT) — {iso_now()}")
    lines.append("")
    lines.append("This report is generated from uploaded attachments. It does not invent facts. Any linkage beyond explicit data is labeled **CANDIDATE/HEURISTIC**.")
    lines.append("")

    # Summary
    if cm.empty:
        lines.append("## Summary")
        lines.append("- No CONTRADICTION_MAP*.csv found or it contained no rows.")
        out_path.write_text("\n".join(lines), encoding="utf-8")
        return

    total = len(cm)
    open_ct = int((cm.get("status", pd.Series(dtype=str)).fillna("") == "OPEN").sum())
    lines.append("## Summary")
    lines.append(f"- Contradiction items: **{total}**")
    lines.append(f"- Status OPEN: **{open_ct}**")
    lines.append("")

    # Group by src_id
    lines.append("## Contradiction / Gap Queue (grouped by src_id)")
    for sid, g in cm.groupby(cm["src_id"].fillna(""), sort=True):
        sid = str(sid).strip() or "(missing src_id)"
        lines.append(f"### {sid}")
        for _, r in g.iterrows():
            cm_id = str(r.get("cm_id") or "").strip()
            desc = str(r.get("description") or "").strip()
            pin = str(r.get("pin") or "").strip()
            status = str(r.get("status") or "").strip()
            lines.append(f"- **{cm_id}** [{status}] — {desc}")
            if pin:
                lines.append(f"  - pin: `{pin}`")

            # Candidate vehicle/authority matching (heuristic)
            # Use description as query; focus on Vehicle/Authority node types if present in base_nodes.
            veh_hits = keyword_match_candidates(base_nodes, desc, allowed_node_types={"Vehicle", "Complaint", "Defense", "Remedy"}, max_hits=5)
            auth_hits = keyword_match_candidates(base_nodes, desc, allowed_node_types={"Authority", "AuthorityHub"}, max_hits=8)

            if veh_hits:
                lines.append("  - CANDIDATE vehicles/remedy nodes (heuristic match):")
                for n, sc, why in veh_hits:
                    lines.append(f"    - ({sc:.2f}) {n.node_type} `{n.uid}` name=`{n.props.get('name','')}` [{why}]")

            if auth_hits:
                lines.append("  - CANDIDATE authorities/caselaw hubs (heuristic match):")
                for n, sc, why in auth_hits:
                    lines.append(f"    - ({sc:.2f}) {n.node_type} `{n.uid}` name=`{n.props.get('name','')}` [{why}]")

            lines.append("  - Recommended procedural action (non-legal remedy): Acquire the referenced exhibit/document, ingest, attach provenance, then re-run compiler to close this gap.")
        lines.append("")

    lines.append("## Notes")
    lines.append("- Two exhibit binders appear to be scan/image heavy; this runtime does not OCR by default. Add OCR stage if you want QuoteAtom extraction from those PDFs.")
    lines.append("- If you want strict Michigan-only authority routing, tag non-MI authorities (e.g., FRE/MRPC) as overlay and exclude them from vehicle scoring.")
    out_path.write_text("\n".join(lines), encoding="utf-8")


# ---------------------------
# Validation
# ---------------------------

def validate_graph(nodes: List[Node], edges: List[Edge]) -> Dict[str, Any]:
    violations: Dict[str, Any] = {"errors": [], "warnings": [], "stats": {}}

    node_ids = [n.uid for n in nodes]
    edge_ids = [e.uid for e in edges]

    # Uniqueness
    dup_nodes = sorted({x for x in node_ids if node_ids.count(x) > 1})
    if dup_nodes:
        violations["errors"].append({"code": "DUP_NODE_UID", "count": len(dup_nodes), "sample": dup_nodes[:10]})

    dup_edges = sorted({x for x in edge_ids if edge_ids.count(x) > 1})
    if dup_edges:
        violations["errors"].append({"code": "DUP_EDGE_UID", "count": len(dup_edges), "sample": dup_edges[:10]})

    node_set = set(node_ids)
    bad_from = [e.uid for e in edges if e.from_uid not in node_set]
    bad_to = [e.uid for e in edges if e.to_uid not in node_set]
    if bad_from:
        violations["errors"].append({"code": "EDGE_FROM_MISSING", "count": len(bad_from), "sample": bad_from[:10]})
    if bad_to:
        violations["errors"].append({"code": "EDGE_TO_MISSING", "count": len(bad_to), "sample": bad_to[:10]})

    # Basic uid pattern
    pat = re.compile(r"^[A-Za-z0-9_.:\-]{3,128}$")
    bad_uid = [n.uid for n in nodes if not pat.match(n.uid)]
    if bad_uid:
        violations["warnings"].append({"code": "UID_PATTERN_WARN", "count": len(bad_uid), "sample": bad_uid[:10]})

    # Stats
    by_type = {}
    for n in nodes:
        by_type[n.node_type] = by_type.get(n.node_type, 0) + 1
    by_rel = {}
    for e in edges:
        by_rel[e.rel_type] = by_rel.get(e.rel_type, 0) + 1

    violations["stats"] = {"nodes": len(nodes), "edges": len(edges), "node_types": by_type, "rel_types": by_rel}
    return violations


# ---------------------------
# Writers
# ---------------------------

def write_nodes_csv(path: Path, nodes: List[Node]) -> None:
    ensure_dir(path.parent)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["uid:ID", "node_type", "labels:LABEL", "props_json"])
        for n in nodes:
            w.writerow([n.uid, n.node_type, ";".join(n.labels), json.dumps(n.props, ensure_ascii=False, sort_keys=True)])


def write_edges_csv(path: Path, edges: List[Edge]) -> None:
    ensure_dir(path.parent)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["uid", "from_uid:START_ID", "to_uid:END_ID", "rel_type:TYPE", "props_json"])
        for e in edges:
            w.writerow([e.uid, e.from_uid, e.to_uid, e.rel_type, json.dumps(e.props, ensure_ascii=False, sort_keys=True)])


def write_graphml(path: Path, nodes: List[Node], edges: List[Edge]) -> None:
    if nx is None:
        return
    ensure_dir(path.parent)
    G = nx.MultiDiGraph()
    for n in nodes:
        G.add_node(n.uid, node_type=n.node_type, labels=";".join(n.labels), props_json=json.dumps(n.props, ensure_ascii=False, sort_keys=True))
    for e in edges:
        G.add_edge(e.from_uid, e.to_uid, key=e.uid, uid=e.uid, rel_type=e.rel_type, props_json=json.dumps(e.props, ensure_ascii=False, sort_keys=True))
    nx.write_graphml(G, path)


# ---------------------------
# Main
# ---------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description="LitigationOS Compiler Runtime (attachments -> graph exports + action report)")
    ap.add_argument("--in-dir", default=str(Path.cwd()), help="Directory containing uploaded artifacts (default: current dir)")
    ap.add_argument("--out-dir", default="out", help="Output directory (relative to in-dir unless absolute)")
    ap.add_argument("--nodes-merged", default="nodes_merged.csv", help="Primary node CSV filename")
    ap.add_argument("--nodes-neo4j-admin", default="nodes_neo4j_admin.csv", help="Secondary node CSV filename (optional)")
    ap.add_argument("--contradiction-glob", default="CONTRADICTION_MAP*.csv", help="Glob for contradiction map CSVs")
    ap.add_argument("--emit-graphml", action="store_true", help="Emit graph.graphml (requires networkx)")
    args = ap.parse_args()

    in_dir = Path(args.in_dir).resolve()
    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = in_dir / out_dir

    ensure_dir(out_dir)

    # Load node sources
    nm = load_nodes_csv(in_dir / args.nodes_merged)
    na = load_nodes_csv(in_dir / args.nodes_neo4j_admin)

    base_nodes: List[Node] = []
    if not nm.empty:
        base_nodes.extend(build_nodes_from_df(nm, source_tag="nodes_merged.csv"))
    if not na.empty:
        base_nodes.extend(build_nodes_from_df(na, source_tag="nodes_neo4j_admin.csv"))

    # Deduplicate by uid across sources (prefer first occurrence = nodes_merged)
    seen = set()
    dedup_nodes: List[Node] = []
    for n in base_nodes:
        if n.uid in seen:
            continue
        seen.add(n.uid)
        dedup_nodes.append(n)
    dedup_nodes.sort(key=lambda n: (n.node_type, n.uid))

    # Load contradiction map(s)
    cm_paths = sorted(in_dir.glob(args.contradiction_glob))
    cm = load_contradiction_map(cm_paths)

    c_nodes, c_edges = make_contradiction_nodes_and_edges(cm)

    # Combine into graph
    all_nodes = dedup_nodes + c_nodes
    # re-dedupe after adding contradiction nodes
    seen2 = set()
    all_nodes2 = []
    for n in all_nodes:
        if n.uid in seen2:
            continue
        seen2.add(n.uid)
        all_nodes2.append(n)
    all_nodes2.sort(key=lambda n: (n.node_type, n.uid))

    all_edges = c_edges  # base node CSVs do not include edges in your attachments

    # Validate
    violations = validate_graph(all_nodes2, all_edges)

    # Write outputs
    nodes_out = out_dir / "neo4j_nodes.csv"
    edges_out = out_dir / "neo4j_edges.csv"
    graphml_out = out_dir / "graph.graphml"
    viol_out = out_dir / "violations.json"
    report_out = out_dir / "action_report.md"

    write_nodes_csv(nodes_out, all_nodes2)
    write_edges_csv(edges_out, all_edges)
    if args.emit_graphml:
        if nx is None:
            print("[WARN] networkx not available; skipping graphml.", file=sys.stderr)
        else:
            write_graphml(graphml_out, all_nodes2, all_edges)

    viol_out.write_text(json.dumps(violations, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    build_action_report(report_out, cm, all_nodes2, c_nodes, c_edges)

    # Status
    err_ct = len(violations.get("errors", []))
    if err_ct:
        print(f"[DONE] status=warn_or_fail errors={err_ct} out={out_dir}")
        return 1
    print(f"[DONE] status=ok out={out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
