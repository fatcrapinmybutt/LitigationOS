#!/usr/bin/env python3
"""
proofread_filings.py — LitigationOS Court Filing Proofreader
Scans all .md/.txt files in 04_COURT_FILINGS, checks for required components,
validates citations against auth_rules, fixes files in-place, and generates a report.
"""

import os
import re
import sqlite3
from datetime import datetime
from pathlib import Path

# ── Configuration ──────────────────────────────────────────────────────
BASE_DIR = Path(r"C:\Users\andre\LitigationOS\04_COURT_FILINGS")
DB_PATH = Path(r"C:\Users\andre\litigation_context.db")
REPORT_PATH = Path(r"C:\Users\andre\LitigationOS\06_ANALYSIS\proofreading_report.md")

CASE_NUMBERS = {
    "custody": "2024-001507-DC",
    "ppo": "2023-5907-PP",
    "coa": "COA 366810",
}

# Keywords in filename or content that indicate actual court filings
FILING_KEYWORDS = [
    "motion", "brief", "affidavit", "petition", "complaint", "response",
    "application", "order", "memorandum", "reply", "objection",
    "show.?cause", "leave.?to.?appeal", "writ", "mandamus",
    "consolidat", "sanction", "contempt", "discovery", "reconsideration",
    "custody", "disqualif", "terminate", "venue", "supervised",
    "support.?modification", "default", "uccjea", "in.?forma.?pauperis",
    "impeachment", "alienation.?brief", "1983.?complaint",
    "superintending.?control", "misconduct.?brief", "grievance",
    "civil.?complaint", "criminal.?referral", "bar.?complaint",
    "foia.?request", "immediate.?consideration",
    "docketing.?statement", "cover.?sheet",
    "table.?of.?authorities",
    "proposed.?order",
    "appendix.?record",
    "affidavit.?of.?service",
]

# Files/patterns to SKIP — never treat these as filings
SKIP_PATTERNS = [
    r"readme", r"manifest", r"checklist", r"narrative", r"evidence.?mining",
    r"compliance.?audit", r"proofread.?log", r"structured.?data",
    r"inventory", r"tracker", r"sequence", r"strategy.?memo",
    r"instructions", r"exhibit.?index", r"exhibit.?authentication",
    r"proof.?of.?service.?template", r"start.?here", r"index\.md$",
    r"mission.?complete", r"quick.?start", r"package.?summary",
    r"qa.?checklist", r"qa.?comprehensive", r"qa.?mission",
    r"binder.?assembly", r"digital.?evidence", r"exhibit.?checklist",
    r"exhibit.?production", r"filing.?status.?report",
    r"master.?exhibit.?index", r"complete.?document.?inventory",
    r"master.?filing.?sequence", r"deadline.?tracker",
    r"filing.?bundle.?checklist", r"research.?findings",
    r"litigation.?strategy", r"final.?filing.?instructions",
    r"_process_artifacts", r"user.?narrative",
    r"filing.?instructions", r"exhibit.?list\.md",
    r"urgent.?filing.?deadline", r"updated.?filing.?manifest",
    r"filing.?manifest", r"companion.?filings",
    r"master.?exhibit", r"exhibit.?authentication.?templates",
    r"proof.?of.?service.?template",
]

PLACEHOLDER_PATTERNS = [
    r"\[PLACEHOLDER\]",
    r"\[TODO\]",
    r"\[INSERT[^\]]*\]",
    r"\bTBD\b",
    r"\bXXX\b",
    r"\[ADDRESS PLACEHOLDER\]",
    r"\[ADDRESS\]",
    r"\[CITY,?\s*STATE\s*ZIP\]",
    r"\[PHONE\]",
    r"\[EMAIL\]",
    r"\[DATE\]",
    r"\[####\]",
    r"\[TO BE (?:COMPLETED|ASSIGNED|DETERMINED)[^\]]*\]",
]

# ── Caption templates ──────────────────────────────────────────────────

CAPTION_14TH_CUSTODY = """STATE OF MICHIGAN
IN THE 14TH JUDICIAL CIRCUIT COURT FOR THE COUNTY OF MUSKEGON

ANDREW PIGORS,
    Plaintiff,                          Case No. 2024-001507-DC

v.                                      Hon. Jenny L. McNeill

HALEY WATSON,
    Defendant.
________________________________/
"""

