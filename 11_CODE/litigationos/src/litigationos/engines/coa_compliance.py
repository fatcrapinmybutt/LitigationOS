"""COA Brief Compliance Engine — MCR 7.212 / 7.215 appellate brief checker.

Validates Michigan Court of Appeals briefs against court-rule requirements
including required sections (MCR 7.212(C)), word limits (MCR 7.212(B)),
format rules (MCR 7.215), record-citation discipline, and appendix
completeness (MCR 7.212(H)).  Returns a structured :class:`ComplianceReport`
with per-rule findings, severity, and fix suggestions.

Also provides a COA Forms Registry mapping every commonly-used Court of
Appeals form to its SCAO number, MCR authority, and purpose.

Usage::

    from litigationos.engines.coa_compliance import (
        COAComplianceEngine,
        check_brief_compliance,
        count_words,
        check_record_citations,
        check_standard_of_review,
        get_coa_forms,
    )

    report = check_brief_compliance(brief_text, brief_type="initial")
    print(report.passed, report.score, report.issues)
"""

from __future__ import annotations

import logging
import re
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_CASE_NUMBER = "366810"
_LOWER_COURT = "14th Circuit Court"
_LOWER_COUNTY = "Muskegon County"
_LOWER_CASE = "2024-001507-DC"

# MCR 7.212(B) word limits by brief type
_WORD_LIMITS: dict[str, int] = {
    "initial": 16_000,
    "appellant": 16_000,
    "appellee": 16_000,
    "reply": 8_000,
    "cross-appeal": 16_000,
    "amicus": 8_000,
}

# MCR 7.212(B) page-limit fallback (if word count unavailable)
_PAGE_LIMITS: dict[str, int] = {
    "initial": 50,
    "appellant": 50,
    "appellee": 50,
    "reply": 25,
    "cross-appeal": 50,
    "amicus": 25,
}

# MCR 7.212(C) required brief sections (order matters)
_REQUIRED_SECTIONS: list[dict[str, str]] = [
    {
        "id": "toc",
        "label": "Table of Contents",
        "mcr": "MCR 7.212(C)(1)",
        "pattern": r"(?i)\btable\s+of\s+contents\b",
    },
    {
        "id": "authorities",
        "label": "Index of Authorities",
        "mcr": "MCR 7.212(C)(2)",
        "pattern": r"(?i)\bindex\s+of\s+authorit(?:y|ies)\b",
    },
    {
        "id": "jurisdiction",
        "label": "Jurisdictional Statement",
        "mcr": "MCR 7.212(C)(3)",
        "pattern": r"(?i)\bjurisdict(?:ion(?:al)?)\s+(?:statement|basis)\b|\bstatement\s+of\s+jurisdiction\b",
    },
    {
        "id": "questions",
        "label": "Statement of Questions Presented",
        "mcr": "MCR 7.212(C)(4)",
        "pattern": r"(?i)\bquestions?\s+presented\b|\bissues?\s+presented\b",
    },
    {
        "id": "facts",
        "label": "Statement of Facts",
        "mcr": "MCR 7.212(C)(5)",
        "pattern": r"(?i)\bstatement\s+of\s+facts\b",
    },
    {
        "id": "argument",
        "label": "Argument",
        "mcr": "MCR 7.212(C)(6)",
        "pattern": r"(?i)^[ \t]*(?:I{1,3}V?|V?I{0,3})?\.?\s*ARGUMENT\b",
    },
    {
        "id": "relief",
        "label": "Relief Requested",
        "mcr": "MCR 7.212(C)(7)",
        "pattern": r"(?i)\brelief\s+requested\b|\bconclusion\s+and\s+relief\b|\bprayer\s+for\s+relief\b",
    },
    {
        "id": "signature",
        "label": "Signature Block",
        "mcr": "MCR 7.212(C)(8)",
        "pattern": r"(?i)\brespectfully\s+submitted\b|^[ \t]*/s/\s|\bAndrew\s+(?:James\s+)?Pigors\b",
    },
]

