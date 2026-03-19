#!/usr/bin/env python3
import argparse, json

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--in-json", required=True)
    ap.add_argument("--out-facts-jsonl", required=True)
    ap.add_argument("--max", type=int, default=500)
    args=ap.parse_args()

    payload=json.load(open(args.in_json,"r",encoding="utf-8"))
    items=payload.get("items") or []
    n=0
    with open(args.out_facts_jsonl,"w",encoding="utf-8") as out:
        for it in items:
            if n>=args.max: break
            sp=(it.get("source_path") or "").strip()
            st=(it.get("source_type") or "other").strip()
            if not sp:
                continue
            n+=1
            out.write(json.dumps({
                "fact_id": f"EI{n:04d}",
                "text":"",
                "pinpoint":{"source_type":st,"source_path":sp},
                "tags":["TEMPLATE_ONLY","PINPOINT_MISSING"],
                "notes":"FILL_TEXT_AND_LOCATOR_FIELDS"
            }, ensure_ascii=False)+"\n")
    print("OK skeleton_facts=", n)

if __name__=="__main__":
    main()
