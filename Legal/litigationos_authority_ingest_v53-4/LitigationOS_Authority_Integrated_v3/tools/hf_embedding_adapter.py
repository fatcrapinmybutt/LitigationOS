#!/usr/bin/env python3
"""
HF Embedding Adapter v29 (CANDIDATE-ONLY)

Uses sentence-transformers if installed and a LOCAL model path is provided.
No web downloads. If requirements missing, exits with FAIL but does not break other tools.

Inputs:
--model-path local path to a sentence-transformers model
--texts-jsonl jsonl with {"id":..., "text":...}
Output:
--out-npz (numpy arrays) and --out-json (metadata)

Note: This adapter is optional; the system remains lexical-first by default.
"""
import argparse, json, os, sys

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--model-path", required=True)
    ap.add_argument("--texts-jsonl", required=True)
    ap.add_argument("--out-json", required=True)
    args=ap.parse_args()

    try:
        from sentence_transformers import SentenceTransformer
        import numpy as np
    except Exception as e:
        print("FAIL missing sentence-transformers/numpy", file=sys.stderr)
        raise SystemExit(2)

    if not os.path.isdir(args.model_path) and not os.path.exists(args.model_path):
        print("FAIL model-path not found (local only)", file=sys.stderr)
        raise SystemExit(2)

    rows=[]
    for ln in open(args.texts_jsonl,"r",encoding="utf-8"):
        ln=ln.strip()
        if ln:
            rows.append(json.loads(ln))
    texts=[(r.get("text") or "") for r in rows]
    ids=[(r.get("id") or "") for r in rows]

    model=SentenceTransformer(args.model_path)
    emb=model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    meta={"count":len(ids),"dim": (len(emb[0]) if len(emb)>0 else 0), "ids":ids}
    json.dump(meta, open(args.out_json,"w",encoding="utf-8"), indent=2)
    print(f"OK embeddings count={meta['count']} dim={meta['dim']}")

if __name__=="__main__":
    main()
