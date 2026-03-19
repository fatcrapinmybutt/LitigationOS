#!/usr/bin/env python3
"""
LitigationOS_CyclePack_Peak_AllInOne.py

One-file, open-source pipeline to scan input ZIPs / folders, inventory recursively,
convert documents to MD, create line-addressable shards, and emit derived analytics
(ExhibitMatrix, ChronoDB, StatementIndex).

Key features:
- zip-slip safe extraction + caps (prevents zip bombs)
- PDF extraction via pypdf (embedded text only), capped pages + per-PDF timeout
- DOCX extraction via python-docx
- line shards (JSONL) + line-number views
- analytics: OCR flags, keyword hits, regex hits (case nos + dates)
- derived: CaseState, ExhibitMatrix, ChronoDB, StatementIndex

QUOTELOCK note: extracted PDF text is CANDIDATE until independently re-checked vs the source PDF.

Usage examples:
  python LitigationOS_CyclePack_Peak_AllInOne.py --inputs ETERNAL_SUPERGRAPH_MASTER.zip --out /tmp/out --run-all
  python LitigationOS_CyclePack_Peak_AllInOne.py --inputs some_folder --out ./out --run-all
"""

from __future__ import annotations
import os, re, json, csv, zipfile, hashlib, shutil, argparse, signal, time
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict

try:
    import pandas as pd
except Exception:
    pd = None

try:
    from pypdf import PdfReader
    PYPDF_OK = True
except Exception:
    PdfReader = None
    PYPDF_OK = False

try:
    import docx
    DOCX_OK = True
except Exception:
    docx = None
    DOCX_OK = False

ALLOW_EXTS = {'.pdf','.doc','.docx','.rtf','.txt','.md','.png','.jpg','.jpeg','.tif','.tiff','.zip','.json','.jsonl','.csv','.html','.htm','.wav','.mp3','.m4a','.mp4'}

CASE_PAT = re.compile(r"\b\d{2,4}-\d{3,6}-[A-Z]{2,4}\b")
DATE_PATS = [
    re.compile(r"\b\d{4}-\d{2}-\d{2}\b"),
    re.compile(r"\b\d{1,2}/\d{1,2}/\d{2,4}\b"),
    re.compile(r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2},\s+\d{4}\b", re.IGNORECASE),
]

KEYWORDS = [
    'mcneill','watson','emily','albert','lori',
    'ex parte','exparte','parenting time','custody',
    'ppo','personal protection order','show cause',
    'contempt','healthwest','drug screen','drug test',
    'mental health','evaluation','suspension','restricted',
    'hearing','order','motion','objection','appeal','court of appeals','supreme court','jtc','judicial tenure commission'
]

STMT_TERMS = [
    'alleg','claim','accus','violation','violat','threat','meth','drug','stalk','harass',
    'jail','sentenc','contempt','ex parte','suspend','withhold','denied','bias','perjur','hearsay'
]

def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def ts_utc() -> str:
    return datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')

def sha1(s: str) -> str:
    return hashlib.sha1(s.encode('utf-8')).hexdigest()

def out_id(seed: str) -> str:
    return sha1(seed)

def file_kind(ext: str) -> str:
    e = ext.lower()
    if e == '.pdf': return 'pdf'
    if e == '.zip': return 'archive'
    if e in ('.doc','.docx','.rtf'): return 'word'
    if e in ('.png','.jpg','.jpeg','.tif','.tiff'): return 'image'
    if e in ('.txt','.md','.html','.htm'): return 'text'
    if e in ('.csv','.json','.jsonl'): return 'data'
    if e in ('.wav','.mp3','.m4a'): return 'audio'
    if e == '.mp4': return 'video'
    return 'other'

