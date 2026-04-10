import sys
sys.path.insert(0, r'C:\Users\andre\LitigationOS\00_SYSTEM')
import json

from convergence.certifier import ConvergenceCertifier
from convergence.wiring import WiringValidator
from convergence.report import generate_report

print('=== CERTIFICATION ===')
with ConvergenceCertifier() as cert:
    cert_result = cert.certify_all()
print(json.dumps(cert_result, indent=2, ensure_ascii=False))

print('\n=== WIRING ===')
with WiringValidator() as wv:
    wv.validate_all()
    wiring_result = wv.summary()
print(json.dumps(wiring_result, indent=2, ensure_ascii=False))

print('\n=== REPORT ===')
report = generate_report(cert_result, wiring_result)
print(f'Report written to: 04_ANALYSIS/convergence_report.md ({len(report)} chars)')
