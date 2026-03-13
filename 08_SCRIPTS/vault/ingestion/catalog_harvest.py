#!/usr/bin/env python3
"""
catalog_harvest.py — Full catalog of harvest texts directory.
Reads ALL 767 files, extracts legal metadata, classifies topics,
outputs JSONL catalog + summary report.
"""

import sys
import os
import json
import re
import time
from collections import Counter, defaultdict
from pathlib import Path

# Force UTF-8 stdout
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')
sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', errors='replace')

SOURCE_DIR = Path(r"I:\20260209_0430_HARVEST_000000006_FULL_SAFE\texts")
OUT_JSONL = Path(r"C:\Users\andre\LitigationOS\temp\harvest_catalog.jsonl")
OUT_SUMMARY = Path(r"C:\Users\andre\LitigationOS\temp\harvest_summary.txt")

LEGAL_TERMS = [
    "MCR", "MCL", "ex parte", "parenting time", "custody", "PPO",
    "contempt", "hearing", "order", "motion", "McNeill", "Watson",
    "Pigors", "bond", "alienation", "constitutional", "due process",
]

KEY_PARTIES = {
    "McNeill": re.compile(r"McNeill", re.IGNORECASE),
    "Watson": re.compile(r"Watson", re.IGNORECASE),
    "Pigors": re.compile(r"Pigors", re.IGNORECASE),
    "Barnes": re.compile(r"Barnes", re.IGNORECASE),
    "Berry": re.compile(r"Berry", re.IGNORECASE),
    "Rusco": re.compile(r"Rusco", re.IGNORECASE),
}

CASE_NUMBER_RE = re.compile(r"\d{4}-\d+-[A-Z]{2}")

DATE_PATTERNS = re.compile(
    r"(?:"
    r"\d{1,2}/\d{1,2}/\d{2,4}"        # MM/DD/YYYY or M/D/YY
    r"|\d{4}-\d{2}-\d{2}"              # YYYY-MM-DD
    r"|\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b"
    r"|\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b"
    r"|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s+\d{1,2},?\s+\d{4}\b"
    r")",
    re.IGNORECASE,
)

# Topic classification: keyword groups → topic label
TOPIC_KEYWORDS = {
    "custody": ["custody", "parenting time", "visitation", "placement", "parental rights", "child"],
    "PPO": ["PPO", "personal protection order", "stalking", "harassment", "restraining"],
    "judicial_misconduct": ["McNeill", "judicial", "misconduct", "bias", "recusal", "disqualif", "JTC", "canon"],
    "appellate": ["appeal", "appellate", "COA", "MSC", "court of appeals", "brief", "amicus"],
    "housing": ["eviction", "lease", "tenant", "landlord", "housing", "Shady Oaks", "rent"],
    "federal": ["1983", "federal", "constitutional", "due process", "civil rights", "14th amendment", "42 USC"],
    "evidence": ["evidence", "exhibit", "testimony", "deposition", "witness", "affidavit", "declaration"],
    "financial": ["support", "income", "wage", "financial", "arrears", "FOC", "obligation", "payment"],
}


def classify_topic(content_lower: str, term_counts: dict) -> str:
    """Classify dominant topic based on weighted keyword frequency."""
    scores = defaultdict(int)
    for topic, keywords in TOPIC_KEYWORDS.items():
        for kw in keywords:
            count = content_lower.count(kw.lower())
            scores[topic] += count
    if not scores or max(scores.values()) == 0:
        return "general"
    return max(scores, key=scores.get)


def count_legal_terms(content: str) -> dict:
    """Count occurrences of each legal term (case-insensitive)."""
    lower = content.lower()
    counts = {}
    for term in LEGAL_TERMS:
        counts[term] = lower.count(term.lower())
    return counts


def process_file(fpath: Path) -> dict:
    """Read a single file and extract all catalog metadata."""
    stat = fpath.stat()
    size = stat.st_size

    try:
        content = fpath.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return {
            "file_name": fpath.name,
            "file_path": str(fpath),
            "size_bytes": size,
            "error": str(e),
            "preview": "",
            "term_counts": {},
            "total_term_hits": 0,
            "case_numbers": [],
            "dates_found": [],
            "topic": "error",
            "party_mentions": {},
        }

    content_lower = content.lower()
    term_counts = count_legal_terms(content)
    total_hits = sum(term_counts.values())
    case_numbers = sorted(set(CASE_NUMBER_RE.findall(content)))
    dates_found = sorted(set(DATE_PATTERNS.findall(content)))[:50]  # cap dates list
    topic = classify_topic(content_lower, term_counts)

    party_mentions = {}
    for party, pattern in KEY_PARTIES.items():
        party_mentions[party] = len(pattern.findall(content))

    return {
        "file_name": fpath.name,
        "file_path": str(fpath),
        "size_bytes": size,
        "preview": content[:500],
        "term_counts": term_counts,
        "total_term_hits": total_hits,
        "case_numbers": case_numbers,
        "dates_found": dates_found,
        "topic": topic,
        "party_mentions": party_mentions,
    }


