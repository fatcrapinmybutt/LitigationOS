\
#!/usr/bin/env python3
"""
LitigationOS Autopilot Compiler Runtime

- Ingests: dirs, files, ZIPs (auto-extract)
- Supports: nodes/edges CSVs (multiple formats), contradiction maps, KNOWLEDGE_ALL (jsonl/txt),
  PDFs (embedded-text extraction + optional OCR fail-soft)
- Emits: Neo4j core CSVs + props jsonl.gz, GraphML, Bloom metadata, action report, constraints, contract, manifest.

Design goals:
- Deterministic ids
- Non-destructive outputs
- Fail-soft defaults
"""

from __future__ import annotations

import argparse
import csv
import datetime as _dt
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import zipfile
import zlib
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple

import pandas as pd
import networkx as nx
import yaml

try:
    import fitz  # PyMuPDF
except Exception:  # pragma: no cover
    fitz = None

try:
    from PIL import Image  # noqa
except Exception:  # pragma: no cover
    Image = None

try:
    import pytesseract  # noqa
except Exception:  # pragma: no cover
    pytesseract = None


# -------------------------
# Utilities
# -------------------------

def iso_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def stable_id(*parts: str) -> str:
    h = hashlib.sha1("||".join(parts).encode("utf-8", errors="ignore")).hexdigest()
    return h[:24]

def crc32_file(p: Path) -> str:
    crc = 0
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            crc = zlib.crc32(chunk, crc)
    return format(crc & 0xFFFFFFFF, "08x")

def safe_json(s: Any) -> Optional[Any]:
    if s is None:
        return None
    if isinstance(s, (dict, list)):
        return s
    if not isinstance(s, str):
        return None
    t = s.strip()
    if not t or t.lower() == "nan":
        return None
    try:
        return json.loads(t)
    except Exception:
        return None

def parse_labels_cell(cell: Any) -> List[str]:
    if cell is None:
        return []
    s = str(cell).strip()
    if not s or s.lower() == "nan":
        return []
    if ";" in s:
        return [p.strip() for p in s.split(";") if p.strip()]
    return [s]

def infer_type_from_id(uid: str) -> str:
    s = (uid or "").lower()
    for p, t in [
        ("violation", "Violation"),
        ("viol", "Violation"),
        ("harm", "Harm"),
        ("remedy", "Remedy"),
        ("rem_", "Remedy"),
        ("vehicle", "Vehicle"),
        ("court", "Court"),
        ("mcr", "Authority"),
        ("mcl", "Authority"),
        ("mre", "Authority"),
        ("authority", "Authority"),
        ("auth", "Authority"),
        ("case", "Case"),
        ("jtc", "JTC"),
        ("module", "Module"),
        ("fact", "Fact"),
        ("quote", "QuoteAtom"),
        ("source", "SourceRef"),
        ("schema", "Schema"),
    ]:
        if s.startswith(p) or f"{p}:" in s or f"{p}::" in s:
            return t
    if s.startswith("file:"):
        return "File"
    if s.startswith("dir:"):
        return "Directory"
    if s.startswith("sha:"):
        return "ContentHash"
    if s.startswith("url:") or s.startswith("http"):
        return "URL"
    if s.startswith("ext:"):
        return "Extension"
    return "Node"

def make_labels(group: Optional[str], node_type: str) -> List[str]:
    labs: List[str] = []
    if group and str(group).strip() and str(group).strip().lower() != "nan":
        labs.append(str(group).strip())
    if node_type:
        labs.append(node_type)
    return sorted(set(labs)) if labs else ([node_type] if node_type else [])


# -------------------------
# Graph model
# -------------------------

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


class GraphBuilder:
    def __init__(self) -> None:
        self.nodes: Dict[str, Node] = {}
        self.edges: Dict[str, Edge] = {}

    def add_node(self, node: Node) -> None:
        if node.uid in self.nodes:
            ex = self.nodes[node.uid]
            labels = sorted(set(ex.labels + node.labels))
            props2 = dict(ex.props)
            for k, v in node.props.items():
                if k not in props2:
                    props2[k] = v
            node_type = ex.node_type or node.node_type
            self.nodes[node.uid] = Node(uid=ex.uid, node_type=node_type, labels=labels, props=props2)
        else:
            self.nodes[node.uid] = node

    def add_edge(self, edge: Edge) -> None:
        if edge.uid in self.edges:
            return
        self.edges[edge.uid] = edge


# -------------------------
# Ingesters
# -------------------------

CITE_RXS = [
    re.compile(r"\bMCR\s+\d+\.\d+(?:\([A-Za-z0-9]+\))*", re.IGNORECASE),
    re.compile(r"\bMCL\s+\d+(?:\.\d+)*[A-Za-z]?(?:\([^)]+\))*", re.IGNORECASE),
    re.compile(r"\bMRE\s+\d+\b", re.IGNORECASE),
]

def norm_cite(s: str) -> str:
    s = (s or "").strip().upper()
    s = re.sub(r"\s+", " ", s)
    s = s.replace(" )", ")").replace("( ", "(")
    return s

def extract_cites(text: str) -> List[str]:
    hits: List[str] = []
    for rx in CITE_RXS:
        hits += [norm_cite(m.group(0)) for m in rx.finditer(text or "")]
    out: List[str] = []
    seen = set()
    for h in hits:
        if h not in seen:
            seen.add(h)
            out.append(h)
    return out

