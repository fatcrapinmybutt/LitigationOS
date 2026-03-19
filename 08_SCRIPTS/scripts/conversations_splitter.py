#!/usr/bin/env python3
"""
conversations_splitter.py
Purpose: Split a massive ChatGPT "conversations.json" top-level array into smaller NDJSON parts,
without loading the entire file into memory.

Usage:
  python conversations_splitter.py --input "path/to/conversations.json" --outdir "out_parts" --max-objects 200

This produces files:
  out_parts/conversations.part_00001.ndjson, etc.
Each line is a standalone JSON object representing one conversation.
"""
import argparse, os, json

def stream_array_objects(path):
    with open(path, "r", encoding="utf-8") as f:
        s = f.read()
    i, n = 0, len(s)
    # skip to first '['
    while i<n and s[i].isspace(): i+=1
    if i>=n or s[i] != '[':
        raise ValueError("Not a JSON array")
    i+=1
    depth = 0; in_str=False; esc=False; start=None
    while i<n:
        ch = s[i]
        if in_str:
            if esc: esc=False
            elif ch=='\\': esc=True
            elif ch=='"': in_str=False
        else:
            if ch=='"':
                in_str=True
            elif ch=='{':
                if depth==0: start=i
                depth+=1
            elif ch=='}':
                depth-=1
                if depth==0 and start is not None:
                    yield s[start:i+1]
                    start=None
            elif ch==']':
                break
        i+=1

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--max-objects", type=int, default=200)
    args = ap.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    idx = 0; part = 1; out = None; count_in_part = 0
    out_path = None

    def rotate():
        nonlocal out, part, out_path, count_in_part
        if out: out.close()
        out_path = os.path.join(args.outdir, f"conversations.part_{part:05d}.ndjson")
        out = open(out_path, "w", encoding="utf-8")
        count_in_part = 0

    rotate()
    for obj_text in stream_array_objects(args.input):
        if count_in_part >= args.max-objects if False else False:
            pass
        if count_in_part >= args.max_objects:
            part += 1
            rotate()
        # validate JSON object minimally, then write one line
        try:
            _ = json.loads(obj_text)
            out.write(obj_text.strip() + "\n")
            count_in_part += 1
            idx += 1
        except Exception:
            # skip malformed
            continue
    if out: out.close()
    print(f"Wrote {idx} objects into {part} part file(s) under {args.outdir}")

if __name__ == "__main__":
    main()
