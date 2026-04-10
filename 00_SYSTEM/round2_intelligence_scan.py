"""Round 2 Comprehensive Intelligence Extraction.
Scans key text/md files across drives for:
1. New adversary mentions with context
2. Court rules/procedures for DB ingestion
3. Brian Cross intelligence (identified GAP)
4. New harms, dates, patterns
"""
import sqlite3, os, re, glob, json
from collections import defaultdict

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"

def get_db():
    db = sqlite3.connect(DB_PATH)
    db.execute("PRAGMA busy_timeout=60000")
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA cache_size=-32000")
    return db

# Target adversaries for intelligence expansion
ADVERSARIES = {
    "Brian Cross": ["Brian Cross", "Cross", "park manager", "trailer park"],
    "Kim Davis": ["Kim Davis", "Davis"],
    "Kostrzewa": ["Kostrzewa", "60th District", "criminal case"],
    "Cassandra VanDam": ["VanDam", "Cassandra", "Van Dam"],
    "Lauren Duguid": ["Duguid", "Lauren Duguid", "prosecutor"],
    "DJ Hilson": ["Hilson", "D.J. Hilson", "DJ Hilson", "county prosecutor"],
    "Cavan Berry": ["Cavan Berry", "Cavan", "attorney magistrate"],
    "Ronald Berry": ["Ronald Berry", "Ron Berry", "Ronald T"],
    "Lori Watson": ["Lori Watson", "Lori", "Albert and Lori"],
    "Pamela Rusco": ["Rusco", "Pamela Rusco", "FOC"],
    "Mandi Martini": ["Martini", "Mandi Martini", "caseworker"],
}

# Patterns for court rules extraction
RULE_PATTERNS = [
    (r"MCR\s+(\d+\.\d+(?:\([A-Za-z0-9]+\))*)", "MCR"),
    (r"MCL\s+(\d+\.\d+[a-z]?(?:\([0-9]+\))*)", "MCL"),
    (r"MRE\s+(\d+(?:\([a-z]\))*)", "MRE"),
    (r"FRCP\s+(\d+(?:\([a-z]\))*)", "FRCP"),
    (r"42\s+USC\s+(?:§|Section)\s*1983", "FEDERAL"),
    (r"28\s+USC\s+(?:§|Section)\s*1343", "FEDERAL"),
]

# SCAO form patterns
FORM_PATTERNS = [
    (r"(FOC\s*\d+[a-z]?)", "FOC_FORM"),
    (r"(MC\s*\d+[a-z]?)", "MC_FORM"),
    (r"(DC\s*\d+[a-z]?)", "DC_FORM"),
    (r"(CC\s*\d+[a-z]?)", "CC_FORM"),
    (r"(SCAO\s+Form\s+\S+)", "SCAO_FORM"),
]

def scan_file_for_intel(filepath, max_size_mb=50):
    """Extract adversary mentions and rule citations from a text file."""
    try:
        size = os.path.getsize(filepath)
        if size > max_size_mb * 1024 * 1024:
            return None, None, None
        
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        
        # Find adversary mentions with context
        adversary_hits = defaultdict(list)
        lines = content.split("\n")
        for i, line in enumerate(lines):
            for adv_name, keywords in ADVERSARIES.items():
                for kw in keywords:
                    if kw.lower() in line.lower() and len(line.strip()) > 20:
                        # Get context (2 lines before + 2 after)
                        start = max(0, i - 2)
                        end = min(len(lines), i + 3)
                        ctx = "\n".join(lines[start:end]).strip()
                        if len(ctx) > 30 and ctx not in [h[1] for h in adversary_hits[adv_name]]:
                            adversary_hits[adv_name].append((kw, ctx[:500]))
                        break  # One hit per adversary per line
        
        # Find rule citations
        rules_found = set()
        for pattern, rule_type in RULE_PATTERNS:
            for m in re.finditer(pattern, content):
                rules_found.add((rule_type, m.group(0).strip()))
        
        # Find form references
        forms_found = set()
        for pattern, form_type in FORM_PATTERNS:
            for m in re.finditer(pattern, content, re.IGNORECASE):
                forms_found.add((form_type, m.group(0).strip()))
        
        return adversary_hits, rules_found, forms_found
    except Exception as e:
        return None, None, None

