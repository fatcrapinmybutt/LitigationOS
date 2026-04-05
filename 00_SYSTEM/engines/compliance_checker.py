#!/usr/bin/env python3
"""
ENGINE 8: FILING COMPLIANCE CHECKER
Verifies each filing package meets court-specific formatting rules.
MCR 7.212 for COA, local rules for USDC WD Mich, JTC procedures.
"""
import sqlite3
import os
import re
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

db_path = str(Path(__file__).resolve().parents[2] / "litigation_context.db")
conn = sqlite3.connect(db_path)
conn.execute("PRAGMA busy_timeout = 60000")
conn.execute("PRAGMA journal_mode = WAL")
conn.execute("PRAGMA cache_size = -32000")
c = conn.cursor()

logger.info("=" * 70)
logger.info("  FILING COMPLIANCE CHECKER v1.0")
logger.info("=" * 70)

# Create compliance table
c.execute('''CREATE TABLE IF NOT EXISTS filing_compliance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    package_id TEXT,
    package_name TEXT,
    check_name TEXT,
    check_category TEXT,
    status TEXT,
    details TEXT,
    rule_reference TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
)''')

c.execute("SELECT COUNT(*) FROM filing_compliance")
if c.fetchone()[0] > 0:
    c.execute("DELETE FROM filing_compliance")
    conn.commit()

# MCR 7.212 requirements for COA briefs
COA_CHECKS = [
    ('cover_page', 'FORMAT', 'Cover page with case caption, court name, parties, attorney info', 'MCR 7.212(B)'),
    ('table_contents', 'FORMAT', 'Table of Contents with page references', 'MCR 7.212(B)'),
    ('table_authorities', 'FORMAT', 'Table of Authorities with page references', 'MCR 7.212(B)'),
    ('jurisdiction', 'CONTENT', 'Statement of Jurisdiction', 'MCR 7.212(C)(1)'),
    ('questions_presented', 'CONTENT', 'Statement of Questions Presented — concise, numbered', 'MCR 7.212(C)(2)'),
    ('statement_facts', 'CONTENT', 'Statement of Facts with record citations', 'MCR 7.212(C)(4)'),
    ('standard_review', 'CONTENT', 'Standard of Review for each issue', 'MCR 7.212(C)(5)'),
    ('argument', 'CONTENT', 'Argument with citations to authority', 'MCR 7.212(C)(6)'),
    ('relief', 'CONTENT', 'Statement of Relief Requested', 'MCR 7.212(C)(7)'),
    ('cert_service', 'PROCEDURE', 'Certificate of Service', 'MCR 7.212(D)'),
    ('page_limit', 'FORMAT', 'Brief not to exceed 50 pages (or 16,000 words)', 'MCR 7.212(B)(3)'),
    ('font_size', 'FORMAT', 'Proportionally spaced 12-point or monospaced 10-point font', 'MCR 7.212(B)(4)'),
    ('signature', 'PROCEDURE', 'Signature of filer', 'MCR 7.212(D)'),
]

# Generic filing checks
GENERIC_CHECKS = [
    ('case_caption', 'FORMAT', 'Correct case caption with all party names', 'Court Rules'),
    ('case_number', 'FORMAT', 'Case number present and correct', 'Court Rules'),
    ('date_field', 'FORMAT', 'Date field present', 'Court Rules'),
    ('signature_block', 'PROCEDURE', 'Signature block with address and phone', 'Court Rules'),
    ('cert_service', 'PROCEDURE', 'Certificate of service on all parties', 'Court Rules'),
    ('verification', 'PROCEDURE', 'Verification/affidavit if required', 'Court Rules'),
]

# Scan Delta99 packages
delta = r'I:\LitigationOS_Delta99'
results = []
total_pass = 0
total_fail = 0
total_warn = 0

if not os.path.isdir(delta):
    logger.warning("Delta99 directory not found: %s", delta)
    logger.warning("Skipping package scan — I:\\ drive may not be mounted.")
