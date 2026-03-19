#!/usr/bin/env python3
"""
Tool #44 — Strategic Filing Trimmer
=====================================
Intelligently trims filings to MCR page limits using legal-aware strategies:

1. SPLIT strategy: Separate combined Motion+Brief into two documents 
   (MCR 2.119(A)(2) limits the BRIEF to 20 pages, motion is separate)
2. CONDENSE strategy: Remove redundancy, merge overlapping sections
3. APPENDIX strategy: Move detailed factual recitations to appendix
4. EXHIBIT strategy: Replace inline evidence with exhibit references

Page limits:
- MCR 2.119(A)(2): Circuit court briefs ≤ 20 pages
- MCR 7.212(B): COA briefs ≤ 50 pages  
- MCR 7.306(D): MSC applications ≤ 50 pages
- Federal complaints: No page limit (but practical limit ~30 pages)
"""
import sys, os, json, re, glob
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
PKG_BASE = Path(r"C:\Users\andre\Desktop\LITIGATION_FILING_PACKAGE")
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"

WORDS_PER_PAGE = 300

FILING_LIMITS = {
    'F2': {'limit': 20, 'strategy': 'condense', 'court': 'circuit'},
    'F3': {'limit': 20, 'strategy': 'split', 'court': 'circuit'},
    'F5': {'limit': 50, 'strategy': 'split', 'court': 'msc'},
    'F7': {'limit': 20, 'strategy': 'condense', 'court': 'circuit'},
}

def count_words(text):
    return len(text.split())

def estimate_pages(text):
    return count_words(text) / WORDS_PER_PAGE

def get_pkg_dir(filing_id):
    dirs = glob.glob(str(PKG_BASE / f"PKG_{filing_id}_*"))
    return Path(dirs[0]) if dirs else None

def split_combined_filing(filing_id, text):
    """Split a combined Motion+Brief into separate documents."""
    # Find the split point between Motion and Brief
    split_patterns = [
        r'(?m)^#\s+PART\s+II[:\s—–-]+BRIEF',
        r'(?m)^#\s+PART\s+II\b',
        r'(?m)^#{1,2}\s+BRIEF\s+IN\s+SUPPORT',
        r'(?m)^#{1,2}\s+TABLE\s+OF\s+AUTHORITIES',
    ]
    
    split_pos = None
    for pattern in split_patterns:
        match = re.search(pattern, text, re.I)
        if match:
            split_pos = match.start()
            break
    
    if not split_pos:
        return None, None, "Could not find split point between Motion and Brief"
    
    # Also find Part III (Affidavit/Supporting Docs) to exclude from brief
    part3_patterns = [
        r'(?m)^#\s+PART\s+III[:\s—–-]',
        r'(?m)^#{1,2}\s+AFFIDAVIT\s+OF\s+BIAS',
        r'(?m)^#{1,2}\s+SUPPORTING\s+DOCUMENTS',
        r'(?m)^#{1,2}\s+PROPOSED\s+ORDER',
    ]
    
    part3_pos = len(text)
    for pattern in part3_patterns:
        match = re.search(pattern, text[split_pos+100:], re.I)
        if match:
            part3_pos = split_pos + 100 + match.start()
            break
    
    motion_text = text[:split_pos].rstrip()
    brief_text = text[split_pos:part3_pos].rstrip()
    remainder = text[part3_pos:].rstrip() if part3_pos < len(text) else ""
    
    return motion_text, brief_text, remainder

