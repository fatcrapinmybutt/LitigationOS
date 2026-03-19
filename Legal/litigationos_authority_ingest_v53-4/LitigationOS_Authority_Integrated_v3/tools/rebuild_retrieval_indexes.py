#!/usr/bin/env python3
"""
Rebuild Retrieval Indexes v30
Regenerates:
- authority_anchor_index_v29.jsonl + summary (from authority_store.sqlite)
- authority_anchor_fts.sqlite (from anchor index)
"""
import argparse, os, subprocess, sys, time

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--authority-store", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--tools-dir", default="tools")
    args=ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    anchor_py=os.path.join(args.tools_dir, "authority_anchor_index_from_db.py")
    fts_py=os.path.join(args.tools_dir, "authority_anchor_fts_build.py")
    if not os.path.exists(anchor_py) or not os.path.exists(fts_py):
        print("missing required tools", file=sys.stderr); raise SystemExit(2)

    idx_jsonl=os.path.join(args.out_dir, "authority_anchor_index_v29.jsonl")
    idx_sum=os.path.join(args.out_dir, "authority_anchor_index_summary_v29.json")
    fts_db=os.path.join(args.out_dir, "authority_anchor_fts.sqlite")

    t0=time.time()
    subprocess.run([sys.executable, anchor_py, "--db", args.authority_store, "--out-jsonl", idx_jsonl, "--out-json", idx_sum], check=True)
    subprocess.run([sys.executable, fts_py, "--index-jsonl", idx_jsonl, "--out-sqlite", fts_db], check=True)
    dt=time.time()-t0
    print(f"OK rebuilt seconds={dt:.2f} idx_jsonl={idx_jsonl} fts_db={fts_db}")

if __name__=="__main__":
    main()
