#!/usr/bin/env python3
"""
Ω3: EVIDENCE HARVESTER — OMEGA-ELITE-MASTER
Right-click any folder → extract quotes, dates, names, allegations from all documents.
Builds a structured evidence index from raw files.
"""
import sys, os, re, json, csv
from pathlib import Path
from datetime import datetime
from collections import Counter

DATE_PATTERNS = [
    r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b',
    r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',
    r'\b\d{4}-\d{2}-\d{2}\b',
]

PERSON_PATTERNS = [
    r'Andrew\s+(?:J\.?\s+)?Pigors',
    r'Emily\s+(?:A\.?\s+)?Watson',
    r'(?:Judge|Hon\.?)\s+\w+\s+\w+',
    r'Albert\s+Watson', r'Diana\s+Watson', r'Ronald\s+Berry',
    r'Pamela\s+Rusco', r'Jennifer\s+Barnes',
    r'Shannon\s+Berry', r'Cavan\s+Berry',
]

ALLEGATION_MARKERS = [
    r'(?i)allege[ds]?\b', r'(?i)claim[eds]?\b', r'(?i)assert[eds]?\b',
    r'(?i)accuse[ds]?\b', r'(?i)threaten', r'(?i)violat',
    r'(?i)abuse[ds]?\b', r'(?i)harass', r'(?i)stalking',
    r'(?i)domestic\s+violence', r'(?i)assault',
]

QUOTE_PATTERN = r'"([^"]{20,500})"'

def extract_evidence(fp):
    """Extract evidence elements from a single file."""
    try:
        text = fp.read_text(encoding='utf-8', errors='replace')
    except Exception:
        return None

    evidence = {"file": fp.name, "dates": [], "persons": [], "allegations": [], "quotes": [], "citations": []}

    for pat in DATE_PATTERNS:
        evidence["dates"].extend(re.findall(pat, text))
    evidence["dates"] = list(set(evidence["dates"]))

    for pat in PERSON_PATTERNS:
        evidence["persons"].extend(re.findall(pat, text))
    evidence["persons"] = list(set(evidence["persons"]))

    for pat in ALLEGATION_MARKERS:
        for m in re.finditer(pat, text):
            start = max(0, m.start() - 100)
            end = min(len(text), m.end() + 200)
            snippet = text[start:end].replace('\n', ' ').strip()
            evidence["allegations"].append(snippet)
    evidence["allegations"] = evidence["allegations"][:30]

    evidence["quotes"] = re.findall(QUOTE_PATTERN, text)[:20]

    mcr = re.findall(r'MCR\s+\d+\.\d+(?:\([A-Za-z0-9]+\))*', text)
    mcl = re.findall(r'MCL\s+\d+\.\d+[a-z]?', text)
    cases = re.findall(r'\b\w+\s+v\.?\s+\w+,?\s+\d+\s+(?:Mich|NW|F)\w*\s+\d+', text)
    evidence["citations"] = list(set(mcr + mcl + cases))

    return evidence

def harvest_folder(target):
    target = Path(target).resolve()
    print(f"{'='*60}")
    print(f"  Ω3: EVIDENCE HARVESTER")
    print(f"  Target: {target}")
    print(f"{'='*60}\n")

    all_evidence = []
    all_dates = Counter()
    all_persons = Counter()
    all_citations = Counter()
    files_processed = 0

    for fp in sorted(target.rglob("*")):
        if fp.suffix.lower() in ('.md', '.txt', '.pdf', '.docx', '.csv') and fp.is_file():
            ev = extract_evidence(fp)
            if ev:
                all_evidence.append(ev)
                files_processed += 1
                for d in ev["dates"]: all_dates[d] += 1
                for p in ev["persons"]: all_persons[p] += 1
                for c in ev["citations"]: all_citations[c] += 1
                if files_processed % 50 == 0:
                    print(f"  Processed {files_processed} files...")

    print(f"\n📊 HARVEST RESULTS")
    print(f"  Files processed: {files_processed:,}")
    print(f"  Total dates:     {sum(all_dates.values()):,} ({len(all_dates)} unique)")
    print(f"  Total persons:   {sum(all_persons.values()):,} ({len(all_persons)} unique)")
    print(f"  Total citations: {sum(all_citations.values()):,} ({len(all_citations)} unique)")
    total_quotes = sum(len(e["quotes"]) for e in all_evidence)
    total_allegations = sum(len(e["allegations"]) for e in all_evidence)
    print(f"  Total quotes:    {total_quotes:,}")
    print(f"  Allegations:     {total_allegations:,}")

    print(f"\n👤 TOP PERSONS:")
    for person, count in all_persons.most_common(15):
        print(f"  {count:>4}x  {person}")
    print(f"\n📅 TOP DATES:")
    for date, count in all_dates.most_common(15):
        print(f"  {count:>4}x  {date}")
    print(f"\n📜 TOP CITATIONS:")
    for cit, count in all_citations.most_common(15):
        print(f"  {count:>4}x  {cit}")

    report_path = target / f"_evidence_harvest_{datetime.now():%Y%m%d_%H%M%S}.json"
    with open(report_path, "w") as f:
        json.dump({"harvest_time": datetime.now().isoformat(), "files": files_processed,
                    "evidence": all_evidence[:200],
                    "date_index": dict(all_dates.most_common(100)),
                    "person_index": dict(all_persons),
                    "citation_index": dict(all_citations)}, f, indent=2)
    print(f"\n📄 Report: {report_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python omega_03_evidence_harvest.py <folder_path>")
        sys.exit(1)
    harvest_folder(sys.argv[1])
    input("\nPress Enter to close...")
