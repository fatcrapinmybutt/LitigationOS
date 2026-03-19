#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Authority Snapshot Builder (MI-only; local/operator-supplied sources only)

Config keys (config/config.json):
{
  "authority_snapshot": {
     "snapshot_id": "MI_AUTH_YYYYMMDD",
     "effective_date": "YYYY-MM-DD",
     "paths": ["F:/Authorities/MCR.pdf", "..."]
  }
}

Outputs:
- config/authority_snapshot_index.json (typed AuthorityRef rows + pinpoints)
- RUN_*/db/AuthorityDB.jsonl (authority chunks w/ pinpoints)
"""
import json, re, hashlib, datetime
from pathlib import Path
from typing import Dict, Any, List, Iterable, Optional
import orjson

try:
    import fitz  # PyMuPDF
except Exception:
    fitz = None

def now_iso():
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat()+"Z"

def sha1(s:str)->str:
    h=hashlib.sha1(); h.update(s.encode("utf-8","ignore")); return h.hexdigest()

def mk_pinpoint(path:str,page:int=None,line:int=None):
    return {"path":path,"page":page,"line":line,"para_anchor":None,"bbox":None,"timecode":None,"bates":None}

CITE_RX = re.compile(r'\b(MCR|MCL|MRE)\s*\d+(\.\d+)*([A-Za-z]?\(?[0-9A-Za-z]+\)?)?')
AO_RX = re.compile(r'\bAO\s*\d{4}-\d+\b', re.IGNORECASE)

TYPE_HINTS=[
    ("michigan court rules","MCR"),
    ("michigan compiled laws","MCL"),
    ("michigan rules of evidence","MRE"),
    ("administrative order","MSC_ADMIN_ORDER"),
    ("benchbook","MI_BENCHBOOK"),
    ("model jury","MJI"),
    ("mji","MJI"),
    ("scao","SCAO_GUIDE"),
    ("mc ","SCAO_FORM"),
    ("foc ","SCAO_FORM"),
    ("instructions","SCAO_FORM_INSTR"),
]

def guess_type(path:Path, text_sample:str)->str:
    low=(path.name+" "+(text_sample or "")[:500]).lower()
    for k,t in TYPE_HINTS:
        if k in low:
            return t
    # last resort based on file name prefix
    n=path.name.lower()
    if n.startswith("mcr"): return "MCR"
    if n.startswith("mcl"): return "MCL"
    if n.startswith("mre"): return "MRE"
    return "MI_BENCHBOOK"

def pdf_pages(path:Path)->List[str]:
    if fitz is None:
        return []
    doc=fitz.open(str(path))
    out=[]
    for i in range(doc.page_count):
        out.append(doc.load_page(i).get_text("text") or "")
    doc.close()
    return out

def write_jsonl(p:Path, rows:Iterable[Dict[str,Any]]):
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("ab") as f:
        for r in rows:
            f.write(orjson.dumps(r)); f.write(b"\n")

def build(cfg_path:Path, out_index:Path, out_db:Path):
    cfg=json.loads(cfg_path.read_text(encoding="utf-8", errors="ignore"))
    snap=cfg.get("authority_snapshot") or {}
    snapshot_id=snap.get("snapshot_id")
    eff=snap.get("effective_date")
    paths=[Path(x) for x in (snap.get("paths") or [])]
    if not snapshot_id:
        raise SystemExit("Missing config.authority_snapshot.snapshot_id")
    if not paths:
        raise SystemExit("Missing config.authority_snapshot.paths")

    out_db.mkdir(parents=True, exist_ok=True)
    index={"snapshot_id":snapshot_id,"effective_date":eff,"built_at":now_iso(),"authorities":[],"authority_refs":[]}

    auth_rows=[]
    for p in paths:
        if not p.exists():
            index["authorities"].append({"path":str(p),"status":"MISSING"})
            continue
        if p.suffix.lower()==".pdf":
            pages=pdf_pages(p)
            atype=guess_type(p, pages[0] if pages else "")
            for i,txt in enumerate(pages, start=1):
                if not (txt or "").strip():
                    continue
                cites=set(m.group(0).strip() for m in CITE_RX.finditer(txt))
                aos=set(m.group(0).upper().replace(" ","") for m in AO_RX.finditer(txt))
                chunk_id=f"AUTHCH:{sha1(str(p)+'|'+str(i))}"
                pin=mk_pinpoint(str(p),page=i)
                auth_rows.append({"auth_chunk_id":chunk_id,"snapshot_id":snapshot_id,"type":atype,"source_path":str(p),
                                  "pinpoint":pin,"text":txt,"citations":sorted(cites|aos),"record_time":now_iso(),"confidence":0.7})
        else:
            lines=p.read_text(encoding="utf-8", errors="ignore").splitlines()
            atype=guess_type(p, "\n".join(lines[:50]))
            for j,ln in enumerate(lines, start=1):
                if not ln.strip(): continue
                cites=set(m.group(0).strip() for m in CITE_RX.finditer(ln))
                aos=set(m.group(0).upper().replace(" ","") for m in AO_RX.finditer(ln))
                chunk_id=f"AUTHCH:{sha1(str(p)+'|'+str(j)+'|'+ln[:80])}"
                pin=mk_pinpoint(str(p),page=1,line=j)
                auth_rows.append({"auth_chunk_id":chunk_id,"snapshot_id":snapshot_id,"type":atype,"source_path":str(p),
                                  "pinpoint":pin,"text":ln,"citations":sorted(cites|aos),"record_time":now_iso(),"confidence":0.55})
        index["authorities"].append({"path":str(p),"status":"OK","type":atype})

    write_jsonl(out_db/"AuthorityDB.jsonl", auth_rows)

    seen=set()
    refs=[]
    for r in auth_rows:
        for c in (r.get("citations") or []):
            key=(c,r["source_path"],r["pinpoint"].get("page"),r["pinpoint"].get("line"))
            if key in seen: continue
            seen.add(key)
            auth_id=f"AUTH:{sha1(c+'|'+r['source_path'])}"
            refs.append({"auth_id":auth_id,"type":r["type"],"citation":c,"pinpoint":r["pinpoint"],
                         "snapshot_id":snapshot_id,"effective_date":eff,"repealed_date":None,
                         "notes":"auto-indexed; refine as needed"})
    index["authority_refs"]=refs
    out_index.parent.mkdir(parents=True, exist_ok=True)
    out_index.write_text(json.dumps(index, indent=2), encoding="utf-8")
    return {"snapshot_id":snapshot_id,"chunks":len(auth_rows),"authority_refs":len(refs)}

def main():
    import argparse
    ap=argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--out-index", required=True)
    ap.add_argument("--out-db", required=True)
    args=ap.parse_args()
    res=build(Path(args.config), Path(args.out_index), Path(args.out_db))
    print(json.dumps(res))
if __name__=="__main__":
    main()
