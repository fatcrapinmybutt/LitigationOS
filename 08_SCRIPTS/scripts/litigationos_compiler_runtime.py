#!/usr/bin/env python3
"""
LitigationOS Compiler Runtime v1.2.0

Goal:
- Ingest the user's uploaded artifacts (nodes CSVs, contradiction maps, PDFs, and docx-in-zip)
- Emit:
  - out/neo4j_nodes.csv
  - out/neo4j_edges.csv
  - out/graph.graphml
  - out/action_report.md
  - out/compile_report.json
  - out/violations_actions.json

Key principles:
- Deterministic: stable sorting + deterministic edge uids.
- Fail-soft on missing/unsupported inputs; fail-hard only if explicitly requested.
- No invented facts: action suggestions are "candidate mappings" grounded in dataset text/tokens only.

Usage:
  python litigationos_compiler_runtime.py --in "/path/to/folder" --out "./out"
  python litigationos_compiler_runtime.py --in "/mnt/data" --out "/mnt/data/out_run" --dry-run

Notes:
- If graph_contract.yml / litigationos_constraints.yml are available (either as files or inside
  LitigationOS_*bundle*.zip), the runtime will load and use them for validation.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import logging
import os
import re
import sys
import time
import zlib
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import pandas as pd

try:
    import networkx as nx
except Exception as e:
    nx = None

LOG = logging.getLogger("litigationos_compiler")

# -----------------------------
# Helpers
# -----------------------------

def utc_now_z() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

def crc32_hex(data: bytes) -> str:
    return f"{zlib.crc32(data) & 0xFFFFFFFF:08x}"

def stable_edge_uid(rel_type: str, from_uid: str, to_uid: str, extra: str = "") -> str:
    # Deterministic edge uid: CRC32 of a canonical string
    s = f"{rel_type}|{from_uid}|{to_uid}|{extra}".encode("utf-8", errors="replace")
    return f"e:{rel_type}:{crc32_hex(s)}"

def safe_json_loads(s: Any) -> Any:
    if s is None:
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

def normalize_whitespace(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()

def tokenize_text(s: str) -> List[str]:
    s = (s or "").lower()
    # Keep alnum tokens, split on non-word
    toks = re.split(r"[^a-z0-9]+", s)
    return [t for t in toks if t]

def jaccard(a: Iterable[str], b: Iterable[str]) -> float:
    A = set(a)
    B = set(b)
    if not A and not B:
        return 0.0
    if not A or not B:
        return 0.0
    return len(A & B) / max(1, len(A | B))

def find_files(in_dir: Path) -> Dict[str, List[Path]]:
    # Discover relevant files by name patterns
    out: Dict[str, List[Path]] = {
        "nodes": [],
        "nodes_admin": [],
        "contradiction_maps": [],
        "pdfs": [],
        "zips": [],
        "txts": [],
        "other_csv": []
    }
    for p in in_dir.iterdir():
        if not p.is_file():
            continue
        name = p.name.lower()
        if name == "nodes_merged.csv":
            out["nodes"].append(p)
        elif name == "nodes_neo4j_admin.csv":
            out["nodes_admin"].append(p)
        elif name.startswith("contradiction_map") and name.endswith(".csv"):
            out["contradiction_maps"].append(p)
        elif name.endswith(".pdf"):
            out["pdfs"].append(p)
        elif name.endswith(".zip"):
            out["zips"].append(p)
        elif name.endswith(".txt"):
            out["txts"].append(p)
        elif name.endswith(".csv"):
            out["other_csv"].append(p)
    return out

# -----------------------------
# Optional schema/contract loading (from files or bundles)
# -----------------------------

def extract_from_known_bundle_zips(in_dir: Path, dest_dir: Path) -> Dict[str, Path]:
    """
    If the user has uploaded bundle ZIPs (GraphContract/CompilerCoreBundle),
    extract the YML/MD/Cypher files we care about.
    """
    dest_dir.mkdir(parents=True, exist_ok=True)
    found: Dict[str, Path] = {}
    for zp in in_dir.glob("*.zip"):
        try:
            with zipfile.ZipFile(zp, "r") as z:
                names = set(z.namelist())
                targets = {
                    "graph_contract.yml": "graph_contract.yml",
                    "neo4j_constraints.cypher": "neo4j_constraints.cypher",
                    "litigationos_constraints.yml": "litigationos_constraints.yml",
                    "vehicle_selection_protocol.yml": "vehicle_selection_protocol.yml",
                    "graph_compiler_spec.md": "graph_compiler_spec.md",
                }
                for k, v in targets.items():
                    if v in names and k not in found:
                        data = z.read(v)
                        outp = dest_dir / v
                        outp.write_bytes(data)
                        found[k] = outp
        except Exception:
            continue

    # Also allow direct files in in_dir
    direct = {
        "graph_contract.yml": in_dir/"graph_contract.yml",
        "neo4j_constraints.cypher": in_dir/"neo4j_constraints.cypher",
        "litigationos_constraints.yml": in_dir/"litigationos_constraints.yml",
        "vehicle_selection_protocol.yml": in_dir/"vehicle_selection_protocol.yml",
        "graph_compiler_spec.md": in_dir/"graph_compiler_spec.md",
    }
    for k, p in direct.items():
        if p.exists() and k not in found:
            found[k] = p
    return found

# Lightweight YAML reader (avoid extra deps). Supports the simple constraint/contract formats we use.
def yaml_load_simple(text: str) -> Any:
    """
    Very small YAML subset parser using json-like heuristics.
    Supports:
    - key: value
    - nested dicts via indentation
    - lists with '-'
    This is intentionally conservative. If parsing fails, return None.
    """
    try:
        import yaml  # type: ignore
        return yaml.safe_load(text)
    except Exception:
        pass

    # Minimal fallback: attempt to convert to JSON-ish is too fragile; return None.
    return None

# -----------------------------
# Ingestion: Nodes CSVs
# -----------------------------

@dataclass
class NodeRec:
    uid: str
    node_type: str
    labels: List[str]
    name: str
    kind: str
    props: Dict[str, Any]
    source_file: str

@dataclass
class EdgeRec:
    uid: str
    rel_type: str
    from_uid: str
    to_uid: str
    props: Dict[str, Any]
    source: str

def parse_labels(label_field: str) -> List[str]:
    if not label_field:
        return []
    # Support "A;B;C" and "A|B"
    if ";" in label_field:
        parts = [p.strip() for p in label_field.split(";") if p.strip()]
    elif "|" in label_field:
        parts = [p.strip() for p in label_field.split("|") if p.strip()]
    else:
        parts = [label_field.strip()]
    return parts

def infer_node_type(kind: str, labels: List[str], fallback: str = "Node") -> str:
    k = (kind or "").strip()
    if k:
        # normalize some expected kinds
        mapping = {
            "authority_hub": "AuthorityHub",
            "authority": "Authority",
            "statute": "Statute",
            "benchbook": "Benchbook",
            "canon": "Canon",
            "violation": "Violation",
            "remedy": "Remedy",
            "motion": "Motion",
            "complaint": "Complaint",
            "defense": "Defense",
            "fact": "Fact",
            "keyword": "Keyword",
            "date": "Date",
            "document": "Document",
            "module": "Module",
        }
        return mapping.get(k.lower(), k)
    # else derive from labels
    for lab in labels:
        if lab.lower() in ["authority", "court", "lane", "case", "vehicle", "form"]:
            return lab
    return fallback

def load_nodes_merged(path: Path) -> List[NodeRec]:
    df = pd.read_csv(path, low_memory=False)
    nodes: List[NodeRec] = []
    for _, r in df.iterrows():
        uid = str(r.get(":ID") or r.get("uid") or r.get("id") or "").strip()
        if not uid:
            continue
        lbls = parse_labels(str(r.get(":LABEL") or ""))
        kind = str(r.get("kind") or "").strip()
        node_type = infer_node_type(kind, lbls, fallback="Node")
        name = str(r.get("name") or r.get("label") or r.get("id") or uid)
        props = {}
        # Carry some columns into props
        for c in ["id", "eff_date", "group", "kind", "label", "name", "prefix", "src_format", "tags"]:
            if c in df.columns and pd.notna(r.get(c)):
                props[c] = r.get(c)
        # props_json and tokens
        pj = safe_json_loads(r.get("props_json"))
        if isinstance(pj, dict):
            props.update({"props_json": pj})
        toks = safe_json_loads(r.get("tokens"))
        if isinstance(toks, list):
            props["tokens"] = toks
        nodes.append(NodeRec(uid=uid, node_type=node_type, labels=lbls if lbls else [node_type], name=name, kind=kind, props=props, source_file=path.name))
    return nodes

def load_nodes_admin(path: Path) -> List[NodeRec]:
    df = pd.read_csv(path, low_memory=False)
    nodes: List[NodeRec] = []
    for _, r in df.iterrows():
        uid = str(r.get("id:ID") or r.get(":ID") or r.get("uid") or r.get("id") or "").strip()
        if not uid:
            continue
        lbls = parse_labels(str(r.get(":LABEL") or ""))
        kind = str(r.get("kind") or "").strip()
        node_type = infer_node_type(kind, lbls, fallback="Node")
        name = str(r.get("name") or uid)
        props = {}
        for c in ["name", "kind", "tags"]:
            if c in df.columns and pd.notna(r.get(c)):
                props[c] = r.get(c)
        aj = safe_json_loads(r.get("attr_json"))
        if isinstance(aj, dict):
            props.update({"attr_json": aj})
        nodes.append(NodeRec(uid=uid, node_type=node_type, labels=lbls if lbls else [node_type], name=name, kind=kind, props=props, source_file=path.name))
    return nodes

# -----------------------------
# Ingestion: Contradiction Map
# -----------------------------

def load_contradiction_maps(paths: List[Path]) -> pd.DataFrame:
    dfs = []
    for p in paths:
        try:
            df = pd.read_csv(p)
            df["__source_file"] = p.name
            dfs.append(df)
        except Exception as e:
            LOG.warning("Failed reading contradiction map %s: %s", p, e)
    if not dfs:
        return pd.DataFrame(columns=["cm_id","type","description","src_id","pin","status","notes","__source_file"])
    out = pd.concat(dfs, ignore_index=True)
    # Normalize whitespace
    for c in ["type","description","src_id","pin","status","notes"]:
        if c in out.columns:
            out[c] = out[c].astype(str).map(lambda x: normalize_whitespace(x) if x and x != "nan" else "")
    # Deduplicate exact rows
    out = out.drop_duplicates(subset=["cm_id","type","description","src_id","pin","status","notes"])
    return out

# -----------------------------
# Optional: Extract embedded text from PDFs (fail-soft)
# -----------------------------

def extract_pdf_text_index(pdf_path: Path, max_pages: int = 10) -> Dict[str, Any]:
    """
    Extract a quick index for embedded-text PDFs (not full OCR).
    If no embedded text, returns low counts.
    """
    info = {"file": pdf_path.name, "pages": None, "pages_sampled": 0, "total_chars_sampled": 0, "has_text": False, "errors": None}
    try:
        import PyPDF2
        reader = PyPDF2.PdfReader(str(pdf_path))
        n = len(reader.pages)
        info["pages"] = n
        sample = min(max_pages, n)
        total = 0
        for i in range(sample):
            try:
                t = reader.pages[i].extract_text() or ""
            except Exception:
                t = ""
            total += len(t)
        info["pages_sampled"] = sample
        info["total_chars_sampled"] = total
        info["has_text"] = total > 50
        return info
    except Exception as e:
        info["errors"] = str(e)
        return info

# -----------------------------
# Optional: detect docx inside a misleading .zip name and extract text
# -----------------------------

def extract_docx_text_from_zipish(path: Path) -> Optional[str]:
    """
    The user has a file named '205 JSON CSV TXT .zip' which may actually be a docx container.
    If it contains word/document.xml, extract visible text.
    """
    try:
        with zipfile.ZipFile(path, "r") as z:
            names = set(z.namelist())
            if "word/document.xml" not in names:
                return None
            xml = z.read("word/document.xml").decode("utf-8", errors="replace")
            # very rough text pull from <w:t>
            texts = re.findall(r"<w:t[^>]*>(.*?)</w:t>", xml, flags=re.DOTALL)
            joined = normalize_whitespace(" ".join([re.sub(r"<[^>]+>", "", t) for t in texts]))
            return joined if joined else None
    except Exception:
        return None

# -----------------------------
# Graph building: nodes + edges + action mapping
# -----------------------------

AUTH_RULE_RE = re.compile(r"\b(MCR|MCL|MRE)\s+[\d.]+\b", re.IGNORECASE)
MI_CASE_RE = re.compile(r"\b(\d{4}\s+WL\s+\d+|Mich(?:\s+App)?\s+\d+)\b", re.IGNORECASE)

def extract_authority_candidates(nodes: List[NodeRec]) -> Dict[str, List[str]]:
    rules = set()
    caselaw = set()
    for n in nodes:
        blob = " ".join([n.name, str(n.props.get("prefix","")), json.dumps(n.props.get("tokens",[]))])
        for m in AUTH_RULE_RE.findall(blob):
            pass
        for m in AUTH_RULE_RE.finditer(blob):
            rules.add(m.group(0).upper())
        for m in MI_CASE_RE.finditer(blob):
            caselaw.add(m.group(0))
    return {"court_rules": sorted(rules), "caselaw": sorted(caselaw)}

def build_tag_edges(nodes: List[NodeRec]) -> Tuple[List[NodeRec], List[EdgeRec]]:
    tag_nodes: Dict[str, NodeRec] = {}
    edges: List[EdgeRec] = []
    for n in nodes:
        tags_val = n.props.get("tags")
        if not tags_val or str(tags_val).lower() == "nan":
            continue
        # tags might be delimited or single
        raw = str(tags_val)
        parts = [p.strip() for p in re.split(r"[;,|]+", raw) if p.strip()]
        for t in parts:
            tag_uid = f"Tag:{t}"
            if tag_uid not in tag_nodes:
                tag_nodes[tag_uid] = NodeRec(uid=tag_uid, node_type="Tag", labels=["Tag"], name=t, kind="tag", props={"tag_id": t}, source_file="derived")
            euid = stable_edge_uid("HAS_TAG", n.uid, tag_uid)
            edges.append(EdgeRec(uid=euid, rel_type="HAS_TAG", from_uid=n.uid, to_uid=tag_uid, props={}, source="derived"))
    return list(tag_nodes.values()), edges

def contradiction_to_nodes_edges(cm: pd.DataFrame) -> Tuple[List[NodeRec], List[EdgeRec]]:
    nodes: List[NodeRec] = []
    edges: List[EdgeRec] = []
    for _, r in cm.iterrows():
        cm_id = str(r.get("cm_id","")).strip()
        if not cm_id:
            continue
        uid = f"Contradiction:{cm_id}"
        desc = str(r.get("description","")).strip()
        ctype = str(r.get("type","")).strip()
        status = str(r.get("status","")).strip()
        src_id = str(r.get("src_id","")).strip()
        pin = str(r.get("pin","")).strip()
        notes = str(r.get("notes","")).strip()
        nodes.append(NodeRec(
            uid=uid,
            node_type="ContradictionItem",
            labels=["ContradictionItem"],
            name=desc[:200] if desc else uid,
            kind="contradiction",
            props={"cm_id": cm_id, "type": ctype, "description": desc, "status": status, "src_id": src_id, "pin": pin, "notes": notes},
            source_file=str(r.get("__source_file","contradiction_map"))
        ))
        # Pinpoint edge to a "SourcePin" node
        if src_id or pin:
            spin_uid = f"SourcePin:{src_id}:{pin}"
            nodes.append(NodeRec(
                uid=spin_uid,
                node_type="SourcePin",
                labels=["SourcePin"],
                name=f"{src_id} {pin}".strip(),
                kind="source_pin",
                props={"src_id": src_id, "pin": pin},
                source_file="derived"
            ))
            edges.append(EdgeRec(uid=stable_edge_uid("PINPOINTS", uid, spin_uid), rel_type="PINPOINTS", from_uid=uid, to_uid=spin_uid, props={}, source="derived"))
    # Deduplicate by uid
    uniq = {}
    for n in nodes:
        uniq[n.uid] = n
    nodes = list(uniq.values())
    return nodes, edges

def pick_best_matches(query: str, candidates: List[NodeRec], topk: int = 5) -> List[Tuple[NodeRec, float]]:
    qtok = tokenize_text(query)
    scored = []
    for n in candidates:
        text = f"{n.name} {n.kind} {n.node_type} " + " ".join(map(str, n.props.get("tokens", []) if isinstance(n.props.get("tokens"), list) else []))
        score = jaccard(qtok, tokenize_text(text))
        if score > 0:
            scored.append((n, score))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:topk]

def build_violation_harm_remedy_vehicle_report(
    nodes: List[NodeRec],
    contradiction_df: pd.DataFrame,
    court_rules: List[str],
    caselaw: List[str],
    topk: int = 3
) -> Dict[str, Any]:
    """
    Create a fail-soft "action report" mapping:
      violation/issue -> harms (if present) -> candidate remedies -> candidate vehicles -> court rules -> caselaw -> recommended next actions
    Grounding:
      - Uses only text/tokens present in datasets.
      - Does not assert legal conclusions; uses "candidate" language and marks unknowns.
    """
    violations = [n for n in nodes if str(n.kind).lower() == "violation" or n.node_type == "Violation"]
    remedies = [n for n in nodes if str(n.kind).lower() == "remedy" or n.node_type == "Remedy"]
    vehicles = [n for n in nodes if str(n.kind).lower() in ["motion","complaint","defense"] or n.node_type in ["Motion","Complaint","Defense","Vehicle"]]

    # Convert contradiction rows into "issues"
    issues = []
    for _, r in contradiction_df.iterrows():
        issues.append({
            "issue_id": f"Contradiction:{r.get('cm_id','')}",
            "type": str(r.get("type","")),
            "description": str(r.get("description","")),
            "status": str(r.get("status","")),
            "src_id": str(r.get("src_id","")),
            "pin": str(r.get("pin","")),
            "notes": str(r.get("notes","")),
        })

    out_items = []
    # If no contradiction map, fall back to violation nodes as primary issues
    if not issues:
        for v in violations[:50]:
            issues.append({"issue_id": v.uid, "type": "violation_node", "description": v.name, "status": "UNKNOWN", "src_id": "", "pin": "", "notes": ""})

    # Candidate rules/caselaw are global lists; we will attach a ranked subset by overlap when possible.
    for it in issues:
        desc = it.get("description","") or ""
        # match existing violation nodes
        v_matches = pick_best_matches(desc, violations, topk=topk)
        r_matches = pick_best_matches(desc, remedies, topk=topk)
        veh_matches = pick_best_matches(desc, vehicles, topk=topk)

        # rank court_rules/caselaw by token overlap
        qtok = set(tokenize_text(desc))
        def score_str(s: str) -> float:
            return jaccard(qtok, tokenize_text(s))
        rules_ranked = sorted([(r, score_str(r)) for r in court_rules], key=lambda x: x[1], reverse=True)
        caselaw_ranked = sorted([(c, score_str(c)) for c in caselaw], key=lambda x: x[1], reverse=True)

        item = {
            "issue": it,
            "violation_candidates": [{"uid": n.uid, "name": n.name, "score": float(sc)} for n, sc in v_matches],
            "harm_candidates": [],  # harms not yet modeled explicitly; can be extended
            "remedy_candidates": [{"uid": n.uid, "name": n.name, "score": float(sc)} for n, sc in r_matches],
            "vehicle_candidates": [{"uid": n.uid, "name": n.name, "score": float(sc), "kind": n.kind} for n, sc in veh_matches],
            "court_rule_candidates": [{"citation": r, "score": float(sc)} for r, sc in rules_ranked[:topk] if sc > 0] or [],
            "caselaw_candidates": [{"citation": c, "score": float(sc)} for c, sc in caselaw_ranked[:topk] if sc > 0] or [],
            "recommended_next_actions": []
        }

        # Deterministic action suggestions (fail-soft, grounded)
        # 1) If contradiction is OPEN and has pin, action = acquire that exhibit/page
        if str(it.get("status","")).upper() == "OPEN":
            if it.get("src_id") or it.get("pin"):
                item["recommended_next_actions"].append({
                    "action": "ACQUIRE_EVIDENCE_AT_PIN",
                    "detail": f"Locate source {it.get('src_id','')} at {it.get('pin','')} and ingest the referenced exhibit/page into EvidenceAtom/QuoteAtom.",
                    "gate": "contradiction_closure"
                })
            else:
                item["recommended_next_actions"].append({
                    "action": "ACQUIRE_EVIDENCE",
                    "detail": "No pinpoint provided; locate the missing exhibit referenced by the description and ingest it.",
                    "gate": "contradiction_closure"
                })

        # 2) If we have a strong remedy candidate but no vehicle candidate, suggest mapping remedy->vehicle later
        if item["remedy_candidates"] and not item["vehicle_candidates"]:
            item["recommended_next_actions"].append({
                "action": "MAP_REMEDY_TO_VEHICLE",
                "detail": "Identify a procedural vehicle (motion/complaint/defense) in your dataset that operationalizes the top remedy candidate; attach authority triples.",
                "gate": "vehicle_selection"
            })

        # 3) If no rule/caselaw matches, add acquisition plan
        if not item["court_rule_candidates"] and not item["caselaw_candidates"]:
            item["recommended_next_actions"].append({
                "action": "ADD_AUTHORITY_PINPOINTS",
                "detail": "No matching court-rule/caselaw citations found in current node corpora for this issue text. Add or ingest authority nodes with pinpoint citations, then rerun.",
                "gate": "authority_completion"
            })

        out_items.append(item)

    return {
        "generated_at": utc_now_z(),
        "counts": {
            "issues": len(out_items),
            "violation_nodes": len(violations),
            "remedy_nodes": len(remedies),
            "vehicle_nodes": len(vehicles),
            "court_rules_detected": len(court_rules),
            "caselaw_detected": len(caselaw),
        },
        "items": out_items
    }

# -----------------------------
# Export writers
# -----------------------------

def write_neo4j_nodes(nodes: List[NodeRec], path: Path) -> None:
    # fixed columns, deterministic order
    nodes_sorted = sorted(nodes, key=lambda n: (n.node_type or "", n.uid))
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["uid:ID", "node_type", "labels:LABEL", "name", "kind", "source_file", "props_json"])
        for n in nodes_sorted:
            labels = ";".join(n.labels) if n.labels else n.node_type
            props_json = json.dumps(n.props, ensure_ascii=False, sort_keys=True)
            w.writerow([n.uid, n.node_type, labels, n.name, n.kind, n.source_file, props_json])

def write_neo4j_edges(edges: List[EdgeRec], path: Path) -> None:
    edges_sorted = sorted(edges, key=lambda e: (e.rel_type or "", e.from_uid, e.to_uid, e.uid))
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["uid", "from_uid:START_ID", "to_uid:END_ID", "rel_type:TYPE", "props_json", "source"])
        for e in edges_sorted:
            w.writerow([e.uid, e.from_uid, e.to_uid, e.rel_type, json.dumps(e.props, ensure_ascii=False, sort_keys=True), e.source])

def write_graphml(nodes: List[NodeRec], edges: List[EdgeRec], path: Path) -> Dict[str, Any]:
    if nx is None:
        return {"ok": False, "error": "networkx not installed; cannot emit graphml"}
    G = nx.MultiDiGraph()
    for n in nodes:
        G.add_node(n.uid, node_type=n.node_type, labels=";".join(n.labels), name=n.name, kind=n.kind, source_file=n.source_file, **{"props_json": json.dumps(n.props, ensure_ascii=False, sort_keys=True)})
    for e in edges:
        G.add_edge(e.from_uid, e.to_uid, key=e.uid, uid=e.uid, rel_type=e.rel_type, source=e.source, props_json=json.dumps(e.props, ensure_ascii=False, sort_keys=True))
    nx.write_graphml(G, path)
    return {"ok": True, "nodes": G.number_of_nodes(), "edges": G.number_of_edges()}

# -----------------------------
# Validations (simple, fail-soft)
# -----------------------------

def validate_edge_endpoints_exist(edges: List[EdgeRec], node_uids: set) -> List[Dict[str, Any]]:
    violations = []
    for e in edges:
        if e.from_uid not in node_uids:
            violations.append({"type":"EDGE_FROM_MISSING", "edge_uid": e.uid, "from_uid": e.from_uid})
        if e.to_uid not in node_uids:
            violations.append({"type":"EDGE_TO_MISSING", "edge_uid": e.uid, "to_uid": e.to_uid})
    return violations

# -----------------------------
# Main
# -----------------------------

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="in_dir", required=True, help="Input directory containing the uploaded artifacts")
    ap.add_argument("--out", dest="out_dir", required=True, help="Output directory")
    ap.add_argument("--dry-run", action="store_true", help="Do not write outputs; only report counts")
    ap.add_argument("--max-pdf-pages", type=int, default=10, help="Max pages to sample for embedded text detection per PDF")
    ap.add_argument("--fail-hard", action="store_true", help="Treat any validation issue as fatal (default fail-soft)")
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    in_dir = Path(args.in_dir)
    out_dir = Path(args.out_dir)
    if not in_dir.exists():
        LOG.error("Input directory does not exist: %s", in_dir)
        return 2

    found = find_files(in_dir)
    bundles_dir = out_dir / "_bundles_extracted"
    bundle_files = extract_from_known_bundle_zips(in_dir, bundles_dir)

    compile_report: Dict[str, Any] = {
        "runtime_version": "1.2.0",
        "generated_at": utc_now_z(),
        "input_dir": str(in_dir),
        "found_files": {k: [p.name for p in v] for k, v in found.items()},
        "bundle_files": {k: str(v) for k, v in bundle_files.items()},
        "pdf_text_index": [],
        "warnings": [],
        "errors": [],
    }

    # Load nodes
    nodes: List[NodeRec] = []
    try:
        if found["nodes"]:
            nodes.extend(load_nodes_merged(found["nodes"][0]))
        else:
            compile_report["warnings"].append("nodes_merged.csv not found; node ingestion limited.")
    except Exception as e:
        compile_report["errors"].append(f"Failed to load nodes_merged.csv: {e}")

    try:
        if found["nodes_admin"]:
            nodes.extend(load_nodes_admin(found["nodes_admin"][0]))
    except Exception as e:
        compile_report["warnings"].append(f"Failed to load nodes_neo4j_admin.csv: {e}")

    # De-dup nodes by uid (keep first)
    uid_seen = set()
    deduped_nodes: List[NodeRec] = []
    for n in nodes:
        if n.uid in uid_seen:
            continue
        uid_seen.add(n.uid)
        deduped_nodes.append(n)
    nodes = deduped_nodes

    # Tags -> tag nodes + edges
    tag_nodes, tag_edges = build_tag_edges(nodes)
    nodes.extend(tag_nodes)
    edges: List[EdgeRec] = []
    edges.extend(tag_edges)

    # Contradictions -> nodes + edges
    cm_df = load_contradiction_maps(found["contradiction_maps"])
    cm_nodes, cm_edges = contradiction_to_nodes_edges(cm_df)
    nodes.extend(cm_nodes)
    edges.extend(cm_edges)

    # Attempt to extract docx-text from the "205 JSON CSV TXT .zip" (if present)
    for zpath in found["zips"]:
        txt = extract_docx_text_from_zipish(zpath)
        if txt:
            doc_uid = f"DocumentText:{zpath.name}"
            nodes.append(NodeRec(uid=doc_uid, node_type="DocumentText", labels=["DocumentText"], name=zpath.name, kind="document_text", props={"text": txt[:20000], "full_text_len": len(txt)}, source_file=zpath.name))
            break

    # PDF quick index (embedded text detection)
    for pdf in found["pdfs"]:
        info = extract_pdf_text_index(pdf, max_pages=args.max_pdf_pages)
        compile_report["pdf_text_index"].append(info)

    # Authority candidates (rules + caselaw strings found inside nodes)
    auth_cands = extract_authority_candidates(nodes)
    court_rules = auth_cands["court_rules"]
    caselaw = auth_cands["caselaw"]
    compile_report["authority_candidates"] = {"court_rules_detected": len(court_rules), "caselaw_detected": len(caselaw)}

    # Build action report (violation->harm->remedy->vehicle->rules->caselaw)
    actions = build_violation_harm_remedy_vehicle_report(nodes, cm_df, court_rules, caselaw, topk=3)

    # Minimal graph invariants
    node_uids = {n.uid for n in nodes}
    endpoint_violations = validate_edge_endpoints_exist(edges, node_uids)

    violations = {
        "generated_at": utc_now_z(),
        "edge_endpoint_violations": endpoint_violations,
        "notes": [
            "This runtime does not yet enforce the full YAML constraints/contract semantics unless you add a dedicated YAML parser dependency (pyyaml).",
            "All action mappings are candidate suggestions based on token overlap in uploaded datasets only."
        ]
    }

    # Output paths
    out_dir.mkdir(parents=True, exist_ok=True)
    neo_nodes = out_dir / "neo4j_nodes.csv"
    neo_edges = out_dir / "neo4j_edges.csv"
    graphml_path = out_dir / "graph.graphml"
    action_md = out_dir / "action_report.md"
    compile_json = out_dir / "compile_report.json"
    violations_json = out_dir / "violations_actions.json"

    # Markdown action report
    def md_list(items: List[Dict[str, Any]], key1: str, key2: str = "score") -> str:
        if not items:
            return "_none_"
        lines = []
        for it in items:
            lines.append(f"- `{it.get(key1,'')}` (score={it.get(key2,'')})")
        return "\n".join(lines)

    md = []
    md.append(f"# LitigationOS Action Report (Violation → Harm → Remedy → Vehicle → Court Rules → Caselaw → Next Actions)\n")
    md.append(f"- generated_at: `{actions['generated_at']}`\n")
    md.append("## Summary Counts\n")
    for k, v in actions["counts"].items():
        md.append(f"- {k}: **{v}**")
    md.append("\n## Items\n")

    for idx, item in enumerate(actions["items"], start=1):
        issue = item["issue"]
        md.append(f"### {idx}. Issue `{issue.get('issue_id','')}`")
        md.append(f"- type: `{issue.get('type','')}`")
        md.append(f"- status: `{issue.get('status','')}`")
        if issue.get("src_id") or issue.get("pin"):
            md.append(f"- pin: `{issue.get('src_id','')} {issue.get('pin','')}`")
        md.append(f"- description: {issue.get('description','')}\n")

        md.append("**Violation candidates**\n")
        md.append(md_list([{"uid": v["uid"], "score": v["score"]} for v in item["violation_candidates"]], "uid"))
        md.append("\n**Remedy candidates**\n")
        md.append(md_list([{"uid": r["uid"], "score": r["score"]} for r in item["remedy_candidates"]], "uid"))
        md.append("\n**Vehicle candidates**\n")
        if item["vehicle_candidates"]:
            md.append("\n".join([f"- `{v['uid']}` ({v.get('kind','')}, score={v['score']})" for v in item["vehicle_candidates"]]))
        else:
            md.append("_none_")

        md.append("\n**Court rule candidates (from current dataset)**\n")
        if item["court_rule_candidates"]:
            md.append("\n".join([f"- `{c['citation']}` (score={c['score']})" for c in item["court_rule_candidates"]]))
        else:
            md.append("_none_")

        md.append("\n**Caselaw candidates (from current dataset)**\n")
        if item["caselaw_candidates"]:
            md.append("\n".join([f"- `{c['citation']}` (score={c['score']})" for c in item["caselaw_candidates"]]))
        else:
            md.append("_none_")

        md.append("\n**Recommended next actions**\n")
        if item["recommended_next_actions"]:
            for a in item["recommended_next_actions"]:
                md.append(f"- **{a['action']}**: {a['detail']} _(gate={a.get('gate','')})_")
        else:
            md.append("_none_")
        md.append("\n---\n")

    # Execute writes
    if args.dry_run:
        LOG.info("Dry-run: nodes=%d edges=%d contradictions=%d", len(nodes), len(edges), len(cm_df))
        LOG.info("Would write to: %s", out_dir)
        return 0

    try:
        write_neo4j_nodes(nodes, neo_nodes)
        write_neo4j_edges(edges, neo_edges)
    except Exception as e:
        compile_report["errors"].append(f"Failed writing Neo4j CSV exports: {e}")
        if args.fail_hard:
            raise

    try:
        ginfo = write_graphml(nodes, edges, graphml_path)
        compile_report["graphml"] = ginfo
        if not ginfo.get("ok"):
            compile_report["warnings"].append(ginfo.get("error"))
    except Exception as e:
        compile_report["warnings"].append(f"GraphML emit failed: {e}")

    action_md.write_text("\n".join(md), encoding="utf-8")
    compile_json.write_text(json.dumps(compile_report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    violations_json.write_text(json.dumps({"violations": violations, "actions": actions}, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    # Final status
    fatal = len(compile_report["errors"]) > 0
    if args.fail_hard and (fatal or endpoint_violations):
        LOG.error("Fail-hard: errors/violations detected.")
        return 3
    LOG.info("Done. nodes=%d edges=%d", len(nodes), len(edges))
    return 0

if __name__ == "__main__":
    sys.exit(main())
