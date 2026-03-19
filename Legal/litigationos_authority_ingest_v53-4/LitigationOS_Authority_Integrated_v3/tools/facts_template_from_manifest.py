#!/usr/bin/env python3
"""
facts_template_from_manifest.py (v39) — NON-INTERPRETIVE SKELETON GENERATOR

Creates a facts.jsonl template by listing files from a manifest.json (from this bundle),
without inventing any fact text. Each line is a "fact slot" referencing a source file,
with empty text and a placeholder locator field to be filled by the operator.

Output facts are INVALID until operator fills text + locator fields; this is intentional.
"""
import argparse, json, os, sys

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--manifest-json", required=True)
    ap.add_argument("--out-facts-jsonl", required=True)
    ap.add_argument("--max", type=int, default=200)
    args=ap.parse_args()

    m=json.load(open(args.manifest_json,"r",encoding="utf-8"))
    files=(m.get("files") or []) if isinstance(m,dict) else []
    if not isinstance(files, list):
        raise SystemExit(2)

    n=0
    with open(args.out_facts_jsonl,"w",encoding="utf-8") as out:
        for fobj in files:
            if n>=args.max: break
            path=fobj.get("path") or ""
            sha=fobj.get("sha256") or ""
            if not path: 
                continue
            n += 1
            out.write(json.dumps({
                "fact_id": f"F{n:04d}",
                "text": "",
                "pinpoint":{
                    "source_type":"file",
                    "source_path": path,
                    "sha256": sha
                    # locator fields intentionally omitted; validator will FAIL until filled
                },
                "tags":["TEMPLATE_ONLY","PINPOINT_MISSING"]
            }, ensure_ascii=False)+"\n")

    print(f"OK facts_template_lines={n}")

if __name__=="__main__":
    main()
