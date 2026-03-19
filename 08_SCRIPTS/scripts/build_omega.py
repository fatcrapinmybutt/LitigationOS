#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_omega.py — ESD MASTER BLUEPRINT OMEGA builder / forger

Purpose
- Deterministically (re)generate an interactive HTML blueprint + SVG/PNG + DOT + Graph JSON.
- Merge/forge additional blueprint fragments (JSON) into ONE unified "OMEGA" graph.
- Optional "notes ingest": convert your plain-text directives into additional policy/taxonomy nodes.

Non-destructive
- Never deletes sources. Outputs go to a new output directory.

Fragment format (JSON)
{
  "meta": {... optional ...},
  "nodes": [{"id": "...", "label": "...", "category": "...", "cluster": "...", "tooltip": "..."}],
  "edges": [{"id":"...", "source":"...", "target":"...", "rel":"...", "label":"...", "category":"..."}]
}

Dependencies
- Python 3.9+
- graphviz 'dot' available on PATH (for svg/png)
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
import subprocess
import sys
import textwrap
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional


VERSION_DEFAULT = "v2026-01-26.0"


def _now_ts() -> str:
    return _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _die(msg: str, code: int = 2) -> None:
    print(f"[FATAL] {msg}", file=sys.stderr)
    raise SystemExit(code)


def _run(cmd: List[str]) -> Tuple[int, str, str]:
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return p.returncode, p.stdout, p.stderr


def _require_dot() -> None:
    rc, out, err = _run(["dot", "-V"])
    if rc != 0:
        _die("Graphviz 'dot' not found on PATH. Install Graphviz or ensure dot is accessible.")


def _dot_escape(s: str) -> str:
    return (s or "").replace("\\", "\\\\").replace('"', '\\"')


