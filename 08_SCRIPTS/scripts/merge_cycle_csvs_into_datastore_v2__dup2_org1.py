#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
merge_cycle_csvs_into_datastore_v2.py — merge authority/shard CSVs into a single sqlite datastore with audit/prov.

Upgrades:
- Creates/maintains an authority datastore sqlite with schema + migrations
- Imports:
  - MASTER_LEGAL_TEXT_INDEX*.csv or authority_index.csv-like: rows -> AuthorityShard
  - nodes_authorities.csv / authorities_edges.csv / edges_authorities_xref.csv lanes (optional)
- Dedup rules:
  - shard_key = (authority_id, pinpoint, source_path, text_hash)
  - authority_id normalized
- PROV-lite:
  - records import "activities" and created entities with run_id

Outputs:
- <out_db>.sqlite
- reports/merge_report.json + merge_report.md
- data/authority_neighbors_adj.json (optional built from edges)
- data/authority_shards_fts.sqlite (optional built if --build-fts)

No network. Local-only.

USAGE:
  python merge_cycle_csvs_into_datastore_v2.py --out-db F:\\LitigationOS\\Datastore\\authority_store.sqlite --import-index /path/to/MASTER_LEGAL_TEXT_INDEX.csv --build-fts
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sqlite3
import hashlib
import datetime as dt
from pathlib import Path
from typing import Dict, Any, Optional, Iterable, List, Tuple

try:
    from litigationos_common import ensure_dir, sha256_file, atomic_write_text, safe_ascii_filename, now_utc_iso, configure_logging
except Exception:
    def ensure_dir(p: Path) -> Path:
        p.mkdir(parents=True, exist_ok=True); return p
    def atomic_write_text(path: Path, text: str, encoding: str = "utf-8") -> None:
        ensure_dir(path.parent); path.write_text(text, encoding=encoding)
    def now_utc_iso() -> str:
        return dt.datetime.utcnow().replace(microsecond=0).isoformat()+"Z"
    def safe_ascii_filename(name: str, max_len: int = 180) -> str:
        return re.sub(r"[^A-Za-z0-9._\-]+", "_", name)[:max_len] or "artifact"
    def configure_logging(log_path: Path, verbose: bool=False, quiet: bool=False):
        import logging, sys
        ensure_dir(log_path.parent)
        logger=logging.getLogger("merge"); logger.setLevel(logging.DEBUG); logger.handlers.clear()
        fh=logging.FileHandler(str(log_path), encoding="utf-8"); fh.setLevel(logging.DEBUG)
        fmt=logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"); fh.setFormatter(fmt); logger.addHandler(fh)
        if not quiet:
            ch=logging.StreamHandler(sys.stdout); ch.setLevel(logging.DEBUG if verbose else logging.INFO); ch.setFormatter(fmt); logger.addHandler(ch)
        return logger

SCHEMA_SQL = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS prov_activity (
  activity_id TEXT PRIMARY KEY,
  type TEXT NOT NULL,
  started_at_utc TEXT NOT NULL,
  ended_at_utc TEXT,
  status TEXT,
  notes TEXT
);

