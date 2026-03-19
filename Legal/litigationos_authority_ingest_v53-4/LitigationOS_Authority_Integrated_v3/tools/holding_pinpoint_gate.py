#!/usr/bin/env python3
import argparse, csv, os, sys

def die(msg, code=2):
    print(msg, file=sys.stderr); raise SystemExit(code)

def load_csv(path):
    with open(path,"r",encoding="utf-8") as f:
        return list(csv.DictReader(f))

def write_csv(path, rows, fields):
    with open(path,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=fields); w.writeheader()
        for r in rows: w.writerow(r)

def has_pinpoint(r):
    for k in ("holding_pinpoint","pinpoint_page","pinpoint_para","pinpoint_line"):
        if (r.get(k) or "").strip():
            return True
    return False

def main():
    ap=argparse.ArgumentParser(description="Holding Pinpoint Gate (structural)")
    ap.add_argument("--in-csv", required=True)
    ap.add_argument("--out-validated-csv", required=True)
    ap.add_argument("--out-fixlist-csv", required=True)
    args=ap.parse_args()

    if not os.path.exists(args.in_csv): die("Input CSV missing")
    rows=load_csv(args.in_csv)

    validated=[]
    fix=[]
    for idx,r in enumerate(rows, start=1):
        reasons=[]
        cit=(r.get("citation") or "").strip()
        if not cit:
            reasons.append("MISSING:citation")
        if not has_pinpoint(r):
            reasons.append("MISSING:holding_pinpoint_any")

        status_promote="PASS" if not reasons else "FAIL"
        rr=dict(r)
        rr["status_promote"]=status_promote
        rr["promote_reasons"]=";".join(reasons)
        validated.append(rr)

        for rs in reasons:
            parts=rs.split(":",1)
            fix.append({"row":idx,"citation":cit,"issue":parts[0],"field":parts[1] if len(parts)>1 else ""})

    if validated:
        fields=list(validated[0].keys())
        write_csv(args.out_validated_csv, validated, fields)
    else:
        write_csv(args.out_validated_csv, [], ["citation","status_promote","promote_reasons"])
    write_csv(args.out_fixlist_csv, fix, ["row","citation","issue","field"])

if __name__=="__main__":
    main()
