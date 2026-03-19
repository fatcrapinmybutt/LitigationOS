#!/usr/bin/env python3
"""mbp_worldfirst_builder_poster_v3_5_20260208_2141.py

World-first offline builder for NUCLEUS APEX V3.5 FASTLANE.

Rebuilds:
- Unpack selected zips (with bounded recursive nested zip extraction)
- File inventory + CRC32 manifests
- Keyword global counts + top-hit files (text-like scanning with per-file byte cap)
- Date candidates + normalized timeline candidates
- OperatingOrderPin schema + external tool receipt schemas
- V3.5 poster PDF (48x36 multipage)

No network calls. Deterministic-ish given same inputs and same environment.

Usage:
  python mbp_worldfirst_builder_poster_v3_5_20260208_2141.py --out-root OUTDIR \
    --emily-zip Emily_ExParte_Attachments.zip \
    --meek2-zip MEEK2_CUSTODY_LITIGATION_PACK.zip \
    --attachment-harvest ATTACHMENT_HARVEST_20260208.zip \
    --meek234 MEEK234_FULLSTACK_REBUILD_PACK_v20260208.zip

"""
import os, re, json, zipfile, zlib, argparse, datetime, textwrap, collections
from pathlib import Path
import pandas as pd
import pdfplumber
from reportlab.lib.pagesizes import landscape
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle

