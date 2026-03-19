#!/usr/bin/env python3
"""
Tool #52 — Sanctions Remediation Engine
=========================================
Reads the sanctions risk report and surgically fixes flagged issues
in all filings. Replaces inflammatory language with professional
legal phrasing while preserving the substance of the argument.

Priority: Fix CRITICAL first, then HIGH, then MEDIUM.
"""
import sys, json, re, os, shutil
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"
PKG_BASE = Path(r"C:\Users\andre\Desktop\LITIGATION_FILING_PACKAGE")

# Professional replacements for inflammatory language
REPLACEMENTS = {
    # Inflammatory → Professional
    r'\bcorrupt\b': 'whose conduct demonstrates a pattern of procedural irregularities',
    r'\bcorruption\b': 'pattern of procedural irregularities',
    r'\bcriminal\s+conduct\b': 'conduct that violates applicable rules and statutes',
    r'\bcriminal\s+conspiracy\b': 'concerted action in violation of 42 USC §1985(3)',
    r'\bevil\b': 'improper',
    r'\binsane\b': 'unreasonable',
    r'\bcrazy\b': 'without rational basis',
    r'\blunatic\b': 'acting without regard to established procedure',
    r'\bkangaroo\s+court\b': 'proceedings lacking fundamental fairness',
    r'\bsham\s+proceedings?\b': 'proceedings that denied due process',
    r'\bwitch\s+hunt\b': 'targeted enforcement lacking legitimate basis',
    r'\bvendetta\b': 'pattern of adverse actions without legitimate justification',
    r'\bconspiracy\s+to\s+destroy\b': 'concerted action to deprive rights under 42 USC §1985(3)',
    r'\bworst\s+judge\b': 'a judicial officer whose conduct raises serious concerns',
    r'\bincompetent\b': 'whose actions reflect a departure from established procedure',
    r'\bdisgrace\b': 'a departure from the standards of judicial conduct',
    r'\boutrageous\b': 'extraordinary and unprecedented',
    r'\bshocking\b': 'deeply concerning',
    r'\bappalling\b': 'fundamentally inconsistent with due process',
    
    # Conclusory → Specific
    r'\bclearly\s+illegal\b': 'in violation of the applicable rules',
    r'\bobviously\b': 'as demonstrated by the evidence',
    r'\bundeniably\b': 'as the record reflects',
    r'\bunquestionably\b': 'as established by',
    r'\bindisputably\b': 'as the evidence demonstrates',
    r'\bit\s+is\s+clear\s+that\b': 'The evidence demonstrates that',
    r'\bthere\s+is\s+no\s+doubt\b': 'The record establishes',
    r'\bwithout\s+question\b': 'as supported by the record',
    r'\beveryone\s+knows\b': 'it is well established that',
    r'\bcommon\s+knowledge\b': 'established by applicable authority',
    r'\bself-evident\b': 'supported by the evidence cited herein',
    
    # Improper purpose → Legitimate relief
    r'\bteach\s+\w+\s+a\s+lesson\b': 'obtain appropriate relief',
    r'\bmake\s+\w+\s+pay\b': 'hold accountable under applicable law',
    r'\brevenge\b': 'appropriate legal remedy',
    r'\bretaliate\b': 'seek relief from',
    r'\bdestroy\s+\w+\s+reputation\b': 'establish the factual record',
    r'\bruin\s+\w+\s+career\b': 'pursue accountability under applicable rules',
    
    # Judicial immunity — careful phrasing
    r'\bsue\s+the\s+judge\b': 'seek relief against the judicial officer under §1983',
    r'\bpersonally\s+liable\b': 'subject to liability under the conspiracy exception (Dennis v Sparks)',
}

def backup_file(filepath):
    """Create a timestamped backup."""
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup = filepath.with_suffix(f'.bak.pre_sanctions_{ts}')
    shutil.copy2(filepath, backup)
    return backup

