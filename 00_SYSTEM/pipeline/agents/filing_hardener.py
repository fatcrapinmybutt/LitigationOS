#!/usr/bin/env python3
"""
Pipeline Agent E04: Filing Hardener
=====================================
Scans the 3 GO filing packages (F3, F6, F10) and generates
specific fix-lists to make them court-ready.

Checks: placeholders, form completeness, exhibit attachments,
certificate of service, affidavit status, formatting compliance.

NOVEL INNOVATION: Auto-generates a HARDENING CHECKLIST per filing
with exact line numbers and specific fix instructions.

Agent Contract: run() → AgentResult(agent_id='E04', status, stats)
"""
import os, sys, json, re
from datetime import datetime
from pathlib import Path

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPORT_DIR = os.path.join(os.path.dirname(__file__), '..', 'reports')
os.makedirs(REPORT_DIR, exist_ok=True)

PKG_BASE = r"C:\Users\andre\Desktop\LITIGATION_FILING_PACKAGE"

FILING_PACKAGES = {
    "F3": {
        "dir": "PKG_F3_DISQUALIFICATION_MCR_2003",
        "name": "Disqualification Motion (MCR 2.003)",
        "court": "14th Circuit Court — Family Division",
        "case_number": "2024-001507-DC",
        "filing_fee": "$0"
    },
    "F6": {
        "dir": "PKG_F6_JTC_COMPLAINT",
        "name": "JTC Complaint",
        "court": "Judicial Tenure Commission",
        "case_number": "JTC-TBD",
        "filing_fee": "$0"
    },
    "F10": {
        "dir": "PKG_F10_COA_EMERGENCY_MOTION",
        "name": "COA Emergency Motion",
        "court": "Michigan Court of Appeals",
        "case_number": "COA 366810",
        "filing_fee": "$0 (IFP)"
    }
}

# Patterns to detect placeholders and issues
PLACEHOLDER_PATTERNS = [
    (r'\[ANDREW[:\s].*?\]', 'ANDREW_ACTION'),
    (r'\[INSERT.*?\]', 'INSERT_NEEDED'),
    (r'\[ATTACH.*?\]', 'ATTACH_NEEDED'),
    (r'\[VERIFY.*?\]', 'VERIFY_NEEDED'),
    (r'\[TODO.*?\]', 'TODO'),
    (r'\[SIGN.*?\]', 'SIGNATURE_NEEDED'),
    (r'\[DATE.*?\]', 'DATE_NEEDED'),
    (r'\[FILL.*?\]', 'FILL_NEEDED'),
    (r'_{5,}', 'BLANK_LINE'),
    (r'\[CITATION NEEDED\]', 'CITATION_NEEDED'),
]

QUALITY_CHECKS = [
    ('has_caption', r'STATE OF MICHIGAN|CIRCUIT COURT|COURT OF APPEALS|JUDICIAL TENURE', 'Caption present'),
    ('has_case_number', r'2024-001507|366810|JTC', 'Case number present'),
    ('has_signature_block', r'Respectfully submitted|Pro Se|Andrew.*Pigors', 'Signature block present'),
    ('has_cert_service', r'CERTIFICATE OF SERVICE|PROOF OF SERVICE|certif.*serv', 'Certificate of service reference'),
    ('has_verification', r'under penalty of perjury|swear|affirm', 'Verification/oath language'),
    ('cites_authority', r'MCR \d|MCL \d|USC §|Canon \d|MRPC', 'Legal authority citations'),
    ('child_privacy', r'L\.D\.W\.|initials only', 'Child referred to by initials'),
]