def resolve_tesseract_cmd(tesseract: Optional[str]) -> Optional[str]:
    if not tesseract:
        return None
    p = Path(tesseract)
    if p.is_file() and p.name.lower() == "tesseract.exe":
        return str(p)
    if p.is_dir():
        # bounded recursive search
        exe = None
        for q in p.rglob("tesseract.exe"):
            exe = q
            break
        if exe:
            return str(exe)
    return None

def ingest_simple_nodes_edges(g: GraphBuilder, nodes_csv: Path, edges_csv: Path, source_tag: str) -> Tuple[int, int]:
    ndf = pd.read_csv(nodes_csv, dtype=str, low_memory=False)
    edf = pd.read_csv(edges_csv, dtype=str, low_memory=False)

    for _, r in ndf.iterrows():
        uid = str(r.get("id") or r.get(":ID") or r.get("uid") or "").strip()
        if not uid:
            continue
        label = str(r.get("label") or r.get("name") or uid).strip()
        group = r.get("group")
        nt = infer_type_from_id(uid)
        labs = make_labels(group, nt)
        props: Dict[str, Any] = {"label": label, "group": "" if group is None else str(group), "source": source_tag}
        for c in ndf.columns:
            if c in ("id", "label", "group"):
                continue
            v = r.get(c)
            if v is not None and str(v).lower() != "nan":
                props[c] = v
        g.add_node(Node(uid=uid, node_type=nt, labels=labs, props=props))

    for _, r in edf.iterrows():
        fr = str(r.get("source") or r.get("from") or r.get("from_uid") or r.get("start") or "").strip()
        to = str(r.get("target") or r.get("to") or r.get("to_uid") or r.get("end") or "").strip()
        if not fr or not to:
            continue
        rel = r.get(":TYPE") or r.get("relation") or r.get("type") or r.get("rel_type") or "RELATED_TO"
        rel = str(rel).strip()
        if not rel or rel.lower() == "nan":
            rel = "RELATED_TO"
        eid = f"E:{stable_id(source_tag, fr, to, rel)}"
        g.add_edge(Edge(uid=eid, rel_type=rel, from_uid=fr, to_uid=to, props={"source": source_tag}))

    return len(ndf), len(edf)

def ingest_nodes_merged(g: GraphBuilder, path: Path, source_tag: str) -> int:
    df = pd.read_csv(path, dtype=str, low_memory=False)
    for _, r in df.iterrows():
        uid = str(r.get(":ID") or "").strip()
        if not uid:
            continue
        labels = parse_labels_cell(r.get(":LABEL"))
        kind = str(r.get("kind") or "").strip()
        name = str(r.get("name") or r.get("label") or uid).strip()
        group = str(r.get("group") or "").strip()
        nt = infer_type_from_id(uid)
        if kind:
            if kind.lower() in {"authority", "authority_hub"}:
                nt = "AuthorityHub" if kind.lower() == "authority_hub" else "Authority"
            elif kind.lower() in {"violation", "harm", "remedy", "vehicle", "court", "case", "module", "fact"}:
                nt = kind.capitalize()
        labs = sorted(set(labels + make_labels(group if group else None, nt) + ([f"Kind_{kind}"] if kind else [])))
        props: Dict[str, Any] = {
            "source": source_tag,
            "id": r.get("id") or uid,
            "name": name,
            "kind": kind,
            "group": group if group and group.lower() != "nan" else "",
            "eff_date": r.get("eff_date") or "",
            "prefix": r.get("prefix") or "",
            "tags": r.get("tags") or "",
            "src_format": r.get("src_format") or "",
        }
        pj = safe_json(r.get("props_json"))
        if isinstance(pj, dict):
            props["props_json"] = pj
        g.add_node(Node(uid=uid, node_type=nt, labels=labs, props=props))
    return len(df)

def ingest_nodes_neo4j_admin(g: GraphBuilder, path: Path, source_tag: str) -> int:
    df = pd.read_csv(path, dtype=str, low_memory=False)
    for _, r in df.iterrows():
        uid = str(r.get("id:ID") or r.get(":ID") or "").strip()
        if not uid:
            continue
        labels = parse_labels_cell(r.get(":LABEL"))
        kind = str(r.get("kind") or "").strip()
        name = str(r.get("name") or uid).strip()
        nt = infer_type_from_id(uid)
        if "AuthorityHub" in labels:
            nt = "AuthorityHub"
        elif "Authority" in labels:
            nt = "Authority"
        if kind and kind.lower() in {"violation", "harm", "remedy", "vehicle", "court", "case", "module", "fact"}:
            nt = kind.capitalize()
        labs = sorted(set(labels + ([f"Kind_{kind}"] if kind else []) + [nt]))
        props: Dict[str, Any] = {"source": source_tag, "name": name, "kind": kind, "tags": r.get("tags") or ""}
        aj = safe_json(r.get("attr_json"))
        if isinstance(aj, dict):
            props["attr_json"] = aj
        g.add_node(Node(uid=uid, node_type=nt, labels=labs, props=props))
    return len(df)