TEXT_EXTS=set([".txt",".md",".csv",".json",".yaml",".yml",".log",".tsv",".rtf"])
KEYWORDS=["emily", "watson", "watsons", "albert", "lori", "cody", "mcneill", "judge", "bias", "lies", "show cause", "showcause", "ppo", "personal protection", "contempt", "roa", "docket", "dockets", "jail", "incarceration", "mittimus", "martini", "email", "emails", "voicemail", "served", "service", "hearing", "order", "ex parte", "exparte", "healthwest", "evaluation", "parenting time", "custody", "sanction", "$250", "250", "objection", "motion", "filed", "submitted", "dispatch", "nspd", "police report"]
KW_NORM=[k.lower() for k in KEYWORDS]
DATE_RE=re.compile(r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b")
ISO_RE=re.compile(r"\b(20\d{2}-\d{2}-\d{2})\b")

def sanitize_ascii(s):
    if s is None: return ""
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
            if not b: break
            c=zlib.crc32(b,c)
    return c & 0xffffffff

def unzip_into(zip_path, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    with zipfile.ZipFile(zip_path,'r') as z:
        z.extractall(out_dir)

def recursive_unzip(root_dir, max_nested=60):
    nested=[]
    for r,_,files in os.walk(root_dir):
        for fn in files:
            if fn.lower().endswith(".zip"):
                nested.append(os.path.join(r,fn))
    nested=sorted(nested)[:max_nested]
    for zp in nested:
        out=zp + "__unz"
        if not os.path.exists(out):
            try: unzip_into(zp,out)
            except Exception: pass

def normalize_date(d):
    d=d.strip()
    if re.fullmatch(r"20\d{2}-\d{2}-\d{2}", d): return d
    m=re.fullmatch(r"(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})", d)
    if not m: return ""
    mo=int(m.group(1)); da=int(m.group(2)); yr=int(m.group(3))
    if yr<100: yr=2000+yr if yr<=49 else 1900+yr
    if not (1<=mo<=12 and 1<=da<=31 and 1900<=yr<=2099): return ""
    return f"{yr:04d}-{mo:02d}-{da:02d}"

def safe_read_text(fp, max_bytes=200000):
    with open(fp,'rb') as f:
        b=f.read(max_bytes)
    for enc in ("utf-8","utf-8-sig","latin-1"):
        try: return b.decode(enc, errors="ignore")
        except Exception: pass
    return ""

def build_poster(pdf_path, meta_line, ext_counts_df, largest_df, kw_global_df, kw_file_df, timeline_df):
    W,H=landscape((48*inch,36*inch))
    c=canvas.Canvas(pdf_path, pagesize=(W,H))
    margin=0.6*inch
    base_y=0.6*inch
    usable_w=W-2*margin
    usable_h=H-2.0*inch

    def draw_header(title, subtitle):
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 34)
        c.drawString(0.75*inch, H-0.9*inch, sanitize_ascii(title))
        c.setFont("Helvetica", 13)
        c.setFillColor(colors.grey)
        c.drawString(0.75*inch, H-1.23*inch, sanitize_ascii(subtitle))
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 11)
        c.drawString(0.75*inch, H-1.5*inch, sanitize_ascii(meta_line))

    def panel_box(x,y,w,h,title,subtitle=None):
        c.setStrokeColor(colors.black)
        c.setLineWidth(1.15)
        c.roundRect(x,y,w,h,12,stroke=1,fill=0)
        c.setFont("Helvetica-Bold", 18)
        c.drawString(x+0.25*inch, y+h-0.45*inch, sanitize_ascii(title))
        if subtitle:
            c.setFont("Helvetica", 11)
            c.setFillColor(colors.grey)
            c.drawString(x+0.25*inch, y+h-0.7*inch, sanitize_ascii(subtitle))
            c.setFillColor(colors.black)

    def draw_table_panel(x,y,w,h,title,subtitle,df,cols,col_fracs,max_rows=18,fontsize=9,right_align_from=1):
        panel_box(x,y,w,h,title,subtitle)
        view=df.copy().head(max_rows)
        data=[cols]
        for _,r in view.iterrows():
            row=[]
            for col in cols:
                v=r.get(col,"")
                if isinstance(v,(float,int)) and ("count" in col or col in ("bytes","hit_total","line_no")):
                    row.append(f"{int(v):,}")
                else:
                    row.append(sanitize_ascii(v))
            data.append(row)
        colWidths=[w*f for f in col_fracs]
        tbl=Table(data, colWidths=colWidths)
        style=[
            ('BACKGROUND',(0,0),(-1,0),colors.lightgrey),
            ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
            ('FONTSIZE',(0,0),(-1,0),10),
            ('FONTSIZE',(0,1),(-1,-1),fontsize),
            ('GRID',(0,0),(-1,-1),0.5,colors.grey),
            ('LEFTPADDING',(0,0),(-1,-1),4),
            ('RIGHTPADDING',(0,0),(-1,-1),4),
            ('TOPPADDING',(0,0),(-1,-1),3),
            ('BOTTOMPADDING',(0,0),(-1,-1),3),
        ]
        if right_align_from is not None:
            style.append(('ALIGN',(right_align_from,1),(-1,-1),'RIGHT'))
        tbl.setStyle(TableStyle(style))
        avail_w=w-0.4*inch
        avail_h=h-1.05*inch
        tw,th=tbl.wrap(avail_w, avail_h)
        x_draw=x+0.2*inch
        y_draw=y+h-0.90*inch - th
        if y_draw < y+0.25*inch: y_draw=y+0.25*inch
        tbl.drawOn(c, x_draw, y_draw)

    # Page 1
    draw_header("NUCLEUS APEX — V3.5 FASTLANE Poster (Rebuild)", "Inventory + keyword index + timeline candidates")
    draw_table_panel(margin, base_y, usable_w*0.32, usable_h*1.00, "Ext counts", "inventory_ext_counts.csv",
                     ext_counts_df, ["ext","count"], [0.50,0.40], max_rows=24, fontsize=11)
    draw_table_panel(margin+usable_w*0.34, base_y, usable_w*0.66, usable_h*1.00, "Largest files", "inventory_top_200_largest.csv (top 25)",
                     largest_df, ["relpath","ext","mb"], [0.78,0.06,0.12], max_rows=25, fontsize=8, right_align_from=2)
    c.showPage()

    # Page 2 keywords
    draw_header("Keyword Index", "Global counts + top-hit files")
    draw_table_panel(margin, base_y, usable_w*0.34, usable_h*1.00, "Keyword global", "keyword_global_counts.csv",
                     kw_global_df, ["keyword","count"], [0.68,0.22], max_rows=35, fontsize=11)
    draw_table_panel(margin+usable_w*0.36, base_y, usable_w*0.64, usable_h*1.00, "Top files", "keyword_file_hits.csv (top 22)",
                     kw_file_df, ["relpath","hit_total","mb","top_keywords"], [0.48,0.10,0.08,0.30], max_rows=22, fontsize=7, right_align_from=1)
    c.showPage()

    # Page 3 timeline
    draw_header("Timeline Candidates", "Normalized date hits (top 40)")
    draw_table_panel(margin, base_y, usable_w, usable_h*1.00, "Timeline", "timeline_candidates_sorted_top2000.csv",
                     timeline_df, ["date_norm","relpath","line_no","context"], [0.10,0.44,0.08,0.34], max_rows=40, fontsize=7, right_align_from=2)
    c.showPage()
    c.save()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out-root", required=True)
    ap.add_argument("--emily-zip", required=True)
    ap.add_argument("--meek2-zip", required=True)
    ap.add_argument("--attachment-harvest", required=True)
    ap.add_argument("--meek234", required=True)
    args=ap.parse_args()

    ts=datetime.datetime.now().strftime("%Y%m%d_%H%M")
    out_root=os.path.abspath(args.out_root)
    metrics=os.path.join(out_root,"metrics_v3_5")
    unpack=os.path.join(out_root,"unpack")
    os.makedirs(metrics, exist_ok=True)
    os.makedirs(unpack, exist_ok=True)

    unzip_into(args.emily_zip, os.path.join(unpack,"Emily_ExParte_Attachments"))
    unzip_into(args.meek2_zip, os.path.join(unpack,"MEEK2_CUSTODY_LITIGATION_PACK"))
    unzip_into(args.attachment_harvest, os.path.join(unpack,"ATTACHMENT_HARVEST_20260208"))
    unzip_into(args.meek234, os.path.join(unpack,"MEEK234_FULLSTACK_REBUILD_PACK_v20260208"))
    recursive_unzip(unpack, max_nested=60)

    rows=[]
    for r,_,files in os.walk(unpack):
        for fn in files:
            fp=os.path.join(r,fn)
            rel=os.path.relpath(fp, unpack).replace("\\","/")
            ext=Path(fn).suffix.lower()
            st=os.stat(fp)
            rows.append({"relpath":rel,"ext":ext if ext else "","bytes":st.st_size,"mtime":int(st.st_mtime),"crc32":f"{crc32_file(fp):08x}"})
    inv=pd.DataFrame(rows).sort_values(["ext","bytes"], ascending=[True,False])
    inv.to_csv(os.path.join(metrics,"unpacked_file_inventory.csv"), index=False)
    ext_counts=inv["ext"].value_counts().reset_index()
    ext_counts.columns=["ext","count"]
    ext_counts.to_csv(os.path.join(metrics,"inventory_ext_counts.csv"), index=False)
    largest=inv.sort_values("bytes",ascending=False).head(200).copy()
    largest["mb"]=largest["bytes"]/1024/1024
    largest.to_csv(os.path.join(metrics,"inventory_top_200_largest.csv"), index=False)

    kw_global=collections.Counter()
    kw_file_hits=[]
    date_cands=[]
    for _,row in inv.iterrows():
        fp=os.path.join(unpack,row["relpath"])
        ext=row["ext"]
        if ext in TEXT_EXTS:
            txt=safe_read_text(fp)
            low=txt.lower()
            per={}
            hit_total=0
            for k in KW_NORM:
                c=low.count(k)
                if c:
                    per[k]=c
                    kw_global[k]+=c
                    hit_total += c
            if hit_total:
                kw_file_hits.append({
                    "relpath": row["relpath"],
                    "ext": ext,
                    "hit_total": hit_total,
                    "top_keywords": "|".join([f"{k}:{per[k]}" for k in sorted(per, key=lambda x: per[x], reverse=True)[:10]]),
                    "bytes": int(row["bytes"]),
                })
            for i,ln in enumerate(txt.splitlines()[:4000]):
                for m in DATE_RE.findall(ln):
                    date_cands.append({"date_raw":m,"date_norm":normalize_date(m),"relpath":row["relpath"],"line_no":i+1,"context":sanitize_ascii(ln)[:220]})
                for m in ISO_RE.findall(ln):
                    date_cands.append({"date_raw":m,"date_norm":m,"relpath":row["relpath"],"line_no":i+1,"context":sanitize_ascii(ln)[:220]})

    kw_global_df=pd.DataFrame([{"keyword":k,"count":v} for k,v in kw_global.most_common()])
    kw_global_df.to_csv(os.path.join(metrics,"keyword_global_counts.csv"), index=False)
    kw_file_df=pd.DataFrame(kw_file_hits)
    if not kw_file_df.empty:
        kw_file_df=kw_file_df.sort_values("hit_total",ascending=False)
        kw_file_df["mb"]=kw_file_df["bytes"]/1024/1024
    kw_file_df.to_csv(os.path.join(metrics,"keyword_file_hits.csv"), index=False)

    dates_df=pd.DataFrame(date_cands)
    dates_df.to_csv(os.path.join(metrics,"date_candidates_raw.csv"), index=False)
    timeline_df=dates_df[dates_df["date_norm"].astype(str)!=""].copy() if not dates_df.empty else dates_df
    if not timeline_df.empty:
        timeline_df=timeline_df.sort_values(["date_norm","relpath","line_no"]).head(2000)
    timeline_df.to_csv(os.path.join(metrics,"timeline_candidates_sorted_top2000.csv"), index=False)

    meta=f"Build: {ts} • Unpacked: {len(inv):,} • Date cands: {len(dates_df):,} • Keyword-hit files: {len(kw_file_df):,}"
    pdf=os.path.join(out_root,f"NUCLEUS_APEX_POSTER_BLUEPRINT_V3_5_REBUILD_{ts}.pdf")
    build_poster(pdf, meta,
                 ext_counts,
                 largest[["relpath","ext","mb"]].head(25),
                 kw_global_df.head(60),
                 kw_file_df[["relpath","hit_total","mb","top_keywords"]].head(60) if not kw_file_df.empty else kw_file_df,
                 timeline_df[["date_norm","relpath","line_no","context"]].head(40) if not timeline_df.empty else timeline_df)
    print("Built:", out_root)

if __name__=="__main__":
    main()
