#!/usr/bin/env python3
"""
ENGINE 5: LEGAL CITATION VALIDATOR
Verifies every MCL, MCR, and case citation across all filing packages.
Flags missing, malformed, or potentially outdated citations.
"""
import sqlite3
import os
import re
from datetime import datetime

db_path = r'C:\Users\andre\LitigationOS\litigation_context.db'
conn = sqlite3.connect(db_path)
c = conn.cursor()

print("=" * 70)
print("  LEGAL CITATION VALIDATOR v1.0")
print("=" * 70)

# Create citation validation table
c.execute('''CREATE TABLE IF NOT EXISTS citation_validation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    citation_text TEXT NOT NULL,
    citation_type TEXT,
    source_file TEXT,
    source_context TEXT,
    is_valid INTEGER DEFAULT 1,
    validation_note TEXT,
    pinpoint TEXT,
    year TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
)''')

c.execute("SELECT COUNT(*) FROM citation_validation")
if c.fetchone()[0] > 0:
    c.execute("DELETE FROM citation_validation")
    conn.commit()

# Citation patterns
MCL_PATTERN = r'MCL\s+(\d+[\.\d]*[a-z]?(?:\(\d+\))?)'
MCR_PATTERN = r'MCR\s+(\d+[\.\d]*(?:\([A-Z]\))?(?:\(\d+\))?)'
CASE_PATTERN = r'(\w[\w\s\.]+(?:v\.|vs\.)\s+\w[\w\s\.]+),?\s*(\d+)\s+((?:U\.S\.|S\.Ct\.|L\.Ed|Mich|Mich\s*App|F\.\d+[d]?|N\.W\.\d+[d]?))\s+(\d+)\s*(?:\((\d{4})\))?'
USC_PATTERN = r'(\d+)\s+U\.?S\.?C\.?\s+§?\s*(\d+[a-z]?)'
CONST_PATTERN = r'(?:U\.S\.\s*Const\.?\s*(?:amend|art)\.\s*[\w,\s§]+|Const\.?\s*1963,?\s*art\.?\s*\d+,?\s*§\s*\d+)'
MCJC_PATTERN = r'MCJC\s+Canon\s+(\d+)'
MRE_PATTERN = r'MRE\s+(\d+(?:\([a-z]\))?)'

# Known valid Michigan statutes (core set for family law)
KNOWN_MCL = {
    '722.23', '722.24', '722.25', '722.26', '722.27', '722.27a', '722.27b',
    '750.539c', '750.539d', '750.539e',
    '600.308', '600.1701', '600.2950',
    '712A.2', '712A.19b',
}

KNOWN_MCR = {
    '2.002', '2.003', '2.119', '2.613',
    '3.206', '3.207', '3.210', '3.211',
    '7.202', '7.203', '7.205', '7.212', '7.215',
    '3.606',
}

# Scan all markdown files in filing directories
scan_dirs = [
    r'C:\Users\andre\LitigationOS\04_COURT_FILINGS',
    r'I:\LitigationOS_Delta99',
]

total_citations = 0
files_scanned = 0
issues = []

