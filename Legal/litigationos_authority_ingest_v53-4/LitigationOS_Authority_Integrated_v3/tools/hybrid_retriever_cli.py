#!/usr/bin/env python3
import argparse, os, sqlite3, sys, json
def die(msg, code=2):
    print(msg, file=sys.stderr); raise SystemExit(code)
def fts_query(db, q, limit):
    con=sqlite3.connect(db); con.row_factory=sqlite3.Row
    cur=con.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='shards_fts';")
    if not cur.fetchone(): die("FTS table shards_fts not found. Run build_fts_index.py first.")
    cur.execute("""
      SELECT authority_ref, snippet(shards_fts, 1, '[', ']', ' … ', 20) AS snippet, bm25(shards_fts) AS score
      FROM shards_fts
      WHERE shards_fts MATCH ?
      ORDER BY score
      LIMIT ?;
    """,(q,limit))
    rows=[dict(r) for r in cur.fetchall()]; con.close(); return rows
def main():
    ap=argparse.ArgumentParser(description="Hybrid Retriever CLI (FTS + optional FAISS rerank)")
    ap.add_argument("--db", required=True)
    ap.add_argument("--q", required=True)
    ap.add_argument("--limit", type=int, default=25)
    ap.add_argument("--vector-dir", default="")
    ap.add_argument("--model", default="sentence-transformers/all-MiniLM-L6-v2")
    ap.add_argument("--out-json", default="")
    args=ap.parse_args()
    if not os.path.exists(args.db) or os.path.getsize(args.db)==0: die("DB missing/empty")
    results=fts_query(args.db, args.q, args.limit)
    if args.vector_dir:
        idx_path=os.path.join(args.vector_dir,"vector_index.faiss")
        meta_path=os.path.join(args.vector_dir,"vector_meta.jsonl")
        if os.path.exists(idx_path) and os.path.exists(meta_path):
            try:
                from sentence_transformers import SentenceTransformer
                import numpy as np, faiss
            except Exception:
                pass
            else:
                model=SentenceTransformer(args.model)
                qvec=model.encode([args.q], normalize_embeddings=True).astype("float32")
                index=faiss.read_index(idx_path)
                D,I=index.search(qvec, min(1000, index.ntotal))
                refs=[]
                with open(meta_path,"r",encoding="utf-8") as f:
                    for ln in f: refs.append(json.loads(ln)["authority_ref"])
                vec_scores={}
                for sc, ix in zip(D[0].tolist(), I[0].tolist()):
                    if 0 <= ix < len(refs): vec_scores[refs[ix]]=float(sc)
                for r in results: r["vector_score"]=vec_scores.get(r["authority_ref"], None)
                results=sorted(results, key=lambda x: (x.get("vector_score") is None, -(x.get("vector_score") or -1e9), x["score"]))
    if args.out_json:
        with open(args.out_json,"w",encoding="utf-8") as f: json.dump({"query":args.q,"results":results}, f, indent=2)
    for r in results[: min(len(results), 25)]:
        print(f'{r["authority_ref"]}\tbm25={r["score"]}\tvec={r.get("vector_score")}\t{r["snippet"]}')
if __name__=="__main__":
    main()
