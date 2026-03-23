"""Michigan Court of Appeals Filing Form Library.

Generates court-ready COA filings including claims of appeal, leave
applications, docketing statements, appellate briefs, motions, and
appendices.  Every document follows MCR 7.201–7.219 requirements with
proper captions, signature blocks, and certificates of service.

Usage::

    lib = COAFormLibrary()
    types = lib.list_filing_types()
    claim = lib.generate_claim_of_appeal(case_info, issues)
    brief = lib.generate_brief("appellant_brief", case_info, issues, arguments)
    validation = lib.validate_brief(brief.full_text)
    deadlines = lib.calculate_deadlines(date(2025, 3, 15))
"""

from __future__ import annotations

import logging
import re
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Verified party identity — SINGLE SOURCE OF TRUTH (never fabricate)
# ---------------------------------------------------------------------------

PARTIES: dict[str, dict[str, str]] = {
    "appellant": {
        "name": "Andrew James Pigors",
        "address": "1977 Whitehall Road, Lot 17\nNorth Muskegon, MI 49445",
        "phone": "(231) 903-5690",
        "email": "andrewjpigors@gmail.com",
        "status": "Pro Se Appellant",
    },
    "appellee": {
        "name": "Emily A. Watson",
        "address": "2160 Garland Drive\nNorton Shores, MI 49441",
    },
    "lower_court_judge": {
        "name": "Hon. Jenny L. McNeill",
        "court": "14th Circuit Court, Family Division",
        "county": "Muskegon",
    },
    "child": {
        "initials": "L.D.W.",
    },
}

LOWER_COURT_CASE_NUMBER = "2024-001507-DC"
COA_CASE_NUMBER = "366810"
LOWER_COURT_NAME = "14th Circuit Court"
LOWER_COURT_COUNTY = "Muskegon County"
LOWER_COURT_DIVISION = "Family Division"
COA_COURT_NAME = "Michigan Court of Appeals"

# ---------------------------------------------------------------------------
# Brief format constants — MCR 7.212
# ---------------------------------------------------------------------------

BRIEF_PAGE_LIMIT = 50
BRIEF_FONT_PT = 12
BRIEF_LINE_SPACING = "double"
BRIEF_MARGINS_INCHES = 1.0

MCR_7212_REQUIRED_SECTIONS = [
    "Table of Contents",
    "Index of Authorities",
    "Statement of Jurisdiction",
    "Statement of Questions Presented",
    "Statement of Facts",
    "Argument",
    "Relief Requested",
]


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class COAFilingType(BaseModel):
    """Metadata for a COA filing type."""

    name: str
    mcr_rule: str
    deadline_days: Optional[int] = None
    deadline_description: str = ""
    required_docs: list[str] = Field(default_factory=list)
    filing_fee: str = "$0.00"
    description: str = ""
    scao_form: Optional[str] = None

    model_config = ConfigDict(frozen=True)


class COACaseInfo(BaseModel):
    """Case identification for COA filing generation."""

    lower_court_case_number: str = LOWER_COURT_CASE_NUMBER
    coa_case_number: Optional[str] = COA_CASE_NUMBER
    appellant: str = "Andrew James Pigors"
    appellee: str = "Emily A. Watson"
    lower_court_judge: str = "Hon. Jenny L. McNeill"
    lower_court: str = LOWER_COURT_NAME
    lower_court_county: str = LOWER_COURT_COUNTY
    lower_court_division: str = LOWER_COURT_DIVISION
    child_initials: str = "L.D.W."

    model_config = ConfigDict(frozen=True)


class COADeadline(BaseModel):
    """A calculated appellate deadline."""

    filing_type: str
    trigger_date: date
    deadline_date: date
    days_remaining: int
    is_expired: bool
    mcr_rule: str = ""
    description: str = ""

    model_config = ConfigDict(frozen=True)


class BriefSection(BaseModel):
    """A single section of an appellate brief."""

    heading: str
    content: str
    standard_of_review: Optional[str] = None

    model_config = ConfigDict(frozen=True)


