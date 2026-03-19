from __future__ import annotations
import argparse, csv, json, sqlite3, uuid, re
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from extractors import extract_text_generic
from quote_event_atomizer import quoteize_text, eventize_quotes
from mi_vehicle_router import choose_vehicle
from pack_router import build_pack

def load_jsonc(path: Path) -> Dict[str, Any]:
    txt = path.read_text(encoding="utf-8", errors="ignore")
    txt = re.sub(r"//.*", "", txt)
    txt = re.sub(r",\s*([}\]])", r"\1", txt)
    return json.loads(txt)

def utc_now() -> str:
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
        "logs": ws / "10_LOGS",
    }
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)
    return dirs

def lane_for_path(path_str: str, cfg: Dict[str, Any]) -> str:
    low = path_str.lower()
    for lane, needles in cfg.get("lanes", {}).items():
        for needle in needles:
            if needle.lower().replace("*","") in low:
                return lane
    return "UNKNOWN"

def case_for_path(path_str: str, cfg: Dict[str, Any]) -> Optional[str]:
    low = path_str.lower()
    for rule in cfg.get("case_rules", []):
        for n in rule.get("needles", []):
            if n.lower() in low:
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
    return {
        "source_path_norm": str(path.resolve()),
        "bytes_size": int(st.st_size),
        "mtime_utc": datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat(),
        "ctime_utc": datetime.fromtimestamp(st.st_ctime, tz=timezone.utc).isoformat(),
        "file_id": str(file_id) if file_id is not None else None,
        "volume_serial": None
    }

def open_db(cfg):
    dirs = ensure_dirs(cfg)
    db_path = dirs["db"] / "corpus.sqlite"
    con = sqlite3.connect(str(db_path))
    return con, db_path

def cmd_inventory(cfg):
    dirs = ensure_dirs(cfg)
    run_id = utc_now()
    out_csv = dirs["inventory"] / f"DRIVE_INVENTORY_{run_id}.csv"
    out_jsonl = dirs["inventory"] / f"DRIVE_INVENTORY_{run_id}.jsonl"
    rows = 0
    with out_csv.open("w", newline="", encoding="utf-8") as fc, out_jsonl.open("w", encoding="utf-8") as fj:
        w = csv.writer(fc)
        w.writerow(["path","size","mtime_utc","ext","kind","lane","case_id"])
        for root in cfg.get("roots", []):
            rp = Path(root)
            if not rp.exists():
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
                    w.writerow([ident["source_path_norm"], ident["bytes_size"], ident["mtime_utc"], ext, kind, lane, case_id or ""])
                    fj.write(json.dumps({"identity": ident, "ext": ext, "kind": kind, "lane": lane, "case_id": case_id}) + "\n")
                    rows += 1
                except Exception as e:
                    fj.write(json.dumps({"error":"inventory_fail","path":str(p),"detail":str(e)}) + "\n")
    print(out_csv)
    print(out_jsonl)
    print(f"inventory_rows={rows}")

def cmd_initdb(cfg):
    con, db_path = open_db(cfg)
    schema = (Path(__file__).parent / "fts_schema.sql").read_text(encoding="utf-8")
    con.executescript(schema)
    con.commit()
    con.close()
    print(db_path)

