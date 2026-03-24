#!/usr/bin/env python3
"""
Filing Readiness Scorecard — Automated Court Filing Compliance Checker
======================================================================
Novel tool for LitigationOS that scores each filing against Michigan court rules,
detecting missing sections, placeholder text, fabricated citations, and compliance gaps.

Usage:
    python filing_readiness_scorecard.py [filing_dir] [--all] [--json] [--verbose]
    
Examples:
    python filing_readiness_scorecard.py PKG_F9_COA_BRIEF_ON_APPEAL
    python filing_readiness_scorecard.py --all
    python filing_readiness_scorecard.py --all --json > readiness_report.json

Author: LitigationOS / Copilot Agent Fleet
"""

import sys
import os
import re
import json
import glob
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional
from datetime import datetime

# UTF-8 output safety
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

FILING_PACKAGE_DIR = r"C:\Users\andre\Desktop\LITIGATION_FILING_PACKAGE"

# Known fabricated citations/canons to flag
FABRICATED_ITEMS = [
    ("Canon 4", "Canon 4 was identified as fabricated — MI Judicial Canons have no Canon 4 for delegation"),
    ("SBN P35878", "Fabricated bar number"),
    ("91% alienation", "Fabricated pseudo-scientific score"),
    ("CPS records [VERIFY — check actual CPS records for count]", "Unverified inflated count"),
    ("Emily Ann", "Wrong middle name — Emily A. Watson"),
    ("Emily M.", "Wrong middle initial — Emily A. Watson"),
    ("Amy McNeill", "Wrong first name — Hon. Jenny L. McNeill"),
    ("Tiffany", "Wrong name for Emily Watson"),
]

# Known adverse/removed citations
ADVERSE_CITATIONS = [
    ("Pittman v Cuyahoga", "Adverse — limits §1983 family law claims"),
    ("Monell v Department", "Irrelevant — municipal liability, no municipality sued"),
    ("Crawford v Washington", "Criminal case — inapplicable to civil"),
    ("Tower v Glover", "About public defenders — inapplicable"),
    ("Mapp v Ohio", "Criminal exclusionary rule — not applicable in civil"),
    ("Wong Sun", "Criminal fruit of poisonous tree — civil analog needed"),
    ("Craig v Boren", "Gender discrimination — not the issue here"),
    ("US v Virginia", "VMI case — not applicable"),
    ("Hazel v Raines", "Removed — adverse or inapplicable"),
]

# Placeholder patterns
PLACEHOLDER_PATTERNS = [
    r'\[ANDREW[_\s]REQUIRED\]',
    r'\[INSERT[^\]]*\]',
    r'\[ATTACH[^\]]*\]',
    r'\[TO BE DETERMINED[^\]]*\]',
    r'\[ASSIGNED JUDGE\]',
    r'\[UNKNOWN[^\]]*\]',
    r'\[VERIFY[^\]]*\]',
    r'\[CITE[^\]]*\]',
    r'\[DATE[^\]]*\]',
    r'_________________',  # Blank date lines
    r'\[TBD\]',
    r'\[FILL[^\]]*\]',
]

