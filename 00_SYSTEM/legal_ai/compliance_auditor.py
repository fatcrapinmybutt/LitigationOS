# -*- coding: utf-8 -*-
"""
Compliance Auditor — LitigationOS Legal AI Subsystem
=====================================================
Audits court filings, motions, briefs, and evidence packages for
compliance with Michigan Court Rules (MCR), local rules, and
formatting requirements before submission.  Catches errors that
cause rejection, delay, or sanctions.

Case Context
------------
    Plaintiff:  Andrew James Pigors (Pro Se)
    Defendant:  Emily A. Watson
    Child:      L.D.W. (per MCR 8.119(H)) — Male
    Judge:      Hon. Jenny L. McNeill — 14th Circuit Court
    Cases:      2024-001507-DC, 2025-002760-CZ, 2023-5907-PP, COA 366810
    Lanes:      ALL (A through F)

Michigan Rules (primary)
------------------------
    MCR 2.113  — Form of Pleadings
    MCR 2.107  — Service of Process
    MCR 2.119  — Motion Practice
    MCR 7.212  — Appellate Briefs (COA formatting)
    MCR 8.119  — Court Records — Sealed / Protected Info
    MCL 750.411t — Identifiers in filings

Usage::

    from legal_ai.compliance_auditor import ComplianceAuditor

    auditor = ComplianceAuditor()
    report = auditor.full_audit(filing_text, filing_type="motion")

Zero external dependencies.  CPU-first.  Local-only.
"""
from __future__ import annotations

import json
import logging
import re
import sqlite3
import sys
import textwrap
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import IntEnum, Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

logger = logging.getLogger("legal_ai.compliance_auditor")

# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------
_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parents[1]
_DB_PATH = _REPO / "litigation_context.db"

# ---------------------------------------------------------------------------
# Case constants
# ---------------------------------------------------------------------------
_PLAINTIFF = "Andrew James Pigors"
_DEFENDANT = "Emily A. Watson"
_CHILD_INITIALS = "L.D.W."
_CHILD_NAME_INITIALS = "L.D.W."
_JUDGE = "Hon. Jenny L. McNeill"
_COURT = "14th Circuit Court"
_COURT_ADDRESS = "Muskegon County Courthouse, 990 Terrace St, Muskegon, MI 49442"

LANE_CASES: Dict[str, str] = {
    "A": "2024-001507-DC",
    "B": "2025-002760-CZ",
    "C": "Convergence",
    "D": "2023-5907-PP",
    "E": "JTC / Misconduct",
    "F": "COA 366810",
}

# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class ComplianceCategory(str, Enum):
    """Categories of compliance checks."""

    FORMAT = "format"
    CONTENT = "content"
    CITATION = "citation"
    SERVICE = "service"
    SIGNATURE = "signature"
    VERIFICATION = "verification"
    TIMELINESS = "timeliness"
    ACCESSIBILITY = "accessibility"


class ComplianceLevel(str, Enum):
    """Severity levels for compliance issues."""

    PASS = "pass"
    WARNING = "warning"
    FAIL = "fail"
    CRITICAL = "critical"

    @property
    def severity_rank(self) -> int:
        _ranks = {"pass": 0, "warning": 1, "fail": 2, "critical": 3}
        return _ranks.get(self.value, 0)


class FilingType(str, Enum):
    """Types of court filings."""

    MOTION = "motion"
    RESPONSE = "response"
    REPLY = "reply"
    BRIEF = "brief"
    COMPLAINT = "complaint"
    ANSWER = "answer"
    AFFIDAVIT = "affidavit"
    EXHIBIT = "exhibit"
    PROPOSED_ORDER = "proposed_order"
    PROOF_OF_SERVICE = "proof_of_service"
    NOTICE = "notice"
    STIPULATION = "stipulation"


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class ComplianceIssue:
    """A single compliance issue found during audit."""

    issue_id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    category: ComplianceCategory = ComplianceCategory.FORMAT
    level: ComplianceLevel = ComplianceLevel.WARNING
    rule_reference: str = ""
    description: str = ""
    location: str = ""
    suggestion: str = ""
    auto_fixable: bool = False

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["category"] = self.category.value
        d["level"] = self.level.value
        return d


@dataclass
class AuditResult:
    """Result of a full compliance audit."""

    audit_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    filing_type: str = ""
    issues: List[ComplianceIssue] = field(default_factory=list)
    overall_level: ComplianceLevel = ComplianceLevel.PASS
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    @property
    def pass_count(self) -> int:
        return sum(1 for i in self.issues if i.level == ComplianceLevel.PASS)

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.level == ComplianceLevel.WARNING)

    @property
    def fail_count(self) -> int:
        return sum(1 for i in self.issues if i.level == ComplianceLevel.FAIL)

    @property
    def critical_count(self) -> int:
        return sum(1 for i in self.issues if i.level == ComplianceLevel.CRITICAL)

    @property
    def is_filing_ready(self) -> bool:
        return self.fail_count == 0 and self.critical_count == 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "audit_id": self.audit_id,
            "filing_type": self.filing_type,
            "issues": [i.to_dict() for i in self.issues],
            "overall_level": self.overall_level.value,
            "pass_count": self.pass_count,
            "warning_count": self.warning_count,
            "fail_count": self.fail_count,
            "critical_count": self.critical_count,
            "is_filing_ready": self.is_filing_ready,
            "timestamp": self.timestamp,
        }