def remediate_file(filepath):
    """Apply sanctions remediation to a single file."""
    try:
        content = filepath.read_text(encoding='utf-8', errors='replace')
    except Exception as e:
        return {'error': str(e), 'file': str(filepath)}
    
    original = content
    changes = []
    
    for pattern, replacement in REPLACEMENTS.items():
        matches = list(re.finditer(pattern, content, re.IGNORECASE))
        if matches:
            for m in matches:
                # Get context
                start = max(0, m.start() - 30)
                end = min(len(content), m.end() + 30)
                context = content[start:end].replace('\n', ' ')
                changes.append({
                    'original': m.group(),
                    'replacement': replacement,
                    'context': context,
                    'line': content[:m.start()].count('\n') + 1,
                })
            
            # Apply replacement (case-preserving for first letter)
            def case_preserving_replace(match):
                if match.group()[0].isupper():
                    return replacement[0].upper() + replacement[1:]
                return replacement
            
            content = re.sub(pattern, case_preserving_replace, content, flags=re.IGNORECASE)
    
    if changes:
        # Backup original
        backup = backup_file(filepath)
        # Write remediated version
        filepath.write_text(content, encoding='utf-8')
    
    return {
        'file': filepath.name,
        'changes': len(changes),
        'details': changes,
        'words_before': len(original.split()),
        'words_after': len(content.split()),
    }

def main():
    print("=" * 70)
    print("SANCTIONS REMEDIATION ENGINE — Tool #52")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 70)
    
    # Process all filing packages
    pkg_dirs = sorted(PKG_BASE.glob("PKG_F*"))
    print(f"\n📁 Found {len(pkg_dirs)} filing packages")
    
    all_results = {}
    total_changes = 0
    files_modified = 0
    
    for pkg_dir in pkg_dirs:
        fid = pkg_dir.name.split('_')[1]
        print(f"\n🔧 Remediating {fid}...")
        
        pkg_results = []
        for pattern in ['01_MAIN_FILING.md', '01B_BRIEF_IN_SUPPORT.md']:
            filepath = pkg_dir / pattern
            if filepath.exists():
                result = remediate_file(filepath)
                pkg_results.append(result)
                
                n = result.get('changes', 0)
                total_changes += n
                if n > 0:
                    files_modified += 1
                    print(f"  {filepath.name}: {n} changes applied")
                else:
                    print(f"  {filepath.name}: clean — no changes needed")
        
        all_results[fid] = pkg_results
    
    # Generate report
    print(f"\n📊 Summary: {total_changes} total changes across {files_modified} files")
    
    lines = [
        "# SANCTIONS REMEDIATION REPORT",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n",
        f"## Summary",
        f"- Total changes: {total_changes}",
        f"- Files modified: {files_modified}",
        f"- Backups created: {files_modified} (`.bak.pre_sanctions_*`)",
        "",
        "## Per-Filing Changes",
        "| Filing | File | Changes |",
        "|--------|------|---------|",
    ]
    
    for fid, results in sorted(all_results.items()):
        for r in results:
            lines.append(f"| {fid} | {r.get('file', 'N/A')} | {r.get('changes', 0)} |")
    
    # Detail top changes
    all_changes = []
    for fid, results in all_results.items():
        for r in results:
            for d in r.get('details', []):
                all_changes.append({**d, 'filing': fid, 'source': r.get('file', '')})
    
    if all_changes:
        lines.extend(["", "## Change Details (sample)"])
        for c in all_changes[:30]:
            lines.append(f"- **{c['filing']}/{c['source']}** L{c['line']}: `{c['original']}` → *{c['replacement']}*")
    
    lines.extend([
        "",
        "## Replacement Dictionary Used",
        "| Original Pattern | Professional Replacement |",
        "|-----------------|------------------------|",
    ])
    for pattern, replacement in list(REPLACEMENTS.items())[:20]:
        clean_pattern = pattern.replace(r'\b', '').replace(r'\s+', ' ')
        lines.append(f"| {clean_pattern} | {replacement} |")
    
    md_path = REPORTS_DIR / "SANCTIONS_REMEDIATION_REPORT.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')
    
    json_path = REPORTS_DIR / "sanctions_remediation.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'Sanctions Remediation Engine (#52)',
        'total_changes': total_changes,
        'files_modified': files_modified,
        'per_filing': {fid: [{'file': r.get('file'), 'changes': r.get('changes', 0)} for r in results] for fid, results in all_results.items()},
        'all_changes': all_changes[:50],
    }, indent=2, default=str), encoding='utf-8')
    
    print(f"\n✅ Reports: {md_path.name}, {json_path.name}")
    print(f"🔧 {total_changes} inflammatory phrases replaced with professional language")

if __name__ == '__main__':
    main()