# MCR 7.212(H) appendix requirements
_APPENDIX_ITEMS: list[dict[str, str]] = [
    {
        "id": "decision_appealed",
        "label": "Decision/Order Appealed",
        "mcr": "MCR 7.212(H)(1)",
        "pattern": r"(?i)\border\b.*\bappeal(?:ed)?\b|\bjudgment\b.*\bappeal(?:ed)?\b",
    },
    {
        "id": "register_of_actions",
        "label": "Register of Actions",
        "mcr": "MCR 7.212(H)(2)",
        "pattern": r"(?i)\bregister\s+of\s+actions\b",
    },
    {
        "id": "relevant_docket",
        "label": "Relevant Docket Entries",
        "mcr": "MCR 7.212(H)(3)",
        "pattern": r"(?i)\bdocket\s+entr(?:y|ies)\b",
    },
    {
        "id": "transcript_excerpts",
        "label": "Relevant Transcript Excerpts",
        "mcr": "MCR 7.212(H)(4)",
        "pattern": r"(?i)\btranscript\b",
    },
    {
        "id": "relevant_pleadings",
        "label": "Relevant Pleadings/Documents",
        "mcr": "MCR 7.212(H)(5)",
        "pattern": r"(?i)\bpleading|exhibit|document\b",
    },
]

# MCR 7.212(B) format requirements
_FORMAT_RULES: dict[str, Any] = {
    "paper_size": "8.5 × 11 inches",
    "margins_min_inches": 1.0,
    "font_proportional_min_pt": 14,
    "font_monospaced_min_pt": 12,
    "line_spacing": "double-spaced (body), single-spaced (quotes/footnotes)",
    "page_numbering": "bottom center, beginning after cover page",
    "binding": "saddle-stapled or bound on the left margin",
    "cover_color_appellant": "white",
    "cover_color_appellee": "light blue",
    "cover_color_reply": "light yellow",
    "cover_color_amicus": "light green",
}

# Standard-of-review keywords
_STANDARD_OF_REVIEW_PATTERNS: list[str] = [
    r"(?i)\bstandard\s+of\s+review\b",
    r"(?i)\bde\s+novo\b",
    r"(?i)\babuse\s+of\s+discretion\b",
    r"(?i)\bclear(?:ly)?\s+erroneous\b",
    r"(?i)\bgreat\s+weight\b",
    r"(?i)\bplain\s+error\b",
    r"(?i)\breview(?:ed|able)?\s+for\s+(?:an?\s+)?(?:abuse|errors?)\b",
]

# Record citation pattern — (page, line) or (vol, page) or (Tr at page)
_RECORD_CITE_RE = re.compile(
    r"\("
    r"(?:"
    r"(?:[Tt]r|[Hh]rg)[\s.]+(?:at\s+)?\d+"          # (Tr at 42) or (Hrg. 17)
    r"|(?:\d+[a-z]*\s+)?(?:Tr|Hrg|Ex|R|Doc)\s*\.?\s*"  # (2d Tr. 100)
    r"(?:at\s+)?\d+"
    r"|\d+[a-z]*\s*(?:at|p[p]?\.|pg\.?)\s*\d+"         # (1a at 23) or (pp. 5)
    r"|(?:App(?:x|endix)?|Appx?)[\s.]+\d+"              # (Appx 12)
    r")"
    r"\)"
)

# ---------------------------------------------------------------------------
# COA Forms Registry
# ---------------------------------------------------------------------------