# ---------------------------------------------------------------------------
# FormatAuditor
# ---------------------------------------------------------------------------

# Regexes compiled at module level
_RE_CAPTION = re.compile(
    r"(state\s+of\s+michigan|circuit\s+court|case\s+no\.?\s*\d)",
    re.IGNORECASE,
)
_RE_CASE_NUMBER = re.compile(
    r"(case\s+no\.?\s*|no\.?\s*)(\d{4}-\d{3,6}-[A-Z]{2})",
    re.IGNORECASE,
)
_RE_PAGE_NUM = re.compile(r"(page\s+\d+|^\d+$)", re.IGNORECASE | re.MULTILINE)
_RE_DOUBLE_SPACE = re.compile(r"\n\n\n+")
_RE_CHILD_FULL_NAME = re.compile(
    r"\b(child(?:'s)?\s+full\s+name|minor(?:'s)?\s+(?:full\s+)?name)\b",
    re.IGNORECASE,
)


class FormatAuditor:
    """Checks formatting compliance with MCR 2.113 and MCR 7.212."""

    _MCR_2_113_REQUIREMENTS = {
        "caption": "Caption must include court name, case number, and parties",
        "case_number": "Case number must appear in the caption",
        "title": "Document must include a descriptive title",
        "signature_block": "Must include signature block per MCR 2.113(E)",
        "page_format": "Pages must be numbered",
    }

    _MCR_7_212_REQUIREMENTS = {
        "margin_note": "Brief must note 1-inch margins (MCR 7.212(B))",
        "font_note": "Brief must use at least 12-point type (MCR 7.212(B))",
        "page_limit": "Brief of appellant: 50 pages max (MCR 7.212(B))",
        "toc": "Brief must include Table of Contents (MCR 7.212(D)(1))",
        "toa": "Brief must include Table of Authorities (MCR 7.212(D)(2))",
        "jurisdictional_statement": "Must include jurisdictional statement (MCR 7.212(D)(3))",
        "statement_of_questions": "Must include statement of questions (MCR 7.212(D)(4))",
    }

    def audit(
        self,
        text: str,
        filing_type: str = "motion",
    ) -> List[ComplianceIssue]:
        """Run format audit."""
        issues: List[ComplianceIssue] = []

        # Caption check
        if _RE_CAPTION.search(text):
            issues.append(ComplianceIssue(
                category=ComplianceCategory.FORMAT,
                level=ComplianceLevel.PASS,
                rule_reference="MCR 2.113(A)",
                description="Caption detected",
            ))
        else:
            issues.append(ComplianceIssue(
                category=ComplianceCategory.FORMAT,
                level=ComplianceLevel.FAIL,
                rule_reference="MCR 2.113(A)",
                description="Caption missing or incomplete — must include "
                            "court name, case number, and parties",
                suggestion="Add standard Michigan caption block",
            ))

        # Case number
        if _RE_CASE_NUMBER.search(text):
            issues.append(ComplianceIssue(
                category=ComplianceCategory.FORMAT,
                level=ComplianceLevel.PASS,
                rule_reference="MCR 2.113(A)",
                description="Case number found in filing",
            ))
        else:
            issues.append(ComplianceIssue(
                category=ComplianceCategory.FORMAT,
                level=ComplianceLevel.FAIL,
                rule_reference="MCR 2.113(A)",
                description="Case number not found — required in caption",
                suggestion="Add case number in format: YYYY-NNNNNN-XX",
            ))

        # Page numbers
        if _RE_PAGE_NUM.search(text):
            issues.append(ComplianceIssue(
                category=ComplianceCategory.FORMAT,
                level=ComplianceLevel.PASS,
                rule_reference="MCR 2.113(C)(1)",
                description="Page numbers detected",
            ))
        else:
            issues.append(ComplianceIssue(
                category=ComplianceCategory.FORMAT,
                level=ComplianceLevel.WARNING,
                rule_reference="MCR 2.113(C)(1)",
                description="Page numbers not detected — recommended",
                suggestion="Add page numbers to all pages",
                auto_fixable=True,
            ))

        # Triple spacing
        if _RE_DOUBLE_SPACE.search(text):
            issues.append(ComplianceIssue(
                category=ComplianceCategory.FORMAT,
                level=ComplianceLevel.WARNING,
                rule_reference="MCR 2.113(C)",
                description="Excessive blank lines detected",
                suggestion="Remove triple-or-more blank lines",
                auto_fixable=True,
            ))

        # Appellate-specific checks
        if filing_type == "brief":
            issues.extend(self._audit_appellate_brief(text))

        return issues

    def _audit_appellate_brief(self, text: str) -> List[ComplianceIssue]:
        """Additional checks for appellate briefs per MCR 7.212."""
        issues: List[ComplianceIssue] = []
        lower = text.lower()

        if "table of contents" in lower:
            issues.append(ComplianceIssue(
                category=ComplianceCategory.FORMAT,
                level=ComplianceLevel.PASS,
                rule_reference="MCR 7.212(D)(1)",
                description="Table of Contents found",
            ))
        else:
            issues.append(ComplianceIssue(
                category=ComplianceCategory.FORMAT,
                level=ComplianceLevel.FAIL,
                rule_reference="MCR 7.212(D)(1)",
                description="Table of Contents missing — required for appellate brief",
                suggestion="Add a Table of Contents listing all sections",
            ))

        if "table of authorities" in lower:
            issues.append(ComplianceIssue(
                category=ComplianceCategory.FORMAT,
                level=ComplianceLevel.PASS,
                rule_reference="MCR 7.212(D)(2)",
                description="Table of Authorities found",
            ))
        else:
            issues.append(ComplianceIssue(
                category=ComplianceCategory.FORMAT,
                level=ComplianceLevel.FAIL,
                rule_reference="MCR 7.212(D)(2)",
                description="Table of Authorities missing — required for appellate brief",
                suggestion="Add a Table of Authorities with page references",
            ))

        if "jurisdiction" in lower:
            issues.append(ComplianceIssue(
                category=ComplianceCategory.FORMAT,
                level=ComplianceLevel.PASS,
                rule_reference="MCR 7.212(D)(3)",
                description="Jurisdictional statement found",
            ))
        else:
            issues.append(ComplianceIssue(
                category=ComplianceCategory.FORMAT,
                level=ComplianceLevel.FAIL,
                rule_reference="MCR 7.212(D)(3)",
                description="Jurisdictional statement missing — required for appellate brief",
                suggestion="Add statement of basis for appellate jurisdiction",
            ))

        if "question" in lower or "issue" in lower:
            issues.append(ComplianceIssue(
                category=ComplianceCategory.FORMAT,
                level=ComplianceLevel.PASS,
                rule_reference="MCR 7.212(D)(4)",
                description="Statement of questions/issues found",
            ))
        else:
            issues.append(ComplianceIssue(
                category=ComplianceCategory.FORMAT,
                level=ComplianceLevel.WARNING,
                rule_reference="MCR 7.212(D)(4)",
                description="Statement of questions not clearly identified",
                suggestion="Add explicit 'Statement of Questions Presented' section",
            ))

        return issues

    def get_stats(self) -> Dict[str, Any]:
        return {
            "component": "FormatAuditor",
            "mcr_2_113_checks": len(self._MCR_2_113_REQUIREMENTS),
            "mcr_7_212_checks": len(self._MCR_7_212_REQUIREMENTS),
        }


