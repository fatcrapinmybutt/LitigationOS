#!/usr/bin/env python3
"""
Vehicle Candidates Harvester (non-interpretive)
"""
import argparse, csv, json, os, sqlite3, sys, re

def die(msg, code=2):
    print(msg, file=sys.stderr); raise SystemExit(code)

def connect(db):
    if not os.path.exists(db) or os.path.getsize(db)==0:
        die(f"DB not found/empty: {db}")
    con=sqlite3.connect(db); con.row_factory=sqlite3.Row; return con

def fts_match(q: str) -> str:
    q=q.strip()
    q=q.replace('"','""')
    if any(c.isspace() for c in q):
        return f'"{q}"'
    return q

def run_query(con, q, k):
    match=fts_match(q)
    cur=con.cursor()
    cur.execute("""
      SELECT s.authority_ref, snippet(shards_fts, 3, '[', ']', '…', 10) AS snippet
      FROM shards_fts
      JOIN shards s ON s.authority_ref = shards_fts.authority_ref
      WHERE shards_fts MATCH ?
      LIMIT ?;
    """,(match,k))
    return [dict(r) for r in cur.fetchall()]

RULE_RE=re.compile(r'\b(MCR|MCL|MRE)\s+([0-9]{1,4}\.[0-9]{1,4}|[0-9]{3}(?:\.[0-9]+)?)\b')
FORM_RE=re.compile(r'\b(MC|FOC)\s*([0-9]{2,4})\b|\bSCAO\b', re.IGNORECASE)

def extract_rule_tokens(text: str):
    out=set()
    for m in RULE_RE.finditer(text or ""):
        out.add(f"{m.group(1)} {m.group(2)}")
    return sorted(out)

def extract_form_tokens(text: str):
    out=set()
    for m in FORM_RE.finditer(text or ""):
        out.add(m.group(0).strip())
    return sorted(out)

def main():
    p=argparse.ArgumentParser(description="Vehicle Candidates Harvester (non-interpretive)")
    p.add_argument("--db", required=True)
    p.add_argument("--lens", required=True)
    p.add_argument("--k", type=int, default=10)
    p.add_argument("--out", required=True)
    args=p.parse_args()

    lens=json.load(open(args.lens,"r",encoding="utf-8"))
    tokens=list(lens.get("tokens") or [])
    con=connect(args.db)

    rows=[]
    for t in tokens:
        for h in run_query(con, t, args.k):
            sn=h.get("snippet","")
            rows.append({
                "relief_goal":"",
                "vehicle_name_candidate":"",
                "form_candidate":"; ".join(extract_form_tokens(sn)),
                "rule_candidate_token":"; ".join(extract_rule_tokens(sn)),
                "authority_ref": h.get("authority_ref",""),
                "snippet": sn,
                "status":"CANDIDATE"
            })

    cols=["relief_goal","vehicle_name_candidate","form_candidate","rule_candidate_token","authority_ref","snippet","status"]
    with open(args.out,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=cols); w.writeheader()
        for r in rows: w.writerow(r)

if __name__=="__main__":
    main()
