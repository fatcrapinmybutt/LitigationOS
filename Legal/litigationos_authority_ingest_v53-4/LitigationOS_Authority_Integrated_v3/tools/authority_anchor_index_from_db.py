#!/usr/bin/env python3
"""
Authority Anchor Index Builder v29 (NON-INTERPRETIVE)

Builds a thin retrieval layer over authority_store.sqlite shards:
For each page shard:
- stable authority_ref = doc_id::p{page}
- anchors extracted via regex: MCR, MCL, MRE, MJI, Canon, rule numbers, section tokens
- header_lines: minimal direct-extraction lines from the top of the page text (no rewriting)

Outputs:
--out-jsonl : one row per page
--out-json  : summary stats

This module never summarizes or rewrites authority content.
"""
import argparse, json, os, re, sqlite3, sys

RXES=[
    ("MCR", re.compile(r"\bMCR\s+\d+(?:\.\d+)?(?:\([A-Za-z0-9]+\))*", re.IGNORECASE)),
    ("MCL", re.compile(r"\bMCL\s+\d+(?:\.\d+)?[A-Za-z]*", re.IGNORECASE)),
    ("MRE", re.compile(r"\bMRE\s+\d{2,3}\b", re.IGNORECASE)),
    ("MJI", re.compile(r"\bMJI\s+\d+(?:\.\d+)?", re.IGNORECASE)),
    ("CANON", re.compile(r"\bCanon\s+\d+(?:\.\d+)?", re.IGNORECASE)),
    ("RULE_NUM", re.compile(r"\b\d+(?:\.\d+){1,3}\b")),
    ("SECTION", re.compile(r"\b(?:sec\.|section)\s+\d+(?:\.\d+)?\b", re.IGNORECASE)),
]

def iter_shards(con):
    cur=con.cursor()
    # attempt schema variants
    for q in [
        "SELECT doc_id, page, text FROM shards",
        "SELECT doc_id, page_no as page, text FROM shards",
        "SELECT document_id as doc_id, page, text FROM shards"
    ]:
        try:
            cur.execute(q)
            for doc_id,page,text in cur.fetchall():
                yield str(doc_id), int(page), (text or "")
            return
        except sqlite3.OperationalError:
            continue
    raise RuntimeError("Unsupported shards schema")

def header_lines(text, max_lines=6, max_chars=600):
    lines=[]
    for ln in (text or "").splitlines():
        s=ln.strip()
        if not s: 
            continue
        # stop if we already got enough
        lines.append(s)
        if len(lines)>=max_lines:
            break
    blob=" | ".join(lines)[:max_chars]
    return blob

def anchors(text, max_each=25):
    found=[]
    for tag,rx in RXES:
        for m in rx.finditer(text or ""):
            tok=m.group(0).strip()
            if tok:
                found.append((tag,tok))
    # de-dupe while preserving order
    seen=set()
    out=[]
    for tag,tok in found:
        key=(tag,tok.lower())
        if key in seen: 
            continue
        seen.add(key)
        out.append({"tag":tag,"token":tok})
        # cap
        if len(out)>=max_each*len(RXES):
            break
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--out-jsonl", required=True)
    ap.add_argument("--out-json", required=True)
    args=ap.parse_args()

    if not os.path.exists(args.db) or os.path.getsize(args.db)==0:
        print("missing db", file=sys.stderr); raise SystemExit(2)

    con=sqlite3.connect(args.db)
    n=0
    n_anchors=0
    docs=set()
    with open(args.out_jsonl,"w",encoding="utf-8") as out:
        for doc_id,page,text in iter_shards(con):
            n+=1
            docs.add(doc_id)
            row={
                "authority_ref": f"{doc_id}::p{page}",
                "doc_id": doc_id,
                "page": page,
                "anchors": anchors(text),
                "header_lines": header_lines(text)
            }
            n_anchors += len(row["anchors"])
            out.write(json.dumps(row, ensure_ascii=False) + "\n")
    con.close()

    rep={"pages":n,"docs":len(docs),"anchors_total":n_anchors,"anchors_avg_per_page": (n_anchors/n if n else 0.0)}
    json.dump(rep, open(args.out_json,"w",encoding="utf-8"), indent=2)
    print(f"OK pages={n} docs={len(docs)} anchors_total={n_anchors}")

if __name__=="__main__":
    main()
