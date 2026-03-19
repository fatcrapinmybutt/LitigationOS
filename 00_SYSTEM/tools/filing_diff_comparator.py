#!/usr/bin/env python3
"""
Tool #53 — Filing Diff Comparator
====================================
Compares current filing versions against their backup versions to show
exactly what changed during each processing step (convergence, trimming,
sanctions remediation, etc.).

Generates readable diff reports for Andrew to review before filing.
"""
import sys, json, os, difflib
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"
PKG_BASE = Path(r"C:\Users\andre\Desktop\LITIGATION_FILING_PACKAGE")

def find_backup_pairs(pkg_dir):
    """Find current files and their most recent backups."""
    pairs = []
    current_files = [f for f in pkg_dir.glob("*.md") if '.bak.' not in f.name]
    
    for current in current_files:
        # Find all backups for this file
        stem = current.stem
        backups = sorted(
            [f for f in pkg_dir.glob(f"{stem}.md.bak.*")],
            key=lambda f: f.stat().st_mtime,
            reverse=True
        )
        
        if backups:
            pairs.append({
                'current': current,
                'backup': backups[0],  # Most recent backup
                'all_backups': backups,
            })
    
    return pairs

def generate_diff(old_path, new_path, context_lines=3):
    """Generate a unified diff between two files."""
    try:
        old_text = old_path.read_text(encoding='utf-8', errors='replace').splitlines()
        new_text = new_path.read_text(encoding='utf-8', errors='replace').splitlines()
    except Exception as e:
        return f"Error reading files: {e}", 0, 0, 0
    
    diff = list(difflib.unified_diff(
        old_text, new_text,
        fromfile=f"BEFORE ({old_path.name})",
        tofile=f"AFTER ({new_path.name})",
        lineterm='',
        n=context_lines
    ))
    
    additions = sum(1 for line in diff if line.startswith('+') and not line.startswith('+++'))
    deletions = sum(1 for line in diff if line.startswith('-') and not line.startswith('---'))
    
    return '\n'.join(diff), len(diff), additions, deletions

def generate_summary_diff(old_path, new_path):
    """Generate a human-readable summary of changes."""
    try:
        old_text = old_path.read_text(encoding='utf-8', errors='replace')
        new_text = new_path.read_text(encoding='utf-8', errors='replace')
    except:
        return "Could not read files"
    
    old_words = len(old_text.split())
    new_words = len(new_text.split())
    word_diff = new_words - old_words
    
    old_lines = len(old_text.splitlines())
    new_lines = len(new_text.splitlines())
    
    summary = []
    summary.append(f"Words: {old_words:,} → {new_words:,} ({word_diff:+,})")
    summary.append(f"Lines: {old_lines:,} → {new_lines:,} ({new_lines - old_lines:+,})")
    
    # Find changed sections (headers)
    old_headers = [l.strip() for l in old_text.splitlines() if l.strip().startswith('#')]
    new_headers = [l.strip() for l in new_text.splitlines() if l.strip().startswith('#')]
    
    added_headers = set(new_headers) - set(old_headers)
    removed_headers = set(old_headers) - set(new_headers)
    
    if added_headers:
        summary.append(f"Sections added: {len(added_headers)}")
    if removed_headers:
        summary.append(f"Sections removed: {len(removed_headers)}")
    
    return ' | '.join(summary)

def main():
    print("=" * 70)
    print("FILING DIFF COMPARATOR — Tool #53")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 70)
    
    pkg_dirs = sorted(PKG_BASE.glob("PKG_F*"))
    print(f"\n📁 Found {len(pkg_dirs)} filing packages")
    
    all_diffs = {}
    total_pairs = 0
    total_changes = 0
    
    for pkg_dir in pkg_dirs:
        fid = pkg_dir.name.split('_')[1]
        pairs = find_backup_pairs(pkg_dir)
        
        if not pairs:
            print(f"\n{fid}: No backups found")
            continue
        
        print(f"\n📄 {fid}: {len(pairs)} files with backups")
        filing_diffs = []
        
        for pair in pairs:
            current = pair['current']
            backup = pair['backup']
            
            summary = generate_summary_diff(backup, current)
            diff_text, diff_lines, adds, dels = generate_diff(backup, current)
            
            total_pairs += 1
            if diff_lines > 0:
                total_changes += 1
            
            result = {
                'file': current.name,
                'backup': backup.name,
                'backup_count': len(pair['all_backups']),
                'summary': summary,
                'additions': adds,
                'deletions': dels,
                'diff_lines': diff_lines,
            }
            filing_diffs.append(result)
            
            status = f"+{adds}/-{dels}" if diff_lines > 0 else "identical"
            print(f"  {current.name} vs {backup.name}: {status}")
            if diff_lines > 0:
                print(f"    {summary}")
        
        all_diffs[fid] = filing_diffs
    
    print(f"\n📊 Total: {total_pairs} file pairs compared, {total_changes} with changes")
    
    # Generate report
    lines = [
        "# FILING DIFF COMPARISON REPORT",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n",
        f"## Summary",
        f"- File pairs compared: {total_pairs}",
        f"- Files with changes: {total_changes}",
        "",
        "## Per-Filing Changes",
        "| Filing | File | Additions | Deletions | Summary |",
        "|--------|------|-----------|-----------|---------|",
    ]
    
    for fid, diffs in sorted(all_diffs.items()):
        for d in diffs:
            if d['diff_lines'] > 0:
                lines.append(f"| {fid} | {d['file']} | +{d['additions']} | -{d['deletions']} | {d['summary']} |")
    
    # Backup inventory
    lines.extend(["", "## Backup Inventory"])
    for fid, diffs in sorted(all_diffs.items()):
        for d in diffs:
            if d['backup_count'] > 0:
                lines.append(f"- **{fid}/{d['file']}**: {d['backup_count']} backup(s)")
    
    md_path = REPORTS_DIR / "FILING_DIFF_REPORT.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')
    
    json_path = REPORTS_DIR / "filing_diff.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'Filing Diff Comparator (#53)',
        'total_pairs': total_pairs,
        'total_changes': total_changes,
        'diffs': all_diffs,
    }, indent=2, default=str), encoding='utf-8')
    
    print(f"\n✅ Reports: {md_path.name}, {json_path.name}")

if __name__ == '__main__':
    main()
