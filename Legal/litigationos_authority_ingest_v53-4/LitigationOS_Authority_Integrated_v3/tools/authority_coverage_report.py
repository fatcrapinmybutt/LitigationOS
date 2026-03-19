#!/usr/bin/env python3
import argparse, json, csv, os, re, sqlite3, sys
REF1=re.compile(r'^(?P<doc>.+?)(::|:)\s*p?(?P<page>\d+)\s*$', re.IGNORECASE)

def parse_ref(s):
    s=(s or "").strip()
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

def get_doc_page_counts(cur):
    for q in [
        "SELECT doc_id, COUNT(*) FROM shards GROUP BY doc_id",
        "SELECT document_id as doc_id, COUNT(*) FROM shards GROUP BY document_id"
    ]:
        try:
            cur.execute(q)
            return {row[0]: int(row[1]) for row in cur.fetchall()}
        except sqlite3.OperationalError:
            continue
    return {}

def main():
    ap=argparse.ArgumentParser(description="Authority Coverage Report v27")
    ap.add_argument("--authority-store", required=True)
    ap.add_argument("--propositions-jsonl", default="")
    ap.add_argument("--claim-packets-jsonl", default="")
    ap.add_argument("--out-csv", required=True)
    ap.add_argument("--out-json", required=True)
    args=ap.parse_args()

    if not os.path.exists(args.authority_store) or os.path.getsize(args.authority_store)==0:
        print("missing authority store", file=sys.stderr); raise SystemExit(2)

    con=sqlite3.connect(args.authority_store)
    cur=con.cursor()
    doc_pages=get_doc_page_counts(cur)
    con.close()

    refs={}  # (doc,page)->set(sources)
    if args.propositions_jsonl and os.path.exists(args.propositions_jsonl) and os.path.getsize(args.propositions_jsonl)>0:
        for row in read_jsonl(args.propositions_jsonl):
            doc,page=parse_ref(row.get("authority_ref") or "")
            if doc and page is not None:
                refs.setdefault((doc,page), set()).add("propositions")
    if args.claim_packets_jsonl and os.path.exists(args.claim_packets_jsonl) and os.path.getsize(args.claim_packets_jsonl)>0:
        pkt=None
        for row in read_jsonl(args.claim_packets_jsonl):
            pkt=row; break
        if pkt:
            for pr in (pkt.get("authority_propositions") or []):
                doc,page=parse_ref(pr.get("authority_ref") or "")
                if doc and page is not None:
                    refs.setdefault((doc,page), set()).add("claim_packet")

    with open(args.out_csv,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=["doc_id","page","authority_ref","referenced_by"])
        w.writeheader()
        for (doc,page),srcs in sorted(refs.items()):
            w.writerow({"doc_id":doc,"page":page,"authority_ref":f"{doc}::p{page}","referenced_by":";".join(sorted(srcs))})

    by_doc={}
    for (doc,page),srcs in refs.items():
        by_doc.setdefault(doc, {"referenced_pages":0})
        by_doc[doc]["referenced_pages"] += 1

    summary=[]
    for doc,total in doc_pages.items():
        rp=by_doc.get(doc,{}).get("referenced_pages",0)
        summary.append({"doc_id":doc,"total_pages":total,"referenced_pages":rp,"unreferenced_pages":max(0,total-rp)})
    summary=sorted(summary, key=lambda x: (-x["referenced_pages"], x["doc_id"]))

    rep={"docs":summary,"totals":{
        "doc_count":len(summary),
        "total_pages":sum(x["total_pages"] for x in summary),
        "referenced_pages":sum(x["referenced_pages"] for x in summary)
    }}
    json.dump(rep, open(args.out_json,"w",encoding="utf-8"), indent=2)
    print(f"OK docs={rep['totals']['doc_count']} referenced_pages={rep['totals']['referenced_pages']}")

if __name__=="__main__":
    main()
