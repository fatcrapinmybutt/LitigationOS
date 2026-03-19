#!/usr/bin/env python3
"""
merge_versions_final_v52.py — FINAL CONSOLIDATION BUILDER (v52)

Goal
- Operator does NOT run intermediate versions.
- This tool merges many version ZIPs (litigationos_authority_ingest_v*.zip) into ONE FINAL bundle
  with deterministic 'latest-wins' path resolution and a provenance manifest.

Inputs
- --in-dir : folder containing v*.zip files (or any zip paths)
- --pattern: glob pattern (default: litigationos_authority_ingest_v*.zip)
- --out-zip: output final zip path (default: litigationos_authority_ingest_FINAL.zip)

Outputs inside FINAL zip
- /FINAL/ (merged tree)
- FINAL_MERGE_MANIFEST.json : for every file path, which source zip provided it + sha256 + size
- FINAL_ZIPS_ORDER.json : zip ordering used
- build_all.py : one-run orchestrator skeleton (calls shard builder, docket ingest, deadlines, runbook)

Non-destructive
- Does not modify source zips.
- Does not rewrite legal text.

Determinism
- Sorts zips by parsed v-number (ascending), then applies 'last writer wins' (highest v overwrites).
"""
import argparse, os, re, glob, zipfile, json, hashlib, shutil, datetime, sys, tempfile

VNUM_RX=re.compile(r"_v(\d+)\.zip$", re.IGNORECASE)

def sha256_bytes(b):
    h=hashlib.sha256(); h.update(b); return h.hexdigest()

def sha256_file(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for ch in iter(lambda:f.read(1024*1024), b''):
            h.update(ch)
    return h.hexdigest()

def parse_vnum(name):
    m=VNUM_RX.search(name.replace('\\','/'))
    return int(m.group(1)) if m else -1

def list_zips(in_dir, pattern):
    paths=glob.glob(os.path.join(in_dir, pattern))
    paths=sorted(paths, key=lambda p: (parse_vnum(os.path.basename(p)), os.path.basename(p).lower()))
    return paths

def safe_mkdir(p): os.makedirs(p, exist_ok=True)

def extract_zip_to(zip_path, out_dir):
    with zipfile.ZipFile(zip_path,'r') as z:
        z.extractall(out_dir)

def walk_files(root):
    out=[]
    for r,ds,fs in os.walk(root):
        for fn in fs:
            p=os.path.join(r,fn)
            rel=os.path.relpath(p, root).replace('\\','/')
            out.append((rel,p))
    return sorted(out)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--in-dir', required=True)
    ap.add_argument('--pattern', default='litigationos_authority_ingest_v*.zip')
    ap.add_argument('--out-zip', default='litigationos_authority_ingest_FINAL.zip')
    ap.add_argument('--root-prefix', default='FINAL')
    args=ap.parse_args()

    in_dir=os.path.abspath(args.in_dir)
    if not os.path.isdir(in_dir):
        raise SystemExit('in-dir not found: '+in_dir)

    zips=list_zips(in_dir, args.pattern)
    if not zips:
        raise SystemExit('No zips found matching pattern in '+in_dir)

    tmp=tempfile.mkdtemp(prefix='merge_v52_')
    merged=os.path.join(tmp,'merged')
    safe_mkdir(merged)

    merge_manifest={}
    order=[]
    for zp in zips:
        order.append({'zip': os.path.abspath(zp), 'sha256': sha256_file(zp), 'vnum': parse_vnum(os.path.basename(zp))})
        ex=os.path.join(tmp, 'ex_'+str(len(order)))
        safe_mkdir(ex)
        extract_zip_to(zp, ex)

        # detect bundle root inside extracted zip (first folder with tools/ and authority_store.sqlite)
        bundle_root=None
        for r,ds,fs in os.walk(ex):
            if 'authority_store.sqlite' in fs and 'tools' in ds:
                bundle_root=r; break
        if bundle_root is None:
            # fallback: merge everything
            bundle_root=ex

        for rel, p in walk_files(bundle_root):
            # ignore any previous FINAL merge artifacts if present
            if rel.startswith('FINAL/') or rel.startswith(args.root_prefix+'/'):
                continue
            dst=os.path.join(merged, rel)
            safe_mkdir(os.path.dirname(dst))
            shutil.copy2(p, dst)
            merge_manifest[rel]={
                'from_zip': os.path.abspath(zp),
                'from_vnum': parse_vnum(os.path.basename(zp)),
                'size_bytes': os.path.getsize(p),
                'sha256': sha256_file(p)
            }

    # Ensure build_all.py exists (latest-wins if already present)
    build_all=os.path.join(merged,'build_all.py')
    if not os.path.exists(build_all):
        open(build_all,'w',encoding='utf-8').write("""#!/usr/bin/env python3
\"\"\"build_all.py — ONE-RUN ORCHESTRATOR (FINAL)

This script is generated/packaged by merge_versions_final_v52.py.
It is intentionally conservative and non-interpretive.

What it should do (when you run FINAL):
1) Locate/ingest authority PDFs (from your mounted folders or provided --pdf-dir)
2) Build authority shards + index + density report:
   - python tools/build_authority_shards_v51.py --pdf-dir <...> --out-dir outputs
3) (Optional) Docket ingest + candidate deadlines:
   - python tools/docket_ingest_*.py ...
   - python tools/deadlines_from_docket_v49.py ...
4) Run mainframe_next.py to generate runbook + next-best-step report

You can extend this orchestrator as the mainframe grows.
\"\"\"
import argparse, os, sys, subprocess

def run(cmd):
    print('RUN:', ' '.join(cmd))
    subprocess.check_call(cmd)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--pdf-dir', default='sources/pdfs')
    ap.add_argument('--out-dir', default='outputs')
    args=ap.parse_args()

    # Authority shards
    shard_builder=os.path.join('tools','build_authority_shards_v51.py')
    if os.path.exists(shard_builder):
        run([sys.executable, shard_builder, '--pdf-dir', args.pdf_dir, '--out-dir', args.out_dir])

    # Mainframe next
    mf=os.path.join('tools','mainframe_next.py')
    if os.path.exists(mf):
        run([sys.executable, mf])

if __name__=='__main__':
    main()
""")
        os.chmod(build_all,0o755)

    # Write merge artifacts
    merge_meta={
        'generated_utc': datetime.datetime.utcnow().isoformat()+'Z',
        'zip_count': len(zips),
        'pattern': args.pattern,
        'root_prefix': args.root_prefix,
        'order': order
    }
    open(os.path.join(merged,'FINAL_ZIPS_ORDER.json'),'w',encoding='utf-8').write(json.dumps(merge_meta, indent=2))
    open(os.path.join(merged,'FINAL_MERGE_MANIFEST.json'),'w',encoding='utf-8').write(json.dumps({
        'generated_utc': merge_meta['generated_utc'],
        'files': merge_manifest
    }, indent=2))

    # Build final zip
    out_zip=os.path.abspath(args.out_zip)
    if os.path.exists(out_zip):
        os.remove(out_zip)
    with zipfile.ZipFile(out_zip,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for rel, p in walk_files(merged):
            z.write(p, arcname=os.path.join(args.root_prefix, rel))
    print('OK ->', out_zip)

if __name__=='__main__':
    main()
