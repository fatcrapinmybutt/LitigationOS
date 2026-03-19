#!/usr/bin/env python3
"""
Filing Word Trimmer — Auto-condenses over-limit filings to meet MCR page limits.

Novel LitigationOS Tool #20

Strategy:
1. Identify redundant paragraphs (semantic similarity via TF-IDF)
2. Find verbose legal phrases and suggest concise alternatives
3. Detect duplicated arguments across sections
4. Calculate exact trim targets per filing
5. Generate trimmed versions with tracked changes

MCR Page Limits:
- MCR 2.119(A)(2): Circuit court briefs/motions ≤ 20 pages
- MCR 7.212(B): COA briefs ≤ 50 pages (exclusive of tables/appendices)
- MCR 7.306(D): MSC applications ≤ 50 pages
- MCR 7.211(C)(2): COA motions ≤ 20 pages
"""
import sys, os, json, re, math
from collections import defaultdict, Counter
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

# Constants
WORDS_PER_PAGE = 300  # Conservative estimate (double-spaced, 12pt Times New Roman)
PAGE_LIMITS = {
    'F1': 20, 'F2': 20, 'F3': 20, 'F4': 20,
    'F5': 50,  # COA brief
    'F6': 20, 'F7': 20, 'F8': 20,
    'F9': 50,  # COA brief
    'F10': 20,
}

# Verbose phrase replacements for legal writing
VERBOSE_TO_CONCISE = {
    r'\bat this point in time\b': 'now',
    r'\bin the event that\b': 'if',
    r'\bfor the reason that\b': 'because',
    r'\bwith regard to\b': 'regarding',
    r'\bwith respect to\b': 'regarding',
    r'\bin order to\b': 'to',
    r'\bprior to\b': 'before',
    r'\bsubsequent to\b': 'after',
    r'\bnotwithstanding the fact that\b': 'although',
    r'\bfor the purpose of\b': 'to',
    r'\bin the matter of\b': 'in',
    r'\bit is clear that\b': '',
    r'\bit is evident that\b': '',
    r'\bit is important to note that\b': '',
    r'\bit should be noted that\b': '',
    r'\bit is well established that\b': '',
    r'\bthe fact that\b': 'that',
    r'\bin light of the fact that\b': 'because',
    r'\bdespite the fact that\b': 'although',
    r'\bon the basis of\b': 'based on',
    r'\bin accordance with\b': 'under',
    r'\bpursuant to\b': 'under',
    r'\bat the present time\b': 'now',
    r'\bdue to the fact that\b': 'because',
    r'\bas a result of\b': 'from',
    r'\bin the absence of\b': 'without',
    r'\bis able to\b': 'can',
    r'\bis unable to\b': 'cannot',
    r'\bhas the ability to\b': 'can',
    r'\buntil such time as\b': 'until',
    r'\ba large number of\b': 'many',
    r'\ba sufficient number of\b': 'enough',
    r'\bthe above-mentioned\b': 'this',
    r'\bthe aforementioned\b': 'this',
    r'\bin close proximity to\b': 'near',
    r'\bin the neighborhood of\b': 'about',
    r'\bby means of\b': 'by',
    r'\bby virtue of\b': 'by',
    r'\bfor all intents and purposes\b': 'effectively',
    r'\beach and every\b': 'every',
    r'\bany and all\b': 'all',
    r'\bnull and void\b': 'void',
    r'\bcease and desist\b': 'stop',
    r'\bfull and complete\b': 'complete',
    r'\btrue and correct\b': 'true',
}

FILING_DIR = Path(r"C:\Users\andre\Desktop\LITIGATION_FILING_PACKAGE")
REPORT_DIR = Path(r"C:\Users\andre\LitigationOS\00_SYSTEM\reports")


def find_filing_file(filing_id):
    """Find the main filing markdown file using glob pattern."""
    pattern = f"PKG_{filing_id}_*"
    matches = list(FILING_DIR.glob(pattern))
    if matches:
        main_file = matches[0] / "01_MAIN_FILING.md"
        if main_file.exists():
            return main_file
    return None


def count_words(text):
    """Count words excluding markdown formatting."""
    clean = re.sub(r'^#+\s+.*$', '', text, flags=re.MULTILINE)  # headers
    clean = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', clean)  # links
    clean = re.sub(r'[*_~`]', '', clean)  # formatting
    clean = re.sub(r'---+', '', clean)  # horizontal rules
    words = clean.split()
    return len(words)