CAPTION_14TH_PPO = """STATE OF MICHIGAN
IN THE 14TH JUDICIAL CIRCUIT COURT FOR THE COUNTY OF MUSKEGON

ANDREW PIGORS,
    Petitioner,                         Case No. 2023-5907-PP

v.                                      Hon. Jenny L. McNeill

HALEY WATSON,
    Respondent.
________________________________/
"""

CAPTION_COA = """STATE OF MICHIGAN
IN THE COURT OF APPEALS

ANDREW PIGORS,
    Plaintiff-Appellant,                Case No. COA 366810

v.                                      Hon. Jenny L. McNeill

HALEY WATSON,
    Defendant-Appellee.
________________________________/
"""

SIGNATURE_BLOCK = """
Respectfully submitted,

_______________________________
Andrew Pigors, Pro Se
1977 Whitehall Rd
Laketon Township, MI 49445
(231) 903-5690
Date: _______________
"""

CERT_OF_SERVICE_TEMPLATE = """
CERTIFICATE OF SERVICE

I certify that on _________________, I served a copy of this {doc_type} on all parties
by first-class mail, postage prepaid, and/or electronic service to:

Jennifer Barnes
Barnes Law Firm, PLLC
880 Jefferson St., Ste. B
Muskegon, MI 49440

_______________________________
Andrew Pigors
"""


def load_auth_rules(db_path: Path) -> dict:
    """Load all rule_type + rule_number combos from auth_rules into a lookup set."""
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    cur.execute("SELECT rule_type, rule_number FROM auth_rules")
    rules = {}
    for rule_type, rule_number in cur.fetchall():
        key = f"{rule_type} {rule_number}"
        rules[key] = True
        # Also store normalized forms
        rules[f"{rule_type} {rule_number.lstrip('0')}"] = True
    conn.close()
    return rules


def is_filing(filepath: Path, content: str) -> bool:
    """Determine if a file is an actual court filing vs. admin/support document."""
    fname_lower = filepath.name.lower()
    rel_path_lower = str(filepath).lower()

    # Check skip patterns first
    for pat in SKIP_PATTERNS:
        if re.search(pat, fname_lower, re.IGNORECASE):
            return False
        if re.search(pat, rel_path_lower, re.IGNORECASE):
            return False

    # Check if the filename or first 2000 chars of content match filing keywords
    content_head = content[:2000].lower()
    for kw in FILING_KEYWORDS:
        if re.search(kw, fname_lower, re.IGNORECASE):
            return True
        if re.search(kw, content_head, re.IGNORECASE):
            return True

    # Additional heuristic: if it starts with STATE OF MICHIGAN, it's a filing
    stripped = content.strip()
    if stripped.startswith("STATE OF MICHIGAN") or stripped.startswith("# STATE OF MICHIGAN"):
        return True

    return False


def detect_case_type(filepath: Path, content: str) -> str:
    """Determine which case lane this filing belongs to."""
    fname = filepath.name.lower()
    rel_path = str(filepath).lower()
    content_upper = content[:3000].upper()

    # COA indicators
    if "coa" in fname or "02_coa" in rel_path or "court of appeals" in rel_path:
        return "coa"
    if "COA 366810" in content_upper or "366810" in content_upper:
        return "coa"
    if "COURT OF APPEALS" in content_upper or "LEAVE TO APPEAL" in content_upper:
        return "coa"
    if "DOCKETING" in content_upper and "APPEAL" in content_upper:
        return "coa"
    if "MEEK3" in fname:
        return "coa"

    # PPO indicators
    if "ppo" in fname or "2023-5907" in content_upper or "2023.5907" in content_upper:
        return "ppo"
    if "TERMINATE_PPO" in fname.upper() or "TERMINATE PPO" in content_upper:
        return "ppo"
    if "PERSONAL PROTECTION" in content_upper:
        return "ppo"
    if "MEEK2" in fname:
        return "ppo"

    # JTC / MSC / USDC — skip caption insertion for these (different courts)
    if "jtc" in fname or "03_jtc" in rel_path or "MEEK4" in fname:
        return "jtc"
    if "msc" in fname or "04_msc" in rel_path:
        return "msc"
    if "usdc" in fname or "05_usdc" in rel_path or "federal" in fname or "MEEK5" in fname:
        return "usdc"
    if "1983" in fname:
        return "usdc"

    # Default to custody
    return "custody"


