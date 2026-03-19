#!/usr/bin/env python3
"""Filing Validator Engine - MCR compliance validation for court filings.

Validates litigation documents against Michigan Court Rules (MCR).
Checks caption format, signature blocks, certificates of service,
word count limits, motion requirements, and page formatting.

Usage:
    python filing_validator_engine.py --file path/to/filing.md --type brief
    python filing_validator_engine.py --file path/to/motion.md --type motion --output json
    python filing_validator_engine.py --file path/to/filing.md --type complaint --fix
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import argparse
import json
import os
import re
import sqlite3
import textwrap
from collections import OrderedDict
from datetime import datetime
from pathlib import Path

DB = r'C:\Users\andre\LitigationOS\litigation_context.db'

FILING_TYPES = ['brief', 'motion', 'complaint', 'petition', 'response', 'reply', 'appeal']

WORD_LIMITS = {
    'brief': 16000,        # MCR 7.212(B) - COA briefs
    'motion': 5000,        # MCR 2.119 general motions
    'reply': 8000,         # MCR 7.212(B) - reply briefs
    'complaint': None,     # No word limit
    'petition': None,
    'response': 16000,
    'appeal': 16000,
}

# Regex patterns for validation checks
PATTERNS = {
    'case_number': re.compile(
        r'(?:Case\s*(?:No\.?|Number|#)\s*[:.]?\s*)'
        r'(\d{2,4}[-/]\d{3,8}[-/]?\w*)',
        re.IGNORECASE
    ),
    'court_name': re.compile(
        r'(?:Circuit\s+Court|District\s+Court|Court\s+of\s+Appeals|Supreme\s+Court'
        r'|Probate\s+Court|Family\s+Division)',
        re.IGNORECASE
    ),
    'parties': re.compile(
        r'(?:Plaintiff|Defendant|Appellant|Appellee|Petitioner|Respondent)',
        re.IGNORECASE
    ),
    'attorney_designation': re.compile(
        r'(?:Attorney\s+(?:for|at\s+Law)|Pro\s+Se|In\s+Propria\s+Persona|Self-Represented)',
        re.IGNORECASE
    ),
    'signature_block': re.compile(
        r'(?:Respectfully\s+submitted|/s/|___+\s*\n)',
        re.IGNORECASE
    ),
    'certificate_of_service': re.compile(
        r'(?:Certificate\s+of\s+Service|CERTIFICATE\s+OF\s+SERVICE|'
        r'I\s+(?:hereby\s+)?certif(?:y|ied)\s+that)',
        re.IGNORECASE
    ),
    'proposed_order': re.compile(
        r'(?:Proposed\s+Order|ORDER\s+(?:GRANTING|DENYING))',
        re.IGNORECASE
    ),
    'brief_in_support': re.compile(
        r'(?:Brief\s+in\s+Support|Memorandum\s+(?:of\s+Law\s+)?in\s+Support|'
        r'BRIEF\s+IN\s+SUPPORT)',
        re.IGNORECASE
    ),
    'record_citation': re.compile(
        r'(?:\(?\s*(?:R\.|Rec\.|Record)\s*(?:at\s*)?\d+)',
        re.IGNORECASE
    ),
    'passive_voice': re.compile(
        r'\b(?:was|were|been|being|is|are|am)\s+(?:\w+ed|(?:given|taken|made|done|shown|known|seen|found))\b',
        re.IGNORECASE
    ),
}


def get_db_connection():
    """Open DB connection with standard pragmas."""
    conn = sqlite3.connect(DB, timeout=120)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    return conn


def load_mcr_rules(conn, rule_numbers=None):
    """Load MCR rules from mcr_encyclopedia table."""
    rules = {}
    try:
        if rule_numbers:
            placeholders = ','.join('?' for _ in rule_numbers)
            rows = conn.execute(
                f"SELECT rule_number, rule_title, full_text, requirements_json "
                f"FROM mcr_encyclopedia WHERE rule_number IN ({placeholders})",
                rule_numbers
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT rule_number, rule_title, full_text, requirements_json "
                "FROM mcr_encyclopedia LIMIT 100"
            ).fetchall()

        for row in rows:
            rules[row[0]] = {
                'title': row[1],
                'text': row[2] or '',
                'requirements': row[3] or '{}'
            }
    except Exception as e:
        print(f"  [WARN] Could not load MCR rules: {e}")

    return rules


def read_filing(file_path):
    """Read filing content from file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Filing not found: {file_path}")

    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    return content