def cmd_scan(cfg):
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
                atom_id = f"FA::{uuid.uuid5(uuid.NAMESPACE_URL, ident['source_path_norm'])}"
                con.execute(
                    """INSERT OR REPLACE INTO fileatoms(
                        atom_id,source_path_norm,bytes_size,mtime_utc,ctime_utc,file_id,volume_serial,ext,kind,lane,case_id,discovered_at_utc,truth_tag,labels_json
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (atom_id, ident["source_path_norm"], ident["bytes_size"], ident["mtime_utc"], ident["ctime_utc"], ident["file_id"], ident["volume_serial"],
                     p.suffix.lower(), kind_for_ext(p.suffix), lane, case_id, datetime.now(timezone.utc).isoformat(), "UNVERIFIED", "[]")
                )
                atoms += 1
            except Exception:
                pass
    con.commit(); con.close()
    print(db_path)
    print(f"scan_atoms={atoms}")

def cmd_extract(cfg):
    dirs = ensure_dirs(cfg)
    con, db_path = open_db(cfg)
    run_id = utc_now()
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
            (atom_id, extractor, datetime.now(timezone.utc).isoformat(), str(out_path), len(text), json.dumps(warnings))
        )
        extracted += 1
    con.commit(); con.close()
    print(text_dir)
    print(f"extracted={extracted}")

def cmd_quoteize(cfg):
    con, db_path = open_db(cfg)
    rows = con.execute(
        "SELECT e.atom_id, e.text_path, f.lane, f.case_id FROM extractions e JOIN fileatoms f ON f.atom_id=e.atom_id ORDER BY e.extracted_at_utc DESC"
    ).fetchall()
    q_count = 0; ev_count = 0
    for atom_id, text_path, lane, case_id in rows:
        p = Path(text_path)
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        quotes = []
        for (start, end, chunk) in quoteize_text(text):
            quote_id = f"QA::{uuid.uuid5(uuid.NAMESPACE_URL, atom_id + '::' + str(start) + '::' + str(end))}"
            quotes.append((quote_id, atom_id, chunk, start, end, "UNVERIFIED", "text_span", f"{start}-{end}", lane, case_id))
        for rec in quotes:
            con.execute("INSERT OR REPLACE INTO quotes(quote_id,atom_id,text,start_pos,end_pos,truth_tag,pinpoint_scheme,pinpoint_value,lane,case_id) VALUES (?,?,?,?,?,?,?,?,?,?)", rec)
            con.execute("INSERT INTO corpus_fts(quote_id, atom_id, lane, case_id, text) VALUES (?,?,?,?,?)", (rec[0], rec[1], rec[8] or "", rec[9] or "", rec[2]))
            q_count += 1
        events = eventize_quotes([{"text": q[2]} for q in quotes[:50]])
        for i, e in enumerate(events, start=1):
            ev_id = f"EV::{uuid.uuid5(uuid.NAMESPACE_URL, atom_id + '::' + str(i) + '::' + e['action'])}"
            con.execute(
                "INSERT OR REPLACE INTO events(event_id, atom_id, action, actor, object, when_event_utc, when_recorded_utc, truth_tag, support_quote_ids_json, lane, case_id) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (ev_id, atom_id, e["action"], None, None, None, datetime.now(timezone.utc).isoformat(), "UNVERIFIED", "[]", lane, case_id)
            )
            ev_count += 1
    con.commit(); con.close()
    print(db_path)
    print(f"quotes={q_count} events={ev_count}")

def cmd_build_pack(cfg, purpose, query, lane, case_id):
    dirs = ensure_dirs(cfg)
    _, db_path = open_db(cfg)
    max_quotes = int(cfg.get("pack_recipes", {}).get(purpose, {}).get("max_quotes", 120))
    pack_path = build_pack(db_path, dirs["packs"], purpose, query, lane=lane, case_id=case_id, max_quotes=max_quotes)
    print(pack_path)

def cmd_courtpack(cfg, pack_path_str):
    dirs = ensure_dirs(cfg)
    pack_path = Path(pack_path_str)
    pack = json.loads(pack_path.read_text(encoding="utf-8"))
    lane = pack.get("scope", {}).get("lane") or "UNKNOWN"
    case_id = pack.get("scope", {}).get("case_id") or None
    vd = choose_vehicle(lane, pack.get("purpose",""), case_id)
    cp_id = f"COURTPACK_{utc_now()}_{uuid.uuid4().hex[:8]}"
    cp_dir = dirs["courtpacks"] / lane / (case_id or "NOCASE") / cp_id
    cp_dir.mkdir(parents=True, exist_ok=True)

    (cp_dir / "DRAFT_BLOCKS_DROPIN.md").write_text(
        f"# Draft Blocks — {cp_id}\n\n## Background\n- [Insert Pack facts]\n\n## Facts\n- [Chronology]\n\n## Argument\n- Forum: {vd.forum}\n- Vehicle: {vd.candidate_vehicle}\n- Rationale: {vd.rationale}\n\n## Relief\n- [Tailor relief]\n",
        encoding="utf-8"
    )
    with (cp_dir / "EXHIBIT_MATRIX.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["exhibit_no","quote_id","atom_id","pinpoint","snippet"])
        for i, q in enumerate(pack.get("quotes", []), start=1):
            w.writerow([f"Exh-{i}", q.get("quote_id"), q.get("atom_id"), q.get("pinpoint_value","PINPOINT_MISSING"), (q.get("text","")[:180]).replace("\n"," ")])
    (cp_dir / "VEHICLE_MAP.md").write_text(f"# Vehicle Map\n\n- Lane: {lane}\n- Case: {case_id or 'UNKNOWN'}\n- Forum: {vd.forum}\n- Vehicle: {vd.candidate_vehicle}\n- Rationale: {vd.rationale}\n", encoding="utf-8")
    (cp_dir / "ACQUISITION_TASKS.md").write_text("# Acquisition Tasks\n\n- Add file-stamped orders/ROA\n- Add transcript page-line pinpoints\n- Verify MCR/MCL/MRE/MJI pinpoints\n", encoding="utf-8")
    manifest = {
        "courtpack_id": cp_id,
        "lane": lane,
        "case_id": case_id,
        "forum": vd.forum,
        "vehicle": vd.candidate_vehicle,
        "pack_source": str(pack_path),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "files": sorted([p.name for p in cp_dir.iterdir() if p.is_file()])
    }
    (cp_dir / "PACK_MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(cp_dir)

def cmd_full_cycle(cfg, query, purpose, lane, case_id):
    cmd_inventory(cfg); cmd_initdb(cfg); cmd_scan(cfg); cmd_extract(cfg); cmd_quoteize(cfg)
    dirs = ensure_dirs(cfg)
    _, db_path = open_db(cfg)
    max_quotes = int(cfg.get("pack_recipes", {}).get(purpose, {}).get("max_quotes", 120))
    pack_path = build_pack(db_path, dirs["packs"], purpose, query, lane=lane, case_id=case_id, max_quotes=max_quotes)
    cmd_courtpack(cfg, str(pack_path))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["inventory","initdb","scan","extract","quoteize","build-pack","courtpack","full-cycle"])
    ap.add_argument("--config", required=True)
    ap.add_argument("--purpose", default="timeline")
    ap.add_argument("--query", default="parenting time custody PPO McNeill")
    ap.add_argument("--lane", default=None)
    ap.add_argument("--case-id", dest="case_id", default=None)
    ap.add_argument("--pack", default=None)
    args = ap.parse_args()
    cfg = load_jsonc(Path(args.config))
    if args.command == "inventory": cmd_inventory(cfg)
    elif args.command == "initdb": cmd_initdb(cfg)
    elif args.command == "scan": cmd_scan(cfg)
    elif args.command == "extract": cmd_extract(cfg)
    elif args.command == "quoteize": cmd_quoteize(cfg)
    elif args.command == "build-pack": cmd_build_pack(cfg, args.purpose, args.query, args.lane, args.case_id)
    elif args.command == "courtpack":
        if not args.pack: raise SystemExit("--pack required")
        cmd_courtpack(cfg, args.pack)
    elif args.command == "full-cycle": cmd_full_cycle(cfg, args.query, args.purpose, args.lane, args.case_id)

if __name__ == "__main__":
    main()