def has_caption(content: str) -> bool:
    """Check if the filing already has a Michigan-style caption."""
    upper = content[:1500].upper()
    has_state = "STATE OF MICHIGAN" in upper or "MICHIGAN" in upper[:200]
    has_case_no = bool(re.search(r"CASE\s*NO", upper)) or bool(re.search(
        r"2024-001507|2023-5907|366810", upper
    ))
    has_parties = "PIGORS" in upper and ("WATSON" in upper or "V." in upper or "VS" in upper)
    return has_state and (has_case_no or has_parties)


def has_signature_block(content: str) -> bool:
    """Check if filing has a signature block at the end."""
    tail = content[-2000:].lower()
    patterns = [
        r"respectfully submitted",
        r"_+\s*\n\s*andrew",
        r"pro\s*se",
        r"signature",
        r"dated:?\s",
        r"certification",  # JTC/docketing forms
    ]
    matches = sum(1 for p in patterns if re.search(p, tail))
    return matches >= 2


def has_certificate_of_service(content: str) -> bool:
    """Check if filing has a certificate of service."""
    lower = content.lower()
    return bool(re.search(r"certificate\s+of\s+service", lower))


def extract_citations(content: str) -> list:
    """Extract all MCR, MCL, MRE citations from content."""
    citations = []
    # MCR patterns: MCR 2.119, MCR 7.205(B), etc.
    for m in re.finditer(r"\bMCR\s+(\d+\.\d+[a-zA-Z]?)", content):
        citations.append(("MCR", m.group(1)))
    # MCL patterns: MCL 722.23, MCL 600.2950, etc.
    for m in re.finditer(r"\bMCL\s+(\d+\.\d+[a-zA-Z]?)", content):
        citations.append(("MCL", m.group(1)))
    # MRE patterns: MRE 801, MRE 403, etc.
    for m in re.finditer(r"\bMRE\s+(\d+)", content):
        citations.append(("MRE", m.group(1)))
    return list(set(citations))


def find_placeholders(content: str) -> list:
    """Find all placeholder patterns in content."""
    found = []
    for pat in PLACEHOLDER_PATTERNS:
        for m in re.finditer(pat, content, re.IGNORECASE):
            found.append(m.group(0))
    return found


def check_formatting(content: str) -> list:
    """Check for formatting issues."""
    issues = []
    lines = content.split("\n")

    # Check heading hierarchy — look for ## without prior #
    has_h1 = any(re.match(r"^#\s+[^#]", line) for line in lines)
    has_h2 = any(re.match(r"^##\s+[^#]", line) for line in lines)
    if has_h2 and not has_h1:
        issues.append("Missing H1 heading — document starts with H2")

    # Check for very long paragraphs (>500 chars without break) — potential formatting issue
    for i, line in enumerate(lines):
        if len(line.strip()) > 600 and not line.strip().startswith("|"):
            issues.append(f"Line {i+1}: Very long line ({len(line.strip())} chars) — may need line breaks")
            break  # Only report first instance

    return issues


def get_caption_for_case(case_type: str) -> str:
    """Return the appropriate caption template."""
    if case_type == "coa":
        return CAPTION_COA
    elif case_type == "ppo":
        return CAPTION_14TH_PPO
    else:
        return CAPTION_14TH_CUSTODY


def get_doc_type_from_filename(filepath: Path) -> str:
    """Infer document type from filename for certificate of service."""
    fname = filepath.stem.lower()
    if "motion" in fname:
        return "Motion"
    if "brief" in fname:
        return "Brief"
    if "affidavit" in fname:
        return "Affidavit"
    if "petition" in fname:
        return "Petition"
    if "complaint" in fname:
        return "Complaint"
    if "application" in fname:
        return "Application"
    if "response" in fname:
        return "Response"
    if "grievance" in fname:
        return "Grievance"
    if "referral" in fname:
        return "Referral Packet"
    return "Document"


def score_filing(issues: dict) -> int:
    """Score a filing 0-100 based on issues found."""
    score = 100
    if not issues["has_caption"]:
        score -= 20
    if not issues["has_signature"]:
        score -= 15
    if not issues["has_cert_service"]:
        score -= 15
    # Deduct for placeholders
    n_placeholders = len(issues["placeholders"])
    score -= min(n_placeholders * 3, 20)
    # Deduct for bad citations
    n_bad_cites = len(issues["bad_citations"])
    score -= min(n_bad_cites * 5, 15)
    # Deduct for formatting
    n_fmt = len(issues["formatting"])
    score -= min(n_fmt * 3, 10)
    return max(score, 0)