# Court-specific required sections by filing type
FILING_REQUIREMENTS = {
    "F1": {
        "name": "Emergency TRO (Housing)",
        "court": "Circuit Court",
        "required_sections": ["PARTIES", "JURISDICTION", "LEGAL STANDARD", "PRAYER FOR RELIEF", "VERIFICATION"],
        "required_mcl": ["MCR 3.310", "MCL 125.2301", "MCL 600.2918"],
        "needs_affidavit": True,
        "needs_proposed_order": True,
        "needs_cert_of_service": True,
    },
    "F2": {
        "name": "Amended Complaint (Housing)",
        "court": "Circuit Court",
        "required_sections": ["PARTIES", "JURISDICTION", "GENERAL ALLEGATIONS", "PRAYER FOR RELIEF", "VERIFICATION", "JURY DEMAND"],
        "required_mcl": ["MCL 445.903", "MCL 554.139", "MCL 600.2919a", "MCL 125.2301"],
        "needs_affidavit": False,
        "needs_cert_of_service": True,
    },
    "F3": {
        "name": "Disqualification Motion (MCR 2.003)",
        "court": "Circuit Court",
        "required_sections": ["STATEMENT OF FACTS", "LEGAL STANDARD", "ARGUMENT", "RELIEF REQUESTED"],
        "required_mcl": ["MCR 2.003"],
        "needs_affidavit": True,
        "needs_cert_of_service": True,
    },
    "F4": {
        "name": "Federal §1983 Complaint",
        "court": "Federal (USDC WDMI)",
        "required_sections": ["PARTIES", "JURISDICTION", "STATEMENT OF FACTS", "COUNTS", "PRAYER FOR RELIEF"],
        "required_mcl": ["42 USC 1983", "42 USC 1985"],
        "needs_affidavit": False,
        "needs_cert_of_service": True,
        "needs_ifp": True,
    },
    "F5": {
        "name": "MSC Original Action",
        "court": "Michigan Supreme Court",
        "required_sections": ["QUESTIONS PRESENTED", "STATEMENT OF FACTS", "ARGUMENT", "RELIEF REQUESTED"],
        "required_mcl": ["Const 1963 Art 6"],
        "needs_affidavit": True,
        "needs_cert_of_service": True,
    },
    "F6": {
        "name": "JTC Complaint",
        "court": "Judicial Tenure Commission",
        "required_sections": ["COMPLAINANT", "RESPONDENT", "STATEMENT OF FACTS", "VIOLATIONS"],
        "required_mcl": ["MCR 9.104", "MCR 9.202"],
        "needs_affidavit": True,
        "needs_cert_of_service": False,
    },
    "F7": {
        "name": "Custody Modification Motion",
        "court": "Circuit Court",
        "required_sections": ["STATEMENT OF FACTS", "LEGAL STANDARD", "ARGUMENT", "RELIEF REQUESTED"],
        "required_mcl": ["MCL 722.23", "MCL 722.27"],
        "needs_affidavit": True,
        "needs_cert_of_service": True,
    },
    "F8": {
        "name": "PPO Termination/Modification",
        "court": "Circuit Court",
        "required_sections": ["STATEMENT OF FACTS", "LEGAL STANDARD", "ARGUMENT", "RELIEF REQUESTED"],
        "required_mcl": ["MCL 600.2950"],
        "needs_affidavit": True,
        "needs_cert_of_service": True,
    },
    "F9": {
        "name": "COA Brief on Appeal",
        "court": "Court of Appeals",
        "required_sections": ["STATEMENT OF JURISDICTION", "STATEMENT OF QUESTIONS", "STATEMENT OF FACTS", "ARGUMENT", "RELIEF REQUESTED"],
        "required_mcl": ["MCR 7.212"],
        "needs_affidavit": True,
        "needs_cert_of_service": True,
        "needs_cert_of_compliance": True,
        "needs_appendix": True,
        "word_limit": 16000,
    },
    "F10": {
        "name": "COA Emergency Motion",
        "court": "Court of Appeals",
        "required_sections": ["STATEMENT OF FACTS", "ARGUMENT", "RELIEF REQUESTED"],
        "required_mcl": ["MCR 7.211"],
        "needs_affidavit": True,
        "needs_cert_of_service": True,
    },
}


@dataclass
class Issue:
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    category: str
    message: str
    line: Optional[int] = None
    suggestion: Optional[str] = None


@dataclass
class FilingScore:
    filing_id: str
    name: str
    court: str
    total_score: float = 0.0
    max_score: float = 100.0
    grade: str = "F"
    ready_to_file: bool = False
    issues: list = field(default_factory=list)
    section_scores: dict = field(default_factory=dict)
    word_count: int = 0
    placeholder_count: int = 0
    fabrication_count: int = 0
    adverse_citation_count: int = 0
    has_affidavit: bool = False
    has_cert_of_service: bool = False
    has_exhibit_index: bool = False
    has_court_forms: bool = False
    has_caption: bool = False


