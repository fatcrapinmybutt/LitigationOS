from __future__ import annotations
import argparse, csv, fnmatch, json, sqlite3, uuid, re, sys, traceback
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Tuple

# Relative-import safe (run as script or module)
try:
    from .extractors import extract_text_generic
    from .quote_event_atomizer import quoteize_text, eventize_quotes, contradiction_pairs
    from .mi_vehicle_router import choose_vehicle
    from .pack_router import build_pack
    from .authority_router import authority_triples_for_lane
except ImportError:
    from extractors import extract_text_generic
    from quote_event_atomizer import quoteize_text, eventize_quotes, contradiction_pairs
    from mi_vehicle_router import choose_vehicle
    from pack_router import build_pack
    from authority_router import authority_triples_for_lane

def load_jsonc(path: Path) -> Dict[str, Any]:
    txt = path.read_text(encoding="utf-8", errors="ignore")
    txt = re.sub(r"//.*", "", txt)
    txt = re.sub(r",\s*([}\]])", r"\1", txt)
    return json.loads(txt)

def utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

def ensure_dirs(cfg: Dict[str, Any]) -> Dict[str, Path]:
    ws = Path(cfg["workspace_root"])
    dirs = {
        "ws": ws,
        "inventory": ws / "01_INVENTORY",
        "textbank": ws / "02_TEXTBANK",
        "db": ws / "03_INDEX",
        "packs": ws / "04_PACKS",
        "courtpacks": ws / "05_COURTPACKS",
        "validation": ws / "90_VALIDATION",
        "logs": ws / "10_LOGS",
    }
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)
    return dirs

def write_log(dirs: Dict[str, Path], kind: str, payload: Dict[str, Any]) -> None:
    p = dirs["logs"] / "run_ledger.jsonl"
    rec = {"ts": utc_iso(), "kind": kind, **payload}
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")

def lane_for_path(path_str: str, cfg: Dict[str, Any]) -> str:
    low = path_str.lower()
    for lane, patterns in cfg.get("lanes", {}).items():
        for pat in patterns:
            p = pat.lower()
            if "*" in p or "?" in p:
                if fnmatch.fnmatch(low, p):
                    return lane
            elif p in low:
                return lane
    return "UNKNOWN"

def case_for_path(path_str: str, cfg: Dict[str, Any]) -> Optional[str]:
    low = path_str.lower()
    for rule in cfg.get("case_rules", []):
        for pat in rule.get("match", []) + rule.get("needles", []):
            p = str(pat).lower()
            if ("*" in p or "?" in p and fnmatch.fnmatch(low, p)) or p in low:
                return rule["case_id"]
    return None

def kind_for_ext(ext: str) -> str:
    ext = ext.lower()
    if ext == ".pdf": return "pdf"
    if ext == ".docx": return "docx"
    if ext in {".txt",".md",".log",".csv",".json",".jsonc",".yaml",".yml"}: return "txt"
    if ext in {".png",".jpg",".jpeg",".tif",".tiff",".webp"}: return "image"
    if ext in {".mp3",".wav",".m4a"}: return "audio"
    if ext in {".mp4",".mov",".mkv"}: return "video"
    return "other"

def identity_for(path: Path) -> Dict[str, Any]:
    st = path.stat()
    file_id = getattr(st, "st_ino", None)
    ident = {
        "source_path_norm": str(path.resolve()),
        "bytes_size": int(st.st_size),
        "mtime_utc": datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat(),
        "ctime_utc": datetime.fromtimestamp(st.st_ctime, tz=timezone.utc).isoformat(),
        "file_id": str(file_id) if file_id is not None else None,
        "volume_serial": None
    }
    ident["identity_key"] = f"{ident['source_path_norm']}|{ident['bytes_size']}|{ident['mtime_utc']}|{ident['ctime_utc']}|{ident['file_id'] or ''}"
    return ident

def open_db(cfg: Dict[str, Any]):
    dirs = ensure_dirs(cfg)
    db_path = dirs["db"] / "corpus.sqlite"
    con = sqlite3.connect(str(db_path))
    return con, db_path