def estimate_pages(word_count):
    """Estimate page count from word count."""
    return math.ceil(word_count / WORDS_PER_PAGE)


def find_verbose_phrases(text):
    """Find verbose phrases that can be made concise."""
    findings = []
    for pattern, replacement in VERBOSE_TO_CONCISE.items():
        matches = list(re.finditer(pattern, text, re.IGNORECASE))
        for m in matches:
            original = m.group()
            word_savings = len(original.split()) - len(replacement.split())
            findings.append({
                'original': original,
                'replacement': replacement or '[DELETE]',
                'word_savings': max(word_savings, 1),
                'position': m.start(),
            })
    return findings


def find_redundant_paragraphs(text, threshold=0.6):
    """Find paragraphs that are semantically similar (potential duplicates)."""
    paragraphs = [p.strip() for p in text.split('\n\n') if len(p.strip()) > 50]
    redundant = []
    
    for i, p1 in enumerate(paragraphs):
        words1 = set(p1.lower().split())
        for j, p2 in enumerate(paragraphs):
            if j <= i:
                continue
            words2 = set(p2.lower().split())
            if not words1 or not words2:
                continue
            # Jaccard similarity
            intersection = len(words1 & words2)
            union = len(words1 | words2)
            similarity = intersection / union if union > 0 else 0
            
            if similarity >= threshold:
                redundant.append({
                    'para_a_idx': i,
                    'para_b_idx': j,
                    'similarity': round(similarity, 3),
                    'para_a_preview': p1[:100] + '...',
                    'para_b_preview': p2[:100] + '...',
                    'word_savings': min(count_words(p1), count_words(p2)),
                })
    
    return redundant


def find_citation_clusters(text):
    """Find excessive citation strings (string cites) that can be trimmed."""
    # Pattern: multiple citations in parentheses separated by semicolons
    pattern = r'\(([^)]*(?:;\s*[^)]*){3,})\)'
    clusters = []
    for m in re.finditer(pattern, text):
        full_cite = m.group(1)
        cite_count = len(full_cite.split(';'))
        if cite_count > 3:
            # Each excess citation beyond 3 saves ~10 words
            excess = cite_count - 3
            clusters.append({
                'preview': full_cite[:150] + '...',
                'citation_count': cite_count,
                'excess': excess,
                'word_savings': excess * 10,
                'position': m.start(),
                'recommendation': f'Keep 3 strongest citations, move rest to footnotes'
            })
    return clusters


def find_repeated_arguments(text):
    """Find arguments that are stated multiple times across sections."""
    sections = re.split(r'^#{1,3}\s+', text, flags=re.MULTILINE)
    repeated = []
    
    # Extract key phrases (3+ word sequences) from each section
    section_phrases = []
    for sec in sections:
        words = sec.lower().split()
        phrases = set()
        for k in range(len(words) - 2):
            phrase = ' '.join(words[k:k+3])
            if len(phrase) > 15:  # skip short generic phrases
                phrases.add(phrase)
        section_phrases.append(phrases)
    
    # Find phrases that appear in multiple sections
    phrase_sections = defaultdict(list)
    for idx, phrases in enumerate(section_phrases):
        for phrase in phrases:
            phrase_sections[phrase].append(idx)
    
    for phrase, sections_list in phrase_sections.items():
        if len(sections_list) >= 3:  # appears in 3+ sections
            repeated.append({
                'phrase': phrase,
                'appears_in_sections': len(sections_list),
                'recommendation': 'Consolidate into single occurrence with cross-references',
            })
    
    # Deduplicate by taking most specific phrases
    seen = set()
    unique = []
    for r in sorted(repeated, key=lambda x: -x['appears_in_sections']):
        if r['phrase'] not in seen:
            unique.append(r)
            seen.add(r['phrase'])
    
    return unique[:20]  # Top 20 repeated arguments


