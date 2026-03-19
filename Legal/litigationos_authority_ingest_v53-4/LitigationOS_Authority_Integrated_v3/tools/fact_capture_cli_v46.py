#!/usr/bin/env python3
"""
fact_capture_cli_v46.py — NON-INTERPRETIVE FACT ENTRY HELPER

Goal: reduce friction for creating pinpointed facts.jsonl without inventing content.
This tool appends operator-entered facts into outputs/facts.jsonl.

It does NOT:
- parse PDFs
- infer page/line
- invent text

It DOES:
- enforce required fields are present (text + source_path + locator hint)
- standardize a minimal pinpoint object
- optionally run facts_pinpoint_validate.py if present

Usage:
  python tools/fact_capture_cli_v46.py --facts-jsonl outputs/facts.jsonl --run-validate --manifest-json manifest.json
"""
import argparse, json, os, sys, datetime, subprocess

def prompt(label, required=True):
    while True:
        v=input(label).strip()
        if v or not required:
            return v
        print("Required.")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--facts-jsonl", default="outputs/facts.jsonl")
    ap.add_argument("--manifest-json", default="manifest.json")
    ap.add_argument("--run-validate", action="store_true")
    args=ap.parse_args()

    os.makedirs(os.path.dirname(args.facts_jsonl) or ".", exist_ok=True)
    fact_id=f"F{int(datetime.datetime.utcnow().timestamp())}"
    print("Enter a single fact (no law, no argument).")
    text=prompt("Fact text: ")
    source_path=prompt("Source path (provenance): ")
    source_type=prompt("Source type [pdf/image/audio/video/text/other]: ", required=False) or "other"
    locator=prompt("Locator (page/line, timestamp, Bates, etc.): ")
    notes=prompt("Notes (optional): ", required=False)

    obj={
      "fact_id": fact_id,
      "text": text,
      "pinpoint":{
        "source_type": source_type,
        "source_path": source_path,
        "locator": locator
      },
      "tags":["OPERATOR_ENTERED"],
      "notes": notes
    }

    with open(args.facts_jsonl,"a",encoding="utf-8") as out:
        out.write(json.dumps(obj, ensure_ascii=False)+"\n")
    print("OK appended", fact_id, "->", args.facts_jsonl)

    if args.run_validate:
        vp=os.path.join(os.path.dirname(os.path.abspath(__file__)),"facts_pinpoint_validate.py")
        if os.path.exists(vp) and os.path.exists(args.manifest_json):
            print("Running validator...")
            subprocess.run([sys.executable, vp, "--facts-jsonl", args.facts_jsonl, "--manifest-json", args.manifest_json,
                            "--out-json", os.path.join(os.path.dirname(args.facts_jsonl) or ".", "facts_validation.json")],
                           check=False)
        else:
            print("Validator not available or manifest missing; skipped.")

if __name__=="__main__":
    main()
