#!/usr/bin/env python3
"""
doc_convert_router_v50.py — Document Conversion Backend Router (v50)

Backends (optional; auto-fallback):
- pdftotext (Poppler) with -layout (fast)
- unstructured.partition.pdf (typed elements; strategies auto/fast/hi_res/ocr_only)
- docling (Granite-Docling via docling pipelines; structure-preserving)

Non-interpretive:
- No rewriting/summarizing. 'header_lines' are directly extracted lines/elements.
- Emits backend metadata so downstream shard builders can prefer higher-fidelity output.

Output JSON:
{
  "backend": "pdftotext|unstructured|docling",
  "pdf": "...",
  "pages": [{"page":1,"text":"...","header_lines":[...],"anchors":[...],"meta":{...}}, ...]
}
"""
import argparse, json, os, re, subprocess, tempfile, shutil, datetime

RULE_RX=re.compile(r"\b(MCR|MCL|MRE)\s*[\dA-Z]+\b", re.IGNORECASE)
SECTION_RX=re.compile(r"\b(§|Sec\.|Section)\s*\d+[\w\.\-\(\)]*", re.IGNORECASE)

def which(cmd): return shutil.which(cmd)

def run_pdftotext(pdf_path, first_page, last_page):
    if not which("pdftotext"): raise RuntimeError("pdftotext not found on PATH")
    out=[]
    for p in range(first_page, last_page+1):
        tf=tempfile.NamedTemporaryFile(delete=False, suffix=".txt"); tf.close()
        try:
            subprocess.check_call(["pdftotext","-layout","-f",str(p),"-l",str(p),pdf_path,tf.name],
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            txt=open(tf.name,"r",encoding="utf-8",errors="replace").read()
        finally:
            try: os.remove(tf.name)
            except Exception: pass
        out.append((p,txt,[]))
    return out

def run_unstructured(pdf_path, strategy="auto"):
    try:
        from unstructured.partition.pdf import partition_pdf
    except Exception as e:
        raise RuntimeError(f"unstructured not available: {e}")
    elements = partition_pdf(filename=pdf_path, strategy=strategy, include_page_breaks=True)
    pages=[]; page=1; buf=[]; titles=[]
    for el in elements:
        cls=el.__class__.__name__
        if cls.lower()=="pagebreak":
            pages.append((page,"\n".join(buf),titles)); page+=1; buf=[]; titles=[]; continue
        t=getattr(el,"text",None) or str(el)
        if t: buf.append(t)
        cat=getattr(el,"category",None) or getattr(el,"type",None) or cls
        if str(cat).lower() in ("title","header","heading"): titles.append(t.strip())
    pages.append((page,"\n".join(buf),titles))
    return [(p,txt,tl) for p,txt,tl in pages]

def run_docling(pdf_path):
    try:
        from docling.document_converter import DocumentConverter
    except Exception as e:
        raise RuntimeError(f"docling not available: {e}")
    conv=DocumentConverter()
    res=conv.convert(pdf_path)
    doc=getattr(res,"document",None) or getattr(res,"doc",None) or res
    if hasattr(doc,"pages"):
        out=[]
        for i,pg in enumerate(doc.pages, start=1):
            if hasattr(pg,"text"): txt=pg.text
            elif hasattr(pg,"to_markdown"): txt=pg.to_markdown()
            else: txt=str(pg)
            out.append((i,txt,[]))
        if out: return out
    if hasattr(doc,"to_markdown"): md=doc.to_markdown()
    elif hasattr(res,"to_markdown"): md=res.to_markdown()
    else: md=str(res)
    return [(1,md,[])]

def header_lines_from_text(txt, n):
    lines=[ln.strip() for ln in (txt or "").splitlines() if ln.strip()]
    return lines[:n]

def anchors_from_text(txt, maxn=64):
    anchors=[]
    for m in RULE_RX.finditer(txt or ""):
        anchors.append(m.group(0))
        if len(anchors)>=maxn: break
    if len(anchors)<maxn:
        for m in SECTION_RX.finditer(txt or ""):
            anchors.append(m.group(0))
            if len(anchors)>=maxn: break
    seen=set(); out=[]
    for a in anchors:
        k=a.lower()
        if k in seen: continue
        seen.add(k); out.append(a)
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--pdf", required=True)
    ap.add_argument("--backend", choices=["auto","pdftotext","unstructured","docling"], default="auto")
    ap.add_argument("--unstructured-strategy", default="auto", choices=["auto","fast","hi_res","ocr_only"])
    ap.add_argument("--max-header-lines", type=int, default=6)
    ap.add_argument("--out-json", required=True)
    ap.add_argument("--first-page", type=int, default=1)
    ap.add_argument("--last-page", type=int, default=0)
    args=ap.parse_args()

    pdf=args.pdf
    if not os.path.exists(pdf): raise SystemExit("PDF not found: "+pdf)
    lp=args.last_page if args.last_page>0 else args.first_page

    chosen=None; pages=None

    def try_backend(name, fn):
        nonlocal chosen, pages
        try:
            pages=fn(); chosen=name; return True
        except Exception:
            return False

    if args.backend=="pdftotext":
        if not try_backend("pdftotext", lambda: run_pdftotext(pdf,args.first_page,lp)): raise SystemExit("pdftotext failed")
    elif args.backend=="unstructured":
        if not try_backend("unstructured", lambda: run_unstructured(pdf,args.unstructured_strategy)): raise SystemExit("unstructured failed")
    elif args.backend=="docling":
        if not try_backend("docling", lambda: run_docling(pdf)): raise SystemExit("docling failed")
    else:
        if which("pdftotext"): try_backend("pdftotext", lambda: run_pdftotext(pdf,args.first_page,lp))
        if chosen is None: try_backend("unstructured", lambda: run_unstructured(pdf,args.unstructured_strategy))
        if chosen is None: try_backend("docling", lambda: run_docling(pdf))
        if chosen is None: raise SystemExit("No usable backend found")

    out_pages=[]
    for p,txt,titles in pages:
        hl=(titles[:args.max_header_lines] if titles else header_lines_from_text(txt,args.max_header_lines))
        anchors=anchors_from_text("\n".join(hl)+"\n"+(txt or ""))
        out_pages.append({"page":int(p),"text":txt or "","header_lines":hl,"anchors":anchors,
                          "meta":{"backend":chosen,"unstructured_strategy":args.unstructured_strategy}})

    out={"backend":chosen,"pdf":os.path.abspath(pdf),"pages":out_pages,
         "meta":{"generated_utc":datetime.datetime.utcnow().isoformat()+"Z"}}
    os.makedirs(os.path.dirname(args.out_json) or ".", exist_ok=True)
    json.dump(out, open(args.out_json,"w",encoding="utf-8"), indent=2, ensure_ascii=False)
    print("OK", chosen, len(out_pages), "->", args.out_json)

if __name__=="__main__":
    main()
