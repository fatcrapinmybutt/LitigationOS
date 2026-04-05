"""Placeholder Scanner Engine — finds all unresolved placeholders across filing stacks."""
import sys, os, re, json
from pathlib import Path
try:
    sys.stdout.reconfigure(encoding='utf-8')
except (AttributeError, OSError):
    pass

LITIGOS_ROOT = str(Path(__file__).resolve().parents[2])
FILING_DIRS = [
    '01_COA_366810',
    '02_TRIAL_14TH',
    '03_FEDERAL_1983',
    '04_MSC_ORIGINAL_ACTION',
    '06_EMERGENCY',
]

PLACEHOLDER_PATTERNS = [
    r'\[ANDREW:.*?\]',
    r'\[PLACEHOLDER.*?\]',
    r'\[TODO.*?\]',
    r'\[INSERT.*?\]',
    r'\[FILL.*?\]',
    r'\[TBD.*?\]',
    r'\[DATE.*?\]',
    r'\[NAME.*?\]',
    r'\[ADDRESS.*?\]',
    r'\[CITE.*?\]',
    r'\[RECORD.*?\]',
    r'\{\{.*?\}\}',
    r'_{5,}',  # Five or more underscores
    r'X{4,}',  # Four or more X's
    r'\$\[.*?\]',  # Dollar amounts in brackets
]

def scan_file(filepath):
    """Scan a single file for placeholder patterns."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
    except Exception:
        return []
    
    findings = []
    lines = content.split('\n')
    for i, line in enumerate(lines, 1):
        for pattern in PLACEHOLDER_PATTERNS:
            for match in re.finditer(pattern, line, re.IGNORECASE):
                findings.append({
                    'file': filepath,
                    'line': i,
                    'match': match.group(),
                    'context': line.strip()[:200],
                    'pattern': pattern,
                })
    return findings

def scan_all():
    all_findings = []
    files_scanned = 0
    
    for filing_dir in FILING_DIRS:
        dirpath = os.path.join(LITIGOS_ROOT, filing_dir)
        if not os.path.exists(dirpath):
            continue
        for root, dirs, files in os.walk(dirpath):
            for f in files:
                if f.endswith(('.md', '.txt', '.html', '.docx')):
                    fp = os.path.join(root, f)
                    findings = scan_file(fp)
                    all_findings.extend(findings)
                    files_scanned += 1
    
    return all_findings, files_scanned

def categorize(findings):
    categories = {
        'PERSONAL_INFO': [],  # Address, phone, email
        'CASE_FACTS': [],     # Dates, specific events
        'LEGAL_CITATIONS': [],# Case law, statutes, record cites
        'FINANCIAL': [],      # Dollar amounts, income
        'SIGNATURES': [],     # Sign and date
        'OTHER': [],
    }
    
    for f in findings:
        m = f['match'].upper()
        if any(k in m for k in ['ADDRESS', 'PHONE', 'EMAIL', 'NAME']):
            categories['PERSONAL_INFO'].append(f)
        elif any(k in m for k in ['DATE', 'HEARING', 'EVENT', 'WHEN']):
            categories['CASE_FACTS'].append(f)
        elif any(k in m for k in ['CITE', 'RECORD', 'TRANSCRIPT', 'PAGE']):
            categories['LEGAL_CITATIONS'].append(f)
        elif any(k in m for k in ['$', 'AMOUNT', 'INCOME', 'FINANCIAL']):
            categories['FINANCIAL'].append(f)
        elif any(k in m for k in ['SIGN', 'SIGNATURE', 'NOTARY']):
            categories['SIGNATURES'].append(f)
        else:
            categories['OTHER'].append(f)
    
    return categories

if __name__ == '__main__':
    findings, files_scanned = scan_all()
    categories = categorize(findings)
    
    # Write JSON report
    report = {
        'files_scanned': files_scanned,
        'total_placeholders': len(findings),
        'by_category': {k: len(v) for k, v in categories.items()},
        'findings': findings,
    }
    
    report_path = os.path.join(LITIGOS_ROOT, '00_SYSTEM', 'PLACEHOLDER_MASTER_REPORT.json')
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, default=str)
    
    # Write human-readable markdown report
    md_path = os.path.join(LITIGOS_ROOT, '00_SYSTEM', 'PLACEHOLDER_MASTER_REPORT.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write('# PLACEHOLDER MASTER REPORT\n\n')
        f.write(f'Files scanned: {files_scanned}\n')
        f.write(f'Total placeholders: {len(findings)}\n\n')
        
        f.write('## Summary by Category\n\n')
        for cat, items in categories.items():
            f.write(f'- **{cat}**: {len(items)} placeholders\n')
        
        f.write('\n## By Filing Stack\n\n')
        by_stack = {}
        for finding in findings:
            # Extract stack name from path
            rel = os.path.relpath(finding['file'], LITIGOS_ROOT)
            stack = rel.split(os.sep)[0]
            by_stack.setdefault(stack, []).append(finding)
        
        for stack, items in sorted(by_stack.items()):
            f.write(f'\n### {stack} ({len(items)} placeholders)\n\n')
            for item in items:
                rel_file = os.path.relpath(item['file'], LITIGOS_ROOT)
                f.write(f'- **{rel_file}** (line {item["line"]}): `{item["match"]}`\n')
                f.write(f'  Context: {item["context"][:100]}\n')
    
    print(f'Scanned {files_scanned} files')
    print(f'Found {len(findings)} placeholders')
    for cat, items in categories.items():
        print(f'  {cat}: {len(items)}')
    print(f'\nReports written to:')
    print(f'  {report_path}')
    print(f'  {md_path}')