def count_words(text: str) -> int:
    """Count words in text, excluding markdown formatting."""
    clean = re.sub(r'[#*_\-|>]', ' ', text)
    clean = re.sub(r'\s+', ' ', clean)
    return len(clean.split())


def check_placeholders(text: str, lines: list) -> list:
    """Find all placeholder patterns in filing text."""
    found = []
    for i, line in enumerate(lines, 1):
        for pattern in PLACEHOLDER_PATTERNS:
            matches = re.findall(pattern, line, re.IGNORECASE)
            for m in matches:
                found.append((i, m if isinstance(m, str) else m))
    return found


def check_fabrications(text: str, lines: list) -> list:
    """Check for known fabricated names, citations, statistics."""
    found = []
    for i, line in enumerate(lines, 1):
        for pattern, reason in FABRICATED_ITEMS:
            if pattern.lower() in line.lower():
                found.append((i, pattern, reason))
    return found


def check_adverse_citations(text: str, lines: list) -> list:
    """Check for known adverse/removed citations."""
    found = []
    for i, line in enumerate(lines, 1):
        for pattern, reason in ADVERSE_CITATIONS:
            if pattern.lower() in line.lower():
                found.append((i, pattern, reason))
    return found


def check_required_sections(text: str, filing_id: str) -> tuple:
    """Check if all required sections are present."""
    reqs = FILING_REQUIREMENTS.get(filing_id, {})
    required = reqs.get("required_sections", [])
    found = []
    missing = []
    for section in required:
        # Case-insensitive search for section headers
        pattern = re.compile(re.escape(section), re.IGNORECASE)
        if pattern.search(text):
            found.append(section)
        else:
            missing.append(section)
    return found, missing


def check_required_authorities(text: str, filing_id: str) -> tuple:
    """Check if key MCL/MCR citations are present."""
    reqs = FILING_REQUIREMENTS.get(filing_id, {})
    required = reqs.get("required_mcl", [])
    found = []
    missing = []
    for auth in required:
        if auth.lower().replace(" ", "") in text.lower().replace(" ", ""):
            found.append(auth)
        else:
            missing.append(auth)
    return found, missing


def check_party_accuracy(text: str) -> list:
    """Verify party names and details are correct."""
    issues = []
    # Check for wrong Emily name variants
    if re.search(r'Emily\s+Ann\b', text):
        issues.append("Wrong name: 'Emily Ann' should be 'Emily A.'")
    if re.search(r'Emily\s+M\.', text):
        issues.append("Wrong initial: 'Emily M.' should be 'Emily A.'")
    if re.search(r'Amy\s+McNeill', text, re.IGNORECASE):
        issues.append("Wrong name: 'Amy McNeill' should be 'Jenny L. McNeill'")
    # Check child name exposure
    child_full_name_patterns = [
        r'L\w+\s+D\w+\s+W\w+',  # Full name pattern
    ]
    for p in child_full_name_patterns:
        if re.search(p, text) and "L.D.W." in text:
            pass  # Initials are fine
    # Check Rusco title
    if re.search(r'Rusco.*(?:FOC|Friend of Court|clerk)', text, re.IGNORECASE):
        issues.append("Wrong title: Pamela Rusco is JUDICIAL SECRETARY, not FOC/clerk")
    # Check Berry attorney claim
    if re.search(r'Berry.*(?:Esq|attorney|counsel|P\d{5})', text, re.IGNORECASE):
        if not re.search(r'claims\s+attorney|non-attorney|no.*bar', text, re.IGNORECASE):
            issues.append("Ronald Berry has NO verified bar number — do not imply attorney status")
    return issues


