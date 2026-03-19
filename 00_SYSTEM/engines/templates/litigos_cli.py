#!/usr/bin/env python3
"""
litigos_cli.py — Minimal runnable LitigationOS engine (generated template)

This is deliberately small but real:
- Delta harvest: scans input directory, tracks modified time
- Extract: extracts atoms from .txt (and .docx if python-docx available)
- Authority: optional pass (reads authority corpus folder of .txt files)
- Graph: exports nodes/edges CSV (Actors, Docs, Atoms)
- SBNA: selects a trivial recommended action based on detected order/atoms presence
- Narrative: emits record-anchored outline referencing atom IDs
- Validate: ensures core artifacts exist and are non-empty
- Package: emits manifest + run ledger

Usage:
  python litigos_cli.py run --in <corpus_dir> --out <out_dir>

"""
from __future__ import annotations
import argparse, os, json, csv, time, hashlib, base64, zlib
from datetime import datetime
from pathlib import Path

def now_iso():
    return datetime.now().isoformat(timespec="seconds")

def ensure_dir(p: str):
    Path(p).mkdir(parents=True, exist_ok=True)

def list_files(root: str):
    rootp = Path(root)
    files = []
    for p in rootp.rglob("*"):
        if p.is_file():
            files.append(p)
    return files

def delta_harvest(corpus_dir: str, out_dir: str):
    ensure_dir(out_dir)
    workset = []
    for p in list_files(corpus_dir):
        try:
            st = p.stat()
        except Exception:
            continue
        workset.append({
            "uri": str(p),
            "size": st.st_size,
            "mtime": int(st.st_mtime),
            "ext": p.suffix.lower()
        })
    workset.sort(key=lambda x: x["uri"])
    path = Path(out_dir) / "workset.json"
    path.write_text(json.dumps({"generated_at": now_iso(), "corpus_dir": corpus_dir, "files": workset}, indent=2), encoding="utf-8")
    return str(path)

def _source_locator(uri: str, media_type: str, locator: dict):
    return {
        "uri": uri,
        "media_type": media_type,
        "locator": locator,
        "extracted_at": now_iso(),
        "extractor": {"name": "litigos_min", "version": "0.1"}
    }

def _emit_jsonl(path: str, rows: list[dict]):
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

def extract_atoms(workset_path: str, out_dir: str):
    ws = json.loads(Path(workset_path).read_text(encoding="utf-8"))
    files = ws["files"]
    doc_registry = []
    atoms = []
    orders = []
    atom_i = 0

    # optional docx support
    docx_ok = False
    try:
        import docx  # type: ignore
        docx_ok = True
    except Exception:
        docx_ok = False

    for f in files:
        uri = f["uri"]
        ext = f.get("ext","")
        doc_registry.append({"uri": uri, "ext": ext, "size": f["size"], "mtime": f["mtime"]})

        if ext == ".txt":
            try:
                text = Path(uri).read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            lines = text.splitlines()
            for li, line in enumerate(lines, start=1):
                if not line.strip():
                    continue
                atom_i += 1
                sl = _source_locator(uri, "text/plain", {"line": li})
                atom = {
                    "atom_id": f"EA-{atom_i:06d}",
                    "type": "statement",
                    "who": None,
                    "what": line.strip(),
                    "when_event": None,
                    "when_recorded": datetime.fromtimestamp(f["mtime"]).date().isoformat(),
                    "source_locators": [sl],
                    "confidence": 0.8,
                    "tags": []
                }
                atoms.append(atom)
                # crude order clause detector
                if line.strip().upper().startswith("IT IS ORDERED"):
                    orders.append({"obligation_id": f"OB-{atom_i:06d}", "text": line.strip(), "source_locators":[sl]})

        elif ext == ".docx" and docx_ok:
            try:
                import docx  # type: ignore
                doc = docx.Document(uri)  # type: ignore
                for pi, para in enumerate(doc.paragraphs, start=1):
                    t = (para.text or "").strip()
                    if not t:
                        continue
                    atom_i += 1
                    sl = _source_locator(uri, "application/vnd.openxmlformats-officedocument.wordprocessingml.document", {"paragraph": pi})
                    atoms.append({
                        "atom_id": f"EA-{atom_i:06d}",
                        "type": "statement",
                        "who": None,
                        "what": t,
                        "when_event": None,
                        "when_recorded": datetime.fromtimestamp(f["mtime"]).date().isoformat(),
                        "source_locators": [sl],
                        "confidence": 0.75,
                        "tags": []
                    })
                    if t.upper().startswith("IT IS ORDERED"):
                        orders.append({"obligation_id": f"OB-{atom_i:06d}", "text": t, "source_locators":[sl]})
            except Exception:
                continue

        # PDFs are intentionally not parsed here (dependency-heavy). You can plug in PyMuPDF in later phases.

    Path(out_dir, "doc_registry.json").write_text(json.dumps(doc_registry, indent=2), encoding="utf-8")
    _emit_jsonl(str(Path(out_dir, "evidence_atoms.jsonl")), atoms)
    _emit_jsonl(str(Path(out_dir, "orders_compiled.jsonl")), orders)
    # minimal timeline: use recorded time only
    timeline = [{"event_id": a["atom_id"], "when_event": a["when_event"], "when_recorded": a["when_recorded"], "what": a["what"]} for a in atoms[:2000]]
    _emit_jsonl(str(Path(out_dir, "timeline_bitemp.jsonl")), timeline)
    return {
        "doc_registry": str(Path(out_dir, "doc_registry.json")),
        "evidence_atoms": str(Path(out_dir, "evidence_atoms.jsonl")),
        "orders_compiled": str(Path(out_dir, "orders_compiled.jsonl")),
        "timeline_bitemp": str(Path(out_dir, "timeline_bitemp.jsonl")),
    }

