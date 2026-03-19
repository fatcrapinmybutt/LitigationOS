#!/usr/bin/env python3
import argparse, csv, hashlib, json, os, re, sys, time
from pathlib import Path

EXTS = {'.pdf','.doc','.docx','.rtf','.txt','.xlsx','.xls','.csv','.png','.jpg','.jpeg','.eml','.msg','.mp3','.wav','.mp4','.mov','.heic','.m4a'}

def sha256_file(path, max_bytes=1024*1024):
    h = hashlib.sha256()
    try:
        with open(path, 'rb') as f:
            chunk = f.read(max_bytes)
            h.update(chunk)
    except Exception:
        return ''
    return h.hexdigest()

def load_map_csv(p):
    rows = []
    with open(p, 'r', encoding='utf-8') as f:
        r = csv.DictReader(f)
        for row in r:
            rows.append(row)
    return rows

def write_csv(p, rows, header=None):
    if not rows: return
    if header is None: header = list(rows[0].keys())
    with open(p, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=header)
        w.writeheader()
        for row in rows:
            w.writerow(row)

def tokenize_citation(cite):
    # Extract key numbers like 2.116 or 554.139 or 722.23
    if not cite: return []
    toks = re.findall(r'\d+\.\d+|\d{3,}', cite)
    return list(set(toks))

def score_file_to_node(filepath, node, patterns):
    text = filepath.lower()
    score = 0
    reasons = []
    # tag
    tag = (node.get('tag') or '').lower()
    label = (node.get('label') or '').lower()
    cite = node.get('citation') or ''
    # Citation tokens
    for tok in tokenize_citation(cite):
        if tok in text:
            score += 3
            reasons.append(f'citation:{tok}')
    # Tag keyword
    if tag and tag in text:
        score += 1
        reasons.append(f'tag:{tag}')
    # Label keywords
    for w in label.split():
        if len(w) >= 4 and w in text:
            score += 1
            reasons.append(f'label:{w}')
    # Pattern file
    for tagname, pats in patterns.get('tag_patterns', {}).items():
        if tag == tagname.lower():
            for pat in pats:
                if pat.lower() in text:
                    score += 2
                    reasons.append(f'pat:{pat}')
    # Node overrides
    node_pats = patterns.get('node_overrides', {}).get(node['id'], [])
    for pat in node_pats:
        if pat.lower() in text:
            score += 5
            reasons.append(f'node_pat:{pat}')
    return score, reasons

def main():
    ap = argparse.ArgumentParser(description="Index files and merge exhibits into the map CSV.")
    ap.add_argument('--roots', nargs='+', required=True, help='Root folders to scan (e.g., F:\\ E:\\ Z:\\ G:\\MyDrive)')
    ap.add_argument('--map-csv', required=True, help='Path to eternal_codex_mapping_full_STAMPED.csv')
    ap.add_argument('--index-out', default='exhibit_index.csv', help='Where to write the raw file index')
    ap.add_argument('--merged-out', default='eternal_codex_mapping_full_MERGED.csv', help='Output merged CSV for the map')
    ap.add_argument('--patterns', default='patterns.json', help='Optional patterns JSON for better matching')
    ap.add_argument('--max-files', type=int, default=0, help='Limit for testing; 0 = no limit')
    ap.add_argument('--uri', action='store_true', help='Convert file paths to file:/// URIs')
    args = ap.parse_args()

    patterns = {}
    if Path(args.patterns).exists():
        with open(args.patterns,'r',encoding='utf-8') as f:
            patterns = json.load(f)

    # Load map rows
    rows = load_map_csv(args.map_csv)
    nodes = [r for r in rows if r.get('hub','False')=='False']

    # Walk filesystem
    files = []
    count = 0
    for root in args.roots:
        root = os.path.expanduser(root)
        for dirpath, dirnames, filenames in os.walk(root):
            for fn in filenames:
                ext = os.path.splitext(fn)[1].lower()
                if ext not in EXTS: 
                    continue
                full = os.path.join(dirpath, fn)
                try:
                    st = os.stat(full)
                except Exception:
                    continue
                files.append({
                    'path': full,
                    'ext': ext,
                    'size': st.st_size,
                    'mtime': int(st.st_mtime),
                    'sha256': sha256_file(full)
                })
                count += 1
                if args.max_files and count >= args.max_files:
                    break
            if args.max_files and count >= args.max_files:
                break
        if args.max_files and count >= args.max_files:
            break

    # Score mapping
    index_rows = []
    node_exhibits = {n['id']: [] for n in nodes}
    for f in files:
        best = None
        best_score = 0
        best_reasons = []
        for n in nodes:
            s, reasons = score_file_to_node(f['path'], n, patterns)
            if s > best_score:
                best, best_score, best_reasons = n, s, reasons
        guess = best['id'] if best else ''
        path_val = f['path']
        if args.uri:
            # Convert to file:/// URI for Windows paths
            p = Path(path_val)
            path_val = 'file:///' + str(p.as_posix()).lstrip('/').replace(':/',':/')
        index_rows.append({
            'file': path_val,
            'size': f['size'],
            'mtime': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(f['mtime'])),
            'sha256': f['sha256'],
            'guess_node_id': guess,
            'guess_score': best_score,
            'guess_reasons': ';'.join(best_reasons)
        })
        if guess and best_score > 0:
            node_exhibits[guess].append(path_val)

    write_csv(args.index_out, index_rows, header=['file','size','mtime','sha256','guess_node_id','guess_score','guess_reasons'])

    # Merge into map
    merged = []
    for r in rows:
        if r.get('hub','False')=='True':
            merged.append(r); continue
        lid = r['id']
        exhibits = node_exhibits.get(lid, [])
        if exhibits:
            # store JSON array so the updated HTML can render multiple
            r['exhibit'] = json.dumps(exhibits, ensure_ascii=False)
        merged.append(r)

    write_csv(args.merged_out, merged, header=list(rows[0].keys()))
    print(f"Indexed {len(files)} files. Wrote index to {args.index_out}. Wrote merged map to {args.merged_out}.")

if __name__ == '__main__':
    sys.exit(main())