def base_graph(version: str) -> Dict[str, Any]:
    """Return the canonical base OMEGA graph."""
    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []

    def add_node(node_id: str, label: str, category: str, cluster: str, tooltip: str) -> None:
        nodes.append({
            "id": node_id,
            "label": label,
            "category": category,
            "cluster": cluster,
            "tooltip": tooltip,
        })

    def add_edge(src: str, dst: str, rel: str, label: str, category: str) -> None:
        edges.append({
            "id": f"{src}__{rel}__{dst}",
            "source": src,
            "target": dst,
            "rel": rel,
            "label": label,
            "category": category,
        })

    # === DATA SPINE (ERD) ===
    add_node("RUN", "RUN", "spine", "ERD", "Run metadata: ids, track, case_key, spec_version, timestamps.")
    add_node("ARTIFACT", "ARTIFACT", "spine", "ERD", "Universal artifact spine with kind/media/path/bytes and DERIVED_FROM.")
    add_node("EVENT_LOG", "EVENT_LOG", "spine", "ERD", "Append-only event stream; replay + provenance backbone.")
    add_node("CHECKPOINT", "CHECKPOINT", "spine", "ERD", "Stage checkpoints for resumable pipelines.")
    add_node("ANCHOR", "ANCHOR", "spine", "ERD", "Pinpoint selector: text offsets, media fragments, bbox, timecodes.")
    add_node("EVIDENCE_ATOM", "EVIDENCE_ATOM", "spine", "ERD", "Atomic evidence claim/statement with pinned location.")
    add_node("AUTHORITY_SNAPSHOT", "AUTHORITY_SNAPSHOT", "spine", "ERD", "Locked snapshot of Michigan authorities with effective date.")
    add_node("AUTHORITY_ATOM", "AUTHORITY_ATOM", "spine", "ERD", "Atomic authority unit: citation, binding level, text anchor.")
    add_node("PINPOINT", "PINPOINT", "spine", "ERD", "Pinpoint locator for authority atom; ties to anchors.")
    add_node("PROPOSITION", "PROPOSITION", "spine", "ERD", "Proposition: proposition_key + statement; cites pinpoints.")
    add_node("VEHICLE", "VEHICLE", "spine", "ERD", "Procedural vehicle/form binding: motion/form/order/request type.")
    add_node("FORM", "FORM", "spine", "ERD", "SCAO/FOC/local form binding (when applicable).")
    add_node("PROOF_OBLIGATION", "PROOF_OBLIGATION", "spine", "ERD", "Proof Obligation (PO): required pins + test; OPEN/PARTIAL/SATISFIED.")
    add_node("GATE_RESULT", "GATE_RESULT", "spine", "ERD", "Gate evaluation: PASS/FAIL/HOLD + reasons + UNSAT_CORE.")
    add_node("DRAFT_DOC", "DRAFT_DOC", "spine", "ERD", "Draft document artifact + trace map to evidence/propositions.")
    add_node("PACKET", "PACKET", "spine", "ERD", "Court packet: zip + manifest + service plan.")
    add_node("RELEASE", "RELEASE", "spine", "ERD", "Release: timestamped, attestable, reproducible packet delivery.")

    # === INFRA ===
    add_node("DRIVE_SCAN", "DRIVE_SCAN", "infra", "INFRA", "Drive scanning across allowed drives; excludes system files.")
    add_node("FS_WATCHER", "FS_WATCHER", "infra", "INFRA", "Filesystem watcher that triggers incremental harvest cycles.")
    add_node("BUCKET", "BUCKET", "infra", "INFRA", "File-type bucket classification (<=15 buckets).")
    add_node("OCR_BUCKET", "OCR_BUCKET", "infra", "INFRA", "Quarantine bucket for items needing OCR (status UNKNOWN until processed).")
    add_node("DEDUP_ENGINE", "DEDUP_ENGINE", "infra", "INFRA", "Dedup + provenance-preserving consolidation engine (append-only).")

    # === POLICY ===
    add_node("TRUTH_LOCK", "policy", "policy", "POLICY", "No invented facts; evidence atoms must include pins.")
    add_node("AUTH_LOCK", "policy", "policy", "POLICY", "Michigan-only authority snapshots; no out-of-snapshot propositions.")
    add_node("FORMS_FIRST", "policy", "policy", "POLICY", "Relief→Vehicle/Form→Rule/Std→Elements→POs→Deadlines→Service→Exhibits.")
    add_node("PCW_ADD", "policy", "policy", "POLICY", "Assurance-Driven Deliberation + PCW states for POs.")
    add_node("PCG_GATE", "policy", "policy", "POLICY", "Final Proof-Carrying Gate for irreversible actions (file/serve).")
    add_node("BUMPERS", "policy", "policy", "POLICY", "Soft stoppers: log blockers into traveling bumper ledger; keep progressing.")

    # === ENGINES ===
    add_node("INTAKE_ENGINE", "engine", "engine", "ENGINE", "Non-destructive intake: expand zips, inventory, provenance snapshot.")
    add_node("EXTRACT_ENGINE", "engine", "engine", "ENGINE", "Format extractors: PDF→text, DOCX→text, HTML parse, etc.")
    add_node("ATOMIZER", "engine", "engine", "ENGINE", "Atomization into EvidenceAtoms/AuthorityAtoms/OrderAtoms/ServiceAtoms.")
    add_node("ADVERSARIAL_MINER", "engine", "engine", "ENGINE", "Detect adversarial knowledge, negative statements, rights violations signals.")
    add_node("GRAPHIR_COMPILER", "engine", "engine", "ENGINE", "GraphIR: produce Neo4j import CSV + Cypher + constraints/indexes.")
    add_node("VALIDATOR", "engine", "engine", "ENGINE", "Schema + integrity validation; produces VRpt and UNSAT cores.")
    add_node("PCW_ENGINE", "engine", "engine", "ENGINE", "Compute PO states; attach evidence pins; generate acquisition tasks.")
    add_node("DRAFT_FACTORY", "engine", "engine", "ENGINE", "Generate court-ready drafts with trace maps.")
    add_node("PACKET_BUILDER", "engine", "engine", "ENGINE", "Bundle exhibits, manifests, service plan; produce packet zip.")
    add_node("RELEASE_ENGINE", "engine", "engine", "ENGINE", "Release + attestation; create deliverables and logs.")

    # === TAXONOMY ===
    add_node("MISCONDUCT_VECTOR", "taxonomy", "taxonomy", "TAXONOMY", "Bias/weaponization/retaliation vectors mapping: signals→proof→remedy.")
    add_node("ACTOR_MODEL", "taxonomy", "taxonomy", "TAXONOMY", "Judge/FOC/opponent actor models + failure modes.")
    add_node("EVENT_TO_MV_MAP", "taxonomy", "taxonomy", "TAXONOMY", "Event→MisconductVector mapping rules (machine-usable).")

    # === OUTPUTS ===
    add_node("DOCTYPE_REGISTRY_JSON", "DOCTYPE_REGISTRY.json", "output", "OUTPUTS", "Doctype registry: kinds, extractors, buckets, schemas.")
    add_node("EVENT_MV_MAPPING_JSON", "EVENT_TO_MV_MAPPING.json", "output", "OUTPUTS", "Mapping from harvested events to misconduct vectors.")
    add_node("BUMPER_QUERY_PACK", "BUMPER_QUERY_PACK", "output", "OUTPUTS", "Cypher query pack that surfaces stoppers/unsat cores and priorities.")
    add_node("BOOTSTRAP_BUNDLE", "BOOTSTRAP_BUNDLE", "output", "OUTPUTS", "Drop-in schema/ + queries/ bundle with registries and query packs.")
    add_node("CASE_STATE", "CASE_STATE", "output", "OUTPUTS", "<=25 lines: status + deltas; append-only cycle summary.")
    add_node("CYCLE_LEDGER", "CYCLE_LEDGER.jsonl", "output", "OUTPUTS", "Append-only per-cycle run ledger JSONL.")
    add_node("PROVENANCE_INDEX", "PROVENANCE_INDEX.json", "output", "OUTPUTS", "Deterministic provenance index for re-open recipes.")
    add_node("VALIDATION_REPORT", "VRpt.json", "output", "OUTPUTS", "Validation report; PASS required for PCG.")
    add_node("EXHIBIT_MATRIX", "EXHIBIT_MATRIX.csv", "output", "OUTPUTS", "Exhibit matrix with cover-page requirements + labels.")
    add_node("TIMELINE", "TIMELINE_bitemp.json", "output", "OUTPUTS", "Bi-temporal timeline index with evidence pins.")
    add_node("AUTH_TRIPLES", "AUTHORITY_TRIPLES.jsonl", "output", "OUTPUTS", "AuthorityTriples: proposition→authority→pinpoint.")
    add_node("CONTRADICTION_MAP", "CONTRADICTION_MAP.json", "output", "OUTPUTS", "ContradictionMap: statement clashes with pins.")
    add_node("SBNA", "SBNA.json", "output", "OUTPUTS", "Single Best Next Action computed from PO states and risk/benefit.")

    # === UI ===
    add_node("DASHBOARD_HTML", "DASHBOARD.html", "ui", "UI", "Interactive blueprint/map dashboards (HTML+SVG+JS).")
    add_node("NEO4J_BLOOM", "Neo4j Bloom", "ui", "UI", "Bloom perspective seeds + query library for interactive graph exploration.")
    add_node("EXPORTERS", "Exporters", "ui", "UI", "Export to PNG/SVG/JSON/CSV + query packs; deterministic outputs.")

    # ERD rels
    add_edge("RUN", "ARTIFACT", "HAS_ARTIFACT", "0..N", "spine_rel")
    add_edge("RUN", "EVENT_LOG", "HAS_EVENT_LOG", "1", "spine_rel")
    add_edge("RUN", "CHECKPOINT", "HAS_CHECKPOINT", "0..N", "spine_rel")
    add_edge("ARTIFACT", "ARTIFACT", "DERIVED_FROM", "DERIVED_FROM", "spine_rel")
    add_edge("ARTIFACT", "EVIDENCE_ATOM", "YIELDS", "0..N", "spine_rel")
    add_edge("EVIDENCE_ATOM", "ANCHOR", "PINNED_BY", "0..1", "spine_rel")
    add_edge("RUN", "AUTHORITY_SNAPSHOT", "USES_SNAPSHOT", "0..1", "spine_rel")
    add_edge("AUTHORITY_SNAPSHOT", "AUTHORITY_ATOM", "CONTAINS", "0..N", "spine_rel")
    add_edge("AUTHORITY_ATOM", "PINPOINT", "HAS_PINPOINT", "0..N", "spine_rel")
    add_edge("PROPOSITION", "PINPOINT", "CITES", "CITES", "spine_rel")
    add_edge("VEHICLE", "FORM", "BINDS_FORM", "0..1", "spine_rel")
    add_edge("VEHICLE", "PROOF_OBLIGATION", "REQUIRES_PO", "0..N", "spine_rel")
    add_edge("PROPOSITION", "PROOF_OBLIGATION", "SUPPORTS_PO", "REQUIRES", "spine_rel")
    add_edge("EVIDENCE_ATOM", "PROOF_OBLIGATION", "SATISFIES_PO", "SATISFIES", "spine_rel")
    add_edge("PROOF_OBLIGATION", "GATE_RESULT", "DRIVES_GATE", "drives eval", "spine_rel")
    add_edge("VEHICLE", "DRAFT_DOC", "PRODUCES_DRAFT", "produces", "spine_rel")
    add_edge("DRAFT_DOC", "PACKET", "INCLUDED_IN", "included in", "spine_rel")
    add_edge("PACKET", "RELEASE", "RELEASED_AS", "0..N", "spine_rel")

    # Policy bindings
    for pol in ["TRUTH_LOCK", "AUTH_LOCK", "FORMS_FIRST", "PCW_ADD", "PCG_GATE", "BUMPERS"]:
        add_edge(pol, "VALIDATOR", "GOVERNS", "governs", "policy_rel")
    add_edge("FORMS_FIRST", "PCW_ENGINE", "DRIVES", "drives", "policy_rel")
    add_edge("PCW_ADD", "PCW_ENGINE", "ENABLES", "enables", "policy_rel")
    add_edge("PCG_GATE", "RELEASE_ENGINE", "GATES", "gates", "policy_rel")
    add_edge("BUMPERS", "EVENT_LOG", "APPENDS_TO", "appends to", "policy_rel")

    # Infra + engines
    add_edge("DRIVE_SCAN", "INTAKE_ENGINE", "FEEDS", "feeds", "infra_rel")
    add_edge("FS_WATCHER", "INTAKE_ENGINE", "TRIGGERS", "triggers", "infra_rel")
    add_edge("INTAKE_ENGINE", "EXTRACT_ENGINE", "CALLS", "calls", "engine_rel")
    add_edge("EXTRACT_ENGINE", "ATOMIZER", "CALLS", "calls", "engine_rel")
    add_edge("ATOMIZER", "ADVERSARIAL_MINER", "CALLS", "calls", "engine_rel")
    add_edge("ADVERSARIAL_MINER", "MISCONDUCT_VECTOR", "CLASSIFIES", "classifies", "taxonomy_rel")
    add_edge("ADVERSARIAL_MINER", "ACTOR_MODEL", "SCORES_AGAINST", "scores", "taxonomy_rel")
    add_edge("ATOMIZER", "GRAPHIR_COMPILER", "FEEDS", "feeds", "engine_rel")
    add_edge("GRAPHIR_COMPILER", "NEO4J_BLOOM", "SEEDS", "seeds", "ui_rel")
    add_edge("GRAPHIR_COMPILER", "EXPORTERS", "OUTPUTS", "outputs", "ui_rel")
    add_edge("GRAPHIR_COMPILER", "VALIDATOR", "SUBMITS", "submits", "engine_rel")
    add_edge("VALIDATOR", "PCW_ENGINE", "UNBLOCKS", "unblocks", "engine_rel")
    add_edge("PCW_ENGINE", "DRAFT_FACTORY", "UNBLOCKS", "unblocks", "engine_rel")
    add_edge("DRAFT_FACTORY", "PACKET_BUILDER", "FEEDS", "feeds", "engine_rel")
    add_edge("PACKET_BUILDER", "RELEASE_ENGINE", "FEEDS", "feeds", "engine_rel")

    # Bucketing + OCR + dedup
    add_edge("INTAKE_ENGINE", "BUCKET", "ASSIGNS", "assigns", "infra_rel")
    add_edge("EXTRACT_ENGINE", "OCR_BUCKET", "QUARANTINES", "quarantines", "infra_rel")
    add_edge("DEDUP_ENGINE", "ARTIFACT", "CONSOLIDATES", "consolidates", "infra_rel")

    # Engine → spine entities
    add_edge("INTAKE_ENGINE", "RUN", "CREATES", "creates", "engine_to_spine")
    add_edge("INTAKE_ENGINE", "ARTIFACT", "CREATES", "creates", "engine_to_spine")
    add_edge("INTAKE_ENGINE", "EVENT_LOG", "APPENDS", "appends", "engine_to_spine")
    add_edge("EXTRACT_ENGINE", "ARTIFACT", "DERIVES", "derives", "engine_to_spine")
    add_edge("ATOMIZER", "EVIDENCE_ATOM", "CREATES", "creates", "engine_to_spine")
    add_edge("ATOMIZER", "AUTHORITY_ATOM", "CREATES", "creates", "engine_to_spine")
    add_edge("ATOMIZER", "PROPOSITION", "CREATES", "creates", "engine_to_spine")
    add_edge("PCW_ENGINE", "PROOF_OBLIGATION", "EVALUATES", "evaluates", "engine_to_spine")
    add_edge("VALIDATOR", "GATE_RESULT", "PRODUCES", "produces", "engine_to_spine")
    add_edge("DRAFT_FACTORY", "DRAFT_DOC", "PRODUCES", "produces", "engine_to_spine")
    add_edge("PACKET_BUILDER", "PACKET", "PRODUCES", "produces", "engine_to_spine")
    add_edge("RELEASE_ENGINE", "RELEASE", "PRODUCES", "produces", "engine_to_spine")

    # Outputs
    add_edge("GRAPHIR_COMPILER", "DOCTYPE_REGISTRY_JSON", "EMITS", "emits", "output_rel")
    add_edge("ADVERSARIAL_MINER", "EVENT_MV_MAPPING_JSON", "EMITS", "emits", "output_rel")
    add_edge("GRAPHIR_COMPILER", "BUMPER_QUERY_PACK", "EMITS", "emits", "output_rel")
    add_edge("BOOTSTRAP_BUNDLE", "DOCTYPE_REGISTRY_JSON", "CONTAINS", "contains", "output_rel")
    add_edge("BOOTSTRAP_BUNDLE", "EVENT_MV_MAPPING_JSON", "CONTAINS", "contains", "output_rel")
    add_edge("BOOTSTRAP_BUNDLE", "BUMPER_QUERY_PACK", "CONTAINS", "contains", "output_rel")

    add_edge("RELEASE_ENGINE", "CASE_STATE", "EMITS", "emits", "output_rel")
    add_edge("RELEASE_ENGINE", "CYCLE_LEDGER", "EMITS", "emits", "output_rel")
    add_edge("RELEASE_ENGINE", "PROVENANCE_INDEX", "EMITS", "emits", "output_rel")
    add_edge("VALIDATOR", "VALIDATION_REPORT", "EMITS", "emits", "output_rel")
    add_edge("PACKET_BUILDER", "EXHIBIT_MATRIX", "EMITS", "emits", "output_rel")
    add_edge("PCW_ENGINE", "TIMELINE", "EMITS", "emits", "output_rel")
    add_edge("ATOMIZER", "AUTH_TRIPLES", "EMITS", "emits", "output_rel")
    add_edge("ATOMIZER", "CONTRADICTION_MAP", "EMITS", "emits", "output_rel")
    add_edge("PCW_ENGINE", "SBNA", "EMITS", "emits", "output_rel")

    meta = {
        "version": version,
        "generated_at": _now_ts(),
        "node_count": len(nodes),
        "edge_count": len(edges),
        "source": "base_graph()",
    }
    return {"meta": meta, "nodes": nodes, "edges": edges}


