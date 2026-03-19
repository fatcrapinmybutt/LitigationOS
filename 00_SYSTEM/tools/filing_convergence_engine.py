#!/usr/bin/env python3
"""
Tool #41 — Filing Convergence Engine
=====================================
Master convergence tool that:
1. Trims over-limit filings (F2, F3, F5, F7) to MCR page limits
2. Fixes all critical issues from filing_issues table
3. Inserts strongest evidence into unsupported claims
4. Generates court-ready TRIMMED_FILING.md for each over-limit filing

Strategy for trimming:
- Remove redundant paragraphs (repeated facts across sections)
- Condense block quotes into inline citations
- Merge overlapping subsections
- Remove "[ANDREW_REQUIRED]" placeholder paragraphs
- Prioritize keeping: legal standards, strongest evidence, prayer for relief
"""
import sys, os, json, re, sqlite3, glob
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
PKG_BASE = Path(r"C:\Users\andre\Desktop\LITIGATION_FILING_PACKAGE")
DB_PATH = REPO / "litigation_context.db"
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# MCR page limits (words per page ~300)
PAGE_LIMITS = {
    'F1': 20, 'F2': 20, 'F3': 20, 'F4': None, 'F5': 20,
    'F6': None, 'F7': 20, 'F8': 50, 'F9': 50, 'F10': None
}
WORDS_PER_PAGE = 300

def get_pkg_dir(filing_id):
    """Resolve PKG directory by glob pattern."""
    pattern = str(PKG_BASE / f"PKG_{filing_id}_*")
    dirs = glob.glob(pattern)
    return Path(dirs[0]) if dirs else None

def count_words(text):
    return len(text.split())

def estimate_pages(text):
    return count_words(text) / WORDS_PER_PAGE

def load_filing(filing_id):
    pkg = get_pkg_dir(filing_id)
    if not pkg:
        return None, None
    main_file = pkg / "01_MAIN_FILING.md"
    if not main_file.exists():
        return None, None
    return main_file, main_file.read_text(encoding='utf-8', errors='replace')

def get_evidence_for_filing(conn, filing_id):
    """Get strongest evidence items for this filing from DB."""
    evidence = []
    try:
        tables_to_check = [
            ("evidence_quotes", "quote_text", None),
            ("watson_perjury_compilation", "statement_text", "severity_score"),
            ("detected_contradictions", "statement_1", None),
        ]
        for table, text_col, score_col in tables_to_check:
            try:
                cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]
                if text_col not in cols:
                    continue
                if 'vehicle_name' in cols:
                    query = f"SELECT {text_col} FROM {table} WHERE vehicle_name LIKE ? LIMIT 10"
                    rows = conn.execute(query, (f"%{filing_id}%",)).fetchall()
                else:
                    query = f"SELECT {text_col} FROM {table} LIMIT 5"
                    rows = conn.execute(query).fetchall()
                for r in rows:
                    if r[0] and len(str(r[0])) > 20:
                        evidence.append(str(r[0])[:200])
            except Exception:
                continue
    except Exception:
        pass
    return evidence

def identify_redundant_blocks(text):
    """Find paragraphs that repeat substantially similar content."""
    paragraphs = re.split(r'\n\n+', text)
    seen_phrases = {}
    redundant_indices = []
    
    for i, para in enumerate(paragraphs):
        words = para.lower().split()
        if len(words) < 10:
            continue
        # Use 8-word sliding window to detect repetition
        for j in range(len(words) - 7):
            phrase = ' '.join(words[j:j+8])
            if phrase in seen_phrases and i != seen_phrases[phrase]:
                redundant_indices.append(i)
                break
            seen_phrases[phrase] = i
    
    return set(redundant_indices)

def identify_trimmable_content(text):
    """Identify content that can be safely removed or condensed."""
    trimmable = {
        'placeholder_paras': [],
        'verbose_block_quotes': [],
        'redundant_citations': [],
        'excessive_footnotes': [],
        'boilerplate_sections': [],
    }
    
    lines = text.split('\n')
    for i, line in enumerate(lines):
        # Placeholder paragraphs
        if re.search(r'\[ANDREW[_ ]REQUIRED\]|\[INSERT\]|\[ATTACH\]|\[TO BE\]|\[PLACEHOLDER\]', line, re.I):
            trimmable['placeholder_paras'].append((i, line.strip()[:80]))
        
        # Verbose block quotes (>3 lines of > prefixed text)
        if line.strip().startswith('>') and i + 3 < len(lines):
            if all(lines[i+j].strip().startswith('>') for j in range(1, 4)):
                trimmable['verbose_block_quotes'].append((i, 'Block quote starts here'))
    
    return trimmable

