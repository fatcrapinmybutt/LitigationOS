
# omni_scan_ascii.py  -- dependency-free scanner (ASCII only)
# Usage examples (Windows PowerShell):
#   & "C:\Program Files\Python313\python.exe" "D:\omni_scan_ascii.py" --paths "D:\" --out "D:\LITIGATION_OS\data" --dry-run --max-files 50
#   & "C:\Program Files\Python313\python.exe" "D:\omni_scan_ascii.py" --paths "D:\" --out "D:\LITIGATION_OS\data" --once --workers 6
#
# Features:
# - Scans only text-like files: .txt, .md, .csv, .json
# - Builds SQLite DB (files, events, nodes, edges, patterns)
# - Extracts simple entities (CASE_NO, MCR, MCL, FORM, CANON, PERSON) via regex
# - Finds dates, computes simhash for text similarity (no external libs)
# - Exports graph_nodes.json and graph_edges.json, optional bundle ZIP
# - Exclude patterns supported
#
# No external packages. ASCII only to avoid encoding errors.

import os, re, json, sqlite3, zipfile, argparse, hashlib, fnmatch
from pathlib import Path
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

TEXT_EXT = {'.txt', '.md', '.csv', '.json'}
INGEST_EXT = TEXT_EXT

DEFAULT_EXCLUDES = ['System Volume Information', '$RECYCLE.BIN', 'FOUND.*', 'Config.Msi']

ENTITY_PATTERNS = {
    "CASE_NO": r"\b20\d{2}[-_](\d{6}|\d{7})[-_]([A-Z]{2})\b",
    "MCR": r"\bMCR\s*\d\.\d+(?:\([A-Za-z0-9]+\))*\b",
    "MCL": r"\bMCL\s*\d+\.?\d*(?:\([A-Za-z0-9]+\))*\b",
    "CANON": r"\bCanon\s*[1-9]\b",
    "FORM": r"\b(?:FOC|MC|SCAO|JC)[-\s]?\d{1,4}[a-z]?\b"
}

DATE_PATTERNS = [
    r"\b(20\d{2}[-/\.](0?[1-9]|1[0-2])[-/\.](0?[1-9]|[12]\d|3[01]))\b",
    r"\b((0?[1-9]|1[0-2])[-/\.](0?[1-9]|[12]\d|3[01])[-/\.]20\d{2})\b",
    r"\b(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+(0?[1-9]|[12]\d|3[01]),\s+20\d{2}\b"
]

SEED_PARTIES = {"Andrew J. Pigors", "Emily Watson", "Judge McNeill", "Shady Oaks Park MHP LLC",
                "Homes of America", "Partridge Equity", "Alden Global Capital", "EGLE", "Friend of the Court"}

