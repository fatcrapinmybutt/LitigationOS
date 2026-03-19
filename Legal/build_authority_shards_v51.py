#!/usr/bin/env python3
"""
build_authority_shards_v51.py — AUTHORITY SHARD BUILDER (v51)
Uses doc_convert_router_v50.py to extract page-scoped text/header_lines/anchors and writes:

- outputs/authority_shards.jsonl (1 JSON object per page)
- outputs/authority_index.jsonl (anchor-first index lines: anchor -> authority_ref list)
- outputs/authority_anchor_density_report.json (non-interpretive metrics)

Fallback heuristic (non-interpretive):
1) Run router with backend=pdftotext
2) If anchor density < threshold OR header_lines empty, rerun with backend=unstructured
3) If still low, rerun with backend=docling

No rewriting. No summaries. Output is direct extraction + computed counts only.

Usage:
  python tools/build_authority_shards_v51.py --pdf-dir sources/pdfs --out-dir outputs
  python tools/build_authority_shards_v51.py --pdf-list outputs/pdf_list.json --out-dir outputs
"""
import argparse, os, json, hashlib, subprocess, datetime, re, sys
from collections import defaultdict

def sha256_bytes(b: bytes) -> str:
    import hashlib
    h=hashlib.sha256(); h.update(b); return h.hexdigest()

def sha256_file(path: str) -> str:
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for ch in iter(lambda:f.read(1024*1024), b""):
            h.update(ch)
    return h.hexdigest()

def safe_mkdir(p): os.makedirs(p, exist_ok=True)

def list_pdfs(pdf_dir):
    out=[]
    for r,ds,fs in os.walk(pdf_dir):
        for fn in fs:
            if fn.lower().endswith(".pdf"):
                out.append(os.path.join(r,fn))
    return sorted(out)

def load_pdf_list(p):
    data=json.load(open(p,"r",encoding="utf-8"))
    if isinstance(data, dict) and "pdfs" in data:
        return data["pdfs"]
    if isinstance(data, list):
        return data
    raise SystemExit("pdf list must be a list or {pdfs:[...]}")

def run_router(router_py, pdf, backend, out_json, unstructured_strategy="auto", first_page=1, last_page=0):
    cmd=[sys.executable, router_py, "--pdf", pdf, "--backend", backend, "--unstructured-strategy", unstructured_strategy,
         "--out-json", out_json, "--first-page", str(first_page), "--last-page", str(last_page)]
    subprocess.check_call(cmd)

def anchor_density(pages):
    # anchors per non-empty page, and header line presence
    total_anchors=0
    nonempty_pages=0
    header_pages=0
    for pg in pages:
        txt=pg.get("text","")
        if (txt or "").strip():
            nonempty_pages += 1
        if pg.get("header_lines"):
            header_pages += 1
        total_anchors += len(pg.get("anchors") or [])
    if nonempty_pages==0:
        return 0.0, total_anchors, nonempty_pages, header_pages
    return total_anchors / float(nonempty_pages), total_anchors, nonempty_pages, header_pages

def doc_id_from_path(p):
    # stable-ish doc_id based on relative filename stem + sha256 of path string
    base=os.path.basename(p)
    stem=os.path.splitext(base)[0]
    sid=sha256_bytes(p.encode("utf-8"))[:12]
    return f"{stem}__{sid}"

