#!/usr/bin/env python3
import argparse, csv, os, sqlite3, sys
def die(msg, code=2):
    print(msg, file=sys.stderr); raise SystemExit(code)
TRIGGERS=[
    ("CAUSE_OF_ACTION","cause of action"),
    ("ELEMENTS","elements"),
    ("BURDEN","burden of proof"),
    ("STANDARD","standard of review"),
    ("JURISDICTION","jurisdiction"),
    ("VENUE","venue"),
    ("SERVICE","service of process"),
    ("NOTICE","notice"),
    ("DEADLINE_WITHIN","within"),
    ("AFFIRMATIVE_DEFENSE","affirmative defense"),
    ("SANCTIONS","sanctions"),
    ("CONTEMPT","contempt"),
    ("INJUNCTION","injunction"),
    ("TRO","temporary restraining"),
    ("PRELIM_INJ","preliminary injunction"),
    ("EX_PARTE","ex parte"),
    ("APPEAL","appeal"),
    ("MANDAMUS","mandamus"),
    ("PROHIBITION","prohibition"),
    ("SUPERINTENDING_CONTROL","superintending control"),
    ("RECUSAL","disqualification"),
]
def main():
    ap=argparse.ArgumentParser(description="Extract litigation-relevant lexical concept candidates from shards (non-interpretive)")
    ap.add_argument("--db", required=True)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--out-csv", required=True)
    args=ap.parse_args()
    if not os.path.exists(args.db) or os.path.getsize(args.db)==0: die("DB missing/empty")
    con=sqlite3.connect(args.db); con.row_factory=sqlite3.Row; cur=con.cursor()
    q="SELECT authority_ref, text FROM shards"
    if args.limit and args.limit>0:
        q += " LIMIT ?"; cur.execute(q,(args.limit,))
    else:
        cur.execute(q)
    rows=cur.fetchall()
    out=[]; seen=set()
    for r in rows:
        ref=r["authority_ref"]; txt=(r["text"] or ""); low=txt.lower()
        for label, phrase in TRIGGERS:
            idx=low.find(phrase)
            if idx==-1: continue
            start=max(0, idx-80); end=min(len(txt), idx+len(phrase)+160)
            snippet=txt[start:end].replace("\n"," ")
            key=(ref,label,phrase)
            if key in seen: continue
            seen.add(key)
            out.append({"authority_ref":ref,"concept_label":label,"trigger_phrase":phrase,"context_snippet":snippet,"status":"CANDIDATE_ONLY_NO_LEGAL_INFERENCE"})
    with open(args.out_csv,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=["authority_ref","concept_label","trigger_phrase","context_snippet","status"])
        w.writeheader()
        for rr in out: w.writerow(rr)
    con.close()
if __name__=="__main__":
    main()
