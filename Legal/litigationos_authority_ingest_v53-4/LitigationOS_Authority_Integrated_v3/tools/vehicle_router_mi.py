#!/usr/bin/env python3
"""
Vehicle Router (MI, forms-first) - candidate-only, table-driven.
- Does NOT invent vehicles or standards.
- Reads a vehicle_catalog.csv if present (user-populated).
- If missing, emits fixlist and a minimal 'available_forms' list derived from extracted SCAO form tokens.
Inputs:
  --relief-json : structured relief request
  --anchors-csv : authority_anchors.csv (for discovered form tokens)
Outputs:
  vehicle_map_candidates.json  (always produced)
  fixlist_vehicle_blockers.csv (produced if missing catalog or match failures)
"""
import argparse, csv, json, os, sys, re

def die(msg, code=2):
    print(msg, file=sys.stderr); raise SystemExit(code)

def load_csv(path):
    with open(path,"r",encoding="utf-8") as f:
        return list(csv.DictReader(f))

def write_csv(path, rows, fields):
    with open(path,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=fields); w.writeheader()
        for r in rows: w.writerow(r)

def norm(s): return re.sub(r'\s+',' ',(s or '').strip().lower())

def main():
    ap=argparse.ArgumentParser(description="MI Vehicle Router (candidate-only, forms-first, non-interpretive).")
    ap.add_argument("--relief-json", required=True)
    ap.add_argument("--anchors-csv", required=True)
    ap.add_argument("--vehicle-catalog-csv", default="")
    ap.add_argument("--out-vehicle-map-json", required=True)
    ap.add_argument("--out-fixlist-csv", required=True)
    args=ap.parse_args()

    if not os.path.exists(args.relief_json): die("relief json missing")
    if not os.path.exists(args.anchors_csv): die("anchors csv missing")

    relief=json.load(open(args.relief_json,"r",encoding="utf-8"))
    relief_text=norm(relief.get("relief",""))

    anchors=load_csv(args.anchors_csv)
    # discover form tokens (non-interpretive)
    forms=sorted(set(a["anchor_token"].strip() for a in anchors if a.get("anchor_kind")=="SCAO_FORM" and a.get("anchor_token")))

    fix=[]
    candidates=[]

    if not args.vehicle_catalog_csv or not os.path.exists(args.vehicle_catalog_csv):
        fix.append({"blocker":"VEHICLE_CATALOG_MISSING","detail":"Provide vehicle_catalog.csv (table-driven) to enable routing beyond 'available_forms'.","status":"FAIL"})
        out={
            "relief_request": relief,
            "routing_status": "CANDIDATE_ONLY_NO_ROUTE_NO_CATALOG",
            "available_forms_discovered": forms,
            "vehicle_candidates": [],
            "prereq_checklist": [],
            "notes": "No catalog present; system will not invent vehicles. Populate vehicle_catalog.csv to enable deterministic routing."
        }
        write_csv(args.out_fixlist_csv, fix, ["blocker","detail","status"])
        json.dump(out, open(args.out_vehicle_map_json,"w",encoding="utf-8"), indent=2)
        print("OK vehicle_map=CANDIDATE_ONLY (catalog missing)")
        return

    cat=load_csv(args.vehicle_catalog_csv)
    # Expected columns: relief_keywords, vehicle_name, form_token, rule_anchor_token, prereqs
    for row in cat:
        kws=norm(row.get("relief_keywords",""))
        if not kws: 
            continue
        # match if any keyword present
        match=False
        for k in [x.strip() for x in kws.split("|") if x.strip()]:
            if k and k in relief_text:
                match=True; break
        if not match:
            continue
        candidates.append({
            "vehicle_name": row.get("vehicle_name",""),
            "form_token": row.get("form_token",""),
            "rule_anchor_token": row.get("rule_anchor_token",""),
            "prereqs": row.get("prereqs",""),
            "status": "CANDIDATE_ONLY_TABLE_MATCH"
        })

    if not candidates:
        fix.append({"blocker":"NO_VEHICLE_MATCH","detail":"Catalog present but no match for relief text; expand relief_keywords in vehicle_catalog.csv.","status":"FAIL"})
        routing_status="CANDIDATE_ONLY_NO_MATCH"
    else:
        routing_status="CANDIDATE_ONLY_MATCHED"

    out={
        "relief_request": relief,
        "routing_status": routing_status,
        "available_forms_discovered": forms,
        "vehicle_candidates": candidates,
        "prereq_checklist": [],
        "notes": "Candidate-only routing. No legal standards asserted; downstream Claim Compiler must PASS gates."
    }
    write_csv(args.out_fixlist_csv, fix, ["blocker","detail","status"])
    json.dump(out, open(args.out_vehicle_map_json,"w",encoding="utf-8"), indent=2)
    print(f"OK vehicle_candidates={len(candidates)} status={routing_status}")

if __name__=="__main__":
    main()