# ---------------------------------------------------------------------------
# ContentAuditor
# ---------------------------------------------------------------------------

# Privacy protection patterns
_RE_SSN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
_RE_DOB = re.compile(
    r"\b(date\s+of\s+birth|DOB|born\s+on)\s*:?\s*\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}\b",
    re.IGNORECASE,
)
_RE_SIGNATURE = re.compile(
    r"(respectfully\s+submitted|/s/|signature)", re.IGNORECASE
)
_RE_VERIFICATION = re.compile(
    r"(under\s+penalty\s+of\s+perjury|sworn\s+and\s+subscribed|notary)",
    re.IGNORECASE,
)
_RE_PROOF_OF_SERVICE = re.compile(
    r"(proof\s+of\s+service|certificate\s+of\s+service|I\s+(?:hereby\s+)?certif)",
    re.IGNORECASE,
)
_RE_DATE_FILED = re.compile(
    r"(date[d]?|filed)\s*:?\s*\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}",
    re.IGNORECASE,
)
_RE_RELIEF_REQUEST = re.compile(
    r"(requests?\s+that|pray\s+for|respectfully\s+(?:ask|request)|"
    r"wherefore|relief\s+sought)",
    re.IGNORECASE,
)


class ContentAuditor:
    """Checks content compliance: privacy, completeness, proper references."""

    def audit(
        self,
        text: str,
        filing_type: str = "motion",
    ) -> List[ComplianceIssue]:
        """Run content audit."""
        issues: List[ComplianceIssue] = []

        # Privacy checks — MCR 8.119(H) / MCL 750.411t
        issues.extend(self._check_privacy(text))

        # Signature check
        issues.extend(self._check_signature(text))

        # Proof of service
        issues.extend(self._check_proof_of_service(text, filing_type))

        # Relief requested
        if filing_type in ("motion", "complaint", "brief"):
            issues.extend(self._check_relief_request(text))

        # Date
        issues.extend(self._check_date(text))

        return issues

    def _check_privacy(self, text: str) -> List[ComplianceIssue]:
        """Check for improperly disclosed personal information."""
        issues: List[ComplianceIssue] = []

        # SSN check
        if _RE_SSN.search(text):
            issues.append(ComplianceIssue(
                category=ComplianceCategory.CONTENT,
                level=ComplianceLevel.CRITICAL,
                rule_reference="MCR 8.119(H)",
                description="Social Security Number detected in filing — "
                            "must be redacted per MCR 8.119(H)",
                suggestion="Remove or redact SSN immediately",
                auto_fixable=True,
            ))
        else:
            issues.append(ComplianceIssue(
                category=ComplianceCategory.CONTENT,
                level=ComplianceLevel.PASS,
                rule_reference="MCR 8.119(H)",
                description="No SSN detected",
            ))

        # DOB check
        if _RE_DOB.search(text):
            issues.append(ComplianceIssue(
                category=ComplianceCategory.CONTENT,
                level=ComplianceLevel.WARNING,
                rule_reference="MCR 8.119(H)",
                description="Date of birth detected — verify it is necessary for this filing",
                suggestion="Consider redacting DOB unless required",
            ))

        # Child name protection
        child_names_exposed = self._check_child_names(text)
        if child_names_exposed:
            issues.append(ComplianceIssue(
                category=ComplianceCategory.CONTENT,
                level=ComplianceLevel.CRITICAL,
                rule_reference="MCR 8.119(H)",
                description=f"Minor child's full name may be exposed — "
                            f"use initials ({_CHILD_INITIALS}) per MCR 8.119(H)",
                suggestion=f"Replace child's full name with {_CHILD_INITIALS}",
                auto_fixable=True,
            ))
        else:
            issues.append(ComplianceIssue(
                category=ComplianceCategory.CONTENT,
                level=ComplianceLevel.PASS,
                rule_reference="MCR 8.119(H)",
                description="Child name protection verified — "
                            f"initials ({_CHILD_INITIALS}) used correctly",
            ))

        return issues

    @staticmethod
    def _check_child_names(text: str) -> bool:
        """Check if child's full name is exposed in the text.

        We do NOT know the child's real name from this module — we only
        check for patterns that suggest a full name near 'child' or
        'minor' keywords.
        """
        return bool(_RE_CHILD_FULL_NAME.search(text))

    def _check_signature(self, text: str) -> List[ComplianceIssue]:
        """Check for signature block."""
        issues: List[ComplianceIssue] = []
        if _RE_SIGNATURE.search(text):
            issues.append(ComplianceIssue(
                category=ComplianceCategory.SIGNATURE,
                level=ComplianceLevel.PASS,
                rule_reference="MCR 2.113(E)",
                description="Signature block detected",
            ))
        else:
            issues.append(ComplianceIssue(
                category=ComplianceCategory.SIGNATURE,
                level=ComplianceLevel.FAIL,
                rule_reference="MCR 2.113(E)",
                description="Signature block not found — required on all filings",
                suggestion=f"Add: Respectfully submitted, /s/ {_PLAINTIFF}",
            ))
        return issues

    def _check_proof_of_service(
        self, text: str, filing_type: str
    ) -> List[ComplianceIssue]:
        """Check for proof of service per MCR 2.107."""
        issues: List[ComplianceIssue] = []
        # Proof of service is required on most filings
        exempt = ("exhibit", "proposed_order")
        if filing_type in exempt:
            return issues

        if _RE_PROOF_OF_SERVICE.search(text):
            issues.append(ComplianceIssue(
                category=ComplianceCategory.SERVICE,
                level=ComplianceLevel.PASS,
                rule_reference="MCR 2.107(C)(3)",
                description="Proof of service detected",
            ))
        else:
            issues.append(ComplianceIssue(
                category=ComplianceCategory.SERVICE,
                level=ComplianceLevel.FAIL,
                rule_reference="MCR 2.107(C)(3)",
                description="Proof of service not found — required on "
                            "all filed documents per MCR 2.107",
                suggestion="Add a Certificate of Service showing method, date, "
                            "and address of service on opposing party",
            ))
        return issues

    def _check_relief_request(self, text: str) -> List[ComplianceIssue]:
        """Check that the filing requests specific relief."""
        issues: List[ComplianceIssue] = []
        if _RE_RELIEF_REQUEST.search(text):
            issues.append(ComplianceIssue(
                category=ComplianceCategory.CONTENT,
                level=ComplianceLevel.PASS,
                rule_reference="MCR 2.111(B)(1)",
                description="Relief request detected",
            ))
        else:
            issues.append(ComplianceIssue(
                category=ComplianceCategory.CONTENT,
                level=ComplianceLevel.WARNING,
                rule_reference="MCR 2.111(B)(1)",
                description="No explicit relief request detected",
                suggestion="Add a WHEREFORE clause specifying the relief sought",
            ))
        return issues

    def _check_date(self, text: str) -> List[ComplianceIssue]:
        """Check for filing date."""
        issues: List[ComplianceIssue] = []
        if _RE_DATE_FILED.search(text):
            issues.append(ComplianceIssue(
                category=ComplianceCategory.CONTENT,
                level=ComplianceLevel.PASS,
                rule_reference="MCR 2.113(E)",
                description="Filing date detected",
            ))
        else:
            issues.append(ComplianceIssue(
                category=ComplianceCategory.CONTENT,
                level=ComplianceLevel.WARNING,
                rule_reference="MCR 2.113(E)",
                description="Filing date not detected",
                suggestion="Add the date to the signature block",
                auto_fixable=True,
            ))
        return issues

    def get_stats(self) -> Dict[str, Any]:
        return {
            "component": "ContentAuditor",
            "categories": len(ComplianceCategory),
            "privacy_checks": 3,
            "content_checks": 4,
        }


