#!/usr/bin/env python3
"""
record_matcher_v2.py
Match a litigation record corpus (txt/md/json/csv/jsonl/html/xml + nested zips) against an existing WarChest DB.

Outputs:
- record_atoms.csv
- authority_triplets.csv
- issue_grid.csv
- match_report.txt
"""

from __future__ import annotations
import argparse, io, os, re, zipfile, hashlib, sqlite3, csv, json
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Dict, Iterable

TEXT_EXT = {".txt",".md",".json",".csv",".jsonl",".xml",".html",".rtf"}
TARGET_EXT = TEXT_EXT | {".zip"}  # records can be zips too

ORDER_VERBS = re.compile(r"\b(IT IS ORDERED|ORDERED|SHALL|MUST|IS HEREBY|SUSPEND|SUSPENDED|PROHIBIT|RESTRAIN|ENJOIN|DENY|GRANT)\b", re.IGNORECASE)
ACCUSATION_TERMS = re.compile(r"\b(threat|harass|stalk|danger|unsafe|abuse|violat|contempt|jail|arrest|mental|delus|manic|suicide|weaponiz)\w*\b", re.IGNORECASE)
DATE_HINT = re.compile(r"\b(20\d{2}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/](20\d{2}))\b")

CITE_PATTERNS = {
    "MCL": re.compile(r"\bMCL\s+(\d{1,4}\.\d+[a-zA-Z0-9()\-]*)", re.IGNORECASE),
    "MCR": re.compile(r"\bMCR\s+(\d+(?:\.\d+)+[a-zA-Z0-9()\-]*)", re.IGNORECASE),
    "MRE": re.compile(r"\bMRE\s+(\d{3}[a-zA-Z0-9()\-]*)", re.IGNORECASE),
    "MI_CONST": re.compile(r"\b(Michigan\s+Constitution|Const\.\s*1963|Const\.\s*1908|Const\.\s*1835)\b", re.IGNORECASE),
    "US_CONST": re.compile(r"\b(U\.S\.\s*Constitution|U\.S\.\s*Const\.|US\s*Constitution)\b", re.IGNORECASE),
}

def sha256_bytes(b: bytes) -> str:
    import hashlib
    h = hashlib.sha256(); h.update(b); return h.hexdigest()

def iter_record_inputs(paths: List[Path]) -> Iterable[Tuple[str, bytes]]:
    def walk_zip(chain: List[str], zbytes: bytes):
        try:
            with zipfile.ZipFile(io.BytesIO(zbytes), "r") as z:
                for name in sorted(z.namelist(), key=lambda x:(x.count("/"), x.lower())):
                    if name.endswith("/"): 
                        continue
                    ext = Path(name).suffix.lower()
                    if ext == ".zip":
                        try:
                            yield from walk_zip(chain+[name], z.read(name))
                        except Exception:
                            continue
                    elif ext in TEXT_EXT:
                        try:
                            yield ("::".join(chain+[name]), z.read(name))
                        except Exception:
                            continue
        except Exception:
            return

    for p in paths:
        if p.is_dir():
            for fp in sorted(p.rglob("*")):
                if fp.is_file() and fp.suffix.lower() in TEXT_EXT:
                    yield str(fp), fp.read_bytes()
            continue
        if p.suffix.lower() == ".zip":
            with zipfile.ZipFile(p, "r") as z:
                for name in sorted(z.namelist(), key=lambda x:(x.count("/"), x.lower())):
                    if name.endswith("/"): 
                        continue
                    ext = Path(name).suffix.lower()
                    if ext == ".zip":
                        try:
                            yield from walk_zip([p.name, name], z.read(name))
                        except Exception:
                            continue
                    elif ext in TEXT_EXT:
                        try:
                            yield (f"{p.name}::{name}", z.read(name))
                        except Exception:
                            continue
            continue
        if p.suffix.lower() in TEXT_EXT:
            yield p.name, p.read_bytes()

def decode_text(b: bytes) -> str:
    for enc in ("utf-8","utf-8-sig","cp1252","latin-1"):
        try:
            return b.decode(enc, errors="replace")
        except Exception:
            continue
    return b.decode("utf-8", errors="replace")

def extract_atoms(text: str, pointer: str, source_id: str) -> List[Dict]:
    atoms = []
    lines = text.splitlines()
    for i, line in enumerate(lines, start=1):
        s = line.strip()
        if not s or len(s) < 8:
            continue
        if ORDER_VERBS.search(s):
            dt = None
            m = DATE_HINT.search(s)
            if m: dt = m.group(0)
            atoms.append({"atom_type":"ORDER_DIRECTIVE","text":s,"pointer":f"{pointer}#L{i}","date_hint":dt})
        elif ACCUSATION_TERMS.search(s):
            dt = None
            m = DATE_HINT.search(s)
            if m: dt = m.group(0)
            atoms.append({"atom_type":"ACCUSATION","text":s,"pointer":f"{pointer}#L{i}","date_hint":dt})
    return atoms