def _validate_graph(g: Dict[str, Any], src: str) -> None:
    if not isinstance(g, dict):
        _die(f"{src}: graph must be a JSON object")
    if "nodes" not in g or "edges" not in g:
        _die(f"{src}: graph must contain 'nodes' and 'edges'")
    if not isinstance(g["nodes"], list) or not isinstance(g["edges"], list):
        _die(f"{src}: 'nodes' and 'edges' must be lists")

    node_ids = set()
    for n in g["nodes"]:
        if not isinstance(n, dict) or "id" not in n:
            _die(f"{src}: each node must be an object with an 'id'")
        nid = str(n["id"]).strip()
        if not nid:
            _die(f"{src}: node id cannot be empty")
        if nid in node_ids:
            _die(f"{src}: duplicate node id: {nid}")
        node_ids.add(nid)

    edge_ids = set()
    for e in g["edges"]:
        if not isinstance(e, dict) or "id" not in e or "source" not in e or "target" not in e:
            _die(f"{src}: each edge must have 'id','source','target'")
        eid = str(e["id"]).strip()
        if not eid:
            _die(f"{src}: edge id cannot be empty")
        if eid in edge_ids:
            _die(f"{src}: duplicate edge id: {eid}")
        edge_ids.add(eid)


def load_fragment(path: Path) -> Dict[str, Any]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        _die(f"Failed to read fragment JSON: {path} ({e})")
    _validate_graph(raw, str(path))
    # normalize fields
    for n in raw["nodes"]:
        n.setdefault("label", n["id"])
        n.setdefault("category", "policy")
        n.setdefault("cluster", "POLICY")
        n.setdefault("tooltip", "")
    for e in raw["edges"]:
        e.setdefault("rel", "RELATED_TO")
        e.setdefault("label", e.get("rel", "RELATED_TO"))
        e.setdefault("category", "spine_rel")
    return raw


