"""Court-Specific PDF Formatting Engine — MCR-compliant document formatting.

Produces court-ready formatted text for Michigan Circuit, COA, MSC, Federal
(WDMI), and JTC filings.  Handles captions, signature blocks, certificates
of service, page numbering, line numbering, exhibit covers, Bates stamps,
and full filing-package assembly.

All output is plain text (ready for downstream PDF rendering via
``pdf_production``).  No external PDF libraries are imported here — this
engine is a *formatting* layer, not a rendering layer.

Usage::

    fmt = PDFFormatter()
    result = fmt.format_for_court("# Motion\\n...", "circuit")
    pkg = fmt.assemble_filing_package([caption, body, cert])
"""

from __future__ import annotations

import logging
import re
import textwrap
from datetime import datetime
from enum import Enum
from typing import Any, Optional, Sequence

from pydantic import BaseModel, ConfigDict, Field, field_validator

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_LINE_WIDTH = 65  # characters per line at 12pt Times in 1″ margins


class CourtType(str, Enum):
    """Supported court types."""

    CIRCUIT = "circuit"
    COA = "coa"
    MSC = "msc"
    FEDERAL = "federal"
    JTC = "jtc"


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class CourtFormat(BaseModel):
    """Court-specific formatting rules."""

    court_type: CourtType
    margin_inches: float = 1.0
    font_size: int = 12
    line_spacing: float = 2.0
    max_pages: Optional[int] = None
    required_sections: list[str] = Field(default_factory=list)
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CaptionInfo(BaseModel):
    """Data needed to render a court caption."""

    court_name: str
    case_number: str
    case_title: Optional[str] = None
    plaintiff: str
    defendant: str
    document_title: str
    judge: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class SignerInfo(BaseModel):
    """Signer data for the signature block."""

    name: str
    address: str
    phone: str
    email: str
    bar_number: Optional[str] = None
    designation: str = "Pro Se"

    model_config = ConfigDict(from_attributes=True)

    @field_validator("designation", mode="before")
    @classmethod
    def _default_designation(cls, v: str | None) -> str:
        return v or "Pro Se"


class ServiceEntry(BaseModel):
    """A single service recipient."""

    name: str
    address: str
    method: str = "first-class mail"

    model_config = ConfigDict(from_attributes=True)


class ServiceInfo(BaseModel):
    """Certificate of service metadata."""

    date: str = Field(default_factory=lambda: datetime.now().strftime("%B %d, %Y"))
    recipients: list[ServiceEntry] = Field(default_factory=list)
    method: str = "first-class mail, postage prepaid"

    model_config = ConfigDict(from_attributes=True)


class FormattingResult(BaseModel):
    """Outcome of a formatting operation."""

    formatted_text: str
    page_count: int = 0
    warnings: list[str] = Field(default_factory=list)
    compliant: bool = True

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Default court format presets
# ---------------------------------------------------------------------------

_COURT_FORMATS: dict[CourtType, CourtFormat] = {
    CourtType.CIRCUIT: CourtFormat(
        court_type=CourtType.CIRCUIT,
        margin_inches=1.0,
        font_size=12,
        line_spacing=2.0,
        max_pages=50,
        required_sections=["caption", "body", "signature", "certificate_of_service"],
        notes="MCR 2.113 caption format; MCR 2.119 motion practice",
    ),
    CourtType.COA: CourtFormat(
        court_type=CourtType.COA,
        margin_inches=1.0,
        font_size=12,
        line_spacing=2.0,
        max_pages=50,
        required_sections=[
            "caption",
            "table_of_contents",
            "table_of_authorities",
            "jurisdictional_statement",
            "statement_of_questions",
            "statement_of_facts",
            "argument",
            "relief_requested",
            "signature",
            "certificate_of_service",
        ],
        notes="MCR 7.212 brief format; proportional 12pt font",
    ),
    CourtType.MSC: CourtFormat(
        court_type=CourtType.MSC,
        margin_inches=1.0,
        font_size=12,
        line_spacing=2.0,
        max_pages=50,
        required_sections=[
            "caption",
            "questions_presented",
            "statement_of_facts",
            "argument",
            "relief_requested",
            "signature",
            "certificate_of_service",
        ],
        notes="MCR 7.305/7.306; 50-page limit",
    ),
    CourtType.FEDERAL: CourtFormat(
        court_type=CourtType.FEDERAL,
        margin_inches=1.0,
        font_size=12,
        line_spacing=2.0,
        max_pages=25,
        required_sections=[
            "caption",
            "body",
            "signature",
            "certificate_of_service",
        ],
        notes="LCivR formatting; CM/ECF compatible; WDMI local rules",
    ),
    CourtType.JTC: CourtFormat(
        court_type=CourtType.JTC,
        margin_inches=1.0,
        font_size=12,
        line_spacing=2.0,
        max_pages=None,
        required_sections=[
            "caption",
            "allegations",
            "supporting_facts",
            "relief_requested",
            "signature",
            "verification",
        ],
        notes="JTC Rule 11 complaint format",
    ),
}