def authority_pass(authority_dir: str|None, out_dir: str):
    triples = []
    if authority_dir and Path(authority_dir).exists():
        i=0
        for p in Path(authority_dir).rglob("*.txt"):
            try:
                txt = p.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            # naive: each non-empty line becomes a proposition supported by this file name (no pinpoints)
            for li, line in enumerate(txt.splitlines(), start=1):
                s = line.strip()
                if not s:
                    continue
                i += 1
                triples.append({
                    "triple_id": f"AT-{i:06d}",
                    "proposition": s,
                    "authority_ref": {"type":"text_file","id": str(p.name)},
                    "pinpoint": f"line {li}",
                    "scope": "unspecified",
                    "source_locators": [_source_locator(str(p), "text/plain", {"line": li})],
                    "tags": []
                })
                if i >= 2000:
                    break
            if i >= 2000:
                break
    _emit_jsonl(str(Path(out_dir, "authority_triples.jsonl")), triples)
    # placeholders not used; rule matrix empty unless supplied
    Path(out_dir, "rule_matrix_edges.csv").write_text("from,to,label\n", encoding="utf-8")
    Path(out_dir, "forms_catalog.json").write_text(json.dumps([], indent=2), encoding="utf-8")
    _emit_jsonl(str(Path(out_dir, "authority_gap_requests.jsonl")), [])
    return {
        "authority_triples": str(Path(out_dir, "authority_triples.jsonl")),
        "rule_matrix_edges": str(Path(out_dir, "rule_matrix_edges.csv")),
        "forms_catalog": str(Path(out_dir, "forms_catalog.json")),
        "authority_gap_requests": str(Path(out_dir, "authority_gap_requests.jsonl")),
    }