def extract_citations(text: str) -> List[Tuple[str,str,int]]:
    found = []
    for ctype, pat in CITE_PATTERNS.items():
        ms = pat.findall(text)
        if not ms:
            continue
        counts = {}
        for m in ms:
            key = m if isinstance(m,str) else " ".join(m)
            key = re.sub(r"\s+"," ",key).strip()
            counts[key] = counts.get(key, 0) + 1
        for key,cnt in counts.items():
            found.append((ctype,key,cnt))
    return found

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--warchest", required=True, help="path to mi_warchest_v2.sqlite")
    ap.add_argument("--records", nargs="+", required=True, help="record inputs (txt/md/zip/folder)")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    db = sqlite3.connect(Path(args.warchest).resolve())
    db.execute("PRAGMA busy_timeout=60000")
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA cache_size=-32000")
    cur = db.cursor()

    # load citation index from WarChest
    cite_index = {}  # (ctype,ckey)->(cite_id)
    for cid, ctype, ckey in cur.execute("SELECT cite_id, cite_type, cite_key FROM citations"):
        cite_index[(ctype, ckey)] = cid

    # gather record atoms + citations
    atoms = []
    triplets = []
    issue_rows = []

    record_files = [Path(x).expanduser().resolve() for x in args.records]
    for vpath, b in iter_record_inputs(record_files):
        text = decode_text(b)
        sha = sha256_bytes(b)
        source_id = sha[:32]
        # atoms
        a = extract_atoms(text, vpath, source_id)
        for atom in a:
            atom_id = sha256_bytes((source_id + atom["pointer"] + atom["text"]).encode("utf-8"))[:32]
            atom["atom_id"] = atom_id
            atom["source_id"] = source_id
            atoms.append(atom)

        # citations in record text
        cites = extract_citations(text)
        for ctype, ckey, cnt in cites:
            cid = cite_index.get((ctype, ckey))
            if not cid:
                continue
            triplets.append({
                "record_source": vpath,
                "record_source_id": source_id,
                "cite_type": ctype,
                "cite_key": ckey,
                "cite_id": cid,
                "count": cnt
            })

    # write record_atoms.csv
    atoms_csv = out_dir/"record_atoms.csv"
    with atoms_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["atom_id","source_id","atom_type","text","pointer","date_hint"])
        w.writeheader()
        for r in atoms:
            w.writerow(r)

    # write authority_triplets.csv (record->citation)
    trip_csv = out_dir/"authority_triplets.csv"
    with trip_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["record_source","record_source_id","cite_type","cite_key","cite_id","count"])
        w.writeheader()
        for r in triplets:
            w.writerow(r)

    # issue grid: join atoms to citations by shared source file (coarse but effective)
    # (next version can do sentence-window joins)
    issues = {}
    for r in triplets:
        key = r["record_source"]
        issues.setdefault(key, {"record_source":key, "citations":set(), "directives":0, "accusations":0})
        issues[key]["citations"].add(f"{r['cite_type']} {r['cite_key']}")

    for a in atoms:
        key = a["pointer"].split("#")[0]
        issues.setdefault(key, {"record_source":key, "citations":set(), "directives":0, "accusations":0})
        if a["atom_type"] == "ORDER_DIRECTIVE":
            issues[key]["directives"] += 1
        elif a["atom_type"] == "ACCUSATION":
            issues[key]["accusations"] += 1

    issue_csv = out_dir/"issue_grid.csv"
    with issue_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["record_source","directives","accusations","citations"])
        w.writeheader()
        for k in sorted(issues.keys()):
            row = issues[k]
            w.writerow({
                "record_source": row["record_source"],
                "directives": row["directives"],
                "accusations": row["accusations"],
                "citations": "; ".join(sorted(list(row["citations"])))[:50000]
            })

    # report
    rpt = out_dir/"match_report.txt"
    rpt.write_text(
        "\n".join([
            f"Record Matcher v2 report ({datetime.utcnow().isoformat()}Z)",
            f"- record_files_scanned: {len(record_files)}",
            f"- atoms_extracted: {len(atoms)}",
            f"- citation_links_found: {len(triplets)}",
            f"- issue_grid_rows: {len(issues)}",
        ]),
        encoding="utf-8"
    )

    db.close()
    print("OK")

if __name__ == "__main__":
    main()
