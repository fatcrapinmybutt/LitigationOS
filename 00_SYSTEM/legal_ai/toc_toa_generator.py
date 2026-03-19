"""
LitigationOS Table of Contents & Table of Authorities Generator
================================================================

Generates MCR 7.212(C)-compliant Table of Contents and Table of
Authorities from Markdown filing text.  Integrates with the existing
TOC generator at ``00_SYSTEM/local_model/engines/table_of_contents_generator.py``
but adds full Table of Authorities, citation categorization, pagination
estimates, and both Markdown and HTML output.

Citation categories follow Michigan appellate practice:
    - Michigan cases (e.g., *People v Smith*, 500 Mich 123)
    - Federal cases (e.g., *Mathews v Eldridge*, 424 US 319)
    - Michigan statutes (MCL §§)
    - Court rules (MCR, MRE, MRPC)
    - Constitutional provisions (US Const, Mich Const)
    - Other authorities (treatises, secondary sources)

Case: Pigors v. Watson, 2024-001507-DC
Plaintiff: Andrew James Pigors (Pro Se)
Defendant: Emily A. Watson
Judge: Hon. Jenny L. McNeill
"""

from __future__ import annotations

import html as html_mod
import json
import logging
import math
import re
import textwrap
from collections import OrderedDict, defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DB_PATH = Path(__file__).resolve().parents[2] / "litigation_context.db"

WORDS_PER_PAGE = 250

DOT_LEADER_CHAR = "."
DOT_LEADER_WIDTH = 60  # characters for dot-leader lines

# Required sections per MCR 7.212(C) for COA briefs
COA_REQUIRED_SECTIONS = [
    "TABLE OF CONTENTS",
    "INDEX OF AUTHORITIES",
    "STATEMENT OF JURISDICTION",
    "STATEMENT OF QUESTIONS PRESENTED",
    "STATEMENT OF FACTS",
    "ARGUMENT",
    "RELIEF REQUESTED",
]

# Required sections per MCR 7.306 for MSC applications
MSC_REQUIRED_SECTIONS = [
    "TABLE OF CONTENTS",
    "INDEX OF AUTHORITIES",
    "STATEMENT OF QUESTIONS PRESENTED",
    "STATEMENT OF FACTS",
    "ARGUMENT",
    "RELIEF REQUESTED",
]


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------
class CitationCategory(str, Enum):
    """Categories of legal authorities for Table of Authorities."""

    CASES_MICHIGAN = "cases_michigan"
    CASES_FEDERAL = "cases_federal"
    CASES_OTHER = "cases_other"
    STATUTES = "statutes"
    RULES = "rules"
    CONSTITUTIONAL = "constitutional"
    OTHER = "other"


# Display labels for TOA sections
CATEGORY_LABELS: Dict[str, str] = {
    CitationCategory.CASES_MICHIGAN: "Michigan Cases",
    CitationCategory.CASES_FEDERAL: "Federal Cases",
    CitationCategory.CASES_OTHER: "Other Cases",
    CitationCategory.STATUTES: "Statutes",
    CitationCategory.RULES: "Court Rules",
    CitationCategory.CONSTITUTIONAL: "Constitutional Provisions",
    CitationCategory.OTHER: "Other Authorities",
}

# Category grouping for traditional TOA format
CATEGORY_GROUPS: List[Tuple[str, List[str]]] = [
    ("Cases", [
        CitationCategory.CASES_MICHIGAN,
        CitationCategory.CASES_FEDERAL,
        CitationCategory.CASES_OTHER,
    ]),
    ("Statutes", [CitationCategory.STATUTES]),
    ("Court Rules", [CitationCategory.RULES]),
    ("Constitutional Provisions", [CitationCategory.CONSTITUTIONAL]),
    ("Other Authorities", [CitationCategory.OTHER]),
]


# ---------------------------------------------------------------------------
# Citation Patterns (compiled for performance)
# ---------------------------------------------------------------------------

# Michigan cases: *People v Smith*, 500 Mich 123 (2020)
_RE_MI_CASE = re.compile(
    r"(?:(?:\*?[A-Z][a-zA-Z.']+(?:\s+(?:v\.?|vs\.?)\s+)[A-Z][a-zA-Z.']+\*?)"
    r",?\s*\d+\s+Mich(?:\s+App)?\s+\d+)"
    r"(?:\s*\(\d{4}\))?",
    re.MULTILINE,
)