class COABrief(BaseModel):
    """A complete appellate brief per MCR 7.212."""

    brief_type: str
    case_info: COACaseInfo
    caption: str
    table_of_contents: str
    index_of_authorities: str
    statement_of_jurisdiction: str
    statement_of_questions: str
    statement_of_facts: str
    arguments: list[BriefSection] = Field(default_factory=list)
    relief_requested: str
    signature_block: str
    certificate_of_service: str
    appendix_contents: list[str] = Field(default_factory=list)
    generated_at: str = Field(default_factory=lambda: datetime.now().isoformat())

    model_config = ConfigDict(from_attributes=True)

    @property
    def full_text(self) -> str:
        """Return the full brief as a single string."""
        parts = [self.caption, ""]
        parts.append("## TABLE OF CONTENTS\n")
        parts.append(self.table_of_contents)
        parts.append("")
        parts.append("## INDEX OF AUTHORITIES\n")
        parts.append(self.index_of_authorities)
        parts.append("")
        parts.append("## STATEMENT OF JURISDICTION\n")
        parts.append(self.statement_of_jurisdiction)
        parts.append("")
        parts.append("## STATEMENT OF QUESTIONS PRESENTED\n")
        parts.append(self.statement_of_questions)
        parts.append("")
        parts.append("## STATEMENT OF FACTS\n")
        parts.append(self.statement_of_facts)
        parts.append("")
        for arg in self.arguments:
            parts.append(f"## ARGUMENT: {arg.heading.upper()}\n")
            if arg.standard_of_review:
                parts.append(f"**Standard of Review:** {arg.standard_of_review}\n")
            parts.append(arg.content)
            parts.append("")
        parts.append("## RELIEF REQUESTED\n")
        parts.append(self.relief_requested)
        parts.append("")
        parts.append(self.signature_block)
        parts.append("")
        parts.append(self.certificate_of_service)
        return "\n".join(parts)


class COAMotion(BaseModel):
    """A COA motion document."""

    motion_type: str
    case_info: COACaseInfo
    caption: str
    body_sections: dict[str, str]
    relief_requested: list[str]
    signature_block: str
    certificate_of_service: str
    generated_at: str = Field(default_factory=lambda: datetime.now().isoformat())

    model_config = ConfigDict(from_attributes=True)

    @property
    def full_text(self) -> str:
        """Return the full motion as a single string."""
        parts = [self.caption, ""]
        for heading, content in self.body_sections.items():
            parts.append(f"## {heading.upper()}")
            parts.append(content)
            parts.append("")
        if self.relief_requested:
            parts.append("## RELIEF REQUESTED\n")
            for i, item in enumerate(self.relief_requested, 1):
                parts.append(f"{i}. {item}")
            parts.append("")
        parts.append(self.signature_block)
        parts.append("")
        parts.append(self.certificate_of_service)
        return "\n".join(parts)


class COADocument(BaseModel):
    """A generic COA filing document (claim, leave app, docketing statement)."""

    document_type: str
    case_info: COACaseInfo
    caption: str
    body_sections: dict[str, str]
    signature_block: str
    certificate_of_service: str
    scao_form: Optional[str] = None
    generated_at: str = Field(default_factory=lambda: datetime.now().isoformat())

    model_config = ConfigDict(from_attributes=True)

    @property
    def full_text(self) -> str:
        """Return the full document as a single string."""
        parts = [self.caption, ""]
        for heading, content in self.body_sections.items():
            parts.append(f"## {heading.upper()}")
            parts.append(content)
            parts.append("")
        parts.append(self.signature_block)
        parts.append("")
        parts.append(self.certificate_of_service)
        return "\n".join(parts)


class BriefValidation(BaseModel):
    """Results from validating a brief against MCR 7.212."""

    is_compliant: bool
    page_count: int = 0
    issues: list[str] = Field(default_factory=list)
    mcr_7212_checklist: dict[str, bool] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


class AppendixItem(BaseModel):
    """An item in the required appendix."""

    label: str
    description: str
    required: bool = True

    model_config = ConfigDict(frozen=True)


# ---------------------------------------------------------------------------
# Filing type registry — Michigan Court of Appeals
# ---------------------------------------------------------------------------

