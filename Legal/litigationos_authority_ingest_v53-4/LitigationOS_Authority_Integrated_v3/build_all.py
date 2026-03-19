#!/usr/bin/env python3
"""
build_all.py — ONE-RUN MAINFRAME ORCHESTRATOR (v53)

Run once on the FINAL merged bundle.
Non-interpretive: no installs, no network calls, no rewriting authority text.

Pipeline:
1) env probe -> outputs/env_report.json
2) authority shards/index/density -> tools/build_authority_shards_v51.py
3) mainframe next-step report -> tools/mainframe_next.py (if present)
4) CyclePack ZIP -> tools/pack_cyclepack_v53.py
"""
import argparse, os, sys, subprocess

def run(cmd):
    print('RUN:', ' '.join(cmd))
    subprocess.check_call(cmd)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--pdf-dir', default='sources/pdfs', help='Folder containing authority PDFs (recursive)')
    ap.add_argument('--out-dir', default='outputs')
    ap.add_argument('--density-threshold', default='2.0')
    ap.add_argument('--unstructured-strategy', default='auto', choices=['auto','fast','hi_res','ocr_only'])
    ap.add_argument('--skip-pack', action='store_true')
    args=ap.parse_args()

    env_probe=os.path.join('tools','env_probe_v53.py')
    if os.path.exists(env_probe):
        run([sys.executable, env_probe, '--out', os.path.join(args.out_dir,'env_report.json')])

    shard_builder=os.path.join('tools','build_authority_shards_v51.py')
    if os.path.exists(shard_builder):
        run([sys.executable, shard_builder,
             '--pdf-dir', args.pdf_dir,
             '--out-dir', args.out_dir,
             '--density-threshold', str(args.density_threshold),
             '--unstructured-strategy', args.unstructured_strategy])

    mf=os.path.join('tools','mainframe_next.py')
    if os.path.exists(mf):
        run([sys.executable, mf])

    if not args.skip_pack:
        pack=os.path.join('tools','pack_cyclepack_v53.py')
        if os.path.exists(pack):
            run([sys.executable, pack, '--base', '.', '--include', 'outputs', '--include', 'docs', '--include', 'tools', '--include', 'manifest.json', '--include', 'manifest.csv'])

if __name__=='__main__':
    main()
