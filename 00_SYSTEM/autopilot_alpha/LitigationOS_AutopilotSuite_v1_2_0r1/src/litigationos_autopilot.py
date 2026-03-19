#!/usr/bin/env python3
from __future__ import annotations

"""
LitigationOS Autopilot Compiler v1.2.0r1

Implements:
- Authority resolution (exact/fuzzy + stubs) from authority corpus
- AUTHORITY_SUPPORTS_VEHICLE edges (corpus-driven when present)
- VEHICLE_IN_COURT edges (heuristic court placement)
- VEHICLE_REQUIRES_OPERATING_ORDER gate nodes/edges + validator output
- Lane-first Bloom perspectives (MEEK1-4 + MSC/JTC)
- Optional PDF extraction + OCR with directory-safe Tesseract discovery
"""

import argparse
import json
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd

try:
    import networkx as nx
except Exception:
    nx = None

from graph_io import Node, Edge, write_nodes_csv, write_edges_csv
from utils import iso_now, stable_id, parse_props_json_cell, normalize_space
from authority_vehicle_resolver import extract_citations, build_authority_index, resolve_citation, infer_vehicle_links_from_authority_props
from lane_perspectives import build_lane_perspectives, write_lane_perspectives_json, write_lane_queries_cypher
from ocr_ingest import extract_pdf_text_and_optional_ocr, build_quote_atoms_from_pages

VERSION = "1.2.0r1"

CONSTRAINTS_CYPHER = r"""// Neo4j constraints/indexes (safe to re-run)
CREATE CONSTRAINT IF NOT EXISTS constraint_uid_authority
FOR (n:Authority) REQUIRE n.uid IS UNIQUE;

CREATE CONSTRAINT IF NOT EXISTS constraint_uid_vehicle
FOR (n:Vehicle) REQUIRE n.uid IS UNIQUE;

CREATE CONSTRAINT IF NOT EXISTS constraint_uid_contradiction
FOR (n:ContradictionItem) REQUIRE n.uid IS UNIQUE;

CREATE CONSTRAINT IF NOT EXISTS constraint_uid_sourceref
FOR (n:SourceRef) REQUIRE n.uid IS UNIQUE;

CREATE CONSTRAINT IF NOT EXISTS constraint_uid_quote
FOR (n:QuoteAtom) REQUIRE n.uid IS UNIQUE;

CREATE CONSTRAINT IF NOT EXISTS constraint_uid_stub
FOR (n:AuthorityCiteStub) REQUIRE n.uid IS UNIQUE;

CREATE CONSTRAINT IF NOT EXISTS constraint_uid_orderpin
FOR (n:OperatingOrderPin) REQUIRE n.uid IS UNIQUE;

CREATE CONSTRAINT IF NOT EXISTS constraint_uid_gate
FOR (n:GateResult) REQUIRE n.uid IS UNIQUE;

CREATE CONSTRAINT IF NOT EXISTS constraint_uid_court
FOR (n:Court) REQUIRE n.uid IS UNIQUE;

CREATE INDEX IF NOT EXISTS idx_node_type FOR (n) ON (n.node_type);
"""

