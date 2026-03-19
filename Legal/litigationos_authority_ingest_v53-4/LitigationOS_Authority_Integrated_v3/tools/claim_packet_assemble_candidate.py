#!/usr/bin/env python3
import argparse, json, os, hashlib

def sha256_file(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for chunk in iter(lambda:f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()

def read_jsonl(p):
    rows=[]
    with open(p,"r",encoding="utf-8") as f:
        for ln in f:
            ln=ln.strip()
            if ln:
                rows.append(json.loads(ln))
    return rows

def load_optional(p, kind):
    if not p: return None
    if not os.path.exists(p) or os.path.getsize(p)==0: return None
    if kind=="json": return json.load(open(p,"r",encoding="utf-8"))
    if kind=="jsonl": return read_jsonl(p)
    return None

def add_file(man, label, path):
    if path and os.path.exists(path) and os.path.getsize(path)>0:
        man.append({"label":label,"path":path,"size_bytes":os.path.getsize(path),"sha256":sha256_file(path)})

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--facts-jsonl", default="")
    ap.add_argument("--facts-validation-json", default="")
    ap.add_argument("--vehicle-json", default="")
    ap.add_argument("--triples-jsonl", default="")
    ap.add_argument("--deadlines-json", default="")
    ap.add_argument("--out-json", required=True)
    ap.add_argument("--out-manifest-json", required=True)
    args=ap.parse_args()

    packet={
      "meta":{"confidence":"CANDIDATE_ONLY","notes":"PACKAGING_ONLY_NO_CLAIM_ASSERTIONS"},
      "facts": load_optional(args.facts_jsonl,"jsonl") or [],
      "facts_validation": load_optional(args.facts_validation_json,"json") or {},
      "vehicle": load_optional(args.vehicle_json,"json") or {},
      "authority_triples": load_optional(args.triples_jsonl,"jsonl") or [],
      "deadlines": load_optional(args.deadlines_json,"json") or {}
    }
    json.dump(packet, open(args.out_json,"w",encoding="utf-8"), indent=2, ensure_ascii=False)

    man=[]
    add_file(man,"facts_jsonl",args.facts_jsonl)
    add_file(man,"facts_validation_json",args.facts_validation_json)
    add_file(man,"vehicle_json",args.vehicle_json)
    add_file(man,"triples_jsonl",args.triples_jsonl)
    add_file(man,"deadlines_json",args.deadlines_json)
    add_file(man,"packet_json",args.out_json)
    json.dump({"files":man}, open(args.out_manifest_json,"w",encoding="utf-8"), indent=2)
    print(f"OK packet_facts={len(packet['facts'])} triples={len(packet['authority_triples'])}")

if __name__=="__main__":
    main()