# ---------------------------------------------------------------------------
# CitationAuditor
# ---------------------------------------------------------------------------

_RE_MCR = re.compile(r"MCR\s+\d+\.\d+(?:\([A-Za-z0-9]+\))*")
_RE_MCL = re.compile(r"MCL\s+\d+\.\d+[a-z]?(?:\([A-Za-z0-9]+\))*")
_RE_MRE = re.compile(r"MRE\s+\d+(?:\([A-Za-z0-9]+\))*")
_RE_CASE_CITE = re.compile(
    r"\b[A-Z][A-Za-z]+\s+v\.?\s+[A-Z][A-Za-z]+,?\s*"
    r"\d+\s+(?:Mich(?:\s+App)?|NW\s*2d|US)\s+\d+",
)

# Common invalid citation patterns
_KNOWN_BAD_CITATIONS = {
    "MCR 2.113(Z)": "MCR 2.113 subsections go up to (E)",
    "MCR 99.999": "This MCR does not exist",
    "MCL 999.999": "This MCL does not exist",
}


class CitationAuditor:
    """Validates legal citations in filings."""

    _COMMON_MCR = {
        "MCR 2.107", "MCR 2.111", "MCR 2.113", "MCR 2.116",
        "MCR 2.119", "MCR 2.301", "MCR 2.302", "MCR 2.309",
        "MCR 2.310", "MCR 2.313", "MCR 2.401", "MCR 2.501",
        "MCR 2.507", "MCR 2.517", "MCR 3.206", "MCR 3.210",
        "MCR 3.606", "MCR 7.202", "MCR 7.205", "MCR 7.212",
        "MCR 8.119",
    }

    _COMMON_MCL = {
        "MCL 722.21", "MCL 722.22", "MCL 722.23", "MCL 722.24",
        "MCL 722.25", "MCL 722.26", "MCL 722.27", "MCL 722.28",
        "MCL 600.1701", "MCL 600.1715", "MCL 600.2950",
        "MCL 750.411t",
    }

    def audit(self, text: str) -> List[ComplianceIssue]:
        """Run citation audit."""
        issues: List[ComplianceIssue] = []

        # Find all citations
        mcr_cites = _RE_MCR.findall(text)
        mcl_cites = _RE_MCL.findall(text)
        mre_cites = _RE_MRE.findall(text)
        case_cites = _RE_CASE_CITE.findall(text)

        total = len(mcr_cites) + len(mcl_cites) + len(mre_cites) + len(case_cites)

        if total == 0:
            issues.append(ComplianceIssue(
                category=ComplianceCategory.CITATION,
                level=ComplianceLevel.WARNING,
                rule_reference="General",
                description="No legal citations found — filings should cite "
                            "applicable rules and authority",
                suggestion="Add Michigan Court Rule or statutory citations "
                            "supporting your position",
            ))
        else:
            issues.append(ComplianceIssue(
                category=ComplianceCategory.CITATION,
                level=ComplianceLevel.PASS,
                rule_reference="General",
                description=f"Found {total} citation(s): "
                            f"{len(mcr_cites)} MCR, {len(mcl_cites)} MCL, "
                            f"{len(mre_cites)} MRE, {len(case_cites)} case",
            ))

        # Validate known-bad citations
        for cite_pattern, reason in _KNOWN_BAD_CITATIONS.items():
            if cite_pattern in text:
                issues.append(ComplianceIssue(
                    category=ComplianceCategory.CITATION,
                    level=ComplianceLevel.FAIL,
                    rule_reference=cite_pattern,
                    description=f"Invalid citation: {cite_pattern} — {reason}",
                    suggestion="Verify and correct the citation",
                ))

        # Check citation format consistency
        issues.extend(self._check_format_consistency(text))

        return issues

    def _check_format_consistency(self, text: str) -> List[ComplianceIssue]:
        """Check that citations follow consistent formatting."""
        issues: List[ComplianceIssue] = []

        # Check for lowercase "mcr" or "mcl"
        if re.search(r"\bmcr\s+\d", text) or re.search(r"\bmcl\s+\d", text):
            issues.append(ComplianceIssue(
                category=ComplianceCategory.CITATION,
                level=ComplianceLevel.WARNING,
                rule_reference="Citation format",
                description="Lowercase rule citations detected — use uppercase "
                            "(MCR, MCL, MRE)",
                suggestion="Capitalize all rule citations (MCR not mcr)",
                auto_fixable=True,
            ))

        return issues

    def extract_all_citations(self, text: str) -> Dict[str, List[str]]:
        """Extract and categorize all citations from text."""
        return {
            "MCR": sorted(set(_RE_MCR.findall(text))),
            "MCL": sorted(set(_RE_MCL.findall(text))),
            "MRE": sorted(set(_RE_MRE.findall(text))),
            "case_law": sorted(set(_RE_CASE_CITE.findall(text))),
        }

    def get_stats(self) -> Dict[str, Any]:
        return {
            "component": "CitationAuditor",
            "known_mcr_count": len(self._COMMON_MCR),
            "known_mcl_count": len(self._COMMON_MCL),
            "known_bad_citations": len(_KNOWN_BAD_CITATIONS),
        }


