#!/usr/bin/env python3
"""
vehicle_registry_miner_candidate.py (v39) — CANDIDATE ONLY / NON-INTERPRETIVE

Goal: produce *candidate* vehicle registry entries by mining authority text for procedural keywords,
without asserting correctness. This helps populate docs/vehicle_registry_seed_v35.json.

Method:
- Runs repeated FTS queries for procedural patterns (Motion, Appeal, Service, Stipulation, Default, etc.)
- For each query, takes top hits and emits candidate vehicle stubs with:
    vehicle_id (deterministic),
    name (query label),
    keywords (tokenized query),
    primary_authority_query (the query),
    authority_candidates (authority_ref/page/header_lines)

Output JSON:
{
  "vehicles":[ ... ],
  "meta":{...}
}

IMPORTANT: This does not claim legal validity. It only proposes candidates for human validation.
"""
import argparse, json, os, re, sys, subprocess, tempfile, hashlib

DEFAULT_QUERIES=[
  {"id":"Q_MOTION","label":"Motion (generic)","q":"motion"},
  {"id":"Q_APPEAL","label":"Appeal / appellate","q":"appeal OR appellate"},
  {"id":"Q_SERVICE","label":"Service of process","q":"service OR served OR proof of service"},
  {"id":"Q_DEFAULT","label":"Default / set aside","q":"default OR set aside default"},
  {"id":"Q_CONTEMPT","label":"Contempt / show cause","q":"contempt OR show cause"},
  {"id":"Q_DISCOVERY","label":"Discovery","q":"interrogatories OR requests for production OR deposition"},
  {"id":"Q_SANCTIONS","label":"Sanctions","q":"sanctions"},
  {"id":"Q_INJUNCTION","label":"Injunction / TRO","q":"injunction OR temporary restraining"},
  {"id":"Q_RECONSIDER","label":"Reconsideration","q":"reconsideration"},
  {"id":"Q_RECUSAL","label":"Recusal / disqualification","q":"disqualification OR recusal"},
]

def slug(s):
    s=re.sub(r'[^A-Za-z0-9]+','_',s.strip())
    s=re.sub(r'_+','_',s).strip('_')
    return s[:48] if s else "X"

def make_id(label, query):
    h=hashlib.sha256((label+"|"+query).encode("utf-8")).hexdigest()[:10]
    return f"V_{slug(label).upper()}_{h}"

def tokenize(q):
    parts=re.split(r'[^A-Za-z0-9]+', q.lower())
    kws=[p for p in parts if p and p not in {"or","and"}]
    # de-dup preserving order
    seen=set(); out=[]
    for k in kws:
        if k not in seen:
            out.append(k); seen.add(k)
    return out[:12]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--out-json", required=True)
    ap.add_argument("--topk", type=int, default=15)
    ap.add_argument("--fts-search", default=os.path.join("tools","authority_anchor_fts_search.py"))
    ap.add_argument("--queries-json", default="")
    args=ap.parse_args()

    if not os.path.exists(args.db) or os.path.getsize(args.db)==0:
        print("missing FTS db", file=sys.stderr); raise SystemExit(2)
    if not os.path.exists(args.fts_search):
        print("missing fts search tool", file=sys.stderr); raise SystemExit(2)

    queries=DEFAULT_QUERIES
    if args.queries_json:
        queries=json.load(open(args.queries_json,"r",encoding="utf-8"))

    vehicles=[]
    for qobj in queries:
        label=qobj.get("label") or qobj.get("id") or "Vehicle"
        q=qobj.get("q") or ""
        if not q.strip():
            continue
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tf:
            tmp=tf.name
        subprocess.run([sys.executable, args.fts_search, "--db", args.db, "--q", q, "--topk", str(args.topk), "--out-json", tmp], check=True)
        res=json.load(open(tmp,"r",encoding="utf-8"))
        os.remove(tmp)
        vid=make_id(label,q)
        vehicles.append({
            "vehicle_id": vid,
            "name": label,
            "keywords": tokenize(q),
            "primary_authority_query": q,
            "forms": [],
            "confidence":"CANDIDATE_ONLY",
            "authority_candidates":[{
                "authority_ref": h.get("authority_ref"),
                "doc_id": h.get("doc_id"),
                "page": h.get("page"),
                "header_lines": h.get("header_lines"),
                "confidence":"CANDIDATE_ONLY"
            } for h in (res.get("results") or [])]
        })

    out={"vehicles":vehicles,"meta":{"confidence":"CANDIDATE_ONLY","notes":"MINED_FROM_FTS_QUERIES_NON_INTERPRETIVE"}}
    json.dump(out, open(args.out_json,"w",encoding="utf-8"), indent=2, ensure_ascii=False)
    print(f"OK vehicles={len(vehicles)}")

if __name__=="__main__":
    main()