GRAPH_CONTRACT_YML = r"""version: 1.2.0
contract: LitigationOS_GraphContract
purpose: >
  Deterministic compiler contract for Neo4j + Bloom + Gephi emissions.
  DRAFT mode is fail-soft; gates emit structured nodes/edges but do not block compilation.

nodes:
  - type: Authority
    key: uid
    required_props: [name]
    optional_props: [citation, pinpoint, authority_class, source, props_json]
  - type: Vehicle
    key: uid
    required_props: [name]
    optional_props: [vehicle_class, lane, court_hint, source, props_json]
  - type: Court
    key: uid
    required_props: [name]
    optional_props: [court_level]
  - type: ContradictionItem
    key: uid
    required_props: [cm_id]
    optional_props: [type, description, status, pin, src_id, notes]
  - type: SourceRef
    key: uid
    required_props: [src_id]
    optional_props: [bundle_uid, entry_path, locator, method, integrity_key]
  - type: QuoteAtom
    key: uid
    required_props: [text]
    optional_props: [provenance, created_at]
  - type: AuthorityCiteStub
    key: uid
    required_props: [citation]
  - type: OperatingOrderPin
    key: uid
    required_props: [order_id]
    optional_props: [entry_date, roa_entry, served_date, effective_status, superseded_by, stayed_by, notes]
  - type: GateResult
    key: uid
    required_props: [gate_name, status]
    optional_props: [details]

edges:
  - type: CITES_AUTHORITY
    from: QuoteAtom|Corpus|Node
    to: Authority
    props: [citation, mode]
  - type: CITES_AUTHORITY_CANDIDATE
    from: QuoteAtom|Corpus|Node
    to: Authority
    props: [citation, mode, score]
  - type: CITES_AUTHORITY_UNRESOLVED
    from: QuoteAtom|Corpus|Node
    to: AuthorityCiteStub
    props: [citation, mode]
  - type: AUTHORITY_SUPPORTS_VEHICLE
    from: Authority
    to: Vehicle
    props: [basis, confidence]
  - type: VEHICLE_IN_COURT
    from: Vehicle
    to: Court
    props: [basis]
  - type: VEHICLE_REQUIRES_OPERATING_ORDER
    from: Vehicle
    to: GateResult
    props: [gate_name]
  - type: GATE_FOR_VEHICLE
    from: GateResult
    to: Vehicle
    props: [gate_name]

validators:
  - id: gate.operating_order_pin
    description: Vehicle requires at least one OperatingOrderPin with required fields for FILE_READY/PCG.
    required_fields: [order_id, entry_date, roa_entry, effective_status]
"""

DEFAULT_COURTS = [
    {"uid":"Court:MI_TRIAL", "name":"Michigan Trial Court", "court_level":"trial"},
    {"uid":"Court:MI_COA", "name":"Michigan Court of Appeals", "court_level":"coa"},
    {"uid":"Court:MI_MSC", "name":"Michigan Supreme Court", "court_level":"msc"},
    {"uid":"Court:MI_JTC", "name":"Judicial Tenure Commission", "court_level":"jtc"},
]


def load_config(script_dir: Path) -> Dict[str, Any]:
    cfg_path = script_dir / "litigationos_config.json"
    if cfg_path.exists():
        return json.loads(cfg_path.read_text(encoding="utf-8"))
    return {"tesseract_candidates": [], "lane_rules": {}, "ocr": {}}


def load_csv_if_exists(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, dtype=str, low_memory=False)


def normalize_labels(label_cell: Any) -> List[str]:
    if label_cell is None or (isinstance(label_cell, float) and pd.isna(label_cell)):
        return []
    s = str(label_cell).strip()
    if not s:
        return []
    return [p.strip() for p in s.split(";") if p.strip()]


def node_type_from_row(kind: str, labels: List[str], name: str) -> str:
    k = (kind or "").strip().lower()
    if "Authority" in labels or k in {"authority", "benchbook", "statute", "canon", "caselaw"}:
        return "Authority"
    if k == "vehicle":
        return "Vehicle"
    if k == "authority_hub":
        return "AuthorityHub"
    n = (name or "").upper()
    if n.startswith(("MCR ", "MCL ", "MRE ")):
        return "Authority"
    return "Node"


def build_nodes_from_df(df: pd.DataFrame, source_tag: str) -> List[Node]:
    out: List[Node] = []
    if df.empty:
        return out
    for _, r in df.iterrows():
        uid = str(r.get(":ID") or r.get("uid") or r.get("id") or "").strip()
        if not uid:
            continue
        labels = normalize_labels(r.get(":LABEL") or r.get("labels"))
        kind = (r.get("kind") or "").strip()
        name = (r.get("name") or r.get("label") or "").strip()
        props_json = parse_props_json_cell(r.get("props_json"))
        props: Dict[str, Any] = {
            "source": source_tag,
            "name": name,
            "kind": kind,
            "group": (r.get("group") or ""),
            "tags_raw": (r.get("tags") or r.get("tags_raw") or ""),
            "tokens_raw": (r.get("tokens") or r.get("tokens_raw") or ""),
        }
        if props_json:
            props["props_json"] = props_json
        nt = node_type_from_row(kind, labels, name)
        labels2 = sorted(set(labels + ([nt] if nt not in labels else [])))
        out.append(Node(uid=uid, node_type=nt, labels=labels2, props=props))
    out.sort(key=lambda n: (n.node_type, n.uid))
    return out