def check_date_consistency(text: str) -> list:
    """Check for date inconsistencies."""
    issues = []
    # SC#5/6/7 should be 2025 not 2024
    if re.search(r'SC\s*#?\s*[567].*2024', text):
        issues.append("SC#5/6/7 happened in 2025, not 2024")
    # LDW birth year should be 2022
    if re.search(r'(?:born|birth|DOB).*2021', text, re.IGNORECASE):
        issues.append("L.D.W. born November 9, 2022 — NOT 2021")
    # Job count
    job_match = re.search(r'(?:lost|losing)\s+(?:two|2)\s+jobs', text, re.IGNORECASE)
    if job_match:
        issues.append("Should be FOUR jobs lost (Metal Arc, IndiGrow, USPS, Shape Corp), not two")
    return issues


def check_db_stat_references(text: str, lines: list) -> list:
    """Flag any hardcoded DB statistics that could be inflated."""
    found = []
    # Common inflated stat patterns
    stat_patterns = [
        (r'308[,.]?704\s*(?:evidence|quotes)', "Stale DB count — evidence_quotes was deduped to 36,891"),
        (r'1[,.]?127\s*(?:judicial|violation)', "May be current but verify with live query"),
        (r'13[,.]?016\s*(?:action)', "Verify with live DB query"),
        (r'24\s+ex\s*parte\s+orders', "EXACTLY 2 ex-parte orders, not 24 (24 = total orders of all types)"),
    ]
    for i, line in enumerate(lines, 1):
        for pattern, reason in stat_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                found.append((i, pattern, reason))
    return found