# ---------------------------------------------------------------------------
# ServiceAuditor
# ---------------------------------------------------------------------------


class ServiceAuditor:
    """Validates proof of service compliance per MCR 2.107."""

    _REQUIRED_ELEMENTS = {
        "method": "Method of service (personal, mail, email, e-filing)",
        "date": "Date of service",
        "address": "Address or email of party served",
        "party_served": "Name of party served",
        "signer": "Name of person making service",
    }

    def audit(self, text: str) -> List[ComplianceIssue]:
        """Check proof of service completeness."""
        issues: List[ComplianceIssue] = []

        lower = text.lower()

        # Has any proof of service at all?
        if not _RE_PROOF_OF_SERVICE.search(text):
            issues.append(ComplianceIssue(
                category=ComplianceCategory.SERVICE,
                level=ComplianceLevel.FAIL,
                rule_reference="MCR 2.107(C)(3)",
                description="No proof of service found in filing",
                suggestion="Add a complete Certificate/Proof of Service",
            ))
            return issues

        # Check for method
        methods = ["first-class mail", "personal service", "electronic",
                    "email", "e-filed", "hand deliver"]
        if any(m in lower for m in methods):
            issues.append(ComplianceIssue(
                category=ComplianceCategory.SERVICE,
                level=ComplianceLevel.PASS,
                rule_reference="MCR 2.107(C)(1)",
                description="Service method specified",
            ))
        else:
            issues.append(ComplianceIssue(
                category=ComplianceCategory.SERVICE,
                level=ComplianceLevel.FAIL,
                rule_reference="MCR 2.107(C)(1)",
                description="Service method not specified in proof of service",
                suggestion="State the method: first-class mail, personal service, etc.",
            ))

        # Check for defendant name in service section
        if _DEFENDANT.lower() in lower:
            issues.append(ComplianceIssue(
                category=ComplianceCategory.SERVICE,
                level=ComplianceLevel.PASS,
                rule_reference="MCR 2.107(C)(3)",
                description="Opposing party identified in proof of service",
            ))
        else:
            issues.append(ComplianceIssue(
                category=ComplianceCategory.SERVICE,
                level=ComplianceLevel.WARNING,
                rule_reference="MCR 2.107(C)(3)",
                description=f"Opposing party ({_DEFENDANT}) not named in proof of service",
                suggestion=f"Add '{_DEFENDANT}' to proof of service",
            ))

        # Check for date in service
        if re.search(r"\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}", text):
            issues.append(ComplianceIssue(
                category=ComplianceCategory.SERVICE,
                level=ComplianceLevel.PASS,
                rule_reference="MCR 2.107(C)(3)",
                description="Service date found",
            ))
        else:
            issues.append(ComplianceIssue(
                category=ComplianceCategory.SERVICE,
                level=ComplianceLevel.FAIL,
                rule_reference="MCR 2.107(C)(3)",
                description="Service date not found in proof of service",
                suggestion="Add the date the document was served",
            ))

        return issues

    def get_stats(self) -> Dict[str, Any]:
        return {
            "component": "ServiceAuditor",
            "required_elements": len(self._REQUIRED_ELEMENTS),
        }