def needs_cert_of_service(filepath: Path, content: str) -> bool:
    """Determine if this filing type requires a certificate of service."""
    fname = filepath.name.lower()
    # Motions and briefs always need cert of service
    needs_it = any(kw in fname for kw in [
        "motion", "brief", "petition", "complaint", "application",
        "response", "reply", "objection", "memorandum",
    ])
    # Content-based check
    content_head = content[:2000].lower()
    if any(kw in content_head for kw in [
        "motion to", "brief in support", "petition for", "complaint",
        "application for", "response to", "reply to",
    ]):
        needs_it = True
    return needs_it


def process_filing(filepath: Path, auth_rules: dict) -> dict:
    """Process a single filing: check, score, and fix."""
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        original_content = f.read()

    content = original_content
    case_type = detect_case_type(filepath, content)
    fixes_applied = []
    issues = {
        "has_caption": has_caption(content),
        "has_signature": has_signature_block(content),
        "has_cert_service": has_certificate_of_service(content),
        "placeholders": find_placeholders(content),
        "bad_citations": [],
        "formatting": check_formatting(content),
        "case_type": case_type,
    }

    # Check citations
    citations = extract_citations(content)
    for rule_type, rule_num in citations:
        key = f"{rule_type} {rule_num}"
        if key not in auth_rules:
            issues["bad_citations"].append(key)

    # Calculate pre-fix score
    pre_score = score_filing(issues)

    # ── Apply Fixes ────────────────────────────────────────────────────
    # Only fix caption/signature/cert for supported case types
    fixable_types = {"custody", "ppo", "coa"}

    # Fix 1: Insert caption if missing
    if not issues["has_caption"] and case_type in fixable_types:
        caption = get_caption_for_case(case_type)
        # Prepend caption
        content = caption + "\n" + content
        issues["has_caption"] = True
        fixes_applied.append("Inserted Michigan caption")

    # Fix 2: Append signature block if missing
    if not issues["has_signature"] and case_type in fixable_types:
        content = content.rstrip() + "\n\n" + SIGNATURE_BLOCK.strip() + "\n"
        issues["has_signature"] = True
        fixes_applied.append("Appended signature block")

    # Fix 3: Append certificate of service if missing and needed
    if not issues["has_cert_service"] and needs_cert_of_service(filepath, original_content):
        doc_type = get_doc_type_from_filename(filepath)
        cert = CERT_OF_SERVICE_TEMPLATE.format(doc_type=doc_type)
        content = content.rstrip() + "\n\n" + cert.strip() + "\n"
        issues["has_cert_service"] = True
        fixes_applied.append("Appended certificate of service")

    # Calculate post-fix score
    post_issues = dict(issues)
    post_score = score_filing(post_issues)

    # Write back if changed
    if content != original_content:
        with open(filepath, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)

    return {
        "filepath": filepath,
        "case_type": case_type,
        "pre_score": pre_score,
        "post_score": post_score,
        "issues": issues,
        "fixes": fixes_applied,
        "citations_found": len(citations),
        "bad_citations": issues["bad_citations"],
        "placeholders": issues["placeholders"],
        "formatting_issues": issues["formatting"],
    }