def generate_trim_plan(filing_id, text, page_limit):
    """Generate a comprehensive trim plan for a filing."""
    word_count = count_words(text)
    current_pages = estimate_pages(word_count)
    target_words = page_limit * WORDS_PER_PAGE
    words_to_cut = max(0, word_count - target_words)
    
    plan = {
        'filing_id': filing_id,
        'current_words': word_count,
        'current_pages': current_pages,
        'page_limit': page_limit,
        'target_words': target_words,
        'words_to_cut': words_to_cut,
        'over_limit': current_pages > page_limit,
        'verbose_phrases': [],
        'redundant_paragraphs': [],
        'citation_clusters': [],
        'repeated_arguments': [],
        'total_potential_savings': 0,
    }
    
    if not plan['over_limit']:
        plan['status'] = 'WITHIN_LIMIT'
        return plan
    
    # Strategy 1: Verbose phrases
    verbose = find_verbose_phrases(text)
    plan['verbose_phrases'] = verbose
    verbose_savings = sum(v['word_savings'] for v in verbose)
    
    # Strategy 2: Redundant paragraphs
    redundant = find_redundant_paragraphs(text)
    plan['redundant_paragraphs'] = redundant
    redundant_savings = sum(r['word_savings'] for r in redundant)
    
    # Strategy 3: Citation clusters
    clusters = find_citation_clusters(text)
    plan['citation_clusters'] = clusters
    cluster_savings = sum(c['word_savings'] for c in clusters)
    
    # Strategy 4: Repeated arguments
    repeated = find_repeated_arguments(text)
    plan['repeated_arguments'] = repeated
    
    plan['total_potential_savings'] = verbose_savings + redundant_savings + cluster_savings
    plan['savings_breakdown'] = {
        'verbose_phrase_savings': verbose_savings,
        'redundant_paragraph_savings': redundant_savings,
        'citation_cluster_savings': cluster_savings,
    }
    
    # Assess feasibility
    if plan['total_potential_savings'] >= words_to_cut:
        plan['status'] = 'TRIMMABLE_AUTO'
        plan['confidence'] = 'HIGH'
    elif plan['total_potential_savings'] >= words_to_cut * 0.5:
        plan['status'] = 'TRIMMABLE_WITH_REWRITE'
        plan['confidence'] = 'MEDIUM'
    else:
        plan['status'] = 'NEEDS_MAJOR_REWRITE'
        plan['confidence'] = 'LOW'
        plan['recommendation'] = f"Need to cut {words_to_cut} words but auto-trim can only save ~{plan['total_potential_savings']}. Consider splitting into main brief + appendix."
    
    return plan


def apply_verbose_fixes(text, verbose_phrases):
    """Apply verbose phrase replacements to text."""
    result = text
    applied = 0
    for fix in verbose_phrases:
        pattern = re.escape(fix['original'])
        new_text, count = re.subn(pattern, fix['replacement'], result, count=1, flags=re.IGNORECASE)
        if count > 0:
            result = new_text
            applied += 1
    return result, applied


