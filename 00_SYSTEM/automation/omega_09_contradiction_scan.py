#!/usr/bin/env python3
"""
Ω9: CONTRADICTION SCANNER — OMEGA-ELITE-MASTER
Right-click any folder → find contradictions across all documents.
Compares statements within and across files to detect inconsistencies.
Uses sentence-level comparison with keyword opposition detection.
"""
import sys, os, re, json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

OPPOSITION_PAIRS = [
    ("never", "always"), ("denied", "admitted"), ("no", "yes"),
    ("absent", "present"), ("refused", "agreed"), ("false", "true"),
    ("did not", "did"), ("was not", "was"), ("cannot", "can"),
    ("will not", "will"), ("doesn't", "does"), ("haven't", "have"),
    ("safe", "unsafe"), ("appropriate", "inappropriate"),
    ("voluntary", "involuntary"), ("fit", "unfit"),
    ("cooperative", "uncooperative"), ("stable", "unstable"),
    ("compliant", "noncompliant"), ("responsible", "irresponsible"),
    ("peaceful", "violent"), ("sober", "intoxicated"),
]

CLAIM_KEYWORDS = [
    r'(?i)claimed\b', r'(?i)stated\b', r'(?i)testified\b',
    r'(?i)alleged\b', r'(?i)asserted\b', r'(?i)reported\b',
    r'(?i)told\b', r'(?i)said\b', r'(?i)wrote\b',
    r'(?i)confirmed\b', r'(?i)denied\b',
]

def extract_statements(fp, target):
    """Extract claim-bearing sentences from a file."""
    try:
        text = fp.read_text(encoding='utf-8', errors='replace')
    except Exception:
        return []

    sentences = re.split(r'(?<=[.!?])\s+', text)
    statements = []
    for i, sent in enumerate(sentences):
        sent = sent.strip()
        if len(sent) < 20 or len(sent) > 500:
            continue
        for kw in CLAIM_KEYWORDS:
            if re.search(kw, sent):
                statements.append({
                    "text": sent,
                    "source": str(fp.relative_to(target)),
                    "index": i,
                    "keywords": [w.lower() for w in re.findall(r'\b\w{4,}\b', sent.lower())]
                })
                break
    return statements

def find_contradictions(statements):
    """Find statement pairs that contain opposing language about same topic."""
    contradictions = []
    
    for i, s1 in enumerate(statements):
        for j, s2 in enumerate(statements):
            if j <= i:
                continue
            if s1["source"] == s2["source"] and abs(s1["index"] - s2["index"]) < 3:
                continue

            # Check for shared topic (3+ common keywords)
            common = set(s1["keywords"]) & set(s2["keywords"])
            if len(common) < 2:
                continue

            # Check for opposition
            t1 = s1["text"].lower()
            t2 = s2["text"].lower()
            for pos, neg in OPPOSITION_PAIRS:
                if (pos in t1 and neg in t2) or (neg in t1 and pos in t2):
                    severity = "HIGH" if len(common) >= 4 else "MEDIUM"
                    contradictions.append({
                        "statement_a": s1["text"][:200],
                        "source_a": s1["source"],
                        "statement_b": s2["text"][:200],
                        "source_b": s2["source"],
                        "shared_topic": list(common)[:5],
                        "opposition": f"{pos} ↔ {neg}",
                        "severity": severity,
                    })
                    break

            if len(contradictions) >= 500:
                return contradictions
    return contradictions

def scan_folder(target):
    target = Path(target).resolve()
    print(f"{'='*60}")
    print(f"  Ω9: CONTRADICTION SCANNER")
    print(f"  Target: {target}")
    print(f"{'='*60}\n")

    all_statements = []
    files = 0
    for fp in sorted(target.rglob("*")):
        if fp.suffix.lower() in ('.md', '.txt', '.docx') and fp.is_file():
            stmts = extract_statements(fp, target)
            all_statements.extend(stmts)
            files += 1

    print(f"  Files scanned:    {files:,}")
    print(f"  Statements found: {len(all_statements):,}")
    print(f"  Analyzing contradictions...")

    contradictions = find_contradictions(all_statements)

    high = sum(1 for c in contradictions if c["severity"] == "HIGH")
    medium = len(contradictions) - high

    print(f"\n📊 CONTRADICTION RESULTS")
    print(f"  Contradictions found: {len(contradictions)}")
    print(f"  🔴 HIGH severity: {high}")
    print(f"  🟡 MEDIUM severity: {medium}")

    if contradictions:
        print(f"\n{'─'*60}")
        for i, c in enumerate(contradictions[:25]):
            icon = "🔴" if c["severity"] == "HIGH" else "🟡"
            print(f"\n  {icon} #{i+1} [{c['severity']}] Opposition: {c['opposition']}")
            print(f"    A: \"{c['statement_a'][:100]}...\"")
            print(f"       Source: {c['source_a']}")
            print(f"    B: \"{c['statement_b'][:100]}...\"")
            print(f"       Source: {c['source_b']}")
            print(f"    Shared topic: {', '.join(c['shared_topic'])}")

    report_path = target / f"_contradictions_{datetime.now():%Y%m%d_%H%M%S}.json"
    with open(report_path, "w") as f:
        json.dump({"scan_time": datetime.now().isoformat(),
                    "files": files, "statements": len(all_statements),
                    "total_contradictions": len(contradictions),
                    "high_severity": high, "medium_severity": medium,
                    "contradictions": contradictions}, f, indent=2)
    print(f"\n📄 Report: {report_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python omega_09_contradiction_scan.py <folder_path>")
        sys.exit(1)
    scan_folder(sys.argv[1])
    input("\nPress Enter to close...")
