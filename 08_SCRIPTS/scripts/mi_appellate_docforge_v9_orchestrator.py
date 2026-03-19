#!/usr/bin/env python3
"""
MI Appellate DocForge V9 Accelerator (read-only ingest, no SHA-256 default)
Commands:
  inventory      -> inventory files under roots
  initdb         -> create SQLite schema
  scan           -> build FileAtoms + insert fileatoms
  extract        -> extract text into TextBank + insert extractions
  quoteize       -> chunk into QuoteAtoms + index FTS
  build-pack     -> build a targeted Pack from lexical query
  courtpack      -> compile CourtPack folder from one pack
  full-cycle     -> inventory + initdb + scan + extract + quoteize + build-pack(optional)
"""
from __future__ import annotations
import argparse, csv, datetime as dt, fnmatch, json, os, re, sqlite3, sys, textwrap
from pathlib import Path
from typing import Dict, Any, Iterable, List, Tuple

try:
    import docx  # python-docx
except Exception:
    docx = None

def utc_now():
    return dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

def strip_jsonc(s: str) -> str:
    s = re.sub(r'//.*', '', s)
    return s

def load_config(path: Path) -> Dict[str, Any]:
    return json.loads(strip_jsonc(path.read_text(encoding='utf-8')))

def norm_path(p: str) -> str:
    return os.path.normpath(p).replace('\\', '/')

def ensure_dirs(work: Path):
    for rel in [
        "00_POINTERS", "02_TEXTBANK/text", "03_INDEX", "04_PACKS", "05_COURTPACKS",
        "10_LOGS/run_ledger", "10_LOGS/reports"
    ]:
        (work / rel).mkdir(parents=True, exist_ok=True)

def log_jsonl(work: Path, event: Dict[str, Any]):
    p = work / "10_LOGS/run_ledger" / "RUN_LEDGER.jsonl"
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")

def connect_db(work: Path):
    dbp = work / "03_INDEX" / "corpus.sqlite"
    conn = sqlite3.connect(dbp)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(work: Path, schema_path: Path):
    ensure_dirs(work)
    conn = connect_db(work)
    conn.executescript(schema_path.read_text(encoding="utf-8"))
    conn.commit()
    conn.close()
    log_jsonl(work, {"ts": utc_now(), "op": "initdb", "status": "ok", "schema": str(schema_path)})

def iter_files(roots: List[str]) -> Iterable[Path]:
    for r in roots:
        rp = Path(r)
        if not rp.exists():
            continue
        if rp.is_file():
            yield rp
            continue
        for path in rp.rglob("*"):
            if path.is_file():
                yield path

def classify_lane_case(p: str, cfg: Dict[str, Any]) -> Tuple[str, str|None]:
    low = p.lower()
    lane = "UNKNOWN"
    for lname, patterns in cfg.get("lanes", {}).items():
        if any(fnmatch.fnmatch(low, pat.lower()) for pat in patterns):
            lane = lname
            break
    case_id = None
    for rule in cfg.get("case_rules", []):
        if any(fnmatch.fnmatch(low, pat.lower()) for pat in rule.get("match", [])):
            case_id = rule.get("case_id")
            break
    return lane, case_id

def detect_kind(ext: str, cfg: Dict[str, Any]) -> str:
    return cfg.get("doc_kind_map", {}).get(ext.lower(), "other")

def atom_id_for(path: Path, st) -> str:
    # Deterministic enough, no SHA-256. Uses path + size + mtime + inode-ish
    inode = getattr(st, "st_ino", 0)
    token = f"{norm_path(str(path))}|{st.st_size}|{int(st.st_mtime)}|{inode}"
    # cheap deterministic id
    import zlib
    return f"FA::{zlib.crc32(token.encode('utf-8')):08x}"

