"""
LitigationOS Exhibit Stamper — Bates Numbering, Tabs, and Index Generation
===========================================================================

Stamps exhibits with PIGORS-XXXX Bates numbering, generates exhibit cover
pages, tab/divider pages, and a master exhibit index for court filing.

Integrates with:
    - EternalCodex_Pro/tools/bates_stamp.py — PDF Bates stamping
    - 00_SYSTEM/master_exhibit_index.json — 21 primary exhibits
    - 00_SYSTEM/engines/doc_assembly_engine.py — document assembly

Bates format: PIGORS-0001 through PIGORS-NNNN (4-digit zero-padded,
expandable to 6-digit for large collections).

Case: Pigors v. Watson, 2024-001507-DC
Plaintiff: Andrew James Pigors (Pro Se)
Defendant: Emily A. Watson
Judge: Hon. Jenny L. McNeill
"""

from __future__ import annotations

import hashlib
import html as html_mod
import json
import logging
import re
import textwrap
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DB_PATH = Path(__file__).resolve().parents[2] / "litigation_context.db"

MASTER_EXHIBIT_INDEX_PATH = (
    Path(__file__).resolve().parents[2] / "master_exhibit_index.json"
)

BATES_PREFIX = "PIGORS"
BATES_SEPARATOR = "-"
BATES_DIGITS = 4  # PIGORS-0001 (expandable)

CASE_INFO = {
    "plaintiff": "ANDREW J. PIGORS",
    "defendant": "EMILY A. WATSON",
    "case_name": "Pigors v. Watson",
    "trial_case_no": "2024-001507-DC",
    "coa_case_no": "366810",
    "judge": "Hon. Jenny L. McNeill",
    "court_14th": "14th Judicial Circuit Court, Muskegon County",
    "court_coa": "Michigan Court of Appeals",
}

# Authentication status values
class AuthStatus(str, Enum):
    """Exhibit authentication status."""

    AUTHENTICATED = "authenticated"
    PENDING = "pending"
    SELF_AUTHENTICATING = "self_authenticating"
    STIPULATED = "stipulated"
    OBJECTED = "objected"


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------
@dataclass
class ExhibitEntry:
    """A single exhibit in the filing package.

    Attributes:
        exhibit_letter: Letter designation (A, B, ... Z, AA, AB, ...).
        title: Short descriptive title of the exhibit.
        description: Longer description of exhibit content.
        bates_start: Starting Bates number (e.g., 'PIGORS-0001').
        bates_end: Ending Bates number (e.g., 'PIGORS-0015').
        page_count: Number of pages in the exhibit.
        source_file: Original source file path.
        filing_target: Which filing(s) this exhibit supports.
        authentication_status: Current authentication state.
        stacks_referenced: Litigation stacks that reference this exhibit.
        source_table: Database source table (e.g., 'exhibit_registry').
        sha256: Hash of the source file for integrity.
    """

    exhibit_letter: str = ""
    title: str = ""
    description: str = ""
    bates_start: str = ""
    bates_end: str = ""
    page_count: int = 0
    source_file: str = ""
    filing_target: str = ""
    authentication_status: str = AuthStatus.PENDING
    stacks_referenced: List[str] = field(default_factory=list)
    source_table: str = "exhibit_registry"
    sha256: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize entry to dictionary."""
        return asdict(self)

    @property
    def bates_range_str(self) -> str:
        """Human-readable Bates range string.

        Returns:
            String like 'PIGORS-0001 to PIGORS-0015' or single number.
        """
        if self.bates_end and self.bates_end != self.bates_start:
            return f"{self.bates_start} to {self.bates_end}"
        return self.bates_start

    @property
    def exhibit_label(self) -> str:
        """Full exhibit label (e.g., 'Exhibit A').

        Returns:
            Formatted exhibit label string.
        """
        return f"Exhibit {self.exhibit_letter}"


@dataclass
class ExhibitPackage:
    """Complete exhibit package for court filing.

    Attributes:
        exhibits: Ordered list of exhibit entries.
        master_index_markdown: Formatted master index as Markdown.
        master_index_html: Formatted master index as HTML.
        cover_pages: Dict of exhibit_letter -> cover page Markdown.
        tab_pages: Dict of exhibit_letter -> tab page Markdown.
        total_pages: Total page count across all exhibits.
        bates_range: Tuple of (first_bates, last_bates).
        case_caption: Case caption used in the package.
        generated_at: ISO-8601 generation timestamp.
        warnings: Any packaging warnings.
    """

    exhibits: List[ExhibitEntry] = field(default_factory=list)
    master_index_markdown: str = ""
    master_index_html: str = ""
    cover_pages: Dict[str, str] = field(default_factory=dict)
    tab_pages: Dict[str, str] = field(default_factory=dict)
    total_pages: int = 0
    bates_range: Tuple[str, str] = ("", "")
    case_caption: str = ""
    generated_at: str = ""
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize package to dictionary."""
        return {
            "exhibits": [e.to_dict() for e in self.exhibits],
            "master_index_markdown": self.master_index_markdown,
            "master_index_html": self.master_index_html,
            "cover_pages": self.cover_pages,
            "tab_pages": self.tab_pages,
            "total_pages": self.total_pages,
            "bates_range": list(self.bates_range),
            "case_caption": self.case_caption,
            "generated_at": self.generated_at,
            "warnings": self.warnings,
        }


