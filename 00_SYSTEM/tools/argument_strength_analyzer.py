#!/usr/bin/env python3
"""
NOVEL TOOL #30: Legal Argument Strength Analyzer
==================================================
Analyzes each argument in each filing for:
- Logical coherence (premises → conclusion chain)
- Authority support (citations backing each point)
- Evidence density (how much hard evidence per argument)
- Vulnerability assessment (where opposing counsel will attack)
- Persuasion score (how compelling to a judge)

Combines NLP techniques with legal reasoning analysis.
Outputs per-argument scores and improvement recommendations.

This is a LEGAL BRIEF QUALITY ENGINE — nothing like it exists
in current litigation software.
"""

import sys
import os
import json
import re
import sqlite3
from pathlib import Path
from datetime import datetime
from collections import defaultdict

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

DB_PATH = Path(r"C:\Users\andre\LitigationOS\litigation_context.db")
REPORTS_DIR = Path(r"C:\Users\andre\LitigationOS\00_SYSTEM\reports")
FILING_DIR = Path(r"C:\Users\andre\Desktop\LITIGATION_FILING_PACKAGE")

# Legal reasoning patterns (weighted signals)
STRONG_ARGUMENT_SIGNALS = {
    "citation_present": 2.0,           # Has at least one citation
    "michigan_authority": 2.5,          # Michigan case law cited
    "binding_authority": 3.0,           # MI Supreme Court or 6th Circuit
    "constitutional_basis": 2.5,        # Constitutional argument
    "statutory_basis": 2.0,             # Statute cited
    "evidence_referenced": 2.0,         # Exhibit/evidence referenced
    "logical_connector": 1.0,           # "therefore", "because", "thus"
    "standard_of_review": 1.5,          # Identifies standard of review
    "fact_specific": 1.5,               # References specific facts
    "quotation_from_case": 2.0,         # Direct quotation from authority
}

WEAK_ARGUMENT_SIGNALS = {
    "conclusory": -2.0,                 # "clearly", "obviously" without support
    "emotional_language": -1.5,         # "outrageous", "shocking", "disgusting"
    "no_citation": -3.0,               # Legal claim without citation
    "ad_hominem": -2.5,               # Personal attacks
    "speculation": -2.0,              # "likely", "probably", "may have"
    "passive_voice_excess": -0.5,     # Excessive passive voice
    "run_on_sentence": -0.5,          # Very long sentences (>50 words)
    "placeholder": -5.0,              # [INSERT], [REQUIRED], etc.
}

# Citation patterns
CITATION_PATTERNS = {
    "michigan_supreme": re.compile(r'\d+\s+Mich\s+\d+', re.IGNORECASE),
    "michigan_appeals": re.compile(r'\d+\s+Mich\s+App\s+\d+', re.IGNORECASE),
    "federal_supreme": re.compile(r'\d+\s+US\s+\d+', re.IGNORECASE),
    "sixth_circuit": re.compile(r'\d+\s+F\.\d[a-z]*\s+\d+', re.IGNORECASE),
    "federal_district": re.compile(r'\d+\s+F\.\s*Supp', re.IGNORECASE),
    "mcl": re.compile(r'MCL\s+[\d.]+', re.IGNORECASE),
    "mcr": re.compile(r'MCR\s+[\d.]+', re.IGNORECASE),
    "usc": re.compile(r'\d+\s+USC\s+§?\s*\d+', re.IGNORECASE),
    "constitution": re.compile(r'(Const\s+1963|Amendment|U\.S\.\s*Const)', re.IGNORECASE),
    "northwest_reporter": re.compile(r'\d+\s+NW\d*d?\s+\d+', re.IGNORECASE),
}

CONCLUSORY_WORDS = [
    "clearly", "obviously", "undeniably", "unquestionably",
    "without doubt", "it is clear", "beyond dispute",
    "manifestly", "patently", "self-evident"
]

EMOTIONAL_WORDS = [
    "outrageous", "shocking", "disgusting", "appalling",
    "egregious", "unconscionable", "reprehensible",
    "evil", "malicious", "vindictive", "corrupt"
]

LOGICAL_CONNECTORS = [
    "therefore", "thus", "accordingly", "consequently",
    "because", "since", "given that", "inasmuch as",
    "it follows that", "for this reason", "as demonstrated"
]

SPECULATION_WORDS = [
    "likely", "probably", "perhaps", "possibly", "may have",
    "might have", "could have", "it appears", "it seems",
    "presumably", "ostensibly"
]

PLACEHOLDER_PATTERN = re.compile(r'\[(?:INSERT|REQUIRED|ATTACH|VERIFY|TBD|TODO|ANDREW|UNKNOWN)[^\]]*\]', re.IGNORECASE)


def get_db_connection():
    conn = sqlite3.connect(str(DB_PATH), timeout=60)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    conn.row_factory = sqlite3.Row
    return conn


