#!/usr/bin/env python3
import argparse, json, os, sys, subprocess, tempfile

def load_json(p): return json.load(open(p,"r",encoding="utf-8"))

def kw_score(text, kws):
    t=text.lower()
    return sum(1 for k in (kws or []) if str(k).strip().lower() in t and str(k).strip())

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--intents-json", required=True)
    ap.add_argument("--vehicle-registry-json", required=True)
    ap.add_argument("--out-json", required=True)
    ap.add_argument("--topk", type=int, default=20)
    ap.add_argument("--fts-search", default=os.path.join("tools","authority_anchor_fts_search.py"))
    args=ap.parse_args()

    if not os.path.exists(args.db) or os.path.getsize(args.db)==0:
        print("missing FTS db", file=sys.stderr); raise SystemExit(2)
    if not os.path.exists(args.fts_search):
        print("missing fts search tool", file=sys.stderr); raise SystemExit(2)

    intents=load_json(args.intents_json).get("intents") or []
    reg=load_json(args.vehicle_registry_json).get("vehicles") or []
    if not isinstance(intents, list) or not isinstance(reg, list):
        raise SystemExit(2)

    out={"intents":[],"meta":{"confidence":"CANDIDATE_ONLY","notes":"REGISTRY_MATCH + FTS_RETRIEVAL_ONLY"}}
    for it in intents:
        iid=it.get("id") or f"R{len(out['intents'])+1}"
        text=(it.get("text") or "").strip()

        scored=[(kw_score(text, v.get("keywords") or []), v) for v in reg]
        scored=[x for x in scored if x[0]>0]
        scored.sort(key=lambda x:(-x[0], (x[1].get("vehicle_id") or "")))

        candidates=[]
        for s,v in scored[:10]:
            q=(v.get("primary_authority_query") or "").strip() or text
            with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tf:
                tmp=tf.name
            subprocess.run([sys.executable, args.fts_search, "--db", args.db, "--q", q, "--topk", str(args.topk), "--out-json", tmp], check=True)
            res=json.load(open(tmp,"r",encoding="utf-8"))
            os.remove(tmp)
            candidates.append({
                "vehicle_id": v.get("vehicle_id"),
                "name": v.get("name"),
                "match_score": s,
                "retrieval_query": q,
                "forms": v.get("forms") or [],
                "authority_candidates": [{
                    "authority_ref": h.get("authority_ref"),
                    "doc_id": h.get("doc_id"),
                    "page": h.get("page"),
                    "header_lines": h.get("header_lines"),
                    "confidence":"CANDIDATE_ONLY"
                } for h in (res.get("results") or [])]
            })

        out["intents"].append({"id":iid,"text":text,"vehicle_candidates":candidates})

    json.dump(out, open(args.out_json,"w",encoding="utf-8"), indent=2, ensure_ascii=False)
    print(f"OK intents={len(out['intents'])}")

if __name__=="__main__":
    main()