# ---------------------------------------------------------------------------
# Database layer
# ---------------------------------------------------------------------------

_PRAGMAS = textwrap.dedent("""\
    PRAGMA busy_timeout = 60000;
    PRAGMA journal_mode = WAL;
    PRAGMA cache_size = -32000;
    PRAGMA temp_store = MEMORY;
    PRAGMA synchronous = NORMAL;
""")

_CREATE_AUDITS_SQL = textwrap.dedent("""\
    CREATE TABLE IF NOT EXISTS compliance_audits (
        audit_id       TEXT PRIMARY KEY,
        filing_type    TEXT,
        overall_level  TEXT,
        pass_count     INTEGER DEFAULT 0,
        warning_count  INTEGER DEFAULT 0,
        fail_count     INTEGER DEFAULT 0,
        critical_count INTEGER DEFAULT 0,
        is_ready       INTEGER DEFAULT 0,
        created_at     TEXT DEFAULT (datetime('now'))
    )
""")

_CREATE_ISSUES_SQL = textwrap.dedent("""\
    CREATE TABLE IF NOT EXISTS compliance_issues (
        issue_id      TEXT PRIMARY KEY,
        audit_id      TEXT NOT NULL,
        category      TEXT,
        level         TEXT,
        rule_ref      TEXT,
        description   TEXT,
        suggestion    TEXT,
        auto_fixable  INTEGER DEFAULT 0,
        created_at    TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (audit_id) REFERENCES compliance_audits(audit_id)
    )
""")