def score_filing(filing_dir: str) -> FilingScore:
    """Score a single filing package for court readiness."""
    pkg_name = os.path.basename(filing_dir)
    
    # Extract filing ID (F1-F10)
    fid_match = re.search(r'F(\d+)', pkg_name)
    if not fid_match:
        return FilingScore(filing_id="UNKNOWN", name=pkg_name, court="Unknown")
    
    filing_id = f"F{fid_match.group(1)}"
    reqs = FILING_REQUIREMENTS.get(filing_id, {})
    
    score = FilingScore(
        filing_id=filing_id,
        name=reqs.get("name", pkg_name),
        court=reqs.get("court", "Unknown"),
    )
    
    # Check which package files exist
    main_filing = os.path.join(filing_dir, "01_MAIN_FILING.md")
    affidavit = os.path.join(filing_dir, "02_AFFIDAVIT.md")
    exhibit_index = os.path.join(filing_dir, "03_EXHIBIT_INDEX.md")
    cert_of_service = os.path.join(filing_dir, "04_CERTIFICATE_OF_SERVICE.md")
    court_forms = os.path.join(filing_dir, "05_COURT_FORMS_CHECKLIST.md")
    caption = os.path.join(filing_dir, "06_CAPTION.md")
    
    score.has_affidavit = os.path.exists(affidavit)
    score.has_exhibit_index = os.path.exists(exhibit_index)
    score.has_cert_of_service = os.path.exists(cert_of_service)
    score.has_court_forms = os.path.exists(court_forms)
    score.has_caption = os.path.exists(caption)
    
    if not os.path.exists(main_filing):
        score.issues.append(Issue("CRITICAL", "missing_file", "Main filing document not found"))
        score.total_score = 0
        score.grade = "F"
        return score
    
    # Read main filing
    with open(main_filing, 'r', encoding='utf-8', errors='replace') as f:
        text = f.read()
    lines = text.split('\n')
    score.word_count = count_words(text)
    
    # === SCORING CATEGORIES (100 points total) ===
    points = 0.0
    max_points = 0.0
    
    # 1. Required Sections (25 points)
    max_points += 25
    found_sections, missing_sections = check_required_sections(text, filing_id)
    if found_sections:
        section_ratio = len(found_sections) / (len(found_sections) + len(missing_sections))
        points += 25 * section_ratio
    for s in missing_sections:
        score.issues.append(Issue("CRITICAL", "missing_section", f"Required section missing: {s}"))
    score.section_scores["required_sections"] = {
        "found": found_sections, "missing": missing_sections,
        "score": round(25 * len(found_sections) / max(1, len(found_sections) + len(missing_sections)), 1)
    }
    
    # 2. Required Authorities (15 points)
    max_points += 15
    found_auth, missing_auth = check_required_authorities(text, filing_id)
    if found_auth:
        auth_ratio = len(found_auth) / (len(found_auth) + len(missing_auth))
        points += 15 * auth_ratio
    for a in missing_auth:
        score.issues.append(Issue("HIGH", "missing_authority", f"Key authority not cited: {a}"))
    score.section_scores["authorities"] = {
        "found": found_auth, "missing": missing_auth,
        "score": round(15 * len(found_auth) / max(1, len(found_auth) + len(missing_auth)), 1)
    }
    
    # 3. No Placeholders (15 points)
    max_points += 15
    placeholders = check_placeholders(text, lines)
    score.placeholder_count = len(placeholders)
    if score.placeholder_count == 0:
        points += 15
    elif score.placeholder_count <= 3:
        points += 10
    elif score.placeholder_count <= 6:
        points += 5
    for line_num, placeholder in placeholders:
        score.issues.append(Issue("HIGH", "placeholder", f"Line {line_num}: Placeholder found: {placeholder}"))
    score.section_scores["placeholders"] = {"count": score.placeholder_count, "score": round(max(0, 15 - score.placeholder_count * 2.5), 1)}
    
    # 4. No Fabrications (15 points)
    max_points += 15
    fabrications = check_fabrications(text, lines)
    score.fabrication_count = len(fabrications)
    if score.fabrication_count == 0:
        points += 15
    for line_num, pattern, reason in fabrications:
        score.issues.append(Issue("CRITICAL", "fabrication", f"Line {line_num}: Fabricated item '{pattern}' — {reason}"))
    score.section_scores["fabrications"] = {"count": score.fabrication_count, "score": 15 if score.fabrication_count == 0 else 0}
    
    # 5. No Adverse Citations (10 points)
    max_points += 10
    adverse = check_adverse_citations(text, lines)
    score.adverse_citation_count = len(adverse)
    if score.adverse_citation_count == 0:
        points += 10
    for line_num, pattern, reason in adverse:
        score.issues.append(Issue("HIGH", "adverse_citation", f"Line {line_num}: Adverse citation '{pattern}' — {reason}"))
    score.section_scores["adverse_citations"] = {"count": score.adverse_citation_count, "score": 10 if score.adverse_citation_count == 0 else 0}
    
    # 6. Party Accuracy (5 points)
    max_points += 5
    party_issues = check_party_accuracy(text)
    if not party_issues:
        points += 5
    for issue in party_issues:
        score.issues.append(Issue("HIGH", "party_accuracy", issue))
    score.section_scores["party_accuracy"] = {"issues": party_issues, "score": 5 if not party_issues else 0}
    
    # 7. Date Consistency (5 points)
    max_points += 5
    date_issues = check_date_consistency(text)
    if not date_issues:
        points += 5
    for issue in date_issues:
        score.issues.append(Issue("MEDIUM", "date_consistency", issue))
    score.section_scores["date_consistency"] = {"issues": date_issues, "score": 5 if not date_issues else 0}
    
    # 8. DB Stat References (5 points)
    max_points += 5
    db_stats = check_db_stat_references(text, lines)
    if not db_stats:
        points += 5
    for line_num, pattern, reason in db_stats:
        score.issues.append(Issue("HIGH", "db_stat", f"Line {line_num}: Hardcoded DB stat — {reason}"))
    
    # 9. Package Completeness (5 points)
    max_points += 5
    pkg_score = 0
    pkg_items = []
    if score.has_caption:
        pkg_score += 1
        pkg_items.append("caption")
    if score.has_cert_of_service:
        pkg_score += 1
        pkg_items.append("cert_of_service")
    if score.has_exhibit_index:
        pkg_score += 1
        pkg_items.append("exhibit_index")
    if reqs.get("needs_affidavit") and score.has_affidavit:
        pkg_score += 1
        pkg_items.append("affidavit")
    elif not reqs.get("needs_affidavit"):
        pkg_score += 1
        pkg_items.append("affidavit_not_required")
    if score.has_court_forms:
        pkg_score += 1
        pkg_items.append("court_forms")
    points += (pkg_score / 5) * 5
    
    if reqs.get("needs_affidavit") and not score.has_affidavit:
        score.issues.append(Issue("CRITICAL", "missing_file", "Affidavit required but not found"))
    if reqs.get("needs_cert_of_service") and not score.has_cert_of_service:
        score.issues.append(Issue("HIGH", "missing_file", "Certificate of Service required but not found"))
    if reqs.get("needs_cert_of_compliance"):
        if not re.search(r'certificate of compliance', text, re.IGNORECASE):
            score.issues.append(Issue("CRITICAL", "missing_section", "Certificate of Compliance REQUIRED by MCR 7.212(D) — COA will REJECT without it"))
    if reqs.get("needs_appendix"):
        if not re.search(r'appendix', text, re.IGNORECASE):
            score.issues.append(Issue("HIGH", "missing_section", "Appendix required by MCR 7.212(G) for COA brief"))
    
    score.section_scores["package"] = {"items": pkg_items, "score": round((pkg_score / 5) * 5, 1)}
    
    # Word count check for COA brief
    if reqs.get("word_limit"):
        if score.word_count > reqs["word_limit"]:
            score.issues.append(Issue("HIGH", "word_count", f"Word count {score.word_count} exceeds {reqs['word_limit']} limit"))
    
    # Calculate final score
    score.total_score = round((points / max_points) * 100, 1) if max_points > 0 else 0
    
    # Grade assignment
    if score.total_score >= 95:
        score.grade = "A+"
    elif score.total_score >= 90:
        score.grade = "A"
    elif score.total_score >= 85:
        score.grade = "A-"
    elif score.total_score >= 80:
        score.grade = "B+"
    elif score.total_score >= 75:
        score.grade = "B"
    elif score.total_score >= 70:
        score.grade = "B-"
    elif score.total_score >= 65:
        score.grade = "C+"
    elif score.total_score >= 60:
        score.grade = "C"
    elif score.total_score >= 50:
        score.grade = "D"
    else:
        score.grade = "F"
    
    # Ready to file if score >= 85 AND no CRITICAL issues
    critical_count = sum(1 for i in score.issues if i.severity == "CRITICAL")
    score.ready_to_file = score.total_score >= 85 and critical_count == 0
    
    return score