def utc_now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def sha256_path(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for ch in iter(lambda: f.read(1024 * 1024), b""):
            h.update(ch)
    return h.hexdigest()

def simhash_text(text: str, bitlen: int = 64) -> str:
    v = [0] * bitlen
    for tok in re.findall(r"\w+", text.lower()):
        h = int(hashlib.md5(tok.encode()).hexdigest(), 16)
        for i in range(bitlen):
            v[i] += 1 if (h >> i) & 1 else -1
    out = 0
    for i in range(bitlen):
        if v[i] >= 0:
            out |= 1 << i
    return f"{out:0{bitlen//4}x}"

def classify_text(s: str) -> str:
    if re.search(r"\b(custody|parenting\s*time|visitation|722\.27a|best interest factors)\b", s, re.I):
        return "CUSTODY"
    if re.search(r"\b(PPO|Personal Protection Order|Show Cause)\b", s, re.I):
        return "PPO"
    if re.search(r"\b(eviction|landlord|MHP|rent|EGLE|sewage|Homes of America|Shady Oaks)\b", s, re.I):
        return "HOUSING"
    if re.search(r"\b(MCR|MCL|Benchbook|Canon)\b", s, re.I):
        return "JUDICIAL"
    return "GENERAL"

def find_dates(s: str):
    hits = set()
    for rx in DATE_PATTERNS:
        for m in re.finditer(rx, s, flags=re.I):
            hits.add(m.group(0))
    return sorted(hits)

def normalize_date(raw: str):
    raw = raw.strip()
    m = re.match(r"^(20\d{2})[-/\.](0?\d{1,2})[-/\.](0?\d{1,2})$", raw)
    if m:
        y, mo, d = map(int, m.groups())
        try:
            return datetime(y, mo, d).strftime("%Y-%m-%d")
        except Exception:
            return None
    m = re.match(r"^(0?\d{1,2})[-/\.](0?\d{1,2})[-/\.]20\d{2}$", raw)
    if m:
        mo, d, y = map(int, m.groups())
        try:
            return datetime(y, mo, d).strftime("%Y-%m-%d")
        except Exception:
            return None
    for fmt in ("%B %d, %Y", "%b %d, %Y"):
        try:
            return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
        except Exception:
            pass
    return None

def extract_entities(s: str):
    out = {"CASE_NO": [], "MCR": [], "MCL": [], "CANON": [], "FORM": [], "PERSON": []}
    for name, rx in ENTITY_PATTERNS.items():
        for m in re.finditer(rx, s, flags=re.I):
            out[name].append(m.group(0))
    for m in re.finditer(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z\.]+){1,3})\b", s):
        val = m.group(1).strip()
        if val in SEED_PARTIES or (len(val.split()) >= 2 and len(val) <= 60):
            out["PERSON"].append(val)
    for k in out:
        out[k] = sorted(set(out[k]))
    return out

class Paths:
    def __init__(self, base_out: str):
        b = Path(base_out); b.mkdir(parents=True, exist_ok=True)
        self.base = b
        self.db = b / "autogrow_state.db"
        self.exports = b / "exports"; self.exports.mkdir(parents=True, exist_ok=True)
        self.txt_dir = self.exports / "txt"; self.txt_dir.mkdir(parents=True, exist_ok=True)
        self.bundle = self.exports / "AUTO_BUNDLE.zip"
        self.nodes_json = self.exports / "graph_nodes.json"
        self.edges_json = self.exports / "graph_edges.json"
        self.ingest_log = self.exports / "ingest_log.jsonl"
        self.error_log = self.exports / "errors.log"

def log_line(paths: Paths, d):
    with paths.ingest_log.open("a", encoding="utf-8") as f:
        f.write(json.dumps(d, ensure_ascii=False) + "\n")

def log_error(paths: Paths, msg: str):
    with paths.error_log.open("a", encoding="utf-8") as f:
        f.write("[" + utc_now_iso() + "] " + msg + "\n")

def db_connect(db_path: Path):
    c = sqlite3.connect(str(db_path), check_same_thread=False)
    c.execute("PRAGMA journal_mode=WAL;")
    c.execute("PRAGMA synchronous=NORMAL;")
    return c

def db_init(paths: Paths):
    conn = db_connect(paths.db); cur = conn.cursor()
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
        cur.execute("INSERT OR IGNORE INTO patterns(name,regex,type,enabled) VALUES(?,?,?,1)", (name, rx, "ENTITY"))
    conn.commit(); conn.close()

def _is_excluded(path: Path, patterns):
    parts = [p.lower() for p in path.parts]
    for pat in patterns or []:
        pat = pat.lower()
        for part in parts:
            if fnmatch.fnmatch(part, pat):
                return True
    return False

def iter_files(roots, excludes):
    for r in roots:
        if not os.path.exists(r): continue
        for dp, dn, fn in os.walk(r, topdown=True, onerror=None):
            dn[:] = [d for d in dn if not _is_excluded(Path(dp) / d, excludes)]
            for name in fn:
                p = Path(dp) / name
                if _is_excluded(p, excludes): continue
                ext = p.suffix.lower()
                if ext in INGEST_EXT:
                    yield p

