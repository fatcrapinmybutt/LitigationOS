#!/usr/bin/env python3
import argparse, csv, hashlib, os

def stable_id(prefix, *parts):
    h=hashlib.sha256(("|".join([prefix]+[p or "" for p in parts])).encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{h}"

def load_csv(path):
    with open(path,"r",encoding="utf-8") as f:
        return list(csv.DictReader(f))

def write_csv(path, rows, fields):
    with open(path,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=fields); w.writeheader()
        for r in rows:
            # drop unknown keys deterministically
            w.writerow({k: r.get(k,"") for k in fields})

def main():
    ap=argparse.ArgumentParser(description="Export candidate tables to Neo4j-style CSVs")
    ap.add_argument("--docket-events-csv")
    ap.add_argument("--caselaw-governed-csv")
    ap.add_argument("--claim-vehicle-routes-csv")
    ap.add_argument("--out-dir", required=True)
    args=ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)

    nodes=[]
    edges=[]

    if args.docket_events_csv and os.path.exists(args.docket_events_csv):
        for r in load_csv(args.docket_events_csv):
            nid=stable_id("DocketEvent", r.get("event_date",""), r.get("kind",""), (r.get("docket_text","") or "")[:120], r.get("file_path",""))
            nodes.append({"id":nid,"label":"DocketEvent","event_date":r.get("event_date",""),"kind":r.get("kind",""),"text":r.get("docket_text",""),"status":"CANDIDATE"})

    if args.caselaw_governed_csv and os.path.exists(args.caselaw_governed_csv):
        for r in load_csv(args.caselaw_governed_csv):
            nid=stable_id("CaselawCitation", r.get("citation",""))
            nodes.append({"id":nid,"label":"CaselawCitation","citation":r.get("citation",""),"court_level":r.get("court_level_candidate",""),"pub_status":r.get("publication_status_candidate",""),"reporter":r.get("reporter_candidate",""),"status":"CANDIDATE"})

    if args.claim_vehicle_routes_csv and os.path.exists(args.claim_vehicle_routes_csv):
        for r in load_csv(args.claim_vehicle_routes_csv):
            ar=r.get("authority_ref","")
            rid=stable_id("Route", r.get("element_token_candidate",""), r.get("form_candidate",""), r.get("rule_candidate_token",""), ar)
            nodes.append({"id":rid,"label":"CandidateRoute","authority_ref":ar,"element_token":r.get("element_token_candidate",""),"form_candidate":r.get("form_candidate",""),"rule_candidate":r.get("rule_candidate_token",""),"status":"CANDIDATE"})
            aid=stable_id("AuthorityRef", ar)
            nodes.append({"id":aid,"label":"AuthorityRef","authority_ref":ar,"status":"CANDIDATE"})
            edges.append({"source":rid,"target":aid,"type":"POINTS_TO_AUTHORITY_REF","status":"CANDIDATE"})

    # Dedup nodes by id
    uniq={}
    for n in nodes:
        uniq[n["id"]]=n
    nodes=list(uniq.values())

    node_fields=sorted({k for n in nodes for k in n.keys()}) if nodes else ["id"]
    write_csv(os.path.join(args.out_dir,"nodes_candidates.csv"), nodes, node_fields)
    write_csv(os.path.join(args.out_dir,"edges_candidates.csv"), edges, ["source","target","type","status"])

if __name__=="__main__":
    main()
