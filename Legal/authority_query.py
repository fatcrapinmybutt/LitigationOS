#!/usr/bin/env python3
"""
LitigationOS Authority Query Tool (offline, deterministic)
- Searches Authority Store SQLite (FTS5) built from Michigan authority PDFs converted with pdftotext -layout.
- Provides: FTS search, anchor lookup, ref fetch, and export of results with pinpoints.

No network calls. No authority rewriting. Outputs are pointers + verbatim snippets only.

USAGE:
  python authority_query.py --db authority_store.sqlite search --q "MCR 2.003" --k 25
  python authority_query.py --db authority_store.sqlite anchor --a "MCR 2.003" --k 50
  python authority_query.py --db authority_store.sqlite get --ref "DOC_xxxxxxxx:p0001"
"""

import argparse, json, os, re, sqlite3, sys, csv
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple

def die(msg: str, code: int = 2) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)

def ensure_db(path: str) -> None:
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        die(f"DB not found or empty: {path}")

def connect(db_path: str) -> sqlite3.Connection:
    ensure_db(db_path)
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    return con

def fts_escape(q: str) -> str:
    # Keep simple: wrap in quotes if contains spaces; escape quotes
    q = q.replace('"', '""')
    if any(c.isspace() for c in q.strip()):
        return f'"{q}"'
    return q

def search_fts(con: sqlite3.Connection, q: str, k: int) -> List[Dict[str, Any]]:
    # Use FTS5 bm25; query through MATCH.
    # If user provides already-FTS syntax, pass through; otherwise use escaped token/phrase.
    q2 = q.strip()
    if not q2:
        return []
    # Heuristic: if contains FTS operators, don't escape.
    if any(op in q2 for op in [' NEAR ', '*', ' OR ', ' AND ', ' NOT ', ':']):
        match = q2
    else:
        match = fts_escape(q2)

    cur = con.cursor()
    cur.execute("""
        SELECT s.authority_ref, s.doc_id, s.page, s.pdf_sha256, s.txt_sha256, s.text_sha256,
               s.header_lines, s.lexical_anchors,
               snippet(shards_fts, 3, '[', ']', '…', 12) AS snippet,
               bm25(shards_fts) AS score
        FROM shards_fts
        JOIN shards s ON s.authority_ref = shards_fts.authority_ref
        WHERE shards_fts MATCH ?
        ORDER BY score
        LIMIT ?;
    """, (match, k))
    return [dict(r) for r in cur.fetchall()]

def get_ref(con: sqlite3.Connection, ref: str) -> Optional[Dict[str, Any]]:
    cur = con.cursor()
    cur.execute("""
        SELECT authority_ref, doc_id, page, pdf_sha256, txt_sha256, text_sha256,
               header_lines, lexical_anchors, text
        FROM shards
        WHERE authority_ref = ?;
    """, (ref,))
    row = cur.fetchone()
    return dict(row) if row else None

ANCHOR_SPLIT = re.compile(r"\s*\|\s*")

def anchor_lookup(con: sqlite3.Connection, anchor: str, k: int) -> List[Dict[str, Any]]:
    # Anchors are stored as a pipe-delimited string in shards.lexical_anchors
    a = anchor.strip()
    if not a:
        return []
    # Exact match within pipe-delimited string: use LIKE guards
    pat_mid = f"%| {a} |%"
    pat_start = f"{a} |%"
    pat_end = f"%| {a}"
    pat_only = f"{a}"
    cur = con.cursor()
    cur.execute("""
        SELECT authority_ref, doc_id, page, pdf_sha256, txt_sha256, text_sha256,
               header_lines, lexical_anchors
        FROM shards
        WHERE lexical_anchors = ?
           OR lexical_anchors LIKE ?
           OR lexical_anchors LIKE ?
           OR lexical_anchors LIKE ?
        ORDER BY doc_id, page
        LIMIT ?;
    """, (pat_only, pat_mid, pat_start, pat_end, k))
    return [dict(r) for r in cur.fetchall()]

def write_json(path: str, rows: List[Dict[str, Any]]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2, ensure_ascii=False)

def write_csv(path: str, rows: List[Dict[str, Any]]) -> None:
    if not rows:
        with open(path, "w", newline="", encoding="utf-8") as f:
            pass
        return
    cols = sorted({k for r in rows for k in r.keys()})
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow(r)

def cmd_search(args: argparse.Namespace) -> None:
    con = connect(args.db)
    rows = search_fts(con, args.q, args.k)
    if args.out_json:
        write_json(args.out_json, rows)
    if args.out_csv:
        write_csv(args.out_csv, rows)
    if args.print:
        for r in rows:
            print(f"{r['authority_ref']}  score={r.get('score')}")
            sn = r.get("snippet") or ""
            print(sn)
            print("-"*80)

def cmd_anchor(args: argparse.Namespace) -> None:
    con = connect(args.db)
    rows = anchor_lookup(con, args.a, args.k)
    if args.out_json:
        write_json(args.out_json, rows)
    if args.out_csv:
        write_csv(args.out_csv, rows)
    if args.print:
        for r in rows:
            print(f"{r['authority_ref']}  {r.get('lexical_anchors','')}")
            print((r.get("header_lines") or "").splitlines()[:5])
            print("-"*80)

def cmd_get(args: argparse.Namespace) -> None:
    con = connect(args.db)
    row = get_ref(con, args.ref)
    if not row:
        die(f"Not found: {args.ref}", 3)
    if args.out_json:
        write_json(args.out_json, [row])
    if args.print:
        print(f"{row['authority_ref']}  doc={row['doc_id']}  page={row['page']}")
        print(row.get("header_lines") or "")
        print("-"*80)
        txt = row.get("text") or ""
        if args.max_chars and len(txt) > args.max_chars:
            txt = txt[:args.max_chars] + "\n…(truncated output; source stored verbatim in DB)…\n"
        print(txt)

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="authority_query.py",
        formatter_class=argparse.RawTextHelpFormatter,
        description="Query Michigan authority store (FTS + anchors) with pinpoint refs."
    )
    p.add_argument("--db", required=True, help="Path to authority_store.sqlite")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("search", help="FTS search in header_lines/lexical_anchors/text")
    s.add_argument("--q", required=True, help="Query string")
    s.add_argument("--k", type=int, default=25, help="Top K results")
    s.add_argument("--out-json", dest="out_json", help="Write results to JSON")
    s.add_argument("--out-csv", dest="out_csv", help="Write results to CSV")
    s.add_argument("--print", action="store_true", help="Print snippets")
    s.set_defaults(func=cmd_search)

    a = sub.add_parser("anchor", help="Exact-ish anchor lookup in lexical_anchors")
    a.add_argument("--a", required=True, help="Anchor string (e.g., 'MCR 2.003')")
    a.add_argument("--k", type=int, default=200, help="Max rows")
    a.add_argument("--out-json", dest="out_json", help="Write results to JSON")
    a.add_argument("--out-csv", dest="out_csv", help="Write results to CSV")
    a.add_argument("--print", action="store_true", help="Print headers")
    a.set_defaults(func=cmd_anchor)

    g = sub.add_parser("get", help="Fetch one shard by authority_ref")
    g.add_argument("--ref", required=True, help="Authority ref, e.g., DOC_xxx:p0001")
    g.add_argument("--out-json", dest="out_json", help="Write record to JSON")
    g.add_argument("--print", action="store_true", help="Print full text")
    g.add_argument("--max-chars", type=int, default=12000, help="Max chars to print (DB retains full text)")
    g.set_defaults(func=cmd_get)

    return p

def main() -> None:
    p = build_parser()
    args = p.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