CREATE TABLE IF NOT EXISTS authority (
  authority_id TEXT PRIMARY KEY,
  authority_kind TEXT,
  citation TEXT,
  title TEXT,
  source_path TEXT,
  created_at_utc TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS authority_shard (
  shard_id INTEGER PRIMARY KEY AUTOINCREMENT,
  authority_id TEXT,
  source_path TEXT,
  pinpoint TEXT,
  text TEXT,
  text_sha256 TEXT NOT NULL,
  created_at_utc TEXT NOT NULL,
  activity_id TEXT,
  UNIQUE(authority_id, source_path, pinpoint, text_sha256),
  FOREIGN KEY(authority_id) REFERENCES authority(authority_id),
  FOREIGN KEY(activity_id) REFERENCES prov_activity(activity_id)
);

CREATE INDEX IF NOT EXISTS idx_shard_authority ON authority_shard(authority_id);
CREATE INDEX IF NOT EXISTS idx_shard_source ON authority_shard(source_path);

CREATE TABLE IF NOT EXISTS authority_edge (
  edge_id INTEGER PRIMARY KEY AUTOINCREMENT,
  src_authority_id TEXT NOT NULL,
  dst_authority_id TEXT NOT NULL,
  edge_type TEXT,
  weight REAL,
  created_at_utc TEXT NOT NULL,
  activity_id TEXT,
  UNIQUE(src_authority_id, dst_authority_id, edge_type),
  FOREIGN KEY(activity_id) REFERENCES prov_activity(activity_id)
);

CREATE INDEX IF NOT EXISTS idx_edge_src ON authority_edge(src_authority_id);
CREATE INDEX IF NOT EXISTS idx_edge_dst ON authority_edge(dst_authority_id);
"""

def norm_auth_id(s: Optional[str]) -> Optional[str]:
    if not s:
        return None
    t = s.strip()
    # normalize spaces
    t = re.sub(r"\s+", " ", t)
    return t

def text_hash(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8", errors="replace")).hexdigest()

def connect_db(db_path: Path) -> sqlite3.Connection:
    ensure_dir(db_path.parent)
    conn = sqlite3.connect(str(db_path))
    conn.executescript(SCHEMA_SQL)
    return conn

def begin_activity(conn: sqlite3.Connection, activity_id: str, typ: str, notes: str="") -> None:
    conn.execute("INSERT OR REPLACE INTO prov_activity(activity_id,type,started_at_utc,status,notes) VALUES(?,?,?,?,?)",
                 (activity_id, typ, now_utc_iso(), "RUNNING", notes))
    conn.commit()

def end_activity(conn: sqlite3.Connection, activity_id: str, status: str="OK", notes: str="") -> None:
    conn.execute("UPDATE prov_activity SET ended_at_utc=?, status=?, notes=COALESCE(notes,'') || ? WHERE activity_id=?",
                 (now_utc_iso(), status, ("\n"+notes if notes else ""), activity_id))
    conn.commit()

def upsert_authority(conn: sqlite3.Connection, authority_id: str, kind: Optional[str], citation: Optional[str], title: Optional[str], source_path: Optional[str]) -> None:
    conn.execute("""INSERT OR IGNORE INTO authority(authority_id, authority_kind, citation, title, source_path, created_at_utc)
                    VALUES(?,?,?,?,?,?)""",
                 (authority_id, kind, citation, title, source_path, now_utc_iso()))

def insert_shard(conn: sqlite3.Connection, authority_id: Optional[str], source_path: Optional[str], pinpoint: Optional[str], text: str, activity_id: str) -> Tuple[bool, Optional[int]]:
    th = text_hash(text)
    try:
        cur = conn.execute("""INSERT OR IGNORE INTO authority_shard(authority_id, source_path, pinpoint, text, text_sha256, created_at_utc, activity_id)
                              VALUES(?,?,?,?,?,?,?)""",
                           (authority_id, source_path, pinpoint, text, th, now_utc_iso(), activity_id))
        conn.commit()
        # if inserted, lastrowid is set
        if cur.rowcount == 1:
            return True, cur.lastrowid
        return False, None
    except Exception:
        return False, None

def import_index_csv(conn: sqlite3.Connection, csv_path: Path, activity_id: str, logger) -> Dict[str, Any]:
    # Heuristic field mapping:
    # expected columns may include: authority_id, citation, source_path, pinpoint, text, excerpt, quote, page, line
    with csv_path.open("r", encoding="utf-8", errors="replace", newline="") as f:
        reader = csv.DictReader(f)
        cols = [c for c in reader.fieldnames or []]
        def pick(*names):
            for n in names:
                if n in cols:
                    return n
            return None
        col_auth = pick("authority_id","authority","auth_id","rule_id","mcr","mcl","mre")
        col_text = pick("text","excerpt","quote","content","shard_text")
        col_src = pick("source_path","source","path","file_path","canonical_path")
        col_pin = pick("pinpoint","locator","page_line","page","page_num","line","lines","section")
        col_cit = pick("citation","cite","formal_citation")
        col_title = pick("title","heading","name")
        col_kind = pick("authority_kind","kind","type")

        inserted = 0
        deduped = 0
        total = 0

        for row in reader:
            total += 1
            a = norm_auth_id(row.get(col_auth)) if col_auth else None
            txt = (row.get(col_text) or "").strip() if col_text else ""
            if not txt:
                continue
            src = (row.get(col_src) or "").strip() if col_src else str(csv_path)
            pin = (row.get(col_pin) or "").strip() if col_pin else ""
            cit = (row.get(col_cit) or "").strip() if col_cit else ""
            title = (row.get(col_title) or "").strip() if col_title else ""
            kind = (row.get(col_kind) or "").strip() if col_kind else ""

            if a:
                upsert_authority(conn, a, kind or None, cit or None, title or None, src or None)

            ok, _ = insert_shard(conn, a, src, pin or None, txt, activity_id)
            if ok:
                inserted += 1
            else:
                deduped += 1

    logger.info(f"Imported index: {csv_path.name} | total_rows={total} inserted_shards={inserted} deduped={deduped}")
    return {"csv": str(csv_path), "total_rows": total, "inserted_shards": inserted, "deduped": deduped}

def import_edges_csv(conn: sqlite3.Connection, csv_path: Path, activity_id: str, logger) -> Dict[str, Any]:
    with csv_path.open("r", encoding="utf-8", errors="replace", newline="") as f:
        reader = csv.DictReader(f)
        cols = reader.fieldnames or []
        # Try a few common names
        def pick(*names):
            for n in names:
                if n in cols:
                    return n
            return None
        c_src = pick("src_authority_id","source_authority_id","src","source","from","from_id")
        c_dst = pick("dst_authority_id","target_authority_id","dst","target","to","to_id")
        c_type = pick("edge_type","type","relation")
        c_w = pick("weight","score")
        inserted = 0
        total = 0
        for row in reader:
            total += 1
            src = norm_auth_id(row.get(c_src)) if c_src else None
            dst = norm_auth_id(row.get(c_dst)) if c_dst else None
            if not src or not dst:
                continue
            et = (row.get(c_type) or "RELATED_TO").strip() if c_type else "RELATED_TO"
            try:
                w = float(row.get(c_w)) if c_w and row.get(c_w) else None
            except Exception:
                w = None
            conn.execute("""INSERT OR IGNORE INTO authority_edge(src_authority_id,dst_authority_id,edge_type,weight,created_at_utc,activity_id)
                            VALUES(?,?,?,?,?,?)""",
                         (src, dst, et, w, now_utc_iso(), activity_id))
            inserted += 1
        conn.commit()
    logger.info(f"Imported edges: {csv_path.name} | total_rows={total} inserted_edges~={inserted}")
    return {"csv": str(csv_path), "total_rows": total, "inserted_edges": inserted}

def build_neighbors_json(conn: sqlite3.Connection, out_path: Path) -> Path:
    ensure_dir(out_path.parent)
    adj: Dict[str, List[str]] = {}
    for src, dst in conn.execute("SELECT src_authority_id, dst_authority_id FROM authority_edge"):
        if src and dst:
            adj.setdefault(src, []).append(dst)
            adj.setdefault(dst, []).append(src)
    atomic_write_text(out_path, json.dumps(adj, ensure_ascii=False, indent=2))
    return out_path

def build_fts_sqlite(conn: sqlite3.Connection, out_fts: Path, logger) -> Path:
    ensure_dir(out_fts.parent)
    if out_fts.exists():
        out_fts.unlink()
    fts = sqlite3.connect(str(out_fts))
    fts.execute("CREATE VIRTUAL TABLE shards_fts USING fts5(shard_id UNINDEXED, text, source, authority_id, pinpoint)")
    rows = conn.execute("SELECT shard_id, text, source_path, authority_id, pinpoint FROM authority_shard")
    batch = []
    for shard_id, text, source, authority_id, pinpoint in rows:
        batch.append((shard_id, text or "", source or "", authority_id or "", pinpoint or ""))
        if len(batch) >= 2000:
            fts.executemany("INSERT INTO shards_fts(shard_id,text,source,authority_id,pinpoint) VALUES(?,?,?,?,?)", batch)
            batch.clear()
    if batch:
        fts.executemany("INSERT INTO shards_fts(shard_id,text,source,authority_id,pinpoint) VALUES(?,?,?,?,?)", batch)
    fts.commit()
    fts.close()
    logger.info(f"Built FTS sqlite: {out_fts}")
    return out_fts

def main() -> None:
    ap = argparse.ArgumentParser(description="Merge LitigationOS cycle CSVs into authority_store.sqlite (+ optional FTS).")
    ap.add_argument("--out-db", required=True, help="Output sqlite db path.")
    ap.add_argument("--import-index", action="append", help="CSV index file(s) to import as AuthorityShard rows.", default=[])
    ap.add_argument("--import-edges", action="append", help="CSV edge file(s) to import as authority edges.", default=[])
    ap.add_argument("--build-neighbors", action="store_true", help="Build authority_neighbors_adj.json from imported edges.")
    ap.add_argument("--neighbors-out", default="data/authority_neighbors_adj.json", help="Neighbors json output (relative to db dir if relative).")
    ap.add_argument("--build-fts", action="store_true", help="Build authority_shards_fts.sqlite from authority_store.sqlite.")
    ap.add_argument("--fts-out", default="data/authority_shards_fts.sqlite", help="FTS sqlite output (relative to db dir if relative).")
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    out_db = Path(args.out_db)
    log = configure_logging(out_db.parent / "logs" / "merge.log", verbose=args.verbose, quiet=args.quiet)
    run_id = f"merge_{dt.datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

    conn = connect_db(out_db)
    begin_activity(conn, run_id, "MergeRun", notes=f"inputs={len(args.import_index)} index_csv, {len(args.import_edges)} edge_csv")

    report: Dict[str, Any] = {"run_id": run_id, "started_at_utc": now_utc_iso(), "index_imports": [], "edge_imports": []}
    try:
        for p in args.import_index:
            csvp = Path(p)
            if not csvp.exists():
                log.warning(f"Missing index CSV: {csvp}")
                continue
            report["index_imports"].append(import_index_csv(conn, csvp, run_id, log))

        for p in args.import_edges:
            csvp = Path(p)
            if not csvp.exists():
                log.warning(f"Missing edge CSV: {csvp}")
                continue
            report["edge_imports"].append(import_edges_csv(conn, csvp, run_id, log))

        # neighbors
        if args.build_neighbors:
            neighbors_out = Path(args.neighbors_out)
            if not neighbors_out.is_absolute():
                neighbors_out = out_db.parent / neighbors_out
            build_neighbors_json(conn, neighbors_out)
            report["neighbors_json"] = str(neighbors_out)

        if args.build_fts:
            fts_out = Path(args.fts_out)
            if not fts_out.is_absolute():
                fts_out = out_db.parent / fts_out
            build_fts_sqlite(conn, fts_out, log)
            report["fts_sqlite"] = str(fts_out)

        end_activity(conn, run_id, status="OK")
        report["status"] = "OK"
    except Exception as e:
        end_activity(conn, run_id, status="ERROR", notes=str(e))
        report["status"] = "ERROR"
        report["error"] = str(e)
        raise
    finally:
        report["ended_at_utc"] = now_utc_iso()
        ensure_dir(out_db.parent / "reports")
        atomic_write_text(out_db.parent / "reports" / "merge_report.json", json.dumps(report, ensure_ascii=False, indent=2))
        # MD summary
        md = []
        md.append(f"# Merge Report\n\n- run_id: {run_id}\n- status: {report.get('status')}\n- started_at_utc: {report.get('started_at_utc')}\n- ended_at_utc: {report.get('ended_at_utc')}\n")
        md.append("\n## Index imports\n")
        for item in report.get("index_imports", []):
            md.append(f"- {item.get('csv')} | total_rows={item.get('total_rows')} inserted_shards={item.get('inserted_shards')} deduped={item.get('deduped')}")
        md.append("\n## Edge imports\n")
        for item in report.get("edge_imports", []):
            md.append(f"- {item.get('csv')} | total_rows={item.get('total_rows')} inserted_edges={item.get('inserted_edges')}")
        if report.get("neighbors_json"):
            md.append(f"\nNeighbors JSON: {report.get('neighbors_json')}\n")
        if report.get("fts_sqlite"):
            md.append(f"\nFTS sqlite: {report.get('fts_sqlite')}\n")
        atomic_write_text(out_db.parent / "reports" / "merge_report.md", "\n".join(md))

        conn.close()
        log.info(f"Done. DB: {out_db}")

if __name__ == "__main__":
    main()
