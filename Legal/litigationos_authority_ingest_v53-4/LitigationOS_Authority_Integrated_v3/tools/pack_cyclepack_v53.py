#!/usr/bin/env python3
"""
pack_cyclepack_v53.py — CyclePack Packager (v53)
Packages outputs/docs/tools/manifest.* into a single ZIP for downstream ingestion.
"""
import argparse, os, zipfile, datetime

def add_path(z, base, path):
    if os.path.isdir(path):
        for r,ds,fs in os.walk(path):
            for fn in fs:
                p=os.path.join(r,fn)
                rel=os.path.relpath(p, base).replace('\\','/')
                z.write(p, rel)
    elif os.path.exists(path):
        rel=os.path.relpath(path, base).replace('\\','/')
        z.write(path, rel)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--base', default='.', help='base path for relative entries')
    ap.add_argument('--include', action='append', default=[])
    ap.add_argument('--out', default='')
    args=ap.parse_args()

    base=os.path.abspath(args.base)
    inc=args.include or ['outputs','docs','tools','manifest.json','manifest.csv']

    if not args.out:
        ts=datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
        out=os.path.join(base,'outputs',f'CyclePack_FINAL_{ts}.zip')
    else:
        out=os.path.abspath(args.out)

    os.makedirs(os.path.dirname(out), exist_ok=True)

    with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for p in inc:
            add_path(z, base, os.path.join(base,p))
    print('OK ->', out)

if __name__=='__main__':
    main()