def print_scorecard(score: FilingScore, verbose: bool = False):
    """Print a formatted scorecard for one filing."""
    status = "✅ READY" if score.ready_to_file else "❌ NOT READY"
    
    print(f"\n{'='*70}")
    print(f"  {score.filing_id}: {score.name}")
    print(f"  Court: {score.court}")
    print(f"  Score: {score.total_score}/100 ({score.grade})  |  {status}")
    print(f"  Words: {score.word_count:,}  |  Placeholders: {score.placeholder_count}  |  Fabrications: {score.fabrication_count}")
    print(f"{'='*70}")
    
    # Issue summary by severity
    critical = [i for i in score.issues if i.severity == "CRITICAL"]
    high = [i for i in score.issues if i.severity == "HIGH"]
    medium = [i for i in score.issues if i.severity == "MEDIUM"]
    low = [i for i in score.issues if i.severity == "LOW"]
    
    if critical:
        print(f"\n  🔴 CRITICAL ({len(critical)}):")
        for i in critical:
            print(f"     • {i.message}")
    if high:
        print(f"\n  🟠 HIGH ({len(high)}):")
        for i in high:
            print(f"     • {i.message}")
    if verbose:
        if medium:
            print(f"\n  🟡 MEDIUM ({len(medium)}):")
            for i in medium:
                print(f"     • {i.message}")
        if low:
            print(f"\n  🔵 LOW ({len(low)}):")
            for i in low:
                print(f"     • {i.message}")
    else:
        if medium or low:
            print(f"\n  🟡 MEDIUM: {len(medium)}  |  🔵 LOW: {len(low)}  (use --verbose to see)")
    
    # Package completeness
    pkg = []
    if score.has_caption: pkg.append("✅ Caption")
    else: pkg.append("❌ Caption")
    if score.has_affidavit: pkg.append("✅ Affidavit")
    else: pkg.append("❌ Affidavit")
    if score.has_exhibit_index: pkg.append("✅ Exhibits")
    else: pkg.append("❌ Exhibits")
    if score.has_cert_of_service: pkg.append("✅ Service")
    else: pkg.append("❌ Service")
    if score.has_court_forms: pkg.append("✅ Forms")
    else: pkg.append("❌ Forms")
    
    print(f"\n  Package: {' | '.join(pkg)}")