def merge_graphs(base: Dict[str, Any], fragments: List[Dict[str, Any]]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Merge by id.
    - Nodes: keep base on conflict; record diff.
    - Edges: dedupe by id; keep first.
    """
    merged = {"meta": dict(base.get("meta", {})), "nodes": [], "edges": []}
    report = {"added_nodes": [], "added_edges": [], "node_conflicts": [], "edge_conflicts": []}

    node_map: Dict[str, Dict[str, Any]] = {n["id"]: dict(n) for n in base["nodes"]}
    edge_map: Dict[str, Dict[str, Any]] = {e["id"]: dict(e) for e in base["edges"]}

    for frag in fragments:
        for n in frag["nodes"]:
            nid = n["id"]
            if nid not in node_map:
                node_map[nid] = dict(n)
                report["added_nodes"].append(nid)
            else:
                # conflict check: any meaningful field differs
                base_n = node_map[nid]
                diffs = {k: (base_n.get(k), n.get(k)) for k in ["label","category","cluster","tooltip"] if base_n.get(k) != n.get(k)}
                if diffs:
                    report["node_conflicts"].append({"id": nid, "diffs": diffs, "kept": "base"})

        for e in frag["edges"]:
            eid = e["id"]
            if eid not in edge_map:
                edge_map[eid] = dict(e)
                report["added_edges"].append(eid)
            else:
                base_e = edge_map[eid]
                diffs = {k: (base_e.get(k), e.get(k)) for k in ["source","target","rel","label","category"] if base_e.get(k) != e.get(k)}
                if diffs:
                    report["edge_conflicts"].append({"id": eid, "diffs": diffs, "kept": "base"})

    merged["nodes"] = sorted(node_map.values(), key=lambda x: x["id"])
    merged["edges"] = sorted(edge_map.values(), key=lambda x: (x["source"], x["target"], x.get("rel","")))

    merged["meta"]["merged_at"] = _now_ts()
    merged["meta"]["merged_node_count"] = len(merged["nodes"])
    merged["meta"]["merged_edge_count"] = len(merged["edges"])
    merged["meta"]["fragment_count"] = len(fragments)

    return merged, report


def ingest_notes(graph: Dict[str, Any], notes_path: Path) -> Dict[str, Any]:
    """
    Convert plain text into additional nodes (NOTE_0001...), attempting to classify
    into clusters/categories using keyword heuristics (deterministic).
    """
    txt = notes_path.read_text(encoding="utf-8", errors="replace")
    lines = [ln.strip() for ln in txt.splitlines() if ln.strip()]
    if not lines:
        return graph

    existing_ids = {n["id"] for n in graph["nodes"]}
    note_nodes: List[Dict[str, Any]] = []
    note_edges: List[Dict[str, Any]] = []

    def classify(line: str) -> Tuple[str, str]:
        u = line.upper()
        if any(k in u for k in ["MV", "MISCONDUCT", "BIAS", "RETALIAT", "PPO", "CONTEMPT"]):
            return "taxonomy", "TAXONOMY"
        if any(k in u for k in ["ENGINE", "COMPILER", "VALIDATOR", "HARVEST", "WATCHER", "SCANNER"]):
            return "engine", "ENGINE"
        if any(k in u for k in ["DRIVE", "FOLDER", "BUCKET", "DEDUP", "OCR"]):
            return "infra", "INFRA"
        return "policy", "POLICY"

    # stable sequence based on existing NOTE_* count
    note_start = 1 + sum(1 for i in existing_ids if str(i).startswith("NOTE_"))
    seq = note_start

    for line in lines:
        nid = f"NOTE_{seq:04d}"
        seq += 1
        if nid in existing_ids:
            continue
        cat, cl = classify(line)
        note_nodes.append({
            "id": nid,
            "label": nid,
            "category": cat,
            "cluster": cl,
            "tooltip": line,
        })
        # attach to closest policy nodes when detected
        u = line.upper()
        anchors = []
        if "TRUTH" in u or "NOINV" in u:
            anchors.append("TRUTH_LOCK")
        if "AUTH" in u or "MICHIGAN" in u:
            anchors.append("AUTH_LOCK")
        if "FORM" in u or "FORMSFIRST" in u:
            anchors.append("FORMS_FIRST")
        if "PCW" in u or "ADD" in u:
            anchors.append("PCW_ADD")
        if "PCG" in u or "GATE" in u:
            anchors.append("PCG_GATE")
        if "BUMPER" in u or "STOPPER" in u:
            anchors.append("BUMPERS")

        for a in anchors:
            if a in existing_ids:
                eid = f"{a}__NOTES__{nid}"
                note_edges.append({
                    "id": eid,
                    "source": a,
                    "target": nid,
                    "rel": "NOTES",
                    "label": "notes",
                    "category": "policy_rel",
                })

    if note_nodes:
        graph = dict(graph)
        graph["nodes"] = list(graph["nodes"]) + note_nodes
        graph["edges"] = list(graph["edges"]) + note_edges
        graph["meta"] = dict(graph.get("meta", {}))
        graph["meta"]["notes_ingested_from"] = str(notes_path)
        graph["meta"]["notes_line_count"] = len(lines)
        graph["meta"]["notes_node_count"] = len(note_nodes)
    return graph


CAT_STYLE = {
    "spine": {"shape": "box", "style": "rounded,filled", "fillcolor": "#eef6ff"},
    "policy": {"shape": "hexagon", "style": "filled", "fillcolor": "#fff4e6"},
    "engine": {"shape": "component", "style": "filled", "fillcolor": "#eefbf0"},
    "output": {"shape": "folder", "style": "filled", "fillcolor": "#f4f0ff"},
    "taxonomy": {"shape": "diamond", "style": "filled", "fillcolor": "#fff0f0"},
    "infra": {"shape": "cylinder", "style": "filled", "fillcolor": "#f0f7ff"},
    "ui": {"shape": "tab", "style": "filled", "fillcolor": "#f2f2f2"},
}

CLUSTER_LABELS = {
    "ERD": "DATA SPINE (ERD)",
    "ENGINE": "ENGINES",
    "POLICY": "POLICY / GOVERNANCE",
    "OUTPUTS": "OUTPUT ARTIFACTS",
    "TAXONOMY": "TAXONOMY / ADVERSARIAL MODELS",
    "INFRA": "INFRA / DRIVE + WATCHER",
    "UI": "UI / EXPLORATION",
}


def build_dot(graph: Dict[str, Any]) -> str:
    by_cluster: Dict[str, List[Dict[str, Any]]] = {}
    for n in graph["nodes"]:
        by_cluster.setdefault(n.get("cluster", "POLICY"), []).append(n)
    for cl in by_cluster:
        by_cluster[cl] = sorted(by_cluster[cl], key=lambda x: x["id"])

    cluster_order = ["POLICY", "INFRA", "ENGINE", "TAXONOMY", "ERD", "OUTPUTS", "UI"]
    # include any extra clusters at the end
    extra = [c for c in sorted(by_cluster.keys()) if c not in cluster_order]
    cluster_order += extra

    edges_sorted = sorted(graph["edges"], key=lambda e: (e["source"], e["target"], e.get("rel", "")))

    lines = []
    lines.append('digraph ESD_MASTER_BLUEPRINT_OMEGA {')
    lines.append('  graph [rankdir=LR, splines=true, overlap=false, fontsize=14, fontname="Helvetica"];')
    lines.append('  node [fontname="Helvetica", fontsize=12];')
    lines.append('  edge [fontname="Helvetica", fontsize=10, arrowsize=0.8];')
    lines.append('')

    for cl in cluster_order:
        if cl not in by_cluster:
            continue
        lines.append(f'  subgraph cluster_{re.sub(r"[^a-z0-9_]+","_",cl.lower())} {{')
        lines.append('    style="rounded";')
        lines.append('    color="#999999";')
        lines.append(f'    label="{_dot_escape(CLUSTER_LABELS.get(cl, cl))}";')
        for n in by_cluster[cl]:
            st = CAT_STYLE.get(n.get("category", "policy"), {"shape": "box", "style": "filled", "fillcolor": "#ffffff"})
            attrs = {
                "label": n.get("label", n["id"]),
                "shape": st["shape"],
                "style": st["style"],
                "fillcolor": st["fillcolor"],
                "tooltip": n.get("tooltip", ""),
                "id": f"node_{n['id']}",
                "class": f"node cat_{n.get('category','policy')} cl_{cl}",
                "URL": "javascript:void(0)",
                "target": "_self",
            }
            attr_str = ", ".join([f'{k}="{_dot_escape(str(v))}"' for k, v in attrs.items()])
            lines.append(f'    "{n["id"]}" [{attr_str}];')
        lines.append('  }')
        lines.append('')

    for e in edges_sorted:
        attrs = {
            "label": e.get("label", e.get("rel", "RELATED_TO")),
            "tooltip": e.get("rel", "RELATED_TO"),
            "id": f"edge_{e['id']}",
            "class": f"edge cat_{e.get('category','spine_rel')} rel_{re.sub(r'[^A-Za-z0-9_]+','_',e.get('rel','RELATED_TO'))}",
        }
        attr_str = ", ".join([f'{k}="{_dot_escape(str(v))}"' for k, v in attrs.items()])
        lines.append(f'  "{e["source"]}" -> "{e["target"]}" [{attr_str}];')

    lines.append('}')
    return "\n".join(lines)


def svg_inline(svg_text: str) -> str:
    m = re.search(r"(<svg[\\s\\S]*</svg>)", svg_text)
    return m.group(1) if m else svg_text


def build_html(version: str, stamp: str, graph: Dict[str, Any], dot_text: str, svg_text: str) -> str:
    svg_in = svg_inline(svg_text)
    node_count = len(graph["nodes"])
    edge_count = len(graph["edges"])
    dot_embedded = _dot_escape(dot_text)

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>ESD MASTER BLUEPRINT OMEGA — {version}</title>
<style>
  :root {{ --bg:#0b0f14; --panel:#111826; --panel2:#0f172a; --fg:#e5e7eb; --muted:#94a3b8; --border:#1f2937; }}
  html,body {{ height:100%; margin:0; background:var(--bg); color:var(--fg); font-family: ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial; }}
  .app {{ display:grid; grid-template-columns: 360px 1fr; height:100vh; }}
  .side {{ background:var(--panel); border-right:1px solid var(--border); padding:14px; overflow:auto; }}
  .main {{ position:relative; overflow:hidden; }}
  h1 {{ font-size:14px; margin:0 0 10px; letter-spacing:0.4px; }}
  .meta {{ font-size:12px; color:var(--muted); line-height:1.35; margin-bottom:12px; }}
  .box {{ background:var(--panel2); border:1px solid var(--border); border-radius:10px; padding:10px; margin:10px 0; }}
  .row {{ display:flex; gap:8px; align-items:center; }}
  input[type="text"] {{ width:100%; padding:10px; border-radius:10px; border:1px solid var(--border); background:#0b1220; color:var(--fg); outline:none; }}
  button {{ width:100%; padding:10px; border-radius:10px; border:1px solid var(--border); background:#0b1220; color:var(--fg); cursor:pointer; }}
  button:hover {{ border-color:#334155; }}
  .btns {{ display:grid; grid-template-columns:1fr 1fr; gap:8px; }}
  .checks {{ display:grid; grid-template-columns:1fr; gap:6px; }}
  label {{ font-size:12px; color:var(--fg); }}
  .small {{ font-size:11px; color:var(--muted); }}
  .kbd {{ font-family: ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,monospace; font-size:11px; color:#cbd5e1; }}
  .hint {{ font-size:11px; color:var(--muted); line-height:1.35; }}
  .svgWrap {{ position:absolute; inset:0; overflow:hidden; }}
  .svgWrap svg {{ width:100%; height:100%; }}
  .dim {{ opacity:0.12 !important; }}
  .hi {{ opacity:1 !important; filter: drop-shadow(0 0 6px rgba(34,197,94,0.35)); }}
  .edgeHi path {{ stroke-width:2.6px !important; }}
  g.node ellipse, g.node polygon, g.node path {{ stroke:#cbd5e1; }}
  g.edge path {{ stroke:#94a3b8; }}
  g.edge polygon {{ fill:#94a3b8; stroke:#94a3b8; }}
  text {{ fill:#e5e7eb; }}
  .hidden {{ display:none !important; }}
  .status {{ font-size:12px; line-height:1.35; color:var(--muted); padding:8px 10px; border-radius:10px; border:1px solid var(--border); background:#0b1220; }}
  .status b {{ color:var(--fg); }}
</style>
</head>
<body>
<div class="app">
  <div class="side">
    <h1>ESD MASTER BLUEPRINT OMEGA</h1>
    <div class="meta">
      <div><span class="kbd">{version}</span></div>
      <div>Generated: <span class="kbd">{stamp}</span></div>
      <div>Nodes: <span class="kbd">{node_count}</span> · Edges: <span class="kbd">{edge_count}</span></div>
    </div>

    <div class="box">
      <div class="row" style="margin-bottom:8px;">
        <input id="search" type="text" placeholder="Search node id/label (e.g., PROOF_OBLIGATION)"/>
      </div>
      <div class="btns">
        <button id="btnReset">Reset View</button>
        <button id="btnClear">Clear Highlight</button>
      </div>
      <div style="height:8px;"></div>
      <div class="btns">
        <button id="btnExportJSON">Export Graph JSON</button>
        <button id="btnExportDOT">Export DOT</button>
      </div>
      <div style="height:8px;"></div>
      <div class="hint">Click a node to highlight neighbors. Drag to pan. Wheel to zoom. Search + Enter to jump. Double-click node to center.</div>
    </div>

    <div class="box">
      <div class="small" style="margin-bottom:6px;"><b>Cluster filters</b></div>
      <div id="clusterChecks" class="checks"></div>
    </div>

    <div class="box">
      <div class="small" style="margin-bottom:6px;"><b>Category filters</b></div>
      <div id="catChecks" class="checks"></div>
    </div>

    <div class="status" id="status"><b>Status:</b> Ready. No node selected.</div>
  </div>

  <div class="main">
    <div class="svgWrap" id="svgWrap">
      {svg_in}
    </div>
  </div>
</div>

<script>
const GRAPH = {json.dumps(graph)};
</script>

<script>
(function() {{
  const svgWrap = document.getElementById('svgWrap');
  const svg = svgWrap.querySelector('svg');
  const status = document.getElementById('status');
  const search = document.getElementById('search');

  function ensureViewBox() {{
    if (!svg.getAttribute('viewBox')) {{
      const w = parseFloat(svg.getAttribute('width')) || svg.clientWidth;
      const h = parseFloat(svg.getAttribute('height')) || svg.clientHeight;
      svg.setAttribute('viewBox', `0 0 ${{w}} ${{h}}`);
    }}
  }}
  ensureViewBox();
  const baseViewBox = svg.getAttribute('viewBox').split(/\\s+/).map(Number);
  let viewBox = baseViewBox.slice();
  function setViewBox(vb) {{ viewBox = vb.slice(); svg.setAttribute('viewBox', viewBox.join(' ')); }}
  function resetView() {{ setViewBox(baseViewBox); }}

  const nodeById = new Map(GRAPH.nodes.map(n => [n.id, n]));
  const labelIndex = new Map();
  for (const n of GRAPH.nodes) labelIndex.set((n.label||'').toUpperCase(), n.id);

  const outEdges = new Map(), inEdges = new Map(), edgeById = new Map();
  for (const e of GRAPH.edges) {{
    edgeById.set(e.id, e);
    if (!outEdges.has(e.source)) outEdges.set(e.source, []);
    if (!inEdges.has(e.target)) inEdges.set(e.target, []);
    outEdges.get(e.source).push(e.id);
    inEdges.get(e.target).push(e.id);
  }}

  const elNode = (id) => document.getElementById('node_' + id);
  const elEdge = (id) => document.getElementById('edge_' + id);

  let selected = null;

  function clearHighlight() {{
    selected = null;
    for (const n of GRAPH.nodes) {{
      const g = elNode(n.id);
      if (g) g.classList.remove('dim','hi');
    }}
    for (const e of GRAPH.edges) {{
      const g = elEdge(e.id);
      if (g) g.classList.remove('dim','hi','edgeHi');
    }}
    status.innerHTML = '<b>Status:</b> Ready. No node selected.';
  }}

  function highlightNode(id) {{
    const n = nodeById.get(id);
    if (!n) return;
    selected = id;

    const neighborNodes = new Set([id]);
    const neighborEdges = new Set();

    for (const eid of (outEdges.get(id) || [])) {{
      neighborEdges.add(eid);
      neighborNodes.add(edgeById.get(eid).target);
    }}
    for (const eid of (inEdges.get(id) || [])) {{
      neighborEdges.add(eid);
      neighborNodes.add(edgeById.get(eid).source);
    }}

    for (const nn of GRAPH.nodes) {{
      const g = elNode(nn.id);
      if (!g) continue;
      if (neighborNodes.has(nn.id)) {{ g.classList.remove('dim'); g.classList.add('hi'); }}
      else {{ g.classList.add('dim'); g.classList.remove('hi'); }}
    }}
    for (const ee of GRAPH.edges) {{
      const g = elEdge(ee.id);
      if (!g) continue;
      if (neighborEdges.has(ee.id)) {{ g.classList.remove('dim'); g.classList.add('hi','edgeHi'); }}
      else {{ g.classList.add('dim'); g.classList.remove('hi','edgeHi'); }}
    }}
    status.innerHTML = `<b>Status:</b> Selected <span class="kbd">${{id}}</span><br/><span class="small">${{(n.tooltip||'')}}</span>`;
  }}

  function centerOnNode(id) {{
    const g = elNode(id);
    if (!g) return;
    try {{
      const bb = g.getBBox();
      const pad = 60;
      setViewBox([bb.x - pad, bb.y - pad, Math.max(bb.width + pad*2, 200), Math.max(bb.height + pad*2, 120)]);
    }} catch (e) {{}}
  }}

  for (const n of GRAPH.nodes) {{
    const g = elNode(n.id);
    if (!g) continue;
    g.style.cursor = 'pointer';
    g.addEventListener('click', (ev) => {{ ev.preventDefault(); highlightNode(n.id); }});
    g.addEventListener('dblclick', (ev) => {{ ev.preventDefault(); centerOnNode(n.id); }});
  }}

  let isPanning = false;
  let start = null;

  function clientToSvg(x,y) {{
    const pt = svg.createSVGPoint(); pt.x = x; pt.y = y;
    return pt.matrixTransform(svg.getScreenCTM().inverse());
  }}

  svg.addEventListener('mousedown', (ev) => {{
    isPanning = true;
    start = {{ x: ev.clientX, y: ev.clientY, vb: viewBox.slice() }};
  }});
  window.addEventListener('mousemove', (ev) => {{
    if (!isPanning || !start) return;
    const p0 = clientToSvg(start.x, start.y);
    const p1 = clientToSvg(ev.clientX, ev.clientY);
    const dx = p0.x - p1.x, dy = p0.y - p1.y;
    setViewBox([start.vb[0] + dx, start.vb[1] + dy, start.vb[2], start.vb[3]]);
  }});
  window.addEventListener('mouseup', () => {{ isPanning = false; start = null; }});

  svg.addEventListener('wheel', (ev) => {{
    ev.preventDefault();
    const scale = (ev.deltaY < 0) ? 0.9 : 1.1;
    const p = clientToSvg(ev.clientX, ev.clientY);
    const [x,y,w,h] = viewBox;
    const nx = p.x - (p.x - x) * scale;
    const ny = p.y - (p.y - y) * scale;
    setViewBox([nx, ny, w*scale, h*scale]);
  }}, {{ passive:false }});

  const clusters = Array.from(new Set(GRAPH.nodes.map(n => n.cluster))).sort();
  const categories = Array.from(new Set(GRAPH.nodes.map(n => n.category))).sort();
  const visibleClusters = new Set(clusters);
  const visibleCats = new Set(categories);

  const clusterChecks = document.getElementById('clusterChecks');
  const catChecks = document.getElementById('catChecks');

  function mkCheck(container, name, set, onChange) {{
    const id = 'chk_' + name;
    const div = document.createElement('div');
    div.className = 'row';
    const cb = document.createElement('input');
    cb.type = 'checkbox'; cb.checked = true; cb.id = id;
    cb.addEventListener('change', () => {{ cb.checked ? set.add(name) : set.delete(name); onChange(); }});
    const lab = document.createElement('label'); lab.setAttribute('for', id); lab.textContent = name;
    div.appendChild(cb); div.appendChild(lab); container.appendChild(div);
  }}

  function applyFilters() {{
    const nodeVisible = new Map();
    for (const n of GRAPH.nodes) {{
      const ok = visibleClusters.has(n.cluster) && visibleCats.has(n.category);
      nodeVisible.set(n.id, ok);
      const g = elNode(n.id);
      if (g) g.classList.toggle('hidden', !ok);
    }}
    for (const e of GRAPH.edges) {{
      const ok = nodeVisible.get(e.source) && nodeVisible.get(e.target);
      const g = elEdge(e.id);
      if (g) g.classList.toggle('hidden', !ok);
    }}
    if (selected && !nodeVisible.get(selected)) clearHighlight();
  }}

  for (const cl of clusters) mkCheck(clusterChecks, cl, visibleClusters, applyFilters);
  for (const cat of categories) mkCheck(catChecks, cat, visibleCats, applyFilters);

  function resolveSearch(q) {{
    if (!q) return null;
    const u = q.trim().toUpperCase();
    if (nodeById.has(u)) return u;
    if (labelIndex.has(u)) return labelIndex.get(u);
    for (const n of GRAPH.nodes) {{
      if ((n.id||'').toUpperCase().includes(u) || (n.label||'').toUpperCase().includes(u)) return n.id;
    }}
    return null;
  }}

  function jumpTo(q) {{
    const id = resolveSearch(q);
    if (!id) {{ status.innerHTML = `<b>Status:</b> No match for <span class="kbd">${{q}}</span>`; return; }}
    highlightNode(id); centerOnNode(id);
  }}

  search.addEventListener('keydown', (ev) => {{ if (ev.key === 'Enter') jumpTo(search.value); }});
  document.getElementById('btnReset').addEventListener('click', () => resetView());
  document.getElementById('btnClear').addEventListener('click', () => clearHighlight());

  function downloadText(filename, text) {{
    const blob = new Blob([text], {{type:'text/plain'}});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = url; a.download = filename;
    document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url);
  }}
  document.getElementById('btnExportJSON').addEventListener('click', () => downloadText(`graph_omega_${version}.json`, JSON.stringify(GRAPH, null, 2)));
  document.getElementById('btnExportDOT').addEventListener('click', () => downloadText(`ESD_MASTER_BLUEPRINT_OMEGA_${version}.dot`, "{dot_embedded}"));

  clearHighlight();
}})();
</script>
</body>
</html>"""


def write_outputs(out_dir: Path, version: str, graph: Dict[str, Any], emit_zip: bool) -> Dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = _now_ts()

    # Write graph JSON
    graph_path = out_dir / f"graph_omega_{version}.json"
    graph_path.write_text(json.dumps(graph, indent=2), encoding="utf-8")

    # DOT
    dot_text = build_dot(graph)
    dot_path = out_dir / f"ESD_MASTER_BLUEPRINT_OMEGA_{version}.dot"
    dot_path.write_text(dot_text, encoding="utf-8")

    # Render SVG/PNG
    _require_dot()
    svg_path = out_dir / f"ESD_MASTER_BLUEPRINT_OMEGA_{version}.svg"
    png_path = out_dir / f"ESD_MASTER_BLUEPRINT_OMEGA_{version}.png"

    rc, _, err = _run(["dot", "-Tsvg", str(dot_path), "-o", str(svg_path)])
    if rc != 0:
        _die(f"dot -Tsvg failed: {err.strip()}")
    rc, _, err = _run(["dot", "-Tpng", str(dot_path), "-o", str(png_path), "-Gdpi=220"])
    if rc != 0:
        _die(f"dot -Tpng failed: {err.strip()}")

    # HTML (embed svg + interactive controls)
    html_text = build_html(version=version, stamp=stamp, graph=graph, dot_text=dot_text, svg_text=svg_path.read_text(encoding="utf-8"))
    html_path = out_dir / f"ESD_MASTER_BLUEPRINT_OMEGA_{version}.html"
    html_path.write_text(html_text, encoding="utf-8")

    outputs = {
        "out_dir": str(out_dir),
        "version": version,
        "generated_at": stamp,
        "files": {
            "graph_json": str(graph_path),
            "dot": str(dot_path),
            "svg": str(svg_path),
            "png": str(png_path),
            "html": str(html_path),
        }
    }

    if emit_zip:
        zip_path = out_dir.parent / f"ESD_MASTER_BLUEPRINT_OMEGA_BUNDLE_{version}.zip"
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
            for p in [graph_path, dot_path, svg_path, png_path, html_path]:
                z.write(p, arcname=p.name)
            # include a copy of this builder in the zip (deterministic name)
            z.write(__file__, arcname="build_omega.py")
        outputs["files"]["zip"] = str(zip_path)

    # Basic integrity checks
    for k, fp in outputs["files"].items():
        p = Path(fp)
        if not p.exists() or p.stat().st_size <= 0:
            _die(f"Output missing or empty: {k} -> {p}")

    return outputs


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        prog="build_omega.py",
        formatter_class=argparse.RawTextHelpFormatter,
        description="Build/merge ESD MASTER BLUEPRINT OMEGA (HTML+SVG+PNG+DOT+JSON).",
    )
    ap.add_argument("--version", default=VERSION_DEFAULT, help="Version tag used in filenames.")
    ap.add_argument("--out-dir", default=f"./ESD_MASTER_BLUEPRINT_OMEGA_{VERSION_DEFAULT}", help="Output directory.")
    ap.add_argument("--fragment", action="append", default=[], help="Path to a fragment graph JSON to merge (repeatable).")
    ap.add_argument("--ingest-notes", default=None, help="Path to a text file; lines become NOTE nodes.")
    ap.add_argument("--zip", action="store_true", help="Also emit a bundle zip in the parent directory.")
    ap.add_argument("--selftest", action="store_true", help="Run a self-test build into --out-dir and exit.")
    return ap.parse_args()


