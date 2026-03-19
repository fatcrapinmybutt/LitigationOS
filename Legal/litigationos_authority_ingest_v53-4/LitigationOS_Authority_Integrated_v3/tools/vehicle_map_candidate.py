#!/usr/bin/env python3
"""
vehicle_map_candidate.py (v33) — CANDIDATE ONLY / NON-INTERPRETIVE
Relief intents -> candidate authority_ref via FTS.
"""
import argparse, json, os, subprocess, sys, tempfile

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out-json", required=True)
    ap.add_argument("--topk", type=int, default=25)
    ap.add_argument("--fts-search", default=os.path.join("tools","authority_anchor_fts_search.py"))
    args=ap.parse_args()

    payload=json.load(open(args.inp,"r",encoding="utf-8"))
    intents=payload.get("intents") or []
    if not isinstance(intents, list):
        print("intents must be list", file=sys.stderr); raise SystemExit(2)

    out={"intents":[],"meta":{"confidence":"CANDIDATE_ONLY","notes":"RETRIEVAL_ONLY_NO_VEHICLE_ASSERTIONS"}}
    for it in intents:
        iid=it.get("id") or f"R{len(out['intents'])+1}"
        text=(it.get("text") or "").strip()
        q=text
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tf:
            tmp=tf.name
        subprocess.run([sys.executable, args.fts_search, "--db", args.db, "--q", q, "--topk", str(args.topk), "--out-json", tmp], check=True)
        res=json.load(open(tmp,"r",encoding="utf-8"))
        os.remove(tmp)

        out["intents"].append({
            "id": iid,
            "text": text,
            "retrieval_query": q,
            "candidates": [{
                "authority_ref": h.get("authority_ref"),
                "doc_id": h.get("doc_id"),
                "page": h.get("page"),
                "header_lines": h.get("header_lines"),
                "confidence": "CANDIDATE_ONLY"
            } for h in res.get("results", [])]
        })

    json.dump(out, open(args.out_json,"w",encoding="utf-8"), indent=2, ensure_ascii=False)
    print(f"OK intents={len(out['intents'])}")

if __name__=="__main__":
    main()