def ingest_contradictions(g: GraphBuilder, paths: List[Path], source_tag: str) -> int:
    dfs = []
    for p in paths:
        if p.exists():
            dfs.append(pd.read_csv(p, dtype=str, low_memory=False))
    if not dfs:
        return 0
    df = pd.concat(dfs, ignore_index=True).drop_duplicates()
    for col in ["cm_id", "type", "description", "src_id", "pin", "status", "notes"]:
        if col not in df.columns:
            df[col] = ""
    for _, r in df.iterrows():
        cm_id = str(r.get("cm_id") or "").strip()
        if not cm_id:
            continue
        c_uid = f"Contradiction:{cm_id}"
        props = {k: ("" if r.get(k) is None or str(r.get(k)).lower() == "nan" else str(r.get(k))) for k in ["cm_id", "type", "description", "src_id", "pin", "status", "notes"]}
        props["source"] = source_tag
        g.add_node(Node(uid=c_uid, node_type="ContradictionItem", labels=["ContradictionItem", "Gap"], props=props))

        sid = str(r.get("src_id") or "").strip()
        if sid:
            s_uid = f"SourceRef:{sid}"
            g.add_node(Node(uid=s_uid, node_type="SourceRef", labels=["SourceRef"], props={"src_id": sid, "source": source_tag}))
            g.add_edge(Edge(uid=f"E:{stable_id('CONTRAD_SRC', c_uid, s_uid)}", rel_type="CONTRADICTION_FROM_SOURCE", from_uid=c_uid, to_uid=s_uid, props={"pin": props.get("pin", "")}))

        h_uid = f"HarmCand:{stable_id('HARM', cm_id)}"
        g.add_node(Node(uid=h_uid, node_type="HarmCandidate", labels=["HarmCandidate", "Harm"], props={"cm_id": cm_id, "text": props.get("description", ""), "source": source_tag}))
        g.add_edge(Edge(uid=f"E:{stable_id('CONTRAD_HARM', c_uid, h_uid)}", rel_type="GAP_IMPLICATES_HARM_CANDIDATE", from_uid=c_uid, to_uid=h_uid, props={}))

        rm_uid = f"RemedyCand:Acquire:{cm_id}"
        g.add_node(Node(uid=rm_uid, node_type="RemedyCandidate", labels=["RemedyCandidate", "Remedy"], props={"cm_id": cm_id, "remedy_kind": "acquire_and_ingest", "source": source_tag}))
        g.add_edge(Edge(uid=f"E:{stable_id('CONTRAD_REMEDY', c_uid, rm_uid)}", rel_type="REMEDY_FOR_GAP", from_uid=c_uid, to_uid=rm_uid, props={}))

        v_uid = f"VehicleCand:Resolve:{cm_id}"
        g.add_node(Node(uid=v_uid, node_type="VehicleCandidate", labels=["VehicleCandidate", "Vehicle"], props={"cm_id": cm_id, "vehicle_kind": "to_be_resolved", "source": source_tag}))
        g.add_edge(Edge(uid=f"E:{stable_id('REMEDY_VEH', rm_uid, v_uid)}", rel_type="REMEDY_IMPLIES_VEHICLE_CANDIDATE", from_uid=rm_uid, to_uid=v_uid, props={}))

        a_uid = f"AuthorityCand:{stable_id('AUTH', cm_id)}"
        g.add_node(Node(uid=a_uid, node_type="AuthorityCandidate", labels=["AuthorityCandidate", "Authority"], props={"cm_id": cm_id, "source": source_tag}))
        g.add_edge(Edge(uid=f"E:{stable_id('VEH_AUTH', v_uid, a_uid)}", rel_type="VEHICLE_REQUIRES_AUTHORITY_CANDIDATE", from_uid=v_uid, to_uid=a_uid, props={}))

        cl_uid = f"CaselawCand:{stable_id('CASELAW', cm_id)}"
        g.add_node(Node(uid=cl_uid, node_type="CaselawCandidate", labels=["CaselawCandidate", "Authority"], props={"cm_id": cm_id, "source": source_tag}))
        g.add_edge(Edge(uid=f"E:{stable_id('AUTH_CASELAW', a_uid, cl_uid)}", rel_type="AUTHORITY_SUPPORTED_BY_CASELAW_CANDIDATE", from_uid=a_uid, to_uid=cl_uid, props={}))

        act_uid = f"Action:{cm_id}"
        g.add_node(Node(uid=act_uid, node_type="NextAction", labels=["NextAction", "Action"], props={"cm_id": cm_id, "action": "Acquire referenced exhibit; ingest; rerun; then resolve vehicle/auth.", "source": source_tag}))
        g.add_edge(Edge(uid=f"E:{stable_id('CASELAW_ACTION', cl_uid, act_uid)}", rel_type="CASELAW_SUPPORTS_ACTION", from_uid=cl_uid, to_uid=act_uid, props={}))

    return len(df)

