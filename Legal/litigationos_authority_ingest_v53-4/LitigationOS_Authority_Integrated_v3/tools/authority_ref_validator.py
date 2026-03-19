#!/usr/bin/env python3
import argparse, json, csv, os, re, sqlite3, sys
REF1=re.compile(r'^(?P<doc>.+?)(::|:)\s*p?(?P<page>\d+)\s*$', re.IGNORECASE)

def parse_ref(x):
    if isinstance(x, dict):
        d=(x.get("doc_id") or "").strip()
        p=x.get("page")
        if d and isinstance(p,int): return d, p
        return "", None
    s=(x or "").strip()
    if not s: return "", None
    m=REF1.match(s)
    if m:
        return m.group("doc").strip(), int(m.group("page"))
    return "", None

def read_jsonl(path):
    with open(path,"r",encoding="utf-8") as f:
        for ln in f:
            ln=ln.strip()
            if ln: yield json.loads(ln)

def shard_exists(cur, doc_id, page):
    for q in [
        "SELECT 1 FROM shards WHERE doc_id=? AND page=? LIMIT 1",
        "SELECT 1 FROM shards WHERE doc_id=? AND page_no=? LIMIT 1",
        "SELECT 1 FROM shards WHERE document_id=? AND page=? LIMIT 1"
    ]:
        try:
            cur.execute(q, (doc_id, page))
            if cur.fetchone(): return True
        except sqlite3.OperationalError:
            continue
    return False

def main():
    ap=argparse.ArgumentParser(description="Authority Ref Validator v27")
    ap.add_argument("--authority-store", required=True)
    ap.add_argument("--in-jsonl", required=True)
    ap.add_argument("--mode", choices=["propositions","claim_packet"], required=True)
    ap.add_argument("--out-json", required=True)
    ap.add_argument("--out-csv", required=True)
    args=ap.parse_args()

    if not os.path.exists(args.authority_store) or os.path.getsize(args.authority_store)==0:
        print("missing authority store", file=sys.stderr); raise SystemExit(2)
    if not os.path.exists(args.in_jsonl) or os.path.getsize(args.in_jsonl)==0:
        print("missing/empty input jsonl", file=sys.stderr); raise SystemExit(2)

    con=sqlite3.connect(args.authority_store)
    cur=con.cursor()

    refs=set()
    if args.mode=="propositions":
        for row in read_jsonl(args.in_jsonl):
            r=row.get("authority_ref") or row.get("authorityRef") or ""
            doc,page=parse_ref(r)
            if doc and page is not None:
                refs.add((doc,page))
    else:
        pkt=None
        for row in read_jsonl(args.in_jsonl):
            pkt=row; break
        if not pkt:
            print("no rows", file=sys.stderr); raise SystemExit(2)
        for pr in (pkt.get("authority_propositions") or []):
            r=pr.get("authority_ref") or ""
            doc,page=parse_ref(r)
            if doc and page is not None:
                refs.add((doc,page))

    missing=[]
    for doc,page in sorted(refs):
        if not shard_exists(cur, doc, page):
            missing.append({"doc_id":doc,"page":page,"authority_ref":f"{doc}::p{page}"})
    con.close()

    status="PASS" if len(missing)==0 else "FAIL"
    rep={"status":status,"checked_refs":len(refs),"missing_refs":len(missing)}
    json.dump(rep, open(args.out_json,"w",encoding="utf-8"), indent=2)

    with open(args.out_csv,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=["authority_ref","doc_id","page"])
        w.writeheader()
        for r in missing: w.writerow(r)

    print(f"OK {status} checked={len(refs)} missing={len(missing)}")
    if status=="FAIL":
        raise SystemExit(2)

if __name__=="__main__":
    main()