def extract_zip_to_scratch(z: Path, scratch: Path) -> None:
    scratch.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(z, "r") as zz:
        zz.extractall(scratch / z.stem)


def ingest_knowledge_jsonl(path: Path) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    auth: List[Dict[str, Any]] = []
    veh: List[Dict[str, Any]] = []
    if not path.exists():
        return auth, veh
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            uid = str(obj.get("uid") or obj.get("id") or obj.get(":ID") or "").strip()
            labels = obj.get("labels") or obj.get(":LABEL") or []
            if isinstance(labels, str):
                labels = [x for x in labels.split(";") if x]
            node_type = str(obj.get("node_type") or obj.get("type") or "").strip()
            name = obj.get("name") or obj.get("citation") or (obj.get("props") or {}).get("name")
            props = obj.get("props") if isinstance(obj.get("props"), dict) else obj
            blob_labels = " ".join([str(x) for x in labels]).lower()

            if ("authority" in blob_labels) or (node_type.lower() == "authority") or (isinstance(name, str) and name.upper().startswith(("MCR ","MCL ","MRE "))):
                if uid:
                    auth.append({"uid": uid, "name": name or "", "citation": obj.get("citation") or "", "pinpoint": obj.get("pinpoint") or "", "props": props})
                continue
            if ("vehicle" in blob_labels) or (node_type.lower() == "vehicle"):
                if uid:
                    veh.append({"uid": uid, "name": name or "", "props": props})
                continue
            if "vehicle_types" in obj and isinstance(obj["vehicle_types"], list):
                for v in obj["vehicle_types"]:
                    if isinstance(v, dict):
                        vu = str(v.get("uid") or v.get("id") or v.get("vehicle_id") or "").strip()
                        nm = v.get("name") or v.get("vehicle") or ""
                        if vu:
                            veh.append({"uid": vu, "name": nm, "props": v})

    def dedupe(recs):
        seen=set(); out=[]
        for r in recs:
            if r["uid"] in seen: 
                continue
            seen.add(r["uid"]); out.append(r)
        return out
    return dedupe(auth), dedupe(veh)


def ensure_court_nodes(nodes: List[Node]) -> None:
    present = set(n.uid for n in nodes)
    for c in DEFAULT_COURTS:
        if c["uid"] in present:
            continue
        nodes.append(Node(uid=c["uid"], node_type="Court", labels=["Court"], props={"name": c["name"], "court_level": c["court_level"]}))


def find_files(in_dir: Path, scratch: Path, glob_pat: str) -> List[Path]:
    hits = list(in_dir.glob(glob_pat))
    hits += list(scratch.rglob(glob_pat))
    hits = [p for p in hits if p.is_file()]
    return sorted(set(hits))


def load_contradiction_maps(paths: List[Path]) -> pd.DataFrame:
    dfs = []
    for p in paths:
        try:
            dfs.append(pd.read_csv(p, dtype=str, low_memory=False))
        except Exception:
            continue
    if not dfs:
        return pd.DataFrame(columns=["cm_id","type","description","src_id","pin","status","notes"])
    df = pd.concat(dfs, ignore_index=True).drop_duplicates()
    if "cm_id" in df.columns:
        df = df.sort_values(["cm_id"], kind="mergesort")
    return df


def contradiction_graph(df: pd.DataFrame) -> Tuple[List[Node], List[Edge]]:
    nodes: List[Node] = []
    edges: List[Edge] = []
    if df.empty:
        return nodes, edges
    src_ids = sorted(set([str(x).strip() for x in df.get("src_id", pd.Series(dtype=str)).fillna("").tolist() if str(x).strip()]))
    for sid in src_ids:
        nodes.append(Node(uid=f"SourceRef:{sid}", node_type="SourceRef", labels=["SourceRef"], props={"src_id": sid}))
    for _, r in df.iterrows():
        cm_id = str(r.get("cm_id") or "").strip()
        if not cm_id:
            continue
        c_uid = f"Contradiction:{cm_id}"
        props = {k: (r.get(k) or "") for k in ["cm_id","type","description","src_id","pin","status","notes"]}
        nodes.append(Node(uid=c_uid, node_type="ContradictionItem", labels=["ContradictionItem"], props=props))
        sid = str(r.get("src_id") or "").strip()
        if sid:
            edges.append(Edge(uid=f"Edge:{stable_id('CONTRAD_FROM', c_uid, sid)}",
                              rel_type="CONTRADICTION_FROM_SOURCE",
                              from_uid=c_uid, to_uid=f"SourceRef:{sid}",
                              props={"pin": props.get("pin","")}))
    return nodes, edges