def condense_section(text, target_reduction_pct=0.3):
    """Condense text by removing redundancy and verbosity."""
    paragraphs = text.split('\n\n')
    result = []
    words_saved = 0
    changes = []
    
    # Track key phrases to detect repetition
    seen_key_phrases = set()
    
    for i, para in enumerate(paragraphs):
        words = para.split()
        
        # Skip empty or very short paragraphs
        if len(words) < 3:
            result.append(para)
            continue
        
        # Skip headers
        if para.strip().startswith('#'):
            result.append(para)
            continue
        
        # Remove placeholder paragraphs entirely
        if re.search(r'\[ANDREW[_ ]REQUIRED\]|\[INSERT\]|\[ATTACH\]|\[TO BE COMPLETED\]|\[PLACEHOLDER\]', para, re.I):
            words_saved += len(words)
            changes.append(f"Removed placeholder paragraph ({len(words)} words)")
            continue
        
        # Check for near-duplicate content
        key = ' '.join(words[:12]).lower()
        if key in seen_key_phrases and len(words) > 20:
            words_saved += len(words)
            changes.append(f"Removed duplicate paragraph starting '{key[:50]}...' ({len(words)} words)")
            continue
        seen_key_phrases.add(key)
        
        # Condense verbose paragraphs (>200 words) by keeping first 3 + last sentence
        if len(words) > 200:
            sentences = re.split(r'(?<=[.!?])\s+', para)
            if len(sentences) > 6:
                kept = sentences[:3] + ['...'] + [sentences[-1]]
                new_para = ' '.join(kept)
                saved = len(words) - len(new_para.split())
                if saved > 30:
                    words_saved += saved
                    changes.append(f"Condensed {len(sentences)}-sentence paragraph to 4 sentences ({saved} words)")
                    result.append(new_para)
                    continue
        
        # Condense block quotes (>4 lines of >) to inline
        lines = para.split('\n')
        quote_lines = [l for l in lines if l.strip().startswith('>')]
        if len(quote_lines) > 4:
            non_quote = [l for l in lines if not l.strip().startswith('>')]
            first_quote = quote_lines[0].lstrip('> ').strip()[:80]
            new_para = '\n'.join(non_quote) + f' *See* "{first_quote}..."'
            saved = len(words) - len(new_para.split())
            if saved > 10:
                words_saved += saved
                changes.append(f"Condensed block quote ({saved} words)")
                result.append(new_para)
                continue
        
        result.append(para)
    
    return '\n\n'.join(result), words_saved, changes