def generate_report(results: list, skipped: list, report_path: Path):
    """Generate the proofreading report."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total_filings = len(results)
    total_fixes = sum(len(r["fixes"]) for r in results)
    avg_pre = sum(r["pre_score"] for r in results) / max(total_filings, 1)
    avg_post = sum(r["post_score"] for r in results) / max(total_filings, 1)

    lines = []
    lines.append("# PROOFREADING REPORT — PIGORS v. WATSON")
    lines.append(f"**Generated:** {now}")
    lines.append(f"**Script:** `00_SYSTEM/analysis/proofread_filings.py`")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## EXECUTIVE SUMMARY")
    lines.append("")
    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Total filings scanned | {total_filings} |")
    lines.append(f"| Files skipped (non-filings) | {len(skipped)} |")
    lines.append(f"| Average score BEFORE fixes | {avg_pre:.1f}/100 |")
    lines.append(f"| Average score AFTER fixes | {avg_post:.1f}/100 |")
    lines.append(f"| Total fixes applied | {total_fixes} |")

    # Count issue types
    missing_captions = sum(1 for r in results if "Inserted Michigan caption" in r["fixes"])
    missing_sigs = sum(1 for r in results if "Appended signature block" in r["fixes"])
    missing_certs = sum(1 for r in results if "Appended certificate of service" in r["fixes"])
    total_placeholders = sum(len(r["placeholders"]) for r in results)
    total_bad_cites = sum(len(r["bad_citations"]) for r in results)

    lines.append("")
    lines.append("### Fix Breakdown")
    lines.append("")
    lines.append(f"| Fix Type | Count |")
    lines.append(f"|----------|-------|")
    lines.append(f"| Captions inserted | {missing_captions} |")
    lines.append(f"| Signature blocks appended | {missing_sigs} |")
    lines.append(f"| Certificates of service appended | {missing_certs} |")
    lines.append(f"| Placeholders found (manual fix needed) | {total_placeholders} |")
    lines.append(f"| Unverified citations (manual review) | {total_bad_cites} |")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## FILING-BY-FILING RESULTS")
    lines.append("")

    # Sort by score (lowest first — most issues first)
    sorted_results = sorted(results, key=lambda r: r["post_score"])

    for r in sorted_results:
        rel = os.path.relpath(r["filepath"], BASE_DIR.parent)
        emoji = "✅" if r["post_score"] >= 80 else "⚠️" if r["post_score"] >= 50 else "❌"
        lines.append(f"### {emoji} `{rel}`")
        lines.append("")
        lines.append(f"- **Case type:** {r['case_type'].upper()}")
        lines.append(f"- **Score:** {r['pre_score']} → {r['post_score']}")
        lines.append(f"- **Citations found:** {r['citations_found']}")

        if r["fixes"]:
            lines.append(f"- **Fixes applied:**")
            for fix in r["fixes"]:
                lines.append(f"  - ✏️ {fix}")

        if r["bad_citations"]:
            lines.append(f"- **Unverified citations:** {', '.join(r['bad_citations'])}")

        if r["placeholders"]:
            unique_ph = list(set(r["placeholders"]))[:10]
            lines.append(f"- **Placeholders found:** {', '.join(unique_ph)}")

        if r["formatting_issues"]:
            for fi in r["formatting_issues"]:
                lines.append(f"- **Formatting:** {fi}")

        lines.append("")

    if skipped:
        lines.append("---")
        lines.append("")
        lines.append("## SKIPPED FILES (Non-Filings)")
        lines.append("")
        for s in sorted(skipped):
            rel = os.path.relpath(s, BASE_DIR.parent)
            lines.append(f"- `{rel}`")
        lines.append("")

    # Write report
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))
    print(f"\n✅ Report written to: {report_path}")


def main():
    print("=" * 70)
    print("  LitigationOS — Court Filing Proofreader")
    print("=" * 70)
    print()

    # Load auth rules
    print(f"Loading auth_rules from {DB_PATH}...")
    auth_rules = load_auth_rules(DB_PATH)
    print(f"  Loaded {len(auth_rules)} rule entries")

    # Scan files
    print(f"\nScanning {BASE_DIR} for .md and .txt files...")
    all_files = []
    for ext in ("*.md", "*.txt"):
        all_files.extend(BASE_DIR.rglob(ext))
    all_files = sorted(set(all_files))
    print(f"  Found {len(all_files)} files")

    results = []
    skipped = []

    for filepath in all_files:
        try:
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception as e:
            print(f"  ⚠️ Error reading {filepath}: {e}")
            skipped.append(filepath)
            continue

        if not content.strip():
            skipped.append(filepath)
            continue

        if not is_filing(filepath, content):
            skipped.append(filepath)
            continue

        rel = os.path.relpath(filepath, BASE_DIR.parent)
        print(f"  📄 Processing: {rel}")
        result = process_filing(filepath, auth_rules)
        results.append(result)

        fix_str = f" | Fixes: {', '.join(result['fixes'])}" if result["fixes"] else ""
        print(f"     Score: {result['pre_score']} → {result['post_score']}{fix_str}")

    # Generate report
    print(f"\n{'=' * 70}")
    print(f"  Generating report...")
    generate_report(results, skipped, REPORT_PATH)

    # Summary
    total_fixes = sum(len(r["fixes"]) for r in results)
    avg_pre = sum(r["pre_score"] for r in results) / max(len(results), 1)
    avg_post = sum(r["post_score"] for r in results) / max(len(results), 1)
    print(f"\n  📊 Total filings processed: {len(results)}")
    print(f"  📊 Files skipped (non-filings): {len(skipped)}")
    print(f"  📊 Average score: {avg_pre:.1f} → {avg_post:.1f}")
    print(f"  📊 Total fixes applied: {total_fixes}")
    print(f"\n{'=' * 70}")


if __name__ == "__main__":
    main()
