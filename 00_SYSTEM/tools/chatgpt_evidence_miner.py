#!/usr/bin/env python3
"""
Tool #46 — ChatGPT Evidence Miner
====================================
Scans ChatGPT export files (conversations.json) for litigation-relevant
evidence. ChatGPT conversations between Andrew and Emily (or about the case)
may contain admissions, contradictions, and timeline data.

Searches for:
- Admissions by Emily Watson
- Contradictions with court filings
- Timeline events (custody exchanges, incidents)
- Financial discussions (rent, child support)
- Statements about the child (L.D.W.)
- References to court proceedings, judges, attorneys
"""
import sys, json, re, os, glob, sqlite3
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
DB_PATH = REPO / "litigation_context.db"
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"

# Search paths for ChatGPT exports
SEARCH_PATHS = [
    r"C:\Users\andre",
    "D:\\",
    "F:\\",
    "G:\\",
    "I:\\",
]

# Evidence keywords
KEYWORDS = {
    'custody': ['custody', 'parenting time', 'visitation', 'overnight', 'pickup', 'dropoff', 'exchange'],
    'admissions': ['i did', 'i know', 'i admit', 'you\'re right', 'my fault', 'i lied', 'i was wrong'],
    'child': ['L.D.W.', 'the baby', 'our child', 'our kid', 'daughter', 'son'],
    'court': ['court', 'judge', 'McNeill', 'hearing', 'order', 'filed', 'motion', 'attorney', 'Barnes'],
    'financial': ['rent', 'child support', 'money', 'payment', 'owe', 'paid', 'deposit'],
    'threats': ['police', 'arrest', 'ppo', 'protection order', 'restraining', 'jail', 'contempt'],
    'housing': ['shady oaks', 'mobile home', 'trailer', 'eviction', 'lease', 'lot rent'],
    'watson_family': ['Emily', 'Watson', 'Berry', 'Ronald', 'Lori', 'mother'],
}

def find_chatgpt_exports():
    """Find ChatGPT export files across drives."""
    found = []
    patterns = [
        '**/conversations.json',
        '**/chat.html',
        '**/ChatGPT*export*',
        '**/chatgpt*/*.json',
        '**/*openai*export*',
    ]
    
    for search_path in SEARCH_PATHS:
        for pattern in patterns:
            try:
                matches = glob.glob(os.path.join(search_path, pattern), recursive=True)
                for m in matches[:10]:  # Limit per path
                    size = os.path.getsize(m)
                    if size > 100:  # Skip empty files
                        found.append({'path': m, 'size': size})
            except (PermissionError, OSError):
                continue
    
    return found

def extract_evidence_from_json(filepath):
    """Extract litigation-relevant content from ChatGPT JSON export."""
    evidence = []
    
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            data = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        return [{'error': str(e), 'file': filepath}]
    
    conversations = data if isinstance(data, list) else [data]
    
    for conv in conversations:
        if not isinstance(conv, dict):
            continue
        
        title = conv.get('title', 'Unknown')
        create_time = conv.get('create_time', 0)
        
        # Extract messages
        mapping = conv.get('mapping', {})
        for node_id, node in mapping.items():
            msg = node.get('message')
            if not msg or not isinstance(msg, dict):
                continue
            
            content = msg.get('content', {})
            if isinstance(content, dict):
                parts = content.get('parts', [])
                text = ' '.join(str(p) for p in parts if isinstance(p, str))
            elif isinstance(content, str):
                text = content
            else:
                continue
            
            if len(text) < 20:
                continue
            
            # Check for keyword matches
            matches = {}
            text_lower = text.lower()
            for category, keywords in KEYWORDS.items():
                hits = [kw for kw in keywords if kw.lower() in text_lower]
                if hits:
                    matches[category] = hits
            
            if matches:
                role = msg.get('author', {}).get('role', 'unknown')
                evidence.append({
                    'conversation': title,
                    'role': role,
                    'text': text[:500],
                    'categories': list(matches.keys()),
                    'keyword_hits': matches,
                    'timestamp': create_time,
                    'source_file': filepath,
                })
    
    return evidence