def main():
    args = sys.argv[1:]
    output_json = "--json" in args
    verbose = "--verbose" in args or "-v" in args
    scan_all = "--all" in args
    
    # Clean flags from args
    target_dirs = [a for a in args if not a.startswith("--") and not a.startswith("-")]
    
    if scan_all:
        # Scan all F1-F10 packages
        pattern = os.path.join(FILING_PACKAGE_DIR, "PKG_F*")
        target_dirs = sorted(glob.glob(pattern))
    elif target_dirs:
        # Resolve relative to filing package dir
        resolved = []
        for d in target_dirs:
            if os.path.isabs(d):
                resolved.append(d)
            elif os.path.exists(os.path.join(FILING_PACKAGE_DIR, d)):
                resolved.append(os.path.join(FILING_PACKAGE_DIR, d))
            else:
                # Try glob match
                matches = glob.glob(os.path.join(FILING_PACKAGE_DIR, f"*{d}*"))
                resolved.extend(matches)
        target_dirs = resolved
    else:
        print("Usage: python filing_readiness_scorecard.py [--all] [filing_dir] [--json] [--verbose]")
        print("\nExamples:")
        print("  python filing_readiness_scorecard.py --all")
        print("  python filing_readiness_scorecard.py PKG_F9_COA_BRIEF_ON_APPEAL")
        print("  python filing_readiness_scorecard.py F9")
        return
    
    scores = []
    for d in target_dirs:
        if os.path.isdir(d):
            scores.append(score_filing(d))
    
    if output_json:
        # JSON output
        output = []
        for s in scores:
            obj = asdict(s)
            # Convert Issue objects
            obj["issues"] = [asdict(i) for i in s.issues]
            output.append(obj)
        print(json.dumps(output, indent=2, default=str))
    else:
        # Console output
        print("\n" + "█" * 70)
        print("  FILING READINESS SCORECARD — LitigationOS")
        print(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("█" * 70)
        
        for s in scores:
            print_scorecard(s, verbose)
        
        # Summary
        print(f"\n{'='*70}")
        print("  SUMMARY")
        print(f"{'='*70}")
        ready = sum(1 for s in scores if s.ready_to_file)
        total = len(scores)
        avg_score = sum(s.total_score for s in scores) / total if total else 0
        total_issues = sum(len(s.issues) for s in scores)
        total_critical = sum(sum(1 for i in s.issues if i.severity == "CRITICAL") for s in scores)
        
        print(f"  Ready to file: {ready}/{total}")
        print(f"  Average score: {avg_score:.1f}/100")
        print(f"  Total issues: {total_issues} ({total_critical} CRITICAL)")
        
        # Filing order recommendation
        print(f"\n  📋 RECOMMENDED FILING ORDER (by score):")
        for s in sorted(scores, key=lambda x: x.total_score, reverse=True):
            emoji = "✅" if s.ready_to_file else "❌"
            print(f"     {emoji} {s.filing_id} ({s.grade}, {s.total_score}): {s.name}")
        
        print(f"\n{'='*70}")


if __name__ == "__main__":
    main()
