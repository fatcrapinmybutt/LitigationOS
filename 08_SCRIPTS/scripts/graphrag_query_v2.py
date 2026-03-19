#!/usr/bin/env python3
"""GraphRAG Query — AuthorityGraph lane

Chain:
1) FTS candidates (SQLite FTS)
2) BM25 rerank
3) Expand by authority_id neighbors (authority_neighbors_adj.json)
4) Return supporting shards + pinpoints

Notes:
- Neighbor expansion only returns authority_ids by default; you can optionally fetch shards for those authority_ids
  by querying the shards table (non-FTS) if present in your datastore, or by running a second FTS query.

"""
from __future__ import annotations
import argparse, json, sqlite3
from pathlib import Path

def bm25(query: str, text: str, avgdl: float, k1=1.2, b=0.75):
    toks=[t for t in query.lower().split() if t.strip()]
    low=text.lower()
    tf=sum(low.count(t) for t in toks) or 1
    dl=max(1, len(text.split()))
    return (tf*(k1+1.0))/(tf + k1*(1.0-b + b*(dl/(avgdl or 1.0))))

def fts_search(db_path: str, query: str, limit: int):
    con=sqlite3.connect(db_path)
    cur=con.cursor()
    cur.execute("SELECT shard_id, text, source, authority_id, pinpoint FROM shards_fts WHERE shards_fts MATCH ? LIMIT ?",
                (query, limit))
    rows=cur.fetchall()
    con.close()
    return rows

def load_neighbors(p: Path):
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--authority_fts_db", required=True)
    ap.add_argument("--neighbors_json", required=True)
    ap.add_argument("--query", required=True)
    ap.add_argument("--topk", type=int, default=250)
    ap.add_argument("--per_authority_cap", type=int, default=3)
    ap.add_argument("--neighbor_hops", type=int, default=1)
    ap.add_argument("--neighbor_cap", type=int, default=75)
    ap.add_argument("--out_json", required=True)
    args=ap.parse_args()

    rows=fts_search(args.authority_fts_db, args.query, args.topk)

    dls=[max(1,len((r[1] or '').split())) for r in rows] or [1]
    avgdl=sum(dls)/len(dls)
    scored=[]
    for r in rows:
        scored.append((bm25(args.query, r[1] or '', avgdl), r))
    scored.sort(key=lambda x: x[0], reverse=True)

    # aggregate by authority_id
    by_auth={}
    for score,(sid,txt,src,aid,pin) in scored:
        if not aid:
            continue
        a=by_auth.setdefault(aid, {"authority_id":aid,"max_bm25":0.0,"supporting_shards":[]})
        if score>a["max_bm25"]:
            a["max_bm25"]=score
        if len(a["supporting_shards"])<args.per_authority_cap:
            a["supporting_shards"].append({"bm25":score,"shard_id":sid,"source":src,"pinpoint":pin,"text":txt})

    neighbors=load_neighbors(Path(args.neighbors_json))
    expanded=set(by_auth.keys())
    frontier=set(by_auth.keys())
    for _ in range(args.neighbor_hops):
        nxt=set()
        for a in list(frontier)[:args.neighbor_cap]:
            for nb in neighbors.get(a, []):
                if nb not in expanded:
                    expanded.add(nb); nxt.add(nb)
        frontier=nxt

    out={
        "query": args.query,
        "authority_hits": sorted(by_auth.values(), key=lambda x: x["max_bm25"], reverse=True),
        "expanded_neighbor_authority_ids": sorted(expanded - set(by_auth.keys()))
    }
    Path(args.out_json).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {args.out_json}")

if __name__=="__main__":
    main()