def cmd_inventory(cfg):
    dirs = ensure_dirs(cfg)
    run_id = utc_stamp()
    out_csv = dirs["inventory"] / f"DRIVE_INVENTORY_{run_id}.csv"
    out_jsonl = dirs["inventory"] / f"DRIVE_INVENTORY_{run_id}.jsonl"
    rows = 0
    with out_csv.open("w", newline="", encoding="utf-8") as fc, out_jsonl.open("w", encoding="utf-8") as fj:
        w = csv.writer(fc)
        w.writerow(["path","size","mtime_utc","ext","kind","lane","case_id","identity_key"])
        for root in cfg.get("roots", []):
            rp = Path(root)
            if not rp.exists():
                fj.write(json.dumps({"warn":"missing_root","root":str(rp)}) + "\n")
                continue
            for p in rp.rglob("*"):
                try:
                    if not p.is_file():
                        continue
                    ident = identity_for(p)
                    lane = lane_for_path(str(p), cfg)
                    case_id = case_for_path(str(p), cfg)
                    ext = p.suffix.lower()
                    kind = kind_for_ext(ext)
                    w.writerow([ident["source_path_norm"], ident["bytes_size"], ident["mtime_utc"], ext, kind, lane, case_id or "", ident["identity_key"]])
                    fj.write(json.dumps({"identity": ident, "ext": ext, "kind": kind, "lane": lane, "case_id": case_id}) + "\n")
                    rows += 1
                except Exception as e:
                    fj.write(json.dumps({"error":"inventory_fail","path":str(p),"detail":str(e)}) + "\n")
    write_log(dirs, "inventory", {"rows": rows, "csv": str(out_csv), "jsonl": str(out_jsonl)})
    print(out_csv)
    print(out_jsonl)
    print(f"inventory_rows={rows}")

def cmd_initdb(cfg):
    dirs = ensure_dirs(cfg)
    con, db_path = open_db(cfg)
    schema = (Path(__file__).parent / "fts_schema.sql").read_text(encoding="utf-8")
    con.executescript(schema)
    con.commit()
    con.close()
    write_log(dirs, "initdb", {"db": str(db_path)})
    print(db_path)

