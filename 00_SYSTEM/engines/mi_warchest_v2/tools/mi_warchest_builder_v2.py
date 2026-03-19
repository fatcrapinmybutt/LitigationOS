#!/usr/bin/env python3
"""
mi_warchest_builder_v2.py
Build an Authority WarChest from local inputs (folders/zips/files), including nested ZIP recursion.

Outputs:
- mi_warchest_v2.sqlite
- mi_warchest_graph.cypher (Neo4j import)
- mi_warchest_report.txt

Offline-first. Feed official corpora locally for maximum completeness.
"""

from __future__ import annotations
import argparse, io, os, re, zipfile, hashlib, sqlite3, tempfile, json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Iterable, Optional

# ---------- patterns ----------
PATTERNS = {
    "MCL": re.compile(r"\bMCL\s+(\d{1,4}\.\d+[a-zA-Z0-9()\-]*)", re.IGNORECASE),
    "MCR": re.compile(r"\bMCR\s+(\d+(?:\.\d+)+[a-zA-Z0-9()\-]*)", re.IGNORECASE),
    "MRE": re.compile(r"\bMRE\s+(\d{3}[a-zA-Z0-9()\-]*)", re.IGNORECASE),
    "MI_CONST": re.compile(r"\b(Michigan\s+Constitution|Const\.\s*1963|Const\.\s*1908|Const\.\s*1835)\b", re.IGNORECASE),
    "US_CONST": re.compile(r"\b(U\.S\.\s*Constitution|U\.S\.\s*Const\.|US\s*Constitution)\b", re.IGNORECASE),
}

TEXT_EXT = {".txt",".md",".json",".csv",".jsonl",".xml",".html",".rtf"}
TARGET_EXT = TEXT_EXT | {".pdf",".docx"}

def sha256_bytes(b: bytes) -> str:
    h = hashlib.sha256(); h.update(b); return h.hexdigest()

def load_topics_yaml(path: Path) -> Tuple[List[str], Dict[str, List[str]]]:
    """
    Minimal parser for the suite's topics.yaml format.
    Returns (exclude_keywords, topics_synonyms).
    """
    exclude = []
    topics = {}
    cur = None
    in_exclude = False
    in_topics = False
    for line in path.read_text(encoding="utf-8").splitlines():
        raw = line.rstrip("\n")
        if raw.strip().startswith("#") or not raw.strip():
            continue
        if raw.startswith("scope_guard:"):
            in_exclude = False; in_topics = False; continue
        if raw.strip().startswith("exclude_keywords:"):
            in_exclude = True; in_topics = False; continue
        if raw.startswith("topics:"):
            in_topics = True; in_exclude = False; continue
        if in_exclude and re.match(r"^\s{4}-\s+", raw):
            exclude.append(raw.split("-",1)[1].strip().strip('"').strip("'"))
            continue
        if in_topics and re.match(r"^\s{2}[A-Z0-9_]+:", raw):
            cur = raw.strip().rstrip(":")
            topics[cur] = []
            continue
        if in_topics and cur and "synonyms:" in raw:
            # synonyms: ["a","b"]
            m = re.search(r"\[(.*)\]", raw)
            if m:
                items = [x.strip().strip('"').strip("'") for x in m.group(1).split(",") if x.strip()]
                topics[cur] = items
    return [x.lower() for x in exclude], {k:[s.lower() for s in v] for k,v in topics.items()}

def scope_excluded(name: str, exclude_keywords: List[str]) -> bool:
    s = name.lower()
    return any(k in s for k in exclude_keywords)

def iter_inputs(paths: List[Path], exclude_keywords: List[str]) -> Iterable[Tuple[str, bytes]]:
    """
    Yield (virtual_path, bytes) for every file, recursing into nested ZIPs.
    virtual_path is a chain like: root.zip::inner.zip::file.txt
    """
    def walk_zip(chain: List[str], zbytes: bytes):
        try:
            with zipfile.ZipFile(io.BytesIO(zbytes), "r") as z:
                for name in sorted(z.namelist(), key=lambda x:(x.count("/"), x.lower())):
                    if name.endswith("/"): 
                        continue
                    if scope_excluded(name, exclude_keywords):
                        continue
                    ext = Path(name).suffix.lower()
                    if ext == ".zip":
                        try:
                            walk_zip(chain+[name], z.read(name))
                        except Exception:
                            continue
                    else:
                        if ext in TARGET_EXT:
                            try:
                                yield ("::".join(chain+[name]), z.read(name))
                            except Exception:
                                continue
        except Exception:
            return

    for p in paths:
        if p.is_dir():
            for fp in sorted(p.rglob("*")):
                if fp.is_file():
                    if scope_excluded(str(fp), exclude_keywords):
                        continue
                    ext = fp.suffix.lower()
                    if ext in TARGET_EXT:
                        yield (str(fp), fp.read_bytes())
            continue
        if p.suffix.lower() == ".zip":
            with zipfile.ZipFile(p, "r") as z:
                for name in sorted(z.namelist(), key=lambda x:(x.count("/"), x.lower())):
                    if name.endswith("/"):
                        continue
                    if scope_excluded(name, exclude_keywords):
                        continue
                    ext = Path(name).suffix.lower()
                    if ext == ".zip":
                        try:
                            yield from walk_zip([p.name, name], z.read(name))
                        except Exception:
                            continue
                    else:
                        if ext in TARGET_EXT:
                            try:
                                yield (f"{p.name}::{name}", z.read(name))
                            except Exception:
                                continue
            continue
        # normal file
        if not scope_excluded(p.name, exclude_keywords) and p.suffix.lower() in TARGET_EXT:
            yield (p.name, p.read_bytes())