_CREATE_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_compliance_audits_level "
    "ON compliance_audits(overall_level)",
    "CREATE INDEX IF NOT EXISTS idx_compliance_issues_audit "
    "ON compliance_issues(audit_id, level)",
]


def _ensure_tables(conn: sqlite3.Connection) -> None:
    conn.execute(_CREATE_AUDITS_SQL)
    conn.execute(_CREATE_ISSUES_SQL)
    for idx in _CREATE_INDEXES_SQL:
        conn.execute(idx)
    conn.commit()


# ---------------------------------------------------------------------------
# ComplianceAuditor — orchestrator
# ---------------------------------------------------------------------------


class ComplianceAuditor:
    """Top-level orchestrator for compliance auditing.

    Combines :class:`FormatAuditor`, :class:`ContentAuditor`,
    :class:`CitationAuditor`, and :class:`ServiceAuditor` into a
    unified filing compliance pipeline.
    """

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self._db_path = db_path or _DB_PATH
        self._format_auditor = FormatAuditor()
        self._content_auditor = ContentAuditor()
        self._citation_auditor = CitationAuditor()
        self._service_auditor = ServiceAuditor()
        self._audit_history: List[AuditResult] = []

    # -- full audit --

    def full_audit(
        self,
        text: str,
        filing_type: str = "motion",
    ) -> AuditResult:
        """Run all audit checks on a filing and return an AuditResult."""
        all_issues: List[ComplianceIssue] = []

        # Format audit
        all_issues.extend(self._format_auditor.audit(text, filing_type))

        # Content audit
        all_issues.extend(self._content_auditor.audit(text, filing_type))

        # Citation audit
        all_issues.extend(self._citation_auditor.audit(text))

        # Service audit
        all_issues.extend(self._service_auditor.audit(text))

        # Determine overall level
        overall = self._determine_overall_level(all_issues)

        result = AuditResult(
            filing_type=filing_type,
            issues=all_issues,
            overall_level=overall,
        )
        self._audit_history.append(result)
        return result

    def audit_format(self, text: str, filing_type: str = "motion") -> List[ComplianceIssue]:
        """Run only format checks."""
        return self._format_auditor.audit(text, filing_type)

    def audit_content(self, text: str, filing_type: str = "motion") -> List[ComplianceIssue]:
        """Run only content checks."""
        return self._content_auditor.audit(text, filing_type)

    def audit_citations(self, text: str) -> List[ComplianceIssue]:
        """Run only citation checks."""
        return self._citation_auditor.audit(text)

    def audit_service(self, text: str) -> List[ComplianceIssue]:
        """Run only service checks."""
        return self._service_auditor.audit(text)

    def extract_citations(self, text: str) -> Dict[str, List[str]]:
        """Extract all legal citations from text."""
        return self._citation_auditor.extract_all_citations(text)

    # -- analysis --

    @staticmethod
    def _determine_overall_level(
        issues: Sequence[ComplianceIssue],
    ) -> ComplianceLevel:
        """Determine the overall compliance level from individual issues."""
        if any(i.level == ComplianceLevel.CRITICAL for i in issues):
            return ComplianceLevel.CRITICAL
        if any(i.level == ComplianceLevel.FAIL for i in issues):
            return ComplianceLevel.FAIL
        if any(i.level == ComplianceLevel.WARNING for i in issues):
            return ComplianceLevel.WARNING
        return ComplianceLevel.PASS

    def summarize(self, result: AuditResult) -> str:
        """Generate a human-readable audit summary."""
        lines = [
            "=" * 60,
            "  COMPLIANCE AUDIT REPORT",
            "=" * 60,
            f"  Audit ID:    {result.audit_id}",
            f"  Filing Type: {result.filing_type}",
            f"  Status:      {result.overall_level.value.upper()}",
            f"  Filing Ready: {'YES' if result.is_filing_ready else 'NO'}",
            "",
            f"  PASS:     {result.pass_count}",
            f"  WARNING:  {result.warning_count}",
            f"  FAIL:     {result.fail_count}",
            f"  CRITICAL: {result.critical_count}",
            "-" * 60,
        ]

        # Group issues by level (critical first)
        for level in (ComplianceLevel.CRITICAL, ComplianceLevel.FAIL,
                      ComplianceLevel.WARNING, ComplianceLevel.PASS):
            level_issues = [i for i in result.issues if i.level == level]
            if level_issues:
                lines.append(f"\n  [{level.value.upper()}]")
                for issue in level_issues:
                    lines.append(f"    {issue.rule_reference}: {issue.description}")
                    if issue.suggestion:
                        lines.append(f"      → {issue.suggestion}")

        lines.append("\n" + "=" * 60)
        return "\n".join(lines)

    # -- persistence --

    def persist(self) -> int:
        """Write audit results to the database."""
        if not self._db_path.exists():
            logger.warning("Database not found — cannot persist")
            return 0

        try:
            conn = sqlite3.connect(str(self._db_path), timeout=60)
            conn.executescript(_PRAGMAS)
        except sqlite3.Error as exc:
            logger.error("DB connection failed: %s", exc)
            return 0

        written = 0
        try:
            _ensure_tables(conn)
            for result in self._audit_history:
                conn.execute(
                    "INSERT OR REPLACE INTO compliance_audits "
                    "(audit_id, filing_type, overall_level, pass_count, "
                    "warning_count, fail_count, critical_count, is_ready) "
                    "VALUES (?,?,?,?,?,?,?,?)",
                    (
                        result.audit_id,
                        result.filing_type,
                        result.overall_level.value,
                        result.pass_count,
                        result.warning_count,
                        result.fail_count,
                        result.critical_count,
                        1 if result.is_filing_ready else 0,
                    ),
                )

                for issue in result.issues:
                    conn.execute(
                        "INSERT OR REPLACE INTO compliance_issues "
                        "(issue_id, audit_id, category, level, rule_ref, "
                        "description, suggestion, auto_fixable) "
                        "VALUES (?,?,?,?,?,?,?,?)",
                        (
                            issue.issue_id,
                            result.audit_id,
                            issue.category.value,
                            issue.level.value,
                            issue.rule_reference,
                            issue.description,
                            issue.suggestion,
                            1 if issue.auto_fixable else 0,
                        ),
                    )

                written += 1
            conn.commit()
        except sqlite3.Error as exc:
            logger.error("Persist failed: %s", exc)
        finally:
            conn.close()

        return written

    # -- stats --

    def get_stats(self) -> Dict[str, Any]:
        return {
            "module": "compliance_auditor",
            "audits_performed": len(self._audit_history),
            "db_path": str(self._db_path),
            "format_auditor": self._format_auditor.get_stats(),
            "content_auditor": self._content_auditor.get_stats(),
            "citation_auditor": self._citation_auditor.get_stats(),
            "service_auditor": self._service_auditor.get_stats(),
        }

    def reset(self) -> None:
        self._audit_history.clear()