def scan_files(roots, excludes, max_files=None):
    out = []
    for p in iter_files(roots, excludes):
        try:
            st = p.stat()
        except Exception:
            continue
        if st.st_size <= 0: continue
        out.append(p)
        if max_files and len(out) >= max_files: break
    return out

def read_text_safe(p: Path):
    try:
        return p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        try:
            return p.read_text(encoding="latin-1", errors="ignore")
        except Exception:
            return ""

def extract_text_meta(p: Path):
    ext = p.suffix.lower()
    meta = {"path": str(p), "size": None, "mtime": None}
    text = ""
    try:
        st = p.stat(); meta["size"] = st.st_size; meta["mtime"] = st.st_mtime
    except Exception:
        pass
    if ext in TEXT_EXT:
        text = read_text_safe(p)
    return {"text": text or "", "meta": meta}

def upsert_node(conn, key, label, ntype, meta):
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO nodes(key,label,type,meta_json) VALUES(?,?,?,?)",
              (key, label, ntype, json.dumps(meta, ensure_ascii=False)))
    row = c.execute("SELECT meta_json FROM nodes WHERE key=?", (key,)).fetchone()
    if row:
        try:
            old = json.loads(row[0]) if row[0] else {}
            old.update(meta)
            c.execute("UPDATE nodes SET label=?,type=?,meta_json=? WHERE key=?",
                      (label, ntype, json.dumps(old, ensure_ascii=False), key))
        except Exception:
            pass

def add_edge(conn, src_key, dst_key, etype, meta):
    conn.cursor().execute("INSERT INTO edges(src_key,dst_key,type,meta_json) VALUES(?,?,?,?)",
                          (src_key, dst_key, etype, json.dumps(meta, ensure_ascii=False)))

def persist_graph_exports(conn, paths):
    nodes = []; edges = []; c = conn.cursor()
    for r in c.execute("SELECT key,label,type,meta_json FROM nodes"):
        nodes.append({"key": r[0], "label": r[1], "type": r[2], "meta": json.loads(r[3] or "{}")})
    for r in c.execute("SELECT src_key,dst_key,type,meta_json FROM edges"):
        edges.append({"src": r[0], "dst": r[1], "type": r[2], "meta": json.loads(r[3] or "{}")})
    paths.nodes_json.write_text(json.dumps(nodes, ensure_ascii=False, indent=2), encoding="utf-8")
    paths.edges_json.write_text(json.dumps(edges, ensure_ascii=False, indent=2), encoding="utf-8")

