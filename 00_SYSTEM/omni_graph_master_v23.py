# omni_graph_master_v23.py
# Hardened ingest + graph engine. Safer scanner, better diagnostics.
# Python 3.9+.

import os, sys, time, re, json, hashlib, sqlite3, zipfile, argparse, traceback, fnmatch
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

# Optional deps
try:
    import fitz  # PyMuPDF
except Exception:
    fitz = None
try:
    import docx  # python-docx
except Exception:
    docx = None
try:
    from PIL import Image
except Exception:
    Image = None
try:
    import pytesseract
except Exception:
    pytesseract = None
try:
    import exifread
except Exception:
    exifread = None
try:
    from neo4j import GraphDatabase
except Exception:
    GraphDatabase = None

DEFAULT_EXCLUDES = [
    'System Volume Information', '$RECYCLE.BIN', 'FOUND.*', 'Config.Msi',
    'pagefile.sys', 'hiberfil.sys', 'swapfile.sys'
]

TEXT_EXT = {'.txt', '.md', '.csv', '.json'}
DOC_EXT  = {'.docx'}
PDF_EXT  = {'.pdf'}
IMG_EXT  = {'.png', '.jpg', '.jpeg', '.tif', '.tiff', '.bmp', '.webp'}
INGEST_EXT = TEXT_EXT | DOC_EXT | PDF_EXT | IMG_EXT

CATEGORY_RULES = [
    ("FOC_FORM", r"\bFOC[-\s]?\d{1,3}[a-z]?\b"),
    ("SCAO_FORM", r"\b(MC|JC|FOC|SCAO)[-\s]?\d{1,4}[a-z]?\b"),
    ("CASE_DC",  r"\b20\d{2}[-_](\d{6}|\d{7})[-_](DC|DM|DZ|DP|DO)\b"),
    ("CASE_PP",  r"\b20\d{2}[-_](\d{6}|\d{7})[-_](PP)\b"),
    ("PPO",      r"\b(PPO|Personal Protection Order|Show Cause)\b"),
    ("CUSTODY",  r"\b(custody|parenting\s*time|visitation|722\.27a|best interest factors)\b"),
    ("HOUSING",  r"\b(eviction|landlord|MHP|rent|EGLE|sewage|Homes of America|Shady Oaks)\b"),
    ("JUDICIAL", r"\b(MCR|MCL|Benchbook|Canon)\b"),
]

ENTITY_PATTERNS = {
    "CASE_NO": r"\b20\d{2}[-_](\d{6}|\d{7})[-_](?:[A-Z]{2})\b",
    "MCR":     r"\bMCR\s*\d\.\d+(?:\([A-Za-z0-9]+\))*\b",
    "MCL":     r"\bMCL\s*\d+\.?\d*(?:\([A-Za-z0-9]+\))*\b",
    "CANON":   r"\bCanon\s*[1-9]\b",
    "FORM":    r"\b(?:FOC|MC|SCAO|JC)[-\s]?\d{1,4}[a-z]?\b",
}

DATE_PATTERNS = [
    r"\b(20\d{2}[-/\.](0?[1-9]|1[0-2])[-/\.](0?[1-9]|[12]\d|3[01]))\b",
    r"\b((0?[1-9]|1[0-2])[-/\.](0?[1-9]|[12]\d|3[01])[-/\.]20\d{2})\b",
    r"\b(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
    r"Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|"
    r"Dec(?:ember)?)\s+(0?[1-9]|[12]\d|3[01]),\s+20\d{2}\b",
]

SEED_PARTIES = {"Andrew J. Pigors", "Emily Watson", "Judge McNeill", "Shady Oaks Park MHP LLC",
                "Homes of America", "Partridge Equity", "Alden Global Capital", "EGLE",
                "Friend of the Court"}

