#!/usr/bin/env python3
"""
Ω4: CITATION EXTRACTOR — OMEGA-ELITE-MASTER
Right-click any folder → extract ALL legal citations (MCR, MCL, MRE, case law)
from every document. Builds a complete citation index with frequency analysis.
"""
import sys, os, re, json
from pathlib import Path
from datetime import datetime
from collections import Counter, defaultdict

CITATION_PATTERNS = {
    "MCR": r'MCR\s+(\d+\.\d+(?:\([A-Za-z0-9]+\))*(?:\([a-z]+\))*)',
    "MCL": r'MCL\s+(\d+\.\d+[a-z]?(?:\([0-9]+\))?)',
    "MRE": r'MRE\s+(\d+(?:\([a-z]\))?)',
    "USC": r'(\d+)\s+U\.?S\.?C\.?\s+§?\s*(\d+)',
    "FRCP": r'(?:FRCP|Fed\.?\s*R\.?\s*Civ\.?\s*P\.?)\s+(\d+)',
    "CASE_MICH": r'(\b\w+(?:\s+\w+)?\s+v\.?\s+\w+(?:\s+\w+)?),?\s+(\d+)\s+Mich(?:\s+App)?\s+(\d+)',
    "CASE_NW": r'(\b\w+(?:\s+\w+)?\s+v\.?\s+\w+(?:\s+\w+)?),?\s+(\d+)\s+NW\.?2d\s+(\d+)',
    "CASE_FED": r'(\b\w+(?:\s+\w+)?\s+v\.?\s+\w+(?:\s+\w+)?),?\s+(\d+)\s+F\.?(?:2d|3d|Supp\.?(?:2d|3d)?)\s+(\d+)',
    "CONST": r'Const\s+1963,?\s+art\s+(\d+),?\s+§\s*(\d+)',
}

KNOWN_BAD = {"MCL 722.27c", "MCR 2.119(F)(1)", "MCR 2.119(F)(2)"}

def extract_citations(fp):
    try:
        text = fp.read_text(encoding='utf-8', errors='replace')
    except Exception:
        return {}
    
    found = defaultdict(list)
    for ctype, pattern in CITATION_PATTERNS.items():
        for match in re.finditer(pattern, text):
            full = match.group(0).strip()
            found[ctype].append(full)
    return dict(found)

def extract_folder(target):
    target = Path(target).resolve()
    print(f"{'='*60}")
    print(f"  Ω4: CITATION EXTRACTOR")
    print(f"  Target: {target}")
    print(f"{'='*60}\n")

    all_citations = defaultdict(Counter)
    file_citations = {}
    warnings = []

    for fp in sorted(target.rglob("*")):
        if fp.suffix.lower() in ('.md', '.txt', '.docx') and fp.is_file():
            cits = extract_citations(fp)
            if cits:
                file_citations[str(fp.relative_to(target))] = {k: list(set(v)) for k, v in cits.items()}
                for ctype, items in cits.items():
                    for item in items:
                        all_citations[ctype][item] += 1
                        if any(bad in item for bad in KNOWN_BAD):
                            warnings.append(f"⚠️ KNOWN HALLUCINATION in {fp.name}: {item}")

    total = sum(sum(c.values()) for c in all_citations.values())
    unique = sum(len(c) for c in all_citations.values())

    print(f"📊 CITATION INDEX")
    print(f"  Total citations: {total:,}")
    print(f"  Unique citations: {unique}")
    print(f"  Files with citations: {len(file_citations)}")

    for ctype in ["MCR", "MCL", "MRE", "USC", "FRCP", "CASE_MICH", "CASE_NW", "CASE_FED", "CONST"]:
        if ctype in all_citations:
            print(f"\n📜 {ctype} ({len(all_citations[ctype])} unique, {sum(all_citations[ctype].values())} total):")
            for cit, count in all_citations[ctype].most_common(10):
                print(f"  {count:>4}x  {cit}")

    if warnings:
        print(f"\n🔴 WARNINGS ({len(warnings)}):")
        for w in warnings[:20]:
            print(f"  {w}")

    report_path = target / f"_citation_index_{datetime.now():%Y%m%d_%H%M%S}.json"
    with open(report_path, "w") as f:
        json.dump({
            "extract_time": datetime.now().isoformat(),
            "total_citations": total, "unique_citations": unique,
            "by_type": {k: dict(v.most_common()) for k, v in all_citations.items()},
            "by_file": file_citations, "warnings": warnings,
        }, f, indent=2)
    print(f"\n📄 Report: {report_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python omega_04_citation_extract.py <folder_path>")
        sys.exit(1)
    extract_folder(sys.argv[1])
    input("\nPress Enter to close...")