def write_bundle(paths):
    with zipfile.ZipFile(paths.bundle, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for p in [paths.nodes_json, paths.edges_json, paths.ingest_log, paths.db, paths.error_log]:
            if p.exists():
                z.write(p, arcname=p.name)

def commit_item(paths, conn, p: Path, text, meta, fuzzy, fuzzy_thresh):
    c = conn.cursor(); rel = meta.get("path", str(p))
    try:
        st = Path(rel).stat(); size, mtime = st.st_size, st.st_mtime
    except Exception:
        size, mtime = None, None
    try:
        sha = sha256_path(Path(rel))
    except Exception:
        sha = hashlib.sha256(rel.encode("utf-8", "ignore")).hexdigest()

    row = c.execute("SELECT id,size,mtime,sha256 FROM files WHERE path=?", (rel,)).fetchone()
    if row and row[1] == size and row[2] == mtime and row[3] == sha:
        return

    category = classify_text(text)
    txt_name = "txt_" + hashlib.sha1(rel.encode("utf-8", "ignore")).hexdigest() + ".txt"
    txt_path = paths.txt_dir / txt_name
    try:
        txt_path.write_text(text or "", encoding="utf-8", errors="ignore")
    except Exception:
        pass

    raw_dates = find_dates(text or "")
    norm = [d for d in (normalize_date(x) for x in raw_dates) if d]
    ents = extract_entities(text or "")
    text_sig = simhash_text(text) if (text and len(text) > 32) else None

    c.execute("""INSERT OR IGNORE INTO files(path,size,mtime,sha256,ingested_at,text_path,meta_json,category,text_simhash)
                 VALUES(?,?,?,?,?,?,?,?,?)""",
              (rel, size, mtime, sha, utc_now_iso(), str(txt_path), json.dumps(meta, ensure_ascii=False),
               category, text_sig))
    c.execute("""UPDATE files SET size=?,mtime=?,sha256=?,ingested_at=?,text_path=?,meta_json=?,category=?,text_simhash=? WHERE path=?""",
              (size, mtime, sha, utc_now_iso(), str(txt_path), json.dumps(meta, ensure_ascii=False), category, text_sig, rel))

    fid = c.execute("SELECT id FROM files WHERE path=?", (rel,)).fetchone()[0]
    for d in norm:
        c.execute("INSERT INTO events(file_id,date,label,type,source_ref) VALUES(?,?,?,?,?)",
                  (fid, d, "Event from " + Path(rel).name, category, rel))

    doc_key = "DOC::" + sha[:16]
    upsert_node(conn, doc_key, Path(rel).name, "DOCUMENT", {"path": rel, "sha256": sha, "category": category, "size": size})

    for case in ents.get("CASE_NO", []):
        ck = "CASE::" + case.upper(); upsert_node(conn, ck, case, "CASE", {}); add_edge(conn, doc_key, ck, "REFERS_TO", {"why": "case_no"})
    for frm in ents.get("FORM", []):
        fk = "FORM::" + frm.upper(); upsert_node(conn, fk, frm, "FORM", {}); add_edge(conn, doc_key, fk, "MENTIONS", {"why": "form"})
    for mcr in ents.get("MCR", []):
        mk = "MCR::" + mcr.replace(" ", ""); upsert_node(conn, mk, mcr, "MCR", {}); add_edge(conn, doc_key, mk, "CITES", {})
    for mcl in ents.get("MCL", []):
        lk = "MCL::" + mcl.replace(" ", ""); upsert_node(conn, lk, mcl, "MCL", {}); add_edge(conn, doc_key, lk, "CITES", {})
    for can in ents.get("CANON", []):
        ck = "CANON::" + can.replace(" ", ""); upsert_node(conn, ck, can, "CANON", {}); add_edge(conn, doc_key, ck, "CITES", {})
    for person in ents.get("PERSON", []):
        pk = "PERSON::" + person; upsert_node(conn, pk, person, "PERSON", {}); add_edge(conn, doc_key, pk, "MENTIONS", {})

    if fuzzy and text_sig:
        sim_req = max(0, min(100, fuzzy_thresh)); max_dist = int(round((100 - sim_req) / 100 * 64))
        for (op, osg) in c.execute("SELECT path,text_simhash FROM files WHERE text_simhash IS NOT NULL AND path<>?", (rel,)):
            try:
                if osg and ((int(text_sig, 16) ^ int(osg, 16)).bit_count() <= max_dist):
                    osha = c.execute("SELECT sha256 FROM files WHERE path=?", (op,)).fetchone()
                    if osha:
                        add_edge(conn, doc_key, "DOC::" + osha[0][:16], "NEAR_DUPLICATE_OF", {"by": "text_simhash"})
                    break
            except Exception:
                pass

    conn.commit()
    log_line(paths, {"ts": utc_now_iso(), "op": "ingest", "path": rel, "sha256": sha, "category": category, "dates": norm, "entities": ents})

def process_items(paths, items, workers, fuzzy, fuzzy_thresh):
    conn = db_connect(paths.db)
    try:
        with ThreadPoolExecutor(max_workers=max(1, workers)) as ex:
            futs = {ex.submit(extract_text_meta, p): p for p in items}
            for fut in as_completed(futs):
                p = futs[fut]
                try:
                    res = fut.result()
                except Exception as e:
                    log_error(paths, "extract_error " + str(p) + ": " + str(e))
                    continue
                try:
                    commit_item(paths, conn, p, res["text"], res["meta"], fuzzy, fuzzy_thresh)
                except Exception as e:
                    log_error(paths, "commit_error " + str(p) + ": " + str(e))
    finally:
        conn.close()

def persist_graph(paths):
    conn = db_connect(paths.db)
    try:
        nodes = []; edges = []; c = conn.cursor()
        for r in c.execute("SELECT key,label,type,meta_json FROM nodes"):
            nodes.append({"key": r[0], "label": r[1], "type": r[2], "meta": json.loads(r[3] or "{}")})
        for r in c.execute("SELECT src_key,dst_key,type,meta_json FROM edges"):
            edges.append({"src": r[0], "dst": r[1], "type": r[2], "meta": json.loads(r[3] or "{}")})
        paths.nodes_json.write_text(json.dumps(nodes, ensure_ascii=False, indent=2), encoding="utf-8")
        paths.edges_json.write_text(json.dumps(edges, ensure_ascii=False, indent=2), encoding="utf-8")
    finally:
        conn.close()

def write_bundle(paths):
    with zipfile.ZipFile(paths.bundle, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for p in [paths.nodes_json, paths.edges_json, paths.ingest_log, paths.db, paths.error_log]:
            if p.exists():
                z.write(p, arcname=p.name)

def run_once(paths, roots, workers, fuzzy, fuzzy_thresh, write_zip, excludes, max_files=None):
    items = scan_files(roots, excludes, max_files=max_files)
    process_items(paths, items, workers, fuzzy, fuzzy_thresh)
    persist_graph(paths)
    if write_zip:
        write_bundle(paths)

def run_cycles(paths, roots, n, workers, fuzzy, fuzzy_thresh, write_zip, excludes):
    for i in range(1, n + 1):
        run_once(paths, roots, workers, fuzzy, fuzzy_thresh, write_zip, excludes, None)
        log_line(paths, {"ts": utc_now_iso(), "op": "cycle_complete", "cycle": i})

def parse_args():
    ap = argparse.ArgumentParser(description="Dependency-free drive scanner and graph exporter")
    ap.add_argument("--paths", nargs="+")
    ap.add_argument("--roots", nargs="+")
    ap.add_argument("--out", type=str, default=str(Path(__file__).with_name("data")))
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--cycles", type=int, default=0)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--zip", action="store_true")
    ap.add_argument("--fuzzy", action="store_true")
    ap.add_argument("--fuzzy-threshold", type=int, default=90)
    ap.add_argument("--exclude-globs", nargs="+", default=DEFAULT_EXCLUDES)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--max-files", type=int, default=0)
    return ap.parse_args()

def main():
    a = parse_args()
    roots = a.paths or a.roots or [str(Path.cwd())]
    paths = Paths(a.out); db_init(paths)
    excludes = a.exclude_globs or DEFAULT_EXCLUDES

    if a.dry_run:
        items = scan_files(roots, excludes, max_files=(a.max_files or None))
        print("Dry run: {} files matched.".format(len(items)))
        for p in items[:20]:
            print(str(p))
        return

    max_files = a.max_files if a.max_files > 0 else None

    if a.once:
        run_once(paths, roots, a.workers, a.fuzzy, a.fuzzy_threshold, a.zip, excludes, max_files)
        return
    if a.cycles and a.cycles > 0:
        run_cycles(paths, roots, a.cycles, a.workers, a.fuzzy, a.fuzzy_threshold, a.zip, excludes)
        return
    run_once(paths, roots, a.workers, a.fuzzy, a.fuzzy_threshold, a.zip, excludes, max_files)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        base = Path(__file__).with_name("data"); base.mkdir(parents=True, exist_ok=True)
        with (base / "fatal_error.log").open("a", encoding="utf-8") as f:
            f.write("[" + datetime.now().isoformat() + "] " + str(e) + "\n")
        raise
