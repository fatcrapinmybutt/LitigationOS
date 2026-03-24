#!/usr/bin/env python3
"""Quick automated scan of all 10 filings for known issues."""
import sys, os, re, glob
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

BASE = r"C:\Users\andre\Desktop\LITIGATION_FILING_PACKAGE"
CRITICAL_PATTERNS = {
    'HALLUCINATED_NAMES': [
        (r'Amy McNeill', 'CRITICAL: Wrong judge name — should be "Jenny L. McNeill"'),
        (r'McNeill-Hoopes', 'CRITICAL: Wrong judge name variant'),
        (r'Emily Ann\b', 'HIGH: Wrong middle name — should be "Emily A."'),
        (r'Emily M\.', 'HIGH: Wrong middle initial'),
        (r'Tiffany', 'HIGH: Wrong name for Emily'),
    ],
    'INFLATED_STATS': [
        (r'24\s+(?:of\s+)?(?:55\s+)?ex\s*[- ]?parte', 'CRITICAL: Inflated ex-parte count — should be exactly 2'),
        (r'43\.6%', 'CRITICAL: Inflated percentage from old stats'),
        (r'52\s+ex\s*[- ]?parte', 'CRITICAL: Inflated ex-parte count'),
        (r'55\s+orders', 'HIGH: "55 orders" is inflated count'),
        (r'308,?704', 'CRITICAL: Old inflated evidence_quotes count'),
        (r'1,?435\s+document', 'CRITICAL: DB-derived document count'),
        (r'212\s+database', 'CRITICAL: DB-derived reference count'),
        (r'126\s+violation', 'HIGH: May be DB-derived violation count'),
        (r'91%?\s*alienation', 'CRITICAL: Pseudo-scientific score — fabricated'),
        (r'9\s+CPS\s+investigation', 'CRITICAL: Fabricated CPS count'),
    ],
    'PLACEHOLDERS': [
        (r'\[ANDREW_REQUIRED\]', 'HIGH: Unfilled placeholder'),
        (r'\[INSERT\s', 'HIGH: Unfilled placeholder'),
        (r'\[ATTACH\s', 'HIGH: Unfilled placeholder'),
        (r'\[TBD\]', 'MEDIUM: Unfilled placeholder'),
        (r'\[VERIFY\]', 'MEDIUM: Needs verification'),
        (r'\[DATE\]', 'MEDIUM: Missing date'),
        (r'\[CASE\s*NUMBER\]', 'HIGH: Missing case number'),
        (r'\[EXHIBIT\s', 'MEDIUM: Unfilled exhibit reference'),
    ],
    'DB_LANGUAGE': [
        (r'database\s+(?:shows?|contains?|reveals?|references?)', 'HIGH: DB-sourced language in court filing'),
        (r'(?:our|the)\s+database', 'HIGH: References "database" — remove from court filing'),
        (r'litigation_context\.db', 'CRITICAL: Raw DB filename in court filing'),
        (r'SQL\s+query', 'CRITICAL: Technical language in court filing'),
        (r'evidence_quotes', 'CRITICAL: DB table name in court filing'),
        (r'judicial_violations\s+table', 'CRITICAL: DB table name in court filing'),
    ],
    'BERRY_ATTORNEY': [
        (r'Ronald\s+Berry.*(?:attorney|counsel|Esq|represent)', 'CRITICAL: Berry is NOT an attorney'),
        (r'Berry.*(?:P\d{5}|bar\s+number)', 'CRITICAL: Berry has no bar number'),
    ],
}

results = {}
total_issues = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}

# Scan all PKG directories
for pkg_dir in sorted(glob.glob(os.path.join(BASE, 'PKG_F*'))):
    pkg_name = os.path.basename(pkg_dir)
    pkg_issues = []
    
    for md_file in glob.glob(os.path.join(pkg_dir, '*.md')):
        fname = os.path.basename(md_file)
        with open(md_file, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        lines = content.split('\n')
        
        for category, patterns in CRITICAL_PATTERNS.items():
            for pattern, message in patterns:
                for i, line in enumerate(lines, 1):
                    if re.search(pattern, line, re.IGNORECASE):
                        severity = message.split(':')[0]
                        pkg_issues.append({
                            'file': fname,
                            'line': i,
                            'severity': severity,
                            'category': category,
                            'message': message,
                            'context': line.strip()[:120]
                        })
                        total_issues[severity] = total_issues.get(severity, 0) + 1
    
    results[pkg_name] = pkg_issues

# Also scan top-level filing markdown files
for md_file in glob.glob(os.path.join(BASE, '*.md')):
    fname = os.path.basename(md_file)
    if fname.startswith(('00_', '06_EFILING', 'CITATION', 'CROSS', 'ENRICH', 'RED_TEAM', 'SESSION', 'VULN', 'wave')):
        continue  # Skip non-filing docs
    with open(md_file, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    lines = content.split('\n')
    issues = []
    for category, patterns in CRITICAL_PATTERNS.items():
        for pattern, message in patterns:
            for i, line in enumerate(lines, 1):
                if re.search(pattern, line, re.IGNORECASE):
                    severity = message.split(':')[0]
                    issues.append({
                        'file': fname,
                        'line': i,
                        'severity': severity,
                        'category': category,
                        'message': message,
                        'context': line.strip()[:120]
                    })
                    total_issues[severity] = total_issues.get(severity, 0) + 1
    if issues:
        results[f'TOP_LEVEL/{fname}'] = issues

# Report
print('=' * 70)
print('  AUTOMATED FILING SCAN — KNOWN ISSUE PATTERNS')
print('=' * 70)
print()
print(f'  CRITICAL: {total_issues.get("CRITICAL", 0)}')
print(f'  HIGH:     {total_issues.get("HIGH", 0)}')
print(f'  MEDIUM:   {total_issues.get("MEDIUM", 0)}')
print(f'  LOW:      {total_issues.get("LOW", 0)}')
print()

for pkg_name, issues in sorted(results.items()):
    if not issues:
        print(f'  ✅ {pkg_name}: CLEAN — no known issues')
    else:
        crits = sum(1 for i in issues if i['severity'] == 'CRITICAL')
        highs = sum(1 for i in issues if i['severity'] == 'HIGH')
        print(f'\n  ❌ {pkg_name}: {len(issues)} issues ({crits} CRITICAL, {highs} HIGH)')
        for issue in sorted(issues, key=lambda x: {'CRITICAL':0,'HIGH':1,'MEDIUM':2,'LOW':3}.get(x['severity'],4)):
            print(f'    [{issue["severity"]}] {issue["file"]}:{issue["line"]} — {issue["message"]}')
            print(f'      Context: {issue["context"]}')

# Check for child's full name exposure
print('\n\n=== CHILD NAME PROTECTION CHECK (MCR 8.119(H)) ===')
# We won't print the child's name but will check for patterns that aren't "L.D.W."
child_pattern_count = 0
for pkg_dir in sorted(glob.glob(os.path.join(BASE, 'PKG_F*'))):
    for md_file in glob.glob(os.path.join(pkg_dir, '*.md')):
        with open(md_file, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        # Check for L.D.W. usage (should be the ONLY child reference)
        ldw_count = len(re.findall(r'L\.?D\.?W\.?', content))
        if ldw_count > 0:
            fname = os.path.basename(md_file)
            pkg = os.path.basename(pkg_dir)
            print(f'  {pkg}/{fname}: {ldw_count} references to L.D.W. (correct format)')

print('\n=== SCAN COMPLETE ===')
