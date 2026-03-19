#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
graphrag_query_v2.py — AuthorityGraph retrieval: FTS -> BM25 rerank -> neighbor expansion -> context pack.

Upgrades:
- Supports multi-query batch via --queries-file (one query per line)
- Emits:
  - out_json: ranked shards grouped by authority_id + per-shard pinpoints
  - out_md: compact context pack with citations (source+pinpoint)
- Diversity controls:
  - max_shards_per_authority
  - max_total_shards
  - source_diversity (avoid too many shards from same source)
- Neighbor expansion:
  - uses authority_neighbors_adj.json (built from edges) to expand authority_ids
  - optional fetch of non-FTS shards from authority_store.sqlite if provided

Inputs:
- FTS sqlite: authority_shards_fts.sqlite with table shards_fts(shard_id,text,source,authority_id,pinpoint)
- Neighbors json: authority_neighbors_adj.json mapping authority_id -> [neighbor_ids]
- Optional store sqlite: authority_store.sqlite containing authority_shard table

No network calls.

USAGE:
  python graphrag_query_v2.py --fts authority_shards_fts.sqlite --neighbors authority_neighbors_adj.json --query "MCR 2.003 disqualification standard" --out out.json --out-md out.md
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sqlite3
from collections import defaultdict, Counter
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

try:
    from litigationos_common import ensure_dir, atomic_write_text
except Exception:
    def ensure_dir(p: Path) -> Path:
        p.mkdir(parents=True, exist_ok=True); return p
    def atomic_write_text(path: Path, text: str, encoding: str="utf-8") -> None:
        ensure_dir(path.parent); path.write_text(text, encoding=encoding)

TOKEN_RE = re.compile(r"[A-Za-z0-9_]+", re.UNICODE)

def tokenize(s: str) -> List[str]:
    return [t.lower() for t in TOKEN_RE.findall(s or "")]

def bm25_scores(docs: List[str], query: str, k1: float = 1.5, b: float = 0.75) -> List[float]:
    q = tokenize(query)
    if not q:
        return [0.0 for _ in docs]
    N = len(docs)
    doc_tokens = [tokenize(d) for d in docs]
    df = Counter()
    for toks in doc_tokens:
        df.update(set(toks))
    avgdl = sum(len(t) for t in doc_tokens) / max(1, N)
    scores = []
    for toks in doc_tokens:
        freq = Counter(toks)
        dl = len(toks)
        score = 0.0
        for term in q:
            n = df.get(term, 0)
            if n == 0:
                continue
            idf = math.log(1 + (N - n + 0.5) / (n + 0.5))
            tf = freq.get(term, 0)
            denom = tf + k1 * (1 - b + b * (dl / max(1e-9, avgdl)))
            score += idf * ((tf * (k1 + 1)) / max(1e-9, denom))
        scores.append(score)
    return scores