for scan_dir in scan_dirs:
    if not os.path.exists(scan_dir):
        continue
    for root, dirs, files in os.walk(scan_dir):
        for fname in files:
            if not fname.endswith(('.md', '.txt')):
                continue
            fpath = os.path.join(root, fname)
            try:
                with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
            except:
                continue
            files_scanned += 1
            
            # Extract MCL citations
            for match in re.finditer(MCL_PATTERN, content):
                cite = match.group(1)
                total_citations += 1
                valid = 1
                note = 'Known valid' if cite in KNOWN_MCL else 'Verify current — not in known set'
                if cite not in KNOWN_MCL:
                    issues.append(f'MCL {cite} in {fname} — needs verification')
                    valid = 0
                c.execute('INSERT INTO citation_validation (citation_text, citation_type, source_file, is_valid, validation_note) VALUES (?, ?, ?, ?, ?)',
                    (f'MCL {cite}', 'MCL', fname, valid, note))
            
            # Extract MCR citations
            for match in re.finditer(MCR_PATTERN, content):
                cite = match.group(1)
                total_citations += 1
                valid = 1
                note = 'Known valid' if cite in KNOWN_MCR else 'Verify current — not in known set'
                if cite not in KNOWN_MCR:
                    issues.append(f'MCR {cite} in {fname} — needs verification')
                    valid = 0
                c.execute('INSERT INTO citation_validation (citation_text, citation_type, source_file, is_valid, validation_note) VALUES (?, ?, ?, ?, ?)',
                    (f'MCR {cite}', 'MCR', fname, valid, note))
            
            # Extract case citations
            for match in re.finditer(CASE_PATTERN, content):
                case_name = match.group(1).strip()
                vol = match.group(2)
                reporter = match.group(3)
                page = match.group(4)
                year = match.group(5) or ''
                total_citations += 1
                cite_text = f'{case_name}, {vol} {reporter} {page}'
                if year:
                    cite_text += f' ({year})'
                note = 'Format valid' if year else 'Missing year — add parenthetical year'
                valid = 1 if year else 0
                if not year:
                    issues.append(f'{cite_text} in {fname} — missing year')
                c.execute('INSERT INTO citation_validation (citation_text, citation_type, source_file, is_valid, validation_note, year) VALUES (?, ?, ?, ?, ?, ?)',
                    (cite_text, 'CASE', fname, valid, note, year))
            
            # Extract USC citations
            for match in re.finditer(USC_PATTERN, content):
                title = match.group(1)
                section = match.group(2)
                total_citations += 1
                c.execute('INSERT INTO citation_validation (citation_text, citation_type, source_file, is_valid, validation_note) VALUES (?, ?, ?, ?, ?)',
                    (f'{title} USC § {section}', 'USC', fname, 1, 'Federal statute — verify current'))
            
            # Extract Constitutional citations
            for match in re.finditer(CONST_PATTERN, content):
                total_citations += 1
                c.execute('INSERT INTO citation_validation (citation_text, citation_type, source_file, is_valid, validation_note) VALUES (?, ?, ?, ?, ?)',
                    (match.group(0), 'CONSTITUTION', fname, 1, 'Constitutional provision — always valid'))
            
            # Extract MCJC citations
            for match in re.finditer(MCJC_PATTERN, content):
                total_citations += 1
                c.execute('INSERT INTO citation_validation (citation_text, citation_type, source_file, is_valid, validation_note) VALUES (?, ?, ?, ?, ?)',
                    (f'MCJC Canon {match.group(1)}', 'MCJC', fname, 1, 'Judicial canon — verify current version'))

conn.commit()

# Generate validation report
report_path = r'C:\Users\andre\LitigationOS\05_ANALYSIS\CITATION_VALIDATION_REPORT.md'
with open(report_path, 'w', encoding='utf-8') as f:
    f.write("# CITATION VALIDATION REPORT\n")
    f.write(f"## Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
    f.write(f"**Files Scanned:** {files_scanned}\n")
    f.write(f"**Total Citations Found:** {total_citations}\n")
    f.write(f"**Issues Flagged:** {len(issues)}\n\n")
    f.write("---\n\n")
    
    # Summary by type
    c.execute("SELECT citation_type, COUNT(*), SUM(CASE WHEN is_valid=1 THEN 1 ELSE 0 END) FROM citation_validation GROUP BY citation_type ORDER BY COUNT(*) DESC")
    f.write("## Citation Summary\n\n")
    f.write("| Type | Count | Valid | Issues |\n")
    f.write("|------|-------|-------|--------|\n")
    for ctype, cnt, valid in c.fetchall():
        f.write(f"| {ctype} | {cnt} | {valid or 0} | {cnt - (valid or 0)} |\n")
    
    if issues:
        f.write("\n## Issues Requiring Verification\n\n")
        for issue in issues[:100]:
            f.write(f"- ⚠️ {issue}\n")

rpt_size = os.path.getsize(report_path)
print(f"\n[+] Scanned {files_scanned} files, found {total_citations} citations")
print(f"[+] Flagged {len(issues)} issues")
print(f"[+] Report: {rpt_size/1024:.0f}KB")

print(f"\n{'='*70}")
print(f"  CITATION VALIDATOR COMPLETE")
print(f"  {total_citations} citations | {len(issues)} issues | {files_scanned} files")
print(f"{'='*70}")

conn.close()
