#!/usr/bin/env python3
"""
templates_seed_intents_props_v43.py (v43) — NON-INTERPRETIVE TEMPLATE SEEDER

Creates minimal valid JSON templates for:
- outputs/intents.json
- outputs/propositions.json

No legal content is generated; placeholders remain empty.
"""
import argparse, json, os

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out-dir", default="outputs")
    args=ap.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)

    intents={"intents":[{"id":"R1","text":"","track":"","relief_requested":"","notes":"FILL_ME"}]}
    props={"items":[{"id":"P1","proposition":"","query":"","notes":"FILL_ME"}]}

    with open(os.path.join(args.out_dir,"intents.json"),"w",encoding="utf-8") as f:
        json.dump(intents,f,indent=2,ensure_ascii=False)
    with open(os.path.join(args.out_dir,"propositions.json"),"w",encoding="utf-8") as f:
        json.dump(props,f,indent=2,ensure_ascii=False)

    print("OK wrote intents.json + propositions.json (templates)")

if __name__=="__main__":
    main()