FILING_TYPES: dict[str, COAFilingType] = {
    "claim_of_appeal": COAFilingType(
        name="Claim of Appeal",
        mcr_rule="MCR 7.204",
        deadline_days=21,
        deadline_description="21 days from entry of order or judgment appealed",
        required_docs=[
            "Claim of Appeal (MC 229)",
            "Docketing Statement (MC 231)",
            "Copy of order/judgment appealed",
            "Proof of service on all parties",
            "Filing fee ($375.00) or fee waiver",
            "Lower court register of actions",
        ],
        filing_fee="$375.00",
        description=(
            "Appeal of right from a final order or judgment.  Must be filed "
            "within 21 days of entry of the order or judgment.  MCR 7.204 "
            "requires simultaneous filing of the docketing statement and "
            "payment of the filing fee."
        ),
        scao_form="MC 229",
    ),
    "leave_to_appeal": COAFilingType(
        name="Application for Leave to Appeal",
        mcr_rule="MCR 7.205",
        deadline_days=182,
        deadline_description="6 months from entry of order appealed",
        required_docs=[
            "Application for Leave to Appeal (MC 230)",
            "Docketing Statement (MC 231)",
            "Copy of order appealed",
            "Supporting brief",
            "Proof of service on all parties",
            "Filing fee ($375.00) or fee waiver",
            "Lower court register of actions",
        ],
        filing_fee="$375.00",
        description=(
            "Discretionary appeal from an interlocutory order or an order "
            "where appeal of right is unavailable.  The application must "
            "demonstrate that the issues are meritorious and that immediate "
            "review is appropriate."
        ),
        scao_form="MC 230",
    ),
    "interlocutory_appeal": COAFilingType(
        name="Interlocutory Appeal",
        mcr_rule="MCR 7.205(B)",
        deadline_days=182,
        deadline_description="6 months from entry of interlocutory order",
        required_docs=[
            "Application for Leave to Appeal (MC 230)",
            "Docketing Statement (MC 231)",
            "Copy of interlocutory order",
            "Brief in support",
            "Proof of service on all parties",
            "Filing fee ($375.00) or fee waiver",
        ],
        filing_fee="$375.00",
        description=(
            "Appeal from an interlocutory order that does not resolve all "
            "claims.  Filed as an application for leave under MCR 7.205(B).  "
            "Must show that delay would cause irreparable harm or that the "
            "issue involves a controlling question of law."
        ),
        scao_form="MC 230",
    ),
    "emergency_application": COAFilingType(
        name="Emergency Application for Leave to Appeal",
        mcr_rule="MCR 7.205(F)",
        deadline_days=None,
        deadline_description="No fixed deadline — filed when emergency exists",
        required_docs=[
            "Emergency Application for Leave to Appeal",
            "Affidavit explaining emergency",
            "Brief in support",
            "Copy of order appealed",
            "Proof of service on all parties",
            "Proposed order",
            "Filing fee ($375.00) or fee waiver",
        ],
        filing_fee="$375.00",
        description=(
            "Emergency appeal requiring immediate relief.  Must demonstrate "
            "that the normal appellate process would result in irreparable "
            "harm.  MCR 7.205(F) requires a showing of immediate and "
            "irreparable injury."
        ),
    ),
    "motion_to_stay": COAFilingType(
        name="Motion to Stay Proceedings Pending Appeal",
        mcr_rule="MCR 7.209",
        deadline_days=None,
        deadline_description="Filed after claim/leave filed; no fixed deadline",
        required_docs=[
            "Motion to Stay",
            "Brief in support",
            "Proof that stay was sought in lower court (or explanation why not)",
            "Copy of order appealed",
            "Proof of service on all parties",
        ],
        filing_fee="$0.00",
        description=(
            "Motion to stay enforcement of the lower court order pending "
            "appeal.  Under MCR 7.209, the movant must show: (1) likelihood "
            "of success on the merits, (2) irreparable harm without stay, "
            "(3) no substantial harm to opposing party, and (4) public "
            "interest favors the stay."
        ),
    ),
    "motion_for_peremptory_reversal": COAFilingType(
        name="Motion for Peremptory Reversal",
        mcr_rule="MCR 7.211(C)(4)",
        deadline_days=None,
        deadline_description="Filed with or after claim/leave; no fixed deadline",
        required_docs=[
            "Motion for Peremptory Reversal",
            "Brief in support demonstrating clear error",
            "Copy of order or judgment below",
            "Relevant portions of lower court record",
            "Proof of service on all parties",
        ],
        filing_fee="$0.00",
        description=(
            "Requests reversal without full briefing where the lower court's "
            "error is so clear that oral argument and further briefing are "
            "unnecessary.  MCR 7.211(C)(4) allows peremptory disposition "
            "when the result is 'so clear that full briefing would be a "
            "waste of judicial resources.'"
        ),
    ),
    "superintending_control": COAFilingType(
        name="Complaint for Superintending Control",
        mcr_rule="MCR 7.206",
        deadline_days=None,
        deadline_description="No fixed deadline — filed when extraordinary relief needed",
        required_docs=[
            "Complaint for Superintending Control",
            "Brief in support",
            "All relevant lower court orders",
            "Evidence of lower court's failure to act or clear error",
            "Proof of service on all parties and lower court",
        ],
        filing_fee="$375.00",
        description=(
            "Extraordinary writ directing a lower court to perform or cease "
            "a specific act.  MCR 7.206 requires showing that (1) the lower "
            "court has committed a clear legal error, (2) no adequate "
            "alternative remedy exists, and (3) the damage or injustice "
            "resulting is serious and irreparable."
        ),
    ),
    "appellant_brief": COAFilingType(
        name="Appellant's Brief",
        mcr_rule="MCR 7.212",
        deadline_days=56,
        deadline_description="56 days after claim of appeal or order granting leave",
        required_docs=[
            "Appellant's Brief (original + copies)",
            "Appendix with required items per MCR 7.212(H)",
            "Proof of service on all parties",
        ],
        filing_fee="$0.00",
        description=(
            "Main appellate brief filed by the appellant.  Must comply with "
            "MCR 7.212 format requirements: 50-page limit, 12-point "
            "proportional font, double-spaced, with all required sections "
            "including Table of Contents, Index of Authorities, Statement "
            "of Jurisdiction, Questions Presented, Statement of Facts, "
            "Argument, and Relief Requested."
        ),
    ),
    "reply_brief": COAFilingType(
        name="Reply Brief",
        mcr_rule="MCR 7.212(G)",
        deadline_days=21,
        deadline_description="21 days after appellee's brief is served",
        required_docs=[
            "Reply Brief (original + copies)",
            "Proof of service on all parties",
        ],
        filing_fee="$0.00",
        description=(
            "Optional reply brief addressing arguments raised in the "
            "appellee's brief.  Must be limited to rebuttal of new issues "
            "raised by appellee.  Subject to same MCR 7.212 format "
            "requirements.  Cannot raise new issues not presented in "
            "appellant's brief."
        ),
    ),
}


