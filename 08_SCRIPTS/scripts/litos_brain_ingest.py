#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LitigationOS Tool: Brain Ingest (Atoms→Signals→Scores→Deltas→Gates→Actions→Vehicles + Graph Export)

Purpose:
- Turn operator manuals / blueprints / link corpora / extracted PDFs into structured, replayable artifacts.
- Offline-first: no network calls. URLs remain pointers.
- Truth posture: extracted text is candidate-only; QuoteLock promotion is a separate gate.

Outputs (BRAIN/RUNS/<run_id>/):
- atoms.jsonl
- signals.jsonl
- scores.jsonl
- deltas.jsonl
- gates.jsonl
- actions.jsonl
- vehicles.jsonl
- graph/nodes.csv, graph/edges.csv (GraphContracts compatible)
- receipt.json

Determinism:
- IDs are SHA1 of (kind + source + locator + text) where applicable.
- Stable ordering by source_path then locator.

Exit codes:
 0 OK
 2 Invalid input / no sources
 3 Output write failure
"""
from __future__ import annotations
import argparse, os, re, json, hashlib, datetime, csv
from typing import Dict, Any, List, Tuple

KEYWORDS = {
  "authority": ["mcr","mcl","mre","benchbook","scao","mji","administrative order","court of appeals","michigan supreme court"],
  "forms": ["form","mc ","foc","sca o","sCAO","complaint","motion","affidavit","proof of service","notice","order"],
  "graph": ["neo4j","bloom","graph","node","edge","cypher","apoc","qdrant","vector","embedding","rerank"],
  "automation": ["daemon","watcher","scheduler","autonomous","orchestrator","runner","job queue","event log","replay"],
  "llm_stack": ["ollama","llm","transformer","hugging face","embedding","reranker","tika","ocr","pdfminer","pypdf"],
  "integrity": ["manifest","receipt","hash","crc32","integrity","append-only","no overwrite","idempotent","fail-closed","proof obligation","po ledger","pcw","pcg"],
  "tracks": ["meek1","meek2","meek3","meek4","custody","parenting time","ppo","housing","landlord","tenant","jtc","judicial conduct","appeal","superintending"]
}

URL_RE = re.compile(r'(https?://[^\s\)\]]+)', re.IGNORECASE)

def utc_now_iso() -> str:
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

def sha1(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8", errors="ignore")).hexdigest()

def norm_space(s: str) -> str:
    s = s.strip()
    s = re.sub(r"\s+", " ", s)
    return s

def iter_sources(paths: List[str]) -> List[str]:
    out = []
    for p in paths:
        if os.path.isdir(p):
            for root, _, files in os.walk(p):
                for fn in files:
                    if fn.lower().endswith((".txt",".md")):
                        out.append(os.path.join(root, fn))
        elif os.path.isfile(p) and p.lower().endswith((".txt",".md")):
            out.append(p)
    return sorted(set(out), key=lambda x: x.lower())

def split_atoms(text: str) -> List[str]:
    # Paragraph-ish splitting with bullet retention
    lines = text.splitlines()
    buf = []
    out = []
    def flush():
        nonlocal buf
        s = "\n".join(buf).strip("\n")
        s2 = norm_space(s.replace("\t"," ").replace("\r",""))
        if len(s2) >= 20:
            out.append(s2)
        buf = []
    for ln in lines:
        if ln.strip() == "":
            flush()
            continue
        # hard split on very long separators
        if set(ln.strip()) <= set("=-*_") and len(ln.strip()) >= 8:
            flush()
            continue
        buf.append(ln)
        # limit chunk size
        if sum(len(x) for x in buf) > 800:
            flush()
    flush()
    return out

def tag_for_text(s: str) -> List[str]:
    low = s.lower()
    tags = []
    for k, words in KEYWORDS.items():
        if any(w in low for w in words):
            tags.append(k)
    if URL_RE.search(s):
        tags.append("link")
    # intent-ish tags
    if "must" in low or "shall" in low or "forbidden" in low:
        tags.append("directive")
    if "schema" in low or "contract" in low:
        tags.append("schema")
    if "gate" in low or "validator" in low:
        tags.append("gate")
    return sorted(set(tags))

def atom_type_for(tags: List[str]) -> str:
    if "authority" in tags:
        return "authority_candidate"
    if "link" in tags:
        return "link"
    if "directive" in tags:
        return "directive"
    if "forms" in tags:
        return "procedure"
    if "graph" in tags or "automation" in tags or "llm_stack" in tags:
        return "concept"
    return "other"

def confidence_for(text: str, tags: List[str]) -> int:
    low = text.lower()
    c = 2
    if URL_RE.search(text):
        c += 1
    if any(x in low for x in ["python","pip","cmd","powershell","--","/"]):
        c += 1
    if any(x in tags for x in ["authority","schema","integrity"]):
        c += 1
    return max(1, min(5, c))

def build_atoms(files: List[str]) -> List[Dict[str, Any]]:
    atoms = []
    for fp in files:
        try:
            raw = open(fp, "r", encoding="utf-8", errors="ignore").read()
        except Exception:
            continue
        # locator style: line ranges (approx) OR page markers if present
        # We keep a simple rolling line pointer for determinism.
        parts = split_atoms(raw)
        # approximate locators as "chunk:NNNN"
        for i, chunk in enumerate(parts, start=1):
            tags = tag_for_text(chunk)
            atom_type = atom_type_for(tags)
            loc = f"chunk:{i:04d}"
            atom_id = "ATOM_" + sha1("|".join([atom_type, fp, loc, chunk]))[:16]
            atoms.append({
                "atom_id": atom_id,
                "source_path": fp.replace("\\","/"),
                "source_locator": loc,
                "atom_type": atom_type,
                "text": chunk,
                "tags": tags,
                "confidence": confidence_for(chunk, tags),
                "created_utc": utc_now_iso(),
            })
    # stable ordering
    atoms.sort(key=lambda a: (a["source_path"].lower(), a["source_locator"], a["atom_id"]))
    return atoms

def signal_kind(atom: Dict[str, Any]) -> str:
    tags = set(atom.get("tags") or [])
    if "forms" in tags:
        return "forms"
    if "authority" in tags:
        return "authority"
    if "graph" in tags:
        return "graph"
    if "automation" in tags:
        return "automation"
    if "llm_stack" in tags:
        return "llm_stack"
    if "integrity" in tags or "gate" in tags:
        return "module_need"
    return "other"

def score_signal(text: str, tags: List[str], conf: int) -> Tuple[int,int,int,int,int]:
    low = text.lower()
    impact = 3
    feasibility = 3
    risk = 3
    confidence = conf
    # heuristics
    if any(k in low for k in ["must","shall","required","non-negotiable"]):
        impact += 1
    if any(k in low for k in ["replay","job queue","event log","idempotent","crash-safe"]):
        impact += 1; feasibility -= 0
    if any(k in low for k in ["sign","code signing","msi","installer","ci","reproducible"]):
        impact += 1; feasibility -= 1
    if "authority" in tags:
        risk += 1  # legal assertions risk if mis-pinned
    if "link" in tags:
        feasibility += 1
    # clamp
    impact = max(1, min(5, impact))
    feasibility = max(1, min(5, feasibility))
    risk = max(1, min(5, risk))
    confidence = max(1, min(5, confidence))
    priority = impact*2 + feasibility - risk + confidence
    return impact, feasibility, risk, confidence, priority

def build_signals(atoms: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    signals = []
    scores = []
    for a in atoms:
        kind = signal_kind(a)
        # only promote useful atoms to signals
        if kind == "other" and a["confidence"] <= 2:
            continue
        text = a["text"]
        # signal id keyed on kind+text
        sid = "SIG_" + sha1("|".join([kind, text]))[:16]
        imp, feas, risk, conf, pri = score_signal(text, a.get("tags") or [], a.get("confidence") or 2)
        signals.append({
            "signal_id": sid,
            "kind": kind,
            "text": text if len(text) <= 420 else (text[:417] + "..."),
            "atoms": [a["atom_id"]],
            "score": pri,
            "created_utc": utc_now_iso(),
        })
        scores.append({
            "item_id": sid,
            "impact": imp,
            "feasibility": feas,
            "risk": risk,
            "confidence": conf,
            "priority": pri,
            "created_utc": utc_now_iso(),
        })
    # merge duplicate signals by signal_id
    by = {}
    for s in signals:
        e = by.get(s["signal_id"])
        if not e:
            by[s["signal_id"]] = s
        else:
            e["atoms"].extend(s["atoms"])
            e["atoms"] = sorted(set(e["atoms"]))
            e["score"] = max(e["score"], s["score"])
    signals2 = sorted(by.values(), key=lambda x: (-x["score"], x["signal_id"]))
    scores_by = {sc["item_id"]: sc for sc in scores}
    scores2 = [scores_by[s["signal_id"]] for s in signals2 if s["signal_id"] in scores_by]
    return signals2, scores2

THEMES = [
 ("Replayability","automation",["replay","job queue","event log","idempotent","crash-safe","wal"]),
 ("AuthoritySnapshot","authority",["mcr","mcl","mre","benchbook","authority snapshot","pinpoint"]),
 ("Forms-First","forms",["scao","form","mc ","foc","overlay","autofill"]),
 ("Graph Import/Export","graph",["neo4j","bloom","cypher","apoc","nodes.csv","edges.csv","import"]),
 ("Local LLM Stack","llm_stack",["ollama","embedding","rerank","hugging face","tika","ocr"]),
 ("Integrity + Bundling","module_need",["manifest","receipt","append-only","bundle","700mb","patches","rebuild"]),
]

def build_deltas(signals: List[Dict[str, Any]], atoms: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    deltas = []
    sig_by_id = {s["signal_id"]: s for s in signals}
    # keyword match themes
    for theme, kind, kws in THEMES:
        hits = []
        for s in signals:
            if s["kind"] != kind:
                continue
            low = s["text"].lower()
            if any(k in low for k in kws):
                hits.append(s)
        if not hits:
            continue
        hits = sorted(hits, key=lambda x: -x["score"])[:18]
        supporting_signals = [h["signal_id"] for h in hits]
        supporting_atoms = sorted(set(aid for h in hits for aid in h["atoms"]))[:80]
        priority = int(sum(h["score"] for h in hits[:8]) / max(1, min(8, len(hits))))
        did = "DELTA_" + sha1("|".join([theme] + supporting_signals))[:16]
        desc = f"{theme}: promote signals into shipped cores and enforce via gates/receipts."
        deltas.append({
            "delta_id": did,
            "theme": theme,
            "description": desc,
            "supporting_signals": supporting_signals,
            "supporting_atoms": supporting_atoms,
            "priority": priority,
            "created_utc": utc_now_iso(),
        })
    deltas.sort(key=lambda d: (-d["priority"], d["delta_id"]))
    return deltas

def build_gates(deltas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    # Minimal PCW gate layer for the ingest/graph pathway.
    now = utc_now_iso()
    gates = [
      {"gate_id":"GATE_QUOTES_QUOTELOCK","name":"QuoteLock (verbatim-only)","status":"OBLIGATION_OPEN",
       "requirements":["independent extraction x2","diff==0","pin recipe (page/line)"],
       "evidence":[],"created_utc":now},
      {"gate_id":"GATE_AUTHORITY_SNAPSHOT","name":"AuthoritySnapshot present","status":"OBLIGATION_PARTIAL",
       "requirements":["authority_index.jsonl exists","pin_map exists","receipt exists"],
       "evidence":["AUTHORITY/snapshots/*/receipt.json"],"created_utc":now},
      {"gate_id":"GATE_FORMS_CATALOG","name":"Forms catalog present","status":"OBLIGATION_PARTIAL",
       "requirements":["forms index.json exists","schema validates"],"evidence":["FORMS/catalog/*/index.json"],"created_utc":now},
      {"gate_id":"GATE_P0_LEDGER","name":"PO ledger coupling (PCW enforce)","status":"OBLIGATION_OPEN",
       "requirements":["PO_LEDGER.jsonl per run","PO status machine-checkable"],"evidence":[],"created_utc":now},
      {"gate_id":"GATE_GRAPH_CONTRACTS","name":"GraphContracts validation","status":"OBLIGATION_PARTIAL",
       "requirements":["nodes.csv/edges.csv validated","referential ok"],"evidence":["GRAPH/exports/*/validation_report.json"],"created_utc":now},
      {"gate_id":"GATE_REPLAYABILITY","name":"Replayable run receipts","status":"OBLIGATION_PARTIAL",
       "requirements":["event log jsonl","jobqueue sqlite","receipt.json"],"evidence":["LOGS/*","BRAIN/RUNS/*/receipt.json"],"created_utc":now},
    ]
    return gates

def build_actions(deltas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    now = utc_now_iso()
    actions = []
    # Convert top deltas into concrete build actions.
    for d in deltas[:10]:
        title = f"Implement {d['theme']} core"
        aid = "ACT_" + sha1("|".join([d["delta_id"], title]))[:16]
        depends = []
        if d["theme"] in ["AuthoritySnapshot","Forms-First"]:
            depends = ["GATE_REPLAYABILITY"]
        if d["theme"] in ["Graph Import/Export"]:
            depends = ["GATE_AUTHORITY_SNAPSHOT","GATE_FORMS_CATALOG"]
        if d["theme"] in ["Local LLM Stack"]:
            depends = ["GATE_REPLAYABILITY"]
        if d["theme"] in ["Integrity + Bundling"]:
            depends = ["GATE_REPLAYABILITY"]
        if d["theme"] in ["Replayability"]:
            depends = []
        actions.append({
            "action_id": aid,
            "title": title,
            "description": f"Promote delta {d['delta_id']} into shipped, tested code; wire into governor pipeline; emit receipts.",
            "priority": d["priority"],
            "depends_on_gates": depends,
            "supports_deltas": [d["delta_id"]],
            "created_utc": now,
        })
    actions.sort(key=lambda a: (-a["priority"], a["action_id"]))
    return actions

def build_vehicles(atoms: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    now = utc_now_iso()
    vehicles = []
    # Simple lexical vehicle candidate extraction; filing readiness requires authority pins.
    patterns = [
      ("foia","foia",["foia","mcl 15.23","public records"]),
      ("jtc","jtc",["jtc","judicial tenure","judicial conduct"]),
      ("appeal","appeal",["appeal","court of appeals","superintending","original action"]),
      ("trial","trial",["motion","objection","show cause","contempt","proof of service"]),
      ("system","system",["orchestrator","daemon","pipeline","builder","validator"]),
    ]
    text_all = " \n ".join(a["text"] for a in atoms[:600])
    low_all = text_all.lower()
    for lane, v, kws in patterns:
        if any(k in low_all for k in kws):
            vid = "VEH_" + sha1("|".join([lane, v]))[:16]
            vehicles.append({
                "vehicle_id": vid,
                "lane": lane,
                "vehicle": v,
                "status": "CANDIDATE",
                "missing_authority": ["AUTH_PINPOINT_MISSING"] if lane in ["foia","jtc","appeal","trial"] else [],
                "created_utc": now,
            })
    # Always include system vehicle
    vehicles.append({
        "vehicle_id":"VEH_SYSTEM_PIPELINE",
        "lane":"system",
        "vehicle":"autonomous_ingest_pipeline",
        "status":"CANDIDATE",
        "missing_authority":[],
        "created_utc":now,
    })
    # stable
    by = {v["vehicle_id"]: v for v in vehicles}
    return sorted(by.values(), key=lambda x: (x["lane"], x["vehicle_id"]))

def write_jsonl(path: str, rows: List[Dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

def export_graph(outdir: str, atoms, signals, deltas, actions, gates, vehicles) -> Tuple[str,str]:
    os.makedirs(outdir, exist_ok=True)
    nodes_path = os.path.join(outdir, "nodes.csv")
    edges_path = os.path.join(outdir, "edges.csv")

    now = utc_now_iso()
    nodes = []
    def add_node(nid, labels, source_path="", source_locator="", track="GLOBAL"):
        nodes.append({
            "id": nid,
            "labels": ";".join(labels) if isinstance(labels, list) else labels,
            "case_id": "",
            "track": track or "GLOBAL",
            "source_path": source_path,
            "source_locator": source_locator,
            "created_utc": now,
            "updated_utc": now,
        })

    for a in atoms:
        add_node(a["atom_id"], ["Atom","Brain",a["atom_type"]], a["source_path"], a["source_locator"], "")
    for s in signals:
        add_node(s["signal_id"], ["Signal","Brain",s["kind"]])
    for d in deltas:
        add_node(d["delta_id"], ["Delta","Brain",re.sub(r"[^A-Za-z0-9]+","_",d["theme"])[:48]])
    for ac in actions:
        add_node(ac["action_id"], ["Action","Brain"])
    for g in gates:
        add_node(g["gate_id"], ["Gate","Brain",g["status"]])
    for v in vehicles:
        add_node(v["vehicle_id"], ["Vehicle","Brain",v["lane"]])

    # edges
    edges = []
    def add_edge(start, typ, end):
        edges.append({
            "start_id": start,
            "type": typ,
            "end_id": end,
            "case_id": "",
            "track": "GLOBAL",
            "evidence_path": "",
            "evidence_locator": "",
            "authority_path": "",
            "authority_pinpoint": "",
        })

    for s in signals:
        for aid in s["atoms"]:
            add_edge(s["signal_id"], "DERIVED_FROM", aid)
    for d in deltas:
        for sid in d["supporting_signals"]:
            add_edge(d["delta_id"], "SUPPORTED_BY", sid)
    for ac in actions:
        for did in ac["supports_deltas"]:
            add_edge(ac["action_id"], "IMPLEMENTS", did)
    for g in gates:
        add_edge(g["gate_id"], "GOVERNS", "VEH_SYSTEM_PIPELINE")
    for v in vehicles:
        add_edge(v["vehicle_id"], "AVAILABLE_IN", "VEH_SYSTEM_PIPELINE")

    # write CSV
    node_fields = ["id","labels","case_id","track","source_path","source_locator","created_utc","updated_utc"]
    edge_fields = ["start_id","type","end_id","case_id","track","evidence_path","evidence_locator","authority_path","authority_pinpoint"]
    with open(nodes_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=node_fields)
        w.writeheader()
        for r in nodes:
            w.writerow(r)
    with open(edges_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=edge_fields)
        w.writeheader()
        for r in edges:
            w.writerow(r)
    return nodes_path, edges_path

def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sources", nargs="+", required=True, help="Files or directories (.txt/.md) to ingest")
    ap.add_argument("--outdir", required=True, help="BRAIN/RUNS/<run_id> output directory")
    ap.add_argument("--run-id", required=True, help="Run identifier (stable)")
    args = ap.parse_args(argv)

    files = iter_sources(args.sources)
    if not files:
        print("No ingestible sources found.")
        return 2

    os.makedirs(args.outdir, exist_ok=True)

    atoms = build_atoms(files)
    signals, scores = build_signals(atoms)
    deltas = build_deltas(signals, atoms)
    gates = build_gates(deltas)
    actions = build_actions(deltas)
    vehicles = build_vehicles(atoms)

    write_jsonl(os.path.join(args.outdir, "atoms.jsonl"), atoms)
    write_jsonl(os.path.join(args.outdir, "signals.jsonl"), signals)
    write_jsonl(os.path.join(args.outdir, "scores.jsonl"), scores)
    write_jsonl(os.path.join(args.outdir, "deltas.jsonl"), deltas)
    write_jsonl(os.path.join(args.outdir, "gates.jsonl"), gates)
    write_jsonl(os.path.join(args.outdir, "actions.jsonl"), actions)
    write_jsonl(os.path.join(args.outdir, "vehicles.jsonl"), vehicles)

    nodes_path, edges_path = export_graph(os.path.join(args.outdir, "graph"), atoms, signals, deltas, actions, gates, vehicles)

    receipt = {
        "run_id": args.run_id,
        "generated_utc": utc_now_iso(),
        "sources": files,
        "counts": {
            "atoms": len(atoms),
            "signals": len(signals),
            "deltas": len(deltas),
            "actions": len(actions),
            "gates": len(gates),
            "vehicles": len(vehicles),
        },
        "outputs": {
            "atoms": "atoms.jsonl",
            "signals": "signals.jsonl",
            "scores": "scores.jsonl",
            "deltas": "deltas.jsonl",
            "gates": "gates.jsonl",
            "actions": "actions.jsonl",
            "vehicles": "vehicles.jsonl",
            "graph_nodes": os.path.join("graph","nodes.csv"),
            "graph_edges": os.path.join("graph","edges.csv"),
        },
        "notes": [
            "Offline ingest; URLs are pointers only.",
            "QuoteLock not performed; verbatim quotations remain candidate-only."
        ]
    }
    with open(os.path.join(args.outdir, "receipt.json"), "w", encoding="utf-8") as f:
        json.dump(receipt, f, indent=2)

    print("OK", json.dumps(receipt["counts"], sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
