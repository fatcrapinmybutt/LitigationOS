#!/usr/bin/env python3
"""Temporary syntax check script."""
import py_compile
import sys
import os

os.chdir(r'C:\Users\andre\LitigationOS\00_SYSTEM\scripts')
os.environ['PYTHONUTF8'] = '1'

scripts = [
    ('noreply_pdf_processor.py', 'noreply'),
    ('backup_rotation.py', 'backup'),
    ('ocr_evidence_pipeline.py', 'ocr')
]

all_ok = True
for script, label in scripts:
    try:
        py_compile.compile(script, doraise=True)
        print(f'{label}: OK')
    except SyntaxError as e:
        print(f'{label}: SYNTAX ERROR at line {e.lineno}: {e.msg}')
        all_ok = False
    except Exception as e:
        print(f'{label}: ERROR - {e}')
        all_ok = False

if all_ok:
    print('\nAll syntax checks PASSED - proceeding to functional tests')
    sys.exit(0)
else:
    print('\nSome checks FAILED')
    sys.exit(1)