def scan_text_files_for_chat(search_paths):
    """Scan for text/HTML files that might contain chat exports."""
    evidence = []
    patterns = ['*chat*.txt', '*chat*.html', '*conversation*.txt', '*messages*.txt']
    
    for search_path in search_paths:
        for pattern in patterns:
            try:
                matches = glob.glob(os.path.join(search_path, '**', pattern), recursive=True)
                for m in matches[:20]:
                    try:
                        size = os.path.getsize(m)
                        if 100 < size < 50_000_000:  # Skip empty and huge files
                            with open(m, 'r', encoding='utf-8', errors='replace') as f:
                                text = f.read(100000)  # First 100KB
                            
                            text_lower = text.lower()
                            hits = {}
                            for cat, kws in KEYWORDS.items():
                                found = [kw for kw in kws if kw.lower() in text_lower]
                                if found:
                                    hits[cat] = found
                            
                            if len(hits) >= 2:  # At least 2 categories match
                                evidence.append({
                                    'file': m,
                                    'size': size,
                                    'categories': list(hits.keys()),
                                    'preview': text[:300],
                                })
                    except (PermissionError, IOError):
                        continue
            except (PermissionError, OSError):
                continue
    
    return evidence

def main():
    print("=" * 70)
    print("CHATGPT EVIDENCE MINER — Tool #46")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 70)
    
    # Phase 1: Find ChatGPT export files
    print("\n📁 Phase 1: Scanning for ChatGPT exports...")
    exports = find_chatgpt_exports()
    print(f"  Found {len(exports)} potential export files")
    for exp in exports[:10]:
        print(f"    {exp['path']} ({exp['size']:,} bytes)")
    
    # Phase 2: Extract evidence from JSON exports
    print("\n🔍 Phase 2: Extracting evidence from exports...")
    all_evidence = []
    for exp in exports:
        if exp['path'].endswith('.json'):
            items = extract_evidence_from_json(exp['path'])
            all_evidence.extend(items)
            print(f"  {exp['path']}: {len(items)} evidence items")
    
    # Phase 3: Scan text/HTML files
    print("\n📄 Phase 3: Scanning text/HTML chat files...")
    text_evidence = scan_text_files_for_chat(SEARCH_PATHS[:3])  # Limit scan scope
    print(f"  Found {len(text_evidence)} relevant text files")
    for te in text_evidence[:5]:
        print(f"    {te['file']} ({te['size']:,} bytes) — categories: {', '.join(te['categories'])}")
    
    # Phase 4: Categorize and score
    print("\n📊 Phase 4: Categorizing evidence...")
    category_counts = {}
    for item in all_evidence:
        if 'error' in item:
            continue
        for cat in item.get('categories', []):
            category_counts[cat] = category_counts.get(cat, 0) + 1
    
    for cat, count in sorted(category_counts.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count} items")
    
    # Phase 5: Save reports
    print("\n💾 Phase 5: Saving reports...")
    
    report = {
        'generated': datetime.now().isoformat(),
        'tool': 'ChatGPT Evidence Miner (#46)',
        'summary': {
            'export_files_found': len(exports),
            'evidence_items': len(all_evidence),
            'text_files_found': len(text_evidence),
            'categories': category_counts,
        },
        'exports': [{'path': e['path'], 'size': e['size']} for e in exports],
        'evidence_sample': all_evidence[:50],
        'text_files': text_evidence[:20],
    }
    
    json_path = REPORTS_DIR / "chatgpt_evidence.json"
    json_path.write_text(json.dumps(report, indent=2, default=str), encoding='utf-8')
    
    md_lines = [
        "# CHATGPT EVIDENCE MINING REPORT",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n",
        f"## Summary",
        f"- Export files found: {len(exports)}",
        f"- Evidence items extracted: {len(all_evidence)}",
        f"- Relevant text files: {len(text_evidence)}",
        "",
        "## Category Breakdown",
        "| Category | Items |",
        "|----------|-------|",
    ]
    for cat, count in sorted(category_counts.items(), key=lambda x: -x[1]):
        md_lines.append(f"| {cat} | {count} |")
    
    md_lines.extend([
        "",
        "## Export Files Found",
    ])
    for exp in exports[:10]:
        md_lines.append(f"- `{exp['path']}` ({exp['size']:,} bytes)")
    
    if text_evidence:
        md_lines.extend(["", "## Relevant Text Files"])
        for te in text_evidence[:10]:
            md_lines.append(f"- `{te['file']}` — {', '.join(te['categories'])}")
    
    if all_evidence:
        md_lines.extend(["", "## Sample Evidence Items"])
        for item in all_evidence[:10]:
            if 'error' not in item:
                md_lines.append(f"- **{item.get('conversation', 'Unknown')}** [{item.get('role', '?')}]: {item.get('text', '')[:150]}...")
    
    md_path = REPORTS_DIR / "CHATGPT_EVIDENCE_REPORT.md"
    md_path.write_text('\n'.join(md_lines), encoding='utf-8')
    
    print(f"\n✅ Reports: {json_path.name}, {md_path.name}")
    print(f"📊 Total: {len(all_evidence)} evidence items across {len(category_counts)} categories")

if __name__ == '__main__':
    main()
