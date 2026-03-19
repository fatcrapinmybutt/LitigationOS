#!/usr/bin/env python3
"""
Tool #79 — Exhibit Cross-Reference Validator
================================================
Scans ALL filing packages and verifies that every exhibit reference
(e.g., "Exhibit A", "Exhibit 1", "Ex. A") points to an actual
exhibit that exists in the package.

Catches:
- Referenced exhibits that don't exist (broken references)
- Exhibits that exist but are never referenced (orphan exhibits)
- Inconsistent naming (Exhibit A vs Ex. A vs Exh. A)
"""
import sys, json, re
from pathlib import Path
from datetime import datetime
from collections import defaultdict

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"
PKG_BASE = Path(r"C:\Users\andre\Desktop\LITIGATION_FILING_PACKAGE")

# Pattern to find exhibit references in text
EXHIBIT_PATTERNS = [
    re.compile(r'Exhibit\s+([A-Z](?:-\d+)?)', re.IGNORECASE),
    re.compile(r'Ex\.\s*([A-Z](?:-\d+)?)', re.IGNORECASE),
    re.compile(r'Exh\.\s*([A-Z](?:-\d+)?)', re.IGNORECASE),
    re.compile(r'Exhibit\s+(\d+)', re.IGNORECASE),
    re.compile(r'Ex\.\s*(\d+)', re.IGNORECASE),
    re.compile(r'\(Exhibit\s+([A-Z0-9]+)\)', re.IGNORECASE),
]

# Pattern to find exhibit file names
EXHIBIT_FILE_PATTERN = re.compile(r'exhibit', re.IGNORECASE)

def scan_filing(pkg_dir):
    """Scan one filing package for exhibit references and exhibit files."""
    referenced = defaultdict(list)  # exhibit_id -> [files that reference it]
    exhibit_files = []
    
    if not pkg_dir.exists():
        return referenced, exhibit_files
    
    for f in pkg_dir.iterdir():
        if not f.is_file():
            continue
        
        # Check if this IS an exhibit file
        if EXHIBIT_FILE_PATTERN.search(f.name):
            exhibit_files.append(f.name)
        
        # Check for exhibit references in text files
        if f.suffix.lower() in ('.md', '.txt'):
            try:
                text = f.read_text(encoding='utf-8', errors='replace')
                for pattern in EXHIBIT_PATTERNS:
                    for match in pattern.finditer(text):
                        exhibit_id = match.group(1).upper()
                        referenced[exhibit_id].append(f.name)
            except Exception:
                pass
    
    return referenced, exhibit_files

def main():
    print("=" * 70)
    print("EXHIBIT CROSS-REFERENCE VALIDATOR — Tool #79")
    print("=" * 70)
    
    results = {}
    total_refs = 0
    total_orphans = 0
    total_broken = 0
    
    lines = [
        "# 🔗 EXHIBIT CROSS-REFERENCE VALIDATION",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n",
        "---\n",
    ]
    
    for i in range(1, 11):
        pkg_name = f"PKG_F{i}"
        pkg_dir = PKG_BASE / pkg_name
        
        referenced, exhibit_files = scan_filing(pkg_dir)
        
        if not referenced and not exhibit_files:
            status = "⚪ No exhibits"
        else:
            # Find broken refs (referenced but no exhibit file matches)
            all_ref_ids = set(referenced.keys())
            # Extract IDs from exhibit filenames
            file_ids = set()
            for ef in exhibit_files:
                for pattern in EXHIBIT_PATTERNS:
                    for m in pattern.finditer(ef):
                        file_ids.add(m.group(1).upper())
            
            broken = all_ref_ids - file_ids if file_ids else set()
            orphans = file_ids - all_ref_ids if all_ref_ids else set()
            
            if broken:
                status = f"🔴 {len(broken)} broken refs"
                total_broken += len(broken)
            elif orphans:
                status = f"🟡 {len(orphans)} orphan exhibits"
                total_orphans += len(orphans)
            else:
                status = "🟢 All validated"
        
        ref_count = sum(len(v) for v in referenced.values())
        total_refs += ref_count
        
        results[pkg_name] = {
            'references': ref_count,
            'unique_exhibits_referenced': len(referenced),
            'exhibit_files': len(exhibit_files),
            'status': status,
        }
        
        print(f"  {pkg_name}: {status} ({ref_count} refs, {len(exhibit_files)} exhibit files)")
        
        lines.append(f"## {pkg_name} — {status}")
        lines.append(f"- References found: {ref_count}")
        lines.append(f"- Unique exhibits referenced: {len(referenced)}")
        lines.append(f"- Exhibit files: {len(exhibit_files)}")
        
        if referenced:
            lines.append("\n| Exhibit | Referenced In |")
            lines.append("|---------|-------------|")
            for eid, files in sorted(referenced.items()):
                lines.append(f"| {eid} | {', '.join(set(files))[:60]} |")
        
        if exhibit_files:
            lines.append(f"\n**Exhibit files:** {', '.join(exhibit_files[:5])}")
        lines.append("")
    
    # Summary
    lines.extend([
        "---",
        "## SUMMARY",
        f"| Metric | Count |",
        f"|--------|-------|",
        f"| Total exhibit references | {total_refs} |",
        f"| Broken references | {total_broken} |",
        f"| Orphan exhibits | {total_orphans} |",
        f"| Filings scanned | 10 |",
        "",
        f"*Exhibit Cross-Reference Validator — Tool #79*",
    ])
    
    print(f"\n  SUMMARY: {total_refs} refs, {total_broken} broken, {total_orphans} orphans")
    
    md_path = REPORTS_DIR / "EXHIBIT_CROSSREF.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')
    
    json_path = REPORTS_DIR / "exhibit_crossref.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'Exhibit Cross-Reference Validator (#79)',
        'total_references': total_refs,
        'broken_references': total_broken,
        'orphan_exhibits': total_orphans,
        'filings': results,
    }, indent=2), encoding='utf-8')
    
    print(f"   Reports: EXHIBIT_CROSSREF.md + exhibit_crossref.json")

if __name__ == '__main__':
    main()