def ingest_knowledge_all(g: GraphBuilder, jsonl_path: Optional[Path], txt_path: Optional[Path], out_dir: Path) -> Dict[str, int]:
    from collections import defaultdict
    counts: Dict[str, int] = defaultdict(int)

    if txt_path and txt_path.exists():
        txt = txt_path.read_text(encoding="utf-8", errors="ignore")
        corp_uid = "Corpus:KNOWLEDGE_ALL"
        g.add_node(Node(uid=corp_uid, node_type="Corpus", labels=["Corpus"], props={"path": str(txt_path), "bytes": txt_path.stat().st_size}))
        ex_uid = "Corpus:KNOWLEDGE_ALL:EXCERPT"
        g.add_node(Node(uid=ex_uid, node_type="CorpusExcerpt", labels=["CorpusExcerpt"], props={"excerpt": txt[:5000]}))
        g.add_edge(Edge(uid=f"E:{stable_id('CORP_EX', corp_uid, ex_uid)}", rel_type="HAS_EXCERPT", from_uid=corp_uid, to_uid=ex_uid, props={}))

    if not jsonl_path or not jsonl_path.exists():
        return dict(counts)

    with jsonl_path.open("r", encoding="utf-8", errors="ignore") as f:
        for ln in f:
            try:
                obj = json.loads(ln)
            except Exception:
                counts["_parse_error"] += 1
                continue
            kind = str(obj.get("kind") or "").strip()
            oid = str(obj.get("id") or "").strip()
            title = str(obj.get("title") or oid).strip()
            payload = obj.get("payload") if isinstance(obj.get("payload"), dict) else {}
            src = str(obj.get("source_path") or "")
            uid = f"KA::{kind}::{oid}" if oid else f"KA::{kind}::{stable_id(title, src)}"

            nt = "KnowledgeRecord"
            if kind.startswith("schema."):
                nt = kind.split(".", 1)[1].replace("_", " ").title().replace(" ", "") + "Def"
            elif kind == "glossary.term":
                nt = "GlossaryTerm"
            elif kind.startswith("catalog."):
                nt = "CatalogItem"
            elif kind.startswith("attachments."):
                nt = "AttachmentRecord"

            labels = ["Knowledge", "KnowledgeRecord", nt]
            g.add_node(Node(uid=uid, node_type=nt, labels=sorted(set(labels)), props={
                "kind": kind, "id": oid, "title": title, "source_path": src, "payload": payload
            }))
            counts[kind] += 1

            if kind == "glossary.term":
                parent = payload.get("parent") if isinstance(payload, dict) else None
                if parent:
                    p_uid = f"KA::glossary.term::{parent}"
                    if p_uid not in g.nodes:
                        g.add_node(Node(uid=p_uid, node_type="GlossaryTerm", labels=["Knowledge", "KnowledgeRecord", "GlossaryTerm"], props={
                            "kind": "glossary.term", "id": parent, "title": parent, "source_path": "(implied)", "payload": {}
                        }))
                    g.add_edge(Edge(uid=f"E:{stable_id('TERM_CHILD', uid, p_uid)}", rel_type="TERM_CHILD_OF", from_uid=uid, to_uid=p_uid, props={}))

    return dict(counts)

def extract_pdf_text_and_cites(g: GraphBuilder, pdf: Path, out_dir: Path, tesseract_cmd: Optional[str]) -> Dict[str, Any]:
    if fitz is None:
        return {"pdf": str(pdf), "error": "PyMuPDF not installed"}
    extract_dir = out_dir / "pdf_extracts"
    extract_dir.mkdir(parents=True, exist_ok=True)

    b = pdf.read_bytes()
    crc = format(zlib.crc32(b) & 0xFFFFFFFF, "08x")
    ik = f"IK:{stable_id(pdf.name, crc, str(len(b)))}"

    src_uid = f"SourceRef:PDF:{pdf.name}"
    g.add_node(Node(uid=src_uid, node_type="SourceRef", labels=["SourceRef", "PDF"], props={
        "file": pdf.name, "bytes": len(b), "crc32": crc, "integrity_key": ik, "source": "pdf"
    }))

    doc = fitz.open(pdf)
    total_pages = doc.page_count
    pages_with_text = 0
    cites_total = 0

    # OCR helpers
    ocr_enabled = bool(tesseract_cmd and pytesseract and Image)
    if ocr_enabled:
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    for i in range(total_pages):
        page = doc.load_page(i)
        text = page.get_text("text") or ""
        if not text.strip() and ocr_enabled:
            # fail-soft OCR: render page and OCR
            pix = page.get_pixmap(dpi=200)
            img_path = extract_dir / f"{pdf.stem}__p{i+1:04d}.png"
            pix.save(str(img_path))
            try:
                text = pytesseract.image_to_string(str(img_path)) or ""
            except Exception:
                text = ""

        if not text.strip():
            continue

        pages_with_text += 1
        page_file = extract_dir / f"{pdf.stem}__p{i+1:04d}.txt"
        page_file.write_text(text, encoding="utf-8", errors="ignore")

        q_uid = f"Quote:PDF:{pdf.name}:p{i+1:04d}"
        g.add_node(Node(uid=q_uid, node_type="QuoteAtom", labels=["QuoteAtom", "Quote"], props={
            "pdf": pdf.name, "page": i + 1, "text_path": str(page_file.relative_to(out_dir)), "chars": len(text),
            "excerpt": text[:500]
        }))
        g.add_edge(Edge(uid=f"E:{stable_id('QUOTE_FROM', q_uid, src_uid)}", rel_type="QUOTE_FROM_SOURCE", from_uid=q_uid, to_uid=src_uid, props={"page": i + 1}))

        cites = extract_cites(text)
        cites_total += len(cites)
        for c in cites:
            stub_uid = f"AuthorityCiteStub:{c}"
            g.add_node(Node(uid=stub_uid, node_type="AuthorityCiteStub", labels=["Authority", "AuthorityCiteStub"], props={"citation": c}))
            g.add_edge(Edge(uid=f"E:{stable_id('CITES', q_uid, stub_uid, c)}", rel_type="CITES_AUTHORITY_UNRESOLVED", from_uid=q_uid, to_uid=stub_uid, props={"citation": c, "mode": "unresolved"}))

    return {"pdf": str(pdf), "pages": total_pages, "pages_with_text": pages_with_text, "citations_extracted": cites_total, "ocr_enabled": ocr_enabled}