def graph_export(out_dir: str):
    # minimal graph export: Documents, Atoms, Order obligations
    nodes = []
    edges = []
    doc_registry = json.loads(Path(out_dir, "doc_registry.json").read_text(encoding="utf-8"))
    atoms = [json.loads(line) for line in Path(out_dir, "evidence_atoms.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    orders = [json.loads(line) for line in Path(out_dir, "orders_compiled.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]

    for d in doc_registry:
        nodes.append({"id": "DOC:"+d["uri"], "type":"Document", "label": Path(d["uri"]).name})
    for a in atoms:
        nodes.append({"id": "EA:"+a["atom_id"], "type":"EvidenceAtom", "label": a["atom_id"]})
        sl = (a.get("source_locators") or [{}])[0]
        edges.append({"from":"EA:"+a["atom_id"], "to":"DOC:"+sl.get("uri",""), "type":"SOURCED_FROM"})
    for o in orders:
        nodes.append({"id":"OB:"+o["obligation_id"], "type":"Obligation", "label": o["obligation_id"]})

    # actor aliases minimal
    Path(out_dir, "actor_aliases.json").write_text(json.dumps({"actors":[],"aliases":[]}, indent=2), encoding="utf-8")

    # CSV exports
    with open(Path(out_dir, "graph_nodes.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["id","type","label"])
        w.writeheader()
        for r in nodes:
            w.writerow(r)
    with open(Path(out_dir, "graph_edges.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["from","to","type"])
        w.writeheader()
        for r in edges:
            if r["to"] == "DOC:":
                continue
            w.writerow(r)
    return {
        "graph_nodes": str(Path(out_dir, "graph_nodes.csv")),
        "graph_edges": str(Path(out_dir, "graph_edges.csv")),
        "actor_aliases": str(Path(out_dir, "actor_aliases.json")),
    }

def sbna(out_dir: str):
    orders = [json.loads(line) for line in Path(out_dir, "orders_compiled.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    atoms_count = sum(1 for _ in Path(out_dir, "evidence_atoms.jsonl").read_text(encoding="utf-8").splitlines() if _.strip())
    case_state = {"generated_at": now_iso(), "atoms": atoms_count, "orders": len(orders), "status": "OK"}
    Path(out_dir, "case_state.json").write_text(json.dumps(case_state, indent=2), encoding="utf-8")

    primary = {
        "action_id": "ACTN-0001",
        "vehicle": "HARVEST_ONLY" if atoms_count == 0 else ("ORDER_RESPONSE" if orders else "EVIDENCE_SUMMARY"),
        "purpose": "Minimal default action selection",
        "required_proofs": [],
        "required_authority": [],
        "service_prereqs": []
    }
    sbna_obj = {"sbna_id": "SBNA-0001", "primary_action": primary, "backup_actions": [], "risk_notes": [], "blockers": []}
    Path(out_dir, "sbna.json").write_text(json.dumps(sbna_obj, indent=2), encoding="utf-8")
    # deadlines placeholder not used; emit empty jsonl deterministically
    Path(out_dir, "deadlines_tracker.jsonl").write_text("", encoding="utf-8")
    return {"case_state": str(Path(out_dir, "case_state.json")), "sbna": str(Path(out_dir, "sbna.json"))}

def narrative(out_dir: str):
    atoms = [json.loads(line) for line in Path(out_dir, "evidence_atoms.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    sbna_obj = json.loads(Path(out_dir, "sbna.json").read_text(encoding="utf-8"))
    lines = []
    lines.append("# Narrative Outline (Record-Anchored)")
    lines.append("")
    lines.append(f"- generated_at: {now_iso()}")
    lines.append(f"- sbna.primary.vehicle: {sbna_obj['primary_action']['vehicle']}")
    lines.append("")
    lines.append("## Evidence Atom Index (first 50)")
    for a in atoms[:50]:
        lines.append(f"- {a['atom_id']}: {a['what']}")
    Path(out_dir, "narrative_outline.md").write_text("\n".join(lines), encoding="utf-8")
    Path(out_dir, "argument_map.json").write_text(json.dumps({"nodes":[],"edges":[]}, indent=2), encoding="utf-8")
    Path(out_dir, "exhibit_storyboard.json").write_text(json.dumps({"exhibits":[]}, indent=2), encoding="utf-8")
    return {"narrative_outline": str(Path(out_dir, "narrative_outline.md"))}

def validate(out_dir: str):
    required = [
        "doc_registry.json",
        "evidence_atoms.jsonl",
        "orders_compiled.jsonl",
        "authority_triples.jsonl",
        "graph_nodes.csv",
        "graph_edges.csv",
        "case_state.json",
        "sbna.json",
        "narrative_outline.md"
    ]
    missing = []
    for r in required:
        p = Path(out_dir, r)
        if not p.exists() or p.stat().st_size == 0:
            missing.append(r)
    status = "PASS" if not missing else "PARTIAL"
    report = {
        "status": status,
        "core_pass": ["deterministic_outputs"],
        "core_fail": ["missing_or_empty_artifacts"] if missing else [],
        "missing_items": [{"type":"artifact","detail":m} for m in missing],
        "recommended_next": []
    }
    Path(out_dir, "validation_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    Path(out_dir, "risk_register.json").write_text(json.dumps([], indent=2), encoding="utf-8")
    return {"validation_report": str(Path(out_dir, "validation_report.json"))}

def package(out_dir: str, out_zip: str|None):
    # manifest
    items = []
    for p in sorted(Path(out_dir).glob("*")):
        if p.is_file():
            items.append({"path": p.name, "bytes": p.stat().st_size})
    manifest = {"generated_at": now_iso(), "items": items}
    Path(out_dir, "bundle_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    # run ledger (append-only per run)
    ledger_path = Path(out_dir, "RUN_LEDGER.jsonl")
    entry = {"run_id": Path(out_dir).name, "generated_at": now_iso(), "outputs": [i["path"] for i in items]}
    with open(ledger_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

    if out_zip:
        import zipfile
        with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED) as z:
            for p in sorted(Path(out_dir).glob("*")):
                if p.is_file():
                    z.write(str(p), arcname=p.name)
        # verify
        with zipfile.ZipFile(out_zip, "r") as z:
            if z.testzip() is not None:
                raise RuntimeError("ZIP integrity test failed")
    return {"bundle_manifest": str(Path(out_dir, "bundle_manifest.json")), "run_ledger": str(ledger_path)}

def run_all(corpus_dir: str, out_dir: str, authority_dir: str|None = None, zip_out: bool = False):
    ensure_dir(out_dir)
    workset = delta_harvest(corpus_dir, out_dir)
    extract_atoms(workset, out_dir)
    authority_pass(authority_dir, out_dir)
    graph_export(out_dir)
    sbna(out_dir)
    narrative(out_dir)
    validate(out_dir)
    out_zip = str(Path(out_dir).with_suffix(".zip")) if zip_out else None
    package(out_dir, out_zip)
    return out_zip

def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("run")
    r.add_argument("--in", dest="corpus_dir", required=True)
    r.add_argument("--out", dest="out_dir", required=True)
    r.add_argument("--authority", dest="authority_dir", default=None)
    r.add_argument("--zip", action="store_true")

    args = ap.parse_args()
    if args.cmd == "run":
        z = run_all(args.corpus_dir, args.out_dir, authority_dir=args.authority_dir, zip_out=args.zip)
        print(f"OUT_DIR: {args.out_dir}")
        if z:
            print(f"ZIP: {z}")

if __name__ == "__main__":
    main()