def fts_candidates(fts_path: Path, query: str, limit: int = 200) -> List[Dict[str, Any]]:
    conn = sqlite3.connect(str(fts_path))
    conn.row_factory = sqlite3.Row
    cur = conn.execute(
        "SELECT shard_id, text, source, authority_id, pinpoint FROM shards_fts WHERE shards_fts MATCH ? LIMIT ?",
        (query, limit)
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def load_neighbors(neighbors_path: Optional[Path]) -> Dict[str, List[str]]:
    if not neighbors_path or not neighbors_path.exists():
        return {}
    return json.loads(neighbors_path.read_text(encoding="utf-8"))

def expand_authorities(seed_authority_ids: List[str], neighbors: Dict[str, List[str]], depth: int = 1, max_nodes: int = 5000) -> List[str]:
    seen = set(seed_authority_ids)
    frontier = set(seed_authority_ids)
    for _ in range(depth):
        nxt = set()
        for a in frontier:
            for nb in neighbors.get(a, []):
                if nb not in seen:
                    seen.add(nb)
                    nxt.add(nb)
                    if len(seen) >= max_nodes:
                        return list(seen)
        frontier = nxt
        if not frontier:
            break
    return list(seen)

def fetch_shards_for_authorities(store_sqlite: Path, authority_ids: List[str], limit_per_auth: int = 10) -> List[Dict[str, Any]]:
    if not store_sqlite.exists():
        return []
    conn = sqlite3.connect(str(store_sqlite))
    conn.row_factory = sqlite3.Row
    out = []
    for a in authority_ids:
        cur = conn.execute(
            "SELECT shard_id, text, source_path AS source, authority_id, pinpoint FROM authority_shard WHERE authority_id=? ORDER BY shard_id DESC LIMIT ?",
            (a, limit_per_auth)
        )
        out.extend([dict(r) for r in cur.fetchall()])
    conn.close()
    return out

def build_context_pack(rows: List[Dict[str, Any]], query: str, max_total: int, max_per_auth: int, source_diversity: int) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    # rank by bm25 over text
    docs = [r.get("text","") for r in rows]
    scores = bm25_scores(docs, query)
    for r, s in zip(rows, scores):
        r["bm25"] = float(s)
    rows.sort(key=lambda r: r.get("bm25", 0.0), reverse=True)

    # diversity selection
    selected = []
    per_auth = defaultdict(int)
    per_source = defaultdict(int)
    for r in rows:
        a = (r.get("authority_id") or "").strip()
        src = (r.get("source") or "").strip()
        if per_auth[a] >= max_per_auth:
            continue
        if source_diversity and per_source[src] >= source_diversity:
            continue
        selected.append(r)
        per_auth[a] += 1
        per_source[src] += 1
        if len(selected) >= max_total:
            break

    grouped = defaultdict(list)
    for r in selected:
        grouped[r.get("authority_id") or ""].append(r)

    summary = {
        "query": query,
        "selected_total": len(selected),
        "authorities": len(grouped),
        "top_authority_ids": [a for a,_ in sorted(((a, max(x["bm25"] for x in xs)) for a,xs in grouped.items()), key=lambda t: t[1], reverse=True)[:25]]
    }
    return selected, summary

def to_markdown(selected: List[Dict[str, Any]], summary: Dict[str, Any]) -> str:
    md = []
    md.append(f"# Context Pack\n\n**Query:** {summary.get('query')}\n\n- Selected shards: {summary.get('selected_total')}\n- Authorities: {summary.get('authorities')}\n")
    md.append("\n## Shards (ranked)\n")
    for i, r in enumerate(selected, 1):
        a = r.get("authority_id") or ""
        src = r.get("source") or ""
        pin = r.get("pinpoint") or ""
        text = (r.get("text") or "").strip()
        if len(text) > 900:
            text = text[:900] + "…"
        md.append(f"### {i}. {a}\n- Source: {src}\n- Pinpoint: {pin}\n- BM25: {r.get('bm25'):.4f}\n\n{text}\n")
    return "\n".join(md)

def run_single(args, query: str, out_prefix: str) -> Dict[str, Any]:
    fts_rows = fts_candidates(Path(args.fts), query, limit=args.fts_limit)
    neighbors = load_neighbors(Path(args.neighbors) if args.neighbors else None)

    # group by authority_id and expand
    seed_auths = []
    for r in fts_rows:
        a = (r.get("authority_id") or "").strip()
        if a:
            seed_auths.append(a)
    seed_auths = list(dict.fromkeys(seed_auths))  # preserve order unique
    expanded_auths = expand_authorities(seed_auths, neighbors, depth=args.neighbor_depth, max_nodes=args.neighbor_max) if args.neighbors else seed_auths

    # optional fetch extra shards from store sqlite
    extra = []
    if args.store_sqlite and args.neighbors_fetch_shards:
        extra = fetch_shards_for_authorities(Path(args.store_sqlite), expanded_auths, limit_per_auth=args.neighbors_fetch_limit)

    combined = fts_rows + extra

    selected, summary = build_context_pack(
        combined, query=query,
        max_total=args.max_total_shards,
        max_per_auth=args.max_shards_per_authority,
        source_diversity=args.max_shards_per_source,
    )

    out = {
        "query": query,
        "summary": summary,
        "seed_authority_ids": seed_auths,
        "expanded_authority_ids": expanded_auths,
        "results": selected,
    }

    out_json = Path(args.out_json)
    if args.batch:
        out_json = out_json.parent / f"{safe_name(out_prefix)}.json"
    atomic_write_text(out_json, json.dumps(out, ensure_ascii=False, indent=2))

    if args.out_md:
        out_md = Path(args.out_md)
        if args.batch:
            out_md = out_md.parent / f"{safe_name(out_prefix)}.md"
        atomic_write_text(out_md, to_markdown(selected, summary))

    return {"out_json": str(out_json), "out_md": str(out_md) if args.out_md else None}

def safe_name(s: str) -> str:
    s = re.sub(r"[^A-Za-z0-9._\-]+", "_", s).strip("_")
    return s[:120] or "query"

def main() -> None:
    ap = argparse.ArgumentParser(description="GraphRAG Query — FTS -> BM25 -> neighbor expansion -> context pack.")
    ap.add_argument("--fts", required=True, help="FTS sqlite path (authority_shards_fts.sqlite).")
    ap.add_argument("--neighbors", help="Neighbors json path (authority_neighbors_adj.json).")
    ap.add_argument("--store-sqlite", help="Optional authority_store.sqlite for fetching extra shards.")
    ap.add_argument("--query", help="Single query string.")
    ap.add_argument("--queries-file", help="File with one query per line (batch).")
    ap.add_argument("--out-json", required=True, help="Output json path (single) or directory (batch).")
    ap.add_argument("--out-md", help="Optional markdown output (single) or directory (batch).")
    ap.add_argument("--fts-limit", type=int, default=200)
    ap.add_argument("--neighbor-depth", type=int, default=1)
    ap.add_argument("--neighbor-max", type=int, default=5000)
    ap.add_argument("--neighbors-fetch-shards", action="store_true", help="Fetch shards for expanded authorities from store sqlite.")
    ap.add_argument("--neighbors-fetch-limit", type=int, default=5)
    ap.add_argument("--max-total-shards", type=int, default=60)
    ap.add_argument("--max-shards-per-authority", type=int, default=6)
    ap.add_argument("--max-shards-per-source", type=int, default=20)
    args = ap.parse_args()

    # Validate outputs
    out_json = Path(args.out_json)
    out_md = Path(args.out_md) if args.out_md else None
    args.batch = False

    if args.queries_file:
        args.batch = True
        ensure_dir(out_json)
        if out_md:
            ensure_dir(out_md)
        queries = []
        for line in Path(args.queries_file).read_text(encoding="utf-8", errors="replace").splitlines():
            q = line.strip()
            if q and not q.startswith("#"):
                queries.append(q)
        results = []
        for i, q in enumerate(queries, 1):
            prefix = f"q{i:03d}_{q[:50]}"
            res = run_single(args, q, out_prefix=prefix)
            results.append({"query": q, **res})
        # master index
        atomic_write_text(out_json / "batch_index.json", json.dumps({"results": results}, ensure_ascii=False, indent=2))
        return

    if not args.query:
        raise SystemExit("Provide --query or --queries-file")

    # Single mode
    ensure_dir(out_json.parent)
    if out_md:
        ensure_dir(out_md.parent)
    run_single(args, args.query, out_prefix="query")

if __name__ == "__main__":
    main()
