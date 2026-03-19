#!/usr/bin/env python3
import argparse, json, os, sys, subprocess, tempfile

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--vehicle-elements-json", required=True)
    ap.add_argument("--out-json", required=True)
    ap.add_argument("--topk", type=int, default=15)
    ap.add_argument("--fts-search", default=os.path.join("tools","authority_anchor_fts_search.py"))
    args=ap.parse_args()

    items=json.load(open(args.vehicle_elements_json,"r",encoding="utf-8"))
    if not isinstance(items, list):
        raise SystemExit(2)

    out={"vehicles":[],"meta":{"confidence":"CANDIDATE_ONLY","notes":"USER_ELEMENTS + FTS_RETRIEVAL_ONLY"}}
    for it in items:
        vid=it.get("vehicle_id") or ""
        els=it.get("elements") or []
        qs=it.get("authority_queries") or []
        cand=[]
        for q in qs:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tf:
                tmp=tf.name
            subprocess.run([sys.executable, args.fts_search, "--db", args.db, "--q", str(q), "--topk", str(args.topk), "--out-json", tmp], check=True)
            res=json.load(open(tmp,"r",encoding="utf-8"))
            os.remove(tmp)
            cand.append({"query":q,"authority_candidates":res.get("results", [])})
        out["vehicles"].append({"vehicle_id":vid,"elements":els,"authority_queries":qs,"authority":cand})
    json.dump(out, open(args.out_json,"w",encoding="utf-8"), indent=2, ensure_ascii=False)
    print(f"OK vehicles={len(out['vehicles'])}")

if __name__=="__main__":
    main()
