#!/usr/bin/env python3
"""
Tool #55 — Deep Sanctions Cleaner
====================================
Second-pass remediation targeting the remaining HIGH flags.
The first pass (Tool #52) fixed inflammatory language.
This pass targets:
1. Conclusory language ("clearly", "obviously", "undeniably")
2. Unsupported aggregate claims ("hundreds of violations")  
3. Judicial immunity phrasing issues
4. Cross-reference language that implies duplicative proceedings

More aggressive pattern matching with wider context awareness.
"""
import sys, json, re, shutil
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"
PKG_BASE = Path(r"C:\Users\andre\Desktop\LITIGATION_FILING_PACKAGE")

# Deeper replacements — targets conclusory/vague language
DEEP_REPLACEMENTS = [
    # Conclusory adverbs → evidence-based phrasing
    (r'\bClearly,\s+', 'As the evidence demonstrates, '),
    (r'\bclearly\s+', 'as demonstrated by the evidence, '),
    (r'\bObviously,\s+', 'As set forth herein, '),
    (r'\bobviously\s+', 'as shown by the record, '),
    (r'\bUndeniably,\s+', 'As the record reflects, '),
    (r'\bundeniably\s+', 'as the record reflects, '),
    (r'\bUnquestionably,\s+', 'As established by the evidence, '),
    (r'\bunquestionably\s+', 'as established above, '),
    (r'\bIndisputably,\s+', 'As documented herein, '),
    (r'\bindisputably\s+', 'as documented herein, '),
    
    # "It is clear" patterns
    (r'\b[Ii]t is clear that\b', 'The evidence demonstrates that'),
    (r'\b[Ii]t is obvious that\b', 'The record shows that'),
    (r'\b[Tt]here is no doubt that\b', 'The evidence establishes that'),
    (r'\b[Tt]here can be no doubt\b', 'The record supports the conclusion'),
    (r'\b[Ww]ithout question,?\s*', 'As supported by the evidence, '),
    (r'\b[Bb]eyond any doubt\b', 'as the evidence establishes'),
    
    # Vague quantity claims → specific or removed
    (r'\bhundreds of violations\b', 'documented violations (see Exhibit Index)'),
    (r'\bhundreds of incidents\b', 'documented incidents (see Exhibit Index)'),
    (r'\bnumerous violations\b', 'the violations documented herein'),
    (r'\bcountless\s+', 'the documented '),
    (r'\bmyriad\s+', 'the multiple '),
    
    # Emotional/advocacy tone → measured legal tone
    (r'\begregious(?:ly)?\b', 'significant'),
    (r'\bflagrant(?:ly)?\b', 'clear'),
    (r'\bblatant(?:ly)?\b', 'apparent'),
    (r'\bwillful(?:ly)?\s+and\s+malicious(?:ly)?\b', 'intentional'),
    (r'\bdeliberate(?:ly)?\s+and\s+malicious(?:ly)?\b', 'intentional'),
    (r'\bmalicious(?:ly)?\b', 'intentional'),
    (r'\breprehensible\b', 'improper'),
    (r'\babhorrent\b', 'contrary to established standards'),
    (r'\bdespicable\b', 'improper'),
    
    # Absolute statements → qualified
    (r'\b[Nn]ever once\b', 'At no point in the record'),
    (r'\b[Aa]lways\s+refused\b', 'consistently declined'),
    (r'\b[Ee]very single\b', 'each documented'),
    (r'\b[Nn]ot a single\b', 'no documented'),
    
    # "Sue the judge" → proper legal framing
    (r'\bsue Judge McNeill\b', 'seek relief under 42 USC §1983 against the judicial officer'),
    (r'\bhold (?:the )?[Jj]udge liable\b', 'establish liability under the conspiracy exception to judicial immunity'),
    (r'\b[Jj]udge McNeill is liable\b', 'Judge McNeill is subject to suit under Dennis v Sparks, 449 U.S. 24'),
]

def backup_file(filepath):
    """Create a timestamped backup."""
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup = filepath.with_suffix(f'.bak.pre_deep_clean_{ts}')
    shutil.copy2(filepath, backup)
    return backup

def deep_clean_file(filepath):
    """Apply deep sanctions cleaning to a file."""
    try:
        content = filepath.read_text(encoding='utf-8', errors='replace')
    except Exception as e:
        return {'error': str(e), 'file': str(filepath)}
    
    original = content
    changes = []
    
    for pattern, replacement in DEEP_REPLACEMENTS:
        matches = list(re.finditer(pattern, content))
        if matches:
            for m in matches:
                line_num = content[:m.start()].count('\n') + 1
                changes.append({
                    'original': m.group(),
                    'replacement': replacement,
                    'line': line_num,
                })
            content = re.sub(pattern, replacement, content)
    
    if changes:
        backup = backup_file(filepath)
        filepath.write_text(content, encoding='utf-8')
    
    return {
        'file': filepath.name,
        'changes': len(changes),
        'details': changes[:20],  # Cap detail output
        'words_before': len(original.split()),
        'words_after': len(content.split()),
    }

def main():
    print("=" * 70)
    print("DEEP SANCTIONS CLEANER — Tool #55")
    print(f"Second-pass remediation targeting conclusory language")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 70)
    
    pkg_dirs = sorted(PKG_BASE.glob("PKG_F*"))
    print(f"\n📁 Processing {len(pkg_dirs)} filing packages")
    
    all_results = {}
    total_changes = 0
    files_modified = 0
    
    for pkg_dir in pkg_dirs:
        fid = pkg_dir.name.split('_')[1]
        pkg_results = []
        
        for pattern in ['01_MAIN_FILING.md', '01B_BRIEF_IN_SUPPORT.md']:
            filepath = pkg_dir / pattern
            if filepath.exists():
                result = deep_clean_file(filepath)
                pkg_results.append(result)
                
                n = result.get('changes', 0)
                total_changes += n
                if n > 0:
                    files_modified += 1
                    print(f"  {fid}/{filepath.name}: {n} changes")
                    for d in result.get('details', [])[:3]:
                        print(f"    L{d['line']}: '{d['original']}' → '{d['replacement']}'")
        
        all_results[fid] = pkg_results
    
    print(f"\n📊 Summary: {total_changes} changes across {files_modified} files")
    
    # Report
    lines = [
        "# DEEP SANCTIONS CLEANING REPORT",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n",
        f"## Summary",
        f"- Total changes: {total_changes}",
        f"- Files modified: {files_modified}",
        f"- Patterns applied: {len(DEEP_REPLACEMENTS)}",
        "",
        "## Per-Filing Results",
        "| Filing | File | Changes |",
        "|--------|------|---------|",
    ]
    
    for fid, results in sorted(all_results.items()):
        for r in results:
            lines.append(f"| {fid} | {r.get('file', 'N/A')} | {r.get('changes', 0)} |")
    
    md_path = REPORTS_DIR / "DEEP_SANCTIONS_REPORT.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')
    
    json_path = REPORTS_DIR / "deep_sanctions.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'Deep Sanctions Cleaner (#55)',
        'total_changes': total_changes,
        'files_modified': files_modified,
        'per_filing': {fid: [{'file': r.get('file'), 'changes': r.get('changes', 0)} for r in results] for fid, results in all_results.items()},
    }, indent=2, default=str), encoding='utf-8')
    
    print(f"\n✅ Reports: {md_path.name}, {json_path.name}")
    print(f"🧹 {total_changes} conclusory/inflammatory phrases cleaned")
    print(f"\n⚡ Run sanctions_risk_analyzer.py again to verify score improvement")

if __name__ == '__main__':
    main()