def write_jsonl(path, rows):
    with open(path,"w",encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--pdf-dir", default="")
    ap.add_argument("--pdf-list", default="")
    ap.add_argument("--out-dir", default="outputs")
    ap.add_argument("--router", default="tools/doc_convert_router_v50.py")
    ap.add_argument("--unstructured-strategy", default="auto", choices=["auto","fast","hi_res","ocr_only"])
    ap.add_argument("--density-threshold", type=float, default=2.0, help="anchors per non-empty page")
    ap.add_argument("--max-pdfs", type=int, default=0)
    args=ap.parse_args()

    out_dir=args.out_dir
    safe_mkdir(out_dir)

    pdfs=[]
    if args.pdf_dir:
        pdfs=list_pdfs(args.pdf_dir)
    elif args.pdf_list:
        pdfs=load_pdf_list(args.pdf_list)
    else:
        raise SystemExit("Provide --pdf-dir or --pdf-list")

    if args.max_pdfs and args.max_pdfs>0:
        pdfs=pdfs[:args.max_pdfs]

    router=os.path.abspath(args.router)
    if not os.path.exists(router):
        raise SystemExit("Router not found: "+router)

    shards=[]
    index=defaultdict(list)
    report_docs=[]

    tmp=os.path.join(out_dir,"_router_tmp")
    safe_mkdir(tmp)

    for i,pdf in enumerate(pdfs, start=1):
        if not os.path.exists(pdf):
            continue
        did=doc_id_from_path(pdf)
        dsha=sha256_file(pdf)
        # run router pdftotext first
        out1=os.path.join(tmp, f"{did}.pdftotext.json")
        chosen="pdftotext"
        run_router(router, pdf, "pdftotext", out1, unstructured_strategy=args.unstructured_strategy)
        data=json.load(open(out1,"r",encoding="utf-8"))
        dens, total_anc, nonempty, header_pages = anchor_density(data.get("pages") or [])
        attempted=[{"backend":"pdftotext","density":dens,"total_anchors":total_anc,"nonempty_pages":nonempty,"header_pages":header_pages}]

        # fallback 1
        if dens < args.density_threshold or header_pages==0:
            out2=os.path.join(tmp, f"{did}.unstructured.json")
            if True:
                try:
                    run_router(router, pdf, "unstructured", out2, unstructured_strategy=args.unstructured_strategy)
                    data2=json.load(open(out2,"r",encoding="utf-8"))
                    dens2, ta2, ne2, hp2 = anchor_density(data2.get("pages") or [])
                    attempted.append({"backend":"unstructured","density":dens2,"total_anchors":ta2,"nonempty_pages":ne2,"header_pages":hp2})
                    if dens2 > dens or hp2>header_pages:
                        data=data2; dens=dens2; total_anc=ta2; nonempty=ne2; header_pages=hp2; chosen="unstructured"
                except Exception:
                    attempted.append({"backend":"unstructured","error":"failed"})
        # fallback 2
        if dens < args.density_threshold or header_pages==0:
            out3=os.path.join(tmp, f"{did}.docling.json")
            try:
                run_router(router, pdf, "docling", out3, unstructured_strategy=args.unstructured_strategy)
                data3=json.load(open(out3,"r",encoding="utf-8"))
                dens3, ta3, ne3, hp3 = anchor_density(data3.get("pages") or [])
                attempted.append({"backend":"docling","density":dens3,"total_anchors":ta3,"nonempty_pages":ne3,"header_pages":hp3})
                if dens3 > dens or hp3>header_pages:
                    data=data3; dens=dens3; total_anc=ta3; nonempty=ne3; header_pages=hp3; chosen="docling"
            except Exception:
                attempted.append({"backend":"docling","error":"failed"})

        report_docs.append({
            "doc_id": did,
            "source_path": os.path.abspath(pdf),
            "doc_sha256": dsha,
            "chosen_backend": chosen,
            "anchor_density": dens,
            "total_anchors": total_anc,
            "nonempty_pages": nonempty,
            "header_pages": header_pages,
            "attempts": attempted
        })

        for pg in (data.get("pages") or []):
            pno=int(pg.get("page") or 0)
            authority_ref=f"{did}#p{pno}"
            row={
                "doc_id": did,
                "doc_sha256": dsha,
                "source_path": os.path.abspath(pdf),
                "page": pno,
                "authority_ref": authority_ref,
                "text": pg.get("text",""),
                "header_lines": pg.get("header_lines") or [],
                "anchors": pg.get("anchors") or [],
                "convert_backend": chosen,
                "created_utc": datetime.datetime.utcnow().isoformat()+"Z"
            }
            shards.append(row)
            for a in row["anchors"]:
                index[a].append(authority_ref)

    # Write outputs
    shards_path=os.path.join(out_dir,"authority_shards.jsonl")
    write_jsonl(shards_path, shards)

    idx_rows=[]
    for anchor, refs in sorted(index.items(), key=lambda x: x[0].lower()):
        # de-dupe refs
        seen=set(); out=[]
        for r in refs:
            if r in seen: continue
            seen.add(r); out.append(r)
        idx_rows.append({"anchor": anchor, "authority_refs": out, "count": len(out)})
    idx_path=os.path.join(out_dir,"authority_index.jsonl")
    write_jsonl(idx_path, idx_rows)

    rep_path=os.path.join(out_dir,"authority_anchor_density_report.json")
    json.dump({"generated_utc": datetime.datetime.utcnow().isoformat()+"Z",
               "density_threshold": args.density_threshold,
               "docs": report_docs,
               "totals": {"docs": len(report_docs), "pages": len(shards), "unique_anchors": len(idx_rows)}},
              open(rep_path,"w",encoding="utf-8"), indent=2, ensure_ascii=False)

    print("OK docs=", len(report_docs), "pages=", len(shards), "anchors=", len(idx_rows))
    print("->", shards_path)
    print("->", idx_path)
    print("->", rep_path)

if __name__=="__main__":
    main()