else:
    for pkg_dir in sorted(os.listdir(delta)):
        pkg_path = os.path.join(delta, pkg_dir)
        if not os.path.isdir(pkg_path) or not pkg_dir.startswith('PKG'):
            continue
        
        # Read all markdown content in package
        content = ''
        md_files = []
        for f in os.listdir(pkg_path):
            if f.endswith('.md'):
                md_files.append(f)
                try:
                    with open(os.path.join(pkg_path, f), 'r', encoding='utf-8', errors='replace') as fh:
                        content += fh.read() + '\n'
                except Exception:
                    pass
        
        is_coa = 'COA' in pkg_dir or 'APPELLANT' in pkg_dir
        checks = COA_CHECKS if is_coa else GENERIC_CHECKS
        
        for check_name, category, description, rule in checks:
            status = 'PASS'
            details = ''
            
            if check_name == 'cover_page':
                if 'COURT OF APPEALS' in content.upper() or 'CIRCUIT COURT' in content.upper():
                    details = 'Court name found'
                else:
                    status = 'WARN'
                    details = 'Court name may be missing from cover'
            elif check_name == 'table_contents':
                if 'TABLE OF CONTENTS' in content.upper() or 'CONTENTS' in content.upper():
                    details = 'TOC section found'
                else:
                    status = 'FAIL'
                    details = 'Table of Contents not found'
            elif check_name == 'table_authorities':
                if 'TABLE OF AUTHORITIES' in content.upper() or 'AUTHORITIES' in content.upper():
                    details = 'TOA section found'
                else:
                    status = 'FAIL' if is_coa else 'WARN'
                    details = 'Table of Authorities not found'
            elif check_name == 'jurisdiction':
                if 'JURISDICTION' in content.upper():
                    details = 'Jurisdiction statement found'
                else:
                    status = 'FAIL' if is_coa else 'WARN'
                    details = 'Jurisdiction statement not found'
            elif check_name == 'questions_presented':
                if 'QUESTION' in content.upper() and 'PRESENTED' in content.upper():
                    details = 'Questions presented found'
                elif 'ISSUE' in content.upper():
                    details = 'Issues section found (may need renaming)'
                    status = 'WARN'
                else:
                    status = 'FAIL' if is_coa else 'WARN'
                    details = 'Questions presented not found'
            elif check_name == 'statement_facts':
                if 'STATEMENT OF FACTS' in content.upper() or 'FACTS' in content.upper():
                    details = 'Statement of facts found'
                else:
                    status = 'WARN'
                    details = 'Statement of facts may need strengthening'
            elif check_name == 'standard_review':
                if 'STANDARD OF REVIEW' in content.upper() or 'STANDARD' in content.upper():
                    details = 'Standard of review found'
                else:
                    status = 'FAIL' if is_coa else 'WARN'
                    details = 'Standard of review not found'
            elif check_name == 'argument':
                if 'ARGUMENT' in content.upper():
                    details = 'Argument section found'
                else:
                    status = 'WARN'
                    details = 'Argument section may need labeling'
            elif check_name == 'relief':
                if 'RELIEF' in content.upper() or 'REQUEST' in content.upper() or 'PRAYER' in content.upper():
                    details = 'Relief section found'
                else:
                    status = 'WARN'
                    details = 'Relief requested section not explicit'
            elif check_name == 'cert_service':
                if 'CERTIFICATE OF SERVICE' in content.upper() or 'PROOF OF SERVICE' in content.upper():
                    details = 'Certificate of service found'
                else:
                    status = 'FAIL'
                    details = 'Certificate of service MISSING — required for all filings'
            elif check_name == 'page_limit':
                words = len(content.split())
                if words <= 16000:
                    details = f'{words} words (limit: 16,000)'
                else:
                    status = 'FAIL'
                    details = f'{words} words EXCEEDS 16,000 word limit'
            elif check_name == 'case_caption':
                if 'PIGORS' in content.upper() and 'WATSON' in content.upper():
                    details = 'Case caption with party names found'
                else:
                    status = 'WARN'
                    details = 'Case caption may be incomplete'
            elif check_name == 'case_number':
                if '2024-001507' in content or '366810' in content:
                    details = 'Case number found'
                else:
                    status = 'WARN'
                    details = 'Case number not found in body'
            elif check_name == 'signature_block' or check_name == 'signature':
                if 'ANDREW' in content.upper() and ('PIGORS' in content.upper()):
                    details = 'Signature block found'
                else:
                    status = 'WARN'
                    details = 'Signature block may be missing'
            else:
                details = 'Check not implemented — manual review needed'
                status = 'WARN'
            
            if status == 'PASS':
                total_pass += 1
            elif status == 'FAIL':
                total_fail += 1
            else:
                total_warn += 1
            
            c.execute('''INSERT INTO filing_compliance 
                (package_id, package_name, check_name, check_category, status, details, rule_reference)
                VALUES (?, ?, ?, ?, ?, ?, ?)''',
                (pkg_dir, pkg_dir, check_name, category, status, details, rule))
        
        pass_count = sum(1 for _ in [] if True)  # placeholder
        logger.info("  %s: %d MDs scanned", pkg_dir, len(md_files))

conn.commit()

# Generate report
report_path = r'C:\Users\andre\LitigationOS\05_ANALYSIS\COMPLIANCE_REPORT.md'
with open(report_path, 'w', encoding='utf-8') as f:
    f.write("# FILING COMPLIANCE REPORT\n")
    f.write(f"## Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
    f.write(f"**PASS: {total_pass} | WARN: {total_warn} | FAIL: {total_fail}**\n\n")
    f.write("---\n\n")
    
    c.execute("""SELECT package_name, check_name, status, details, rule_reference 
    FROM filing_compliance ORDER BY package_name, status DESC, check_name""")
    current_pkg = None
    for pkg, check, status, details, rule in c.fetchall():
        if pkg != current_pkg:
            current_pkg = pkg
            f.write(f"\n## {pkg}\n\n")
        icon = "✅" if status == 'PASS' else "❌" if status == 'FAIL' else "⚠️"
        f.write(f"- {icon} **{check}** [{status}] — {details} *(Ref: {rule})*\n")

rpt_size = os.path.getsize(report_path)
logger.info("\n[+] Compliance report: %.0fKB", rpt_size / 1024)

logger.info("\n%s", "=" * 70)
logger.info("  COMPLIANCE CHECKER COMPLETE")
logger.info("  ✅ PASS: %d | ⚠️ WARN: %d | ❌ FAIL: %d", total_pass, total_warn, total_fail)
logger.info("=" * 70)

conn.close()