# ---------------------------------------------------------------------------
# Default party information (verified, single source of truth)
# ---------------------------------------------------------------------------

DEFAULT_CAPTION = CaptionInfo(
    court_name="IN THE 14TH CIRCUIT COURT FOR THE COUNTY OF MUSKEGON\nFAMILY DIVISION",
    case_number="2024-001507-DC",
    plaintiff="ANDREW JAMES PIGORS",
    defendant="EMILY A. WATSON",
    document_title="MOTION",
    judge="Hon. Jenny L. McNeill",
)

DEFAULT_SIGNER = SignerInfo(
    name="Andrew James Pigors",
    address="1977 Whitehall Road, Lot 17\nNorth Muskegon, MI 49445",
    phone="(231) 903-5690",
    email="andrewjpigors@gmail.com",
    bar_number=None,
    designation="Pro Se",
)


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------


class PDFFormatter:
    """Court-specific document formatting engine.

    Produces plain-text formatted content suitable for rendering into
    court-ready PDFs by the ``pdf_production`` module.  All methods are
    stateless and do not require a database connection.
    """

    def __init__(self) -> None:
        self._formats = dict(_COURT_FORMATS)
        logger.info("PDFFormatter initialised with %d court formats", len(self._formats))

    # -- public helpers -----------------------------------------------------

    def get_court_format(self, court_type: str | CourtType) -> CourtFormat:
        """Return the ``CourtFormat`` for *court_type*.

        Raises:
            ValueError: If *court_type* is unknown.
        """
        ct = CourtType(court_type) if isinstance(court_type, str) else court_type
        fmt = self._formats.get(ct)
        if fmt is None:
            raise ValueError(f"Unknown court type: {court_type}")
        return fmt

    # -- core formatting ----------------------------------------------------

    def format_for_court(
        self,
        markdown_text: str,
        court_type: str | CourtType,
    ) -> FormattingResult:
        """Apply court-specific formatting rules to *markdown_text*.

        Strips Markdown headings (``#``), wraps lines, enforces double
        spacing representation, and validates page limits.

        Args:
            markdown_text: Source document in Markdown.
            court_type: Target court.

        Returns:
            A ``FormattingResult`` with the cleaned text and compliance info.
        """
        ct = CourtType(court_type) if isinstance(court_type, str) else court_type
        fmt = self.get_court_format(ct)

        warnings: list[str] = []
        lines: list[str] = []

        for raw_line in markdown_text.splitlines():
            # Strip markdown heading markers
            stripped = re.sub(r"^#{1,6}\s*", "", raw_line)
            # Wrap long lines
            if len(stripped) > _LINE_WIDTH:
                wrapped = textwrap.fill(stripped, width=_LINE_WIDTH)
                lines.extend(wrapped.splitlines())
            else:
                lines.append(stripped)

        formatted = "\n\n".join(lines) if fmt.line_spacing >= 2.0 else "\n".join(lines)

        # Estimate pages (~25 double-spaced lines per page)
        non_blank = [ln for ln in formatted.splitlines() if ln.strip()]
        lines_per_page = 25 if fmt.line_spacing >= 2.0 else 50
        page_count = max(1, (len(non_blank) + lines_per_page - 1) // lines_per_page)

        compliant = True
        if fmt.max_pages and page_count > fmt.max_pages:
            warnings.append(
                f"Document is ~{page_count} pages; {ct.value} limit is {fmt.max_pages}"
            )
            compliant = False

        logger.debug(
            "Formatted for %s: %d lines, ~%d pages, compliant=%s",
            ct.value,
            len(non_blank),
            page_count,
            compliant,
        )

        return FormattingResult(
            formatted_text=formatted,
            page_count=page_count,
            warnings=warnings,
            compliant=compliant,
        )

    # -- caption ------------------------------------------------------------

    def apply_caption(
        self,
        text: str,
        case_info: CaptionInfo | None = None,
    ) -> str:
        """Prepend a court caption to *text*.

        Uses *case_info* (or ``DEFAULT_CAPTION``) to produce a caption
        block formatted per MCR 2.113.
        """
        info = case_info or DEFAULT_CAPTION

        caption_lines = [
            "STATE OF MICHIGAN",
            info.court_name,
            "",
        ]

        # Build left/right alignment
        left_col = f"{info.plaintiff},"
        right_col = f"Case No. {info.case_number}"
        caption_lines.append(f"{left_col:<40s}{right_col}")

        indent_plaintiff = "    Plaintiff,"
        judge_line = f"{'':40s}{info.judge}" if info.judge else ""
        caption_lines.append(f"{indent_plaintiff:<40s}{judge_line}".rstrip())

        caption_lines.append("")
        caption_lines.append("v.")
        caption_lines.append("")
        caption_lines.append(f"{info.defendant},")
        caption_lines.append("    Defendant.")
        caption_lines.append("_" * 40 + "/")
        caption_lines.append("")

        # Document title centred
        caption_lines.append(info.document_title.upper().center(70))
        caption_lines.append("")

        caption = "\n".join(caption_lines)
        return f"{caption}\n{text}"

    # -- signature block ----------------------------------------------------

    def apply_signature_block(
        self,
        text: str,
        signer_info: SignerInfo | None = None,
    ) -> str:
        """Append a signature block to *text*.

        For pro se litigants (no *bar_number*), uses the format required
        by MCR 2.114(B).
        """
        info = signer_info or DEFAULT_SIGNER

        designation = info.designation
        if info.bar_number:
            name_line = f"{info.name} ({info.bar_number})"
        else:
            name_line = f"{info.name}, {designation}"

        block = textwrap.dedent(f"""\


            Respectfully submitted,

            ___________________________
            {name_line}
            {info.address}
            {info.phone}
            {info.email}
        """)
        return f"{text}{block}"

    # -- certificate of service ---------------------------------------------

    def apply_certificate_of_service(
        self,
        text: str,
        service_info: ServiceInfo | None = None,
    ) -> str:
        """Append a Certificate of Service to *text*.

        Per MCR 2.107, certifies that copies were served on all parties.
        """
        info = service_info or ServiceInfo(
            recipients=[
                ServiceEntry(
                    name="Emily A. Watson",
                    address="2160 Garland Drive, Norton Shores, MI 49441",
                ),
            ],
        )

        lines = [
            "",
            "",
            "CERTIFICATE OF SERVICE",
            "",
            (
                f"    I certify that on {info.date}, I served a copy of the "
                f"foregoing document on the following by {info.method}:"
            ),
            "",
        ]
        for recip in info.recipients:
            lines.append(f"    {recip.name}")
            for addr_line in recip.address.splitlines():
                lines.append(f"    {addr_line}")
            lines.append("")

        lines.extend([
            "",
            "___________________________",
            f"{DEFAULT_SIGNER.name}, {DEFAULT_SIGNER.designation}",
        ])

        cert = "\n".join(lines)
        return f"{text}\n{cert}"

    # -- page numbers -------------------------------------------------------

    def number_pages(self, text: str) -> str:
        """Insert page-number markers into *text*.

        Splits the text into pages (~25 double-spaced lines each) and
        appends a ``Page X of Y`` footer to each page.
        """
        all_lines = text.splitlines()
        lines_per_page = 25
        pages: list[list[str]] = []

        for i in range(0, len(all_lines), lines_per_page):
            pages.append(all_lines[i : i + lines_per_page])

        total = len(pages)
        numbered: list[str] = []
        for idx, page_lines in enumerate(pages, start=1):
            numbered.extend(page_lines)
            numbered.append("")
            numbered.append(f"Page {idx} of {total}".center(70))
            if idx < total:
                numbered.append("\f")  # form-feed page break

        return "\n".join(numbered)

    # -- line numbers -------------------------------------------------------

    def add_line_numbers(self, text: str) -> str:
        """Prefix every non-empty line with a sequential line number.

        Some federal and appellate courts require numbered lines in the
        left margin.
        """
        lines = text.splitlines()
        numbered: list[str] = []
        counter = 0
        for line in lines:
            if line.strip():
                counter += 1
                numbered.append(f"{counter:>4d} | {line}")
            else:
                numbered.append(f"{'':>4s} | {line}")
        return "\n".join(numbered)

    # -- validation ---------------------------------------------------------

    def validate_formatting(
        self,
        text: str,
        court_type: str | CourtType,
    ) -> FormattingResult:
        """Check *text* for compliance with *court_type* rules.

        Returns a ``FormattingResult`` whose *warnings* list enumerates
        every detected issue.
        """
        ct = CourtType(court_type) if isinstance(court_type, str) else court_type
        fmt = self.get_court_format(ct)

        warnings: list[str] = []
        text_upper = text.upper()

        # Page-count estimate
        non_blank = [ln for ln in text.splitlines() if ln.strip()]
        lines_per_page = 25 if fmt.line_spacing >= 2.0 else 50
        page_count = max(1, (len(non_blank) + lines_per_page - 1) // lines_per_page)

        if fmt.max_pages and page_count > fmt.max_pages:
            warnings.append(
                f"Estimated {page_count} pages exceeds {ct.value} limit of {fmt.max_pages}"
            )

        # Check for required sections via heuristic heading detection
        section_checks: dict[str, list[str]] = {
            "caption": ["STATE OF MICHIGAN", "CASE NO"],
            "signature": ["RESPECTFULLY SUBMITTED"],
            "certificate_of_service": ["CERTIFICATE OF SERVICE"],
            "table_of_contents": ["TABLE OF CONTENTS"],
            "table_of_authorities": ["TABLE OF AUTHORITIES"],
            "jurisdictional_statement": ["JURISDICTIONAL STATEMENT", "JURISDICTION"],
            "statement_of_questions": ["QUESTIONS PRESENTED", "STATEMENT OF QUESTIONS"],
            "statement_of_facts": ["STATEMENT OF FACTS"],
            "argument": ["ARGUMENT"],
            "relief_requested": ["RELIEF REQUESTED", "PRAYER FOR RELIEF", "WHEREFORE"],
            "body": [],  # always passes — body is the text itself
            "questions_presented": ["QUESTIONS PRESENTED"],
            "allegations": ["ALLEGATIONS", "ALLEGATION"],
            "supporting_facts": ["SUPPORTING FACTS", "FACTS"],
            "verification": ["VERIFICATION", "VERIFY"],
        }

        for section in fmt.required_sections:
            markers = section_checks.get(section, [])
            if markers and not any(m in text_upper for m in markers):
                warnings.append(f"Missing required section: {section}")

        compliant = len(warnings) == 0

        return FormattingResult(
            formatted_text=text,
            page_count=page_count,
            warnings=warnings,
            compliant=compliant,
        )

    # -- exhibit covers -----------------------------------------------------

    def generate_exhibit_cover(
        self,
        exhibit_id: str,
        description: str,
    ) -> str:
        """Generate a plain-text exhibit cover/separator page.

        Args:
            exhibit_id: Label such as ``"A"`` or ``"1"``.
            description: Human-readable description of the exhibit.

        Returns:
            Cover-page text.
        """
        cover = textwrap.dedent(f"""\
            {'=' * 60}

            {'EXHIBIT ' + exhibit_id:^60s}

            {description.center(60)}

            {'=' * 60}
        """)
        return cover

    # -- Bates stamps -------------------------------------------------------

    def generate_bates_stamp(
        self,
        start_num: int = 1,
        prefix: str = "PIGORS",
        count: int = 1,
    ) -> list[str]:
        """Generate a sequence of Bates-number strings.

        Args:
            start_num: First number in the sequence.
            prefix: Prefix label (default ``PIGORS``).
            count: How many Bates numbers to generate.

        Returns:
            List of formatted Bates labels, e.g. ``["PIGORS-000001"]``.
        """
        stamps: list[str] = []
        for i in range(count):
            stamps.append(f"{prefix}-{start_num + i:06d}")
        return stamps

    # -- filing-package assembly --------------------------------------------

    def assemble_filing_package(
        self,
        components: Sequence[str],
        *,
        separator: str = "\n\f\n",
    ) -> FormattingResult:
        """Combine multiple text components into a single filing package.

        Each component is separated by a form-feed (page break).  The
        total page count is estimated and returned in the result.

        Args:
            components: Ordered text blocks (caption, body, exhibits, cert …).
            separator: String inserted between components.

        Returns:
            A ``FormattingResult`` with the assembled text.
        """
        if not components:
            return FormattingResult(
                formatted_text="",
                page_count=0,
                warnings=["No components provided"],
                compliant=False,
            )

        assembled = separator.join(c for c in components if c)
        non_blank = [ln for ln in assembled.splitlines() if ln.strip()]
        page_count = max(1, (len(non_blank) + 24) // 25)

        return FormattingResult(
            formatted_text=assembled,
            page_count=page_count,
            warnings=[],
            compliant=True,
        )