def authority_vehicle_edges(nodes: List[Node], edges: List[Edge], knowledge_auth: List[Dict[str, Any]], knowledge_veh: List[Dict[str, Any]]) -> None:
    vehicle_by_uid = {n.uid: n for n in nodes if (n.node_type == "Vehicle" or "Vehicle" in n.labels)}
    existing = set(vehicle_by_uid.keys())
    for v in knowledge_veh:
        vu = v.get("uid"); nm = v.get("name") or ""
        if vu and vu not in existing:
            nodes.append(Node(uid=vu, node_type="Vehicle", labels=["Vehicle"], props={"name": nm, "source":"KNOWLEDGE_ALL.jsonl"}))
            existing.add(vu)
    vehicle_by_uid = {n.uid: n for n in nodes if (n.node_type == "Vehicle" or "Vehicle" in n.labels)}
    vehicle_by_name = {normalize_space(str(n.props.get("name","")).lower()): n for n in vehicle_by_uid.values() if n.props.get("name")}
    auth_by_uid = {n.uid: n for n in nodes if (n.node_type == "Authority" or "Authority" in n.labels)}

    for a in knowledge_auth:
        au = a.get("uid")
        if not au or au not in auth_by_uid:
            continue
        node = auth_by_uid[au]
        if a.get("pinpoint") and not node.props.get("pinpoint"):
            node.props["pinpoint"] = a.get("pinpoint")
        if a.get("citation") and not node.props.get("citation"):
            node.props["citation"] = a.get("citation")

        raw_links = infer_vehicle_links_from_authority_props(a.get("props", {}) if isinstance(a.get("props", {}), dict) else {})
        for raw in raw_links:
            raw = str(raw).strip()
            if not raw:
                continue
            target = vehicle_by_uid.get(raw)
            if not target:
                target = vehicle_by_name.get(normalize_space(raw.lower()))
            if not target:
                continue
            edges.append(Edge(uid=f"Edge:{stable_id('AUTH_SUPP_VEH', au, target.uid)}",
                              rel_type="AUTHORITY_SUPPORTS_VEHICLE",
                              from_uid=au, to_uid=target.uid,
                              props={"basis":"corpus_props", "confidence":"candidate"}))


def vehicle_court_edges(nodes: List[Node], edges: List[Edge]) -> None:
    ensure_court_nodes(nodes)
    courts = {n.uid for n in nodes if (n.node_type == "Court" or "Court" in n.labels)}
    for v in [n for n in nodes if (n.node_type == "Vehicle" or "Vehicle" in n.labels)]:
        name = (v.props.get("name") or "").lower()
        targets = []
        if any(k in name for k in ["superintending", "claim of appeal", "application for leave", "coa", "court of appeals"]):
            targets.append("Court:MI_COA")
        if any(k in name for k in ["supreme", "msc"]):
            targets.append("Court:MI_MSC")
        if any(k in name for k in ["jtc", "tenure", "judicial conduct"]):
            targets.append("Court:MI_JTC")
        if not targets:
            targets.append("Court:MI_TRIAL")
        for t in targets:
            if t in courts:
                edges.append(Edge(uid=f"Edge:{stable_id('VEH_IN_COURT', v.uid, t)}",
                                  rel_type="VEHICLE_IN_COURT",
                                  from_uid=v.uid, to_uid=t,
                                  props={"basis":"heuristic_name"}))


