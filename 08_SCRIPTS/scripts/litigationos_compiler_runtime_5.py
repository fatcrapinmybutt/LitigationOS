\
#!/usr/bin/env python3
"""
LitigationOS Compiler Runtime v1.1.0

Adds:
- OCR ingestion for PDF exhibit binders (fail-soft)
- Authority resolution (MCR/MCL/MRE citations -> Authority nodes)
- Bloom query pack generation
- EXE packaging scripts included in bundle

Inputs (in-dir):
- nodes_merged.csv
- nodes_neo4j_admin.csv (optional, recommended)
- CONTRADICTION_MAP*.csv
- PDFs (*.pdf) optional: OCR/extract text for QuoteAtoms + citation extraction
- 555.txt optional: treated as text corpus for citation extraction (no quoting guarantees)

Outputs (out-dir):
- neo4j_nodes.csv
- neo4j_edges.csv
- graph.graphml (optional)
- violations.json
- action_report.md
- bloom_queries.cypher
- bloom_perspective_litigationos.json
- ocr/ (page images) + ocr_text.json (when OCR runs)
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

try:
    import networkx as nx
except Exception:
    nx = None

from graph_io import Node, Edge, write_nodes_csv, write_edges_csv
from ocr_ingest import extract_pdf_text_and_optional_ocr, build_quote_atoms_from_pages
from authority_resolver import extract_citations, build_authority_index, resolve_citation
from bloom_generator import write_bloom_queries, write_perspective_json


VERSION = "1.1.0"


def iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def stable_id(*parts: str) -> str:
    h = hashlib.sha1("||".join(parts).encode("utf-8")).hexdigest()
    return h[:24]


def normalize_labels(label_cell: Any) -> List[str]:
    if label_cell is None or (isinstance(label_cell, float) and pd.isna(label_cell)):
        return []
    s = str(label_cell).strip()
    if not s:
        return []
    return [p.strip() for p in s.split(";") if p.strip()]


def safe_json_loads(s: Any) -> Any:
    if s is None or (isinstance(s, float) and pd.isna(s)):
        return None
    if isinstance(s, (dict, list)):
        return s
    if not isinstance(s, str):
        return None
    t = s.strip()
    if not t:
        return None
    try:
        return json.loads(t)
    except Exception:
        return None


def parse_props_json_cell(cell: Any) -> Dict[str, Any]:
    outer = safe_json_loads(cell)
    if isinstance(outer, dict):
        if "props" in outer and isinstance(outer["props"], str):
            inner = safe_json_loads(outer["props"])
            if isinstance(inner, dict):
                out = dict(outer)
                out["props"] = inner
                return out
        return outer
    return {}


def load_nodes_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, dtype=str, low_memory=False)


def node_type_from_row(kind: str, labels: List[str], name: str) -> str:
    k = (kind or "").strip().lower()
    if "Authority" in labels or k in {"authority", "benchbook", "statute", "canon", "caselaw"}:
        return "Authority"
    if k == "authority_hub":
        return "AuthorityHub"
    if k in {"vehicle"}:
        return "Vehicle"
    if k == "violation":
        return "Violation"
    if k == "harm":
        return "Harm"
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

    n = (name or "").upper()
    if n.startswith("MCR ") or n.startswith("MCL ") or n.startswith("MRE "):
        return "Authority"
    return "Node"


def build_nodes_from_df(df: pd.DataFrame, source_tag: str) -> List[Node]:
    out: List[Node] = []
    if df.empty:
        return out
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
        labels2 = sorted(set(labels + ([nt] if nt not in labels else [])))
        out.append(Node(uid=uid, node_type=nt, labels=labels2, props=props))
    out.sort(key=lambda n: (n.node_type, n.uid))
    return out


def load_contradiction_map(paths: List[Path]) -> pd.DataFrame:
    dfs = []
    for p in paths:
        if p.exists():
            dfs.append(pd.read_csv(p, dtype=str, low_memory=False))
    if not dfs:
        return pd.DataFrame(columns=["cm_id", "type", "description", "src_id", "pin", "status", "notes"])
    df = pd.concat(dfs, ignore_index=True).drop_duplicates()
    if "cm_id" in df.columns:
        df = df.sort_values(["cm_id"], kind="mergesort")
    return df


def make_contradiction_graph(cm: pd.DataFrame) -> Tuple[List[Node], List[Edge]]:
    nodes: List[Node] = []
    edges: List[Edge] = []
    if cm.empty:
        return nodes, edges

    src_ids = sorted(set([str(x).strip() for x in cm.get("src_id", pd.Series(dtype=str)).fillna("").tolist() if str(x).strip()]))
    for sid in src_ids:
        nodes.append(Node(uid=f"SourceRef:{sid}", node_type="SourceRef", labels=["SourceRef"], props={"src_id": sid}))

    for _, r in cm.iterrows():
        cm_id = str(r.get("cm_id") or "").strip()
        if not cm_id:
            continue
        c_uid = f"Contradiction:{cm_id}"
        props = {
            "cm_id": cm_id,
            "type": (r.get("type") or ""),
            "description": (r.get("description") or ""),
            "src_id": (r.get("src_id") or ""),
            "pin": (r.get("pin") or ""),
            "status": (r.get("status") or ""),
            "notes": (r.get("notes") or ""),
        }
        nodes.append(Node(uid=c_uid, node_type="ContradictionItem", labels=["ContradictionItem"], props=props))

        sid = str(r.get("src_id") or "").strip()
        if sid:
            edges.append(Edge(
                uid=f"Edge:{stable_id('CONTRAD_FROM', c_uid, sid)}",
                rel_type="CONTRADICTION_FROM_SOURCE",
                from_uid=c_uid,
                to_uid=f"SourceRef:{sid}",
                props={"pin": props["pin"]}
            ))

        # Heuristic: create a HarmCandidate node tied to contradiction description
        harm_uid = f"HarmCand:{stable_id('HARM', cm_id)}"
        nodes.append(Node(uid=harm_uid, node_type="HarmCandidate", labels=["HarmCandidate","Harm"], props={
            "cm_id": cm_id,
            "basis": "heuristic_from_contradiction_description",
            "text": props["description"]
        }))
        edges.append(Edge(
            uid=f"Edge:{stable_id('HARM_OF', c_uid, harm_uid)}",
            rel_type="GAP_IMPLICATES_HARM_CANDIDATE",
            from_uid=c_uid,
            to_uid=harm_uid,
            props={}
        ))

        # Procedural remedy node (acquisition)
        rem_uid = f"ProcRemedy:Acquire:{cm_id}"
        nodes.append(Node(uid=rem_uid, node_type="ProceduralRemedy", labels=["ProceduralRemedy","Remedy"], props={
            "cm_id": cm_id,
            "remedy_kind": "acquire_and_ingest_exhibit"
        }))
        edges.append(Edge(
            uid=f"Edge:{stable_id('REMEDY_FOR', c_uid, rem_uid)}",
            rel_type="REMEDY_FOR_GAP",
            from_uid=c_uid,
            to_uid=rem_uid,
            props={}
        ))

        # Exhibit placeholder parse (optional)
        desc = props["description"]
        m = re.match(r"^\s*(Exhibit\s+[A-Z0-9\-]+)\s*—\s*(.+?)\s*(?:\[|$)", desc, flags=re.IGNORECASE)
        if m:
            ex_id = m.group(1).strip()
            ex_uid = f"Exhibit:{ex_id}"
            nodes.append(Node(uid=ex_uid, node_type="ExhibitPlaceholder", labels=["ExhibitPlaceholder","Exhibit"], props={
                "exhibit_id": ex_id, "title": m.group(2).strip()
            }))
            edges.append(Edge(
                uid=f"Edge:{stable_id('NEEDS_EX', c_uid, ex_uid)}",
                rel_type="NEEDS_EXHIBIT",
                from_uid=c_uid,
                to_uid=ex_uid,
                props={"status": props["status"]}
            ))

    # dedupe nodes
    seen = set()
    nn = []
    for n in nodes:
        if n.uid in seen:
            continue
        seen.add(n.uid)
        nn.append(n)
    nn.sort(key=lambda n: (n.node_type, n.uid))

    eseen = set()
    ee = []
    for e in edges:
        if e.uid in eseen:
            continue
        eseen.add(e.uid)
        ee.append(e)
    ee.sort(key=lambda e: (e.rel_type, e.from_uid, e.to_uid, e.uid))
    return nn, ee


def build_authority_nodes_list(nodes: List[Node]) -> List[Dict[str, Any]]:
    out = []
    for n in nodes:
        if n.node_type in {"Authority","AuthorityHub"} or "Authority" in n.labels:
            out.append({"uid": n.uid, "name": n.props.get("name",""), "props": n.props})
    return out


def add_citation_edges(
    nodes: List[Node],
    edges: List[Edge],
    authority_index,
    citing_nodes: List[Tuple[str, str]]  # (node_uid, text)
) -> List[Edge]:
    new_edges: List[Edge] = []
    for node_uid, text in citing_nodes:
        cites = extract_citations(text)
        for cite in cites:
            uid_exact, uid_fuzzy, mode = resolve_citation(authority_index, cite, fuzzy_cutoff=90)
            if mode == "exact" and uid_exact:
                new_edges.append(Edge(
                    uid=f"Edge:{stable_id('CITES', node_uid, uid_exact, cite)}",
                    rel_type="CITES_AUTHORITY",
                    from_uid=node_uid,
                    to_uid=uid_exact,
                    props={"citation": cite, "mode": "exact"}
                ))
            elif mode == "fuzzy" and uid_fuzzy:
                new_edges.append(Edge(
                    uid=f"Edge:{stable_id('CITES_CAND', node_uid, uid_fuzzy, cite)}",
                    rel_type="CITES_AUTHORITY_CANDIDATE",
                    from_uid=node_uid,
                    to_uid=uid_fuzzy,
                    props={"citation": cite, "mode": "fuzzy"}
                ))
            else:
                # unresolved -> emit a citation stub node so nothing is lost
                stub_uid = f"AuthorityCiteStub:{cite}"
                # node creation handled upstream (we return edges only here)
                new_edges.append(Edge(
                    uid=f"Edge:{stable_id('CITE_STUB', node_uid, stub_uid, cite)}",
                    rel_type="CITES_AUTHORITY_UNRESOLVED",
                    from_uid=node_uid,
                    to_uid=stub_uid,
                    props={"citation": cite, "mode": "unresolved"}
                ))
    # dedupe
    es = set(e.uid for e in edges)
    out = []
    for e in new_edges:
        if e.uid in es:
            continue
        es.add(e.uid)
        out.append(e)
    out.sort(key=lambda e: (e.rel_type, e.from_uid, e.to_uid, e.uid))
    return out


def write_graphml(path: Path, nodes: List[Node], edges: List[Edge]) -> None:
    if nx is None:
        return
    G = nx.MultiDiGraph()
    for n in nodes:
        G.add_node(n.uid, node_type=n.node_type, labels=";".join(n.labels), props_json=json.dumps(n.props, ensure_ascii=False, sort_keys=True))
    for e in edges:
        G.add_edge(e.from_uid, e.to_uid, key=e.uid, uid=e.uid, rel_type=e.rel_type, props_json=json.dumps(e.props, ensure_ascii=False, sort_keys=True))
    nx.write_graphml(G, path)


def validate_graph(nodes: List[Node], edges: List[Edge]) -> Dict[str, Any]:
    out = {"errors": [], "warnings": [], "stats": {}}
    node_uids = [n.uid for n in nodes]
    edge_uids = [e.uid for e in edges]
    # uniqueness
    if len(node_uids) != len(set(node_uids)):
        out["errors"].append({"code":"DUP_NODE_UID"})
    if len(edge_uids) != len(set(edge_uids)):
        out["errors"].append({"code":"DUP_EDGE_UID"})
    ns = set(node_uids)
    bad_from = [e.uid for e in edges if e.from_uid not in ns]
    bad_to = [e.uid for e in edges if e.to_uid not in ns]
    if bad_from:
        out["errors"].append({"code":"EDGE_FROM_MISSING","count":len(bad_from),"sample":bad_from[:10]})
    if bad_to:
        out["errors"].append({"code":"EDGE_TO_MISSING","count":len(bad_to),"sample":bad_to[:10]})

    by_type = {}
    for n in nodes:
        by_type[n.node_type] = by_type.get(n.node_type, 0) + 1
    by_rel = {}
    for e in edges:
        by_rel[e.rel_type] = by_rel.get(e.rel_type, 0) + 1

    out["stats"] = {"nodes": len(nodes), "edges": len(edges), "node_types": by_type, "rel_types": by_rel}
    return out


def build_action_report(path: Path, cm: pd.DataFrame) -> None:
    # Deterministic, evidence-light: do not assert legal harm; only label as candidate.
    lines = []
    lines.append(f"# Action Report (DRAFT) — {iso_now()}")
    lines.append("")
    lines.append("This report chains: gap/violation -> harm candidate -> procedural remedy -> vehicle candidates -> authority candidates -> action.")
    lines.append("All legal mappings are **CANDIDATE/HEURISTIC** unless explicitly grounded in your authority registry.")
    lines.append("")
    if cm.empty:
        lines.append("No contradiction map rows found.")
        path.write_text("\n".join(lines), encoding="utf-8")
        return

    lines.append(f"Contradiction items: {len(cm)}")
    lines.append("")
    for _, r in cm.iterrows():
        cm_id = str(r.get("cm_id") or "").strip()
        desc = str(r.get("description") or "").strip()
        sid = str(r.get("src_id") or "").strip()
        pin = str(r.get("pin") or "").strip()
        status = str(r.get("status") or "").strip()
        lines.append(f"## {cm_id} [{status}]")
        if desc:
            lines.append(f"- Gap/issue: {desc}")
        if sid:
            lines.append(f"- SourceRef: {sid}")
        if pin:
            lines.append(f"- Pin: `{pin}`")
        lines.append("- Harm candidate: derived from gap text (not a finding).")
        lines.append("- Remedy: acquire + ingest missing exhibit; rerun compiler.")
        lines.append("- Vehicle: candidate vehicles will appear in graph via nodes_merged taxonomy and future authority->vehicle mapping.")
        lines.append("- Authority/Caselaw: citations extracted from binder OCR + corpus text and resolved to Authority index.")
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in-dir", default=str(Path.cwd()))
    ap.add_argument("--out-dir", default="out")
    ap.add_argument("--nodes-merged", default="nodes_merged.csv")
    ap.add_argument("--nodes-neo4j-admin", default="nodes_neo4j_admin.csv")
    ap.add_argument("--contradiction-glob", default="CONTRADICTION_MAP*.csv")
    ap.add_argument("--emit-graphml", action="store_true")
    ap.add_argument("--ocr-mode", default="auto", choices=["off","auto","on"])
    ap.add_argument("--ocr-dpi", type=int, default=200)
    ap.add_argument("--ocr-lang", default="eng")
    args = ap.parse_args()

    in_dir = Path(args.in_dir).resolve()
    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = in_dir / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1) Base nodes
    nm = load_nodes_csv(in_dir / args.nodes_merged)
    na = load_nodes_csv(in_dir / args.nodes_neo4j_admin)

    base_nodes: List[Node] = []
    if not nm.empty:
        base_nodes.extend(build_nodes_from_df(nm, "nodes_merged.csv"))
    if not na.empty:
        base_nodes.extend(build_nodes_from_df(na, "nodes_neo4j_admin.csv"))

    # Dedup by uid (prefer earlier = nodes_merged)
    seen = set()
    nodes: List[Node] = []
    for n in base_nodes:
        if n.uid in seen:
            continue
        seen.add(n.uid)
        nodes.append(n)
    nodes.sort(key=lambda n: (n.node_type, n.uid))

    edges: List[Edge] = []

    # 2) Contradiction graph
    cm_paths = sorted(in_dir.glob(args.contradiction_glob))
    cm = load_contradiction_map(cm_paths)
    c_nodes, c_edges = make_contradiction_graph(cm)

    # Add c_nodes
    seen2 = set(n.uid for n in nodes)
    for n in c_nodes:
        if n.uid in seen2:
            continue
        nodes.append(n)
        seen2.add(n.uid)
    nodes.sort(key=lambda n: (n.node_type, n.uid))
    edges.extend(c_edges)

    # 3) OCR/extract PDFs into QuoteAtoms (optional)
    pdfs = sorted(in_dir.glob("*.pdf"))
    ocr_payload = {"pdfs": []}
    quote_nodes: List[Node] = []
    citing_texts: List[Tuple[str, str]] = []

    if pdfs:
        ocr_dir = out_dir / "ocr"
        ocr_dir.mkdir(exist_ok=True)
        for pdf in pdfs:
            try:
                payload = extract_pdf_text_and_optional_ocr(
                    pdf, ocr_dir,
                    ocr_mode=args.ocr_mode,
                    dpi=args.ocr_dpi,
                    lang=args.ocr_lang
                )
                ocr_payload["pdfs"].append(payload)
                # Create QuoteAtom nodes per page (fail-soft)
                q_atoms = build_quote_atoms_from_pages(
                    pdf_path=pdf,
                    pages_payload=payload,
                    bundle_uid="BUNDLE:IN_DIR",
                    entry_path=str(pdf.name)
                )
                for qa in q_atoms:
                    q_uid = qa["quote_id"]
                    text = qa["text"]
                    quote_nodes.append(Node(uid=q_uid, node_type="QuoteAtom", labels=["QuoteAtom"], props={
                        "quote_id": q_uid,
                        "text": text,
                        "provenance": qa.get("provenance", {}),
                        "created_at": iso_now()
                    }))
                    citing_texts.append((q_uid, text))
            except Exception as ex:
                # fail-soft: record in payload
                ocr_payload["pdfs"].append({"pdf": str(pdf), "error": str(ex)})

        (out_dir / "ocr_text.json").write_text(json.dumps(ocr_payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    # Add quote nodes
    for qn in quote_nodes:
        if qn.uid in seen2:
            continue
        nodes.append(qn)
        seen2.add(qn.uid)
    nodes.sort(key=lambda n: (n.node_type, n.uid))

    # 4) Ingest 555.txt as corpus text (optional) for citation extraction only
    txt = in_dir / "555.txt"
    if txt.exists():
        try:
            t = txt.read_text(encoding="utf-8", errors="ignore")
            corp_uid = "Corpus:555"
            if corp_uid not in seen2:
                nodes.append(Node(uid=corp_uid, node_type="Corpus", labels=["Corpus"], props={"path": str(txt.name)}))
                seen2.add(corp_uid)
            citing_texts.append((corp_uid, t[:500000]))  # cap for runtime safety
        except Exception:
            pass

    # 5) Authority resolution: build authority index from existing nodes
    auth_nodes_raw = build_authority_nodes_list(nodes)
    auth_index = build_authority_index(auth_nodes_raw)

    # Add unresolved citation stub nodes as needed
    citation_stub_nodes: List[Node] = []
    citation_edges = add_citation_edges(nodes, edges, auth_index, citing_texts)
    edges.extend(citation_edges)

    # Create stub nodes for unresolved citations referenced by edges
    existing = set(n.uid for n in nodes)
    for e in citation_edges:
        if e.rel_type == "CITES_AUTHORITY_UNRESOLVED" and e.to_uid not in existing:
            citation_stub_nodes.append(Node(uid=e.to_uid, node_type="AuthorityCiteStub", labels=["AuthorityCiteStub","Authority"], props={"citation": e.props.get("citation","")}))
            existing.add(e.to_uid)

    nodes.extend(citation_stub_nodes)
    nodes.sort(key=lambda n: (n.node_type, n.uid))
    edges.sort(key=lambda e: (e.rel_type, e.from_uid, e.to_uid, e.uid))

    # 6) Validate and emit
    violations = validate_graph(nodes, edges)

    # Core exports
    write_nodes_csv(out_dir / "neo4j_nodes.csv", nodes)
    write_edges_csv(out_dir / "neo4j_edges.csv", edges)

    if args.emit_graphml:
        if nx is not None:
            write_graphml(out_dir / "graph.graphml", nodes, edges)

    (out_dir / "violations.json").write_text(json.dumps(violations, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    build_action_report(out_dir / "action_report.md", cm)

    # Bloom artifacts
    write_bloom_queries(out_dir / "bloom_queries.cypher")
    write_perspective_json(out_dir / "bloom_perspective_litigationos.json",
                           node_types=violations["stats"]["node_types"],
                           rel_types=violations["stats"]["rel_types"])

    # Exit status: fail only if hard errors present
    if violations.get("errors"):
        print(f"[DONE] status=warn_or_fail errors={len(violations['errors'])} out={out_dir}")
        return 1

    print(f"[DONE] status=ok out={out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