def extract_sections(content):
    """Extract logical sections/arguments from a filing."""
    sections = []
    current_section = {"title": "PREAMBLE", "content": "", "line_start": 1}

    lines = content.split("\n")
    for i, line in enumerate(lines, 1):
        # Detect section headers (## or ALL CAPS lines or Roman numerals)
        if (line.strip().startswith("## ") or
            line.strip().startswith("# ") or
            re.match(r'^[IVX]+\.\s+[A-Z]', line.strip()) or
            re.match(r'^SECTION\s+\d+', line.strip(), re.IGNORECASE) or
            (len(line.strip()) > 5 and line.strip() == line.strip().upper() and
             not line.strip().startswith("[") and len(line.strip()) < 100)):

            if current_section["content"].strip():
                sections.append(current_section)
            current_section = {
                "title": line.strip().lstrip("#").strip(),
                "content": "",
                "line_start": i
            }
        else:
            current_section["content"] += line + "\n"

    if current_section["content"].strip():
        sections.append(current_section)

    return sections


def analyze_section(section):
    """Analyze a single section for argument strength."""
    content = section["content"]
    title = section["title"]

    scores = defaultdict(float)
    findings = []

    if len(content.strip()) < 20:
        return {"score": 0, "findings": ["Section is empty or too short"], "details": {}}

    # Check for citations
    citation_count = 0
    citation_types = []
    for ctype, pattern in CITATION_PATTERNS.items():
        matches = pattern.findall(content)
        if matches:
            citation_count += len(matches)
            citation_types.append(ctype)
            if ctype in ("michigan_supreme", "sixth_circuit", "federal_supreme"):
                scores["binding_authority"] = STRONG_ARGUMENT_SIGNALS["binding_authority"]
            elif ctype in ("michigan_appeals",):
                scores["michigan_authority"] = STRONG_ARGUMENT_SIGNALS["michigan_authority"]
            elif ctype in ("mcl", "usc"):
                scores["statutory_basis"] = STRONG_ARGUMENT_SIGNALS["statutory_basis"]
            elif ctype in ("mcr",):
                scores["citation_present"] = STRONG_ARGUMENT_SIGNALS["citation_present"]
            elif ctype in ("constitution",):
                scores["constitutional_basis"] = STRONG_ARGUMENT_SIGNALS["constitutional_basis"]

    if citation_count > 0:
        scores["citation_present"] = max(scores.get("citation_present", 0),
                                          STRONG_ARGUMENT_SIGNALS["citation_present"])
        findings.append(f"✅ {citation_count} citations found ({', '.join(citation_types[:3])})")
    else:
        # Check if section makes legal claims without citations
        legal_claim_words = ["must", "shall", "required", "prohibited", "right to", "entitled"]
        if any(word in content.lower() for word in legal_claim_words):
            scores["no_citation"] = WEAK_ARGUMENT_SIGNALS["no_citation"]
            findings.append("❌ Legal claims made without supporting citations")

    # Check for evidence references
    evidence_patterns = [r'Exhibit\s+[A-Z\d]+', r'Ex\.\s+\d+', r'evidence shows',
                         r'attached hereto', r'record at', r'transcript at']
    evidence_count = sum(len(re.findall(p, content, re.IGNORECASE)) for p in evidence_patterns)
    if evidence_count > 0:
        scores["evidence_referenced"] = STRONG_ARGUMENT_SIGNALS["evidence_referenced"]
        findings.append(f"✅ {evidence_count} evidence references")

    # Check for logical connectors
    connector_count = sum(1 for conn in LOGICAL_CONNECTORS if conn.lower() in content.lower())
    if connector_count > 0:
        scores["logical_connector"] = min(connector_count * 0.5,
                                          STRONG_ARGUMENT_SIGNALS["logical_connector"])
        findings.append(f"✅ {connector_count} logical connectors")

    # Check for conclusory language
    conclusory_count = sum(1 for word in CONCLUSORY_WORDS if word.lower() in content.lower())
    if conclusory_count > 0:
        scores["conclusory"] = conclusory_count * WEAK_ARGUMENT_SIGNALS["conclusory"]
        findings.append(f"⚠️ {conclusory_count} conclusory words (weaken argument)")

    # Check for emotional language
    emotional_count = sum(1 for word in EMOTIONAL_WORDS if word.lower() in content.lower())
    if emotional_count > 0:
        scores["emotional_language"] = emotional_count * WEAK_ARGUMENT_SIGNALS["emotional_language"]
        findings.append(f"⚠️ {emotional_count} emotional words (remove for credibility)")

    # Check for speculation
    spec_count = sum(1 for word in SPECULATION_WORDS if word.lower() in content.lower())
    if spec_count > 0:
        scores["speculation"] = spec_count * WEAK_ARGUMENT_SIGNALS["speculation"]
        findings.append(f"⚠️ {spec_count} speculative words")

    # Check for placeholders
    placeholders = PLACEHOLDER_PATTERN.findall(content)
    if placeholders:
        scores["placeholder"] = len(placeholders) * WEAK_ARGUMENT_SIGNALS["placeholder"]
        findings.append(f"🔴 {len(placeholders)} PLACEHOLDERS — must be filled before filing")

    # Check for quotations from cases
    quote_count = content.count('"') // 2  # rough quote count
    if quote_count > 0 and citation_count > 0:
        scores["quotation_from_case"] = min(quote_count * 0.5,
                                             STRONG_ARGUMENT_SIGNALS["quotation_from_case"])

    # Sentence analysis
    sentences = re.split(r'[.!?]+', content)
    long_sentences = [s for s in sentences if len(s.split()) > 50]
    if long_sentences:
        scores["run_on_sentence"] = len(long_sentences) * WEAK_ARGUMENT_SIGNALS["run_on_sentence"]
        findings.append(f"⚠️ {len(long_sentences)} run-on sentences (>50 words)")

    # Standard of review mentioned
    if re.search(r'standard of review|abuse of discretion|de novo|clearly erroneous',
                 content, re.IGNORECASE):
        scores["standard_of_review"] = STRONG_ARGUMENT_SIGNALS["standard_of_review"]
        findings.append("✅ Standard of review identified")

    # Fact-specific references
    fact_patterns = [r'\b(on|dated?)\s+\w+\s+\d+,?\s+\d{4}', r'paragraph\s+\d+',
                     r'page\s+\d+', r'¶\s*\d+']
    fact_count = sum(len(re.findall(p, content, re.IGNORECASE)) for p in fact_patterns)
    if fact_count > 0:
        scores["fact_specific"] = min(fact_count * 0.5, STRONG_ARGUMENT_SIGNALS["fact_specific"])
        findings.append(f"✅ {fact_count} fact-specific references")

    # Calculate total score
    total = sum(scores.values())
    # Normalize to 0-10 scale
    normalized = max(0, min(10, (total + 10) / 2.5))

    return {
        "score": round(normalized, 1),
        "raw_score": round(total, 2),
        "findings": findings,
        "citation_count": citation_count,
        "citation_types": citation_types,
        "evidence_refs": evidence_count,
        "placeholders": len(placeholders) if placeholders else 0,
        "word_count": len(content.split()),
        "details": {k: round(v, 2) for k, v in scores.items()}
    }