def scan_file(filepath):
    """Scan a single file for placeholders and quality issues."""
    issues = []
    quality = {}
    
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
            lines = content.split('\n')
    except Exception as e:
        return [{'type': 'READ_ERROR', 'message': str(e), 'line': 0}], {}
    
    # Check for placeholders
    for pattern, issue_type in PLACEHOLDER_PATTERNS:
        for i, line in enumerate(lines, 1):
            matches = re.findall(pattern, line, re.IGNORECASE)
            for match in matches:
                issues.append({
                    'type': issue_type,
                    'match': match if len(match) < 100 else match[:100] + '...',
                    'line': i,
                    'context': line.strip()[:120]
                })
    
    # Quality checks
    for check_id, pattern, description in QUALITY_CHECKS:
        quality[check_id] = {
            'present': bool(re.search(pattern, content, re.IGNORECASE)),
            'description': description
        }
    
    # Check for full child name (privacy violation)
    # Only check for obviously wrong patterns, not initials
    if re.search(r'(?i)child.{0,20}full.{0,10}name', content):
        issues.append({
            'type': 'PRIVACY_RISK',
            'match': 'Possible child full name reference',
            'line': 0,
            'context': 'Review for MCR 8.119(H) compliance'
        })
    
    # Word count
    word_count = len(content.split())
    
    return issues, quality, word_count

def analyze_package(filing_id, config):
    """Analyze an entire filing package."""
    pkg_dir = os.path.join(PKG_BASE, config['dir'])
    
    result = {
        'filing_id': filing_id,
        'name': config['name'],
        'court': config['court'],
        'case_number': config['case_number'],
        'filing_fee': config['filing_fee'],
        'directory': pkg_dir,
        'exists': os.path.isdir(pkg_dir),
        'files': [],
        'total_issues': 0,
        'blocker_count': 0,
        'total_words': 0,
        'quality_score': 0,
        'hardening_tasks': []
    }
    
    if not result['exists']:
        result['hardening_tasks'].append({
            'priority': 'BLOCKER',
            'task': f'Package directory not found: {pkg_dir}',
            'action': 'Verify package location'
        })
        return result
    
    # Scan all .md files in the package
    for fname in sorted(os.listdir(pkg_dir)):
        if not fname.endswith('.md') or '.bak' in fname:
            continue
        
        fpath = os.path.join(pkg_dir, fname)
        scan_result = scan_file(fpath)
        
        if len(scan_result) == 3:
            issues, quality, word_count = scan_result
        else:
            issues, quality = scan_result
            word_count = 0
        
        file_info = {
            'filename': fname,
            'issues': issues,
            'quality': quality,
            'word_count': word_count,
            'issue_count': len(issues)
        }
        result['files'].append(file_info)
        result['total_issues'] += len(issues)
        result['total_words'] += word_count
    
    # Generate hardening tasks from issues
    for file_info in result['files']:
        for issue in file_info['issues']:
            priority = 'BLOCKER' if issue['type'] in ('SIGNATURE_NEEDED', 'ANDREW_ACTION', 'INSERT_NEEDED') else 'HIGH'
            if issue['type'] == 'BLANK_LINE':
                priority = 'MEDIUM'
            
            result['hardening_tasks'].append({
                'priority': priority,
                'file': file_info['filename'],
                'line': issue['line'],
                'type': issue['type'],
                'match': issue.get('match', ''),
                'action': f"Fix {issue['type']} in {file_info['filename']} at line {issue['line']}"
            })
            
            if priority == 'BLOCKER':
                result['blocker_count'] += 1
    
    # Check for missing critical files
    expected_files = ['01_MAIN_FILING.md', '02_AFFIDAVIT.md', '04_CERTIFICATE_OF_SERVICE.md']
    existing_files = [f['filename'] for f in result['files']]
    for expected in expected_files:
        if expected not in existing_files:
            result['hardening_tasks'].append({
                'priority': 'BLOCKER',
                'file': expected,
                'line': 0,
                'type': 'MISSING_FILE',
                'match': '',
                'action': f'MISSING: {expected} — must create before filing'
            })
            result['blocker_count'] += 1
    
    # Quality score (0-100)
    quality_points = 0
    quality_total = 0
    for file_info in result['files']:
        for check_id, check in file_info.get('quality', {}).items():
            quality_total += 1
            if check.get('present'):
                quality_points += 1
    
    result['quality_score'] = round((quality_points / max(quality_total, 1)) * 100)
    
    return result