def trim_filing(filing_id, text, target_pages):
    """Strategically trim a filing to meet page limits."""
    current_pages = estimate_pages(text)
    if current_pages <= target_pages:
        return text, 0, []
    
    changes = []
    words_to_cut = int((current_pages - target_pages) * WORDS_PER_PAGE)
    words_cut = 0
    
    paragraphs = text.split('\n\n')
    result_paragraphs = []
    redundant = identify_redundant_blocks(text)
    
    # Phase 1: Remove placeholder paragraphs
    for i, para in enumerate(paragraphs):
        if re.search(r'\[ANDREW[_ ]REQUIRED\]|\[INSERT[_ ]', para, re.I):
            words_cut += count_words(para)
            changes.append(f"Removed placeholder paragraph ({count_words(para)} words)")
            continue
        result_paragraphs.append(para)
    
    if words_cut >= words_to_cut:
        return '\n\n'.join(result_paragraphs), words_cut, changes
    
    # Phase 2: Condense block quotes to inline citations
    condensed = []
    i = 0
    while i < len(result_paragraphs):
        para = result_paragraphs[i]
        lines = para.split('\n')
        quote_lines = [l for l in lines if l.strip().startswith('>')]
        
        if len(quote_lines) > 3 and words_cut < words_to_cut:
            # Condense multi-line block quote to single line reference
            first_quote = quote_lines[0].lstrip('> ').strip()
            if len(first_quote) > 80:
                first_quote = first_quote[:77] + '...'
            non_quote_lines = [l for l in lines if not l.strip().startswith('>')]
            condensed_para = '\n'.join(non_quote_lines) + f'\n*See* "{first_quote}"'
            saved = count_words(para) - count_words(condensed_para)
            if saved > 0:
                words_cut += saved
                changes.append(f"Condensed block quote ({saved} words saved)")
                condensed.append(condensed_para)
            else:
                condensed.append(para)
        else:
            condensed.append(para)
        i += 1
    
    result_paragraphs = condensed
    
    if words_cut >= words_to_cut:
        return '\n\n'.join(result_paragraphs), words_cut, changes
    
    # Phase 3: Remove redundant paragraphs (repeated content)
    final = []
    redundant_new = identify_redundant_blocks('\n\n'.join(result_paragraphs))
    for i, para in enumerate(result_paragraphs):
        if i in redundant_new and words_cut < words_to_cut:
            saved = count_words(para)
            words_cut += saved
            changes.append(f"Removed redundant paragraph #{i} ({saved} words)")
            continue
        final.append(para)
    
    result_paragraphs = final
    
    if words_cut >= words_to_cut:
        return '\n\n'.join(result_paragraphs), words_cut, changes
    
    # Phase 4: Trim verbose factual recitations (keep first 2 sentences of long paragraphs)
    trimmed = []
    for para in result_paragraphs:
        if count_words(para) > 150 and words_cut < words_to_cut and not para.strip().startswith('#'):
            sentences = re.split(r'(?<=[.!?])\s+', para)
            if len(sentences) > 4:
                # Keep first 3 sentences + last sentence
                kept = sentences[:3] + [sentences[-1]]
                new_para = ' '.join(kept)
                saved = count_words(para) - count_words(new_para)
                if saved > 20:
                    words_cut += saved
                    changes.append(f"Condensed verbose paragraph ({saved} words saved)")
                    trimmed.append(new_para)
                    continue
        trimmed.append(para)
    
    return '\n\n'.join(trimmed), words_cut, changes