# Federal cases: 424 US 319, 500 F.2d 123, 100 S.Ct. 1234, etc.
_RE_FED_CASE = re.compile(
    r"(?:(?:\*?[A-Z][a-zA-Z.']+(?:\s+(?:v\.?|vs\.?)\s+)[A-Z][a-zA-Z.']+\*?)"
    r",?\s*\d+\s+(?:U\.?S\.?|S\.?\s*Ct\.?|L\.?\s*Ed\.?"
    r"|F\.?\s*(?:2d|3d|4th)?|F\.?\s*Supp\.?\s*(?:2d|3d)?"
    r"|F\.?\s*App(?:'|')x)\s*\d+)"
    r"(?:\s*\(\d{4}\))?",
    re.MULTILINE,
)

# Generic case pattern: Name v Name
_RE_GENERIC_CASE = re.compile(
    r"\*?([A-Z][a-zA-Z.']+(?:\s+(?:v\.?|vs\.?)\s+)[A-Z][a-zA-Z.']+)\*?"
    r"(?:,\s*\d+\s+[A-Za-z.]+\s+\d+)?",
    re.MULTILINE,
)

# MCL statutes: MCL 722.23, MCL § 600.1701
_RE_MCL = re.compile(
    r"MCL\s*§?\s*§?\s*(\d+\.\d+(?:[a-z])?(?:\(\d+\))?)", re.IGNORECASE
)

# Court rules: MCR 2.119, MRE 803, MRPC 3.3
_RE_MCR = re.compile(
    r"(MCR|MRE|MRPC|FRCP|FRE|FRAP)\s+(\d+\.\d+(?:\([A-Za-z0-9]+\))*)",
    re.IGNORECASE,
)

# Constitutional: US Const Amend XIV, Mich Const 1963, art 1, § 17
_RE_CONST = re.compile(
    r"(?:U\.?S\.?\s*Const\.?|Mich\.?\s*Const\.?\s*(?:1963)?)"
    r"(?:,?\s*(?:art\.?\s*\w+|[Aa]mend\.?\s*[IVXLCDM]+|\u00a7\s*\d+|§\s*\d+))*",
    re.IGNORECASE,
)

# Heading pattern for TOC extraction
_RE_HEADING = re.compile(r"^(#{1,4})\s+(.+)$", re.MULTILINE)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------
@dataclass
class TOCEntry:
    """A single Table of Contents entry.

    Attributes:
        level: Heading level (1-4).
        title: Section title text.
        page_number: Estimated page number.
        section_id: Unique identifier for cross-referencing.
        word_offset: Word offset from document start.
    """

    level: int = 1
    title: str = ""
    page_number: int = 1
    section_id: str = ""
    word_offset: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize entry to dictionary."""
        return asdict(self)


@dataclass
class TOAEntry:
    """A single Table of Authorities entry.

    Attributes:
        category: Citation type (cases, statutes, rules, etc.).
        citation: Short-form citation string.
        full_text: Full citation as found in the document.
        pages: List of page numbers where the citation appears.
        is_primary: Whether this is a primary authority (marked with *).
    """

    category: str = "other"
    citation: str = ""
    full_text: str = ""
    pages: List[int] = field(default_factory=list)
    is_primary: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Serialize entry to dictionary."""
        return asdict(self)