def run():
    """Main agent entry point."""
    print("=" * 60)
    print("AGENT E04: FILING HARDENER")
    print("=" * 60)
    print(f"Started: {datetime.now().isoformat()}")
    print(f"Package base: {PKG_BASE}")
    print(f"Filings to harden: {', '.join(FILING_PACKAGES.keys())}")
    
    results = {}
    total_blockers = 0
    total_issues = 0
    
    for filing_id, config in FILING_PACKAGES.items():
        print(f"\n--- Analyzing {filing_id}: {config['name']} ---")
        result = analyze_package(filing_id, config)
        results[filing_id] = result
        total_blockers += result['blocker_count']
        total_issues += result['total_issues']
        
        print(f"  Files: {len(result['files'])}")
        print(f"  Issues: {result['total_issues']}")
        print(f"  Blockers: {result['blocker_count']}")
        print(f"  Quality: {result['quality_score']}%")
        print(f"  Words: {result['total_words']:,}")
    
    # Save reports
    report = {
        'agent_id': 'E04',
        'name': 'Filing Hardener',
        'generated': datetime.now().isoformat(),
        'results': results,
        'summary': {
            'total_filings': len(results),
            'total_blockers': total_blockers,
            'total_issues': total_issues,
            'court_ready': sum(1 for r in results.values() if r['blocker_count'] == 0),
        }
    }
    
    json_path = os.path.join(REPORT_DIR, 'FILING_HARDENING_REPORT.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)
    
    md_path = os.path.join(REPORT_DIR, 'FILING_HARDENING_REPORT.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write("# 🔨 Filing Hardening Report (Agent E04)\n\n")
        f.write(f"Generated: {report['generated']}\n\n")
        f.write(f"**{len(results)} filings analyzed** | ")
        f.write(f"**{total_blockers} BLOCKERS** | ")
        f.write(f"**{total_issues} total issues**\n\n")
        
        for filing_id, result in results.items():
            status_emoji = "✅" if result['blocker_count'] == 0 else "🔴"
            f.write(f"## {status_emoji} {filing_id}: {result['name']}\n\n")
            f.write(f"| Metric | Value |\n|--------|-------|\n")
            f.write(f"| Court | {result['court']} |\n")
            f.write(f"| Case # | {result['case_number']} |\n")
            f.write(f"| Filing Fee | {result['filing_fee']} |\n")
            f.write(f"| Files | {len(result['files'])} |\n")
            f.write(f"| Words | {result['total_words']:,} |\n")
            f.write(f"| Quality Score | {result['quality_score']}% |\n")
            f.write(f"| Blockers | {result['blocker_count']} |\n")
            f.write(f"| Total Issues | {result['total_issues']} |\n\n")
            
            if result['hardening_tasks']:
                f.write("### Hardening Tasks\n\n")
                for task in sorted(result['hardening_tasks'], key=lambda t: {'BLOCKER': 0, 'HIGH': 1, 'MEDIUM': 2}.get(t['priority'], 3)):
                    emoji = {"BLOCKER": "🔴", "HIGH": "🟠", "MEDIUM": "🟡"}.get(task['priority'], "⚪")
                    f.write(f"- {emoji} **[{task['priority']}]** {task['action']}")
                    if task.get('match'):
                        f.write(f" — `{task['match']}`")
                    f.write("\n")
            f.write("\n---\n\n")
    
    print(f"\n{'=' * 60}")
    print(f"AGENT E04 COMPLETE")
    print(f"  Filings analyzed: {len(results)}")
    print(f"  Total blockers: {total_blockers}")
    print(f"  Total issues: {total_issues}")
    print(f"  Court-ready: {report['summary']['court_ready']}/{len(results)}")
    print(f"  Reports: {md_path}")
    
    return report

if __name__ == '__main__':
    run()
