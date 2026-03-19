#!/usr/bin/env python3
import argparse, csv, json, os, re, sqlite3, sys

def die(msg, code=2):
    print(msg, file=sys.stderr); raise SystemExit(code)

AR_RE=re.compile(r'^DOC_[0-9a-fA-F]{1,64}:p[0-9]{4}(#[0-9a-fA-F]{1,16})?$')

def load_csv(path):
    with open(path,"r",encoding="utf-8") as f:
        return list(csv.DictReader(f))

def write_csv(path, rows, fieldnames):
    with open(path,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=fieldnames); w.writeheader()
        for r in rows: w.writerow(r)

def connect(db):
    if not db: return None
    if not os.path.exists(db) or os.path.getsize(db)==0:
        die(f"DB not found/empty: {db}")
    con=sqlite3.connect(db); con.row_factory=sqlite3.Row; return con

def authority_ref_exists(con, ref: str) -> bool:
    if con is None: return True
    cur=con.cursor()
    cur.execute("SELECT 1 FROM shards WHERE authority_ref=? LIMIT 1;", (ref,))
    return cur.fetchone() is not None

def main():
    p=argparse.ArgumentParser(description="Validation Gate Engine (v8) - structural only")
    p.add_argument("--candidates", required=True)
    p.add_argument("--rules", required=True)
    p.add_argument("--db", help="Optional authority_store.sqlite to enforce authority_ref presence")
    p.add_argument("--out-validated", required=True)
    p.add_argument("--out-fixlist", required=True)
    args=p.parse_args()

    if not os.path.exists(args.candidates): die("Candidates CSV not found")
    if not os.path.exists(args.rules): die("Rules file not found")
    con=connect(args.db)
    rows=load_csv(args.candidates)
    _rules=json.load(open(args.rules,"r",encoding="utf-8"))

    validated=[]
    fixlist=[]
    for i,r in enumerate(rows, start=1):
        missing=[]
        invalid=[]
        ar=(r.get("authority_ref") or "").strip()

        if not ar:
            missing.append("authority_ref")
        else:
            if not AR_RE.match(ar):
                invalid.append("authority_ref_shape")
            if not authority_ref_exists(con, ar):
                invalid.append("authority_ref_not_in_db")

        if "pinpoint" in r and not (r.get("pinpoint") or "").strip():
            missing.append("pinpoint")

        for fld in ["posture","service","deadline"]:
            if fld in r and not (r.get(fld) or "").strip():
                missing.append(fld)

        if "computed_deadline" in r:
            sc=(r.get("status_calc") or "").strip()
            if (r.get("computed_deadline") or "").strip() and sc not in ("CALCULATED_CANDIDATE","VERIFIED"):
                invalid.append("status_calc")

        if missing or invalid:
            rr=dict(r); rr["status"]="FAIL"; validated.append(rr)
            for m in missing:
                fixlist.append({"row":i,"authority_ref":ar,"issue":"MISSING","field":m})
            for v in invalid:
                fixlist.append({"row":i,"authority_ref":ar,"issue":"INVALID","field":v})
        else:
            rr=dict(r); rr["status"]="VERIFIED"; validated.append(rr)

    write_csv(args.out_validated, validated, list(validated[0].keys()) if validated else [])
    write_csv(args.out_fixlist, fixlist, ["row","authority_ref","issue","field"])

if __name__=="__main__":
    main()
