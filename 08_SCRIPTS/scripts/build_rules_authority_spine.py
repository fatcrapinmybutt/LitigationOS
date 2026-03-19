#!/usr/bin/env python3
"""
build_rules_authority_spine.py

Builds an Authority Spine for Michigan Court Rules (MCR) from rules_extracted.csv/json.

Inputs (default relative to current working directory):
  - rules_extracted.csv
  - rules_extracted.json (optional; used for hashing/provenance)
  - LEXOS2-Rules.pdf (optional; kept for provenance; MCR pinpoint is the rule/subrule itself)

Outputs:
  - rules_authority_index.json
  - rules_authority_index.csv
  - rules_authority_shards.jsonl

Design note:
  For MCR, the canonical pinpoint is the rule/subrule citation (e.g., "MCR 2.003(C)(1)").
  Page pinpoints are not required for the rule itself in Michigan practice, but you can attach
  PDF page pinpoints later if you want an additional cross-reference.
"""
from __future__ import annotations
import argparse, os, json, hashlib, datetime
import pandas as pd

def sha256_file(p: str) -> str:
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for chunk in iter(lambda:f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()

def norm_ws(s: str) -> str:
    return " ".join(str(s).split())

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--csv", default="rules_extracted.csv", help="Path to rules_extracted.csv")
    ap.add_argument("--json", default="rules_extracted.json", help="Path to rules_extracted.json (optional)")
    ap.add_argument("--pdf", default="LEXOS2-Rules.pdf", help="Path to LEXOS2-Rules.pdf (optional)")
    ap.add_argument("--outdir", default=".", help="Output directory")
    args=ap.parse_args()

    if not os.path.exists(args.csv):
        raise SystemExit(f"Missing CSV: {args.csv}")

    df=pd.read_csv(args.csv)
    df["rule"]=df["rule"].astype(str).str.strip()
    df["context"]=df["context"].astype(str).map(norm_ws)

    agg=(df.groupby(["rule","chapter","source_doc"], dropna=False)
            .agg(context_count=("context","size"),
                 contexts=("context", lambda x: list(dict.fromkeys(x.tolist()))))
            .reset_index()
            .sort_values(["chapter","rule"])
            .reset_index(drop=True))
    agg["authority_id"]=[f"MCR::{r}" for r in agg["rule"]]

    shards=[]
    for _,row in agg.iterrows():
        for ctx in row["contexts"]:
            shards.append({
                "authority_id": row["authority_id"],
                "authority_type": "MCR",
                "citation": row["rule"],
                "pinpoint": row["rule"],
                "chapter": int(row["chapter"]) if pd.notna(row["chapter"]) else None,
                "context_excerpt": ctx,
                "source_doc": row["source_doc"],
            })

    os.makedirs(args.outdir, exist_ok=True)
    out_json=os.path.join(args.outdir, "rules_authority_index.json")
    out_csv=os.path.join(args.outdir, "rules_authority_index.csv")
    out_jsonl=os.path.join(args.outdir, "rules_authority_shards.jsonl")

    meta={
        "generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "record_count": int(len(agg)),
        "source_sha256": {
            os.path.basename(args.csv): sha256_file(args.csv),
            **({os.path.basename(args.json): sha256_file(args.json)} if os.path.exists(args.json) else {}),
            **({os.path.basename(args.pdf): sha256_file(args.pdf)} if os.path.exists(args.pdf) else {}),
        },
        "records": agg.drop(columns=["contexts"]).to_dict(orient="records")
    }
    with open(out_json,"w",encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    agg.drop(columns=["contexts"]).to_csv(out_csv, index=False)
    with open(out_jsonl,"w",encoding="utf-8") as f:
        for o in shards:
            f.write(json.dumps(o, ensure_ascii=False)+"\n")

    print("Wrote:", out_json)
    print("Wrote:", out_csv)
    print("Wrote:", out_jsonl)

if __name__=="__main__":
    main()
