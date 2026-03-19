#!/usr/bin/env python3
"""
embedding_adapter_hf_candidate.py (v43) — OPTIONAL / CANDIDATE

Interface for generating embeddings locally with Hugging Face / sentence-transformers when installed.
This bundle does not vendor models; you supply them offline.

- If sentence_transformers is available, uses it.
- Otherwise emits a clear error and exits nonzero.

Input: JSONL shards (authority_shards.jsonl) or arbitrary lines.
Output: JSONL with {"id":..., "embedding":[...]} suitable for external vector DB ingest.

No network calls. No auto-download. Deterministic only if model is present locally.
"""
import argparse, json, os, sys, hashlib

def sha(s):
    import hashlib
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--model", required=True, help="local model name/path for sentence-transformers")
    ap.add_argument("--in-jsonl", required=True)
    ap.add_argument("--text-field", default="text")
    ap.add_argument("--id-field", default="authority_ref")
    ap.add_argument("--out-jsonl", required=True)
    ap.add_argument("--max", type=int, default=0, help="0=all")
    args=ap.parse_args()

    try:
        from sentence_transformers import SentenceTransformer
    except Exception as e:
        print("ERROR: sentence_transformers not installed. Install offline or vendor wheel. No web download performed.", file=sys.stderr)
        raise SystemExit(2)

    model=SentenceTransformer(args.model)
    n=0
    with open(args.in_jsonl,"r",encoding="utf-8",errors="replace") as f_in, open(args.out_jsonl,"w",encoding="utf-8") as f_out:
        for line in f_in:
            if not line.strip(): continue
            obj=json.loads(line)
            text=(obj.get(args.text_field) or "").strip()
            if not text: continue
            _id=(obj.get(args.id_field) or "") or f"ID_{sha(text)}"
            vec=model.encode([text], normalize_embeddings=True)[0].tolist()
            f_out.write(json.dumps({"id":_id,"embedding":vec},ensure_ascii=False)+"\n")
            n+=1
            if args.max and n>=args.max: break
    print("OK embeddings=", n)

if __name__=="__main__":
    main()