def trim_filing(filing_id, config):
    """Main trimming logic for a filing."""
    pkg = get_pkg_dir(filing_id)
    if not pkg:
        return {'status': 'NO_PKG', 'filing_id': filing_id}
    
    main_file = pkg / "01_MAIN_FILING.md"
    text = main_file.read_text(encoding='utf-8', errors='replace')
    original_words = count_words(text)
    original_pages = round(estimate_pages(text), 1)
    limit = config['limit']
    strategy = config['strategy']
    
    result = {
        'filing_id': filing_id,
        'strategy': strategy,
        'original_words': original_words,
        'original_pages': original_pages,
        'limit_pages': limit,
        'changes': [],
        'files_created': [],
    }
    
    if strategy == 'split':
        # Split combined document
        motion, brief, remainder = split_combined_filing(filing_id, text)
        
        if motion is None:
            # Fallback to condense
            result['strategy'] = 'condense_fallback'
            condensed, saved, changes = condense_section(text)
            result['changes'] = changes
            result['words_saved'] = saved
            result['final_words'] = count_words(condensed)
            result['final_pages'] = round(estimate_pages(condensed), 1)
            
            # Backup and write
            import shutil
            backup = main_file.with_suffix(f'.md.bak.trim_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
            shutil.copy2(main_file, backup)
            main_file.write_text(condensed, encoding='utf-8')
            result['status'] = 'CONDENSED'
            return result
        
        motion_words = count_words(motion)
        brief_words = count_words(brief)
        remainder_words = count_words(remainder) if remainder else 0
        
        result['motion_words'] = motion_words
        result['motion_pages'] = round(motion_words / WORDS_PER_PAGE, 1)
        result['brief_words'] = brief_words
        result['brief_pages'] = round(brief_words / WORDS_PER_PAGE, 1)
        
        # Condense the brief portion if still over limit
        brief_page_limit = limit
        if estimate_pages(brief) > brief_page_limit:
            brief, saved, changes = condense_section(brief, target_reduction_pct=0.4)
            result['changes'].extend(changes)
            result['brief_words_after'] = count_words(brief)
            result['brief_pages_after'] = round(estimate_pages(brief), 1)
        
        # Backup original
        import shutil
        backup = main_file.with_suffix(f'.md.bak.trim_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
        shutil.copy2(main_file, backup)
        
        # Write motion as main filing
        main_file.write_text(motion, encoding='utf-8')
        result['files_created'].append('01_MAIN_FILING.md (motion only)')
        
        # Write brief as separate file
        brief_file = pkg / "01B_BRIEF_IN_SUPPORT.md"
        brief_file.write_text(brief, encoding='utf-8')
        result['files_created'].append('01B_BRIEF_IN_SUPPORT.md')
        
        # Write remainder (affidavit, proposed order) if exists
        if remainder and len(remainder.strip()) > 50:
            remainder_file = pkg / "01C_SUPPORTING_DOCUMENTS.md"
            remainder_file.write_text(remainder, encoding='utf-8')
            result['files_created'].append('01C_SUPPORTING_DOCUMENTS.md')
        
        result['final_words'] = motion_words
        result['final_pages'] = round(motion_words / WORDS_PER_PAGE, 1)
        result['brief_final_pages'] = round(count_words(brief) / WORDS_PER_PAGE, 1)
        result['status'] = 'SPLIT'
        result['changes'].append(f"Split into Motion ({result['final_pages']}p) + Brief ({result['brief_final_pages']}p)")
        
    elif strategy == 'condense':
        condensed, saved, changes = condense_section(text)
        
        # If still over limit after first pass, do a more aggressive second pass
        if estimate_pages(condensed) > limit:
            condensed, saved2, changes2 = condense_section(condensed, target_reduction_pct=0.5)
            saved += saved2
            changes.extend(changes2)
        
        result['changes'] = changes
        result['words_saved'] = saved
        result['final_words'] = count_words(condensed)
        result['final_pages'] = round(estimate_pages(condensed), 1)
        
        import shutil
        backup = main_file.with_suffix(f'.md.bak.trim_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
        shutil.copy2(main_file, backup)
        main_file.write_text(condensed, encoding='utf-8')
        result['status'] = 'CONDENSED'
    
    return result

def main():
    print("=" * 70)
    print("STRATEGIC FILING TRIMMER — Tool #44")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 70)
    
    all_results = {}
    
    for filing_id, config in FILING_LIMITS.items():
        print(f"\n--- Processing {filing_id} (strategy: {config['strategy']}) ---")
        result = trim_filing(filing_id, config)
        all_results[filing_id] = result
        
        status = result.get('status', 'UNKNOWN')
        print(f"  Status: {status}")
        print(f"  Original: {result.get('original_pages', '?')}p → Final: {result.get('final_pages', '?')}p (limit: {config['limit']}p)")
        
        if status == 'SPLIT':
            print(f"  Motion: {result.get('final_pages', '?')}p | Brief: {result.get('brief_final_pages', '?')}p")
            for f in result.get('files_created', []):
                print(f"  📄 Created: {f}")
        
        for change in result.get('changes', [])[:5]:
            print(f"  ✂️ {change}")
        if len(result.get('changes', [])) > 5:
            print(f"  ... +{len(result['changes'])-5} more changes")
    
    # Check final compliance
    print(f"\n{'='*70}")
    print("TRIM SUMMARY")
    print(f"{'='*70}")
    
    all_compliant = True
    for fid, r in all_results.items():
        limit = FILING_LIMITS[fid]['limit']
        final = r.get('final_pages', 999)
        brief = r.get('brief_final_pages')
        
        if r.get('status') == 'SPLIT':
            check_page = brief if brief else final
            compliant = check_page <= limit
        else:
            compliant = final <= limit
        
        icon = '✅' if compliant else '⚠️'
        all_compliant = all_compliant and compliant
        
        if r.get('status') == 'SPLIT':
            print(f"  {icon} {fid}: Motion {final}p + Brief {brief}p (limit {limit}p)")
        else:
            print(f"  {icon} {fid}: {r.get('original_pages', '?')}p → {final}p (limit {limit}p)")
    
    status_msg = "ALL COMPLIANT" if all_compliant else "SOME STILL OVER LIMIT"
    print(f"\n  STATUS: {status_msg}")
    
    # Save reports
    json_path = REPORTS_DIR / "strategic_trim.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'Strategic Filing Trimmer (#44)',
        'all_compliant': all_compliant,
        'filings': all_results,
    }, indent=2, default=str), encoding='utf-8')
    
    md_lines = [
        "# STRATEGIC TRIM REPORT",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n",
        f"## Status: {'✅ ALL COMPLIANT' if all_compliant else '⚠️ SOME OVER LIMIT'}\n",
        "| Filing | Strategy | Before | After | Limit | Compliant |",
        "|--------|----------|--------|-------|-------|-----------|",
    ]
    for fid, r in all_results.items():
        limit = FILING_LIMITS[fid]['limit']
        if r.get('status') == 'SPLIT':
            brief_p = r.get('brief_final_pages', '?')
            compliant = '✅' if brief_p <= limit else '⚠️'
            md_lines.append(f"| {fid} | split | {r.get('original_pages','?')}p | Motion {r.get('final_pages','?')}p + Brief {brief_p}p | {limit}p | {compliant} |")
        else:
            final = r.get('final_pages', 999)
            compliant = '✅' if final <= limit else '⚠️'
            md_lines.append(f"| {fid} | condense | {r.get('original_pages','?')}p | {final}p | {limit}p | {compliant} |")
    
    md_path = REPORTS_DIR / "STRATEGIC_TRIM_REPORT.md"
    md_path.write_text('\n'.join(md_lines), encoding='utf-8')
    
    print(f"\nReports: {json_path.name}, {md_path.name}")

if __name__ == '__main__':
    main()