def decode_text(vpath: str, b: bytes) -> str:
    ext = Path(vpath.split("::")[-1]).suffix.lower()
    if ext in TEXT_EXT:
        for enc in ("utf-8","utf-8-sig","cp1252","latin-1"):
            try:
                return b.decode(enc, errors="replace")
            except Exception:
                continue
    return ""

def detect_topics(text: str, topics: Dict[str, List[str]]) -> List[str]:
    tl = text.lower()
    hits = []
    for t, syns in topics.items():
        if any(s in tl for s in syns):
            hits.append(t)
    return hits

def extract_propositions(text: str) -> List[str]:
    props = []
    for line in text.splitlines():
        s = line.strip()
        if not s or len(s) > 500:
            continue
        if s.startswith("#"):
            props.append(s.lstrip("#").strip()); continue
        if s.startswith(("-", "*", "•")):
            props.append(s.lstrip("-*•").strip()); continue
        if re.match(r"^\(?\d+\)?[.)]\s+\S+", s):
            props.append(s); continue
        if re.match(r"^[A-Z][A-Z0-9 \-_/]{10,}$", s):
            props.append(s); continue
    seen=set(); out=[]
    for p in props:
        k=p.lower()
        if k in seen: continue
        seen.add(k); out.append(p)
    return out