def inventory(work: Path, cfg: Dict[str, Any]):
    ensure_dirs(work)
    rows = []
    for fp in iter_files(cfg.get("roots", [])):
        try:
            st = fp.stat()
            lane, case_id = classify_lane_case(str(fp), cfg)
            rows.append({
                "path": str(fp), "size": st.st_size, "mtime": dt.datetime.utcfromtimestamp(st.st_mtime).isoformat()+"Z",
                "ext": fp.suffix.lower(), "lane": lane, "case_id": case_id or ""
            })
        except Exception as e:
            rows.append({"path": str(fp), "size": -1, "mtime": "", "ext": fp.suffix.lower(), "lane": "ERR", "case_id": str(e)})
    rows.sort(key=lambda r: (r["lane"], r["case_id"], r["path"]))
    out_dir = work / "10_LOGS" / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    csvp = out_dir / "DRIVE_INVENTORY.csv"
    jsonp = out_dir / "DRIVE_INVENTORY.json"
    with csvp.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["path","size","mtime","ext","lane","case_id"])
        w.writeheader(); w.writerows(rows)
    jsonp.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    log_jsonl(work, {"ts": utc_now(), "op": "inventory", "status": "ok", "files": len(rows), "csv": str(csvp), "json": str(jsonp)})
    print(f"Inventory complete: {len(rows)} files")