def count_words(text):
    """Count words in text, excluding headers and formatting."""
    clean = re.sub(r'[#*_\-=]{2,}', '', text)
    clean = re.sub(r'\s+', ' ', clean).strip()
    return len(clean.split())


def check_caption(text, violations):
    """MCR 2.113 - Caption format validation."""
    score = 0
    max_score = 4

    # Check for case number
    if PATTERNS['case_number'].search(text[:2000]):
        score += 1
    else:
        violations.append({
            'rule': 'MCR 2.113(A)',
            'severity': 'HIGH',
            'issue': 'Missing case number in caption',
            'fix': 'Add case number in format: Case No. XX-XXXXX-XX'
        })

    # Check for court identification
    if PATTERNS['court_name'].search(text[:2000]):
        score += 1
    else:
        violations.append({
            'rule': 'MCR 2.113(A)',
            'severity': 'HIGH',
            'issue': 'Missing court name in caption',
            'fix': 'Add full court name (e.g., "Washtenaw County Circuit Court, Family Division")'
        })

    # Check for party designations
    if PATTERNS['parties'].search(text[:3000]):
        score += 1
    else:
        violations.append({
            'rule': 'MCR 2.113(A)',
            'severity': 'MEDIUM',
            'issue': 'Missing party designations (Plaintiff/Defendant)',
            'fix': 'Include party names with designations'
        })

    # Check attorney/pro se designation
    if PATTERNS['attorney_designation'].search(text):
        score += 1
    else:
        violations.append({
            'rule': 'MCR 2.113(E)',
            'severity': 'MEDIUM',
            'issue': 'Missing attorney or pro se designation',
            'fix': 'Add "Pro Se" or attorney information block'
        })

    return score, max_score


def check_signature_block(text, violations):
    """Check for proper signature block."""
    if PATTERNS['signature_block'].search(text[-3000:]):
        return 1, 1
    else:
        violations.append({
            'rule': 'MCR 2.114(A)',
            'severity': 'HIGH',
            'issue': 'Missing signature block',
            'fix': 'Add signature block with "Respectfully submitted," followed by /s/ name, address, phone, email'
        })
        return 0, 1


def check_certificate_of_service(text, violations):
    """MCR 2.107 - Certificate of service."""
    if PATTERNS['certificate_of_service'].search(text):
        return 1, 1
    else:
        violations.append({
            'rule': 'MCR 2.107(C)',
            'severity': 'HIGH',
            'issue': 'Missing Certificate of Service',
            'fix': 'Add Certificate of Service stating method, date, and parties served'
        })
        return 0, 1


def check_word_count(text, filing_type, violations):
    """Check word count against limits."""
    limit = WORD_LIMITS.get(filing_type)
    if limit is None:
        return 1, 1  # No limit for this type

    wc = count_words(text)
    if wc <= limit:
        return 1, 1
    else:
        violations.append({
            'rule': 'MCR 7.212(B)' if filing_type in ('brief', 'appeal', 'response', 'reply') else 'MCR 2.119',
            'severity': 'HIGH',
            'issue': f'Word count {wc:,} exceeds limit of {limit:,} for {filing_type}',
            'fix': f'Reduce by {wc - limit:,} words. Current: {wc:,}, Limit: {limit:,}'
        })
        return 0, 1


def check_motion_requirements(text, filing_type, violations):
    """MCR 2.119 - Motion requirements."""
    if filing_type != 'motion':
        return 0, 0  # N/A

    score = 0
    max_score = 3

    # Brief in support
    if PATTERNS['brief_in_support'].search(text):
        score += 1
    else:
        violations.append({
            'rule': 'MCR 2.119(A)(2)',
            'severity': 'MEDIUM',
            'issue': 'Missing brief in support of motion',
            'fix': 'Include a Brief in Support section or file separately'
        })

    # Proposed order
    if PATTERNS['proposed_order'].search(text):
        score += 1
    else:
        violations.append({
            'rule': 'MCR 2.119(A)(3)',
            'severity': 'MEDIUM',
            'issue': 'Missing proposed order',
            'fix': 'Attach a proposed order granting the requested relief'
        })

    # 21-day notice reference
    if re.search(r'(?:21[\s-]day|twenty[\s-]one[\s-]day|notice\s+of\s+hearing)', text, re.IGNORECASE):
        score += 1
    else:
        violations.append({
            'rule': 'MCR 2.119(C)',
            'severity': 'LOW',
            'issue': 'No reference to 21-day notice requirement',
            'fix': 'Ensure 21-day notice of hearing is served per MCR 2.119(C)'
        })

    return score, max_score