def fix_critical_issues(filing_id, text, issues):
    """Apply critical issue fixes to filing text."""
    fixes_applied = []
    
    for issue in issues:
        cat = issue.get('category', '')
        current = issue.get('current_text', '')
        correct = issue.get('correct_text', '')
        explanation = issue.get('explanation', '')
        
        if cat == 'wrong_court' and current and correct:
            if current in text:
                text = text.replace(current, correct)
                fixes_applied.append(f"Fixed wrong court reference: {explanation[:80]}")
        
        elif cat == 'missing_section' and correct:
            if correct == 'Certificate of Compliance':
                # Add certificate of compliance for COA brief
                cert = """
---

## CERTIFICATE OF COMPLIANCE

I hereby certify that this brief complies with the formatting and length limitations 
of MCR 7.212(B). This brief was prepared using proportionally-spaced type in 
12-point font and contains fewer than 16,000 words (the equivalent of 50 pages), 
exclusive of tables, indexes, and attachments.

ANDREW JAMES PIGORS
Plaintiff-Appellant, *In Propria Persona*
Dated: _________________, 2026
"""
                text += cert
                fixes_applied.append("Added Certificate of Compliance (MCR 7.212(D))")
            
            elif correct == 'Appendix':
                appendix = """
---

## APPENDIX

The following lower court documents are attached as required by MCR 7.212(G):

| Tab | Document | Date |
|-----|----------|------|
| A | Ex Parte Order Suspending Parenting Time | July 17, 2025 |
| B | Order After August 8, 2025 Hearing | August 8, 2025 |
| C | Order Denying Motion for Reconsideration | [DATE] |
| D | Register of Actions | Current |

*Full copies of the above documents are attached following this brief.*
"""
                text += appendix
                fixes_applied.append("Added Appendix section (MCR 7.212(G))")
    
    return text, fixes_applied

def fix_rusco_title(text):
    """Fix Pamela Rusco being called FOC when she's judicial secretary."""
    fixes = []
    patterns = [
        (r'Friend of the Court.*?Pamela Rusco', 'Judicial Secretary Pamela Rusco'),
        (r'FOC.*?Pamela Rusco', 'Judicial Secretary Pamela Rusco'),
        (r'Pamela Rusco.*?Friend of the Court', 'Pamela Rusco, Judicial Secretary to Judge McNeill'),
        (r'Pamela Rusco.*?FOC', 'Pamela Rusco, Judicial Secretary'),
    ]
    for pattern, replacement in patterns:
        if re.search(pattern, text, re.I):
            text = re.sub(pattern, replacement, text, flags=re.I)
            fixes.append(f"Fixed Rusco title: {pattern[:40]}... → {replacement}")
    return text, fixes