_COA_FORMS_REGISTRY: list[dict[str, str]] = [
    {
        "form_number": "MC 229",
        "name": "Claim of Appeal",
        "mcr": "MCR 7.204(B)",
        "purpose": "Initiates an appeal of right in the Court of Appeals.",
        "filing_fee": "$375.00",
        "deadline": "21 days from entry of order/judgment, or 21 days from denial of post-judgment motion",
    },
    {
        "form_number": "MC 230",
        "name": "Application for Leave to Appeal",
        "mcr": "MCR 7.205(B)",
        "purpose": "Requests discretionary review by the Court of Appeals.",
        "filing_fee": "$375.00",
        "deadline": "21 days from entry of order (no post-judgment motion) or 21 days from denial of motion",
    },
    {
        "form_number": "MC 231",
        "name": "Docketing Statement",
        "mcr": "MCR 7.204(C)",
        "purpose": "Provides case summary, issues, and procedural history to the Court of Appeals.",
        "filing_fee": "None (filed with Claim of Appeal)",
        "deadline": "Filed simultaneously with Claim of Appeal",
    },
    {
        "form_number": "MC 232",
        "name": "Certificate of Compliance",
        "mcr": "MCR 7.212(B)",
        "purpose": "Certifies that a brief complies with word/page limits and formatting rules.",
        "filing_fee": "None",
        "deadline": "Filed with each brief",
    },
    {
        "form_number": "MC 233",
        "name": "Motion in the Court of Appeals",
        "mcr": "MCR 7.211(C)",
        "purpose": "General-purpose motion form for any motion filed in the COA.",
        "filing_fee": "$100.00 (waivable on motion for fee waiver)",
        "deadline": "Varies by motion type",
    },
    {
        "form_number": "MC 234 / Local",
        "name": "Motion for Stay Pending Appeal",
        "mcr": "MCR 7.209",
        "purpose": "Requests the COA to stay the lower-court order while appeal is pending.",
        "filing_fee": "$100.00",
        "deadline": "Any time during appeal; must show trial court denial or explain why not sought",
    },
    {
        "form_number": "MC 233 / Local",
        "name": "Motion for Extension of Time",
        "mcr": "MCR 7.211(C)(6)",
        "purpose": "Requests additional time to file a brief or other document.",
        "filing_fee": "$100.00",
        "deadline": "Before or promptly after the existing deadline",
    },
    {
        "form_number": "MC 233 / Local",
        "name": "Motion for Immediate Consideration",
        "mcr": "MCR 7.211(C)(6)",
        "purpose": "Requests that a pending motion be decided on an expedited basis.",
        "filing_fee": "Included with underlying motion",
        "deadline": "Filed with or after the underlying motion",
    },
    {
        "form_number": "MC 233 / Local",
        "name": "Motion for Peremptory Reversal",
        "mcr": "MCR 7.211(C)(4)",
        "purpose": "Requests reversal without full briefing where error is clear and established.",
        "filing_fee": "$100.00",
        "deadline": "Typically with Claim of Appeal or promptly after",
    },
    {
        "form_number": "MC 233 / Local",
        "name": "Motion to Remand",
        "mcr": "MCR 7.211(C)(7)",
        "purpose": "Requests that the case be sent back to the trial court for further proceedings.",
        "filing_fee": "$100.00",
        "deadline": "Any time during appeal",
    },
    {
        "form_number": "MC 233 / Local",
        "name": "Motion to Expand Record",
        "mcr": "MCR 7.210(A)",
        "purpose": "Requests that additional materials be added to the lower-court record on appeal.",
        "filing_fee": "$100.00",
        "deadline": "Before or with brief filing",
    },
    {
        "form_number": "MC 233 / Local",
        "name": "Emergency Motion for Relief / TRO",
        "mcr": "MCR 7.211(C)(6)",
        "purpose": "Emergency relief from the COA when immediate harm is threatened.",
        "filing_fee": "$100.00",
        "deadline": "Immediately upon emergency",
    },
]


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class Severity(str, Enum):
    """Issue severity levels."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ComplianceIssue(BaseModel):
    """A single compliance finding."""

    rule: str = Field(..., description="MCR rule reference (e.g. 'MCR 7.212(C)(1)')")
    section: str = Field(..., description="Brief section the issue relates to")
    severity: Severity = Field(default=Severity.ERROR)
    message: str = Field(..., description="Human-readable description of the issue")
    fix: str = Field(default="", description="Suggested fix or action")

    model_config = ConfigDict(from_attributes=True)


class SectionStatus(BaseModel):
    """Presence/compliance status of a required brief section."""

    section_id: str
    label: str
    mcr: str
    found: bool = False
    location_hint: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class AppendixItem(BaseModel):
    """Presence status of a required appendix item."""

    item_id: str
    label: str
    mcr: str
    found: bool = False

    model_config = ConfigDict(from_attributes=True)


class FormatCheck(BaseModel):
    """Result of a single format-rule check."""

    rule: str
    description: str
    compliant: Optional[bool] = None
    note: str = ""

    model_config = ConfigDict(from_attributes=True)


class COAFormEntry(BaseModel):
    """Registry entry for a COA form."""

    form_number: str
    name: str
    mcr: str
    purpose: str
    filing_fee: str = ""
    deadline: str = ""

    model_config = ConfigDict(from_attributes=True)


class ComplianceReport(BaseModel):
    """Full MCR 7.212 / 7.215 compliance report for an appellate brief."""

    brief_type: str = Field(..., description="Type of brief checked")
    checked_at: datetime = Field(default_factory=datetime.now)
    word_count: int = Field(default=0, ge=0)
    word_limit: int = Field(default=16_000, ge=0)
    word_count_ok: bool = True
    sections: list[SectionStatus] = Field(default_factory=list)
    appendix_items: list[AppendixItem] = Field(default_factory=list)
    standard_of_review_found: bool = False
    record_citations_missing: list[str] = Field(
        default_factory=list,
        description="Factual sentences in Statement of Facts that lack record citations",
    )
    format_checks: list[FormatCheck] = Field(default_factory=list)
    issues: list[ComplianceIssue] = Field(default_factory=list)
    score: int = Field(default=100, ge=0, le=100)
    passed: bool = True

    model_config = ConfigDict(from_attributes=True)

    # -- convenience properties ------------------------------------------

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.ERROR)

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.WARNING)

    def summary(self) -> str:
        """One-line human-readable summary."""
        status = "PASS" if self.passed else "FAIL"
        return (
            f"[{status}] COA Brief Compliance — {self.brief_type} brief "
            f"| score {self.score}/100 | {self.error_count} errors, "
            f"{self.warning_count} warnings | {self.word_count}/{self.word_limit} words"
        )


# ---------------------------------------------------------------------------
# Core engine
# ---------------------------------------------------------------------------

class COAComplianceEngine:
    """Michigan Court of Appeals brief compliance checker.

    Validates an appellate brief against MCR 7.212 (content requirements)
    and MCR 7.215 (format requirements).  Produces a structured
    :class:`ComplianceReport` with per-rule findings.

    Parameters
    ----------
    case_number : str
        COA docket number (default ``366810``).
    lower_court : str
        Name of the lower court.
    """

    def __init__(
        self,
        case_number: str = _CASE_NUMBER,
        lower_court: str = _LOWER_COURT,
    ) -> None:
        self.case_number = case_number
        self.lower_court = lower_court

    # -- public API -------------------------------------------------------

    def check(self, text: str, brief_type: str = "initial") -> ComplianceReport:
        """Run all compliance checks and return a :class:`ComplianceReport`.

        Parameters
        ----------
        text : str
            Full text of the brief.
        brief_type : str
            One of ``initial``, ``appellant``, ``appellee``, ``reply``,
            ``cross-appeal``, ``amicus``.
        """
        brief_type = brief_type.lower().strip()
        issues: list[ComplianceIssue] = []

        # 1. Word count
        wc = count_words(text)
        wl = _WORD_LIMITS.get(brief_type, 16_000)
        wc_ok = wc <= wl
        if not wc_ok:
            issues.append(ComplianceIssue(
                rule="MCR 7.212(B)",
                section="Certificate of Compliance",
                severity=Severity.ERROR,
                message=f"Word count {wc:,} exceeds {brief_type} brief limit of {wl:,}.",
                fix=f"Reduce brief by at least {wc - wl:,} words or seek leave to file overlength brief.",
            ))

        # 2. Required sections (MCR 7.212(C))
        sections = self._check_sections(text, issues, brief_type)

        # 3. Standard of review
        sor_found = check_standard_of_review(text)
        if not sor_found:
            issues.append(ComplianceIssue(
                rule="MCR 7.212(C)(6)",
                section="Argument",
                severity=Severity.ERROR,
                message="No standard of review identified in the Argument section.",
                fix=(
                    "Add a 'Standard of Review' heading and state the applicable "
                    "standard (de novo, abuse of discretion, clearly erroneous, etc.)."
                ),
            ))

        # 4. Record citations in Statement of Facts
        missing_cites = check_record_citations(text)
        if missing_cites:
            issues.append(ComplianceIssue(
                rule="MCR 7.212(C)(5)",
                section="Statement of Facts",
                severity=Severity.WARNING,
                message=f"{len(missing_cites)} factual statement(s) lack record citations.",
                fix="Add (Tr at __) or (R. __) citations to every factual assertion.",
            ))

        # 5. Appendix (MCR 7.212(H))
        appendix_items = self._check_appendix(text, issues)

        # 6. Format (MCR 7.215 / MCR 7.212(B))
        format_checks = self._check_format(text, issues)

        # 7. Score
        score = self._compute_score(issues, sections, appendix_items, wc_ok, sor_found)
        passed = score >= 80 and not any(i.severity == Severity.ERROR for i in issues)

        report = ComplianceReport(
            brief_type=brief_type,
            word_count=wc,
            word_limit=wl,
            word_count_ok=wc_ok,
            sections=sections,
            appendix_items=appendix_items,
            standard_of_review_found=sor_found,
            record_citations_missing=missing_cites,
            format_checks=format_checks,
            issues=issues,
            score=score,
            passed=passed,
        )
        logger.info("COA compliance check: %s", report.summary())
        return report

    # -- section checks ---------------------------------------------------

    def _check_sections(
        self,
        text: str,
        issues: list[ComplianceIssue],
        brief_type: str,
    ) -> list[SectionStatus]:
        """Check presence of every MCR 7.212(C) required section."""
        results: list[SectionStatus] = []
        # Reply briefs don't require all sections
        skip_for_reply = {"toc", "authorities", "jurisdiction", "facts"}

        for sec in _REQUIRED_SECTIONS:
            is_reply = brief_type in ("reply", "amicus")
            if is_reply and sec["id"] in skip_for_reply:
                results.append(SectionStatus(
                    section_id=sec["id"],
                    label=sec["label"],
                    mcr=sec["mcr"],
                    found=True,
                    location_hint="Not required for reply/amicus briefs",
                ))
                continue

            match = re.search(sec["pattern"], text, re.MULTILINE)
            found = match is not None
            hint = None
            if match:
                # Report approximate location as line number
                line_no = text[:match.start()].count("\n") + 1
                hint = f"~line {line_no}"

            results.append(SectionStatus(
                section_id=sec["id"],
                label=sec["label"],
                mcr=sec["mcr"],
                found=found,
                location_hint=hint,
            ))

            if not found:
                issues.append(ComplianceIssue(
                    rule=sec["mcr"],
                    section=sec["label"],
                    severity=Severity.ERROR,
                    message=f"Required section '{sec['label']}' not found.",
                    fix=f"Add a '{sec['label']}' heading per {sec['mcr']}.",
                ))

        return results

    # -- appendix checks --------------------------------------------------

    def _check_appendix(
        self,
        text: str,
        issues: list[ComplianceIssue],
    ) -> list[AppendixItem]:
        """Check presence of required appendix items per MCR 7.212(H)."""
        # Locate the appendix portion (everything after "APPENDIX" heading)
        appendix_match = re.search(
            r"(?i)^[ \t]*APPENDIX\b", text, re.MULTILINE,
        )
        appendix_text = text[appendix_match.start():] if appendix_match else ""

        results: list[AppendixItem] = []
        has_appendix = bool(appendix_match)

        if not has_appendix:
            issues.append(ComplianceIssue(
                rule="MCR 7.212(H)",
                section="Appendix",
                severity=Severity.WARNING,
                message="No 'APPENDIX' section found in the brief.",
                fix=(
                    "Add an Appendix containing the decision appealed, "
                    "register of actions, and relevant transcript excerpts "
                    "per MCR 7.212(H)."
                ),
            ))

        for item in _APPENDIX_ITEMS:
            # Search in the appendix section if found, else entire text
            search_text = appendix_text if has_appendix else text
            found = bool(re.search(item["pattern"], search_text))
            results.append(AppendixItem(
                item_id=item["id"],
                label=item["label"],
                mcr=item["mcr"],
                found=found,
            ))
            if not found and has_appendix:
                issues.append(ComplianceIssue(
                    rule=item["mcr"],
                    section="Appendix",
                    severity=Severity.INFO,
                    message=f"Appendix item '{item['label']}' not detected.",
                    fix=f"Ensure {item['label']} is included per {item['mcr']}.",
                ))

        return results

    # -- format checks ----------------------------------------------------

    def _check_format(
        self,
        text: str,
        issues: list[ComplianceIssue],
    ) -> list[FormatCheck]:
        """Check MCR 7.212(B) / 7.215 format requirements.

        Because this engine works from plain text (not PDF metadata),
        some checks are heuristic or informational only.
        """
        checks: list[FormatCheck] = []

        # Page numbering hint — look for page-number-like patterns
        page_nums = re.findall(r"(?m)^\s*-?\s*\d+\s*-?\s*$", text)
        checks.append(FormatCheck(
            rule="MCR 7.212(B)",
            description="Page numbering (bottom center, consecutive)",
            compliant=len(page_nums) > 0 if page_nums else None,
            note=f"Detected {len(page_nums)} standalone number line(s) that may be page numbers."
                 if page_nums else "Cannot verify page numbering from plain text.",
        ))

        # Font size — heuristic: look for metadata or assume text-only
        checks.append(FormatCheck(
            rule="MCR 7.212(B)",
            description="Font: ≥14pt proportional or ≥12pt monospaced",
            compliant=None,
            note="Font size cannot be verified from plain text. Ensure compliance in final PDF.",
        ))

        # Margins
        checks.append(FormatCheck(
            rule="MCR 7.212(B)",
            description="Margins: ≥1 inch on all sides",
            compliant=None,
            note="Margin compliance requires PDF inspection. Ensure ≥1\" margins in final document.",
        ))

        # Paper size
        checks.append(FormatCheck(
            rule="MCR 7.212(B)",
            description="Paper: 8.5 × 11 inches",
            compliant=None,
            note="Paper size requires PDF inspection.",
        ))

        # Double spacing — look for excessive single-line blocks
        lines = text.split("\n")
        non_empty = [l for l in lines if l.strip()]
        blank_ratio = 1 - (len(non_empty) / max(len(lines), 1))
        double_spaced = blank_ratio > 0.25
        checks.append(FormatCheck(
            rule="MCR 7.212(B)",
            description="Double-spacing (body text)",
            compliant=double_spaced if lines else None,
            note=(
                f"Blank-line ratio: {blank_ratio:.0%}. "
                "Appears double-spaced." if double_spaced
                else f"Blank-line ratio: {blank_ratio:.0%}. "
                "May not be double-spaced — verify in formatted document."
            ),
        ))
        if not double_spaced and lines:
            issues.append(ComplianceIssue(
                rule="MCR 7.212(B)",
                section="Format",
                severity=Severity.WARNING,
                message="Brief text may not be double-spaced.",
                fix="Ensure body text is double-spaced per MCR 7.212(B).",
            ))

        # Binding
        checks.append(FormatCheck(
            rule="MCR 7.212(B)",
            description="Binding: saddle-stapled or bound on left margin",
            compliant=None,
            note="Binding cannot be verified from text. Ensure left-margin binding for hard copies.",
        ))

        return checks

    # -- scoring ----------------------------------------------------------

    @staticmethod
    def _compute_score(
        issues: list[ComplianceIssue],
        sections: list[SectionStatus],
        appendix_items: list[AppendixItem],
        word_count_ok: bool,
        sor_found: bool,
    ) -> int:
        """Compute a 0–100 compliance score.

        Scoring:
        - Start at 100
        - -10 per missing required section (ERROR)
        - -15 for word-count violation
        - -10 for missing standard of review
        - -3 per missing appendix item
        - -2 per WARNING issue
        """
        score = 100

        missing_sections = sum(1 for s in sections if not s.found)
        score -= missing_sections * 10

        if not word_count_ok:
            score -= 15

        if not sor_found:
            score -= 10

        missing_appendix = sum(1 for a in appendix_items if not a.found)
        score -= missing_appendix * 3

        warning_count = sum(
            1 for i in issues
            if i.severity == Severity.WARNING
        )
        score -= warning_count * 2

        return max(0, min(100, score))


# ---------------------------------------------------------------------------
# Module-level convenience functions
# ---------------------------------------------------------------------------

def check_brief_compliance(
    text: str,
    brief_type: str = "initial",
    case_number: str = _CASE_NUMBER,
) -> ComplianceReport:
    """Check an appellate brief for MCR 7.212 / 7.215 compliance.

    Parameters
    ----------
    text : str
        Full text of the brief.
    brief_type : str
        One of ``initial``, ``appellant``, ``appellee``, ``reply``,
        ``cross-appeal``, ``amicus``.
    case_number : str
        COA docket number.

    Returns
    -------
    ComplianceReport
        Structured compliance report with issues, score, and pass/fail.
    """
    engine = COAComplianceEngine(case_number=case_number)
    return engine.check(text, brief_type=brief_type)


def count_words(text: str) -> int:
    """Count words in brief text, excluding common headers and captions.

    Strips table-of-contents lines, page numbers, header/footer
    repetitions, and caption blocks before counting.  Matches the
    methodology expected by MCR 7.212(B) Certificate of Compliance.

    Parameters
    ----------
    text : str
        Full brief text.

    Returns
    -------
    int
        Word count.
    """
    if not text or not text.strip():
        return 0

    lines = text.split("\n")
    filtered: list[str] = []

    for line in lines:
        stripped = line.strip()

        # Skip blank lines
        if not stripped:
            continue

        # Skip standalone page numbers
        if re.match(r"^-?\s*\d+\s*-?$", stripped):
            continue

        # Skip TOC dot-leader lines (e.g., "Table of Contents ....... ii")
        if re.match(r"^.{3,}\s*\.{4,}\s*\w+$", stripped):
            continue

        # Skip repeated caption/header lines (all-caps, short)
        if stripped.isupper() and len(stripped.split()) <= 8:
            continue

        # Skip common footer/header patterns
        if re.match(
            r"^(?:(?:Appellant|Appellee|Reply)\s+Brief"
            r"|Case\s+No\.?\s*\d+"
            r"|COA\s+(?:No\.?|Docket)\s*\d+)",
            stripped,
            re.IGNORECASE,
        ):
            continue

        filtered.append(stripped)

    body = " ".join(filtered)
    words = body.split()
    return len(words)


def check_record_citations(text: str) -> list[str]:
    """Find factual statements in Statement of Facts lacking record citations.

    Extracts the Statement-of-Facts section, splits into sentences, and
    flags any sentence that asserts a fact but lacks a parenthetical
    record citation such as ``(Tr at 42)`` or ``(R. 23)``.

    Parameters
    ----------
    text : str
        Full brief text.

    Returns
    -------
    list[str]
        Sentences that appear to lack record citations.
    """
    # Extract Statement of Facts section
    sof_start = re.search(
        r"(?i)\bstatement\s+of\s+facts\b", text,
    )
    if not sof_start:
        return []

    # Find the end — next major section heading
    sof_text_after = text[sof_start.end():]
    next_section = re.search(
        r"(?im)^[ \t]*(?:"
        r"(?:I{1,3}V?|V?I{0,3})\.?\s+)?(?:ARGUMENT|STANDARD|RELIEF|CONCLUSION)\b",
        sof_text_after,
    )
    sof_body = sof_text_after[:next_section.start()] if next_section else sof_text_after

    # Split into sentences
    sentences = re.split(r"(?<=[.!?])\s+", sof_body.strip())

    missing: list[str] = []
    for sent in sentences:
        sent = sent.strip()
        if not sent or len(sent.split()) < 4:
            continue

        # Skip headings and non-factual lines
        if sent.isupper() or sent.startswith("#"):
            continue

        # Check for record citation
        if not _RECORD_CITE_RE.search(sent):
            missing.append(sent)

    return missing


def check_standard_of_review(text: str) -> bool:
    """Check whether the brief states a standard of review.

    Parameters
    ----------
    text : str
        Full brief text.

    Returns
    -------
    bool
        ``True`` if a standard-of-review statement is found.
    """
    for pattern in _STANDARD_OF_REVIEW_PATTERNS:
        if re.search(pattern, text):
            return True
    return False


def get_coa_forms() -> dict[str, list[COAFormEntry]]:
    """Return the COA Forms Registry organized by category.

    Returns
    -------
    dict[str, list[COAFormEntry]]
        Keys are category names (``"appeals"``, ``"motions"``,
        ``"compliance"``); values are lists of :class:`COAFormEntry`.
    """
    entries = [COAFormEntry(**f) for f in _COA_FORMS_REGISTRY]

    registry: dict[str, list[COAFormEntry]] = {
        "appeals": [],
        "motions": [],
        "compliance": [],
    }

    for entry in entries:
        name_lower = entry.name.lower()
        if "motion" in name_lower or "emergency" in name_lower:
            registry["motions"].append(entry)
        elif "certificate" in name_lower or "compliance" in name_lower:
            registry["compliance"].append(entry)
        else:
            registry["appeals"].append(entry)

    return registry


def get_format_rules() -> dict[str, Any]:
    """Return the MCR 7.212(B) / 7.215 format requirements dictionary.

    Returns
    -------
    dict[str, Any]
        Format rules keyed by rule name.
    """
    return dict(_FORMAT_RULES)