@dataclass
class TOCTOAResult:
    """Combined result of TOC and TOA generation.

    Attributes:
        toc_entries: Ordered list of TOC entries.
        toa_entries: Ordered list of TOA entries.
        toc_markdown: Formatted TOC as Markdown text.
        toa_markdown: Formatted TOA as Markdown text.
        toc_html: Formatted TOC as HTML.
        toa_html: Formatted TOA as HTML.
        total_pages_estimated: Estimated total page count.
        case_count: Number of case citations found.
        statute_count: Number of statute citations found.
        rule_count: Number of court rule citations found.
        constitutional_count: Number of constitutional citations.
        other_count: Number of other authority citations.
        missing_sections: Sections required by court rules but not found.
        warnings: Any compliance warnings.
    """

    toc_entries: List[TOCEntry] = field(default_factory=list)
    toa_entries: List[TOAEntry] = field(default_factory=list)
    toc_markdown: str = ""
    toa_markdown: str = ""
    toc_html: str = ""
    toa_html: str = ""
    total_pages_estimated: int = 0
    case_count: int = 0
    statute_count: int = 0
    rule_count: int = 0
    constitutional_count: int = 0
    other_count: int = 0
    missing_sections: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize result to dictionary."""
        return {
            "toc_entries": [e.to_dict() for e in self.toc_entries],
            "toa_entries": [e.to_dict() for e in self.toa_entries],
            "toc_markdown": self.toc_markdown,
            "toa_markdown": self.toa_markdown,
            "toc_html": self.toc_html,
            "toa_html": self.toa_html,
            "total_pages_estimated": self.total_pages_estimated,
            "case_count": self.case_count,
            "statute_count": self.statute_count,
            "rule_count": self.rule_count,
            "constitutional_count": self.constitutional_count,
            "other_count": self.other_count,
            "missing_sections": self.missing_sections,
            "warnings": self.warnings,
        }


# ---------------------------------------------------------------------------
# Roman numeral helper
# ---------------------------------------------------------------------------
_ROMAN_MAP = [
    (1000, "M"), (900, "CM"), (500, "D"), (400, "CD"),
    (100, "C"), (90, "XC"), (50, "L"), (40, "XL"),
    (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"),
]


def _to_roman(n: int) -> str:
    """Convert integer to Roman numeral string.

    Args:
        n: Positive integer.

    Returns:
        Roman numeral string (e.g., 1 -> 'I', 4 -> 'IV').
    """
    if n <= 0:
        return str(n)
    result: List[str] = []
    for value, numeral in _ROMAN_MAP:
        while n >= value:
            result.append(numeral)
            n -= value
    return "".join(result)


def _to_letter(n: int) -> str:
    """Convert zero-based index to uppercase letter (0->A, 25->Z, 26->AA).

    Args:
        n: Zero-based index.

    Returns:
        Letter string.
    """
    if n < 0:
        return ""
    result: List[str] = []
    n_remaining = n
    while True:
        result.append(chr(65 + (n_remaining % 26)))
        n_remaining = n_remaining // 26 - 1
        if n_remaining < 0:
            break
    return "".join(reversed(result))


# ---------------------------------------------------------------------------
# TOCTOAGenerator
# ---------------------------------------------------------------------------
class TOCTOAGenerator:
    """Generate Table of Contents and Table of Authorities.

    Parses Markdown filing text to extract headings (TOC) and legal
    citations (TOA), then formats both for court filing.

    Usage::

        gen = TOCTOAGenerator()
        result = gen.generate(markdown_text, court_type="coa")
        print(result.toc_markdown)
        print(result.toa_markdown)

    Integration:
        - Aligns with table_of_contents_generator.py TocEntry structure
        - Citation patterns aligned with citation_extractor.py
        - Court section requirements per MCR 7.212(C) and MCR 7.306
    """

    def __init__(
        self,
        words_per_page: int = WORDS_PER_PAGE,
        dot_leader_width: int = DOT_LEADER_WIDTH,
        primary_authority_threshold: int = 3,
    ) -> None:
        """Initialize the TOC/TOA generator.

        Args:
            words_per_page: Baseline words per double-spaced page.
            dot_leader_width: Character width for dot-leader lines.
            primary_authority_threshold: Minimum citation occurrences to
                auto-mark as primary authority.
        """
        self._words_per_page = words_per_page
        self._dot_width = dot_leader_width
        self._primary_threshold = primary_authority_threshold
        self._generation_count = 0
        self._total_citations_found = 0
        logger.info("TOCTOAGenerator initialized (wpp=%d)", words_per_page)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(
        self, text: str, court_type: str = "coa"
    ) -> TOCTOAResult:
        """Generate both TOC and TOA from filing text.

        Args:
            text: Full Markdown text of the filing.
            court_type: Court jurisdiction ('coa', 'msc', '14th_circuit', etc.).

        Returns:
            TOCTOAResult with entries, formatted output, and compliance data.
        """
        warnings: List[str] = []

        if not text or not text.strip():
            warnings.append("Empty input text — no TOC or TOA generated")
            return TOCTOAResult(warnings=warnings)

        # Generate TOC entries
        toc_entries = self.generate_toc(text)
        total_pages = self._estimate_total_pages(text)

        # Generate TOA entries
        toa_entries = self.generate_toa(text)
        toa_entries = self.identify_primary_authorities(toa_entries, text)

        # Check required sections
        missing = self._check_required_sections(toc_entries, court_type)
        if missing:
            warnings.append(
                f"Missing required sections for {court_type}: "
                + ", ".join(missing)
            )

        # Format outputs
        toc_md = self.format_toc_markdown(toc_entries)
        toa_md = self.format_toa_markdown(toa_entries)
        toc_html = self.format_toc_html(toc_entries)
        toa_html = self.format_toa_html(toa_entries)

        # Count by category
        case_count = sum(
            1 for e in toa_entries
            if e.category in (
                CitationCategory.CASES_MICHIGAN,
                CitationCategory.CASES_FEDERAL,
                CitationCategory.CASES_OTHER,
            )
        )
        statute_count = sum(
            1 for e in toa_entries if e.category == CitationCategory.STATUTES
        )
        rule_count = sum(
            1 for e in toa_entries if e.category == CitationCategory.RULES
        )
        const_count = sum(
            1 for e in toa_entries if e.category == CitationCategory.CONSTITUTIONAL
        )
        other_count = sum(
            1 for e in toa_entries if e.category == CitationCategory.OTHER
        )

        self._generation_count += 1
        self._total_citations_found += len(toa_entries)

        return TOCTOAResult(
            toc_entries=toc_entries,
            toa_entries=toa_entries,
            toc_markdown=toc_md,
            toa_markdown=toa_md,
            toc_html=toc_html,
            toa_html=toa_html,
            total_pages_estimated=total_pages,
            case_count=case_count,
            statute_count=statute_count,
            rule_count=rule_count,
            constitutional_count=const_count,
            other_count=other_count,
            missing_sections=missing,
            warnings=warnings,
        )

    def generate_toc(
        self, text: str, words_per_page: Optional[int] = None
    ) -> List[TOCEntry]:
        """Extract headings from Markdown and build TOC entries.

        Args:
            text: Markdown filing text.
            words_per_page: Override words-per-page for page estimation.

        Returns:
            Ordered list of TOCEntry with estimated page numbers.
        """
        wpp = words_per_page or self._words_per_page
        entries: List[TOCEntry] = []
        word_count = 0
        entry_counter = 0

        for line in text.split("\n"):
            stripped = line.strip()
            # Count words for page estimation
            line_words = len(stripped.split()) if stripped else 0

            heading_match = re.match(r"^(#{1,4})\s+(.+)$", stripped)
            if heading_match:
                level = len(heading_match.group(1))
                title = heading_match.group(2).strip()
                # Remove markdown formatting from title
                title = re.sub(r"\*\*(.+?)\*\*", r"\1", title)
                title = re.sub(r"\*(.+?)\*", r"\1", title)
                title = title.strip()

                page_num = max(1, math.ceil(word_count / wpp)) if word_count > 0 else 1

                section_id = f"sec-{entry_counter:03d}-{self._slugify(title)}"
                entry_counter += 1

                entries.append(TOCEntry(
                    level=level,
                    title=title,
                    page_number=page_num,
                    section_id=section_id,
                    word_offset=word_count,
                ))

            word_count += line_words

        return entries

    def generate_toa(self, text: str) -> List[TOAEntry]:
        """Extract and categorize all legal citations from filing text.

        Args:
            text: Full filing text to scan for citations.

        Returns:
            Deduplicated, alphabetically sorted list of TOAEntry.
        """
        citations: Dict[str, TOAEntry] = {}

        # Extract each category of citation
        self._extract_michigan_cases(text, citations)
        self._extract_federal_cases(text, citations)
        self._extract_statutes(text, citations)
        self._extract_rules(text, citations)
        self._extract_constitutional(text, citations)

        # Sort alphabetically within each category
        result = sorted(
            citations.values(),
            key=lambda e: (self._category_sort_key(e.category), e.citation.lower()),
        )

        return result

    def identify_primary_authorities(
        self, entries: List[TOAEntry], filing_text: str
    ) -> List[TOAEntry]:
        """Mark primary authorities based on citation frequency.

        Authorities cited more than ``primary_authority_threshold`` times
        are marked as primary.  Manual overrides via asterisk (*) in the
        original text are also detected.

        Args:
            entries: TOA entries to evaluate.
            filing_text: Full filing text for frequency counting.

        Returns:
            Updated list with ``is_primary`` set appropriately.
        """
        for entry in entries:
            # Count occurrences in text
            pattern = re.escape(entry.citation)
            try:
                count = len(re.findall(pattern, filing_text, re.IGNORECASE))
            except re.error:
                count = filing_text.lower().count(entry.citation.lower())

            if count >= self._primary_threshold:
                entry.is_primary = True

            # Check for explicit asterisk marking
            if f"*{entry.citation}" in filing_text or f"{entry.citation}*" in filing_text:
                entry.is_primary = True

        return entries

    # ------------------------------------------------------------------
    # Formatting: Markdown
    # ------------------------------------------------------------------

    def format_toc_markdown(self, entries: List[TOCEntry]) -> str:
        """Format TOC entries as Markdown with dot leaders.

        Args:
            entries: List of TOC entries.

        Returns:
            Formatted Markdown string.
        """
        if not entries:
            return "## TABLE OF CONTENTS\n\n*(No entries)*\n"

        lines: List[str] = [
            "## TABLE OF CONTENTS",
            "",
        ]

        counters = {"roman": 0, "letter": 0, "number": 0}

        for entry in entries:
            prefix, indent = self._toc_entry_prefix(entry.level, counters)
            title_text = f"{prefix}{entry.title}"
            page_str = str(entry.page_number)
            leader_line = self._format_dot_leader(
                title_text, page_str, self._dot_width, indent_level=entry.level - 1
            )
            lines.append(leader_line)

        lines.append("")
        return "\n".join(lines)

    def format_toa_markdown(self, entries: List[TOAEntry]) -> str:
        """Format TOA entries as Markdown grouped by category.

        Primary authorities are marked with an asterisk (*).
        MCR 7.212(C) compliant format.

        Args:
            entries: List of TOA entries.

        Returns:
            Formatted Markdown string.
        """
        if not entries:
            return "## TABLE OF AUTHORITIES\n\n*(No authorities cited)*\n"

        lines: List[str] = [
            "## TABLE OF AUTHORITIES",
            "",
        ]

        # Group by category
        for group_label, category_keys in CATEGORY_GROUPS:
            group_entries = [
                e for e in entries if e.category in category_keys
            ]
            if not group_entries:
                continue

            lines.append(f"**{group_label}**")
            lines.append("")

            for entry in group_entries:
                primary_mark = "*" if entry.is_primary else " "
                pages_str = ", ".join(str(p) for p in sorted(set(entry.pages)))
                if not pages_str:
                    pages_str = "passim"

                citation_display = f"{primary_mark}{entry.citation}"
                leader_line = self._format_dot_leader(
                    citation_display, pages_str, self._dot_width
                )
                lines.append(leader_line)

            lines.append("")

        # Legend
        lines.append("*Authorities upon which Appellant primarily relies "
                      "are marked with an asterisk (\\*).*")
        lines.append("")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Formatting: HTML
    # ------------------------------------------------------------------

    def format_toc_html(self, entries: List[TOCEntry]) -> str:
        """Format TOC entries as HTML with dot-leader CSS.

        Args:
            entries: List of TOC entries.

        Returns:
            Complete HTML string with embedded CSS.
        """
        if not entries:
            return "<h2>TABLE OF CONTENTS</h2>\n<p><em>No entries</em></p>"

        css = textwrap.dedent("""\
        <style>
        .toc-container {
            font-family: "Times New Roman", Times, serif;
            font-size: 12pt;
            line-height: 2.0;
            max-width: 6.5in;
        }
        .toc-entry {
            display: flex;
            align-items: baseline;
            margin-left: 0;
        }
        .toc-entry.level-2 { margin-left: 0.5in; }
        .toc-entry.level-3 { margin-left: 1.0in; }
        .toc-entry.level-4 { margin-left: 1.5in; }
        .toc-title {
            white-space: nowrap;
        }
        .toc-dots {
            flex: 1;
            border-bottom: 1px dotted #000;
            margin: 0 4px;
            min-width: 20px;
        }
        .toc-page {
            white-space: nowrap;
            text-align: right;
        }
        </style>
        """)

        rows: List[str] = []
        counters = {"roman": 0, "letter": 0, "number": 0}

        for entry in entries:
            prefix, _ = self._toc_entry_prefix(entry.level, counters)
            title_escaped = html_mod.escape(f"{prefix}{entry.title}")
            level_class = f"level-{entry.level}"
            rows.append(
                f'<div class="toc-entry {level_class}">'
                f'<span class="toc-title">{title_escaped}</span>'
                f'<span class="toc-dots"></span>'
                f'<span class="toc-page">{entry.page_number}</span>'
                f"</div>"
            )

        body = "\n".join(rows)
        return f"{css}\n<h2>TABLE OF CONTENTS</h2>\n<div class=\"toc-container\">\n{body}\n</div>"

    def format_toa_html(self, entries: List[TOAEntry]) -> str:
        """Format TOA entries as HTML grouped by category.

        Args:
            entries: List of TOA entries.

        Returns:
            Complete HTML string with embedded CSS.
        """
        if not entries:
            return "<h2>TABLE OF AUTHORITIES</h2>\n<p><em>No authorities cited</em></p>"

        css = textwrap.dedent("""\
        <style>
        .toa-container {
            font-family: "Times New Roman", Times, serif;
            font-size: 12pt;
            line-height: 2.0;
            max-width: 6.5in;
        }
        .toa-category {
            font-weight: bold;
            margin-top: 1em;
            margin-bottom: 0.25em;
            text-decoration: underline;
        }
        .toa-entry {
            display: flex;
            align-items: baseline;
        }
        .toa-citation {
            white-space: nowrap;
        }
        .toa-citation.primary::before {
            content: "*";
            font-weight: bold;
        }
        .toa-dots {
            flex: 1;
            border-bottom: 1px dotted #000;
            margin: 0 4px;
            min-width: 20px;
        }
        .toa-pages {
            white-space: nowrap;
            text-align: right;
        }
        .toa-legend {
            font-style: italic;
            margin-top: 1em;
            font-size: 10pt;
        }
        </style>
        """)

        sections: List[str] = []
        for group_label, category_keys in CATEGORY_GROUPS:
            group_entries = [
                e for e in entries if e.category in category_keys
            ]
            if not group_entries:
                continue

            rows: List[str] = [
                f'<div class="toa-category">{html_mod.escape(group_label)}</div>'
            ]
            for entry in group_entries:
                primary_class = " primary" if entry.is_primary else ""
                citation_escaped = html_mod.escape(entry.citation)
                pages_str = ", ".join(str(p) for p in sorted(set(entry.pages)))
                if not pages_str:
                    pages_str = "passim"
                rows.append(
                    f'<div class="toa-entry">'
                    f'<span class="toa-citation{primary_class}">{citation_escaped}</span>'
                    f'<span class="toa-dots"></span>'
                    f'<span class="toa-pages">{html_mod.escape(pages_str)}</span>'
                    f"</div>"
                )
            sections.append("\n".join(rows))

        body = "\n".join(sections)
        legend = (
            '<p class="toa-legend">Authorities upon which Appellant primarily '
            "relies are marked with an asterisk (*).</p>"
        )

        return (
            f"{css}\n<h2>TABLE OF AUTHORITIES</h2>\n"
            f'<div class="toa-container">\n{body}\n{legend}\n</div>'
        )

    def get_stats(self) -> Dict[str, Any]:
        """Return generator statistics.

        Returns:
            Dict with generation counts and configuration.
        """
        return {
            "generator": "TOCTOAGenerator",
            "version": "1.0.0",
            "generation_count": self._generation_count,
            "total_citations_found": self._total_citations_found,
            "words_per_page": self._words_per_page,
            "primary_authority_threshold": self._primary_threshold,
            "dot_leader_width": self._dot_width,
            "supported_courts": ["coa", "msc", "14th_circuit", "federal", "jtc", "admin"],
            "db_path": str(DB_PATH),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    # ------------------------------------------------------------------
    # Citation Extraction (private)
    # ------------------------------------------------------------------

    def _extract_michigan_cases(
        self, text: str, citations: Dict[str, TOAEntry]
    ) -> None:
        """Extract Michigan case citations from text.

        Args:
            text: Filing text to scan.
            citations: Accumulator dict (citation_key -> TOAEntry).
        """
        for match in _RE_MI_CASE.finditer(text):
            raw = match.group(0).strip().strip("*")
            key = self._normalize_citation(raw)
            if key not in citations:
                citations[key] = TOAEntry(
                    category=CitationCategory.CASES_MICHIGAN,
                    citation=raw,
                    full_text=raw,
                    pages=[],
                )
            page = self._estimate_page_at_offset(text, match.start())
            if page not in citations[key].pages:
                citations[key].pages.append(page)

    def _extract_federal_cases(
        self, text: str, citations: Dict[str, TOAEntry]
    ) -> None:
        """Extract Federal case citations from text.

        Args:
            text: Filing text to scan.
            citations: Accumulator dict.
        """
        for match in _RE_FED_CASE.finditer(text):
            raw = match.group(0).strip().strip("*")
            key = self._normalize_citation(raw)
            if key in citations:
                page = self._estimate_page_at_offset(text, match.start())
                if page not in citations[key].pages:
                    citations[key].pages.append(page)
                continue
            citations[key] = TOAEntry(
                category=CitationCategory.CASES_FEDERAL,
                citation=raw,
                full_text=raw,
                pages=[self._estimate_page_at_offset(text, match.start())],
            )

    def _extract_statutes(
        self, text: str, citations: Dict[str, TOAEntry]
    ) -> None:
        """Extract MCL statute citations from text.

        Args:
            text: Filing text to scan.
            citations: Accumulator dict.
        """
        for match in _RE_MCL.finditer(text):
            section = match.group(1)
            citation_str = f"MCL {section}"
            key = self._normalize_citation(citation_str)
            if key not in citations:
                citations[key] = TOAEntry(
                    category=CitationCategory.STATUTES,
                    citation=citation_str,
                    full_text=match.group(0),
                    pages=[],
                )
            page = self._estimate_page_at_offset(text, match.start())
            if page not in citations[key].pages:
                citations[key].pages.append(page)

    def _extract_rules(
        self, text: str, citations: Dict[str, TOAEntry]
    ) -> None:
        """Extract court rule citations (MCR, MRE, MRPC, FRCP, etc.).

        Args:
            text: Filing text to scan.
            citations: Accumulator dict.
        """
        for match in _RE_MCR.finditer(text):
            rule_type = match.group(1).upper()
            rule_num = match.group(2)
            citation_str = f"{rule_type} {rule_num}"
            key = self._normalize_citation(citation_str)
            if key not in citations:
                citations[key] = TOAEntry(
                    category=CitationCategory.RULES,
                    citation=citation_str,
                    full_text=match.group(0),
                    pages=[],
                )
            page = self._estimate_page_at_offset(text, match.start())
            if page not in citations[key].pages:
                citations[key].pages.append(page)

    def _extract_constitutional(
        self, text: str, citations: Dict[str, TOAEntry]
    ) -> None:
        """Extract constitutional provision citations.

        Args:
            text: Filing text to scan.
            citations: Accumulator dict.
        """
        for match in _RE_CONST.finditer(text):
            raw = match.group(0).strip()
            if len(raw) < 10:
                continue  # Too short to be meaningful
            key = self._normalize_citation(raw)
            if key not in citations:
                citations[key] = TOAEntry(
                    category=CitationCategory.CONSTITUTIONAL,
                    citation=raw,
                    full_text=raw,
                    pages=[],
                )
            page = self._estimate_page_at_offset(text, match.start())
            if page not in citations[key].pages:
                citations[key].pages.append(page)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_citation(raw: str) -> str:
        """Normalize a citation string for deduplication.

        Args:
            raw: Raw citation text.

        Returns:
            Lowercased, whitespace-collapsed key.
        """
        return re.sub(r"\s+", " ", raw.strip().lower())

    def _estimate_page_at_offset(self, text: str, char_offset: int) -> int:
        """Estimate the page number at a character offset.

        Args:
            text: Full document text.
            char_offset: Character position in text.

        Returns:
            Estimated page number (1-based).
        """
        preceding = text[:char_offset]
        word_count = len(preceding.split())
        return max(1, math.ceil(word_count / self._words_per_page))

    def _estimate_total_pages(self, text: str) -> int:
        """Estimate total page count for the document.

        Args:
            text: Full document text.

        Returns:
            Estimated page count (minimum 1).
        """
        clean = re.sub(r"[#*`>|\-_]", " ", text)
        word_count = len(clean.split())
        return max(1, math.ceil(word_count / self._words_per_page))

    @staticmethod
    def _category_sort_key(category: str) -> int:
        """Return sort order for citation categories.

        Args:
            category: CitationCategory value.

        Returns:
            Integer sort key (lower = first).
        """
        order = {
            CitationCategory.CASES_MICHIGAN: 0,
            CitationCategory.CASES_FEDERAL: 1,
            CitationCategory.CASES_OTHER: 2,
            CitationCategory.STATUTES: 3,
            CitationCategory.RULES: 4,
            CitationCategory.CONSTITUTIONAL: 5,
            CitationCategory.OTHER: 6,
        }
        return order.get(category, 99)

    @staticmethod
    def _slugify(text: str) -> str:
        """Convert text to a URL-safe slug.

        Args:
            text: Input text.

        Returns:
            Lowercased, hyphenated slug.
        """
        slug = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower())
        return slug.strip("-")[:50]

    def _toc_entry_prefix(
        self, level: int, counters: Dict[str, int]
    ) -> Tuple[str, int]:
        """Generate hierarchical numbering prefix for a TOC entry.

        Follows appellate brief convention:
            Level 1: Roman numerals (I., II., III.)
            Level 2: Capital letters (A., B., C.)
            Level 3+: Arabic numbers (1., 2., 3.)

        Args:
            level: Heading level (1-4).
            counters: Mutable counter dict with keys 'roman', 'letter', 'number'.

        Returns:
            Tuple of (prefix_string, indent_spaces).
        """
        if level == 1:
            counters["roman"] += 1
            counters["letter"] = 0
            counters["number"] = 0
            return f"{_to_roman(counters['roman'])}. ", 0
        elif level == 2:
            counters["letter"] += 1
            counters["number"] = 0
            return f"{_to_letter(counters['letter'] - 1)}. ", 4
        else:
            counters["number"] += 1
            return f"{counters['number']}. ", 8

    @staticmethod
    def _format_dot_leader(
        left_text: str,
        right_text: str,
        total_width: int,
        dot_char: str = DOT_LEADER_CHAR,
        indent_level: int = 0,
    ) -> str:
        """Format a line with dot leaders between left and right text.

        Args:
            left_text: Text on the left side (title).
            right_text: Text on the right side (page number).
            total_width: Total character width of the line.
            dot_char: Character to use for the leader.
            indent_level: Number of indent levels (each = 4 spaces).

        Returns:
            Formatted string with dot leaders.
        """
        indent = "    " * indent_level
        left = f"{indent}{left_text} "
        right = f" {right_text}"
        available = total_width - len(left) - len(right)
        if available < 3:
            return f"{left}{right}"
        dots = dot_char * available
        return f"{left}{dots}{right}"

    def _check_required_sections(
        self, toc_entries: List[TOCEntry], court_type: str
    ) -> List[str]:
        """Check whether all court-required sections are present.

        Args:
            toc_entries: Current TOC entries.
            court_type: Court jurisdiction key.

        Returns:
            List of missing section names (empty if compliant).
        """
        if court_type == "coa":
            required = COA_REQUIRED_SECTIONS
        elif court_type == "msc":
            required = MSC_REQUIRED_SECTIONS
        else:
            return []

        found_titles = {e.title.upper().strip() for e in toc_entries}
        missing: List[str] = []

        for section in required:
            # Fuzzy match: check if any found title contains the required phrase
            matched = any(section in title for title in found_titles)
            if not matched:
                missing.append(section)

        return missing


# ---------------------------------------------------------------------------
# Module-level convenience functions
# ---------------------------------------------------------------------------

def generate_toc_toa(
    text: str, court_type: str = "coa"
) -> TOCTOAResult:
    """Convenience function to generate TOC and TOA.

    Args:
        text: Markdown filing text.
        court_type: Court jurisdiction key.

    Returns:
        TOCTOAResult with all formatted outputs.
    """
    gen = TOCTOAGenerator()
    return gen.generate(text, court_type=court_type)


def generate_toc(
    text: str, words_per_page: int = WORDS_PER_PAGE
) -> List[TOCEntry]:
    """Convenience function to generate only TOC entries.

    Args:
        text: Markdown filing text.
        words_per_page: Words-per-page for page estimation.

    Returns:
        List of TOCEntry.
    """
    gen = TOCTOAGenerator(words_per_page=words_per_page)
    return gen.generate_toc(text)


def generate_toa(text: str) -> List[TOAEntry]:
    """Convenience function to generate only TOA entries.

    Args:
        text: Filing text to scan for citations.

    Returns:
        Sorted list of TOAEntry.
    """
    gen = TOCTOAGenerator()
    return gen.generate_toa(text)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    if len(sys.argv) < 2:
        print("Usage: python toc_toa_generator.py <filing.md> [court_type]")
        print("  Court types: coa, msc, 14th_circuit, federal, jtc, admin")
        sys.exit(1)

    md_path = Path(sys.argv[1])
    court = sys.argv[2] if len(sys.argv) > 2 else "coa"

    if not md_path.exists():
        print(f"Error: File not found: {md_path}")
        sys.exit(1)

    content = md_path.read_text(encoding="utf-8", errors="replace")
    result = generate_toc_toa(content, court_type=court)

    print("=" * 60)
    print(result.toc_markdown)
    print("=" * 60)
    print(result.toa_markdown)
    print("=" * 60)

    stats = {
        "total_pages_estimated": result.total_pages_estimated,
        "case_count": result.case_count,
        "statute_count": result.statute_count,
        "rule_count": result.rule_count,
        "constitutional_count": result.constitutional_count,
        "other_count": result.other_count,
        "missing_sections": result.missing_sections,
        "warnings": result.warnings,
    }
    print(json.dumps(stats, indent=2))
