#!/usr/bin/env python3
"""
Optional: build embeddings for authority shards (HF sentence-transformers) and store FAISS index + metadata.
Non-interpretive: index/metadata only (authority_ref + text_sha256).
"""
import argparse, os, sys, sqlite3, json, hashlib
def die(msg, code=2):
    print(msg, file=sys.stderr); raise SystemExit(code)
def main():
    ap=argparse.ArgumentParser(description="Build optional embedding vector index for authority shards")
    ap.add_argument("--db", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--model", default="sentence-transformers/all-MiniLM-L6-v2")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--batch", type=int, default=64)
    ap.add_argument("--dry-run", action="store_true")
    args=ap.parse_args()
    if not os.path.exists(args.db) or os.path.getsize(args.db)==0: die("DB missing/empty")
    os.makedirs(args.out_dir, exist_ok=True)
    try:
        from sentence_transformers import SentenceTransformer
        import numpy as np
    except Exception:
        die("Missing deps: pip install sentence-transformers numpy")
    use_faiss=True
    try:
        import faiss
    except Exception:
        use_faiss=False
    con=sqlite3.connect(args.db); con.row_factory=sqlite3.Row
    cur=con.cursor()
    q="SELECT authority_ref, text FROM shards"
    if args.limit and args.limit>0:
        q += " LIMIT ?"; cur.execute(q,(args.limit,))
    else:
        cur.execute(q)
    rows=cur.fetchall(); con.close()
    if args.dry_run:
        print(f"DRY_RUN shards={len(rows)} model={args.model} faiss={use_faiss}")
        return
    refs=[r["authority_ref"] for r in rows]
    texts=[(r["text"] or "").strip() or " " for r in rows]
    model=SentenceTransformer(args.model)
    vecs=[]
    for i in range(0,len(texts),args.batch):
        vecs.append(model.encode(texts[i:i+args.batch], show_progress_bar=False, normalize_embeddings=True))
    V=np.vstack(vecs).astype("float32")
    dim=V.shape[1]
    meta_path=os.path.join(args.out_dir,"vector_meta.jsonl")
    with open(meta_path,"w",encoding="utf-8") as f:
        for ref, txt in zip(refs, texts):
            f.write(json.dumps({"authority_ref":ref,"text_sha256":hashlib.sha256(txt.encode("utf-8",errors="ignore")).hexdigest()})+"\n")
    if use_faiss:
        index=faiss.IndexFlatIP(dim); index.add(V)
        faiss.write_index(index, os.path.join(args.out_dir,"vector_index.faiss"))
        print(f"OK faiss vectors={len(refs)} dim={dim}")
    else:
        np.save(os.path.join(args.out_dir,"vector_embeddings.npy"), V)
        print(f"OK numpy vectors={len(refs)} dim={dim}")
if __name__=="__main__":
    main()