class Paths:
    def __init__(self, base_out: str):
        base = Path(base_out)
        self.base = base
        self.base.mkdir(parents=True, exist_ok=True)
        self.db = base / "autogrow_state.db"
        self.exports = base / "exports"
        self.exports.mkdir(parents=True, exist_ok=True)
        self.txt_dir = self.exports / "txt"
        self.txt_dir.mkdir(parents=True, exist_ok=True)
        self.bundle = self.exports / "AUTO_BUNDLE.zip"
        self.nodes_json = self.exports / "graph_nodes.json"
        self.edges_json = self.exports / "graph_edges.json"
        self.ingest_log = self.exports / "ingest_log.jsonl"
        self.error_log = self.exports / "errors.log"

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def sha256_path(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def log_line(paths: Paths, d: Dict[str, Any]):
    paths.ingest_log.parent.mkdir(parents=True, exist_ok=True)
    with paths.ingest_log.open("a", encoding="utf-8") as f:
        f.write(json.dumps(d, ensure_ascii=False) + "\n")

def log_error(paths: Paths, msg: str):
    paths.error_log.parent.mkdir(parents=True, exist_ok=True)
    with paths.error_log.open("a", encoding="utf-8") as f:
        f.write(f"[{utc_now_iso()}] {msg}\n")

def db_connect(db_path: Path):
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn

def db_init(paths: Paths):
    conn = db_connect(paths.db)
    cur = conn.cursor()
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS files(
        id INTEGER PRIMARY KEY,
        path TEXT UNIQUE,
        size INTEGER,
        mtime REAL,
        sha256 TEXT,
        ingested_at TEXT,
        text_path TEXT,
        meta_json TEXT,
        category TEXT,
        img_phash TEXT,
        text_simhash TEXT
    );
    CREATE TABLE IF NOT EXISTS events(
        id INTEGER PRIMARY KEY,
        file_id INTEGER,
        date TEXT,
        label TEXT,
        type TEXT,
        source_ref TEXT
    );
    CREATE TABLE IF NOT EXISTS nodes(
        id INTEGER PRIMARY KEY,
        key TEXT UNIQUE,
        label TEXT,
        type TEXT,
        meta_json TEXT
    );
    CREATE TABLE IF NOT EXISTS edges(
        id INTEGER PRIMARY KEY,
        src_key TEXT,
        dst_key TEXT,
        type TEXT,
        meta_json TEXT
    );
    CREATE TABLE IF NOT EXISTS patterns(
        id INTEGER PRIMARY KEY,
        name TEXT UNIQUE,
        regex TEXT,
        type TEXT,
        enabled INTEGER DEFAULT 1
    );
    """)
    for name, rx in ENTITY_PATTERNS.items():
        cur.execute("INSERT OR IGNORE INTO patterns(name, regex, type, enabled) VALUES(?,?,?,1)", (name, rx, "ENTITY"))
    conn.commit()
    conn.close()

def image_ahash(p: Path, size: int = 8) -> Optional[str]:
    if not Image:
        return None
    try:
        with Image.open(str(p)) as im:
            im = im.convert("L").resize((size, size))
            pixels = list(im.getdata())
            avg = sum(pixels) / len(pixels)
            bits = 0
            for i, px in enumerate(pixels):
                bits |= (1 if px >= avg else 0) << i
            return f"{bits:0{size*size//4}x}"
    except Exception:
        return None

def simhash_text(text: str, bitlen: int = 64) -> str:
    v = [0]*bitlen
    for tok in re.findall(r"\w+", text.lower()):
        h = int(hashlib.md5(tok.encode()).hexdigest(), 16)
        for i in range(bitlen):
            v[i] += 1 if (h >> i) & 1 else -1
    out = 0
    for i in range(bitlen):
        if v[i] >= 0:
            out |= (1 << i)
    return f"{out:0{bitlen//4}x}"

def hamming_hex(a: str, b: str) -> int:
    try:
        ia, ib = int(a, 16), int(b, 16)
        return (ia ^ ib).bit_count()
    except Exception:
        return 9999

def classify_text(s: str) -> str:
    for cat, rx in CATEGORY_RULES:
        if re.search(rx, s, flags=re.IGNORECASE):
            return cat
    return "GENERAL"

def find_dates(s: str) -> List[str]:
    hits = set()
    for rx in DATE_PATTERNS:
        for m in re.finditer(rx, s, flags=re.IGNORECASE):
            hits.add(m.group(0))
    return sorted(hits)

def normalize_date(raw: str) -> Optional[str]:
    raw = raw.strip()
    m = re.match(r"^(20\d{2})[-/\.](0?\d{1,2})[-/\.](0?\d{1,2})$", raw)
    if m:
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            return datetime(y, mo, d).strftime("%Y-%m-%d")
        except Exception:
            return None
    m = re.match(r"^(0?\d{1,2})[-/\.](0?\d{1,2})[-/\.](20\d{2})$", raw)
    if m:
        mo, d, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            return datetime(y, mo, d).strftime("%Y-%m-%d")
        except Exception:
            return None
    try:
        dt = datetime.strptime(raw, "%B %d, %Y")
        return dt.strftime("%Y-%m-%d")
    except Exception:
        try:
            dt = datetime.strptime(raw, "%b %d, %Y")
            return dt.strftime("%Y-%m-%d")
        except Exception:
            return None

def extract_entities(s: str) -> Dict[str, List[str]]:
    out = {"CASE_NO": [], "MCR": [], "MCL": [], "CANON": [], "FORM": [], "PERSON": []}
    for name, rx in ENTITY_PATTERNS.items():
        for m in re.finditer(rx, s, flags=re.IGNORECASE):
            out.setdefault(name, []).append(m.group(0))
    for m in re.finditer(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z\.]+){1,3})\b", s):
        val = m.group(1).strip()
        if val in SEED_PARTIES or (len(val.split()) >= 2 and len(val) <= 60):
            out["PERSON"].append(val)
    for k in out:
        out[k] = sorted(set(out[k]))
    return out

def upsert_node(conn: sqlite3.Connection, key: str, label: str, ntype: str, meta: Dict[str, Any]):
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO nodes(key,label,type,meta_json) VALUES(?,?,?,?)",
              (key, label, ntype, json.dumps(meta, ensure_ascii=False)))
    row = c.execute("SELECT meta_json FROM nodes WHERE key=?", (key,)).fetchone()
    if row:
        try:
            old = json.loads(row[0]) if row[0] else {}
            old.update(meta)
            c.execute("UPDATE nodes SET label=?, type=?, meta_json=? WHERE key=?",
                      (label, ntype, json.dumps(old, ensure_ascii=False), key))
        except Exception:
            pass

def add_edge(conn: sqlite3.Connection, src_key: str, dst_key: str, etype: str, meta: Dict[str, Any]):
    c = conn.cursor()
    c.execute("INSERT INTO edges(src_key,dst_key,type,meta_json) VALUES(?,?,?,?)",
              (src_key, dst_key, etype, json.dumps(meta, ensure_ascii=False)))

def persist_graph_exports(conn: sqlite3.Connection, paths: Paths):
    nodes, edges = [], []
    c = conn.cursor()
    for row in c.execute("SELECT key,label,type,meta_json FROM nodes"):
        nodes.append({"key": row[0], "label": row[1], "type": row[2], "meta": json.loads(row[3] or "{}")})
    for row in c.execute("SELECT src_key,dst_key,type,meta_json FROM edges"):
        edges.append({"src": row[0], "dst": row[1], "type": row[2], "meta": json.loads(row[3] or "{}")})
    paths.nodes_json.write_text(json.dumps(nodes, ensure_ascii=False, indent=2), encoding="utf-8")
    paths.edges_json.write_text(json.dumps(edges, ensure_ascii=False, indent=2), encoding="utf-8")

def push_neo4j(paths: Paths, conn_str: Optional[str], user: Optional[str], pwd: Optional[str]):
    if not GraphDatabase or not conn_str:
        return
    driver = GraphDatabase.driver(conn_str, auth=(user, pwd))
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
        nodes = json.loads(paths.nodes_json.read_text(encoding="utf-8"))
        edges = json.loads(paths.edges_json.read_text(encoding="utf-8"))
        for n in nodes:
            session.run(
                "MERGE (x:Node {key:$key}) SET x.label=$label, x.type=$type, x.meta=$meta",
                key=n["key"], label=n["label"], type=n["type"], meta=n["meta"]
            )
        for e in edges:
            session.run(
                "MATCH (a:Node {key:$src}), (b:Node {key:$dst}) "
                "MERGE (a)-[r:REL {type:$type}]->(b) SET r.meta=$meta",
                src=e["src"], dst=e["dst"], type=e["type"], meta=e["meta"]
            )
    driver.close()

def write_bundle(paths: Paths):
    with zipfile.ZipFile(paths.bundle, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for p in [paths.nodes_json, paths.edges_json, paths.ingest_log, paths.db, paths.error_log]:
            if p.exists():
                z.write(p, arcname=p.name)

def _is_excluded(path: Path, patterns) -> bool:
    parts = [p.lower() for p in path.parts]
    for pat in patterns or []:
        pat = pat.lower()
        for part in parts:
            if fnmatch.fnmatch(part, pat):
                return True
    return False

def iter_files(roots: List[str], excludes: List[str]):
    for r in roots:
        r = str(r)
        if not os.path.exists(r):
            continue
        for dirpath, dirnames, filenames in os.walk(r, topdown=True, onerror=None):
            # prune excluded dirs
            dirnames[:] = [d for d in dirnames if not _is_excluded(Path(dirpath) / d, excludes)]
            # files
            for name in filenames:
                p = Path(dirpath) / name
                if _is_excluded(p, excludes):
                    continue
                try:
                    ext = p.suffix.lower()
                except Exception:
                    continue
                if ext not in INGEST_EXT:
                    continue
                yield p

def scan_files(roots: List[str], excludes: List[str], max_files: Optional[int] = None) -> List[Path]:
    out = []
    for p in iter_files(roots, excludes):
        try:
            st = p.stat()
        except Exception:
            continue
        if st.st_size <= 0:
            continue
        out.append(p)
        if max_files and len(out) >= max_files:
            break
    return out

def extract_text_meta(p: Path, enable_ocr: bool) -> Dict[str, Any]:
    ext = p.suffix.lower()
    text = ""
    meta = {"path": str(p), "size": None, "mtime": None}
    try:
        st = p.stat()
        meta["size"] = st.st_size
        meta["mtime"] = st.st_mtime
    except Exception:
        pass
    try:
        if ext in TEXT_EXT:
            text = p.read_text(errors="ignore", encoding="utf-8")
        elif ext in DOC_EXT and docx:
            d = docx.Document(str(p))
            text = "\n".join(para.text for para in d.paragraphs)
        elif ext in PDF_EXT and fitz:
            with fitz.open(str(p)) as doc:
                text = "\n".join(page.get_text() for page in doc)
                try:
                    meta["pdf_meta"] = dict(doc.metadata or {})
                except Exception:
                    pass
        elif ext in IMG_EXT:
            try:
                with p.open("rb") as f:
                    tags = exifread.process_file(f, details=False)
                meta["exif"] = {k: str(v) for k, v in tags.items()}
            except Exception:
                pass
            if enable_ocr and pytesseract and Image:
                try:
                    with Image.open(str(p)) as im:
                        text = pytesseract.image_to_string(im)
                except Exception:
                    text = ""
        else:
            text = ""
    except Exception as e:
        meta["extract_error"] = f"{type(e).__name__}: {e}"
    return {"text": text or "", "meta": meta}

def classify_category(text: str) -> str:
    return classify_text(text)

def worker_extract(args):
    p, enable_ocr = args
    try:
        data = extract_text_meta(p, enable_ocr)
        return {"ok": True, "path": str(p), "text": data["text"], "meta": data["meta"]}
    except Exception as e:
        return {"ok": False, "path": str(p), "error": f"{type(e).__name__}: {e}"}

def process_items(paths: Paths, items: List[Path], workers: int, fuzzy: bool, fuzzy_thresh_pct: int, enable_ocr: bool):
    conn = db_connect(paths.db)
    try:
        futures = {}
        with ThreadPoolExecutor(max_workers=max(1, workers)) as ex:
            for p in items:
                futures[ex.submit(worker_extract, (p, enable_ocr))] = p

            for fut in as_completed(futures):
                p = futures[fut]
                try:
                    res = fut.result()
                except Exception as e:
                    log_error(paths, f"extract_error {p}: {e}")
                    continue
                if not res.get("ok"):
                    log_error(paths, f"extract_fail {res.get('path')}: {res.get('error')}")
                    continue
                try:
                    commit_item(paths, conn, Path(res["path"]), res["text"], res["meta"], fuzzy, fuzzy_thresh_pct)
                except Exception as e:
                    log_error(paths, f"commit_error {res.get('path')}: {e}\n{traceback.format_exc()}")
    finally:
        conn.close()

def commit_item(paths: Paths, conn: sqlite3.Connection, p: Path, text: str, meta: Dict[str, Any], fuzzy: bool, fuzzy_thresh_pct: int):
    c = conn.cursor()
    rel = meta.get("path", str(p))
    try:
        st = Path(rel).stat()
        size, mtime = st.st_size, st.st_mtime
    except Exception:
        size, mtime = None, None
    try:
        sha = sha256_path(Path(rel))
    except Exception:
        sha = hashlib.sha256(rel.encode('utf-8', 'ignore')).hexdigest()

    row = c.execute("SELECT id,size,mtime,sha256 FROM files WHERE path=?", (rel,)).fetchone()
    if row and row[1] == size and row[2] == mtime and row[3] == sha:
        return

    category = classify_category(text)
    txt_name = "txt_" + hashlib.sha1(rel.encode('utf-8', 'ignore')).hexdigest() + ".txt"
    txt_path = paths.txt_dir / txt_name
    try:
        txt_path.write_text(text or "", encoding="utf-8", errors="ignore")
    except Exception:
        pass

    raw_dates = find_dates(text or "")
    norm_dates = [d for d in (normalize_date(x) for x in raw_dates) if d]
    ents = extract_entities(text or "")

    ext = Path(rel).suffix.lower()
    img_hash = image_ahash(Path(rel)) if ext in IMG_EXT else None
    text_sig = simhash_text(text) if (text and len(text) > 32) else None

    c.execute("""INSERT OR IGNORE INTO files(path,size,mtime,sha256,ingested_at,text_path,meta_json,category,img_phash,text_simhash)
                 VALUES(?,?,?,?,?,?,?,?,?,?)""",
              (rel, size, mtime, sha, utc_now_iso(), str(txt_path), json.dumps(meta, ensure_ascii=False), category, img_hash, text_sig))
    c.execute("""UPDATE files SET size=?,mtime=?,sha256=?,ingested_at=?,text_path=?,meta_json=?,category=?,img_phash=?,text_simhash=?
                 WHERE path=?""",
              (size, mtime, sha, utc_now_iso(), str(txt_path), json.dumps(meta, ensure_ascii=False), category, img_hash, text_sig, rel))
    file_id = c.execute("SELECT id FROM files WHERE path=?", (rel,)).fetchone()[0]

    for d in norm_dates:
        c.execute("INSERT INTO events(file_id,date,label,type,source_ref) VALUES(?,?,?,?,?)",
                  (file_id, d, f"Event from {Path(rel).name}", category, rel))

    doc_key = f"DOC::{sha[:16]}"
    upsert_node(conn, doc_key, Path(rel).name, "DOCUMENT",
                {"path": rel, "sha256": sha, "category": category, "size": size})

    for case in ents.get("CASE_NO", []):
        case_key = f"CASE::{case.upper()}"
        upsert_node(conn, case_key, case, "CASE", {})
        add_edge(conn, doc_key, case_key, "REFERS_TO", {"why": "case_no"})
    for frm in ents.get("FORM", []):
        frm_key = f"FORM::{frm.upper()}"
        upsert_node(conn, frm_key, frm, "FORM", {})
        add_edge(conn, doc_key, frm_key, "MENTIONS", {"why": "form"})
    for mcr in ents.get("MCR", []):
        mcr_key = f"MCR::{mcr.replace(' ', '')}"
        upsert_node(conn, mcr_key, mcr, "MCR", {})
        add_edge(conn, doc_key, mcr_key, "CITES", {})
    for mcl in ents.get("MCL", []):
        mcl_key = f"MCL::{mcl.replace(' ', '')}"
        upsert_node(conn, mcl_key, mcl, "MCL", {})
        add_edge(conn, doc_key, mcl_key, "CITES", {})
    for can in ents.get("CANON", []):
        can_key = f"CANON::{can.replace(' ', '')}"
        upsert_node(conn, can_key, can, "CANON", {})
        add_edge(conn, doc_key, can_key, "CITES", {})
    for person in ents.get("PERSON", []):
        per_key = f"PERSON::{person}"
        upsert_node(conn, per_key, person, "PERSON", {})
        add_edge(conn, doc_key, per_key, "MENTIONS", {})

    if fuzzy and (img_hash or text_sig):
        sim_req = max(0, min(100, fuzzy_thresh_pct))
        max_dist = int(round((100 - sim_req) / 100 * 64))
        if img_hash:
            for (other_path, other_hash) in c.execute("SELECT path,img_phash FROM files WHERE img_phash IS NOT NULL AND path<>?", (rel,)):
                if not other_hash:
                    continue
                dist = hamming_hex(img_hash, other_hash)
                if dist <= max_dist:
                    other_sha = c.execute("SELECT sha256 FROM files WHERE path=?", (other_path,)).fetchone()
                    if other_sha:
                        other_key = f"DOC::{other_sha[0][:16]}"
                        add_edge(conn, doc_key, other_key, "NEAR_DUPLICATE_OF", {"by": "img_phash", "hamming": dist})
                    break
        if text_sig:
            for (other_path, other_sig) in c.execute("SELECT path,text_simhash FROM files WHERE text_simhash IS NOT NULL AND path<>?", (rel,)):
                if not other_sig:
                    continue
                dist = hamming_hex(text_sig, other_sig)
                if dist <= max_dist:
                    other_sha = c.execute("SELECT sha256 FROM files WHERE path=?", (other_path,)).fetchone()
                    if other_sha:
                        other_key = f"DOC::{other_sha[0][:16]}"
                        add_edge(conn, doc_key, other_key, "NEAR_DUPLICATE_OF", {"by": "text_simhash", "hamming": dist})
                    break

    conn.commit()
    log_line(paths, {"ts": utc_now_iso(), "op": "ingest", "path": rel, "sha256": sha,
                     "category": category, "dates": norm_dates, "entities": ents})

def run_once(paths: Paths, roots: List[str], workers: int, fuzzy: bool, fuzzy_thresh: int, write_zip: bool, neo: Tuple[str,str,str], excludes: List[str], enable_ocr: bool, max_files: Optional[int] = None):
    items = scan_files(roots, excludes, max_files=max_files)
    process_items(paths, items, workers, fuzzy, fuzzy_thresh, enable_ocr)
    conn = db_connect(paths.db)
    try:
        persist_graph_exports(conn, paths)
    finally:
        conn.close()
    if write_zip:
        write_bundle(paths)
    if neo[0]:
        push_neo4j(paths, neo[0], neo[1], neo[2])
    log_line(paths, {"ts": utc_now_iso(), "op": "once_complete", "files": len(items)})

def run_cycles(paths: Paths, roots: List[str], n: int, workers: int, fuzzy: bool, fuzzy_thresh: int, write_zip: bool, neo: Tuple[str,str,str], excludes: List[str], enable_ocr: bool):
    for i in range(1, n+1):
        run_once(paths, roots, workers, fuzzy, fuzzy_thresh, write_zip, neo, excludes, enable_ocr, None)
        log_line(paths, {"ts": utc_now_iso(), "op": "cycle_complete", "cycle": i})

def watch(paths: Paths, roots: List[str], every_sec: int, workers: int, fuzzy: bool, fuzzy_thresh: int, write_zip: bool, neo: Tuple[str,str,str], excludes: List[str], enable_ocr: bool):
    while True:
        try:
            run_once(paths, roots, workers, fuzzy, fuzzy_thresh, write_zip, neo, excludes, enable_ocr, None)
        except Exception as e:
            log_error(paths, f"watch_error: {e}\n{traceback.format_exc()}")
        time.sleep(max(5, every_sec))

def parse_args():
    ap = argparse.ArgumentParser(description="Hardened ingest + graph builder")
    ap.add_argument("--paths", nargs="+", help="Root folders to scan")
    ap.add_argument("--roots", nargs="+", help="Alias for --paths")
    ap.add_argument("--out", type=str, default=str(Path(__file__).with_name("data")), help="Output directory")
    ap.add_argument("--once", action="store_true", help="Run one pass")
    ap.add_argument("--watch", action="store_true", help="Run continuously")
    ap.add_argument("--every", type=int, default=300, help="Watch polling interval in seconds")
    ap.add_argument("--cycles", type=int, default=0, help="Run N improvement cycles")
    ap.add_argument("--workers", type=int, default=min(8, os.cpu_count() or 4), help="Thread workers for extraction")
    ap.add_argument("--zip", action="store_true", help="Write/overwrite bundle zip at end of each pass")
    ap.add_argument("--fuzzy", action="store_true", help="Enable fuzzy near-duplicate detection")
    ap.add_argument("--fuzzy-threshold", type=int, default=90, help="Percent similarity threshold (0-100)")
    ap.add_argument("--neo4j", type=str, default="", help="bolt://host:7687")
    ap.add_argument("--neo4j-user", type=str, default="")
    ap.add_argument("--neo4j-pass", type=str, default="")
    ap.add_argument("--rebuild-graph", action="store_true", help="Export graph JSON from DB only")
    ap.add_argument("--exclude-globs", nargs="+", default=DEFAULT_EXCLUDES, help="Glob patterns to skip")
    ap.add_argument("--no-ocr", action="store_true", help="Disable OCR on images")
    ap.add_argument("--dry-run", action="store_true", help="Scan and print counts only")
    ap.add_argument("--max-files", type=int, default=0, help="Limit number of files during a pass (for testing)")
    return ap.parse_args()

def main():
    args = parse_args()
    roots = args.paths or args.roots or [str(Path.cwd())]
    paths = Paths(args.out)
    db_init(paths)
    neo = (args.neo4j, args.neo4j_user, args.neo4j_pass)
    excludes = args.exclude_globs or DEFAULT_EXCLUDES
    enable_ocr = not args.no_ocr

    if args.rebuild_graph:
        conn = db_connect(paths.db)
        try:
            persist_graph_exports(conn, paths)
        finally:
            conn.close()
        if args.zip:
            write_bundle(paths)
        if args.neo4j:
            push_neo4j(paths, args.neo4j, args.neo4j_user, args.neo4j_pass)
        return

    if args.dry_run:
        items = scan_files(roots, excludes, max_files=(args.max_files or None))
        print(f"Dry run: {len(items)} files matched.")
        print("First 20:")
        for p in items[:20]:
            print(str(p))
        return

    max_files = args.max_files if args.max_files > 0 else None

    if args.once:
        run_once(paths, roots, args.workers, args.fuzzy, args.fuzzy_threshold, args.zip, neo, excludes, enable_ocr, max_files)
        return

    if args.cycles and args.cycles > 0:
        run_cycles(paths, roots, args.cycles, args.workers, args.fuzzy, args.fuzzy_threshold, args.zip, neo, excludes, enable_ocr)
        return

    if args.watch:
        watch(paths, roots, args.every, args.workers, args.fuzzy, args.fuzzy_threshold, args.zip, neo, excludes, enable_ocr)
        return

    run_once(paths, roots, args.workers, args.fuzzy, args.fuzzy_threshold, args.zip, neo, excludes, enable_ocr, max_files)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # last-resort log
        base = Path(__file__).with_name("data")
        base.mkdir(parents=True, exist_ok=True)
        with (base / "fatal_error.log").open("a", encoding="utf-8") as f:
            f.write(f"[{utc_now_iso()}] {e}\n{traceback.format_exc()}\n")
        raise
