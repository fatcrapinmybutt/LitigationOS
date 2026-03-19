#!/usr/bin/env python3
import argparse, json, re

RE_COA_UNPUB = re.compile(r'\b(unpub|unpublished)\b', re.I)
RE_NW2D = re.compile(r'\bNW2d\b', re.I)
RE_DOCKET = re.compile(r'\bNo\.\s*\d+', re.I)
RE_YEAR = re.compile(r'\b(19|20)\d{2}\b')

def classify(cite):
    c=cite.strip()
    flags=[]
    cls={"court_level":"UNKNOWN","publication":"UNKNOWN","reporter":[],"has_docket_no":False,"has_year":False}
    if RE_NW2D.search(c): cls["reporter"].append("NW2d")
    if RE_COA_UNPUB.search(c): cls["publication"]="UNPUBLISHED"
    if re.search(r'\bMich\s*App\b', c, re.I) or re.search(r'\bMich\s+App\b', c, re.I):
        cls["court_level"]="COA"
    elif re.search(r'\bMich\b', c, re.I):
        cls["court_level"]="MSC_CANDIDATE"
        flags.append("VALIDATE_COURT_LEVEL")
    if cls["court_level"]=="COA" and cls["publication"]=="UNKNOWN":
        flags.append("VALIDATE_PUBLICATION_STATUS")
    if RE_DOCKET.search(c): cls["has_docket_no"]=True
    if RE_YEAR.search(c): cls["has_year"]=True
    flags += ["HOLDING_ONLY_REQUIRED","PINPOINT_REQUIRED"]
    validation_required=True
    return cls, flags, validation_required

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--in-json", required=True)
    ap.add_argument("--out-json", required=True)
    args=ap.parse_args()

    payload=json.load(open(args.in_json,"r",encoding="utf-8"))
    citations=payload.get("citations") or []
    out={"items":[],"meta":{"confidence":"CANDIDATE_ONLY","notes":"HEURISTIC_CLASSIFICATION_NO_VERIFICATION"}}
    for it in citations:
        ct=(it.get("citation_text") or "").strip()
        if not ct: 
            continue
        cls, flags, vr = classify(ct)
        out["items"].append({
            "citation_text": ct,
            "classification": cls,
            "status_flags": flags,
            "validation_required": vr,
            "confidence":"CANDIDATE_ONLY"
        })
    json.dump(out, open(args.out_json,"w",encoding="utf-8"), indent=2, ensure_ascii=False)
    print(f"OK items={len(out['items'])}")

if __name__=="__main__":
    main()