# ---------------------------------------------------------------------------
# Standard of review definitions
# ---------------------------------------------------------------------------

STANDARDS_OF_REVIEW: dict[str, str] = {
    "de_novo": (
        "Questions of law, including constitutional issues and the "
        "interpretation of court rules and statutes, are reviewed de novo. "
        "Maldonado v Ford Motor Co, 476 Mich 372, 388 (2006)."
    ),
    "abuse_of_discretion": (
        "A trial court's decision is reviewed for an abuse of discretion. "
        "An abuse of discretion occurs when the trial court's decision falls "
        "outside the range of principled outcomes. Maldonado v Ford Motor Co, "
        "476 Mich 372, 388 (2006)."
    ),
    "clear_error": (
        "Findings of fact are reviewed for clear error. A finding is clearly "
        "erroneous when, although there is evidence to support it, the "
        "reviewing court is left with the definite and firm conviction that a "
        "mistake has been made. MCR 2.613(C)."
    ),
    "great_weight": (
        "Custody determinations and best-interest findings are reviewed "
        "under the great weight of the evidence standard. The court will not "
        "reverse unless the evidence clearly preponderates in the opposite "
        "direction. Vodvarka v Grasmeyer, 259 Mich App 499, 508 (2003)."
    ),
}


# ---------------------------------------------------------------------------
# Appendix requirements — MCR 7.212(H)
# ---------------------------------------------------------------------------

REQUIRED_APPENDIX_ITEMS: list[AppendixItem] = [
    AppendixItem(
        label="a",
        description="Register of actions from the lower court/tribunal",
    ),
    AppendixItem(
        label="b",
        description=(
            "The order or judgment appealed from and any opinion or "
            "findings of the trial court or tribunal"
        ),
    ),
    AppendixItem(
        label="c",
        description="Any pleading, proof, or other item that is the subject of the appeal",
    ),
    AppendixItem(
        label="d",
        description="Any other document or part of the record cited in the brief",
        required=False,
    ),
]


# ---------------------------------------------------------------------------
# Document generation helpers
# ---------------------------------------------------------------------------


def _coa_caption(case_info: COACaseInfo, document_title: str) -> str:
    """Build a standard COA-format caption block."""
    coa_num = case_info.coa_case_number or "[TO BE ASSIGNED]"
    lines = [
        "=" * 65,
        f"  {COA_COURT_NAME.upper()}",
        "=" * 65,
        "",
        f"  {case_info.appellant},",
        f"      {PARTIES['appellant']['status']},",
        "",
        f"          v                        COA Case No. {coa_num}",
        f"                                   LC Case No.  {case_info.lower_court_case_number}",
        "",
        f"  {case_info.appellee},",
        "      Appellee.",
        "",
        "-" * 65,
        f"Lower Court: {case_info.lower_court}, {case_info.lower_court_division}",
        f"Lower Court Judge: {case_info.lower_court_judge}",
        "-" * 65,
        "",
        f"  {document_title.upper()}",
        "",
    ]
    return "\n".join(lines)


def _signature_block() -> str:
    """Standard pro se appellant signature block."""
    p = PARTIES["appellant"]
    return (
        "Respectfully submitted,\n\n"
        "____________________________________\n"
        f"{p['name']}\n"
        f"{p['status']}\n"
        f"{p['address']}\n"
        f"Phone: {p['phone']}\n"
        f"Email: {p['email']}\n"
        f"Date: {date.today().isoformat()}"
    )


def _certificate_of_service(case_info: COACaseInfo) -> str:
    """Certificate of service for COA filings."""
    appellee = PARTIES["appellee"]
    return (
        "CERTIFICATE OF SERVICE\n\n"
        f"I, {PARTIES['appellant']['name']}, certify that on "
        f"{date.today().strftime('%B %d, %Y')}, I served a copy of this "
        "document on the following by first-class mail, postage prepaid:\n\n"
        f"  {appellee['name']}\n"
        f"  {appellee['address']}\n\n"
        "____________________________________\n"
        f"{PARTIES['appellant']['name']}"
    )


def _is_business_day(d: date) -> bool:
    """Check if a date is a weekday (not Saturday/Sunday)."""
    return d.weekday() < 5


def _next_business_day(d: date) -> date:
    """Advance to next Monday if date falls on weekend."""
    while not _is_business_day(d):
        d += timedelta(days=1)
    return d