def main():
    print(f"Scanning: {SOURCE_DIR}")
    if not SOURCE_DIR.exists():
        print(f"ERROR: Directory not found: {SOURCE_DIR}")
        sys.exit(1)

    all_files = sorted(SOURCE_DIR.rglob("*"))
    all_files = [f for f in all_files if f.is_file()]
    total = len(all_files)
    print(f"Found {total} files to process.")

    results = []
    errors = []
    total_bytes = 0
    topic_counter = Counter()
    all_case_numbers = set()
    party_file_map = defaultdict(list)  # party → list of filenames

    t0 = time.time()

    with open(OUT_JSONL, "w", encoding="utf-8") as jf:
        for i, fpath in enumerate(all_files, 1):
            rec = process_file(fpath)
            jf.write(json.dumps(rec, ensure_ascii=False) + "\n")
            results.append(rec)

            total_bytes += rec["size_bytes"]
            topic_counter[rec["topic"]] += 1

            for cn in rec.get("case_numbers", []):
                all_case_numbers.add(cn)

            for party, count in rec.get("party_mentions", {}).items():
                if count > 0:
                    party_file_map[party].append(rec["file_name"])

            if "error" in rec:
                errors.append(rec)

            if i % 100 == 0 or i == total:
                elapsed = time.time() - t0
                rate = i / elapsed if elapsed > 0 else 0
                print(f"  [{i}/{total}] {rate:.0f} files/sec — {rec['file_name'][:60]}")

    elapsed = time.time() - t0
    print(f"\nDone. Processed {total} files in {elapsed:.1f}s.")
    print(f"JSONL written to: {OUT_JSONL}")

    # --- Summary report ---
    sorted_by_size = sorted(results, key=lambda r: r["size_bytes"], reverse=True)
    sorted_by_hits = sorted(results, key=lambda r: r.get("total_term_hits", 0), reverse=True)
    sorted_case_numbers = sorted(all_case_numbers)

    lines = []
    lines.append("=" * 80)
    lines.append("HARVEST CATALOG SUMMARY REPORT")
    lines.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Source: {SOURCE_DIR}")
    lines.append("=" * 80)
    lines.append("")

    lines.append(f"Total files processed: {total}")
    lines.append(f"Total bytes read:      {total_bytes:,} ({total_bytes / (1024*1024):.1f} MB)")
    lines.append(f"Errors/unreadable:     {len(errors)}")
    lines.append(f"Processing time:       {elapsed:.1f}s")
    lines.append("")

    lines.append("-" * 40)
    lines.append("TOPIC DISTRIBUTION")
    lines.append("-" * 40)
    for topic, count in topic_counter.most_common():
        pct = 100 * count / total if total else 0
        bar = "#" * int(pct / 2)
        lines.append(f"  {topic:<25} {count:>4}  ({pct:5.1f}%)  {bar}")
    lines.append("")

    lines.append("-" * 40)
    lines.append("TOP 20 LARGEST FILES")
    lines.append("-" * 40)
    for rec in sorted_by_size[:20]:
        sz_kb = rec["size_bytes"] / 1024
        lines.append(f"  {sz_kb:>10.1f} KB  {rec['file_name']}")
    lines.append("")

    lines.append("-" * 40)
    lines.append("TOP 20 FILES BY LEGAL TERM HITS")
    lines.append("-" * 40)
    for rec in sorted_by_hits[:20]:
        lines.append(f"  {rec.get('total_term_hits', 0):>6} hits  {rec['file_name']}")
        # Show top 5 terms for this file
        tc = rec.get("term_counts", {})
        top5 = sorted(tc.items(), key=lambda x: x[1], reverse=True)[:5]
        top5_str = ", ".join(f"{t}={c}" for t, c in top5 if c > 0)
        if top5_str:
            lines.append(f"           → {top5_str}")
    lines.append("")

    lines.append("-" * 40)
    lines.append(f"ALL UNIQUE CASE NUMBERS ({len(sorted_case_numbers)})")
    lines.append("-" * 40)
    for cn in sorted_case_numbers:
        lines.append(f"  {cn}")
    lines.append("")

    lines.append("-" * 40)
    lines.append("KEY PARTY MENTIONS")
    lines.append("-" * 40)
    for party in ["McNeill", "Watson", "Pigors", "Barnes", "Berry", "Rusco"]:
        flist = party_file_map.get(party, [])
        lines.append(f"\n  {party}: {len(flist)} files")
        for fn in flist[:30]:
            lines.append(f"    - {fn}")
        if len(flist) > 30:
            lines.append(f"    ... and {len(flist) - 30} more")
    lines.append("")

    if errors:
        lines.append("-" * 40)
        lines.append(f"ERRORS ({len(errors)})")
        lines.append("-" * 40)
        for rec in errors:
            lines.append(f"  {rec['file_name']}: {rec.get('error', 'unknown')}")
        lines.append("")

    lines.append("=" * 80)
    lines.append("END OF REPORT")
    lines.append("=" * 80)

    report = "\n".join(lines)
    OUT_SUMMARY.write_text(report, encoding="utf-8")
    print(f"Summary written to: {OUT_SUMMARY}")
    print(f"\nQuick stats:")
    print(f"  Files: {total} | Bytes: {total_bytes:,} | Topics: {len(topic_counter)}")
    print(f"  Case numbers: {len(sorted_case_numbers)} | Errors: {len(errors)}")


if __name__ == "__main__":
    main()
