#!/usr/bin/env python3
"""
authority_triples_candidate.py (v33) — CANDIDATE ONLY / NON-INTERPRETIVE
Retrieval-assist: proposition text -> candidate authority_ref via FTS.
"""
import argparse, json, os, subprocess, sys, tempfile

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out-jsonl", required=True)
    ap.add_argument("--out-json", default="")
    ap.add_argument("--topk", type=int, default=15)
    ap.add_argument("--fts-search", default=os.path.join("tools","authority_anchor_fts_search.py"))
    args=ap.parse_args()

    if not os.path.exists(args.db) or os.path.getsize(args.db)==0:
        print("missing db", file=sys.stderr); raise SystemExit(2)
    if not os.path.exists(args.fts_search):
        print("missing fts search tool", file=sys.stderr); raise SystemExit(2)

    props=json.load(open(args.inp,"r",encoding="utf-8"))
    if not isinstance(props, list):
        print("input must be list", file=sys.stderr); raise SystemExit(2)

    total=0
    by_prop={}
    with open(args.out_jsonl,"w",encoding="utf-8") as out:
        for p in props:
            pid=p.get("id") or f"P{len(by_prop)+1}"
            text=(p.get("text") or "").strip()
            must=p.get("must_include") or []
            q=(p.get("query") or "").strip()
            if not q:
                q=" ".join(must) if must else " ".join(text.split()[:8])

            with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tf:
                tmp=tf.name
            subprocess.run([sys.executable, args.fts_search, "--db", args.db, "--q", q, "--topk", str(args.topk), "--out-json", tmp], check=True)
            res=json.load(open(tmp,"r",encoding="utf-8"))
            os.remove(tmp)

            kept=0
            for h in res.get("results", []):
                if must:
                    blob=((h.get("header_lines") or "")+" "+(h.get("authority_ref") or "")).lower()
                    if any(m.lower() not in blob for m in must):
                        continue
                out.write(json.dumps({
                    "proposition_id": pid,
                    "proposition_text": text,
                    "retrieval_query": q,
                    "authority_ref": h.get("authority_ref"),
                    "doc_id": h.get("doc_id"),
                    "page": h.get("page"),
                    "header_lines": h.get("header_lines"),
                    "confidence": "CANDIDATE_ONLY",
                    "notes": "RETRIEVAL_ONLY_NO_LEGAL_INTERPRETATION"
                }, ensure_ascii=False)+"\n")
                kept += 1
                total += 1
            by_prop[pid]=kept

    summary={"total_candidates": total, "by_proposition": by_prop}
    if args.out_json:
        json.dump(summary, open(args.out_json,"w",encoding="utf-8"), indent=2)
    print(f"OK total_candidates={total} propositions={len(by_prop)}")

if __name__=="__main__":
    main()