def scan(work: Path, cfg: Dict[str, Any]):
    ensure_dirs(work)
    conn = connect_db(work)
    inserted = 0
    for fp in iter_files(cfg.get("roots", [])):
        try:
            st = fp.stat()
        except Exception:
            continue
        ext = fp.suffix.lower()
        kind = detect_kind(ext, cfg)
        lane, case_id = classify_lane_case(str(fp), cfg)
        atom_id = atom_id_for(fp, st)
        ctime = getattr(st, "st_ctime", None)
        conn.execute("""INSERT OR REPLACE INTO fileatoms
            (atom_id, source_path_norm, bytes_size, mtime_utc, ctime_utc, file_id, volume_serial, ext, kind, lane, case_id, discovered_at_utc, truth_tag)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (
            atom_id, norm_path(str(fp)), st.st_size,
            dt.datetime.utcfromtimestamp(st.st_mtime).isoformat()+"Z",
            dt.datetime.utcfromtimestamp(ctime).isoformat()+"Z" if ctime else None,
            str(getattr(st, "st_ino", "")) or None,
            None,
            ext, kind, lane, case_id, utc_now(), "UNVERIFIED"
        ))
        inserted += 1
    conn.commit(); conn.close()
    log_jsonl(work, {"ts": utc_now(), "op": "scan", "status": "ok", "inserted": inserted})
    print(f"Scanned fileatoms: {inserted}")

def extract_txt(fp: Path) -> str:
    return fp.read_text(encoding="utf-8", errors="ignore")

def extract_docx(fp: Path) -> str:
    if docx is None:
        raise RuntimeError("python-docx not installed")
    d = docx.Document(str(fp))
    return "\n".join(p.text for p in d.paragraphs)

def extract_pdf(fp: Path) -> str:
    # best-effort pypdf/PyPDF2
    for mod in ("pypdf", "PyPDF2"):
        try:
            m = __import__(mod)
            reader = m.PdfReader(str(fp))
            out = []
            for i, page in enumerate(reader.pages, start=1):
                try:
                    t = page.extract_text() or ""
                except Exception:
                    t = ""
                out.append(f"\n\n[[PDF_PAGE_{i}]]\n" + t)
            return "".join(out)
        except Exception:
            continue
    raise RuntimeError("No PDF text extractor available")

def extract(work: Path, cfg: Dict[str, Any]):
    ensure_dirs(work)
    conn = connect_db(work)
    cur = conn.execute("SELECT atom_id, source_path_norm, kind FROM fileatoms ORDER BY source_path_norm")
    count = 0
    for row in cur:
        fp = Path(row["source_path_norm"])
        if not fp.exists():
            continue
        kind = row["kind"]
        text = None
        extractor = "other"
        warnings = []
        try:
            if kind == "txt":
                text = extract_txt(fp); extractor = "txt"
            elif kind == "docx":
                text = extract_docx(fp); extractor = "docx"
            elif kind == "pdf":
                text = extract_pdf(fp); extractor = "pdf_text"
            else:
                continue
        except Exception as e:
            warnings.append(str(e))
            continue
        rel_text = f"02_TEXTBANK/text/{row['atom_id']}.txt"
        outp = work / rel_text
        outp.parent.mkdir(parents=True, exist_ok=True)
        outp.write_text(text, encoding="utf-8")
        conn.execute("""INSERT OR REPLACE INTO extractions
            (atom_id, extractor, extracted_at_utc, text_path, char_count, warnings_json)
            VALUES (?, ?, ?, ?, ?, ?)""", (
                row["atom_id"], extractor, utc_now(), rel_text, len(text), json.dumps(warnings, ensure_ascii=False)
            ))
        count += 1
    conn.commit(); conn.close()
    log_jsonl(work, {"ts": utc_now(), "op": "extract", "status": "ok", "count": count})
    print(f"Extractions complete: {count}")

def split_quotes(text: str, chunk_target: int = 1200) -> List[Tuple[int,int,str]]:
    paras = [p.strip() for p in re.split(r'\n\s*\n+', text) if p.strip()]
    out = []
    pos = 0
    for para in paras:
        # locate sequentially
        idx = text.find(para, pos)
        if idx < 0: idx = pos
        if len(para) <= chunk_target:
            out.append((idx, idx+len(para), para))
        else:
            start = 0
            while start < len(para):
                chunk = para[start:start+chunk_target]
                out.append((idx+start, idx+start+len(chunk), chunk))
                start += chunk_target
        pos = idx + len(para)
    return out

def quoteize(work: Path):
    ensure_dirs(work)
    conn = connect_db(work)
    rows = conn.execute("""
        SELECT e.atom_id, e.text_path, f.lane, f.case_id
        FROM extractions e JOIN fileatoms f ON f.atom_id = e.atom_id
        ORDER BY e.atom_id
    """).fetchall()
    qcount = 0
    for r in rows:
        tp = work / r["text_path"]
        if not tp.exists():
            continue
        text = tp.read_text(encoding="utf-8", errors="ignore")
        chunks = split_quotes(text)
        for i,(s,e,ch) in enumerate(chunks, start=1):
            qid = f"Q::{r['atom_id']}::{i:04d}"
            conn.execute("""INSERT OR REPLACE INTO quotes
                (quote_id, atom_id, text, start_pos, end_pos, pinpoint_scheme, pinpoint_value, truth_tag, relevance)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""", (
                    qid, r["atom_id"], ch, s, e, "char_span", f"{s}-{e}", "UNVERIFIED", 0.0
                ))
            conn.execute("""INSERT INTO quotes_fts (quote_id, atom_id, lane, case_id, text) VALUES (?, ?, ?, ?, ?)""", (
                qid, r["atom_id"], r["lane"], r["case_id"] or "", ch
            ))
            qcount += 1
    conn.commit(); conn.close()
    log_jsonl(work, {"ts": utc_now(), "op": "quoteize", "status": "ok", "quotes": qcount})
    print(f"Quote atoms indexed: {qcount}")

def build_pack(work: Path, purpose: str, query: str, lane: str|None=None, case_id: str|None=None, max_quotes: int=120):
    ensure_dirs(work)
    conn = connect_db(work)
    where = []
    params: List[Any] = []
    fts_query = query.strip()
    sql = """SELECT q.quote_id,q.atom_id,q.text,q.start_pos,q.end_pos,q.pinpoint_scheme,q.pinpoint_value,
                    f.lane,f.case_id,f.source_path_norm
             FROM quotes_fts fts
             JOIN quotes q ON q.quote_id=fts.quote_id
             JOIN fileatoms f ON f.atom_id=q.atom_id
             WHERE quotes_fts MATCH ?"""
    params.append(fts_query)
    if lane:
        sql += " AND f.lane=?"; params.append(lane)
    if case_id:
        sql += " AND f.case_id=?"; params.append(case_id)
    sql += " ORDER BY bm25(quotes_fts) LIMIT ?"
    params.append(max_quotes)
    hits = conn.execute(sql, params).fetchall()
    pack_id = f"PACK::{purpose}::{dt.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}"
    pack_dir = work / "04_PACKS" / pack_id.replace("::","__")
    pack_dir.mkdir(parents=True, exist_ok=True)
    quotes = []
    snippets = []
    for h in hits:
        qobj = {
            "quote_id": h["quote_id"], "atom_id": h["atom_id"], "text": h["text"], "start": h["start_pos"], "end": h["end_pos"],
            "pinpoint": {"scheme": h["pinpoint_scheme"] or "char_span", "value": h["pinpoint_value"] or "", "confidence": 0.25},
            "truth_tag": "UNVERIFIED", "relevance": 0.0,
            "lane": h["lane"], "case_id": h["case_id"] or "", "source_path_norm": h["source_path_norm"]
        }
        quotes.append(qobj)
        snippets.append(f"[{qobj['quote_id']}] {qobj['source_path_norm']} @ {qobj['pinpoint']['value']}\n{qobj['text']}\n")
    pack = {
        "pack_id": pack_id,
        "purpose": purpose,
        "scope": {"lane": lane or "", "case_id": case_id or ""},
        "created_at_utc": utc_now(),
        "query_text": query,
        "quotes": quotes,
        "events": [],
        "authority_triples": [],
        "synthesis_instructions": "Use only supplied quotes for facts; unknowns become acquisition tasks; draft Michigan court-ready drop-in blocks."
    }
    (pack_dir / "pack.json").write_text(json.dumps(pack, ensure_ascii=False, indent=2), encoding="utf-8")
    (pack_dir / "snippets.txt").write_text("\n".join(snippets), encoding="utf-8")
    (pack_dir / "timeline.md").write_text("# Bi-Temporal Timeline (seed)\n\nBuild from quote dates + record dates.\n", encoding="utf-8")
    (pack_dir / "ACQUISITION_TASKS.md").write_text("# Acquisition Tasks\n\n- Verify transcript pinpoints\n- Verify ROA dates\n- Verify service proofs\n", encoding="utf-8")
    conn.execute("INSERT OR REPLACE INTO packs (pack_id,purpose,scope_json,created_at_utc,query_text,pack_json) VALUES (?,?,?,?,?,?)",
                 (pack_id, purpose, json.dumps(pack["scope"]), pack["created_at_utc"], query, json.dumps(pack)))
    conn.commit(); conn.close()
    log_jsonl(work, {"ts": utc_now(), "op": "build-pack", "status": "ok", "pack_id": pack_id, "hits": len(hits)})
    print(f"Built pack: {pack_id} ({len(hits)} quotes)")
    return pack_id

def courtpack(work: Path, pack_id: str, lane: str, vehicle: str, court_level: str):
    ensure_dirs(work)
    conn = connect_db(work)
    row = conn.execute("SELECT pack_json FROM packs WHERE pack_id=?", (pack_id,)).fetchone()
    if not row:
        raise SystemExit(f"Pack not found: {pack_id}")
    pack = json.loads(row["pack_json"])
    cp_id = f"COURTPACK::{lane}::{vehicle}::{dt.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}"
    cp_dir = work / "05_COURTPACKS" / cp_id.replace("::","__")
    cp_dir.mkdir(parents=True, exist_ok=True)
    (cp_dir / "PACK_MANIFEST.json").write_text(json.dumps({
        "courtpack_id": cp_id, "lane": lane, "vehicle": vehicle, "court_level": court_level,
        "generated_at_utc": utc_now(), "source_pack_ids":[pack_id],
        "known_gaps": ["Transcript pinpoints", "Verified filing deadlines", "Proofs of service"]
    }, indent=2), encoding="utf-8")
    (cp_dir / "DRAFT_BLOCKS.md").write_text("# Draft Blocks\n\n## Background\n\n## Facts\n\n## Argument\n\n## Relief Requested\n", encoding="utf-8")
    (cp_dir / "EXHIBIT_MATRIX.csv").write_text("exhibit_id,quote_id,source_path,pinpoint,topic\n", encoding="utf-8")
    (cp_dir / "SERVICE_CHECKLIST.md").write_text("# Service Checklist\n\n- Confirm parties and service method\n- Attach proof of service\n", encoding="utf-8")
    (cp_dir / "INSTRUCTIONS_STEP_BY_STEP.txt").write_text(
        "1) Review PACK_MANIFEST and DRAFT_BLOCKS\n2) Fill exact MI authority pinpoints\n3) Verify dates/timeliness\n4) Attach exhibits and service proof\n",
        encoding="utf-8"
    )
    conn.close()
    log_jsonl(work, {"ts": utc_now(), "op": "courtpack", "status": "ok", "courtpack_id": cp_id})
    print(f"CourtPack compiled: {cp_id}")

def full_cycle(args):
    cfg = load_config(Path(args.config))
    work = Path(args.workspace or cfg["workspace_root"])
    inventory(work, cfg)
    init_db(work, Path(args.schema))
    scan(work, cfg)
    extract(work, cfg)
    quoteize(work)
    if args.query:
        pack_id = build_pack(work, args.purpose, args.query, args.lane, args.case_id, args.max_quotes)
        if args.vehicle:
            courtpack(work, pack_id, args.lane or "UNKNOWN", args.vehicle, args.court_level)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=str(Path(__file__).resolve().parents[1] / "CONFIG" / "litigationos_mi_appellate_docforge_v9_accel.jsonc"))
    ap.add_argument("--workspace", default=None)
    ap.add_argument("--schema", default=str(Path(__file__).resolve().parents[1] / "SCHEMA" / "mi_appellate_docforge_v9.sql"))
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("inventory")
    sub.add_parser("initdb")
    sub.add_parser("scan")
    sub.add_parser("extract")
    sub.add_parser("quoteize")

    bp = sub.add_parser("build-pack")
    bp.add_argument("--purpose", required=True)
    bp.add_argument("--query", required=True)
    bp.add_argument("--lane", default=None)
    bp.add_argument("--case-id", default=None)
    bp.add_argument("--max-quotes", type=int, default=120)

    cp = sub.add_parser("courtpack")
    cp.add_argument("--pack-id", required=True)
    cp.add_argument("--lane", required=True)
    cp.add_argument("--vehicle", required=True)
    cp.add_argument("--court-level", default="TRIAL")

    fc = sub.add_parser("full-cycle")
    fc.add_argument("--purpose", default="timeline")
    fc.add_argument("--query", default=None)
    fc.add_argument("--lane", default=None)
    fc.add_argument("--case-id", default=None)
    fc.add_argument("--max-quotes", type=int, default=120)
    fc.add_argument("--vehicle", default=None)
    fc.add_argument("--court-level", default="TRIAL")

    args = ap.parse_args()
    cfg = load_config(Path(args.config))
    work = Path(args.workspace or cfg["workspace_root"])

    if args.cmd == "inventory":
        inventory(work, cfg)
    elif args.cmd == "initdb":
        init_db(work, Path(args.schema))
    elif args.cmd == "scan":
        scan(work, cfg)
    elif args.cmd == "extract":
        extract(work, cfg)
    elif args.cmd == "quoteize":
        quoteize(work)
    elif args.cmd == "build-pack":
        build_pack(work, args.purpose, args.query, args.lane, args.case_id, args.max_quotes)
    elif args.cmd == "courtpack":
        courtpack(work, args.pack_id, args.lane, args.vehicle, args.court_level)
    elif args.cmd == "full-cycle":
        full_cycle(args)

if __name__ == "__main__":
    main()
