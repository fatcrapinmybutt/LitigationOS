#!/usr/bin/env python3
"""
env_probe_v53.py — Environment Probe (v53)

Non-interpretive: no network calls, no installs. Detection only.
Writes outputs/env_report.json by default.
"""
import argparse, json, platform, shutil, sys, datetime, os

def can_import(mod):
    try:
        __import__(mod)
        return True, None
    except Exception as e:
        return False, str(e)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--out', default='outputs/env_report.json')
    args=ap.parse_args()

    rep={
        'generated_utc': datetime.datetime.utcnow().isoformat()+'Z',
        'python': sys.version,
        'platform': platform.platform(),
        'pdftotext_path': shutil.which('pdftotext'),
        'unstructured_import': None,
        'docling_import': None,
    }
    ok, err = can_import('unstructured')
    rep['unstructured_import']={'ok': ok, 'error': err}
    ok, err = can_import('docling')
    rep['docling_import']={'ok': ok, 'error': err}

    os.makedirs(os.path.dirname(args.out) or '.', exist_ok=True)
    json.dump(rep, open(args.out,'w',encoding='utf-8'), indent=2)
    print('OK ->', args.out)

if __name__=='__main__':
    main()