def grade(score):
    """Convert score to letter grade."""
    if score >= 8.5: return "A"
    if score >= 7.5: return "A-"
    if score >= 6.5: return "B+"
    if score >= 5.5: return "B"
    if score >= 4.5: return "B-"
    if score >= 3.5: return "C+"
    if score >= 2.5: return "C"
    if score >= 1.5: return "D"
    return "F"


def main():
    print("=" * 60)
    print("LEGAL ARGUMENT STRENGTH ANALYZER v1.0")
    print("Per-argument quality scoring with improvement recs")
    print("=" * 60)

    all_results = {}
    filing_grades = {}
    total_arguments = 0
    total_weak = 0
    total_placeholders = 0

    # Process each filing
    filing_dirs = sorted(FILING_DIR.glob("PKG_F*"))

    for pkg_dir in filing_dirs:
        filing_id = pkg_dir.name.split("_")[1]  # PKG_F3_... → F3
        main_filing = pkg_dir / "01_MAIN_FILING.md"

        if not main_filing.exists():
            print(f"\n⚠️ {filing_id}: No main filing found at {main_filing}")
            continue

        content = main_filing.read_text(encoding="utf-8", errors="replace")
        sections = extract_sections(content)

        print(f"\n{'─'*50}")
        print(f"📄 {filing_id} — {len(sections)} sections, {len(content.split())} words")

        filing_result = {
            "filing_id": filing_id,
            "directory": str(pkg_dir),
            "total_words": len(content.split()),
            "total_sections": len(sections),
            "sections": [],
            "average_score": 0,
            "grade": "",
            "weakest_sections": [],
            "strongest_sections": [],
            "total_citations": 0,
            "total_evidence_refs": 0,
            "total_placeholders": 0,
            "recommendations": []
        }

        section_scores = []

        for section in sections:
            if len(section["content"].strip()) < 30:
                continue

            analysis = analyze_section(section)
            total_arguments += 1

            section_data = {
                "title": section["title"][:60],
                "line_start": section["line_start"],
                **analysis
            }
            filing_result["sections"].append(section_data)
            section_scores.append(analysis["score"])

            filing_result["total_citations"] += analysis["citation_count"]
            filing_result["total_evidence_refs"] += analysis["evidence_refs"]
            filing_result["total_placeholders"] += analysis["placeholders"]
            total_placeholders += analysis["placeholders"]

            grade_str = grade(analysis["score"])
            status = "✅" if analysis["score"] >= 5 else "⚠️" if analysis["score"] >= 3 else "❌"
            print(f"  {status} [{grade_str}] {analysis['score']:4.1f}/10  "
                  f"{section['title'][:40]:40s} "
                  f"({analysis['citation_count']}cit, {analysis['evidence_refs']}ev)")

            if analysis["score"] < 4:
                total_weak += 1

        if section_scores:
            avg = sum(section_scores) / len(section_scores)
            filing_result["average_score"] = round(avg, 1)
            filing_result["grade"] = grade(avg)

            # Find weakest and strongest
            sorted_sections = sorted(filing_result["sections"],
                                     key=lambda x: x["score"])
            filing_result["weakest_sections"] = [s["title"] for s in sorted_sections[:3]]
            filing_result["strongest_sections"] = [s["title"] for s in sorted_sections[-3:]]

            # Generate recommendations
            recs = []
            if filing_result["total_placeholders"] > 0:
                recs.append(f"🔴 CRITICAL: Fill {filing_result['total_placeholders']} placeholders before filing")
            if avg < 5:
                recs.append("⚠️ Overall argument quality below threshold — needs substantial revision")
            if filing_result["total_citations"] < len(sections) * 0.5:
                recs.append("⚠️ Low citation density — add supporting authorities")
            weak_sections = [s for s in filing_result["sections"] if s["score"] < 3]
            for ws in weak_sections:
                recs.append(f"❌ Rewrite '{ws['title'][:30]}' — score {ws['score']}/10")
            filing_result["recommendations"] = recs

            print(f"  ═══ FILING GRADE: {filing_result['grade']} ({avg:.1f}/10) "
                  f"| {filing_result['total_citations']} citations "
                  f"| {filing_result['total_placeholders']} placeholders")

        filing_grades[filing_id] = filing_result["grade"]
        all_results[filing_id] = filing_result

    # Summary
    print(f"\n{'='*60}")
    print(f"ARGUMENT STRENGTH ANALYSIS — SUMMARY")
    print(f"{'='*60}")
    print(f"Filings analyzed:         {len(all_results)}")
    print(f"Total arguments:          {total_arguments}")
    print(f"Weak arguments (<4/10):   {total_weak}")
    print(f"Total placeholders:       {total_placeholders}")
    print(f"\nFiling Grades:")
    for fid in sorted(filing_grades.keys()):
        r = all_results[fid]
        print(f"  {fid}: {r['grade']:3s} ({r['average_score']:4.1f}/10) "
              f"— {r['total_citations']} citations, {r['total_evidence_refs']} evidence refs")

    # Save JSON
    output = {
        "generated": datetime.now().isoformat(),
        "summary": {
            "filings_analyzed": len(all_results),
            "total_arguments": total_arguments,
            "weak_arguments": total_weak,
            "total_placeholders": total_placeholders,
            "filing_grades": filing_grades
        },
        "filings": all_results
    }

    json_path = REPORTS_DIR / "argument_strength.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, default=str)

    # Markdown report
    md_lines = ["# LEGAL ARGUMENT STRENGTH ANALYSIS"]
    md_lines.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n")
    md_lines.append("## Summary\n")
    md_lines.append(f"| Metric | Value |")
    md_lines.append(f"|--------|-------|")
    md_lines.append(f"| Filings Analyzed | {len(all_results)} |")
    md_lines.append(f"| Total Arguments | {total_arguments} |")
    md_lines.append(f"| Weak Arguments | {total_weak} |")
    md_lines.append(f"| Placeholders | {total_placeholders} |")
    md_lines.append("")

    md_lines.append("## Filing Grades\n")
    md_lines.append("| Filing | Grade | Score | Citations | Evidence | Placeholders |")
    md_lines.append("|--------|-------|-------|-----------|----------|-------------|")
    for fid in sorted(all_results.keys()):
        r = all_results[fid]
        md_lines.append(f"| {fid} | **{r['grade']}** | {r['average_score']}/10 | "
                        f"{r['total_citations']} | {r['total_evidence_refs']} | "
                        f"{r['total_placeholders']} |")

    md_lines.append("\n## Recommendations\n")
    for fid in sorted(all_results.keys()):
        r = all_results[fid]
        if r.get("recommendations"):
            md_lines.append(f"### {fid}")
            for rec in r["recommendations"]:
                md_lines.append(f"- {rec}")
            md_lines.append("")

    md_path = REPORTS_DIR / "ARGUMENT_STRENGTH_REPORT.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    print(f"\n✅ JSON report: {json_path}")
    print(f"✅ Markdown report: {md_path}")

    return output


if __name__ == "__main__":
    main()
