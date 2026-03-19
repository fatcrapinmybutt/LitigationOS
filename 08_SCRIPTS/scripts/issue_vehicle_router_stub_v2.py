#!/usr/bin/env python3
"""LitigationOS Issue/Vehicle Router Stub (candidate sets only)

Chain:
FTS candidates -> BM25 rerank -> expand by authority_id neighbors (optional) -> emit supporting shards + pinpoints.

Inputs:
- authority_shards_fts.sqlite with virtual table shards_fts(shard_id,text,source,authority_id,pinpoint)
- authority_neighbors_adj.json (optional) mapping authority_id -> neighbor authority_ids

Outputs:
- issue_vehicle_candidates.json

"""
from __future__ import annotations
import argparse, json, sqlite3
from pathlib import Path

def fts_rows(db_path: str, query: str, limit: int):
    con=sqlite3.connect(db_path)
    cur=con.cursor()
    cur.execute("SELECT shard_id, text, source, authority_id, pinpoint FROM shards_fts WHERE shards_fts MATCH ? LIMIT ?",
                (query, limit))
    rows=cur.fetchall()
    con.close()
    return rows

def bm25_rerank(query: str, rows, text_idx=1):
    toks=[t for t in query.lower().split() if t.strip()]
    docs=[]
    for r in rows:
        txt=(r[text_idx] or "")
        low=txt.lower()
        tf=sum(low.count(t) for t in toks) or 1
        dl=max(1, len(txt.split()))
        docs.append((r, tf, dl))
    avgdl=(sum(d[2] for d in docs)/len(docs)) if docs else 1.0
    k1=1.2; b=0.75
    scored=[]
    for r,tf,dl in docs:
        score=(tf*(k1+1.0))/(tf + k1*(1.0-b + b*(dl/(avgdl or 1.0))))
        scored.append((score, r))
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored

def load_neighbors(p: str|None):
    if not p:
        return {}
    pp=Path(p)
    if not pp.exists():
        return {}
    return json.loads(pp.read_text(encoding="utf-8"))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--issues_json", required=True)
    ap.add_argument("--vehicles_json", required=True)
    ap.add_argument("--issue_vehicle_map_json", required=True)
    ap.add_argument("--authority_fts_db", required=True)
    ap.add_argument("--neighbors_json", default="")
    ap.add_argument("--out_json", required=True)
    ap.add_argument("--topk", type=int, default=250)
    ap.add_argument("--per_authority_cap", type=int, default=3)
    ap.add_argument("--neighbor_hops", type=int, default=1)
    ap.add_argument("--neighbor_cap", type=int, default=50)
    args=ap.parse_args()

    issues=json.loads(Path(args.issues_json).read_text(encoding="utf-8")).get("issues", [])
    vehicles={v["vehicle_id"]: v for v in json.loads(Path(args.vehicles_json).read_text(encoding="utf-8")).get("vehicles", [])}
    ivm=json.loads(Path(args.issue_vehicle_map_json).read_text(encoding="utf-8")).get("issue_vehicle_map", {})
    neighbors=load_neighbors(args.neighbors_json) if args.neighbors_json else {}

    out={"generated_at":Path(args.issues_json).stat().st_mtime, "issues":[]}

    for issue in issues:
        q=issue.get("query","")
        rows=fts_rows(args.authority_fts_db, q, args.topk)
        ranked=bm25_rerank(q, rows, 1)

        by_auth={}
        for score,(sid,txt,src,aid,pin) in ranked:
            if not aid:
                continue
            a=by_auth.setdefault(aid, {"authority_id":aid,"max_bm25":0.0,"supporting_shards":[]})
            if score>a["max_bm25"]:
                a["max_bm25"]=score
            if len(a["supporting_shards"])<args.per_authority_cap:
                a["supporting_shards"].append({"bm25":score,"shard_id":sid,"source":src,"pinpoint":pin,"text":txt})

        # neighbor expansion (authority_id neighbors only, no additional shard fetch here; downstream can)
        expanded=set(by_auth.keys())
        if neighbors and args.neighbor_hops>0:
            frontier=set(by_auth.keys())
            for _ in range(args.neighbor_hops):
                nxt=set()
                for a in list(frontier)[:args.neighbor_cap]:
                    for nb in neighbors.get(a, []):
                        if nb not in expanded:
                            nxt.add(nb); expanded.add(nb)
                frontier=nxt

        auth_list=sorted(by_auth.values(), key=lambda x: x["max_bm25"], reverse=True)[:200]
        veh_ids=ivm.get(issue.get("issue_id",""), [])
        veh_list=[vehicles[v] for v in veh_ids if v in vehicles]

        out["issues"].append({
            "issue_id": issue.get("issue_id"),
            "label": issue.get("label"),
            "query": q,
            "candidate_vehicles": veh_list,
            "candidate_authorities": auth_list,
            "expanded_neighbor_authority_ids": sorted(expanded - set(by_auth.keys()))
        })

    Path(args.out_json).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {args.out_json}")

if __name__=="__main__":
    main()
