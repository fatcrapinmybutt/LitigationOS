#!/usr/bin/env python3
import argparse, json, os, sys

def read_jsonl(p):
    with open(p,"r",encoding="utf-8") as f:
        for i,ln in enumerate(f, start=1):
            ln=ln.strip()
            if not ln: 
                continue
            try:
                yield i, json.loads(ln)
            except Exception as e:
                yield i, {"_parse_error": str(e), "_raw": ln}

def load_manifest(p):
    if not p: return None
    m=json.load(open(p,"r",encoding="utf-8"))
    files=m.get("files") if isinstance(m,dict) else None
    if not isinstance(files, list): return None
    return { (x.get("path") or ""): x for x in files if isinstance(x,dict) and x.get("path") }

def has_locator(pin):
    if not isinstance(pin, dict): return False
    if isinstance(pin.get("page"), int): return True
    if (pin.get("timecode") or "").strip(): return True
    if (pin.get("bates") or "").strip(): return True
    ls=pin.get("line_start"); le=pin.get("line_end")
    if isinstance(ls,int) and isinstance(le,int): return True
    return False

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--facts-jsonl", required=True)
    ap.add_argument("--manifest-json", default="")
    ap.add_argument("--out-json", required=True)
    args=ap.parse_args()

    if not os.path.exists(args.facts_jsonl) or os.path.getsize(args.facts_jsonl)==0:
        json.dump({"status":"FAIL","error":"facts file missing/empty"}, open(args.out_json,"w",encoding="utf-8"), indent=2)
        raise SystemExit(2)

    manifest=load_manifest(args.manifest_json) if args.manifest_json else None

    violations=[]
    checked=0
    for lnno,row in read_jsonl(args.facts_jsonl):
        checked += 1
        if "_parse_error" in row:
            violations.append({"line":lnno,"code":"JSONL_PARSE_ERROR","detail":row["_parse_error"]})
            continue
        fid=(row.get("fact_id") or "").strip()
        txt=(row.get("text") or "").strip()
        pin=row.get("pinpoint") or {}
        st=(pin.get("source_type") or "").strip()
        sp=(pin.get("source_path") or "").strip()
        if not fid: violations.append({"line":lnno,"code":"MISSING_fact_id"})
        if not txt: violations.append({"line":lnno,"code":"MISSING_text"})
        if not st: violations.append({"line":lnno,"code":"MISSING_pinpoint.source_type"})
        if not sp: violations.append({"line":lnno,"code":"MISSING_pinpoint.source_path"})
        if st and sp and (not has_locator(pin)):
            violations.append({"line":lnno,"code":"MISSING_locator","detail":"need page OR timecode OR bates OR (line_start+line_end)"})
        if manifest is not None and sp:
            ok = (sp in manifest) or any(k.endswith(sp) for k in manifest.keys())
            if not ok:
                violations.append({"line":lnno,"code":"SOURCE_NOT_IN_MANIFEST","detail":sp})

    status="PASS" if not violations else "FAIL"
    out={"status":status,"facts_checked":checked,"violations":violations}
    json.dump(out, open(args.out_json,"w",encoding="utf-8"), indent=2)
    print(f"OK status={status} facts={checked} violations={len(violations)}")

if __name__=="__main__":
    main()