def build_db(out_dir: Path) -> sqlite3.Connection:
    db = sqlite3.connect(out_dir/"mi_warchest_v2.sqlite")
    cur = db.cursor()
    cur.executescript("""
    PRAGMA journal_mode=WAL;

    CREATE TABLE IF NOT EXISTS sources(
      source_id TEXT PRIMARY KEY,
      virtual_path TEXT,
      kind TEXT,
      sha256 TEXT,
      size_bytes INTEGER
    );

    CREATE TABLE IF NOT EXISTS citations(
      cite_id TEXT PRIMARY KEY,
      cite_type TEXT,
      cite_key TEXT
    );

    CREATE TABLE IF NOT EXISTS source_citations(
      source_id TEXT,
      cite_id TEXT,
      count INTEGER,
      PRIMARY KEY(source_id, cite_id)
    );

    CREATE TABLE IF NOT EXISTS propositions(
      prop_id TEXT PRIMARY KEY,
      source_id TEXT,
      text TEXT
    );

    CREATE TABLE IF NOT EXISTS topics(
      topic_id TEXT PRIMARY KEY
    );

    CREATE TABLE IF NOT EXISTS source_topics(
      source_id TEXT,
      topic_id TEXT,
      PRIMARY KEY(source_id, topic_id)
    );
    """)
    db.commit()
    return db

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inputs", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--topics", required=True)
    ap.add_argument("--max_props_per_source", type=int, default=800)
    args = ap.parse_args()

    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    exclude, topics = load_topics_yaml(Path(args.topics).resolve())
    paths = [Path(x).expanduser().resolve() for x in args.inputs]

    db = build_db(out_dir)
    cur = db.cursor()

    for t in topics.keys():
        cur.execute("INSERT OR IGNORE INTO topics(topic_id) VALUES (?)", (t,))
    db.commit()

    def upsert_citation(ctype: str, ckey: str) -> str:
        cid = sha256_bytes(f"{ctype}:{ckey}".encode("utf-8"))[:32]
        cur.execute("INSERT OR IGNORE INTO citations(cite_id, cite_type, cite_key) VALUES (?,?,?)", (cid, ctype, ckey))
        return cid

    # ingest
    for vpath, b in iter_inputs(paths, exclude):
        sha = sha256_bytes(b)
        sid = sha[:32]
        ext = Path(vpath.split("::")[-1]).suffix.lower().lstrip(".") or "bin"
        cur.execute("INSERT OR IGNORE INTO sources(source_id, virtual_path, kind, sha256, size_bytes) VALUES (?,?,?,?,?)",
                    (sid, vpath, ext, sha, len(b)))

        text = decode_text(vpath, b)
        if not text:
            continue

        # topic tags
        for t in set(detect_topics(text, topics)):
            cur.execute("INSERT OR IGNORE INTO source_topics(source_id, topic_id) VALUES (?,?)", (sid, t))

        # citations
        for ctype, pat in PATTERNS.items():
            ms = pat.findall(text)
            if not ms:
                continue
            counts = {}
            for m in ms:
                key = m if isinstance(m, str) else " ".join(m)
                key = re.sub(r"\s+"," ",key).strip()
                counts[key] = counts.get(key, 0) + 1
            for key, cnt in counts.items():
                cid = upsert_citation(ctype, key)
                cur.execute("INSERT OR REPLACE INTO source_citations(source_id, cite_id, count) VALUES (?,?,?)",
                            (sid, cid, cnt))

        # propositions
        for ptxt in extract_propositions(text)[:args.max_props_per_source]:
            pid = sha256_bytes(f"{sid}:{ptxt}".encode("utf-8"))[:32]
            cur.execute("INSERT OR IGNORE INTO propositions(prop_id, source_id, text) VALUES (?,?,?)",
                        (pid, sid, ptxt))

    db.commit()

    # report
    report = out_dir/"mi_warchest_report.txt"
    counts = {
        "sources": cur.execute("SELECT COUNT(*) FROM sources").fetchone()[0],
        "citations": cur.execute("SELECT COUNT(*) FROM citations").fetchone()[0],
        "source_citations": cur.execute("SELECT COUNT(*) FROM source_citations").fetchone()[0],
        "propositions": cur.execute("SELECT COUNT(*) FROM propositions").fetchone()[0],
        "topics": cur.execute("SELECT COUNT(*) FROM topics").fetchone()[0],
        "source_topics": cur.execute("SELECT COUNT(*) FROM source_topics").fetchone()[0],
    }
    top_cites = cur.execute("""
        SELECT cite_type, cite_key, SUM(count) as s
        FROM source_citations sc JOIN citations c ON c.cite_id=sc.cite_id
        GROUP BY cite_type, cite_key
        ORDER BY s DESC
        LIMIT 50
    """).fetchall()

    lines = []
    lines.append(f"MI_WARCHEST v2 report ({datetime.utcnow().isoformat()}Z)")
    lines.append("")
    lines.append("Counts:")
    for k,v in counts.items():
        lines.append(f"- {k}: {v}")
    lines.append("")
    lines.append("Top cited tokens:")
    for ctype, ckey, s in top_cites:
        lines.append(f"- {ctype} {ckey} (mentions={s})")
    report.write_text("\n".join(lines), encoding="utf-8")

    # Neo4j cypher
    cypher = out_dir/"mi_warchest_graph.cypher"
    with cypher.open("w", encoding="utf-8") as f:
        f.write("// MI_WARCHEST_GRAPH v2\n")
        f.write("CREATE CONSTRAINT source_id IF NOT EXISTS FOR (s:Source) REQUIRE s.id IS UNIQUE;\n")
        f.write("CREATE CONSTRAINT cite_id IF NOT EXISTS FOR (c:Citation) REQUIRE c.id IS UNIQUE;\n")
        f.write("CREATE CONSTRAINT topic_id IF NOT EXISTS FOR (t:Topic) REQUIRE t.id IS UNIQUE;\n\n")
        for (tid,) in cur.execute("SELECT topic_id FROM topics ORDER BY topic_id"):
            f.write(f"MERGE (t:Topic {{id:{json.dumps(tid)}}});\n")
        f.write("\n")
        for sid, vpath, kind, sha, sz in cur.execute("SELECT source_id, virtual_path, kind, sha256, size_bytes FROM sources"):
            f.write(f"MERGE (s:Source {{id:{json.dumps(sid)}}}) "
                    f"SET s.path={json.dumps(vpath)}, s.kind={json.dumps(kind)}, s.sha256={json.dumps(sha)}, s.size={sz};\n")
        f.write("\n")
        for sid, cid, ctype, ckey, cnt in cur.execute("""
            SELECT sc.source_id, c.cite_id, c.cite_type, c.cite_key, sc.count
            FROM source_citations sc JOIN citations c ON c.cite_id=sc.cite_id
        """):
            f.write(f"MERGE (c:Citation {{id:{json.dumps(cid)}}}) "
                    f"SET c.type={json.dumps(ctype)}, c.key={json.dumps(ckey)};\n")
            f.write(f"MATCH (s:Source {{id:{json.dumps(sid)}}}), (c:Citation {{id:{json.dumps(cid)}}}) "
                    f"MERGE (s)-[r:MENTIONS]->(c) SET r.count={cnt};\n")
        f.write("\n")
        for sid, tid in cur.execute("SELECT source_id, topic_id FROM source_topics"):
            f.write(f"MATCH (s:Source {{id:{json.dumps(sid)}}}), (t:Topic {{id:{json.dumps(tid)}}}) "
                    f"MERGE (s)-[:TAGGED]->(t);\n")

    db.close()
    print("OK")

if __name__ == "__main__":
    main()