def main() -> None:
    args = parse_args()
    version = args.version

    base = base_graph(version)
    fragments: List[Dict[str, Any]] = []

    for fp in args.fragment:
        p = Path(fp)
        if not p.exists():
            _die(f"Fragment not found: {p}")
        fragments.append(load_fragment(p))

    merged, report = merge_graphs(base, fragments) if fragments else (base, {"fragment_count": 0})
    if args.ingest_notes:
        notes_p = Path(args.ingest_notes)
        if not notes_p.exists():
            _die(f"Notes file not found: {notes_p}")
        merged = ingest_notes(merged, notes_p)

    out_dir = Path(args.out_dir)
    outputs = write_outputs(out_dir=out_dir, version=version, graph=merged, emit_zip=args.zip)

    # Emit merge report + build log
    build_log = {
        "version": version,
        "built_at": outputs.get("generated_at"),
        "out_dir": outputs.get("out_dir"),
        "fragments": args.fragment,
        "notes": args.ingest_notes,
        "merge_report": report,
        "outputs": outputs.get("files"),
    }
    (out_dir / f"build_log_{version}.json").write_text(json.dumps(build_log, indent=2), encoding="utf-8")

    print(json.dumps(build_log, indent=2))

    if args.selftest:
        return


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        _die("Interrupted by user.", code=130)
