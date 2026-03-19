#!/usr/bin/env python3
"""
MBP LitigationOS -- Appellate Document Validator Skill
=======================================================
Validates ANY Michigan appellate document (COA brief, MSC application,
MSC emergency motion) against Michigan Court Rules requirements BEFORE
filing.  Prevents clerk rejections by checking every MCR requirement.

Supported document types:
  - coa_brief      → MCR 7.212 (16 checks)
  - msc_complaint  → MCR 7.306 (9 checks)
  - msc_emergency  → MCR 7.305 (3 checks + MCR 7.306 overlap)

Usage:
    from skills.appellate_validator import AppellateValidator
    v = AppellateValidator()
    result = v.validate_coa_brief(text)
    print(result.overall_score, result.failed_checks)
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(
    0,
    str(
        Path(__file__).resolve().parent.parent
        if "skills" in str(Path(__file__))
        else Path(__file__).resolve().parent
    ),
)
try:
    from cycle_method import cycle_json, cycle_print
except ImportError:
    cycle_json = lambda obj, **kw: print(json.dumps(obj, default=str))
    cycle_print = print

DB_PATH = os.environ.get(
    "LITIGATION_DB_PATH",
    r"C:\Users\andre\LitigationOS\litigation_context.db",
)


# ── Data Classes ─────────────────────────────────────────────────────────────

@dataclass
class CheckResult:
    """Result of a single compliance check."""
    requirement: str
    mcr_citation: str
    passed: bool
    severity: str  # "critical", "major", "minor"
    message: str
    suggestion: str = ""


@dataclass
class ValidationResult:
    """Full validation result for a document."""
    document_type: str
    overall_score: int = 100
    passed_checks: List[CheckResult] = field(default_factory=list)
    failed_checks: List[CheckResult] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    mcr_violations: List[str] = field(default_factory=list)
    word_count: int = 0
    page_estimate: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "document_type": self.document_type,
            "overall_score": self.overall_score,
            "passed_checks": [
                {"requirement": c.requirement, "mcr": c.mcr_citation,
                 "severity": c.severity, "message": c.message}
                for c in self.passed_checks
            ],
            "failed_checks": [
                {"requirement": c.requirement, "mcr": c.mcr_citation,
                 "severity": c.severity, "message": c.message,
                 "suggestion": c.suggestion}
                for c in self.failed_checks
            ],
            "warnings": self.warnings,
            "suggestions": self.suggestions,
            "mcr_violations": self.mcr_violations,
            "word_count": self.word_count,
            "page_estimate": self.page_estimate,
            "total_checks": len(self.passed_checks) + len(self.failed_checks),
            "pass_rate": (
                round(len(self.passed_checks) /
                      max(1, len(self.passed_checks) + len(self.failed_checks)) * 100, 1)
            ),
        }


# ── Severity weights for scoring ─────────────────────────────────────────────
_SEVERITY_PENALTY = {"critical": 15, "major": 8, "minor": 3}


# ── Regex patterns ───────────────────────────────────────────────────────────
_SECTION_PATTERNS: Dict[str, re.Pattern] = {
    "table_of_contents": re.compile(
        r"TABLE\s+OF\s+CONTENTS", re.IGNORECASE
    ),
    "index_of_authorities": re.compile(
        r"(INDEX|TABLE)\s+OF\s+AUTHORITIES", re.IGNORECASE
    ),
    "jurisdiction": re.compile(
        r"STATEMENT\s+OF\s+JURISDICTION|JURISDICTIONAL\s+STATEMENT|"
        r"BASIS\s+(FOR|OF)\s+JURISDICTION",
        re.IGNORECASE,
    ),
    "questions_presented": re.compile(
        r"(STATEMENT\s+OF\s+)?(QUESTIONS?\s+PRESENTED|ISSUES?\s+PRESENTED)",
        re.IGNORECASE,
    ),
    "statement_of_facts": re.compile(
        r"STATEMENT\s+OF\s+(THE\s+)?FACTS|FACTUAL\s+BACKGROUND",
        re.IGNORECASE,
    ),
    "standard_of_review": re.compile(
        r"STANDARD\s+OF\s+REVIEW", re.IGNORECASE
    ),
    "argument": re.compile(
        r"^(?:I+V?|V?I{0,3})\.\s+ARGUMENT|^ARGUMENT\b",
        re.IGNORECASE | re.MULTILINE,
    ),
    "relief_requested": re.compile(
        r"RELIEF\s+REQUESTED|CONCLUSION\s+AND\s+RELIEF|PRAYER\s+FOR\s+RELIEF",
        re.IGNORECASE,
    ),
    "signature_block": re.compile(
        r"Respectfully\s+submitted|/s/|___+\s*\n.*(?:P\d{5}|Bar\s*(?:No|#|Number))",
        re.IGNORECASE,
    ),
    "certificate_of_compliance": re.compile(
        r"CERTIFICATE\s+OF\s+COMPLIANCE|WORD\s+COUNT\s+CERTIFICATION",
        re.IGNORECASE,
    ),
    "appendix": re.compile(
        r"APPENDIX|REGISTER\s+OF\s+ACTIONS", re.IGNORECASE
    ),
    "cover_page": re.compile(
        r"(?:STATE\s+OF\s+MICHIGAN|MICHIGAN\s+COURT\s+OF\s+APPEALS|"
        r"MICHIGAN\s+SUPREME\s+COURT).*(?:Plaintiff|Appellant|Appellee|Defendant)",
        re.IGNORECASE | re.DOTALL,
    ),
    "certificate_of_service": re.compile(
        r"CERTIFICATE\s+OF\s+SERVICE|PROOF\s+OF\s+SERVICE",
        re.IGNORECASE,
    ),
    "affidavit": re.compile(
        r"VERIFICATION|AFFIDAVIT|SWORN|UNDER\s+PENALTY\s+OF\s+PERJURY|"
        r"duly\s+sworn|being\s+first\s+duly\s+sworn",
        re.IGNORECASE,
    ),
    "brief_in_support": re.compile(
        r"BRIEF\s+IN\s+SUPPORT|SUPPORTING\s+BRIEF|MEMORANDUM\s+IN\s+SUPPORT",
        re.IGNORECASE,
    ),
    "proposed_order": re.compile(
        r"PROPOSED\s+ORDER|ORDER\s+(?:GRANTING|TO\s+SHOW\s+CAUSE)",
        re.IGNORECASE,
    ),
    "irreparable_harm": re.compile(
        r"irreparable\s+harm|immediate\s+(?:and\s+)?irreparable|"
        r"imminent\s+(?:harm|danger|injury)",
        re.IGNORECASE,
    ),
    "normal_course_inadequate": re.compile(
        r"normal\s+(?:course|process|procedure)\s+(?:of\s+)?(?:is\s+)?inadequate|"
        r"no\s+(?:adequate|other)\s+remedy|"
        r"extraordinary\s+(?:relief|circumstances?|writ)",
        re.IGNORECASE,
    ),
    "parties_notified": re.compile(
        r"(?:all\s+)?parties?\s+(?:have\s+been\s+|were\s+)?notified|"
        r"notice\s+(?:was\s+)?(?:given|served|provided)\s+to\s+(?:all\s+)?parties|"
        r"served\s+(?:upon|on)\s+(?:all\s+)?(?:opposing\s+)?(?:parties|counsel)",
        re.IGNORECASE,
    ),
    "normal_briefing_inadequate": re.compile(
        r"normal\s+briefing\s+(?:schedule\s+)?(?:is\s+)?inadequate|"
        r"expedited\s+(?:briefing|consideration|review)|"
        r"time\s+(?:is\s+)?(?:of\s+the\s+)?essence",
        re.IGNORECASE,
    ),
    "lower_court_record_ref": re.compile(
        r"\b(?:R\.\s*(?:at\s+)?\d+|Tr\s+(?:at\s+)?\d+|"
        r"(?:Lower\s+Court|LC|Trial\s+Court)\s+(?:Record|Rec)\.?|"
        r"(?:\d+[a-z]?\s+)?(?:at\s+)?\d+(?:a|b)?|"
        r"App(?:endix|x?)\.?\s*\d+)",
        re.IGNORECASE,
    ),
}

# Bar number pattern
_BAR_NUMBER_RE = re.compile(r"P\d{5,6}|Bar\s*(?:No|#|Number)[:\s]*\d{5,6}", re.IGNORECASE)

# Address pattern (basic: city, state ZIP)
_ADDRESS_RE = re.compile(
    r"\d+\s+\w+.*\n.*(?:MI|Michigan)\s+\d{5}", re.IGNORECASE
)

# Filing fee / fee waiver
_FEE_RE = re.compile(
    r"filing\s+fee|fee\s+waiver|in\s+forma\s+pauperis|IFP",
    re.IGNORECASE,
)


# ── Helper functions ─────────────────────────────────────────────────────────

def _count_words(text: str) -> int:
    """Count words, excluding headers/footers/page numbers."""
    cleaned = re.sub(r"^\s*\d+\s*$", "", text, flags=re.MULTILINE)
    cleaned = re.sub(r"-{3,}|={3,}|\*{3,}", "", cleaned)
    return len(cleaned.split())


def _estimate_pages(word_count: int) -> int:
    """Estimate page count from word count (≈250 words/page double-spaced)."""
    return max(1, (word_count + 249) // 250)


def _has_section(text: str, pattern_name: str) -> bool:
    """Check whether document contains a section matching the named pattern."""
    pat = _SECTION_PATTERNS.get(pattern_name)
    return bool(pat and pat.search(text))


def _has_page_references(text: str, section_pattern_name: str) -> bool:
    """Check if a section contains page number references (e.g., '... 12')."""
    pat = _SECTION_PATTERNS.get(section_pattern_name)
    if not pat:
        return False
    m = pat.search(text)
    if not m:
        return False
    # Grab ~3000 chars after the section header
    start = m.end()
    snippet = text[start:start + 3000]
    # Look for page-number patterns like "... 12" or "...... 12" or dotted leaders
    return bool(re.search(r"\.{2,}\s*\d+|\.\s+\d+$|\d+(?:,\s*\d+)+", snippet, re.MULTILINE))


def _get_db() -> Optional[sqlite3.Connection]:
    """Get read-only DB connection."""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA query_only=ON")
        conn.row_factory = sqlite3.Row
        return conn
    except Exception:
        return None


# ── Requirements Definitions ─────────────────────────────────────────────────

COA_BRIEF_REQUIREMENTS: List[Dict[str, str]] = [
    {"id": "toc", "name": "Table of Contents", "mcr": "MCR 7.212(B)(1)",
     "severity": "critical",
     "description": "Table of Contents with page references for each section."},
    {"id": "ioa", "name": "Index of Authorities", "mcr": "MCR 7.212(B)(2)",
     "severity": "critical",
     "description": "Alphabetical list of cases, statutes, rules cited with page references."},
    {"id": "jurisdiction", "name": "Statement of Jurisdiction", "mcr": "MCR 7.212(B)(3)",
     "severity": "critical",
     "description": "Basis for appellate jurisdiction must be stated."},
    {"id": "questions", "name": "Questions Presented", "mcr": "MCR 7.212(B)(4)",
     "severity": "critical",
     "description": "Each question on a separate page, short and concise."},
    {"id": "facts", "name": "Statement of Facts", "mcr": "MCR 7.212(B)(5)",
     "severity": "critical",
     "description": "Concise recitation with Lower Court Record references."},
    {"id": "standard_of_review", "name": "Standard of Review", "mcr": "MCR 7.212(B)(6)",
     "severity": "major",
     "description": "Standard of review stated for each issue."},
    {"id": "argument", "name": "Argument", "mcr": "MCR 7.212(B)(7)",
     "severity": "critical",
     "description": "Separate section for each issue with supporting authority."},
    {"id": "relief", "name": "Relief Requested", "mcr": "MCR 7.212(B)(8)",
     "severity": "critical",
     "description": "Specific relief sought must be stated."},
    {"id": "signature", "name": "Signature Block", "mcr": "MCR 7.212(B)(9)",
     "severity": "critical",
     "description": "Signature with name, address, and bar number (or pro se designation)."},
    {"id": "word_limit", "name": "Word/Page Limit", "mcr": "MCR 7.212(B)(10)",
     "severity": "critical",
     "description": "Appellant opening brief: 16,000 words or 50 pages maximum."},
    {"id": "cert_compliance", "name": "Certificate of Compliance", "mcr": "MCR 7.212(B)(11)",
     "severity": "major",
     "description": "Certificate stating word count and compliance with limits."},
    {"id": "appendix", "name": "Appendix", "mcr": "MCR 7.212(C)",
     "severity": "major",
     "description": "Must include register of actions, opinion/order appealed, relevant documents."},
    {"id": "font", "name": "Font Requirement", "mcr": "MCR 7.212(A)",
     "severity": "minor",
     "description": "Proportional 12pt minimum, or monospaced 10pt minimum."},
    {"id": "margins", "name": "Margins", "mcr": "MCR 7.212(A)",
     "severity": "minor",
     "description": "1-inch margins on all sides."},
    {"id": "spacing", "name": "Double Spacing", "mcr": "MCR 7.212(A)",
     "severity": "minor",
     "description": "Body text must be double-spaced."},
    {"id": "cover_page", "name": "Cover Page", "mcr": "MCR 7.212(A)",
     "severity": "major",
     "description": "Cover page with case caption, docket number, parties, and court information."},
]

MSC_COMPLAINT_REQUIREMENTS: List[Dict[str, str]] = [
    {"id": "jurisdiction_facts", "name": "Jurisdiction Facts",
     "mcr": "MCR 7.306(B)",
     "severity": "critical",
     "description": "Complaint states facts showing MSC jurisdiction."},
    {"id": "normal_course", "name": "Normal Course Inadequate",
     "mcr": "MCR 7.306(B)",
     "severity": "critical",
     "description": "States why relief through normal appellate process is inadequate."},
    {"id": "relief_specific", "name": "Specific Relief",
     "mcr": "MCR 7.306(B)",
     "severity": "critical",
     "description": "States relief sought with specificity."},
    {"id": "affidavit", "name": "Verified by Affidavit",
     "mcr": "MCR 7.306(B)(1)",
     "severity": "critical",
     "description": "Complaint must be verified by affidavit."},
    {"id": "brief_in_support", "name": "Brief in Support",
     "mcr": "MCR 7.306(B)(2)",
     "severity": "critical",
     "description": "Must include a brief in support of the complaint."},
    {"id": "copies", "name": "Required Copies",
     "mcr": "MCR 7.306(B)",
     "severity": "major",
     "description": "Original + 4 copies minimum (13 per MSC local practice)."},
    {"id": "certificate_of_service", "name": "Certificate of Service",
     "mcr": "MCR 7.306(B)",
     "severity": "critical",
     "description": "Certificate of Service on all parties."},
    {"id": "filing_fee", "name": "Filing Fee / Waiver",
     "mcr": "MCR 7.306(B)",
     "severity": "major",
     "description": "Filing fee paid or fee waiver (IFP) application included."},
    {"id": "proposed_order", "name": "Proposed Order",
     "mcr": "MCR 7.306(B)",
     "severity": "major",
     "description": "Proposed order should accompany the complaint."},
]

MSC_EMERGENCY_REQUIREMENTS: List[Dict[str, str]] = [
    {"id": "irreparable_harm", "name": "Irreparable Harm",
     "mcr": "MCR 7.305(F)",
     "severity": "critical",
     "description": "Must show immediate irreparable harm."},
    {"id": "parties_notified", "name": "All Parties Notified",
     "mcr": "MCR 7.305(F)",
     "severity": "critical",
     "description": "All parties notified or explanation why not."},
    {"id": "briefing_inadequate", "name": "Normal Briefing Inadequate",
     "mcr": "MCR 7.305(F)",
     "severity": "critical",
     "description": "Statement why normal briefing schedule is inadequate."},
]


# ── Validator Class ──────────────────────────────────────────────────────────

class AppellateValidator:
    """Validates Michigan appellate documents against MCR requirements.

    Supports COA briefs (MCR 7.212), MSC original actions (MCR 7.306),
    and MSC emergency applications (MCR 7.305).
    """

    WORD_LIMIT_COA = 16_000
    PAGE_LIMIT_COA = 50

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    # ── COA Brief — MCR 7.212 ────────────────────────────────────────

    def validate_coa_brief(
        self, document_text: str, appendix_text: Optional[str] = None
    ) -> ValidationResult:
        """Validate a COA brief against all 16 MCR 7.212 requirements.

        Args:
            document_text: Full text of the appellate brief.
            appendix_text: Optional separate appendix text (if filed separately).

        Returns:
            ValidationResult with per-requirement pass/fail, score, and suggestions.
        """
        result = ValidationResult(document_type="coa_brief")
        full_text = document_text + ("\n" + appendix_text if appendix_text else "")
        wc = _count_words(document_text)
        result.word_count = wc
        result.page_estimate = _estimate_pages(wc)

        checks: List[Tuple[str, str, str, bool, str, str]] = []
        # (requirement_name, mcr, severity, passed, message, suggestion)

        # 1. Table of Contents — MCR 7.212(B)(1)
        has_toc = _has_section(full_text, "table_of_contents")
        toc_pages = _has_page_references(full_text, "table_of_contents") if has_toc else False
        if has_toc and toc_pages:
            checks.append(("Table of Contents", "MCR 7.212(B)(1)", "critical",
                           True, "Table of Contents found with page references.", ""))
        elif has_toc:
            checks.append(("Table of Contents", "MCR 7.212(B)(1)", "critical",
                           False, "Table of Contents found but page references may be missing.",
                           "Add dotted-leader page references for each section heading."))
        else:
            checks.append(("Table of Contents", "MCR 7.212(B)(1)", "critical",
                           False, "No Table of Contents detected.",
                           "Add 'TABLE OF CONTENTS' section with page refs for every section."))

        # 2. Index of Authorities — MCR 7.212(B)(2)
        has_ioa = _has_section(full_text, "index_of_authorities")
        ioa_pages = _has_page_references(full_text, "index_of_authorities") if has_ioa else False
        if has_ioa and ioa_pages:
            checks.append(("Index of Authorities", "MCR 7.212(B)(2)", "critical",
                           True, "Index of Authorities found with page references.", ""))
        elif has_ioa:
            checks.append(("Index of Authorities", "MCR 7.212(B)(2)", "critical",
                           False, "Index of Authorities found but page references may be missing.",
                           "Add page numbers where each authority is cited."))
        else:
            checks.append(("Index of Authorities", "MCR 7.212(B)(2)", "critical",
                           False, "No Index of Authorities detected.",
                           "Use index_of_authorities.generate_index() to auto-generate one."))

        # 3. Statement of Jurisdiction — MCR 7.212(B)(3)
        has_jur = _has_section(full_text, "jurisdiction")
        if has_jur:
            checks.append(("Statement of Jurisdiction", "MCR 7.212(B)(3)", "critical",
                           True, "Statement of Jurisdiction found.", ""))
        else:
            checks.append(("Statement of Jurisdiction", "MCR 7.212(B)(3)", "critical",
                           False, "No Statement of Jurisdiction detected.",
                           "Add section citing MCR 7.203 or MCR 7.204 as basis for jurisdiction."))

        # 4. Questions Presented — MCR 7.212(B)(4)
        has_qp = _has_section(full_text, "questions_presented")
        if has_qp:
            checks.append(("Questions Presented", "MCR 7.212(B)(4)", "critical",
                           True, "Questions Presented section found.", ""))
        else:
            checks.append(("Questions Presented", "MCR 7.212(B)(4)", "critical",
                           False, "No Questions Presented section detected.",
                           "Add 'STATEMENT OF QUESTIONS PRESENTED' — each question on its own page."))

        # 5. Statement of Facts — MCR 7.212(B)(5)
        has_facts = _has_section(full_text, "statement_of_facts")
        has_record_refs = _has_section(full_text, "lower_court_record_ref")
        if has_facts and has_record_refs:
            checks.append(("Statement of Facts", "MCR 7.212(B)(5)", "critical",
                           True, "Statement of Facts found with record references.", ""))
        elif has_facts:
            checks.append(("Statement of Facts", "MCR 7.212(B)(5)", "critical",
                           False, "Statement of Facts found but Lower Court Record references missing.",
                           "Add record citations (e.g., 'R. at 45', 'Tr at 112') for each factual assertion."))
        else:
            checks.append(("Statement of Facts", "MCR 7.212(B)(5)", "critical",
                           False, "No Statement of Facts detected.",
                           "Add 'STATEMENT OF FACTS' with concise recitation and record page cites."))

        # 6. Standard of Review — MCR 7.212(B)(6)
        has_sor = _has_section(full_text, "standard_of_review")
        if has_sor:
            checks.append(("Standard of Review", "MCR 7.212(B)(6)", "major",
                           True, "Standard of Review section found.", ""))
        else:
            checks.append(("Standard of Review", "MCR 7.212(B)(6)", "major",
                           False, "No Standard of Review section detected.",
                           "Add 'STANDARD OF REVIEW' stating the standard for each issue "
                           "(de novo, clear error, abuse of discretion)."))

        # 7. Argument — MCR 7.212(B)(7)
        has_arg = _has_section(full_text, "argument")
        if not has_arg:
            # Fallback: look for generic ARGUMENT header
            has_arg = bool(re.search(r"\bARGUMENT\b", full_text))
        if has_arg:
            checks.append(("Argument", "MCR 7.212(B)(7)", "critical",
                           True, "Argument section found.", ""))
        else:
            checks.append(("Argument", "MCR 7.212(B)(7)", "critical",
                           False, "No Argument section detected.",
                           "Add numbered argument sections with headings for each issue."))

        # 8. Relief Requested — MCR 7.212(B)(8)
        has_relief = _has_section(full_text, "relief_requested")
        if not has_relief:
            # Fallback: look for common relief language
            has_relief = bool(re.search(
                r"(?:asks|requests|prays)\s+(?:that\s+)?this\s+Court|"
                r"(?:reverse|remand|vacate|grant)",
                full_text, re.IGNORECASE
            ))
        if has_relief:
            checks.append(("Relief Requested", "MCR 7.212(B)(8)", "critical",
                           True, "Relief Requested section found.", ""))
        else:
            checks.append(("Relief Requested", "MCR 7.212(B)(8)", "critical",
                           False, "No Relief Requested section detected.",
                           "Add 'RELIEF REQUESTED' specifying exactly what relief is sought "
                           "(reverse, remand, vacate, etc.)."))

        # 9. Signature — MCR 7.212(B)(9)
        has_sig = _has_section(full_text, "signature_block")
        has_bar = bool(_BAR_NUMBER_RE.search(full_text))
        has_addr = bool(_ADDRESS_RE.search(full_text))
        # For pro se: "pro se" designation is acceptable in lieu of bar number
        has_pro_se = bool(re.search(r"pro\s+se|self[- ]represented", full_text, re.IGNORECASE))
        sig_ok = has_sig and (has_bar or has_pro_se) and has_addr
        if sig_ok:
            checks.append(("Signature Block", "MCR 7.212(B)(9)", "critical",
                           True, "Signature with required identifiers found.", ""))
        else:
            missing = []
            if not has_sig:
                missing.append("signature line")
            if not has_bar and not has_pro_se:
                missing.append("bar number or 'pro se' designation")
            if not has_addr:
                missing.append("mailing address")
            checks.append(("Signature Block", "MCR 7.212(B)(9)", "critical",
                           False, f"Signature block incomplete — missing: {', '.join(missing)}.",
                           "Add 'Respectfully submitted,' followed by /s/ Name, address, "
                           "and bar number (or 'Plaintiff/Appellant, pro se')."))

        # 10. Word/Page Limit — MCR 7.212(B)(10)
        within_limit = wc <= self.WORD_LIMIT_COA
        if within_limit:
            checks.append(("Word/Page Limit", "MCR 7.212(B)(10)", "critical",
                           True,
                           f"Word count {wc:,} is within the {self.WORD_LIMIT_COA:,}-word limit.", ""))
        else:
            over = wc - self.WORD_LIMIT_COA
            checks.append(("Word/Page Limit", "MCR 7.212(B)(10)", "critical",
                           False,
                           f"Word count {wc:,} exceeds the {self.WORD_LIMIT_COA:,}-word limit by {over:,} words.",
                           "Reduce brief length or file a motion for leave to exceed word limits."))

        # 11. Certificate of Compliance — MCR 7.212(B)(11)
        has_cert = _has_section(full_text, "certificate_of_compliance")
        if has_cert:
            checks.append(("Certificate of Compliance", "MCR 7.212(B)(11)", "major",
                           True, "Certificate of Compliance found.", ""))
        else:
            checks.append(("Certificate of Compliance", "MCR 7.212(B)(11)", "major",
                           False, "No Certificate of Compliance detected.",
                           "Add certificate stating: 'This brief contains [N] words, "
                           "in compliance with MCR 7.212(B).'"))

        # 12. Appendix — MCR 7.212(C)
        has_app = _has_section(full_text, "appendix")
        if appendix_text:
            has_app = has_app or _has_section(appendix_text, "appendix")
        if has_app:
            checks.append(("Appendix", "MCR 7.212(C)", "major",
                           True, "Appendix detected.", ""))
            # Check for register of actions
            has_roa = bool(re.search(r"REGISTER\s+OF\s+ACTIONS", full_text, re.IGNORECASE))
            if not has_roa and appendix_text:
                has_roa = bool(re.search(r"REGISTER\s+OF\s+ACTIONS", appendix_text, re.IGNORECASE))
            if not has_roa:
                result.warnings.append(
                    "Appendix may be missing Register of Actions (MCR 7.212(C)(1)(a))."
                )
        else:
            checks.append(("Appendix", "MCR 7.212(C)", "major",
                           False, "No Appendix detected.",
                           "Include appendix with: (a) register of actions, "
                           "(b) order/opinion appealed, (c) relevant pleadings."))

        # 13. Font — MCR 7.212(A) — text-based heuristic only
        font_note = ("Font compliance cannot be fully verified from plain text. "
                     "Ensure proportional 12pt minimum or monospaced 10pt minimum.")
        checks.append(("Font Requirement", "MCR 7.212(A)", "minor",
                       True, font_note, ""))
        result.warnings.append(font_note)

        # 14. Margins — MCR 7.212(A) — text-based heuristic only
        margin_note = ("Margin compliance cannot be verified from plain text. "
                       "Ensure 1-inch margins on all sides in final document.")
        checks.append(("Margins", "MCR 7.212(A)", "minor",
                       True, margin_note, ""))
        result.warnings.append(margin_note)

        # 15. Double-spaced — MCR 7.212(A)
        spacing_note = ("Double-spacing cannot be verified from plain text. "
                        "Ensure body text is double-spaced in final document.")
        checks.append(("Double Spacing", "MCR 7.212(A)", "minor",
                       True, spacing_note, ""))
        result.warnings.append(spacing_note)

        # 16. Cover page — MCR 7.212(A)
        has_cover = _has_section(full_text, "cover_page")
        if has_cover:
            checks.append(("Cover Page", "MCR 7.212(A)", "major",
                           True, "Cover page with case information detected.", ""))
        else:
            checks.append(("Cover Page", "MCR 7.212(A)", "major",
                           False, "No cover page detected.",
                           "Add cover page with: court name, docket number, case caption, "
                           "party designations, and document title."))

        # ── Assemble result ──
        self._compile_result(result, checks)
        return result

    # ── MSC Original Action — MCR 7.306 ──────────────────────────────

    def validate_msc_complaint(self, document_text: str) -> ValidationResult:
        """Validate an MSC original action complaint against MCR 7.306 requirements.

        Args:
            document_text: Full text of the MSC complaint.

        Returns:
            ValidationResult with per-requirement pass/fail, score, and suggestions.
        """
        result = ValidationResult(document_type="msc_complaint")
        result.word_count = _count_words(document_text)
        result.page_estimate = _estimate_pages(result.word_count)

        checks: List[Tuple[str, str, str, bool, str, str]] = []

        # 1. Jurisdiction facts
        has_jur = _has_section(document_text, "jurisdiction")
        has_const = bool(re.search(
            r"Const\s+1963.*art\s+6.*§\s*4|article\s+6.*section\s+4|"
            r"original\s+jurisdiction|superintending\s+control",
            document_text, re.IGNORECASE
        ))
        if has_jur or has_const:
            checks.append(("Jurisdiction Facts", "MCR 7.306(B)", "critical",
                           True, "Jurisdictional facts stated.", ""))
        else:
            checks.append(("Jurisdiction Facts", "MCR 7.306(B)", "critical",
                           False, "No jurisdictional statement detected.",
                           "State facts showing MSC jurisdiction under Const 1963, art 6, § 4 "
                           "and MCR 7.306."))

        # 2. Normal course inadequate
        has_nc = _has_section(document_text, "normal_course_inadequate")
        if has_nc:
            checks.append(("Normal Course Inadequate", "MCR 7.306(B)", "critical",
                           True, "Explains why normal appellate course is inadequate.", ""))
        else:
            checks.append(("Normal Course Inadequate", "MCR 7.306(B)", "critical",
                           False, "Does not explain why normal appellate process is inadequate.",
                           "Add section explaining why COA appeal is inadequate "
                           "(e.g., irreparable harm, systemic abuse, delay)."))

        # 3. Specific relief
        has_relief = _has_section(document_text, "relief_requested")
        if not has_relief:
            has_relief = bool(re.search(
                r"(?:asks|requests|prays|seeks)\s+(?:that\s+)?this\s+Court|"
                r"ORDER\s+(?:of|for)\s+(?:superintending|mandamus|prohibition)",
                document_text, re.IGNORECASE
            ))
        if has_relief:
            checks.append(("Specific Relief", "MCR 7.306(B)", "critical",
                           True, "Specific relief stated.", ""))
        else:
            checks.append(("Specific Relief", "MCR 7.306(B)", "critical",
                           False, "No specific relief stated.",
                           "Specify exact relief: vacate orders, mandamus, reassign judge, etc."))

        # 4. Verified by affidavit
        has_aff = _has_section(document_text, "affidavit")
        if has_aff:
            checks.append(("Verified by Affidavit", "MCR 7.306(B)(1)", "critical",
                           True, "Verification/affidavit language found.", ""))
        else:
            checks.append(("Verified by Affidavit", "MCR 7.306(B)(1)", "critical",
                           False, "No affidavit or verification detected.",
                           "Add sworn verification: 'I, [Name], being duly sworn, state that "
                           "the facts set forth in this complaint are true...'"))

        # 5. Brief in support
        has_brief = _has_section(document_text, "brief_in_support")
        # Also accept ARGUMENT as a brief substitute in combined filings
        if not has_brief:
            has_brief = bool(re.search(r"\bARGUMENT\b", document_text))
        if has_brief:
            checks.append(("Brief in Support", "MCR 7.306(B)(2)", "critical",
                           True, "Brief in support / argument section found.", ""))
        else:
            checks.append(("Brief in Support", "MCR 7.306(B)(2)", "critical",
                           False, "No brief in support detected.",
                           "Include a 'BRIEF IN SUPPORT' or 'ARGUMENT' section with legal analysis."))

        # 6. Copies note
        checks.append(("Required Copies", "MCR 7.306(B)", "major",
                       True,
                       "REMINDER: File original + 4 copies minimum; 13 copies per MSC local practice.",
                       "Prepare 13 copies for MSC filing window."))
        result.warnings.append("MSC requires original + 4 copies (13 per local practice). Verify before filing.")

        # 7. Certificate of Service
        has_cos = _has_section(document_text, "certificate_of_service")
        if has_cos:
            checks.append(("Certificate of Service", "MCR 7.306(B)", "critical",
                           True, "Certificate of Service found.", ""))
        else:
            checks.append(("Certificate of Service", "MCR 7.306(B)", "critical",
                           False, "No Certificate of Service detected.",
                           "Add Certificate of Service listing all parties served, "
                           "method of service, and date."))

        # 8. Filing fee
        has_fee = bool(_FEE_RE.search(document_text))
        if has_fee:
            checks.append(("Filing Fee / Waiver", "MCR 7.306(B)", "major",
                           True, "Filing fee or fee waiver reference found.", ""))
        else:
            checks.append(("Filing Fee / Waiver", "MCR 7.306(B)", "major",
                           False, "No filing fee or fee waiver reference.",
                           "Include filing fee payment or attach IFP application."))
            result.warnings.append("Filing fee ($375) or fee waiver (IFP) application required.")

        # 9. Proposed order
        has_po = _has_section(document_text, "proposed_order")
        if has_po:
            checks.append(("Proposed Order", "MCR 7.306(B)", "major",
                           True, "Proposed order detected.", ""))
        else:
            checks.append(("Proposed Order", "MCR 7.306(B)", "major",
                           False, "No proposed order detected.",
                           "Attach a proposed order granting the requested relief."))

        self._compile_result(result, checks)
        return result

    # ── MSC Emergency Application — MCR 7.305(F) ────────────────────

    def validate_msc_emergency(self, document_text: str) -> ValidationResult:
        """Validate an MSC emergency application against MCR 7.305(F).

        Args:
            document_text: Full text of the emergency application.

        Returns:
            ValidationResult with per-requirement pass/fail, score, and suggestions.
        """
        result = ValidationResult(document_type="msc_emergency")
        result.word_count = _count_words(document_text)
        result.page_estimate = _estimate_pages(result.word_count)

        checks: List[Tuple[str, str, str, bool, str, str]] = []

        # 1. Irreparable harm
        has_harm = _has_section(document_text, "irreparable_harm")
        if has_harm:
            checks.append(("Irreparable Harm", "MCR 7.305(F)", "critical",
                           True, "Irreparable harm language found.", ""))
        else:
            checks.append(("Irreparable Harm", "MCR 7.305(F)", "critical",
                           False, "No showing of immediate irreparable harm.",
                           "Add specific facts showing immediate irreparable harm "
                           "(e.g., 567+ days parent-child separation, ongoing constitutional violations)."))

        # 2. All parties notified
        has_notified = _has_section(document_text, "parties_notified")
        if has_notified:
            checks.append(("All Parties Notified", "MCR 7.305(F)", "critical",
                           True, "Party notification language found.", ""))
        else:
            checks.append(("All Parties Notified", "MCR 7.305(F)", "critical",
                           False, "No statement that parties were notified.",
                           "Add: 'All parties have been served/notified of this emergency application' "
                           "or explain why notice was not possible."))

        # 3. Normal briefing inadequate
        has_briefing = _has_section(document_text, "normal_briefing_inadequate")
        if has_briefing:
            checks.append(("Normal Briefing Inadequate", "MCR 7.305(F)", "critical",
                           True, "Explains why normal briefing schedule is inadequate.", ""))
        else:
            checks.append(("Normal Briefing Inadequate", "MCR 7.305(F)", "critical",
                           False, "Does not explain why normal briefing schedule is inadequate.",
                           "Add statement explaining urgency and why standard briefing "
                           "timeline would cause irreparable harm."))

        self._compile_result(result, checks)
        return result

    # ── Router ───────────────────────────────────────────────────────

    def validate_any(
        self,
        document_text: str,
        document_type: str,
        appendix_text: Optional[str] = None,
    ) -> ValidationResult:
        """Route to the correct validator based on document type.

        Args:
            document_text: Full document text.
            document_type: One of 'coa_brief', 'msc_complaint', 'msc_emergency'.
            appendix_text: Optional appendix (COA briefs only).

        Returns:
            ValidationResult from the appropriate validator.

        Raises:
            ValueError: If document_type is not recognized.
        """
        dt = document_type.lower().strip().replace(" ", "_").replace("-", "_")
        if dt in ("coa_brief", "coa", "appellate_brief", "brief"):
            return self.validate_coa_brief(document_text, appendix_text)
        elif dt in ("msc_complaint", "msc_original", "superintending_control",
                     "mandamus", "habeas", "prohibition"):
            return self.validate_msc_complaint(document_text)
        elif dt in ("msc_emergency", "emergency", "emergency_application"):
            return self.validate_msc_emergency(document_text)
        else:
            raise ValueError(
                f"Unknown document type: '{document_type}'. "
                f"Supported: coa_brief, msc_complaint, msc_emergency"
            )

    # ── Requirements Lookup ──────────────────────────────────────────

    @staticmethod
    def get_requirements(document_type: str) -> List[Dict[str, str]]:
        """Return the full list of requirements with MCR citations for a document type.

        Args:
            document_type: One of 'coa_brief', 'msc_complaint', 'msc_emergency'.

        Returns:
            List of dicts with id, name, mcr, severity, description.
        """
        dt = document_type.lower().strip().replace(" ", "_").replace("-", "_")
        if dt in ("coa_brief", "coa", "appellate_brief", "brief"):
            return COA_BRIEF_REQUIREMENTS
        elif dt in ("msc_complaint", "msc_original", "superintending_control"):
            return MSC_COMPLAINT_REQUIREMENTS
        elif dt in ("msc_emergency", "emergency", "emergency_application"):
            return MSC_EMERGENCY_REQUIREMENTS
        else:
            return COA_BRIEF_REQUIREMENTS + MSC_COMPLAINT_REQUIREMENTS + MSC_EMERGENCY_REQUIREMENTS

    # ── Checklist Generator ──────────────────────────────────────────

    @staticmethod
    def generate_checklist(document_type: str) -> str:
        """Generate a printable filing checklist for the given document type.

        Args:
            document_type: One of 'coa_brief', 'msc_complaint', 'msc_emergency'.

        Returns:
            Formatted text checklist ready for printing.
        """
        dt = document_type.lower().strip().replace(" ", "_").replace("-", "_")

        if dt in ("coa_brief", "coa", "appellate_brief", "brief"):
            title = "COA APPELLATE BRIEF FILING CHECKLIST — MCR 7.212"
            reqs = COA_BRIEF_REQUIREMENTS
            extras = [
                "[ ] Proof of Service filed (MCR 2.107)",
                "[ ] Filing fee paid or IFP granted",
                "[ ] Register of Actions in Appendix (MCR 7.212(C)(1)(a))",
                "[ ] Opinion/order appealed in Appendix (MCR 7.212(C)(1)(b))",
                "[ ] All documents bound per COA clerk requirements",
                "[ ] e-Filing via MiFile (or physical copies per court direction)",
            ]
        elif dt in ("msc_complaint", "msc_original", "superintending_control"):
            title = "MSC ORIGINAL ACTION FILING CHECKLIST — MCR 7.306"
            reqs = MSC_COMPLAINT_REQUIREMENTS
            extras = [
                "[ ] 13 physical copies prepared (MSC local practice)",
                "[ ] Affidavit notarized before a notary public",
                "[ ] Filing fee ($375) or IFP application attached",
                "[ ] Service addresses verified for all parties",
                "[ ] All exhibits tabbed and indexed",
                "[ ] Proposed order in separate document",
            ]
        elif dt in ("msc_emergency", "emergency", "emergency_application"):
            title = "MSC EMERGENCY APPLICATION CHECKLIST — MCR 7.305(F)"
            reqs = MSC_EMERGENCY_REQUIREMENTS
            extras = [
                "[ ] Mark envelope/cover: 'EMERGENCY — IMMEDIATE ATTENTION REQUESTED'",
                "[ ] Call MSC Clerk's Office to alert of incoming emergency filing",
                "[ ] Serve opposing parties simultaneously or explain inability",
                "[ ] Include proof of lower court filing (if applicable)",
                "[ ] Attach underlying order being challenged",
                "[ ] Include proposed emergency order",
            ]
        else:
            return f"Unknown document type: {document_type}"

        lines = [
            "=" * 70,
            f"  {title}",
            "=" * 70,
            "",
            "REQUIRED DOCUMENT SECTIONS:",
            "-" * 40,
        ]
        for req in reqs:
            sev_tag = f"[{req['severity'].upper()}]"
            lines.append(f"[ ] {req['name']:40s} {sev_tag:10s} {req['mcr']}")
            lines.append(f"    {req['description']}")
            lines.append("")

        lines.append("ADDITIONAL FILING REQUIREMENTS:")
        lines.append("-" * 40)
        for extra in extras:
            lines.append(extra)

        lines.append("")
        lines.append("=" * 70)
        lines.append("  Validate document with: AppellateValidator().validate_any(text, type)")
        lines.append("=" * 70)

        return "\n".join(lines)

    # ── Internal: compile check tuples into ValidationResult ─────────

    def _compile_result(
        self,
        result: ValidationResult,
        checks: List[Tuple[str, str, str, bool, str, str]],
    ) -> None:
        """Convert raw check tuples into the ValidationResult object."""
        for req_name, mcr, severity, passed, message, suggestion in checks:
            cr = CheckResult(
                requirement=req_name,
                mcr_citation=mcr,
                passed=passed,
                severity=severity,
                message=message,
                suggestion=suggestion,
            )
            if passed:
                result.passed_checks.append(cr)
            else:
                result.failed_checks.append(cr)
                result.mcr_violations.append(f"{mcr}: {req_name}")
                penalty = _SEVERITY_PENALTY.get(severity, 5)
                result.overall_score -= penalty
                if suggestion:
                    result.suggestions.append(f"[{mcr}] {suggestion}")

        result.overall_score = max(0, min(100, result.overall_score))


# ── Module-level convenience functions ───────────────────────────────────────

_default_validator: Optional[AppellateValidator] = None


def _get_validator() -> AppellateValidator:
    global _default_validator
    if _default_validator is None:
        _default_validator = AppellateValidator()
    return _default_validator


def validate_coa_brief(
    document_text: str, appendix_text: Optional[str] = None
) -> ValidationResult:
    """Validate a COA brief against MCR 7.212. See AppellateValidator.validate_coa_brief."""
    return _get_validator().validate_coa_brief(document_text, appendix_text)


def validate_msc_complaint(document_text: str) -> ValidationResult:
    """Validate an MSC complaint against MCR 7.306. See AppellateValidator.validate_msc_complaint."""
    return _get_validator().validate_msc_complaint(document_text)


def validate_msc_emergency(document_text: str) -> ValidationResult:
    """Validate an MSC emergency app against MCR 7.305(F). See AppellateValidator.validate_msc_emergency."""
    return _get_validator().validate_msc_emergency(document_text)


def validate_any(
    document_text: str,
    document_type: str,
    appendix_text: Optional[str] = None,
) -> ValidationResult:
    """Route to correct validator. See AppellateValidator.validate_any."""
    return _get_validator().validate_any(document_text, document_type, appendix_text)


def get_requirements(document_type: str) -> List[Dict[str, str]]:
    """Get requirements list. See AppellateValidator.get_requirements."""
    return AppellateValidator.get_requirements(document_type)


def generate_checklist(document_type: str) -> str:
    """Generate printable checklist. See AppellateValidator.generate_checklist."""
    return AppellateValidator.generate_checklist(document_type)


# ── CLI entry point ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate Michigan appellate documents against MCR requirements."
    )
    parser.add_argument("file", nargs="?", help="Document file to validate")
    parser.add_argument(
        "--type", "-t", default="coa_brief",
        choices=["coa_brief", "msc_complaint", "msc_emergency"],
        help="Document type (default: coa_brief)",
    )
    parser.add_argument(
        "--appendix", "-a", default=None,
        help="Optional appendix file (COA briefs only)",
    )
    parser.add_argument(
        "--checklist", "-c", action="store_true",
        help="Print filing checklist instead of validating",
    )
    parser.add_argument(
        "--requirements", "-r", action="store_true",
        help="Print requirements list instead of validating",
    )
    args = parser.parse_args()

    if args.checklist:
        print(generate_checklist(args.type))
        sys.exit(0)

    if args.requirements:
        reqs = get_requirements(args.type)
        for r in reqs:
            print(f"[{r['severity'].upper():8s}] {r['mcr']:20s} {r['name']}")
            print(f"           {r['description']}")
            print()
        sys.exit(0)

    if not args.file:
        parser.error("Provide a document file to validate, or use --checklist / --requirements.")

    with open(args.file, "r", encoding="utf-8") as f:
        doc_text = f.read()

    app_text = None
    if args.appendix:
        with open(args.appendix, "r", encoding="utf-8") as f:
            app_text = f.read()

    vr = validate_any(doc_text, args.type, app_text)
    cycle_json(vr.to_dict())