def check_page_formatting(text, violations):
    """Check basic formatting indicators."""
    score = 0
    max_score = 2

    lines = text.split('\n')
    long_lines = sum(1 for l in lines if len(l) > 120)
    if long_lines < len(lines) * 0.1:
        score += 1
    else:
        violations.append({
            'rule': 'MCR 7.212(C)',
            'severity': 'LOW',
            'issue': f'{long_lines} lines exceed 120 chars - possible margin issues',
            'fix': 'Ensure 1-inch margins on all sides'
        })

    # Check for double spacing indicators
    blank_line_ratio = sum(1 for l in lines if l.strip() == '') / max(len(lines), 1)
    if blank_line_ratio > 0.15:
        score += 1
    else:
        violations.append({
            'rule': 'MCR 7.212(C)',
            'severity': 'LOW',
            'issue': 'Document may not be double-spaced',
            'fix': 'Ensure double spacing for body text per court rules'
        })

    return score, max_score


def check_document_title(text, violations):
    """Check for proper document title."""
    first_2000 = text[:2000].upper()
    title_patterns = [
        'MOTION', 'BRIEF', 'COMPLAINT', 'PETITION', 'RESPONSE',
        'REPLY', 'MEMORANDUM', 'AFFIDAVIT', 'APPLICATION', 'ANSWER'
    ]
    found = any(p in first_2000 for p in title_patterns)
    if found:
        return 1, 1
    else:
        violations.append({
            'rule': 'MCR 2.113(A)',
            'severity': 'MEDIUM',
            'issue': 'No clear document title found in header',
            'fix': 'Add document title (e.g., "MOTION FOR...", "BRIEF IN SUPPORT OF...")'
        })
        return 0, 1


def validate_filing(file_path, filing_type='brief'):
    """Run all validation checks on a filing."""
    text = read_filing(file_path)
    violations = []
    scores = OrderedDict()

    # Run all checks
    s, m = check_caption(text, violations)
    scores['caption'] = (s, m)

    s, m = check_document_title(text, violations)
    scores['document_title'] = (s, m)

    s, m = check_signature_block(text, violations)
    scores['signature_block'] = (s, m)

    s, m = check_certificate_of_service(text, violations)
    scores['certificate_of_service'] = (s, m)

    s, m = check_word_count(text, filing_type, violations)
    scores['word_count'] = (s, m)

    s, m = check_motion_requirements(text, filing_type, violations)
    if m > 0:
        scores['motion_requirements'] = (s, m)

    s, m = check_page_formatting(text, violations)
    scores['page_formatting'] = (s, m)

    # Calculate overall score
    total_earned = sum(s for s, _ in scores.values())
    total_possible = sum(m for _, m in scores.values())
    overall_score = round((total_earned / max(total_possible, 1)) * 100)

    wc = count_words(text)
    high_violations = sum(1 for v in violations if v['severity'] == 'HIGH')
    medium_violations = sum(1 for v in violations if v['severity'] == 'MEDIUM')
    low_violations = sum(1 for v in violations if v['severity'] == 'LOW')

    report = {
        'file': str(file_path),
        'filing_type': filing_type,
        'validated_at': datetime.now().isoformat(),
        'overall_score': overall_score,
        'word_count': wc,
        'word_limit': WORD_LIMITS.get(filing_type),
        'total_violations': len(violations),
        'violations_by_severity': {
            'HIGH': high_violations,
            'MEDIUM': medium_violations,
            'LOW': low_violations
        },
        'section_scores': {k: f"{s}/{m}" for k, (s, m) in scores.items()},
        'violations': violations,
        'compliance_status': 'PASS' if overall_score >= 80 and high_violations == 0 else 'FAIL'
    }

    return report