def operating_order_gate(nodes: List[Node], edges: List[Edge]) -> None:
    orderpins = [n for n in nodes if (n.node_type == "OperatingOrderPin" or "OperatingOrderPin" in n.labels)]
    required_fields = ["order_id","entry_date","roa_entry","effective_status"]
    orderpin_ok = any(all(str(op.props.get(f,"")).strip() for f in required_fields) for op in orderpins)

    existing = set(n.uid for n in nodes)
    for v in [n for n in nodes if (n.node_type == "Vehicle" or "Vehicle" in n.labels)]:
        gate_uid = f"GateResult:OperatingOrderPin:{v.uid}"
        if gate_uid not in existing:
            nodes.append(Node(uid=gate_uid, node_type="GateResult", labels=["GateResult"], props={
                "gate_name":"OperatingOrderPin",
                "status": "PASS" if orderpin_ok else "FAIL",
                "details":"Requires pinned controlling order metadata (entry_date, ROA entry, effective_status)."
            }))
            existing.add(gate_uid)
        edges.append(Edge(uid=f"Edge:{stable_id('VEH_REQ_OO', v.uid, gate_uid)}",
                          rel_type="VEHICLE_REQUIRES_OPERATING_ORDER",
                          from_uid=v.uid, to_uid=gate_uid,
                          props={"gate_name":"OperatingOrderPin"}))
        edges.append(Edge(uid=f"Edge:{stable_id('GATE_FOR_VEH', gate_uid, v.uid)}",
                          rel_type="GATE_FOR_VEHICLE",
                          from_uid=gate_uid, to_uid=v.uid,
                          props={"gate_name":"OperatingOrderPin"}))


def add_citation_edges(nodes: List[Node], edges: List[Edge], authority_index, citing: List[Tuple[str,str]]) -> None:
    existing_nodes = set(n.uid for n in nodes)
    existing_edges = set(e.uid for e in edges)
    for node_uid, text in citing:
        for cite in extract_citations(text):
            uid_exact, uid_fuzzy, mode, score = resolve_citation(authority_index, cite, fuzzy_cutoff=90)
            if mode == "exact" and uid_exact:
                eid = f"Edge:{stable_id('CITES', node_uid, uid_exact, cite)}"
                if eid not in existing_edges:
                    edges.append(Edge(uid=eid, rel_type="CITES_AUTHORITY", from_uid=node_uid, to_uid=uid_exact,
                                      props={"citation": cite, "mode":"exact"}))
                    existing_edges.add(eid)
            elif mode == "fuzzy" and uid_fuzzy:
                eid = f"Edge:{stable_id('CITES_CAND', node_uid, uid_fuzzy, cite)}"
                if eid not in existing_edges:
                    edges.append(Edge(uid=eid, rel_type="CITES_AUTHORITY_CANDIDATE", from_uid=node_uid, to_uid=uid_fuzzy,
                                      props={"citation": cite, "mode":"fuzzy", "score": score}))
                    existing_edges.add(eid)
            else:
                stub_uid = f"AuthorityCiteStub:{cite}"
                if stub_uid not in existing_nodes:
                    nodes.append(Node(uid=stub_uid, node_type="AuthorityCiteStub", labels=["AuthorityCiteStub","Authority"], props={"citation": cite}))
                    existing_nodes.add(stub_uid)
                eid = f"Edge:{stable_id('CITE_STUB', node_uid, stub_uid, cite)}"
                if eid not in existing_edges:
                    edges.append(Edge(uid=eid, rel_type="CITES_AUTHORITY_UNRESOLVED", from_uid=node_uid, to_uid=stub_uid,
                                      props={"citation": cite, "mode":"unresolved"}))
                    existing_edges.add(eid)


def write_graphml(path: Path, nodes: List[Node], edges: List[Edge]) -> None:
    if nx is None:
        return
    G = nx.MultiDiGraph()
    for n in nodes:
        G.add_node(n.uid, node_type=n.node_type, labels=";".join(n.labels), props_json=json.dumps(n.props, ensure_ascii=False, sort_keys=True))
    for e in edges:
        G.add_edge(e.from_uid, e.to_uid, key=e.uid, uid=e.uid, rel_type=e.rel_type, props_json=json.dumps(e.props, ensure_ascii=False, sort_keys=True))
    nx.write_graphml(G, path)