def cmd_scan(cfg):
    dirs = ensure_dirs(cfg)
    con, db_path = open_db(cfg)
    atoms = 0
    for root in cfg.get("roots", []):
        rp = Path(root)
        if not rp.exists():
            continue
        for p in rp.rglob("*"):
            if not p.is_file():
                continue
            try:
                ident = identity_for(p)
                lane = lane_for_path(str(p), cfg)
                case_id = case_for_path(str(p), cfg)
                atom_id = f"FA::{uuid.uuid5(uuid.NAMESPACE_URL, ident['identity_key'])}"
                con.execute(
                    """INSERT OR REPLACE INTO fileatoms(
                        atom_id,source_path_norm,bytes_size,mtime_utc,ctime_utc,file_id,volume_serial,ext,kind,lane,case_id,discovered_at_utc,truth_tag,identity_key,labels_json
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        atom_id, ident["source_path_norm"], ident["bytes_size"], ident["mtime_utc"], ident["ctime_utc"], ident["file_id"], ident["volume_serial"],
                        p.suffix.lower(), kind_for_ext(p.suffix), lane, case_id, utc_iso(), "UNVERIFIED", ident["identity_key"], "[]"
                    ),
                )
                atoms += 1
            except Exception:
                continue
    con.commit(); con.close()
    write_log(dirs, "scan", {"atoms": atoms, "db": str(db_path)})
    print(db_path)
    print(f"scan_atoms={atoms}")

def cmd_extract(cfg):
    dirs = ensure_dirs(cfg)
    con, db_path = open_db(cfg)
    run_id = utc_stamp()
    text_dir = dirs["textbank"] / run_id
    text_dir.mkdir(parents=True, exist_ok=True)
    rows = con.execute("SELECT atom_id, source_path_norm FROM fileatoms").fetchall()
    extracted = 0
    for atom_id, src in rows:
        p = Path(src)
        if not p.exists():
            continue
        extractor, text, warnings = extract_text_generic(p)
        out_name = atom_id.replace("::","__").replace("/","_").replace("\\","_") + ".txt"
        out_path = text_dir / out_name
        out_path.write_text(text, encoding="utf-8", errors="ignore")
        con.execute(
            "INSERT INTO extractions(atom_id, extractor, extracted_at_utc, text_path, char_count, warnings_json) VALUES (?,?,?,?,?,?)",
            (atom_id, extractor, utc_iso(), str(out_path), len(text), json.dumps(warnings))
        )
        extracted += 1
    con.commit(); con.close()
    write_log(dirs, "extract", {"extracted": extracted, "text_dir": str(text_dir)})
    print(text_dir)
    print(f"extracted={extracted}")

def cmd_quoteize(cfg):
    dirs = ensure_dirs(cfg)
    con, db_path = open_db(cfg)
    rows = con.execute(
        "SELECT e.atom_id, e.text_path, f.lane, f.case_id FROM extractions e JOIN fileatoms f ON f.atom_id=e.atom_id "
        "WHERE e.extracted_at_utc = (SELECT MAX(e2.extracted_at_utc) FROM extractions e2 WHERE e2.atom_id=e.atom_id)"
    ).fetchall()
    q_count = 0
    ev_count = 0
    for atom_id, text_path, lane, case_id in rows:
        p = Path(text_path)
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        quote_dicts = []
        for start, end, chunk, page_hint in quoteize_text(text):
            if not chunk.strip():
                continue
            quote_id = f"QA::{uuid.uuid5(uuid.NAMESPACE_URL, atom_id + '::' + str(start) + '::' + str(end))}"
            pinpoint_scheme = "page_span" if page_hint else "text_span"
            pinpoint_value = f"p{page_hint}:{start}-{end}" if page_hint else f"{start}-{end}"
            quote_dicts.append({
                "quote_id": quote_id, "atom_id": atom_id, "text": chunk, "start_pos": start, "end_pos": end,
                "truth_tag": "UNVERIFIED", "pinpoint_scheme": pinpoint_scheme, "pinpoint_value": pinpoint_value,
                "page_hint": page_hint, "lane": lane, "case_id": case_id
            })
        for rec in quote_dicts:
            con.execute(
                "INSERT OR REPLACE INTO quotes(quote_id,atom_id,text,start_pos,end_pos,truth_tag,pinpoint_scheme,pinpoint_value,page_hint,lane,case_id) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (rec["quote_id"], rec["atom_id"], rec["text"], rec["start_pos"], rec["end_pos"], rec["truth_tag"], rec["pinpoint_scheme"], rec["pinpoint_value"], rec["page_hint"], rec["lane"], rec["case_id"])
            )
            con.execute("INSERT INTO corpus_fts(quote_id, atom_id, lane, case_id, text) VALUES (?,?,?,?,?)",
                        (rec["quote_id"], rec["atom_id"], rec["lane"] or "", rec["case_id"] or "", rec["text"]))
            q_count += 1

        for i, e in enumerate(eventize_quotes(quote_dicts[:200]), start=1):
            ev_id = f"EV::{uuid.uuid5(uuid.NAMESPACE_URL, atom_id + '::' + str(i) + '::' + e['action'])}"
            con.execute(
                "INSERT OR REPLACE INTO events(event_id,atom_id,action,actor,object,when_event_raw,when_event_utc,when_recorded_utc,truth_tag,support_quote_ids_json,lane,case_id) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (ev_id, atom_id, e["action"], None, None, e.get("when_event_raw"), None, utc_iso(), "UNVERIFIED", "[]", lane, case_id)
            )
            ev_count += 1
    con.commit(); con.close()
    write_log(dirs, "quoteize", {"quotes": q_count, "events": ev_count, "db": str(db_path)})
    print(db_path)
    print(f"quotes={q_count} events={ev_count}")

def cmd_build_pack(cfg, purpose, query, lane, case_id):
    dirs = ensure_dirs(cfg)
    _, db_path = open_db(cfg)
    max_quotes = int(cfg.get("pack_recipes", {}).get(purpose, {}).get("max_quotes", 120))
    pack_path = build_pack(db_path, dirs["packs"], purpose, query, lane=lane, case_id=case_id, max_quotes=max_quotes)
    write_log(dirs, "build_pack", {"pack": str(pack_path), "purpose": purpose, "lane": lane, "case_id": case_id})
    print(pack_path)

def _emit_court_artifacts(cp_dir: Path, pack: Dict[str, Any], vd) -> None:
    quotes = pack.get("quotes", [])
    # CASE_STATE
    case_state = {
        "lane": pack.get("scope", {}).get("lane"),
        "case_id": pack.get("scope", {}).get("case_id"),
        "forum_candidate": vd.forum,
        "vehicle_candidate": vd.candidate_vehicle,
        "quote_count": len(quotes),
        "event_count": len(pack.get("events", [])),
        "truth_tags": sorted(list({q.get("truth_tag","UNVERIFIED") for q in quotes})),
    }
    (cp_dir / "CASE_STATE.json").write_text(json.dumps(case_state, indent=2), encoding="utf-8")

    # VehicleMap
    (cp_dir / "VehicleMap.md").write_text(
        "# VehicleMap\n\n"
        f"- Forum candidate: {vd.forum}\n"
        f"- Vehicle candidate: {vd.candidate_vehicle}\n"
        f"- Rationale: {vd.rationale}\n"
        f"- Authority compass: {', '.join(vd.authority_compass)}\n"
        f"- Service compass: {', '.join(vd.service_compass)}\n",
        encoding="utf-8"
    )

    # ContextPack (snippets)
    with (cp_dir / "ContextPack.md").open("w", encoding="utf-8") as f:
        f.write("# ContextPack\n\n")
        for i, q in enumerate(quotes[:80], start=1):
            f.write(f"## Q{i} {q.get('quote_id')}\n")
            f.write(f"- Atom: {q.get('atom_id')}\n")
            f.write(f"- Pinpoint: {q.get('pinpoint_value')}\n\n")
            f.write(q.get("text","") + "\n\n")

    # SoRLedgerΔ (sources)
    with (cp_dir / "SoRLedger_Delta.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["quote_id","atom_id","pinpoint","truth_tag"])
        for q in quotes:
            w.writerow([q.get("quote_id"), q.get("atom_id"), q.get("pinpoint_value"), q.get("truth_tag")])

    # ExhibitMatrix
    with (cp_dir / "ExhibitMatrix.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["exhibit_no","quote_id","atom_id","pinpoint","snippet"])
        for i, q in enumerate(quotes, start=1):
            w.writerow([f"Exh-{i}", q.get("quote_id"), q.get("atom_id"), q.get("pinpoint_value"), (q.get("text","")[:180]).replace("\n"," ")])

    # Timeline + BiTemporal
    with (cp_dir / "BiTemporalTimeline.md").open("w", encoding="utf-8") as f:
        f.write("# BiTemporalTimeline\n\n")
        for e in pack.get("events", [])[:200]:
            f.write(f"- when_event_raw={e.get('when_event_raw')} | recorded={pack.get('created_at_utc')} | action={e.get('action')} | truth={e.get('truth_tag','UNVERIFIED')}\n")

    # Contradiction map
    cands = contradiction_pairs(quotes)
    (cp_dir / "ContradictionMap.json").write_text(json.dumps({"pairs": cands}, indent=2), encoding="utf-8")

    # AuthorityTriples
    triples = authority_triples_for_lane(pack.get("scope",{}).get("lane",""), vd.forum)
    (cp_dir / "AuthorityTriples.json").write_text(json.dumps({"triples": triples}, indent=2), encoding="utf-8")

    # Deadlines (fail-soft)
    (cp_dir / "Deadlines.md").write_text(
        "# Deadlines\n\n"
        "- STATUS: ACQUISITION_REQUIRED\n"
        "- Add exact entry/served dates from ROA/order/service proof.\n"
        "- Then compute TRIAL/COA/MSC/JTC timing windows in this file.\n",
        encoding="utf-8"
    )

    # Validation/RedTeam
    validation = {
        "readiness": {
            "quotes_present": bool(quotes),
            "pinpoints_nonempty_ratio": (sum(1 for q in quotes if q.get("pinpoint_value")) / max(1, len(quotes))),
            "authority_triples_count": len(triples),
            "has_timeline": True,
            "has_exhibit_matrix": True
        },
        "redteam_risks": [
            "Missing transcript page-line pinpoints for appellate-grade fact statements",
            "Authority pinpoints are acquisition stubs until official text graft is completed",
            "Hearsay/authentication objections need vehicle-specific handling"
        ]
    }
    (cp_dir / "Validation_RedTeam.json").write_text(json.dumps(validation, indent=2), encoding="utf-8")

    # SBNA
    (cp_dir / "SBNA.md").write_text(
        "# SBNA (Single Best Next Actions)\n\n"
        "1. Acquire file-stamped order/ROA and service proofs for this lane/case.\n"
        "2. Add transcript pinpoints for highest-value quotes.\n"
        "3. Complete AuthorityTriples pinpoints from official MI sources.\n"
        "4. Use DRAFT_BLOCKS_DROPIN + ProposedOrder + ServiceChecklist to finalize packet.\n",
        encoding="utf-8"
    )

    # Draft blocks + proposed order + service checklist
    (cp_dir / "DRAFT_BLOCKS_DROPIN.md").write_text(
        f"# Draft Blocks\n\n## Background\n- Lane: {pack.get('scope',{}).get('lane')}\n- Case: {pack.get('scope',{}).get('case_id') or 'UNKNOWN'}\n\n"
        "## Facts\n- Insert chronological facts from BiTemporalTimeline + ExhibitMatrix.\n\n"
        f"## Argument\n- Forum: {vd.forum}\n- Vehicle: {vd.candidate_vehicle}\n- Authority compass: " + ", ".join(vd.authority_compass) + "\n\n"
        "## Relief\n- Tailor requested relief to vehicle and record posture.\n",
        encoding="utf-8"
    )
    (cp_dir / "ProposedOrder.md").write_text(
        "# Proposed Order (Draft Skeleton)\n\n"
        "[Caption]\n\nIT IS ORDERED:\n1. [Relief item 1]\n2. [Relief item 2]\n\n"
        "Basis: See attached pack artifacts, exhibit matrix, and authority triples.\n",
        encoding="utf-8"
    )
    (cp_dir / "ServiceChecklist.md").write_text(
        "# ServiceChecklist\n\n"
        "- Correct parties and addresses\n"
        "- Method of service allowed for vehicle\n"
        "- Proof of service form completed\n"
        "- Entry date vs signed date vs served date recorded\n",
        encoding="utf-8"
    )

def cmd_courtpack(cfg, pack_path_str):
    dirs = ensure_dirs(cfg)
    pack_path = Path(pack_path_str)
    pack = json.loads(pack_path.read_text(encoding="utf-8"))
    lane = pack.get("scope", {}).get("lane") or "UNKNOWN"
    case_id = pack.get("scope", {}).get("case_id") or None
    vd = choose_vehicle(lane, pack.get("purpose",""), case_id)
    cp_id = f"COURTPACK_{utc_stamp()}_{uuid.uuid4().hex[:8]}"
    cp_dir = dirs["courtpacks"] / lane / (case_id or "NOCASE") / cp_id
    cp_dir.mkdir(parents=True, exist_ok=True)
    _emit_court_artifacts(cp_dir, pack, vd)
    manifest = {
        "courtpack_id": cp_id,
        "lane": lane,
        "case_id": case_id,
        "forum": vd.forum,
        "vehicle": vd.candidate_vehicle,
        "pack_source": str(pack_path),
        "generated_at_utc": utc_iso(),
        "files": sorted([p.name for p in cp_dir.iterdir() if p.is_file()])
    }
    (cp_dir / "PACK_MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    write_log(dirs, "courtpack", {"courtpack": str(cp_dir), "pack": str(pack_path), "lane": lane, "case_id": case_id})
    print(cp_dir)

def cmd_full_cycle(cfg, query, purpose, lane, case_id):
    cmd_inventory(cfg)
    cmd_initdb(cfg)
    cmd_scan(cfg)
    cmd_extract(cfg)
    cmd_quoteize(cfg)
    dirs = ensure_dirs(cfg)
    _, db_path = open_db(cfg)
    max_quotes = int(cfg.get("pack_recipes", {}).get(purpose, {}).get("max_quotes", 120))
    pack_path = build_pack(db_path, dirs["packs"], purpose, query, lane=lane, case_id=case_id, max_quotes=max_quotes)
    cmd_courtpack(cfg, str(pack_path))

def cmd_autopilot_all(cfg):
    dirs = ensure_dirs(cfg)
    # If DB is missing or empty, run full ingest stack first.
    db_path = dirs["db"] / "corpus.sqlite"
    needs_bootstrap = True
    if db_path.exists():
        try:
            con = sqlite3.connect(str(db_path))
            c = con.execute("SELECT COUNT(*) FROM fileatoms").fetchone()[0]
            q = con.execute("SELECT COUNT(*) FROM quotes").fetchone()[0]
            con.close()
            needs_bootstrap = (c == 0 or q == 0)
        except Exception:
            needs_bootstrap = True
    if needs_bootstrap:
        cmd_initdb(cfg); cmd_scan(cfg); cmd_extract(cfg); cmd_quoteize(cfg)

    created = []
    auto = cfg.get("autopilot", {})
    purposes = auto.get("purposes", ["timeline", "motion_draft"])
    queries = auto.get("default_queries", {})
    for lane in ["MEEK1","MEEK2","MEEK3","MEEK4"]:
        query = queries.get(lane, lane)
        for purpose in purposes:
            try:
                max_quotes = int(cfg.get("pack_recipes", {}).get(purpose, {}).get("max_quotes", 120))
                _, db_path = open_db(cfg)
                pack_path = build_pack(db_path, dirs["packs"], purpose, query, lane=lane, case_id=None, max_quotes=max_quotes)
                cmd_courtpack(cfg, str(pack_path))
                created.append({"lane": lane, "purpose": purpose, "pack": str(pack_path)})
            except Exception as e:
                write_log(dirs, "autopilot_error", {"lane": lane, "purpose": purpose, "error": str(e)})
    summary_path = dirs["validation"] / f"AUTOPILOT_SUMMARY_{utc_stamp()}.json"
    summary_path.write_text(json.dumps({"created": created, "count": len(created)}, indent=2), encoding="utf-8")
    write_log(dirs, "autopilot_all", {"summary": str(summary_path), "count": len(created)})
    print(summary_path)

def cmd_qa_validate(cfg):
    dirs = ensure_dirs(cfg)
    db_path = dirs["db"] / "corpus.sqlite"
    con = sqlite3.connect(str(db_path))
    counts = {
        "fileatoms": con.execute("SELECT COUNT(*) FROM fileatoms").fetchone()[0],
        "extractions": con.execute("SELECT COUNT(*) FROM extractions").fetchone()[0],
        "quotes": con.execute("SELECT COUNT(*) FROM quotes").fetchone()[0],
        "events": con.execute("SELECT COUNT(*) FROM events").fetchone()[0],
    }
    by_lane = {row[0]: row[1] for row in con.execute("SELECT lane, COUNT(*) FROM quotes GROUP BY lane").fetchall()}
    con.close()

    cp_root = dirs["courtpacks"]
    courtpacks = [p for p in cp_root.rglob("PACK_MANIFEST.json")] if cp_root.exists() else []
    issues = []
    if counts["quotes"] == 0:
        issues.append("No quotes indexed")
    if not courtpacks:
        issues.append("No courtpacks compiled")
    readiness = {
        "db_counts": counts,
        "quotes_by_lane": by_lane,
        "courtpack_count": len(courtpacks),
        "issues": issues,
        "status": "PASS" if not issues else "PARTIAL"
    }
    out = dirs["validation"] / f"QA_VALIDATE_{utc_stamp()}.json"
    out.write_text(json.dumps(readiness, indent=2), encoding="utf-8")
    write_log(dirs, "qa_validate", {"out": str(out), "status": readiness["status"]})
    print(out)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["inventory","initdb","scan","extract","quoteize","build-pack","courtpack","full-cycle","autopilot-all","qa-validate"])
    ap.add_argument("--config", required=True)
    ap.add_argument("--purpose", default="timeline")
    ap.add_argument("--query", default="parenting time custody PPO McNeill")
    ap.add_argument("--lane", default=None)
    ap.add_argument("--case-id", dest="case_id", default=None)
    ap.add_argument("--pack", default=None)
    args = ap.parse_args()

    cfg = load_jsonc(Path(args.config))
    try:
        if args.command == "inventory": cmd_inventory(cfg)
        elif args.command == "initdb": cmd_initdb(cfg)
        elif args.command == "scan": cmd_scan(cfg)
        elif args.command == "extract": cmd_extract(cfg)
        elif args.command == "quoteize": cmd_quoteize(cfg)
        elif args.command == "build-pack": cmd_build_pack(cfg, args.purpose, args.query, args.lane, args.case_id)
        elif args.command == "courtpack":
            if not args.pack:
                raise SystemExit("--pack required")
            cmd_courtpack(cfg, args.pack)
        elif args.command == "full-cycle":
            cmd_full_cycle(cfg, args.query, args.purpose, args.lane, args.case_id)
        elif args.command == "autopilot-all":
            cmd_autopilot_all(cfg)
        elif args.command == "qa-validate":
            cmd_qa_validate(cfg)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        traceback.print_exc()
        raise

if __name__ == "__main__":
    main()
