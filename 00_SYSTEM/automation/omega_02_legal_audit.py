#!/usr/bin/env python3
"""
Ω2: LEGAL DOCUMENT AUDIT — OMEGA-ELITE-MASTER
Right-click any folder → audit all legal documents for Michigan court compliance.
Checks: case numbers, party names, citations, COS, signature blocks, hallucinations.
"""
import sys, os, re, json
from pathlib import Path
from datetime import datetime

KNOWN_HALLUCINATIONS = [
    "MCL 722.27c",  # Does not exist
    "MCR 2.119(F)(1)", "MCR 2.119(F)(2)",  # Correct is (F)(3)
    "Brady v. Maryland",  # Criminal only, not civil
]

REQUIRED_PATTERNS = {
    "case_number": r'\d{4}-\d{4,6}-[A-Z]{2}',
    "mcr_citation": r'MCR\s+\d+\.\d+',
    "mcl_citation": r'MCL\s+\d+\.\d+',
    "cos_present": r'(?i)certificate\s+of\s+service',
    "signature_block": r'(?i)respectfully\s+submitted|/s/',
    "date_line": r'(?i)dated?:?\s*\w+\s+\d{1,2},?\s*\d{4}',
    "pro_se": r'(?i)pro\s+se|in\s+propria\s+persona',
    "court_header": r'(?i)state\s+of\s+michigan|circuit\s+court|district\s+court',
}

CHILD_PROTECTIONS = [
    (r'\bLincoln\b', "CHILD_NAME_EXPOSED: Use L.D.W. not Lincoln"),
    (r'\b[Ll]incoln\s+(?:Daniel\s+)?(?:Watson|Pigors)\b', "FULL_CHILD_NAME: Use initials L.D.W."),
]

PARTY_CHECKS = {
    "andrew": r'Andrew\s+J\.?\s+Pigors',
    "emily": r'Emily\s+A\.?\s+Watson',
}

def audit_file(fp):
    """Audit a single legal document."""
    try:
        text = fp.read_text(encoding='utf-8', errors='replace')
    except Exception:
        return {"file": fp.name, "score": 0, "gates": {}, "issues": ["UNREADABLE"]}

    gates = {}
    issues = []

    # Check required patterns
    for name, pattern in REQUIRED_PATTERNS.items():
        found = bool(re.search(pattern, text))
        gates[name] = found
        if not found:
            issues.append(f"MISSING: {name}")

    # Check hallucinations
    for halluc in KNOWN_HALLUCINATIONS:
        if halluc.lower() in text.lower():
            issues.append(f"HALLUCINATION: {halluc}")
            gates["no_hallucinations"] = False

    # Child name protection
    for pattern, msg in CHILD_PROTECTIONS:
        if re.search(pattern, text):
            issues.append(msg)

    # Placeholder detection
    placeholders = re.findall(r'\[(?:INSERT|TODO|TBD|FILL|XXX|EMAIL|ADDRESS|DATE)\]', text, re.I)
    if placeholders:
        issues.append(f"PLACEHOLDERS: {', '.join(set(placeholders))}")

    # Score
    total_gates = len(REQUIRED_PATTERNS) + 2  # +hallucinations +placeholders
    passed = sum(1 for v in gates.values() if v) + (0 if placeholders else 1) + (1 if gates.get("no_hallucinations", True) else 0)
    score = round(passed / total_gates * 100)

    return {"file": fp.name, "score": score, "gates": gates, "issues": issues, "word_count": len(text.split())}

def audit_folder(target):
    target = Path(target).resolve()
    print(f"{'='*60}")
    print(f"  Ω2: LEGAL DOCUMENT AUDIT")
    print(f"  Target: {target}")
    print(f"{'='*60}\n")

    results = []
    for fp in sorted(target.rglob("*")):
        if fp.suffix.lower() in ('.md', '.txt', '.docx') and fp.is_file():
            r = audit_file(fp)
            results.append(r)
            verdict = "✅ GO" if r["score"] >= 85 else "⚠️ FIX" if r["score"] >= 60 else "🔴 FAIL"
            print(f"  {verdict} {r['score']:3d}/100  {r['file']}")
            for iss in r["issues"]:
                print(f"         ⤷ {iss}")

    if results:
        avg = sum(r["score"] for r in results) / len(results)
        print(f"\n{'='*60}")
        print(f"  AUDIT SUMMARY")
        print(f"  Documents:  {len(results)}")
        print(f"  Avg Score:  {avg:.0f}/100")
        print(f"  Filing Ready (≥85): {sum(1 for r in results if r['score'] >= 85)}")
        print(f"  Needs Work (60-84): {sum(1 for r in results if 60 <= r['score'] < 85)}")
        print(f"  Failing (<60):      {sum(1 for r in results if r['score'] < 60)}")
        print(f"{'='*60}")
    else:
        print("  No legal documents (.md, .txt, .docx) found.")

    report_path = target / f"_legal_audit_{datetime.now():%Y%m%d_%H%M%S}.json"
    with open(report_path, "w") as f:
        json.dump({"audit_time": datetime.now().isoformat(), "results": results}, f, indent=2)
    print(f"\n📄 Report: {report_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python omega_02_legal_audit.py <folder_path>")
        sys.exit(1)
    audit_folder(sys.argv[1])
    input("\nPress Enter to close...")