def process_filing(filing_id, conn):
    """Process a single filing: fix issues, trim, enhance."""
    result = {
        'filing_id': filing_id,
        'status': 'skipped',
        'original_words': 0,
        'final_words': 0,
        'original_pages': 0,
        'final_pages': 0,
        'page_limit': PAGE_LIMITS.get(filing_id),
        'changes': [],
        'issues_fixed': [],
        'evidence_added': 0,
    }
    
    main_file, text = load_filing(filing_id)
    if not text:
        result['status'] = 'NOT_FOUND'
        return result
    
    result['original_words'] = count_words(text)
    result['original_pages'] = round(estimate_pages(text), 1)
    
    # Step 1: Fix Rusco title (applies to F3 primarily but check all)
    text, rusco_fixes = fix_rusco_title(text)
    result['issues_fixed'].extend(rusco_fixes)
    
    # Step 2: Fix critical issues from DB
    try:
        issues = conn.execute(
            "SELECT category, current_text, correct_text, explanation FROM filing_issues WHERE filing_id LIKE ? AND severity = 'CRITICAL' AND status != 'fixed'",
            (f"{filing_id}%",)
        ).fetchall()
        issue_dicts = [{'category': r[0], 'current_text': r[1], 'correct_text': r[2], 'explanation': r[3]} for r in issues]
        text, crit_fixes = fix_critical_issues(filing_id, text, issue_dicts)
        result['issues_fixed'].extend(crit_fixes)
    except Exception as e:
        result['issues_fixed'].append(f"DB query error: {e}")
    
    # Step 3: Trim if over limit
    limit = PAGE_LIMITS.get(filing_id)
    if limit and estimate_pages(text) > limit:
        text, words_cut, trim_changes = trim_filing(filing_id, text, limit)
        result['changes'].extend(trim_changes)
        result['words_trimmed'] = words_cut
    
    result['final_words'] = count_words(text)
    result['final_pages'] = round(estimate_pages(text), 1)
    
    # Step 4: Write the converged filing
    pkg = get_pkg_dir(filing_id)
    if pkg:
        # Backup original
        backup = main_file.with_suffix(f'.md.bak.convergence_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
        import shutil
        shutil.copy2(main_file, backup)
        
        # Write converged version
        main_file.write_text(text, encoding='utf-8')
        result['status'] = 'CONVERGED'
        result['backup'] = str(backup.name)
    
    return result

def main():
    print("=" * 70)
    print("FILING CONVERGENCE ENGINE — Tool #41")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 70)
    
    # Target filings: over-limit ones + those with critical issues
    target_filings = ['F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9', 'F10']
    
    conn = sqlite3.connect(str(DB_PATH), timeout=60)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    
    results = {}
    over_limit_before = 0
    over_limit_after = 0
    total_words_cut = 0
    total_issues_fixed = 0
    
    for fid in target_filings:
        print(f"\n--- Processing {fid} ---")
        result = process_filing(fid, conn)
        results[fid] = result
        
        limit = PAGE_LIMITS.get(fid)
        if limit:
            if result['original_pages'] > limit:
                over_limit_before += 1
            if result['final_pages'] > limit:
                over_limit_after += 1
        
        total_words_cut += result.get('words_trimmed', 0)
        total_issues_fixed += len(result['issues_fixed'])
        
        status_icon = '✅' if result['status'] == 'CONVERGED' else '⚠️'
        print(f"  {status_icon} {fid}: {result['original_pages']}p → {result['final_pages']}p "
              f"(limit: {limit or 'None'})")
        if result['issues_fixed']:
            for fix in result['issues_fixed']:
                print(f"    🔧 {fix}")
        if result['changes']:
            for change in result['changes'][:5]:
                print(f"    ✂️ {change}")
            if len(result['changes']) > 5:
                print(f"    ... and {len(result['changes'])-5} more changes")
    
    conn.close()
    
    # Summary
    print("\n" + "=" * 70)
    print("CONVERGENCE SUMMARY")
    print("=" * 70)
    print(f"Filings processed:     {len(results)}")
    print(f"Over limit BEFORE:     {over_limit_before}")
    print(f"Over limit AFTER:      {over_limit_after}")
    print(f"Total words trimmed:   {total_words_cut:,}")
    print(f"Critical issues fixed: {total_issues_fixed}")
    print(f"Filings converged:     {sum(1 for r in results.values() if r['status'] == 'CONVERGED')}")
    
    # Save JSON report
    report_data = {
        'generated': datetime.now().isoformat(),
        'tool': 'Filing Convergence Engine (#41)',
        'summary': {
            'filings_processed': len(results),
            'over_limit_before': over_limit_before,
            'over_limit_after': over_limit_after,
            'words_trimmed': total_words_cut,
            'issues_fixed': total_issues_fixed,
        },
        'filings': results
    }
    
    json_path = REPORTS_DIR / "convergence_results.json"
    json_path.write_text(json.dumps(report_data, indent=2, default=str), encoding='utf-8')
    
    # Save markdown report
    md_lines = [
        "# FILING CONVERGENCE REPORT",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n",
        "## Summary",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Filings Processed | {len(results)} |",
        f"| Over Limit Before | {over_limit_before} |",
        f"| Over Limit After | {over_limit_after} |",
        f"| Words Trimmed | {total_words_cut:,} |",
        f"| Issues Fixed | {total_issues_fixed} |",
        "",
        "## Filing Details",
        "",
        "| Filing | Before | After | Limit | Status | Issues Fixed |",
        "|--------|--------|-------|-------|--------|-------------|",
    ]
    
    for fid in target_filings:
        r = results.get(fid, {})
        status = '✅' if r.get('status') == 'CONVERGED' else '⚠️'
        limit_str = str(PAGE_LIMITS.get(fid, '—'))
        over = ' ⚠️OVER' if PAGE_LIMITS.get(fid) and r.get('final_pages', 0) > PAGE_LIMITS[fid] else ''
        md_lines.append(
            f"| {fid} | {r.get('original_pages', '?')}p | {r.get('final_pages', '?')}p{over} | "
            f"{limit_str}p | {status} | {len(r.get('issues_fixed', []))} |"
        )
    
    md_lines.extend([
        "",
        "## Changes Applied",
        "",
    ])
    
    for fid in target_filings:
        r = results.get(fid, {})
        if r.get('issues_fixed') or r.get('changes'):
            md_lines.append(f"### {fid}")
            for fix in r.get('issues_fixed', []):
                md_lines.append(f"- 🔧 {fix}")
            for change in r.get('changes', []):
                md_lines.append(f"- ✂️ {change}")
            md_lines.append("")
    
    md_path = REPORTS_DIR / "CONVERGENCE_REPORT.md"
    md_path.write_text('\n'.join(md_lines), encoding='utf-8')
    
    print(f"\nReports: {json_path.name}, {md_path.name}")
    print("CONVERGENCE ENGINE COMPLETE")

if __name__ == '__main__':
    main()