def authority_resolution_exact(g: GraphBuilder) -> int:
    # map normalized citation text to authority nodes
    idx: Dict[str, str] = {}
    for n in g.nodes.values():
        if n.node_type in ("Authority", "AuthorityHub"):
            nm = n.props.get("name") or n.props.get("label") or ""
            nm = norm_cite(str(nm))
            if nm.startswith("MCR ") or nm.startswith("MCL ") or nm.startswith("MRE "):
                idx.setdefault(nm, n.uid)

    resolved = 0
    for n in g.nodes.values():
        if n.node_type == "AuthorityCiteStub":
            cite = norm_cite(str(n.props.get("citation") or ""))
            if cite in idx:
                target_uid = idx[cite]
                g.add_edge(Edge(uid=f"E:{stable_id('CITE_RES', n.uid, target_uid)}", rel_type="CITES_AUTHORITY_RESOLVED_EXACT", from_uid=n.uid, to_uid=target_uid, props={"citation": cite, "mode": "exact"}))
                resolved += 1
    return resolved


# -------------------------
# Emitters
# -------------------------

def emit_neo4j_core(g: GraphBuilder, out_dir: Path) -> Dict[str, Any]:
    nodes = sorted(g.nodes.values(), key=lambda n: (n.node_type, n.uid))
    # Ensure :Entity on all
    nodes2 = []
    for n in nodes:
        labs = sorted(set(n.labels + ["Entity"]))
        nodes2.append(Node(uid=n.uid, node_type=n.node_type, labels=labs, props=n.props))
    nodes = nodes2
    edges = sorted(g.edges.values(), key=lambda e: (e.rel_type, e.from_uid, e.to_uid, e.uid))

    nodes_core = out_dir / "neo4j_nodes_core.csv"
    edges_core = out_dir / "neo4j_edges_core.csv"
    node_props = out_dir / "node_props.jsonl.gz"
    edge_props = out_dir / "edge_props.jsonl.gz"

    with nodes_core.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["uid:ID", "labels:LABEL", "node_type", "label", "source", "kind", "group", "tags", "eff_date"])
        for n in nodes:
            label = n.props.get("label") or n.props.get("name") or n.props.get("title") or n.uid
            w.writerow([
                n.uid, ";".join(n.labels), n.node_type, label,
                n.props.get("source", ""), n.props.get("kind", ""), n.props.get("group", ""),
                n.props.get("tags", ""), n.props.get("eff_date", "")
            ])

    with edges_core.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["uid", "from_uid:START_ID", "to_uid:END_ID", "type:TYPE", "source"])
        for e in edges:
            w.writerow([e.uid, e.from_uid, e.to_uid, e.rel_type, e.props.get("source", "")])

    with gzip.open(node_props, "wt", encoding="utf-8") as f:
        for n in nodes:
            f.write(json.dumps({"uid": n.uid, "props": n.props}, ensure_ascii=False) + "\n")

    with gzip.open(edge_props, "wt", encoding="utf-8") as f:
        for e in edges:
            f.write(json.dumps({"uid": e.uid, "props": e.props}, ensure_ascii=False) + "\n")

    return {"nodes": len(nodes), "edges": len(edges)}

def emit_graphml(g: GraphBuilder, out_dir: Path) -> int:
    nodes = g.nodes.values()
    edges = g.edges.values()
    path = out_dir / "graph_core.graphml"
    G = nx.MultiDiGraph()
    for n in nodes:
        label = n.props.get("label") or n.props.get("name") or n.props.get("title") or n.uid
        labels = ";".join(sorted(set(n.labels + ["Entity"])))
        G.add_node(n.uid, node_type=n.node_type, labels=labels, label=label, source=n.props.get("source", ""))
    for e in edges:
        G.add_edge(e.from_uid, e.to_uid, key=e.uid, uid=e.uid, type=e.rel_type, source=e.props.get("source", ""))
    nx.write_graphml(G, path)
    return path.stat().st_size

def emit_constraints(out_dir: Path) -> None:
    cypher = """\
// Neo4j constraints & indexes (LitigationOS Autopilot Suite)
// Safe to run repeatedly (Neo4j 5+)

CREATE CONSTRAINT entity_uid_unique IF NOT EXISTS
FOR (n:Entity) REQUIRE n.uid IS UNIQUE;

CREATE INDEX entity_node_type IF NOT EXISTS
FOR (n:Entity) ON (n.node_type);

CREATE INDEX entity_label IF NOT EXISTS
FOR (n:Entity) ON (n.label);

CREATE INDEX authority_citation IF NOT EXISTS
FOR (n:AuthorityCiteStub) ON (n.citation);
"""
    (out_dir / "neo4j_constraints.cypher").write_text(cypher, encoding="utf-8")