def apply_auto_fixes(file_path, report):
    """Attempt to auto-fix common issues (writes to .fixed copy)."""
    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    original = content
    fixes_applied = []

    # Auto-fix: Add pro se designation if missing
    has_designation = PATTERNS['attorney_designation'].search(content)
    if not has_designation:
        content += '\n\nPro Se Litigant\n'
        fixes_applied.append('Added Pro Se designation')

    # Auto-fix: Add certificate of service template if missing
    has_cos = PATTERNS['certificate_of_service'].search(content)
    if not has_cos:
        cos_template = textwrap.dedent("""

        CERTIFICATE OF SERVICE

        I hereby certify that on {date}, I served a copy of this document
        upon all parties of record by [e-filing/first class mail/personal service]
        at the addresses on file with the Court.

        /s/ ___________________________
        Date: {date}
        """).format(date=datetime.now().strftime('%B %d, %Y'))
        content += cos_template
        fixes_applied.append('Added Certificate of Service template')

    # Auto-fix: Add signature block if missing
    has_sig = PATTERNS['signature_block'].search(content[-3000:])
    if not has_sig and 'certificate_of_service' not in [f.lower() for f in fixes_applied]:
        sig_block = textwrap.dedent("""

        Respectfully submitted,

        /s/ ___________________________
        [Name]
        [Address]
        [City, State ZIP]
        [Phone]
        [Email]
        Pro Se
        """)
        # Insert before certificate of service if it exists
        cos_pos = content.lower().find('certificate of service')
        if cos_pos > 0:
            content = content[:cos_pos] + sig_block + '\n' + content[cos_pos:]
        else:
            content += sig_block
        fixes_applied.append('Added signature block template')

    if fixes_applied:
        fixed_path = Path(file_path).with_suffix('.fixed' + Path(file_path).suffix)
        with open(fixed_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"[FIX] Auto-fixes applied and saved to: {fixed_path}")
        for fix in fixes_applied:
            print(f"  - {fix}")
        return str(fixed_path), fixes_applied
    else:
        print("[FIX] No auto-fixes applicable.")
        return None, []


def format_report_md(report):
    """Format compliance report as markdown."""
    lines = []
    status_icon = '[PASS]' if report['compliance_status'] == 'PASS' else '[FAIL]'
    lines.append(f"# Filing Compliance Report {status_icon}")
    lines.append(f"")
    lines.append(f"**File:** {report['file']}")
    lines.append(f"**Type:** {report['filing_type']}")
    lines.append(f"**Date:** {report['validated_at']}")
    lines.append(f"**Score:** {report['overall_score']}/100")
    lines.append(f"**Word Count:** {report['word_count']:,}")
    if report['word_limit']:
        lines.append(f"**Word Limit:** {report['word_limit']:,}")
    lines.append(f"")

    lines.append(f"## Section Scores")
    for section, score in report['section_scores'].items():
        section_name = section.replace('_', ' ').title()
        lines.append(f"- {section_name}: {score}")
    lines.append(f"")

    if report['violations']:
        lines.append(f"## Violations ({report['total_violations']})")
        lines.append(f"")
        for v in report['violations']:
            sev = v['severity']
            lines.append(f"### [{sev}] {v['rule']}")
            lines.append(f"**Issue:** {v['issue']}")
            lines.append(f"**Fix:** {v['fix']}")
            lines.append(f"")
    else:
        lines.append("## No Violations Found")

    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='Filing Validator Engine - MCR compliance validation'
    )
    parser.add_argument('--file', type=str, required=True, help='Path to filing document')
    parser.add_argument('--type', type=str, choices=FILING_TYPES, default='brief',
                        help='Filing type (default: brief)')
    parser.add_argument('--output', type=str, choices=['json', 'md'], default='json',
                        help='Output format (default: json)')
    parser.add_argument('--fix', action='store_true', help='Auto-fix mode: apply corrections')
    parser.add_argument('--save', type=str, help='Save report to file')

    args = parser.parse_args()

    print(f"[START] Filing Validator Engine - {datetime.now().isoformat()}")
    print(f"[INPUT] File: {args.file}")
    print(f"[INPUT] Type: {args.type}")

    try:
        report = validate_filing(args.file, args.type)

        # Print summary
        status = report['compliance_status']
        score = report['overall_score']
        v_count = report['total_violations']
        print(f"\n[RESULT] Status: {status} | Score: {score}/100 | Violations: {v_count}")
        print(f"  HIGH: {report['violations_by_severity']['HIGH']}  "
              f"MEDIUM: {report['violations_by_severity']['MEDIUM']}  "
              f"LOW: {report['violations_by_severity']['LOW']}")

        # Output
        if args.output == 'json':
            output_text = json.dumps(report, indent=2, ensure_ascii=True)
        else:
            output_text = format_report_md(report)

        if args.save:
            with open(args.save, 'w', encoding='utf-8') as f:
                f.write(output_text)
            print(f"[SAVED] Report written to {args.save}")
        else:
            print(f"\n{output_text}")

        # Auto-fix mode
        if args.fix:
            fixed_path, fixes = apply_auto_fixes(args.file, report)
            if fixed_path:
                print(f"\n[REVALIDATE] Checking fixed version...")
                fixed_report = validate_filing(fixed_path, args.type)
                print(f"[REVALIDATE] New score: {fixed_report['overall_score']}/100 "
                      f"(was {score}/100)")

    except FileNotFoundError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[FATAL] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print(f"[DONE] {datetime.now().isoformat()}")


if __name__ == '__main__':
    main()