# ---------------------------------------------------------------------------
# ExhibitStamper
# ---------------------------------------------------------------------------
class ExhibitStamper:
    """Bates stamp, tab, and index exhibits for court filing.

    Provides sequential PIGORS-XXXX numbering, exhibit letter assignment,
    cover/tab page generation, and master index creation.

    Usage::

        stamper = ExhibitStamper()
        package = stamper.stamp_exhibits([
            {"title": "Court Order", "page_count": 3, "source_file": "order.pdf"},
            {"title": "Email Chain",  "page_count": 7, "source_file": "emails.pdf"},
        ], start_bates=1)
        print(package.master_index_markdown)

    Integration:
        - Bates format matches bates_stamp.py (PIGORS prefix)
        - Index structure matches master_exhibit_index.json schema
    """

    def __init__(
        self,
        prefix: str = BATES_PREFIX,
        separator: str = BATES_SEPARATOR,
        digits: int = BATES_DIGITS,
    ) -> None:
        """Initialize the exhibit stamper.

        Args:
            prefix: Bates number prefix (default 'PIGORS').
            separator: Separator between prefix and number (default '-').
            digits: Minimum zero-padded digit count (default 4).
        """
        self._prefix = prefix
        self._separator = separator
        self._digits = digits
        self._stamp_count = 0
        self._total_exhibits_processed = 0
        self._total_pages_stamped = 0
        logger.info(
            "ExhibitStamper initialized (prefix=%s, digits=%d)",
            prefix, digits,
        )

    # ------------------------------------------------------------------
    # Bates Number Generation
    # ------------------------------------------------------------------

    def format_bates(self, number: int) -> str:
        """Format a Bates number with prefix and zero-padding.

        Args:
            number: The sequential number (1-based).

        Returns:
            Formatted Bates string (e.g., 'PIGORS-0001').
        """
        # Auto-expand digits if number exceeds current width
        effective_digits = max(self._digits, len(str(number)))
        return f"{self._prefix}{self._separator}{number:0{effective_digits}d}"

    def next_bates_number(self, current: str) -> str:
        """Compute the next sequential Bates number.

        Args:
            current: Current Bates string (e.g., 'PIGORS-0015').

        Returns:
            Next Bates string (e.g., 'PIGORS-0016').
        """
        num = self.parse_bates_number(current)
        return self.format_bates(num + 1)

    def parse_bates_number(self, bates_str: str) -> int:
        """Extract the numeric portion from a Bates string.

        Args:
            bates_str: Bates string (e.g., 'PIGORS-0015').

        Returns:
            Integer value (e.g., 15).

        Raises:
            ValueError: If the string cannot be parsed.
        """
        # Match pattern: PREFIX-DIGITS or PREFIXDIGITS
        match = re.search(r"(\d+)$", bates_str)
        if not match:
            raise ValueError(f"Cannot parse Bates number from: {bates_str}")
        return int(match.group(1))

    @staticmethod
    def letter_sequence(n: int) -> str:
        """Convert a zero-based index to an exhibit letter designation.

        0->A, 1->B, ..., 25->Z, 26->AA, 27->AB, ..., 51->AZ, 52->BA, etc.

        Args:
            n: Zero-based exhibit index.

        Returns:
            Uppercase letter designation string.
        """
        if n < 0:
            return ""
        result: List[str] = []
        remaining = n
        while True:
            result.append(chr(65 + (remaining % 26)))
            remaining = remaining // 26 - 1
            if remaining < 0:
                break
        return "".join(reversed(result))

    @staticmethod
    def letter_to_index(letter: str) -> int:
        """Convert an exhibit letter designation to zero-based index.

        A->0, B->1, ..., Z->25, AA->26, AB->27, etc.

        Args:
            letter: Uppercase letter designation.

        Returns:
            Zero-based index.
        """
        letter = letter.upper().strip()
        result = 0
        for i, ch in enumerate(letter):
            result = result * 26 + (ord(ch) - 64)
        return result - 1

    # ------------------------------------------------------------------
    # Core Stamping API
    # ------------------------------------------------------------------

    def stamp_exhibits(
        self,
        exhibits: List[Dict[str, Any]],
        start_bates: int = 1,
        start_letter_index: int = 0,
        case_caption: str = "",
    ) -> ExhibitPackage:
        """Stamp a list of exhibits with Bates numbers and letters.

        Args:
            exhibits: List of exhibit dicts with keys:
                - 'title' (str): Exhibit title.
                - 'description' (str, optional): Exhibit description.
                - 'page_count' (int): Number of pages.
                - 'source_file' (str, optional): Source file path.
                - 'filing_target' (str, optional): Target filing.
                - 'authentication_status' (str, optional): Auth status.
                - 'stacks_referenced' (list, optional): Stack references.
            start_bates: Starting Bates number (default 1).
            start_letter_index: Starting letter index (default 0 = A).
            case_caption: Case caption for index header.

        Returns:
            ExhibitPackage with all generated materials.
        """
        if not case_caption:
            case_caption = (
                f"{CASE_INFO['case_name']}\n"
                f"Case No. {CASE_INFO['trial_case_no']}\n"
                f"{CASE_INFO['judge']}"
            )

        warnings: List[str] = []
        entries: List[ExhibitEntry] = []
        cover_pages: Dict[str, str] = {}
        tab_pages: Dict[str, str] = {}
        current_bates = start_bates
        letter_idx = start_letter_index

        for idx, exhibit_spec in enumerate(exhibits):
            try:
                title = exhibit_spec.get("title", f"Exhibit {letter_idx + 1}")
                description = exhibit_spec.get("description", "")
                page_count = exhibit_spec.get("page_count", 1)
                source_file = exhibit_spec.get("source_file", "")
                filing_target = exhibit_spec.get("filing_target", "")
                auth_status = exhibit_spec.get(
                    "authentication_status", AuthStatus.PENDING
                )
                stacks = exhibit_spec.get("stacks_referenced", [])

                letter = self.letter_sequence(letter_idx)
                bates_start = self.format_bates(current_bates)
                bates_end = self.format_bates(current_bates + page_count - 1)

                # Compute source file hash if path exists
                file_hash = ""
                if source_file:
                    source_path = Path(source_file)
                    if source_path.exists():
                        file_hash = self._sha256_file(source_path)

                entry = ExhibitEntry(
                    exhibit_letter=letter,
                    title=title,
                    description=description,
                    bates_start=bates_start,
                    bates_end=bates_end if page_count > 1 else bates_start,
                    page_count=page_count,
                    source_file=source_file,
                    filing_target=filing_target,
                    authentication_status=auth_status,
                    stacks_referenced=stacks,
                    sha256=file_hash,
                )

                entries.append(entry)

                # Generate cover and tab pages
                cover_pages[letter] = self.generate_cover_page(entry)
                tab_pages[letter] = self.generate_tab_page(entry)

                current_bates += page_count
                letter_idx += 1

            except Exception as exc:
                logger.error("Error stamping exhibit %d: %s", idx, exc)
                warnings.append(f"Exhibit {idx} error: {exc}")

        # Compute totals
        total_pages = sum(e.page_count for e in entries)
        first_bates = entries[0].bates_start if entries else ""
        last_bates = entries[-1].bates_end if entries else ""

        # Build package
        package = ExhibitPackage(
            exhibits=entries,
            cover_pages=cover_pages,
            tab_pages=tab_pages,
            total_pages=total_pages,
            bates_range=(first_bates, last_bates),
            case_caption=case_caption,
            generated_at=datetime.now(timezone.utc).isoformat(),
            warnings=warnings,
        )

        # Generate indexes
        package.master_index_markdown = self.generate_master_index(
            package, case_caption
        )
        package.master_index_html = self.generate_master_index_html(package)

        # Update stats
        self._stamp_count += 1
        self._total_exhibits_processed += len(entries)
        self._total_pages_stamped += total_pages

        return package

    # ------------------------------------------------------------------
    # Cover Page Generation
    # ------------------------------------------------------------------

    def generate_cover_page(self, exhibit: ExhibitEntry) -> str:
        """Generate a cover page for a single exhibit.

        The cover page includes the exhibit designation, title, Bates
        range, and case information.

        Args:
            exhibit: The exhibit entry to create a cover for.

        Returns:
            Formatted Markdown cover page string.
        """
        today = datetime.now().strftime("%B %d, %Y")
        auth_display = exhibit.authentication_status.replace("_", " ").title()

        cover = textwrap.dedent(f"""\
        ---

        # {exhibit.exhibit_label}

        ---

        **{CASE_INFO['case_name']}**

        Case No. {CASE_INFO['trial_case_no']}

        {CASE_INFO['judge']}

        ---

        ## {exhibit.exhibit_label}: {exhibit.title}

        {exhibit.description}

        | Field | Value |
        |-------|-------|
        | Exhibit | {exhibit.exhibit_letter} |
        | Title | {exhibit.title} |
        | Bates Range | {exhibit.bates_range_str} |
        | Page Count | {exhibit.page_count} |
        | Authentication | {auth_display} |
        | Filing Target | {exhibit.filing_target} |
        | Source File | {exhibit.source_file or 'N/A'} |

        ---

        *This exhibit is offered in support of the claims and arguments
        set forth in the accompanying filing.*

        Dated: {today}

        ANDREW J. PIGORS, Pro Se

        ---
        """)
        return cover

    # ------------------------------------------------------------------
    # Tab Page Generation
    # ------------------------------------------------------------------

    def generate_tab_page(self, exhibit: ExhibitEntry) -> str:
        """Generate a tab/divider page for a single exhibit.

        A minimal page designed to be printed on a tab divider.

        Args:
            exhibit: The exhibit entry.

        Returns:
            Formatted Markdown tab page string.
        """
        tab = textwrap.dedent(f"""\
        ---

        # EXHIBIT {exhibit.exhibit_letter}

        **{exhibit.title}**

        {exhibit.bates_range_str}

        ({exhibit.page_count} page{'s' if exhibit.page_count != 1 else ''})

        ---
        """)
        return tab

    # ------------------------------------------------------------------
    # Master Index Generation (Markdown)
    # ------------------------------------------------------------------

    def generate_master_index(
        self, package: ExhibitPackage, case_caption: str = ""
    ) -> str:
        """Generate a master exhibit index in Markdown format.

        Args:
            package: The complete exhibit package.
            case_caption: Case caption for the header.

        Returns:
            Formatted Markdown master index string.
        """
        if not case_caption:
            case_caption = package.case_caption

        today = datetime.now().strftime("%B %d, %Y")
        bates_first, bates_last = package.bates_range

        lines: List[str] = [
            "# MASTER EXHIBIT INDEX",
            "",
            f"**{CASE_INFO['case_name']}**",
            f"Case No. {CASE_INFO['trial_case_no']}",
            f"{CASE_INFO['judge']}",
            "",
            f"Date: {today}",
            f"Total Exhibits: {len(package.exhibits)}",
            f"Total Pages: {package.total_pages}",
            f"Bates Range: {bates_first} to {bates_last}",
            "",
            "---",
            "",
            "| Exhibit | Title | Bates Range | Pages | Authentication | Filing Target |",
            "|---------|-------|-------------|-------|----------------|---------------|",
        ]

        for entry in package.exhibits:
            auth_display = entry.authentication_status.replace("_", " ").title()
            lines.append(
                f"| {entry.exhibit_letter} "
                f"| {entry.title} "
                f"| {entry.bates_range_str} "
                f"| {entry.page_count} "
                f"| {auth_display} "
                f"| {entry.filing_target} |"
            )

        lines.extend([
            "",
            "---",
            "",
            "## Authentication Legend",
            "",
            "- **Authenticated**: Verified authentic through testimony or affidavit",
            "- **Self Authenticating**: MRE 902 self-authenticating document",
            "- **Pending**: Authentication to be established at hearing",
            "- **Stipulated**: Parties have stipulated to authenticity",
            "- **Objected**: Opposing party has objected to authenticity",
            "",
            "---",
            "",
            f"*Generated by LitigationOS Exhibit Stamper — {today}*",
            "",
        ])

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Master Index Generation (HTML)
    # ------------------------------------------------------------------

    def generate_master_index_html(self, package: ExhibitPackage) -> str:
        """Generate a master exhibit index in HTML format.

        Args:
            package: The complete exhibit package.

        Returns:
            Complete HTML string with embedded CSS.
        """
        today = datetime.now().strftime("%B %d, %Y")
        bates_first, bates_last = package.bates_range

        css = textwrap.dedent("""\
        <style>
        .exhibit-index {
            font-family: "Times New Roman", Times, serif;
            font-size: 12pt;
            max-width: 7.5in;
            margin: 0 auto;
        }
        .exhibit-index h1 {
            text-align: center;
            font-size: 14pt;
            text-transform: uppercase;
        }
        .exhibit-index .case-info {
            text-align: center;
            margin-bottom: 1em;
        }
        .exhibit-index table {
            border-collapse: collapse;
            width: 100%;
            margin: 1em 0;
        }
        .exhibit-index th, .exhibit-index td {
            border: 1px solid #000;
            padding: 4px 8px;
            text-align: left;
            font-size: 11pt;
        }
        .exhibit-index th {
            background-color: #f0f0f0;
            font-weight: bold;
        }
        .exhibit-index .summary {
            margin: 1em 0;
            font-size: 11pt;
        }
        .exhibit-index .legend {
            margin-top: 1em;
            font-size: 10pt;
        }
        .exhibit-index .footer {
            margin-top: 2em;
            text-align: center;
            font-size: 9pt;
            font-style: italic;
            color: #666;
        }
        @media print {
            .exhibit-index { max-width: none; }
        }
        </style>
        """)

        # Table rows
        rows: List[str] = []
        for entry in package.exhibits:
            auth_display = html_mod.escape(
                entry.authentication_status.replace("_", " ").title()
            )
            rows.append(
                "<tr>"
                f"<td>{html_mod.escape(entry.exhibit_letter)}</td>"
                f"<td>{html_mod.escape(entry.title)}</td>"
                f"<td>{html_mod.escape(entry.bates_range_str)}</td>"
                f"<td>{entry.page_count}</td>"
                f"<td>{auth_display}</td>"
                f"<td>{html_mod.escape(entry.filing_target)}</td>"
                "</tr>"
            )

        table_body = "\n".join(rows)

        html_content = textwrap.dedent(f"""\
        {css}
        <div class="exhibit-index">
            <h1>Master Exhibit Index</h1>
            <div class="case-info">
                <strong>{html_mod.escape(CASE_INFO['case_name'])}</strong><br>
                Case No. {html_mod.escape(CASE_INFO['trial_case_no'])}<br>
                {html_mod.escape(CASE_INFO['judge'])}
            </div>
            <div class="summary">
                <strong>Date:</strong> {html_mod.escape(today)}<br>
                <strong>Total Exhibits:</strong> {len(package.exhibits)}<br>
                <strong>Total Pages:</strong> {package.total_pages}<br>
                <strong>Bates Range:</strong> {html_mod.escape(bates_first)} to {html_mod.escape(bates_last)}
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Exhibit</th>
                        <th>Title</th>
                        <th>Bates Range</th>
                        <th>Pages</th>
                        <th>Authentication</th>
                        <th>Filing Target</th>
                    </tr>
                </thead>
                <tbody>
        {table_body}
                </tbody>
            </table>
            <div class="legend">
                <strong>Authentication Legend:</strong><br>
                <strong>Authenticated</strong> — Verified authentic through testimony or affidavit<br>
                <strong>Self Authenticating</strong> — MRE 902 self-authenticating document<br>
                <strong>Pending</strong> — Authentication to be established at hearing<br>
                <strong>Stipulated</strong> — Parties have stipulated to authenticity<br>
                <strong>Objected</strong> — Opposing party has objected to authenticity
            </div>
            <div class="footer">
                Generated by LitigationOS Exhibit Stamper &mdash; {html_mod.escape(today)}
            </div>
        </div>
        """)

        return html_content

    # ------------------------------------------------------------------
    # Loading & Merging
    # ------------------------------------------------------------------

    def load_existing_index(
        self, json_path: Optional[Union[str, Path]] = None
    ) -> List[ExhibitEntry]:
        """Load existing exhibits from master_exhibit_index.json.

        Args:
            json_path: Path to the JSON index file.  Defaults to the
                standard location.

        Returns:
            List of ExhibitEntry parsed from the JSON file.
        """
        json_path = Path(json_path) if json_path else MASTER_EXHIBIT_INDEX_PATH

        if not json_path.exists():
            logger.warning("Exhibit index not found: %s", json_path)
            return []

        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            logger.error("Failed to load exhibit index: %s", exc)
            return []

        entries: List[ExhibitEntry] = []
        for item in data.get("exhibits", []):
            try:
                # Parse exhibit letter from "Exhibit A" format
                exhibit_number = item.get("exhibit_number", "")
                letter = exhibit_number.replace("Exhibit ", "").strip()

                entries.append(ExhibitEntry(
                    exhibit_letter=letter,
                    title=item.get("title", ""),
                    description=item.get("description", ""),
                    bates_start=item.get("bates_start", ""),
                    bates_end=item.get("bates_end", "") or item.get("bates_start", ""),
                    page_count=self._compute_page_count_from_bates(
                        item.get("bates_start", ""),
                        item.get("bates_end", ""),
                    ),
                    filing_target=item.get("filing_target", ""),
                    authentication_status=item.get(
                        "authentication_status", AuthStatus.PENDING
                    ),
                    stacks_referenced=item.get("stacks_referenced", []),
                    source_table=item.get("source_table", "exhibit_registry"),
                ))
            except Exception as exc:
                logger.warning("Skipping malformed exhibit entry: %s", exc)

        logger.info("Loaded %d existing exhibits from %s", len(entries), json_path)
        return entries

    def merge_indexes(
        self,
        existing: List[ExhibitEntry],
        new: List[ExhibitEntry],
    ) -> ExhibitPackage:
        """Merge existing and new exhibit entries into a unified package.

        Existing entries are preserved; new entries are appended with
        sequential Bates numbers continuing from the highest existing number.

        Args:
            existing: Previously stamped exhibit entries.
            new: New exhibit entries to add.

        Returns:
            ExhibitPackage with merged exhibits.
        """
        warnings: List[str] = []

        # Find the highest existing Bates number
        max_bates = 0
        for entry in existing:
            try:
                if entry.bates_end:
                    max_bates = max(max_bates, self.parse_bates_number(entry.bates_end))
                elif entry.bates_start:
                    max_bates = max(max_bates, self.parse_bates_number(entry.bates_start))
            except ValueError:
                pass

        # Find the highest existing letter index
        max_letter_idx = -1
        for entry in existing:
            if entry.exhibit_letter:
                try:
                    idx = self.letter_to_index(entry.exhibit_letter)
                    max_letter_idx = max(max_letter_idx, idx)
                except Exception:
                    pass

        # Stamp new entries continuing from existing
        new_start_bates = max_bates + 1
        new_start_letter = max_letter_idx + 1

        merged_exhibits = list(existing)
        cover_pages: Dict[str, str] = {}
        tab_pages: Dict[str, str] = {}
        current_bates = new_start_bates
        letter_idx = new_start_letter

        for entry in new:
            letter = self.letter_sequence(letter_idx)
            bates_start = self.format_bates(current_bates)
            page_count = entry.page_count or 1
            bates_end = self.format_bates(current_bates + page_count - 1)

            stamped = ExhibitEntry(
                exhibit_letter=letter,
                title=entry.title,
                description=entry.description,
                bates_start=bates_start,
                bates_end=bates_end if page_count > 1 else bates_start,
                page_count=page_count,
                source_file=entry.source_file,
                filing_target=entry.filing_target,
                authentication_status=entry.authentication_status,
                stacks_referenced=entry.stacks_referenced,
                sha256=entry.sha256,
            )

            merged_exhibits.append(stamped)
            cover_pages[letter] = self.generate_cover_page(stamped)
            tab_pages[letter] = self.generate_tab_page(stamped)

            current_bates += page_count
            letter_idx += 1

        # Build merged package
        total_pages = sum(e.page_count for e in merged_exhibits)
        first_bates = merged_exhibits[0].bates_start if merged_exhibits else ""
        last_entry = merged_exhibits[-1] if merged_exhibits else None
        last_bates = last_entry.bates_end if last_entry else ""

        package = ExhibitPackage(
            exhibits=merged_exhibits,
            cover_pages=cover_pages,
            tab_pages=tab_pages,
            total_pages=total_pages,
            bates_range=(first_bates, last_bates),
            case_caption=f"{CASE_INFO['case_name']}\nCase No. {CASE_INFO['trial_case_no']}",
            generated_at=datetime.now(timezone.utc).isoformat(),
            warnings=warnings,
        )

        package.master_index_markdown = self.generate_master_index(package)
        package.master_index_html = self.generate_master_index_html(package)

        return package

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate_bates_sequence(
        self, entries: List[ExhibitEntry]
    ) -> List[str]:
        """Validate that Bates numbers form a contiguous sequence.

        Checks for:
            - Gaps in the Bates numbering
            - Overlapping ranges
            - Invalid Bates format
            - Mismatched page counts

        Args:
            entries: List of exhibit entries to validate.

        Returns:
            List of warning/error strings.  Empty if valid.
        """
        issues: List[str] = []

        if not entries:
            return issues

        prev_end = 0
        for entry in entries:
            try:
                start_num = self.parse_bates_number(entry.bates_start)
            except ValueError as exc:
                issues.append(
                    f"Exhibit {entry.exhibit_letter}: Invalid bates_start "
                    f"'{entry.bates_start}': {exc}"
                )
                continue

            try:
                end_str = entry.bates_end or entry.bates_start
                end_num = self.parse_bates_number(end_str)
            except ValueError as exc:
                issues.append(
                    f"Exhibit {entry.exhibit_letter}: Invalid bates_end "
                    f"'{entry.bates_end}': {exc}"
                )
                continue

            # Check sequence continuity
            if prev_end > 0 and start_num != prev_end + 1:
                if start_num <= prev_end:
                    issues.append(
                        f"Exhibit {entry.exhibit_letter}: Bates overlap — "
                        f"starts at {start_num} but previous ended at {prev_end}"
                    )
                else:
                    gap = start_num - prev_end - 1
                    issues.append(
                        f"Exhibit {entry.exhibit_letter}: Bates gap of {gap} "
                        f"numbers between {prev_end} and {start_num}"
                    )

            # Check page count consistency
            computed_pages = end_num - start_num + 1
            if computed_pages != entry.page_count and entry.page_count > 0:
                issues.append(
                    f"Exhibit {entry.exhibit_letter}: Page count mismatch — "
                    f"Bates range implies {computed_pages} pages but "
                    f"page_count is {entry.page_count}"
                )

            # Check start <= end
            if end_num < start_num:
                issues.append(
                    f"Exhibit {entry.exhibit_letter}: bates_end ({end_num}) "
                    f"is less than bates_start ({start_num})"
                )

            prev_end = end_num

        return issues

    # ------------------------------------------------------------------
    # Export to JSON (master_exhibit_index.json compatible)
    # ------------------------------------------------------------------

    def export_to_json(
        self,
        package: ExhibitPackage,
        output_path: Optional[Union[str, Path]] = None,
    ) -> str:
        """Export exhibit package to master_exhibit_index.json format.

        Args:
            package: The exhibit package to export.
            output_path: Destination path.  If None, returns JSON string only.

        Returns:
            JSON string of the exported index.
        """
        export_data = {
            "generated": datetime.now(timezone.utc).isoformat(),
            "agent": "ExhibitStamper-v1.0",
            "case": f"{CASE_INFO['case_name']}, {CASE_INFO['trial_case_no']}",
            "total_primary_exhibits": len(package.exhibits),
            "total_source_documents": 0,
            "exhibits": [],
            "source_document_categories": {},
        }

        for entry in package.exhibits:
            export_data["exhibits"].append({
                "exhibit_number": entry.exhibit_label,
                "title": entry.title,
                "bates_start": entry.bates_start,
                "bates_end": entry.bates_end or None,
                "description": entry.description,
                "filing_target": entry.filing_target,
                "stacks_referenced": entry.stacks_referenced,
                "authentication_status": entry.authentication_status,
                "source_table": entry.source_table,
            })

        json_str = json.dumps(export_data, indent=2, ensure_ascii=False)

        if output_path:
            output_path = Path(output_path)
            try:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(json_str, encoding="utf-8")
                logger.info("Exported exhibit index to %s", output_path)
            except OSError as exc:
                logger.error("Failed to export exhibit index: %s", exc)

        return json_str

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        """Return stamper statistics.

        Returns:
            Dict with stamping counts and configuration.
        """
        return {
            "stamper": "ExhibitStamper",
            "version": "1.0.0",
            "prefix": self._prefix,
            "separator": self._separator,
            "digits": self._digits,
            "stamp_count": self._stamp_count,
            "total_exhibits_processed": self._total_exhibits_processed,
            "total_pages_stamped": self._total_pages_stamped,
            "master_index_path": str(MASTER_EXHIBIT_INDEX_PATH),
            "db_path": str(DB_PATH),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _compute_page_count_from_bates(
        self, bates_start: str, bates_end: Optional[str]
    ) -> int:
        """Compute page count from Bates range.

        Args:
            bates_start: Starting Bates number string.
            bates_end: Ending Bates number string (may be None or empty).

        Returns:
            Computed page count (minimum 1).
        """
        if not bates_start:
            return 1
        if not bates_end:
            return 1
        try:
            start = self.parse_bates_number(bates_start)
            end = self.parse_bates_number(bates_end)
            return max(1, end - start + 1)
        except ValueError:
            return 1

    @staticmethod
    def _sha256_file(path: Path) -> str:
        """Compute SHA-256 hex digest of a file.

        Args:
            path: File path.

        Returns:
            Hex digest string, or empty string on error.
        """
        try:
            h = hashlib.sha256()
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    h.update(chunk)
            return h.hexdigest()
        except OSError as exc:
            logger.warning("SHA-256 failed for %s: %s", path, exc)
            return ""


# ---------------------------------------------------------------------------
# Module-level convenience functions
# ---------------------------------------------------------------------------

def stamp_exhibits(
    exhibits: List[Dict[str, Any]],
    start_bates: int = 1,
    case_caption: str = "",
) -> ExhibitPackage:
    """Convenience function to stamp exhibits.

    Args:
        exhibits: List of exhibit specification dicts.
        start_bates: Starting Bates number.
        case_caption: Case caption for index header.

    Returns:
        ExhibitPackage with all generated materials.
    """
    stamper = ExhibitStamper()
    return stamper.stamp_exhibits(
        exhibits, start_bates=start_bates, case_caption=case_caption
    )


def load_master_index(
    json_path: Optional[Union[str, Path]] = None,
) -> List[ExhibitEntry]:
    """Convenience function to load the master exhibit index.

    Args:
        json_path: Path to the JSON file.  Defaults to standard location.

    Returns:
        List of ExhibitEntry from the index.
    """
    stamper = ExhibitStamper()
    return stamper.load_existing_index(json_path)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    if len(sys.argv) < 2:
        print("Usage: python exhibit_stamper.py <command> [args]")
        print("  Commands:")
        print("    load                  — Load and display existing exhibit index")
        print("    stamp <json_spec>     — Stamp exhibits from JSON specification")
        print("    validate              — Validate existing exhibit Bates sequence")
        print("    stats                 — Show stamper statistics")
        sys.exit(1)

    command = sys.argv[1].lower()
    stamper = ExhibitStamper()

    if command == "load":
        entries = stamper.load_existing_index()
        for entry in entries:
            print(
                f"  {entry.exhibit_label}: {entry.title} "
                f"({entry.bates_range_str})"
            )
        print(f"\nTotal: {len(entries)} exhibits")

    elif command == "validate":
        entries = stamper.load_existing_index()
        issues = stamper.validate_bates_sequence(entries)
        if issues:
            print("Validation issues:")
            for issue in issues:
                print(f"  ⚠ {issue}")
        else:
            print("✓ Bates sequence is valid")

    elif command == "stamp":
        if len(sys.argv) < 3:
            print("Usage: python exhibit_stamper.py stamp <spec.json>")
            sys.exit(1)
        spec_path = Path(sys.argv[2])
        if not spec_path.exists():
            print(f"Error: File not found: {spec_path}")
            sys.exit(1)
        spec_data = json.loads(spec_path.read_text(encoding="utf-8"))
        exhibits = spec_data.get("exhibits", spec_data)
        if isinstance(exhibits, dict):
            exhibits = [exhibits]
        package = stamper.stamp_exhibits(exhibits)
        print(package.master_index_markdown)

    elif command == "stats":
        print(json.dumps(stamper.get_stats(), indent=2))

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