def main():
    # Scan locations (text/md files only — fast, high-value)
    scan_paths = [
        (r"C:\Users\andre\Desktop\*.txt", "Desktop TXT"),
        (r"C:\Users\andre\Desktop\*.md", "Desktop MD"),
        (r"C:\Users\andre\Desktop\**\*.txt", "Desktop Deep TXT"),
        (r"C:\Users\andre\Desktop\**\*.md", "Desktop Deep MD"),
        (r"C:\Users\andre\Documents\*.txt", "Documents TXT"),
        (r"C:\Users\andre\Documents\*.md", "Documents MD"),
        (r"C:\Users\andre\LitigationOS\04_ANALYSIS\**\*.md", "Analysis MD"),
        (r"C:\Users\andre\LitigationOS\05_FILINGS\**\*.md", "Filings MD"),
        (r"C:\Users\andre\LitigationOS\01_EVIDENCE\**\*.txt", "Evidence TXT"),
        (r"C:\Users\andre\LitigationOS\03_COURT\**\*.txt", "Court TXT"),
        (r"C:\Users\andre\LitigationOS\03_COURT\**\*.md", "Court MD"),
        (r"I:\07_LEGAL_INTEL\**\*.txt", "I: Legal Intel TXT"),
        (r"I:\07_LEGAL_INTEL\**\*.md", "I: Legal Intel MD"),
        (r"I:\02_EVIDENCE\**\*.txt", "I: Evidence TXT"),
        (r"D:\LitigationOS_tmp\*.txt", "D: Temp TXT"),
        (r"D:\LitigationOS_tmp\*.md", "D: Temp MD"),
        (r"J:\POLICE_REPORTS\*.txt", "J: Police TXT"),
        (r"J:\POLICE_REPORTS\*.csv", "J: Police CSV"),
    ]
    
    all_adversary_intel = defaultdict(list)
    all_rules = set()
    all_forms = set()
    files_scanned = 0
    brian_cross_intel = []
    
    for pattern, label in scan_paths:
        files = glob.glob(pattern, recursive=True)
        if files:
            print(f"Scanning {label}: {len(files)} files...")
        for filepath in files[:500]:  # Cap per pattern to prevent runaway
            adv, rules, forms = scan_file_for_intel(filepath)
            if adv is None:
                continue
            files_scanned += 1
            
            for name, hits in adv.items():
                for kw, ctx in hits:
                    all_adversary_intel[name].append({
                        "file": filepath,
                        "keyword": kw,
                        "context": ctx
                    })
                    if name == "Brian Cross":
                        brian_cross_intel.append({
                            "file": filepath,
                            "context": ctx
                        })
            
            all_rules.update(rules)
            all_forms.update(forms)
    
    print(f"\n{'='*60}")
    print(f"SCAN COMPLETE: {files_scanned} files processed")
    print(f"{'='*60}")
    
    # Report adversary findings
    print(f"\n=== ADVERSARY INTELLIGENCE FOUND ===")
    for name, hits in sorted(all_adversary_intel.items(), key=lambda x: -len(x[1])):
        print(f"  {name}: {len(hits)} new mentions")
    
    # Brian Cross special focus
    print(f"\n=== BRIAN CROSS INTELLIGENCE (GAP FILL) ===")
    for item in brian_cross_intel[:10]:
        print(f"  File: {item['file']}")
        print(f"  Context: {item['context'][:200]}...")
        print()
    
    # Rule citations found
    print(f"\n=== RULE CITATIONS DISCOVERED ===")
    rules_by_type = defaultdict(set)
    for rule_type, citation in all_rules:
        rules_by_type[rule_type].add(citation)
    for rtype, cites in sorted(rules_by_type.items()):
        print(f"  {rtype}: {len(cites)} unique citations")
        for c in sorted(cites)[:5]:
            print(f"    {c}")
        if len(cites) > 5:
            print(f"    ... and {len(cites)-5} more")
    
    # Form references found
    print(f"\n=== COURT FORMS DISCOVERED ===")
    for form_type, form_ref in sorted(all_forms):
        print(f"  [{form_type}] {form_ref}")
    
    # Save full results to JSON for further processing
    output = {
        "files_scanned": files_scanned,
        "adversary_intel": {k: v[:20] for k, v in all_adversary_intel.items()},  # Top 20 per adversary
        "brian_cross_intel": brian_cross_intel[:20],
        "rules_found": [(t, c) for t, c in all_rules],
        "forms_found": [(t, c) for t, c in all_forms],
    }
    
    out_path = r"D:\LitigationOS_tmp\round2_scan_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\nFull results saved to: {out_path}")

if __name__ == "__main__":
    main()
