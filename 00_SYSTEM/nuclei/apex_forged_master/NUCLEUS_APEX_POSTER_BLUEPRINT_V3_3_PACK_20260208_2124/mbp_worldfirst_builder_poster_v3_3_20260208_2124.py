#!/usr/bin/env python3
"""mbp_worldfirst_builder_poster_v3_3.py

Portable offline builder for the V3.3 poster metrics + assets.

This is intentionally conservative: it extracts core inventories/metrics and copies case-pack assets.
In LitigationOS, wire this into your full runtime to regenerate posters deterministically.
"""
import os, argparse, zipfile, shutil, re, json, zlib, collections, datetime
import pandas as pd
import xml.etree.ElementTree as ET
import html as ihtml

def sanitize_ascii(s):
    if s is None:
        return ""
    s=str(s).replace("\t"," ")
    s=re.sub(r"\s+"," ",s).strip()
    s="".join(ch if 32<=ord(ch)<=126 else "" for ch in s)
    s=re.sub(r"\s+"," ",s).strip()
    return s

def crc32_file(path):
    buf=1024*1024
    c=0
    with open(path,'rb') as f:
        while True:
            b=f.read(buf)
            if not b:
                break
            c=zlib.crc32(b,c)
    return c & 0xffffffff

def integrity_key(path):
    st=os.stat(path)
    return f"IK:{os.path.basename(path)}:{st.st_size}:{int(st.st_mtime)}:{crc32_file(path):08x}"

def unzip_into(zip_path, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    with zipfile.ZipFile(zip_path,'r') as z:
        z.extractall(out_dir)

def zip_inventory(zip_path, pack):
    rows=[]
    with zipfile.ZipFile(zip_path,'r') as z:
        for info in z.infolist():
            if info.is_dir(): 
                continue
            p=info.filename
            ext=os.path.splitext(p)[1].lower()
            rows.append({
                "pack": pack,
                "path": p,
                "basename": os.path.basename(p),
                "ext": ext if ext else "",
                "size": info.file_size,
                "compressed": info.compress_size,
                "mtime": "%04d-%02d-%02d %02d:%02d:%02d"%info.date_time,
            })
    return pd.DataFrame(rows)

def graphml_scan_fast(path, max_tag_tokens=250000):
    node_count=edge_count=0
    kind_counter=collections.Counter()
    edge_counter=collections.Counter()
    tag_counter=collections.Counter()
    token_re=re.compile(r"[A-Za-z0-9_:/\-\.\$]+")
    tags_seen=0
    for event, elem in ET.iterparse(path, events=("end",)):
        tag=elem.tag.split('}')[-1]
        if tag=="node":
            node_count += 1
            kind=None
            tags=None
            for d in elem.findall("{*}data"):
                k=d.attrib.get("key")
                txt=(d.text or "").strip()
                if k=="d3": kind=txt
                elif k=="d2": tags=txt
            if kind: kind_counter[kind]+=1
            if tags and tags_seen < max_tag_tokens:
                t=tags
                for ch in ['|',',',';','\t']:
                    t=t.replace(ch,' ')
                for tok in token_re.findall(t):
                    if len(tok)<=2: 
                        continue
                    tag_counter[tok.lower()]+=1
                    tags_seen += 1
                    if tags_seen>=max_tag_tokens:
                        break
            elem.clear()
        elif tag=="edge":
            edge_count += 1
            et=None
            for d in elem.findall("{*}data"):
                if d.attrib.get("key")=="e0":
                    et=(d.text or "").strip()
                    break
            if et: edge_counter[et]+=1
            elem.clear()
    kind_df=pd.DataFrame([{"kind":k,"count":v} for k,v in kind_counter.most_common()])
    if node_count: kind_df["share"]=kind_df["count"]/node_count
    edge_df=pd.DataFrame([{"edge_type":k,"count":v} for k,v in edge_counter.most_common()])
    if edge_count: edge_df["share"]=edge_df["count"]/edge_count
    tag_df=pd.DataFrame([{"tag_token":k,"count":v} for k,v in tag_counter.most_common()])
    return node_count, edge_count, kind_df, edge_df, tag_df

def normalize_escaped_newlines(text):
    t=ihtml.unescape(text)
    return t.replace("\\r\\n","\n").replace("\\n","\n").replace("\\r","\n")

def extract_md_headings(text):
    heads=[]
    for ln in text.splitlines():
        s=ln.strip()
        if s.startswith("#"):
            lvl=len(s)-len(s.lstrip("#"))
            title=s[lvl:].strip()
            if title:
                heads.append((lvl,title))
    return heads

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--graphml", required=True)
    ap.add_argument("--bloom-html", required=True)
    ap.add_argument("--emily-zip", required=True)
    ap.add_argument("--meek2-zip", required=True)
    ap.add_argument("--out-root", default=None)
    args=ap.parse_args()

    ts=datetime.datetime.now().strftime("%Y%m%d_%H%M")
    root=os.path.abspath(args.out_root or f"NUCLEUS_APEX_V3_3_REBUILD_{ts}")
    metrics=os.path.join(root,"metrics_v3_3")
    unpack=os.path.join(root,"unpack")
    assets=os.path.join(root,"case_pack_assets")
    os.makedirs(metrics, exist_ok=True)
    os.makedirs(unpack, exist_ok=True)
    os.makedirs(assets, exist_ok=True)

    unzip_into(args.emily_zip, os.path.join(unpack,"Emily_ExParte_Attachments"))
    unzip_into(args.meek2_zip, os.path.join(unpack,"MEEK2_CUSTODY_LITIGATION_PACK"))

    inv=pd.concat([
        zip_inventory(args.emily_zip,"Emily_ExParte_Attachments"),
        zip_inventory(args.meek2_zip,"MEEK2_CUSTODY_LITIGATION_PACK"),
    ], ignore_index=True)
    inv.to_csv(os.path.join(metrics,"zip_inventory.csv"), index=False)

    n,e,kind_df,edge_df,tag_df=graphml_scan_fast(args.graphml)
    kind_df.to_csv(os.path.join(metrics,"graphml_kind_counts.csv"), index=False)
    edge_df.to_csv(os.path.join(metrics,"graphml_edge_type_counts.csv"), index=False)
    tag_df.to_csv(os.path.join(metrics,"graphml_tag_token_counts.csv"), index=False)

    raw=open(args.bloom_html,'r',encoding='utf-8',errors='ignore').read()
    norm=normalize_escaped_newlines(raw)
    rows=[]
    for i,(lvl,title) in enumerate(extract_md_headings(norm), start=1):
        rows.append({"idx":i,"level":lvl,"title":sanitize_ascii(title)})
    pd.DataFrame(rows).to_csv(os.path.join(metrics,"bloom_toc_full.csv"), index=False)

    # Copy basic assets: images + first pdf found
    img_dir=os.path.join(unpack,"Emily_ExParte_Attachments")
    for fn in os.listdir(img_dir):
        if fn.lower().endswith((".png",".jpg",".jpeg",".webp")):
            shutil.copy2(os.path.join(img_dir,fn), os.path.join(assets,fn))
    pdf=None
    for r,_,files in os.walk(os.path.join(unpack,"MEEK2_CUSTODY_LITIGATION_PACK")):
        for fn in files:
            if fn.lower().endswith(".pdf"):
                pdf=os.path.join(r,fn); break
        if pdf: break
    if pdf:
        shutil.copy2(pdf, os.path.join(assets, os.path.basename(pdf)))

    print("Rebuild complete:", root)

if __name__=="__main__":
    main()