# ---------------------------------------------------------------------------
# COAFormLibrary — main engine class
# ---------------------------------------------------------------------------


class COAFormLibrary:
    """Michigan Court of Appeals Filing Form Library.

    Pure-logic engine that generates COA filings, briefs, motions, and
    supporting documents per MCR 7.201–7.219.  No database dependency.
    """

    def list_filing_types(self) -> list[dict[str, Any]]:
        """Return all available COA filing types with metadata.

        Returns a list of dicts, each containing the filing type key and
        all metadata fields from the :class:`COAFilingType` model.
        """
        result = []
        for key, ft in FILING_TYPES.items():
            entry = ft.model_dump()
            entry["key"] = key
            result.append(entry)
        return result

    # -- Core filing generators -----------------------------------------------

    def generate_claim_of_appeal(
        self,
        case_info: COACaseInfo | None = None,
        issues: list[str] | None = None,
        order_date: str | None = None,
    ) -> COADocument:
        """Generate a Claim of Appeal (SCAO MC 229).

        Parameters
        ----------
        case_info:
            Case identification; uses defaults if *None*.
        issues:
            List of issues/errors being appealed.
        order_date:
            Date of the lower court order being appealed (YYYY-MM-DD).
        """
        ci = case_info or COACaseInfo()
        issue_list = issues or ["[Issues to be identified]"]
        caption = _coa_caption(ci, "Claim of Appeal")

        body: dict[str, str] = {}
        body["Basis for Jurisdiction"] = (
            "This Court has jurisdiction under MCR 7.203(A) and MCR 7.204.  "
            f"The appeal is from a final order entered in {ci.lower_court}, "
            f"{ci.lower_court_division}, {ci.lower_court_county}, "
            f"Case No. {ci.lower_court_case_number}, by "
            f"{ci.lower_court_judge}."
        )
        if order_date:
            body["Order Appealed"] = (
                f"Appellant appeals the order entered on {order_date} by "
                f"{ci.lower_court_judge} in the above-captioned case."
            )
        else:
            body["Order Appealed"] = (
                "Appellant appeals the order entered by "
                f"{ci.lower_court_judge} in the above-captioned case."
            )

        issues_text = "\n".join(
            f"{i}. {issue}" for i, issue in enumerate(issue_list, 1)
        )
        body["Issues on Appeal"] = (
            "Appellant identifies the following issues for appeal:\n\n"
            + issues_text
        )
        body["Relief Sought"] = (
            "Appellant requests that this Court reverse the order of the "
            "lower court and grant such further relief as is just and proper."
        )

        logger.info("Generated Claim of Appeal for %s", ci.lower_court_case_number)
        return COADocument(
            document_type="claim_of_appeal",
            case_info=ci,
            caption=caption,
            body_sections=body,
            signature_block=_signature_block(),
            certificate_of_service=_certificate_of_service(ci),
            scao_form="MC 229",
        )

    def generate_leave_application(
        self,
        case_info: COACaseInfo | None = None,
        issues: list[str] | None = None,
        why_leave: str = "",
    ) -> COADocument:
        """Generate an Application for Leave to Appeal (SCAO MC 230).

        Parameters
        ----------
        case_info:
            Case identification; uses defaults if *None*.
        issues:
            Issues presented for review.
        why_leave:
            Explanation of why leave should be granted.
        """
        ci = case_info or COACaseInfo()
        issue_list = issues or ["[Issues to be identified]"]
        caption = _coa_caption(ci, "Application for Leave to Appeal")

        body: dict[str, str] = {}
        body["Basis for Jurisdiction"] = (
            "This Court has jurisdiction to grant leave to appeal under "
            f"MCR 7.205.  The order appealed was entered in {ci.lower_court}, "
            f"{ci.lower_court_division}, {ci.lower_court_county}, "
            f"Case No. {ci.lower_court_case_number}, by "
            f"{ci.lower_court_judge}."
        )

        issues_text = "\n".join(
            f"{i}. {issue}" for i, issue in enumerate(issue_list, 1)
        )
        body["Questions Presented"] = (
            "Appellant presents the following questions for review:\n\n"
            + issues_text
        )

        body["Reasons Leave Should Be Granted"] = why_leave or (
            "Leave to appeal should be granted because the lower court "
            "committed significant legal errors affecting the substantial "
            "rights of the appellant and the minor child."
        )

        body["Relief Sought"] = (
            "Appellant respectfully requests that this Court grant leave "
            "to appeal and, upon review, reverse the order of the lower "
            "court and remand for proceedings consistent with this Court's "
            "opinion."
        )

        logger.info(
            "Generated Leave Application for %s", ci.lower_court_case_number
        )
        return COADocument(
            document_type="leave_to_appeal",
            case_info=ci,
            caption=caption,
            body_sections=body,
            signature_block=_signature_block(),
            certificate_of_service=_certificate_of_service(ci),
            scao_form="MC 230",
        )

    def generate_docketing_statement(
        self,
        case_info: COACaseInfo | None = None,
    ) -> COADocument:
        """Generate a Docketing Statement (SCAO MC 231).

        The docketing statement is required with every claim of appeal
        and application for leave to appeal under MCR 7.204(B).
        """
        ci = case_info or COACaseInfo()
        caption = _coa_caption(ci, "Docketing Statement")

        body: dict[str, str] = {}
        body["Appellant Information"] = (
            f"Name: {PARTIES['appellant']['name']}\n"
            f"Address: {PARTIES['appellant']['address']}\n"
            f"Phone: {PARTIES['appellant']['phone']}\n"
            f"Email: {PARTIES['appellant']['email']}\n"
            "Attorney: Pro Se"
        )
        body["Appellee Information"] = (
            f"Name: {PARTIES['appellee']['name']}\n"
            f"Address: {PARTIES['appellee']['address']}\n"
            "Attorney: [Unknown — verify current representation]"
        )
        body["Lower Court Information"] = (
            f"Court: {ci.lower_court}, {ci.lower_court_division}\n"
            f"County: {ci.lower_court_county}\n"
            f"Judge: {ci.lower_court_judge}\n"
            f"Case Number: {ci.lower_court_case_number}"
        )
        body["Nature of Case"] = (
            "Domestic relations — custody, parenting time, and related "
            "family law matters."
        )
        body["Companion or Prior Appeals"] = "None known."

        logger.info(
            "Generated Docketing Statement for %s", ci.lower_court_case_number
        )
        return COADocument(
            document_type="docketing_statement",
            case_info=ci,
            caption=caption,
            body_sections=body,
            signature_block=_signature_block(),
            certificate_of_service=_certificate_of_service(ci),
            scao_form="MC 231",
        )

    # -- Brief generation -----------------------------------------------------

    def generate_brief(
        self,
        brief_type: str,
        case_info: COACaseInfo | None = None,
        issues: list[str] | None = None,
        arguments: list[dict[str, str]] | None = None,
        facts: str = "",
        relief: str = "",
        authorities: list[str] | None = None,
    ) -> COABrief:
        """Generate an appellate brief per MCR 7.212.

        Parameters
        ----------
        brief_type:
            ``"appellant_brief"`` or ``"reply_brief"``.
        case_info:
            Case identification.
        issues:
            Questions presented for review.
        arguments:
            List of dicts, each with ``"heading"``, ``"content"``, and
            optionally ``"standard_of_review"`` (key into
            :data:`STANDARDS_OF_REVIEW`).
        facts:
            Statement of facts narrative.
        relief:
            Relief requested narrative.
        authorities:
            List of case citations for the index of authorities.

        Returns
        -------
        COABrief
            A complete appellate brief model.

        Raises
        ------
        ValueError
            If *brief_type* is not recognised.
        """
        if brief_type not in ("appellant_brief", "reply_brief"):
            raise ValueError(
                f"Unknown brief_type {brief_type!r}; expected "
                "'appellant_brief' or 'reply_brief'"
            )

        ci = case_info or COACaseInfo()
        issue_list = issues or ["[Issue to be identified]"]
        auth_list = authorities or []
        arg_dicts = arguments or []

        title = (
            "Appellant's Brief" if brief_type == "appellant_brief"
            else "Reply Brief"
        )
        caption = _coa_caption(ci, title)

        # Build argument sections
        arg_sections: list[BriefSection] = []
        for a in arg_dicts:
            sor_key = a.get("standard_of_review", "")
            sor_text = STANDARDS_OF_REVIEW.get(sor_key, sor_key)
            arg_sections.append(
                BriefSection(
                    heading=a.get("heading", "Untitled Argument"),
                    content=a.get("content", ""),
                    standard_of_review=sor_text if sor_text else None,
                )
            )

        # Table of contents
        toc_items = list(MCR_7212_REQUIRED_SECTIONS)
        for a in arg_sections:
            toc_items.append(f"  Argument: {a.heading}")
        toc = "\n".join(f"  {item}" for item in toc_items)

        # Index of authorities
        if auth_list:
            ioa = "\n".join(f"  {cite}" for cite in sorted(auth_list))
        else:
            ioa = "  [No authorities cited]"

        # Statement of jurisdiction
        jurisdiction = (
            "This Court has jurisdiction under MCR 7.203(A).  "
            f"The appeal is from the {ci.lower_court}, "
            f"{ci.lower_court_division}, {ci.lower_court_county}, "
            f"Case No. {ci.lower_court_case_number}, "
            f"{ci.lower_court_judge} presiding."
        )

        # Questions presented
        questions = "\n\n".join(
            f"{i}. {q}" for i, q in enumerate(issue_list, 1)
        )

        # Statement of facts
        facts_text = facts or (
            "The facts relevant to this appeal are as follows:\n\n"
            "[Statement of facts to be completed]"
        )

        # Relief requested
        relief_text = relief or (
            "Appellant respectfully requests that this Honorable Court "
            "reverse the decision of the lower court and remand for "
            "further proceedings consistent with its opinion, and grant "
            "such other relief as the Court deems just and equitable."
        )

        # Appendix contents
        appendix = [item.description for item in REQUIRED_APPENDIX_ITEMS]

        logger.info("Generated %s for %s", title, ci.lower_court_case_number)
        return COABrief(
            brief_type=brief_type,
            case_info=ci,
            caption=caption,
            table_of_contents=toc,
            index_of_authorities=ioa,
            statement_of_jurisdiction=jurisdiction,
            statement_of_questions=questions,
            statement_of_facts=facts_text,
            arguments=arg_sections,
            relief_requested=relief_text,
            signature_block=_signature_block(),
            certificate_of_service=_certificate_of_service(ci),
            appendix_contents=appendix,
        )

    # -- Motion generation ----------------------------------------------------

    def generate_motion(
        self,
        motion_type: str,
        case_info: COACaseInfo | None = None,
        grounds: list[str] | None = None,
    ) -> COAMotion:
        """Generate a COA motion document.

        Parameters
        ----------
        motion_type:
            One of ``"motion_to_stay"``, ``"motion_for_peremptory_reversal"``,
            or ``"superintending_control"``.
        case_info:
            Case identification.
        grounds:
            List of grounds supporting the motion.

        Raises
        ------
        ValueError
            If *motion_type* is not a recognised motion filing type.
        """
        motion_filings = {
            "motion_to_stay",
            "motion_for_peremptory_reversal",
            "superintending_control",
        }
        if motion_type not in motion_filings:
            raise ValueError(
                f"Unknown motion_type {motion_type!r}; expected one of "
                f"{sorted(motion_filings)}"
            )

        ci = case_info or COACaseInfo()
        ft = FILING_TYPES[motion_type]
        grounds_list = grounds or ["[Grounds to be specified]"]

        caption = _coa_caption(ci, ft.name)
        body: dict[str, str] = {}

        if motion_type == "motion_to_stay":
            body["Introduction"] = (
                f"Appellant {ci.appellant} respectfully moves this Court "
                "for a stay of the lower court order pending resolution of "
                "this appeal, pursuant to MCR 7.209."
            )
            body["Standard for Stay"] = (
                "Under MCR 7.209, a stay may be granted when the movant "
                "demonstrates: (1) a strong likelihood of success on the "
                "merits; (2) irreparable harm absent a stay; (3) that a "
                "stay will not cause substantial harm to the opposing party; "
                "and (4) that the public interest favors a stay."
            )
            grounds_text = "\n".join(
                f"{i}. {g}" for i, g in enumerate(grounds_list, 1)
            )
            body["Grounds for Stay"] = grounds_text

        elif motion_type == "motion_for_peremptory_reversal":
            body["Introduction"] = (
                f"Appellant {ci.appellant} respectfully moves this Court "
                "for peremptory reversal of the lower court order pursuant "
                "to MCR 7.211(C)(4)."
            )
            body["Standard for Peremptory Reversal"] = (
                "Peremptory reversal is appropriate when the lower court's "
                "error is so clear that full briefing and oral argument are "
                "unnecessary. MCR 7.211(C)(4)."
            )
            grounds_text = "\n".join(
                f"{i}. {g}" for i, g in enumerate(grounds_list, 1)
            )
            body["Clear Error Below"] = grounds_text

        elif motion_type == "superintending_control":
            body["Introduction"] = (
                f"Appellant {ci.appellant} respectfully files this Complaint "
                "for Superintending Control pursuant to MCR 7.206, requesting "
                "this Court to direct the lower court to act in accordance "
                "with the law."
            )
            body["Jurisdiction"] = (
                "This Court has jurisdiction to issue writs of "
                "superintending control under Const 1963, art 6, § 13 and "
                "MCR 7.206."
            )
            body["Standard for Superintending Control"] = (
                "Superintending control is appropriate when: (1) the lower "
                "court has committed a clear legal error; (2) no adequate "
                "alternative remedy exists; and (3) the resulting damage "
                "or injustice is serious and irreparable."
            )
            grounds_text = "\n".join(
                f"{i}. {g}" for i, g in enumerate(grounds_list, 1)
            )
            body["Grounds"] = grounds_text

        relief_items = [
            f"Grant this {ft.name} for the reasons stated herein.",
            "Grant such further relief as this Court deems just and proper.",
        ]

        logger.info("Generated %s for %s", ft.name, ci.lower_court_case_number)
        return COAMotion(
            motion_type=motion_type,
            case_info=ci,
            caption=caption,
            body_sections=body,
            relief_requested=relief_items,
            signature_block=_signature_block(),
            certificate_of_service=_certificate_of_service(ci),
        )

    # -- Appendix generation --------------------------------------------------

    def generate_appendix(
        self,
        documents: list[dict[str, str]] | None = None,
    ) -> list[dict[str, str]]:
        """Generate appendix contents list per MCR 7.212(H).

        Parameters
        ----------
        documents:
            Optional list of dicts with ``"label"`` and ``"description"``
            for additional non-required documents to include.

        Returns
        -------
        list[dict[str, str]]
            Ordered list of appendix items with ``"label"``,
            ``"description"``, and ``"required"`` flag.
        """
        result: list[dict[str, str]] = []
        for item in REQUIRED_APPENDIX_ITEMS:
            result.append({
                "label": item.label,
                "description": item.description,
                "required": "yes" if item.required else "no",
            })
        if documents:
            letter_ord = ord("e")
            for doc in documents:
                result.append({
                    "label": doc.get("label", chr(letter_ord)),
                    "description": doc.get("description", ""),
                    "required": "no",
                })
                letter_ord += 1

        logger.info("Generated appendix with %d items", len(result))
        return result

    # -- Brief validation -----------------------------------------------------

    def validate_brief(self, brief_text: str) -> BriefValidation:
        """Validate a brief against MCR 7.212 requirements.

        Checks for presence of required sections, estimates page count,
        and returns a compliance report.

        Parameters
        ----------
        brief_text:
            The full text of the brief to validate.
        """
        issues: list[str] = []
        checklist: dict[str, bool] = {}

        # Check each required section
        for section in MCR_7212_REQUIRED_SECTIONS:
            pattern = re.compile(re.escape(section), re.IGNORECASE)
            found = bool(pattern.search(brief_text))
            checklist[section] = found
            if not found:
                issues.append(f"Missing required section: {section}")

        # Estimate page count (approx 250 words/page, double-spaced)
        word_count = len(brief_text.split())
        page_count = max(1, word_count // 250)

        if page_count > BRIEF_PAGE_LIMIT:
            issues.append(
                f"Brief exceeds {BRIEF_PAGE_LIMIT}-page limit "
                f"(estimated {page_count} pages)"
            )

        # Check for signature block
        has_signature = "respectfully submitted" in brief_text.lower()
        checklist["Signature Block"] = has_signature
        if not has_signature:
            issues.append("Missing signature block")

        # Check for certificate of service
        has_cos = "certificate of service" in brief_text.lower()
        checklist["Certificate of Service"] = has_cos
        if not has_cos:
            issues.append("Missing certificate of service")

        is_compliant = len(issues) == 0
        logger.info(
            "Brief validation: %s (%d issues)",
            "COMPLIANT" if is_compliant else "NON-COMPLIANT",
            len(issues),
        )
        return BriefValidation(
            is_compliant=is_compliant,
            page_count=page_count,
            issues=issues,
            mcr_7212_checklist=checklist,
        )

    # -- Required documents checklist -----------------------------------------

    def get_required_documents(self, filing_type: str) -> list[str]:
        """Return the checklist of required documents for a filing type.

        Parameters
        ----------
        filing_type:
            Key from :data:`FILING_TYPES` (e.g., ``"claim_of_appeal"``).

        Raises
        ------
        ValueError
            If *filing_type* is not recognised.
        """
        ft = FILING_TYPES.get(filing_type)
        if ft is None:
            raise ValueError(
                f"Unknown filing_type {filing_type!r}; valid types: "
                f"{sorted(FILING_TYPES.keys())}"
            )
        return list(ft.required_docs)

    # -- Deadline calculation -------------------------------------------------

    def calculate_deadlines(
        self,
        lower_court_order_date: date | str,
    ) -> list[COADeadline]:
        """Calculate all COA filing deadlines from the lower court order date.

        Parameters
        ----------
        lower_court_order_date:
            Date the lower court order was entered.  Accepts ``date`` or
            ISO-format string (``"YYYY-MM-DD"``).

        Returns
        -------
        list[COADeadline]
            All applicable deadlines sorted by deadline date.
        """
        if isinstance(lower_court_order_date, str):
            trigger = date.fromisoformat(lower_court_order_date)
        else:
            trigger = lower_court_order_date

        today = date.today()
        deadlines: list[COADeadline] = []

        for key, ft in FILING_TYPES.items():
            if ft.deadline_days is None:
                continue
            raw_deadline = trigger + timedelta(days=ft.deadline_days)
            adj_deadline = _next_business_day(raw_deadline)
            remaining = (adj_deadline - today).days

            deadlines.append(
                COADeadline(
                    filing_type=key,
                    trigger_date=trigger,
                    deadline_date=adj_deadline,
                    days_remaining=remaining,
                    is_expired=remaining < 0,
                    mcr_rule=ft.mcr_rule,
                    description=ft.deadline_description,
                )
            )

        deadlines.sort(key=lambda d: d.deadline_date)
        logger.info(
            "Calculated %d deadlines from order date %s",
            len(deadlines),
            trigger.isoformat(),
        )
        return deadlines