def validate(nodes: List[Node], edges: List[Edge]) -> Dict[str, Any]:
    out = {"errors": [], "warnings": [], "stats": {}}
    nuids = [n.uid for n in nodes]
    euids = [e.uid for e in edges]
    if len(nuids) != len(set(nuids)):
        out["errors"].append({"code":"DUP_NODE_UID"})
    if len(euids) != len(set(euids)):
        out["errors"].append({"code":"DUP_EDGE_UID"})
    ns = set(nuids)
    missing = [e.uid for e in edges if (e.from_uid not in ns or e.to_uid not in ns)]
    if missing:
        out["errors"].append({"code":"EDGE_ENDPOINT_MISSING","count":len(missing),"sample":missing[:20]})
    if not any(n.node_type == "OperatingOrderPin" or "OperatingOrderPin" in n.labels for n in nodes):
        out["warnings"].append({"code":"NO_OPERATING_ORDER_PINS","msg":"Add OperatingOrderPin nodes to satisfy vehicle validity gates."})
    by_type={}
    for n in nodes:
        by_type[n.node_type]=by_type.get(n.node_type,0)+1
    by_rel={}
    for e in edges:
        by_rel[e.rel_type]=by_rel.get(e.rel_type,0)+1
    out["stats"]={"nodes":len(nodes),"edges":len(edges),"node_types":by_type,"rel_types":by_rel}
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in-dir", default=str(Path.cwd()))
    ap.add_argument("--out-dir", default="out")
    ap.add_argument("--emit-graphml", action="store_true")
    ap.add_argument("--skip-pdf", action="store_true")
    ap.add_argument("--ocr-mode", default="")
    ap.add_argument("--ocr-dpi", type=int, default=0)
    ap.add_argument("--ocr-lang", default="")
    ap.add_argument("--tesseract", default="", help="Path to tesseract.exe OR a directory containing it.")
    args = ap.parse_args()

    in_dir = Path(args.in_dir).resolve()
    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = in_dir / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    cfg = load_config(Path(__file__).resolve().parent)
    ocr_cfg = cfg.get("ocr", {})
    lane_rules = cfg.get("lane_rules", {})

    ocr_mode = args.ocr_mode or ocr_cfg.get("mode_default","auto")
    ocr_dpi = args.ocr_dpi or int(ocr_cfg.get("dpi_default",200))
    ocr_lang = args.ocr_lang or ocr_cfg.get("lang_default","eng")
    min_density = float(ocr_cfg.get("min_density_default",0.5))
    t_candidates = cfg.get("tesseract_candidates", [])

    scratch = out_dir / "_scratch"
    scratch.mkdir(exist_ok=True)
    for z in sorted(in_dir.glob("*.zip")):
        try:
            extract_zip_to_scratch(z, scratch)
        except Exception:
            pass

    nodes_merged = find_files(in_dir, scratch, "nodes_merged.csv")
    nodes_admin = find_files(in_dir, scratch, "nodes_neo4j_admin.csv")
    contradiction_maps = find_files(in_dir, scratch, "CONTRADICTION_MAP*.csv")
    knowledge_jsonl = find_files(in_dir, scratch, "KNOWLEDGE_ALL.jsonl")
    knowledge_txt = find_files(in_dir, scratch, "KNOWLEDGE_ALL.txt")

    nodes: List[Node] = []
    edges: List[Edge] = []

    if nodes_merged:
        nodes.extend(build_nodes_from_df(load_csv_if_exists(nodes_merged[0]), nodes_merged[0].name))
    if nodes_admin:
        nodes.extend(build_nodes_from_df(load_csv_if_exists(nodes_admin[0]), nodes_admin[0].name))

    # dedupe nodes
    by_uid={}
    for n in nodes:
        by_uid.setdefault(n.uid, n)
    nodes = sorted(by_uid.values(), key=lambda n:(n.node_type,n.uid))

    ensure_court_nodes(nodes)

    # contradictions
    cm_df = load_contradiction_maps(contradiction_maps)
    c_nodes, c_edges = contradiction_graph(cm_df)
    for n in c_nodes:
        by_uid.setdefault(n.uid, n)
    nodes = sorted(by_uid.values(), key=lambda n:(n.node_type,n.uid))
    edges.extend(c_edges)

    # knowledge
    k_auth, k_veh = ([], [])
    if knowledge_jsonl:
        k_auth, k_veh = ingest_knowledge_jsonl(knowledge_jsonl[0])

    # authority index
    authority_records=[]
    for n in nodes:
        if n.node_type == "Authority" or "Authority" in n.labels:
            authority_records.append({"uid": n.uid, "name": n.props.get("name",""), "citation": n.props.get("citation",""), "props": n.props})
    authority_records.extend(k_auth)
    auth_index = build_authority_index(authority_records)

    authority_vehicle_edges(nodes, edges, k_auth, k_veh)
    vehicle_court_edges(nodes, edges)

    citing: List[Tuple[str,str]] = []
    if knowledge_txt:
        try:
            txt = knowledge_txt[0].read_text(encoding="utf-8", errors="ignore")
            corp_uid = "Corpus:KNOWLEDGE_ALL"
            if corp_uid not in by_uid:
                by_uid[corp_uid] = Node(uid=corp_uid, node_type="Corpus", labels=["Corpus"], props={"name":"KNOWLEDGE_ALL.txt"})
            citing.append((corp_uid, txt[:500000]))
        except Exception:
            pass

    if not args.skip_pdf:
        pdfs = find_files(in_dir, scratch, "*.pdf")
        ocr_payload={"pdfs":[]}
        pdf_dir = out_dir / "pdf_extracts"
        pdf_dir.mkdir(exist_ok=True)
        for pdf in pdfs:
            try:
                payload = extract_pdf_text_and_optional_ocr(
                    pdf_path=pdf,
                    out_dir=pdf_dir,
                    config_candidates=t_candidates,
                    ocr_mode=ocr_mode,
                    min_density=min_density,
                    dpi=ocr_dpi,
                    lang=ocr_lang,
                    tesseract_cmd_or_dir=(args.tesseract.strip() or None),
                )
                ocr_payload["pdfs"].append(payload)
                q_atoms = build_quote_atoms_from_pages(pdf.name, payload, bundle_uid="BUNDLE:IN_DIR", entry_path=pdf.name)
                for qa in q_atoms:
                    q_uid = qa["quote_id"]
                    if q_uid not in by_uid:
                        by_uid[q_uid] = Node(uid=q_uid, node_type="QuoteAtom", labels=["QuoteAtom"], props={
                            "text": qa["text"], "provenance": qa.get("provenance", {}), "created_at": iso_now()
                        })
                    citing.append((q_uid, qa["text"]))
            except Exception as ex:
                ocr_payload["pdfs"].append({"pdf": str(pdf), "error": str(ex)})
        (out_dir / "pdf_extract_index.json").write_text(json.dumps(ocr_payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    nodes = sorted(by_uid.values(), key=lambda n:(n.node_type,n.uid))

    add_citation_edges(nodes, edges, auth_index, citing)
    operating_order_gate(nodes, edges)

    # dedupe edges
    e_by={}
    for e in edges:
        e_by.setdefault(e.uid, e)
    edges = sorted(e_by.values(), key=lambda e:(e.rel_type,e.from_uid,e.to_uid,e.uid))

    violations = validate(nodes, edges)

    # emit contract + constraints
    (out_dir / "graph_contract.yml").write_text(GRAPH_CONTRACT_YML, encoding="utf-8")
    (out_dir / "neo4j_constraints.cypher").write_text(CONSTRAINTS_CYPHER, encoding="utf-8")

    write_nodes_csv(out_dir / "neo4j_nodes.csv", nodes)
    write_edges_csv(out_dir / "neo4j_edges.csv", edges)

    if args.emit_graphml and nx is not None:
        write_graphml(out_dir / "graph_core.graphml", nodes, edges)

    node_dicts = [{"uid": n.uid, "props": n.props} for n in nodes]
    perspectives = build_lane_perspectives(node_dicts, lane_rules)
    write_lane_perspectives_json(out_dir / "bloom_perspectives_by_lane.json", perspectives)
    write_lane_queries_cypher(out_dir / "bloom_lane_queries.cypher", lane_rules)

    (out_dir / "violations.json").write_text(json.dumps(violations, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    (out_dir / "action_report.md").write_text(f"# Action Report (DRAFT) — {iso_now()}\n\n```json\n{json.dumps(violations['stats'], indent=2, sort_keys=True)}\n```\n", encoding="utf-8")
    (out_dir / "run_ledger.jsonl").write_text(json.dumps({"ts": iso_now(), "version": VERSION, "stats": violations["stats"], "warnings": violations.get("warnings", []), "errors": violations.get("errors", [])}, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")

    return 0 if not violations.get("errors") else 1


if __name__ == "__main__":
    raise SystemExit(main())