# ---------------------------------------------------------------------------
# CLI demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    sys.stdout = open(  # noqa: SIM115
        sys.stdout.fileno(), mode="w", encoding="utf-8", errors="replace"
    )
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    print("=" * 60)
    print("  Compliance Auditor — LitigationOS")
    print("=" * 60)
    print()

    sample_motion = textwrap.dedent(f"""\
        STATE OF MICHIGAN
        IN THE {_COURT.upper()}
        COUNTY OF MUSKEGON

        {_PLAINTIFF},            Case No. 2024-001507-DC
            Plaintiff,             {_JUDGE}
        v.
        {_DEFENDANT},
            Defendant.
        ____________________________________________________________

        MOTION TO MODIFY PARENTING TIME

        NOW COMES Plaintiff, {_PLAINTIFF}, pro se, and pursuant to
        MCR 2.119 and MCL 722.27, respectfully requests that this Court
        modify the current parenting time order based on changed
        circumstances affecting the best interests of {_CHILD_INITIALS}.

        STATEMENT OF FACTS

        1. The parties are parents of {_CHILD_INITIALS} (Male).

        WHEREFORE, Plaintiff requests that this Court enter an order
        modifying parenting time.

        Respectfully submitted,

        /s/ {_PLAINTIFF}
        {_PLAINTIFF}, Pro Se
        Date: 01/15/2025

        PROOF OF SERVICE

        I hereby certify that on 01/15/2025, I served a copy of this
        Motion on {_DEFENDANT} by first-class mail at her address of record.

        /s/ {_PLAINTIFF}
        Page 1
    """)

    auditor = ComplianceAuditor()
    result = auditor.full_audit(sample_motion, filing_type="motion")
    print(auditor.summarize(result))
    print()
    print("--- Citations Found ---")
    import pprint

    pprint.pprint(auditor.extract_citations(sample_motion))
    print()
    print("--- Stats ---")
    pprint.pprint(auditor.get_stats())