def main():
    print("=" * 70)
    print("FILING WORD TRIMMER — Auto-Condense Over-Limit Filings")
    print("=" * 70)
    print(f"Run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    all_plans = {}
    over_limit_count = 0
    total_words_to_cut = 0
    
    for filing_id in [f"F{i}" for i in range(1, 11)]:
        filepath = find_filing_file(filing_id)
        if not filepath:
            print(f"  ⚠ {filing_id}: Filing not found")
            continue
        
        text = filepath.read_text(encoding='utf-8', errors='replace')
        page_limit = PAGE_LIMITS.get(filing_id, 20)
        
        plan = generate_trim_plan(filing_id, text, page_limit)
        all_plans[filing_id] = plan
        
        status_icon = '✅' if not plan['over_limit'] else '🔴'
        print(f"  {status_icon} {filing_id}: {plan['current_words']:,} words / {plan['current_pages']}p"
              f" (limit: {page_limit}p)")
        
        if plan['over_limit']:
            over_limit_count += 1
            total_words_to_cut += plan['words_to_cut']
            print(f"     → Must cut {plan['words_to_cut']:,} words ({plan['words_to_cut'] // WORDS_PER_PAGE} pages)")
            print(f"     → Verbose phrases: {len(plan['verbose_phrases'])} found "
                  f"(~{plan['savings_breakdown']['verbose_phrase_savings']} word savings)")
            print(f"     → Redundant paragraphs: {len(plan['redundant_paragraphs'])} found "
                  f"(~{plan['savings_breakdown']['redundant_paragraph_savings']} word savings)")
            print(f"     → Citation clusters: {len(plan['citation_clusters'])} found "
                  f"(~{plan['savings_breakdown']['citation_cluster_savings']} word savings)")
            print(f"     → Repeated arguments: {len(plan['repeated_arguments'])}")
            print(f"     → Total auto-savings: ~{plan['total_potential_savings']:,} words")
            print(f"     → Status: {plan['status']} ({plan['confidence']} confidence)")
    
    print()
    print("=" * 70)
    print(f"SUMMARY: {over_limit_count} filings over limit, {total_words_to_cut:,} total words to cut")
    print("=" * 70)
    
    # Generate detailed trim report
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORT_DIR / "filing_trim_plan.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(all_plans, f, indent=2, default=str)
    print(f"\nDetailed trim plans saved to: {report_path}")
    
    # Generate markdown report
    md_path = REPORT_DIR / "FILING_TRIM_REPORT.md"
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write("# Filing Trim Report\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"## Summary\n\n")
        f.write(f"- **Over-limit filings:** {over_limit_count}\n")
        f.write(f"- **Total words to cut:** {total_words_to_cut:,}\n\n")
        
        f.write("## Page Status\n\n")
        f.write("| Filing | Words | Pages | Limit | Over By | Status |\n")
        f.write("|--------|-------|-------|-------|---------|--------|\n")
        for fid, plan in sorted(all_plans.items()):
            over = plan['current_pages'] - plan['page_limit'] if plan['over_limit'] else 0
            status = '🔴 OVER' if plan['over_limit'] else '✅ OK'
            f.write(f"| {fid} | {plan['current_words']:,} | {plan['current_pages']} | "
                    f"{plan['page_limit']} | {over} | {status} |\n")
        
        for fid, plan in sorted(all_plans.items()):
            if not plan['over_limit']:
                continue
            
            f.write(f"\n---\n\n## {fid} Trim Plan\n\n")
            f.write(f"**Current:** {plan['current_words']:,} words / {plan['current_pages']} pages\n\n")
            f.write(f"**Target:** {plan['target_words']:,} words / {plan['page_limit']} pages\n\n")
            f.write(f"**Must cut:** {plan['words_to_cut']:,} words\n\n")
            f.write(f"**Auto-trimmable:** ~{plan['total_potential_savings']:,} words\n\n")
            f.write(f"**Status:** {plan.get('status', 'UNKNOWN')} ({plan.get('confidence', 'N/A')})\n\n")
            
            if plan['verbose_phrases']:
                f.write(f"### Verbose Phrases ({len(plan['verbose_phrases'])} found)\n\n")
                f.write("| Original | Replace With | Words Saved |\n")
                f.write("|----------|-------------|-------------|\n")
                for vp in plan['verbose_phrases'][:15]:
                    f.write(f"| \"{vp['original']}\" | \"{vp['replacement']}\" | {vp['word_savings']} |\n")
                if len(plan['verbose_phrases']) > 15:
                    f.write(f"\n*...and {len(plan['verbose_phrases']) - 15} more*\n\n")
            
            if plan['redundant_paragraphs']:
                f.write(f"\n### Redundant Paragraphs ({len(plan['redundant_paragraphs'])} pairs)\n\n")
                for rp in plan['redundant_paragraphs'][:5]:
                    f.write(f"- **Similarity {rp['similarity']}** (~{rp['word_savings']} words)\n")
                    f.write(f"  - A: {rp['para_a_preview']}\n")
                    f.write(f"  - B: {rp['para_b_preview']}\n\n")
            
            if plan['repeated_arguments']:
                f.write(f"\n### Repeated Arguments ({len(plan['repeated_arguments'])} found)\n\n")
                for ra in plan['repeated_arguments'][:10]:
                    f.write(f"- \"{ra['phrase']}\" — appears in {ra['appears_in_sections']} sections\n")
            
            if plan.get('recommendation'):
                f.write(f"\n### ⚠️ Recommendation\n\n{plan['recommendation']}\n")
    
    print(f"Markdown report saved to: {md_path}")
    
    # Print actionable next steps
    print("\n🎯 RECOMMENDED ACTIONS:")
    for fid, plan in sorted(all_plans.items()):
        if not plan['over_limit']:
            continue
        status = plan.get('status', 'UNKNOWN')
        if status == 'TRIMMABLE_AUTO':
            print(f"  {fid}: Run auto-trim (verbose phrases alone may suffice)")
        elif status == 'TRIMMABLE_WITH_REWRITE':
            print(f"  {fid}: Auto-trim + manual rewrite of {plan.get('confidence','')} sections")
        else:
            print(f"  {fid}: ⚠️ MAJOR REWRITE needed — consider splitting into brief + appendix")


if __name__ == '__main__':
    main()