def append_jsonl(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a', encoding='utf-8') as f:
        f.write(json.dumps(obj, ensure_ascii=False) + '\n')

def safe_extract_zip(zip_path: Path, out_dir: Path, ledger: Path, cap_members: int, cap_uncompressed_bytes: int) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    members_seen = 0
    uncompressed_seen = 0
    status = 'OK'
    with zipfile.ZipFile(zip_path, 'r') as z:
        bad = z.testzip()
        if bad is not None:
            append_jsonl(ledger, {'ts': utc_now(), 'event': 'zip_bad_member', 'zip': str(zip_path), 'member': bad})
        for info in z.infolist():
            members_seen += 1
            uncompressed_seen += int(info.file_size or 0)
            if members_seen > cap_members:
                status = 'CAP_MAX_FILES'
                append_jsonl(ledger, {'ts': utc_now(), 'event': 'cap_hit_max_files', 'cap': cap_members, 'zip': str(zip_path)})
                break
            if uncompressed_seen > cap_uncompressed_bytes:
                status = 'CAP_MAX_SIZE'
                append_jsonl(ledger, {'ts': utc_now(), 'event': 'cap_hit_max_uncompressed', 'cap_bytes': cap_uncompressed_bytes, 'zip': str(zip_path)})
                break
            if '..' in Path(info.filename).parts:
                append_jsonl(ledger, {'ts': utc_now(), 'event': 'zip_slip_blocked', 'zip': str(zip_path), 'member': info.filename})
                continue
            z.extract(info, out_dir)
    return {'status': status, 'members_seen': members_seen, 'uncompressed_seen': uncompressed_seen}

class _Timeout(Exception):
    pass

def _alarm_handler(signum, frame):
    raise _Timeout()

def parse_date_to_iso(raw: str):
    raw = raw.strip()
    m = re.match(r'^([0-9]{4})-([0-9]{2})-([0-9]{2})$', raw)
    if m:
        return raw, {'method': 'ymd', 'guess': False}
    m = re.match(r'^([0-9]{1,2})/([0-9]{1,2})/([0-9]{2,4})$', raw)
    if m:
        mm, dd, yy = int(m.group(1)), int(m.group(2)), m.group(3)
        if len(yy) == 2:
            yyi = int(yy)
            yyyy = 2000 + yyi if yyi <= 69 else 1900 + yyi
            guess = True
        else:
            yyyy = int(yy)
            guess = False
        return f'{yyyy:04d}-{mm:02d}-{dd:02d}', {'method': 'mdy', 'guess': guess}
    m = re.match(r'^(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+([0-9]{1,2}),\s+([0-9]{4})$', raw, re.IGNORECASE)
    if m:
        mon = m.group(1).lower()[:3]
        dd = int(m.group(2)); yyyy = int(m.group(3))
        months = {'jan':1,'feb':2,'mar':3,'apr':4,'may':5,'jun':6,'jul':7,'aug':8,'sep':9,'oct':10,'nov':11,'dec':12}
        mm = months.get(mon, 0)
        if mm:
            return f'{yyyy:04d}-{mm:02d}-{dd:02d}', {'method':'monthname','guess':False}
    return None, {'method':'unparsed','guess':True}

def zip_folder(folder: Path, zip_path: Path) -> None:
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for root, dirs, files in os.walk(folder):
            for fn in files:
                full = Path(root) / fn
                arc = full.relative_to(folder.parent)
                z.write(full, arcname=str(arc))
    with zipfile.ZipFile(zip_path, 'r') as z:
        bad = z.testzip()
        if bad is not None:
            raise RuntimeError(f'Bad zip member: {bad}')

def run_delta1(inputs: list[Path], out_dir: Path, caps_members: int, caps_bytes: int):
    run_id = f'CYCLEPACK_{ts_utc()}_PEAK'
    root = out_dir / run_id
    for d in ['00_RUN','01_INVENTORY','02_UNPACKED','03_SAMPLES','04_INDEX']:
        (root/d).mkdir(parents=True, exist_ok=True)
    ledger = root/'00_RUN'/'RUN_LEDGER.jsonl'
    append_jsonl(ledger, {'ts': utc_now(), 'event': 'run_start', 'run_id': run_id, 'inputs': [str(p) for p in inputs]})

    unpacked_roots = []
    for p in inputs:
        if p.is_file() and p.suffix.lower()=='.zip':
            outp = root/'02_UNPACKED'/re.sub(r'[^A-Za-z0-9_.-]+','_',p.stem)
            stats = safe_extract_zip(p, outp, ledger, caps_members, caps_bytes)
            unpacked_roots.append(outp)
            append_jsonl(ledger, {'ts': utc_now(), 'event': 'unpack_done', 'zip': str(p), **stats, 'out': str(outp)})
        elif p.is_dir():
            unpacked_roots.append(p)

    rows=[]
    counts=defaultdict(int)
    for base in unpacked_roots:
        for dirpath, dirnames, filenames in os.walk(base):
            for fn in filenames:
                fp = Path(dirpath)/fn
                ext = fp.suffix.lower()
                if ext not in ALLOW_EXTS:
                    continue
                try:
                    st = fp.stat()
                except Exception:
                    counts['errors'] += 1
                    continue
                rel = str(fp.relative_to(base))
                fid = sha1(f'{base}|{rel}|{st.st_size}|{int(st.st_mtime)}')
                k = file_kind(ext)
                rows.append({'file_id': fid,'root': str(base),'relpath': rel,'abspath': str(fp),'ext': ext,'kind': k,'size_bytes': st.st_size,
                             'mtime_utc': datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).replace(microsecond=0).isoformat()})
                counts['files_total'] += 1
                counts[f'kind_{k}'] += 1

    mf_csv = root/'01_INVENTORY'/'manifest_files.csv'
    mf_jsonl = root/'01_INVENTORY'/'manifest_files.jsonl'
    if rows:
        with mf_csv.open('w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader()
            for r in rows: w.writerow(r)
        with mf_jsonl.open('w', encoding='utf-8') as f:
            for r in rows: f.write(json.dumps(r, ensure_ascii=False)+'\n')
    else:
        mf_csv.write_text('file_id,root,relpath,abspath,ext,kind,size_bytes,mtime_utc\n', encoding='utf-8')
        mf_jsonl.write_text('', encoding='utf-8')

    # samples
    samples_pdf=[]; samples_text=[]
    if PYPDF_OK:
        pdfs = [r for r in rows if r['kind']=='pdf']
        pdfs = sorted(pdfs, key=lambda r: r['mtime_utc'], reverse=True)[:25]
        for r in pdfs:
            try:
                reader = PdfReader(r['abspath'])
                txt = ''
                if reader.pages:
                    try: txt = reader.pages[0].extract_text() or ''
                    except Exception: txt = ''
                samples_pdf.append({'file_id': r['file_id'], 'abspath': r['abspath'], 'pages': len(reader.pages), 'first_page_text': (txt or '')[:4000]})
            except Exception:
                continue
    texts = [r for r in rows if r['kind']=='text']
    texts = sorted(texts, key=lambda r: r['mtime_utc'], reverse=True)[:25]
    for r in texts:
        try:
            head = Path(r['abspath']).read_text(encoding='utf-8', errors='replace')[:4000]
        except Exception:
            head = Path(r['abspath']).read_text(errors='replace')[:4000]
        samples_text.append({'file_id': r['file_id'], 'abspath': r['abspath'], 'head': head})

    (root/'03_SAMPLES'/'pdf_firstpage_samples.jsonl').write_text('\n'.join(json.dumps(x,ensure_ascii=False) for x in samples_pdf)+'\n', encoding='utf-8')
    (root/'03_SAMPLES'/'text_head_samples.jsonl').write_text('\n'.join(json.dumps(x,ensure_ascii=False) for x in samples_text)+'\n', encoding='utf-8')

    html=['<!doctype html><meta charset="utf-8"><title>CyclePack Index</title>', f'<h1>{run_id} — Index</h1>', '<h2>Counts</h2><ul>']
    for k,v in sorted(counts.items()): html.append(f'<li>{k}: {v}</li>')
    html.append('</ul>')
    (root/'04_INDEX'/'index.html').write_text('\n'.join(html), encoding='utf-8')

    (root/'00_RUN'/'RUN.json').write_text(json.dumps({'run_id': run_id,'finished_utc': utc_now(),'counts': dict(counts),
                                                     'caps': {'max_zip_members': caps_members,'max_uncompressed_bytes': caps_bytes},
                                                     'notes':['PDF samples are embedded-text only.']}, indent=2, ensure_ascii=False), encoding='utf-8')
    return run_id, root

def run_delta2(delta1_root: Path, out_dir: Path, max_pages_per_pdf: int, pdf_timeout_seconds: int):
    run_id = f'CYCLEPACK_{ts_utc()}_DELTA2'
    root = out_dir / run_id
    for d in ['00_RUN','01_INVENTORY','05_EXTRACT/md','06_SHARDS','07_ANALYTICS','08_DERIVED','09_INDEX']:
        (root/d).mkdir(parents=True, exist_ok=True)
    ledger = root/'00_RUN'/'RUN_LEDGER.jsonl'
    append_jsonl(ledger, {'ts': utc_now(),'event':'run_start','run_id':run_id,'source_delta1': str(delta1_root),
                          'max_pages_per_pdf': max_pages_per_pdf,'pdf_timeout_seconds': pdf_timeout_seconds})

    mf_csv = delta1_root/'01_INVENTORY'/'manifest_files.csv'
    mf_jsonl = delta1_root/'01_INVENTORY'/'manifest_files.jsonl'
    shutil.copy2(mf_csv, root/'01_INVENTORY'/'manifest_files.csv')
    shutil.copy2(mf_jsonl, root/'01_INVENTORY'/'manifest_files.jsonl')

    rows=[]
    with mf_jsonl.open('r', encoding='utf-8') as f:
        for line in f:
            line=line.strip()
            if line: rows.append(json.loads(line))

    md_dir = root/'05_EXTRACT'/'md'
    shards_dir = root/'06_SHARDS'
    outputs=[]; pdf_stats=[]; ocr_required=[]; timeouts=[]

    signal.signal(signal.SIGALRM, _alarm_handler)

    for r in rows:
        kind=r['kind']; ext=r['ext'].lower(); src=Path(r['abspath']); fid=r['file_id']
        out_md = md_dir/f'{fid}.md'
        try:
            if kind=='pdf' and PYPDF_OK:
                t0=time.time()
                signal.alarm(pdf_timeout_seconds)
                reader=PdfReader(str(src))
                pages_total=len(reader.pages)
                parts=[]; total_chars=0; pages_done=0
                for i, page in enumerate(reader.pages, start=1):
                    if i>max_pages_per_pdf: break
                    try: txt = page.extract_text() or ''
                    except Exception: txt = ''
                    txt = (txt or '').replace('\r\n','\n').replace('\r','\n').strip()
                    total_chars += len(txt)
                    parts.append(f'## Page {i}\n{txt}\n')
                    pages_done += 1
                signal.alarm(0)
                out_md.write_text('\n'.join(parts), encoding='utf-8')
                pdf_stats.append({'file_id': fid,'src_abspath': str(src),'pages': pages_total,'pages_extracted': pages_done,
                                  'total_chars_extracted': total_chars,'timing_seconds': round(time.time()-t0,3)})
                if total_chars < 200:
                    ocr_required.append({'file_id': fid,'src_abspath': str(src),'pages': pages_total,'total_chars': total_chars,'reason':'low_or_partial_extracted_text'})
            elif kind=='word' and ext=='.docx' and DOCX_OK:
                d = docx.Document(str(src))
                lines=[p.text.rstrip() for p in d.paragraphs if (p.text or '').rstrip()]
                out_md.write_text('\n\n'.join(lines)+'\n', encoding='utf-8')
            elif kind=='text':
                try: out_md.write_text(src.read_text(encoding='utf-8', errors='replace'), encoding='utf-8')
                except Exception: out_md.write_text(src.read_text(errors='replace'), encoding='utf-8')
            else:
                continue

            st = out_md.stat()
            outputs.append({'output_id': out_id(f'convert|{fid}|{st.st_size}|{int(st.st_mtime)}'), 'source_file_id': fid,'stage':'convert','src_abspath': str(src),
                            'abspath': str(out_md),'kind':'md','size_bytes': st.st_size, 'mtime_utc': datetime.fromtimestamp(st.st_mtime,tz=timezone.utc).replace(microsecond=0).isoformat()})
        except _Timeout:
            signal.alarm(0)
            timeouts.append({'file_id': fid,'src_abspath': str(src),'reason':'pdf_extract_timeout','timeout_seconds': pdf_timeout_seconds})
            out_md.write_text(f'# PDF extraction timed out\n\nSource: {src}\nTimeoutSeconds: {pdf_timeout_seconds}\nMaxPagesAttempted: {max_pages_per_pdf}\n', encoding='utf-8')
            st = out_md.stat()
            outputs.append({'output_id': out_id(f'convert_timeout|{fid}|{st.st_size}|{int(st.st_mtime)}'), 'source_file_id': fid,'stage':'convert_timeout','src_abspath': str(src),
                            'abspath': str(out_md),'kind':'md','size_bytes': st.st_size, 'mtime_utc': datetime.fromtimestamp(st.st_mtime,tz=timezone.utc).replace(microsecond=0).isoformat()})
        except Exception as e:
            signal.alarm(0)
            append_jsonl(ledger, {'ts': utc_now(), 'event': 'convert_error', 'src': str(src), 'err': repr(e)})

    # manifests
    (root/'01_INVENTORY'/'manifest_outputs.jsonl').write_text('\n'.join(json.dumps(x,ensure_ascii=False) for x in outputs)+'\n', encoding='utf-8')
    if pd is not None:
        pd.DataFrame(outputs).to_csv(root/'01_INVENTORY'/'manifest_outputs.csv', index=False)

    # shards
    shards_path = shards_dir/'shards.jsonl'
    if shards_path.exists(): shards_path.unlink()
    shard_count=0
    md_files = sorted(md_dir.glob('*.md'))
    for mdp in md_files:
        fid = mdp.stem
        text = mdp.read_text(encoding='utf-8', errors='replace')
        lines = text.splitlines()
        with (shards_dir/f'{fid}.lines.txt').open('w', encoding='utf-8') as f:
            for i, ln in enumerate(lines, start=1):
                f.write(f'{i:06d}  {ln}\n')
        with shards_path.open('a', encoding='utf-8') as f:
            for i, ln in enumerate(lines, start=1):
                ln = ln.rstrip()
                if not ln: continue
                sid = out_id(f'shard|{fid}|L{i}|{ln[:120]}')
                f.write(json.dumps({'shard_id': sid,'source_file_id': fid,'line_no': i,'text': ln}, ensure_ascii=False)+'\n')
                shard_count += 1

    # analytics: pdf stats + ocr + timeouts
    if pd is not None:
        pd.DataFrame(pdf_stats).to_csv(root/'07_ANALYTICS'/'pdf_text_stats.csv', index=False)
        pd.DataFrame(ocr_required).to_csv(root/'07_ANALYTICS'/'ocr_required.csv', index=False)
        pd.DataFrame(timeouts).to_csv(root/'07_ANALYTICS'/'pdf_extract_timeouts.csv', index=False)

    # keyword + regex hits
    keyword_rows=[]; regex_hits=[]; case_hits=defaultdict(int)
    for mdp in md_files:
        fid = mdp.stem
        text = mdp.read_text(encoding='utf-8', errors='replace')
        low = text.lower()
        for kw in KEYWORDS:
            c = low.count(kw.lower())
            if c:
                keyword_rows.append({'file_id': fid,'keyword': kw,'count': c,'md_path': str(mdp)})
        for m in CASE_PAT.findall(text):
            case_hits[m] += 1
            regex_hits.append({'file_id': fid,'type':'case_no','value': m,'md_path': str(mdp)})
        for pat in DATE_PATS:
            for m in pat.findall(text):
                regex_hits.append({'file_id': fid,'type':'date','value': m,'md_path': str(mdp)})
    if pd is not None:
        pd.DataFrame(keyword_rows).to_csv(root/'07_ANALYTICS'/'keyword_hits.csv', index=False)
        pd.DataFrame(regex_hits).to_csv(root/'07_ANALYTICS'/'regex_hits.csv', index=False)

    top_cases = sorted(case_hits.items(), key=lambda kv: kv[1], reverse=True)[:25]

    # CASE_STATE
    cs=[]
    cs.append(f'[CASE_STATE] {run_id}')
    cs.append(f'ConvertedToMD: {len(md_files)}; Shards: {shard_count:,}')
    cs.append(f'PDF_extract_timeouts: {len(timeouts)}')
    cs.append(f'OCR_REQUIRED_PDFs: {len(ocr_required)}')
    cs.append('CaseNos_detected_top:')
    for c,n in top_cases[:10]: cs.append(f'  - {c} (hits={n})')
    (root/'08_DERIVED'/'CASE_STATE.txt').write_text('\n'.join(cs[:25])+'\n', encoding='utf-8')

    # blockers
    blk=['# Blockers & Acquisition Plan (Δ2)\n',
         f'- pypdf extraction capped pages: {max_pages_per_pdf}\n',
         f'- per-PDF timeout: {pdf_timeout_seconds}s\n',
         '\n## OCR / full-text acquire plan\n',
         '- ocrmypdf (pip) to add text layer to scanned PDFs\n',
         '- Docling/Marker fallback for PDF→MD when pypdf struggles\n']
    (root/'08_DERIVED'/'BLOCKERS_AcquirePlan.md').write_text(''.join(blk), encoding='utf-8')

    (root/'00_RUN'/'RUN.json').write_text(json.dumps({'run_id': run_id,'finished_utc': utc_now(),
                                                     'counts': {'md_converted': len(md_files),'shards': shard_count,'pdfs': len(pdf_stats),
                                                                'ocr_flagged_pdfs': len(ocr_required),'pdf_extract_timeouts': len(timeouts)},
                                                     'top_case_numbers': [{'case_no': c,'hits': n} for c,n in top_cases],
                                                     'notes':['PDF extraction embedded-only; capped pages + timeout.']}, indent=2, ensure_ascii=False), encoding='utf-8')
    return run_id, root

def run_delta3(delta2_root: Path, out_dir: Path):
    if pd is None:
        raise RuntimeError('pandas_required_for_delta3')
    run_id = f'CYCLEPACK_{ts_utc()}_DELTA3'
    root = out_dir / run_id
    for d in ['00_RUN','08_DERIVED','09_INDEX']:
        (root/d).mkdir(parents=True, exist_ok=True)

    manifest_df = pd.read_csv(delta2_root/'01_INVENTORY'/'manifest_files.csv')
    regex_path = delta2_root/'07_ANALYTICS'/'regex_hits.csv'
    kw_path = delta2_root/'07_ANALYTICS'/'keyword_hits.csv'
    regex_df = pd.read_csv(regex_path) if regex_path.exists() else pd.DataFrame(columns=['file_id','type','value','md_path'])
    kw_df = pd.read_csv(kw_path) if kw_path.exists() else pd.DataFrame(columns=['file_id','keyword','count','md_path'])

    case_df = regex_df[regex_df['type']=='case_no'].copy()
    case_df['hits']=1
    dominant = (case_df.groupby(['file_id','value'])['hits'].sum().reset_index()
                .sort_values(['file_id','hits'], ascending=[True,False]))
    dom_top = dominant.groupby('file_id').first().reset_index().rename(columns={'value':'dominant_case_no','hits':'dominant_case_hits'})

    kw_sum = kw_df.groupby(['file_id','keyword'])['count'].sum().reset_index() if not kw_df.empty else pd.DataFrame(columns=['file_id','keyword','count'])
    topkw = (kw_sum.sort_values(['file_id','count'], ascending=[True,False]).groupby('file_id').head(5)) if not kw_sum.empty else pd.DataFrame(columns=['file_id','keyword','count'])
    topkw_join = topkw.groupby('file_id').apply(lambda g: '; '.join([f"{row.keyword}={int(row['count'])}" for _,row in g.iterrows()])).reset_index(name='top_keywords') if not topkw.empty else pd.DataFrame(columns=['file_id','top_keywords'])

    ex_df = manifest_df.merge(dom_top[['file_id','dominant_case_no','dominant_case_hits']], on='file_id', how='left')
    ex_df = ex_df.merge(topkw_join, on='file_id', how='left')
    def exhibit_kind(row):
        k=row.get('kind','')
        if k=='pdf': return 'PDF_Document'
        if k=='word': return 'Word_Document'
        if k=='text': return 'Text_Note'
        if k=='data': return 'Data_File'
        return k or 'Unknown'
    ex_df['exhibit_kind'] = ex_df.apply(exhibit_kind, axis=1)
    ex_sorted = ex_df.sort_values(['mtime_utc','size_bytes'], ascending=[False,False]).reset_index(drop=True)
    ex_sorted['exhibit_id'] = ex_sorted.index.map(lambda i: f'EX_{i+1:04d}')
    ex_sorted.to_csv(root/'08_DERIVED'/'EXHIBIT_MATRIX.csv', index=False)

    # ChronoDB
    md_dir = delta2_root/'05_EXTRACT'/'md'
    date_df = regex_df[regex_df['type']=='date'].copy()
    date_map=defaultdict(list)
    for _, row in date_df.iterrows():
        date_map[str(row['file_id'])].append(str(row['value']))
    chrono=[]
    max_events_total=20000; max_events_per_file=400
    for mdp in md_dir.glob('*.md'):
        fid=mdp.stem
        if fid not in date_map: continue
        dates_unique=list(dict.fromkeys(date_map[fid]))
        text=mdp.read_text(encoding='utf-8', errors='replace')
        for d in dates_unique:
            start=0; occ=0
            while True:
                idx=text.find(d, start)
                if idx==-1: break
                occ += 1
                a=max(0, idx-160); b=min(len(text), idx+160+len(d))
                snippet=text[a:b].replace('\n',' ')
                iso, meta = parse_date_to_iso(d)
                chrono.append({'event_id': out_id(f'chrono|{fid}|{d}|{idx}'),'file_id': fid,'date_raw': d,'date_iso_guess': iso or '',
                               'date_meta': json.dumps(meta),'snippet': snippet,'md_path': str(mdp)})
                start = idx+len(d)
                if occ>=max_events_per_file or len(chrono)>=max_events_total: break
            if len(chrono)>=max_events_total: break
        if len(chrono)>=max_events_total: break
    pd.DataFrame(chrono).to_csv(root/'08_DERIVED'/'CHRONODB.csv', index=False)

    # StatementIndex
    kw_total = kw_df.groupby('file_id')['count'].sum().reset_index().sort_values('count', ascending=False) if not kw_df.empty else pd.DataFrame(columns=['file_id','count'])
    top_file_ids = kw_total['file_id'].head(30).tolist() if not kw_total.empty else []
    shards_dir = delta2_root/'06_SHARDS'
    stmt=[]; max_stmt=20000
    for fid in top_file_ids:
        ln_view = shards_dir/f'{fid}.lines.txt'
        if not ln_view.exists(): continue
        with ln_view.open('r', encoding='utf-8', errors='replace') as f:
            for line in f:
                try:
                    ln_no=int(line[:6]); content=line[8:].rstrip()
                except Exception:
                    continue
                low=content.lower()
                if any(t in low for t in STMT_TERMS):
                    stmt.append({'stmt_id': out_id(f'stmt|{fid}|L{ln_no}|{content[:80]}'),'file_id': fid,'line_no': ln_no,'text': content,'line_view': str(ln_view)})
                if len(stmt)>=max_stmt: break
        if len(stmt)>=max_stmt: break
    pd.DataFrame(stmt).to_csv(root/'08_DERIVED'/'STATEMENT_INDEX.csv', index=False)

    (root/'00_RUN'/'RUN.json').write_text(json.dumps({'run_id': run_id,'finished_utc': utc_now(),
                                                     'counts': {'exhibit_rows': int(ex_sorted.shape[0]),'chrono_events': len(chrono),'statement_rows': len(stmt),
                                                                'dominant_case_assigned_files': int(dom_top.shape[0])}}, indent=2, ensure_ascii=False), encoding='utf-8')
    return run_id, root

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--inputs', nargs='+', required=True, help='ZIPs and/or folders to scan')
    ap.add_argument('--out', required=True, help='Output directory')
    ap.add_argument('--run-all', action='store_true', help='Run Δ1 + Δ2 + Δ3')
    ap.add_argument('--caps-max-zip-members', type=int, default=50000)
    ap.add_argument('--caps-max-uncompressed-bytes', type=int, default=5*1024**3)
    ap.add_argument('--max-pages-per-pdf', type=int, default=12)
    ap.add_argument('--pdf-timeout-seconds', type=int, default=10)
    args = ap.parse_args()

    out_dir = Path(args.out).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    inputs = [Path(p).expanduser().resolve() for p in args.inputs]
    for p in inputs:
        if not p.exists():
            raise SystemExit(f'Missing input: {p}')

    d1_id, d1_root = run_delta1(inputs, out_dir, args.caps_max_zip_members, args.caps_max_uncompressed_bytes)
    zip_folder(d1_root, out_dir/(d1_id+'.zip'))
    if args.run_all:
        d2_id, d2_root = run_delta2(d1_root, out_dir, args.max_pages_per_pdf, args.pdf_timeout_seconds)
        zip_folder(d2_root, out_dir/(d2_id+'.zip'))
        if pd is None:
            print('[WARN] pandas missing; Δ3 skipped')
        else:
            d3_id, d3_root = run_delta3(d2_root, out_dir)
            zip_folder(d3_root, out_dir/(d3_id+'.zip'))
    print('Done. Output:', out_dir)

if __name__ == '__main__':
    main()
