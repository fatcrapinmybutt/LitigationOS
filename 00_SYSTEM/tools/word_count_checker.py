#!/usr/bin/env python3
"""
Tool #82 — Filing Word Count & Page Limit Checker
=====================================================
Verifies all filings comply with Michigan court rules:
- MCR 7.212(B): COA briefs ≤ 50 pages or 16,000 words
- MCR 7.305(A): MSC applications ≤ 50 pages
- MCR 2.119(A)(2): Motion briefs ≤ 20 pages  
- FRCP 7(d) / Local Rule 7.1: Federal briefs ≤ 25 pages
- JTC Rules: No specific page limit but conciseness required

Reports which filings are under/over limits.
"""
import sys, json, re
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"
PKG_BASE = Path(r"C:\Users\andre\Desktop\LITIGATION_FILING_PACKAGE")

# Page limits by filing type (conservative estimates)
# Roughly 250 words per page for court filings
FILING_LIMITS = {
    'PKG_F1': {'name': 'Emergency Parenting Time', 'court': '14th Circuit', 'max_pages': 20, 'rule': 'MCR 2.119(A)(2)'},
    'PKG_F2': {'name': 'Fraud on Court', 'court': '14th Circuit', 'max_pages': 20, 'rule': 'MCR 2.119(A)(2)'},
    'PKG_F3': {'name': 'Judicial Disqualification', 'court': '14th Circuit', 'max_pages': 20, 'rule': 'MCR 2.119(A)(2)'},
    'PKG_F4': {'name': '§1983 Federal Complaint', 'court': 'USDC WDMI', 'max_pages': 25, 'rule': 'Local Rule 7.1(d)'},
    'PKG_F5': {'name': 'MSC Superintending Control', 'court': 'MSC', 'max_pages': 50, 'rule': 'MCR 7.305(A)'},
    'PKG_F6': {'name': 'JTC Complaint', 'court': 'JTC', 'max_pages': 50, 'rule': 'JTC Rule 4 (no strict limit)'},
    'PKG_F7': {'name': 'Custody Modification', 'court': '14th Circuit', 'max_pages': 20, 'rule': 'MCR 2.119(A)(2)'},
    'PKG_F8': {'name': 'COA Leave Application', 'court': 'COA', 'max_pages': 50, 'rule': 'MCR 7.305(A)'},
    'PKG_F9': {'name': 'COA Appeal Brief', 'court': 'COA', 'max_pages': 50, 'rule': 'MCR 7.212(B)'},
    'PKG_F10': {'name': 'AGC Complaint', 'court': 'AGC', 'max_pages': 50, 'rule': 'No strict limit'},
}

WORDS_PER_PAGE = 250  # Standard court assumption

def count_words_in_file(filepath):
    """Count words in a markdown/text file, excluding formatting."""
    try:
        text = filepath.read_text(encoding='utf-8', errors='replace')
        # Remove markdown formatting
        text = re.sub(r'[#*_\-|`>\[\]]', ' ', text)
        text = re.sub(r'https?://\S+', '', text)
        text = re.sub(r'\s+', ' ', text)
        words = len(text.split())
        return words
    except:
        return 0

def main():
    print("=" * 70)
    print("FILING WORD COUNT & PAGE LIMIT CHECKER — Tool #82")
    print("=" * 70)
    
    results = {}
    total_words = 0
    over_limit = 0
    
    lines = [
        "# 📏 FILING WORD COUNT & PAGE LIMIT REPORT",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
        f"*Standard: {WORDS_PER_PAGE} words/page*\n",
        "---\n",
        "| Filing | Court | Words | Pages | Limit | Status | Rule |",
        "|--------|-------|-------|-------|-------|--------|------|",
    ]
    
    for pkg_name, limits in FILING_LIMITS.items():
        pkg_dir = PKG_BASE / pkg_name
        pkg_words = 0
        file_count = 0
        
        if pkg_dir.exists():
            for f in pkg_dir.iterdir():
                if f.suffix.lower() in ('.md', '.txt') and f.is_file():
                    wc = count_words_in_file(f)
                    pkg_words += wc
                    file_count += 1
        
        est_pages = round(pkg_words / WORDS_PER_PAGE, 1)
        max_pages = limits['max_pages']
        
        if est_pages > max_pages:
            status = f"🔴 OVER ({est_pages - max_pages:.0f}p)"
            over_limit += 1
        elif est_pages > max_pages * 0.8:
            status = f"🟡 NEAR ({max_pages - est_pages:.0f}p left)"
        else:
            status = "🟢 OK"
        
        total_words += pkg_words
        results[pkg_name] = {
            'name': limits['name'],
            'court': limits['court'],
            'words': pkg_words,
            'est_pages': est_pages,
            'max_pages': max_pages,
            'rule': limits['rule'],
            'status': 'over' if est_pages > max_pages else 'near' if est_pages > max_pages * 0.8 else 'ok',
            'files': file_count,
        }
        
        lines.append(f"| {pkg_name} | {limits['court']} | {pkg_words:,} | {est_pages} | {max_pages} | {status} | {limits['rule']} |")
        print(f"  {pkg_name}: {pkg_words:>6,} words ({est_pages:>5} pages / {max_pages} max) {status}")
    
    lines.extend([
        "",
        f"**Total words across all filings: {total_words:,}**",
        f"**Filings over limit: {over_limit}/10**",
        "",
        "## Notes",
        "- Word counts include ALL package files (main filing + supporting docs)",
        "- Main filing document is what counts for page limits — supporting docs are separate",
        "- Court rules count only the BRIEF/MOTION body, not exhibits or certificates",
        "- If over limit, consider: (1) trim argument, (2) move detail to exhibits, (3) file leave to exceed",
        "",
        f"*Filing Word Count Checker — Tool #82*",
    ])
    
    md_path = REPORTS_DIR / "WORD_COUNT_REPORT.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')
    
    json_path = REPORTS_DIR / "word_count_report.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'Filing Word Count Checker (#82)',
        'total_words': total_words,
        'over_limit': over_limit,
        'words_per_page': WORDS_PER_PAGE,
        'filings': results,
    }, indent=2), encoding='utf-8')
    
    print(f"\n✅ {total_words:,} total words, {over_limit} over limit")
    print(f"   Reports: WORD_COUNT_REPORT.md + word_count_report.json")

if __name__ == '__main__':
    main()