def emit_bloom(out_dir: Path, node_type_counts: Dict[str, int], rel_type_counts: Dict[str, int]) -> None:
    queries = """\
// Bloom starter queries (LitigationOS Autopilot Suite)

MATCH (c:ContradictionItem) RETURN c LIMIT 500;

MATCH (c:ContradictionItem)-[:REMEDY_FOR_GAP]->(r:RemedyCandidate)-[:REMEDY_IMPLIES_VEHICLE_CANDIDATE]->(v:VehicleCandidate)
RETURN c,r,v LIMIT 500;

MATCH (c:ContradictionItem)-[:GAP_IMPLICATES_HARM_CANDIDATE]->(h:HarmCandidate)
RETURN c,h LIMIT 500;

MATCH (q:QuoteAtom)-[:CITES_AUTHORITY_UNRESOLVED]->(a:AuthorityCiteStub)
RETURN q,a LIMIT 500;

MATCH (t:GlossaryTerm)-[:TERM_CHILD_OF]->(p:GlossaryTerm)
RETURN t,p LIMIT 500;
"""
    (out_dir / "bloom_queries.cypher").write_text(queries, encoding="utf-8")

    meta = {
        "kind": "bloom.perspective_metadata",
        "version": "1.0.0",
        "created_at": iso_now(),
        "imports": {
            "nodes_core": "neo4j_nodes_core.csv",
            "edges_core": "neo4j_edges_core.csv",
            "node_props": "node_props.jsonl.gz",
            "edge_props": "edge_props.jsonl.gz",
            "graphml": "graph_core.graphml",
        },
        "node_type_counts": [{"node_type": k, "count": int(v)} for k, v in sorted(node_type_counts.items(), key=lambda kv: -kv[1])],
        "rel_type_counts": [{"rel_type": k, "count": int(v)} for k, v in sorted(rel_type_counts.items(), key=lambda kv: -kv[1])],
        "suggested_style": {"key_label_property": "label", "key_type_property": "node_type", "primary_label": "Entity"},
        "suggested_categories": [
            {"name": "Gaps/Contradictions", "labels": ["ContradictionItem", "Gap", "RemedyCandidate", "VehicleCandidate", "HarmCandidate", "NextAction"]},
            {"name": "Authorities", "labels": ["Authority", "AuthorityHub", "AuthorityCiteStub", "AuthorityCandidate", "CaselawCandidate"]},
            {"name": "Evidence/Quotes", "labels": ["QuoteAtom", "SourceRef", "PDF", "File"]},
            {"name": "Knowledge/Schema", "labels": ["GlossaryTerm", "KnowledgeRecord", "NodeTypeDef", "EdgeTypeDef", "PropertyDef", "CatalogItem"]},
        ],
    }
    (out_dir / "bloom_perspective.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

def emit_graph_contract(out_dir: Path, node_type_counts: Dict[str, int], rel_type_counts: Dict[str, int]) -> None:
    contract = {
        "contract_id": "LitigationOS_Autopilot_GraphContract",
        "contract_version": "1.0.0",
        "created_at": iso_now(),
        "import_files": {
            "nodes_core_csv": "neo4j_nodes_core.csv",
            "edges_core_csv": "neo4j_edges_core.csv",
            "node_props_jsonl_gz": "node_props.jsonl.gz",
            "edge_props_jsonl_gz": "edge_props.jsonl.gz",
            "graphml": "graph_core.graphml",
            "constraints": "neo4j_constraints.cypher",
        },
        "id_policy": {
            "node_id_property": "uid",
            "edge_id_property": "uid",
            "determinism": "stable_sha1_short",
        },
        "node_types_top": [{"node_type": k, "count": int(v)} for k, v in sorted(node_type_counts.items(), key=lambda kv: -kv[1])[:50]],
        "rel_types_top": [{"rel_type": k, "count": int(v)} for k, v in sorted(rel_type_counts.items(), key=lambda kv: -kv[1])[:50]],
        "chain_contract": {
            "goal": "violation/gap -> harm -> remedy -> vehicle -> authority -> caselaw -> action",
            "nodes": {
                "gap": "ContradictionItem",
                "harm": "HarmCandidate",
                "remedy": "RemedyCandidate",
                "vehicle": "VehicleCandidate",
                "authority": "AuthorityCandidate",
                "caselaw": "CaselawCandidate",
                "action": "NextAction",
            },
            "edges": [
                "GAP_IMPLICATES_HARM_CANDIDATE",
                "REMEDY_FOR_GAP",
                "REMEDY_IMPLIES_VEHICLE_CANDIDATE",
                "VEHICLE_REQUIRES_AUTHORITY_CANDIDATE",
                "AUTHORITY_SUPPORTED_BY_CASELAW_CANDIDATE",
                "CASELAW_SUPPORTS_ACTION",
            ],
            "status": "fail_soft_candidates",
        },
    }
    (out_dir / "graph_contract.yml").write_text(yaml.safe_dump(contract, sort_keys=False, allow_unicode=True), encoding="utf-8")

def emit_action_report(cm_paths: List[Path], out_path: Path) -> None:
    dfs = []
    for p in cm_paths:
        if p.exists():
            dfs.append(pd.read_csv(p, dtype=str, low_memory=False))
    if not dfs:
        out_path.write_text("# Action Report\n\nNo contradiction maps found.\n", encoding="utf-8")
        return
    df = pd.concat(dfs, ignore_index=True).drop_duplicates()
    for col in ["cm_id", "type", "description", "src_id", "pin", "status", "notes"]:
        if col not in df.columns:
            df[col] = ""
    df = df.sort_values(["status", "cm_id"], kind="mergesort")

    lines: List[str] = []
    lines.append(f"# Action Report — Autopilot Run {iso_now()}")
    lines.append("")
    lines.append("Chain: `ContradictionItem → HarmCandidate → RemedyCandidate → VehicleCandidate → AuthorityCandidate → CaselawCandidate → NextAction`")
    lines.append("")
    lines.append(f"Total contradiction rows (deduped): **{len(df)}**")
    lines.append("")

    status_counts = df["status"].fillna("").value_counts()
    lines.append("## Status counts")
    for k, v in status_counts.items():
        lines.append(f"- {k or '(blank)'}: {int(v)}")
    lines.append("")

    for _, r in df.iterrows():
        cm_id = str(r.get("cm_id") or "").strip()
        if not cm_id:
            continue
        lines.append(f"## {cm_id} — {str(r.get('type') or '').strip()} — {str(r.get('status') or '').strip()}")
        desc = str(r.get("description") or "").strip()
        if desc:
            lines.append(f"- Gap: {desc}")
        sid = str(r.get("src_id") or "").strip()
        if sid:
            lines.append(f"- SourceRef: `SourceRef:{sid}`")
        pin = str(r.get("pin") or "").strip()
        if pin:
            lines.append(f"- Pin: `{pin}`")
        notes = str(r.get("notes") or "").strip()
        if notes:
            lines.append(f"- Notes: {notes}")
        lines.append("- Autopilot chain nodes:")
        lines.append(f"  - HarmCandidate: `HarmCand:{stable_id('HARM', cm_id)}`")
        lines.append(f"  - RemedyCandidate: `RemedyCand:Acquire:{cm_id}`")
        lines.append(f"  - VehicleCandidate: `VehicleCand:Resolve:{cm_id}`")
        lines.append(f"  - AuthorityCandidate: `AuthorityCand:{stable_id('AUTH', cm_id)}`")
        lines.append(f"  - CaselawCandidate: `CaselawCand:{stable_id('CASELAW', cm_id)}`")
        lines.append(f"  - NextAction: `Action:{cm_id}`")
        lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")

def emit_manifest(out_dir: Path) -> None:
    files = [p for p in out_dir.rglob("*") if p.is_file()]
    manifest = []
    for p in sorted(files, key=lambda x: str(x.relative_to(out_dir))):
        manifest.append({"path": str(p.relative_to(out_dir)), "bytes": p.stat().st_size, "crc32": crc32_file(p)})
    (out_dir / "manifest.json").write_text(json.dumps({
        "manifest_version": "1.0.0",
        "created_at": iso_now(),
        "root": str(out_dir.name),
        "files": manifest,
    }, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

def emit_violations(g: GraphBuilder, out_dir: Path) -> None:
    node_uids = set(g.nodes.keys())
    missing_from = [e.uid for e in g.edges.values() if e.from_uid not in node_uids]
    missing_to = [e.uid for e in g.edges.values() if e.to_uid not in node_uids]

    from collections import Counter
    node_type_counts = Counter([n.node_type for n in g.nodes.values()])
    rel_type_counts = Counter([e.rel_type for e in g.edges.values()])

    viol = {
        "created_at": iso_now(),
        "node_count": len(g.nodes),
        "edge_count": len(g.edges),
        "missing_from": {"count": len(missing_from), "sample": missing_from[:20]},
        "missing_to": {"count": len(missing_to), "sample": missing_to[:20]},
        "node_type_counts": dict(node_type_counts),
        "rel_type_counts": dict(rel_type_counts),
    }
    (out_dir / "violations.json").write_text(json.dumps(viol, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


# -------------------------
# Path handling / main
# -------------------------

def collect_inputs(inputs: List[str], scratch: Path) -> List[Path]:
    scratch.mkdir(parents=True, exist_ok=True)
    paths: List[Path] = []
    for item in inputs:
        p = Path(item).expanduser()
        if not p.exists():
            continue
        if p.is_file() and p.suffix.lower() == ".zip":
            zdir = scratch / f"zip_{p.stem}_{stable_id(str(p), str(p.stat().st_size))}"
            if zdir.exists():
                shutil.rmtree(zdir)
            zdir.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(p, "r") as zz:
                zz.extractall(zdir)
            paths.append(zdir)
        else:
            paths.append(p)
    return paths

def find_first(root: Path, patterns: List[str]) -> Optional[Path]:
    for pat in patterns:
        found = list(root.rglob(pat))
        if found:
            return found[0]
    return None

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--inputs", nargs="+", required=True, help="Input paths (dirs/files/zips).")
    ap.add_argument("--out-dir", required=True, help="Output directory.")
    ap.add_argument("--scratch-dir", default=None, help="Scratch dir for zip extraction (default: <out-dir>/.scratch).")
    ap.add_argument("--tesseract", default=os.environ.get("TESSERACT_CMD", ""), help="Path to tesseract.exe OR a directory containing it.")
    ap.add_argument("--pdf-extract", action="store_true", help="Extract embedded (and optional OCR) text from PDFs.")
    ap.add_argument("--emit-graphml", action="store_true")
    ap.add_argument("--emit-bloom", action="store_true")
    ap.add_argument("--emit-action-report", action="store_true")
    ap.add_argument("--authority-resolve-exact", action="store_true", help="Resolve MCR/MCL/MRE citations to Authority nodes by exact match when possible.")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    out_dir = Path(args.out_dir).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)
    scratch = Path(args.scratch_dir).expanduser() if args.scratch_dir else (out_dir / ".scratch")

    tesseract_cmd = resolve_tesseract_cmd(args.tesseract.strip()) if args.tesseract else None

    input_paths = collect_inputs(args.inputs, scratch)
    if args.dry_run:
        print(json.dumps({"ts": iso_now(), "inputs_resolved": [str(p) for p in input_paths], "tesseract_cmd": tesseract_cmd}, indent=2))
        return 0

    g = GraphBuilder()
    stats: Dict[str, Any] = {"started_at": iso_now(), "inputs": [str(p) for p in input_paths], "tesseract_cmd": tesseract_cmd}

    # Heuristics: look for common files
    for p in input_paths:
        if p.is_dir():
            # AJP graph suite expected
            n1 = find_first(p, ["nodes_combined.csv", "*nodes_combined.csv"])
            e1 = find_first(p, ["edges_combined.csv", "*edges_combined.csv"])
            if n1 and e1:
                ingest_simple_nodes_edges(g, n1, e1, f"{p.name}:combined")

            n2 = find_first(p, ["APEX_GRAPH_nodes.csv"])
            e2 = find_first(p, ["APEX_GRAPH_edges.csv"])
            if n2 and e2:
                ingest_simple_nodes_edges(g, n2, e2, f"{p.name}:apex")

            # generic: ingest nodes_merged / nodes_neo4j_admin / contradiction map / knowledge_all if present
            nm = find_first(p, ["nodes_merged.csv"])
            if nm:
                ingest_nodes_merged(g, nm, "nodes_merged.csv")

            na = find_first(p, ["nodes_neo4j_admin.csv"])
            if na:
                ingest_nodes_neo4j_admin(g, na, "nodes_neo4j_admin.csv")

            cm = list(p.rglob("CONTRADICTION_MAP*.csv"))
            if cm:
                ingest_contradictions(g, cm, "CONTRADICTION_MAP*.csv")

            kaj = find_first(p, ["KNOWLEDGE_ALL.jsonl"])
            kat = find_first(p, ["KNOWLEDGE_ALL.txt"])
            if kaj or kat:
                ingest_knowledge_all(g, kaj, kat, out_dir)

            # PDFs
            if args.pdf_extract:
                for pdf in p.rglob("*.pdf"):
                    extract_pdf_text_and_cites(g, pdf, out_dir, tesseract_cmd)

        elif p.is_file():
            # individual files
            if p.name.lower().endswith(".pdf") and args.pdf_extract:
                extract_pdf_text_and_cites(g, p, out_dir, tesseract_cmd)
            if p.name.lower() == "nodes_merged.csv":
                ingest_nodes_merged(g, p, "nodes_merged.csv")
            if p.name.lower() == "nodes_neo4j_admin.csv":
                ingest_nodes_neo4j_admin(g, p, "nodes_neo4j_admin.csv")
            if p.name.upper().startswith("CONTRADICTION_MAP") and p.suffix.lower()==".csv":
                ingest_contradictions(g, [p], "CONTRADICTION_MAP*.csv")
            if p.name.lower()=="knowledge_all.jsonl" or p.name.lower()=="knowledge_all.txt":
                # handled in dir scan; allow single file too
                pass

    # Exact authority resolution (optional)
    resolved = 0
    if args.authority_resolve_exact:
        resolved = authority_resolution_exact(g)

    # Emit artifacts
    emit_constraints(out_dir)
    core_stats = emit_neo4j_core(g, out_dir)

    from collections import Counter
    node_type_counts = Counter([n.node_type for n in g.nodes.values()])
    rel_type_counts = Counter([e.rel_type for e in g.edges.values()])

    if args.emit_graphml:
        emit_graphml(g, out_dir)
    if args.emit_bloom:
        emit_bloom(out_dir, dict(node_type_counts), dict(rel_type_counts))
        emit_graph_contract(out_dir, dict(node_type_counts), dict(rel_type_counts))
    if args.emit_action_report:
        cm_paths = [Path(x) for x in []]  # not needed here; report can be built from any found cm files
        # build from any present in outputs scratch
        found_cm = list(scratch.rglob("CONTRADICTION_MAP*.csv")) + list(out_dir.rglob("CONTRADICTION_MAP*.csv"))
        if found_cm:
            emit_action_report(found_cm, out_dir / "action_report.md")
    emit_violations(g, out_dir)
    emit_manifest(out_dir)

    stats.update({
        "ended_at": iso_now(),
        "node_count": core_stats["nodes"],
        "edge_count": core_stats["edges"],
        "authority_resolution_exact_edges_added": resolved,
        "top_node_types": node_type_counts.most_common(15),
        "top_rel_types": rel_type_counts.most_common(15),
    })
    (out_dir / "run_stats.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")
    print(json.dumps(stats, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
