"""
LitigationOS PDF Generator — Court-Formatted PDF from Markdown
===============================================================

Converts Markdown filing documents to court-formatted PDFs compliant with
Michigan court rules (MCR 2.119, MCR 7.212, MCR 7.306) and Federal rules
(FRCP + Local Rules WDMI).

Uses reportlab if available; falls back to HTML generation for manual
browser-to-PDF printing. Zero external dependencies required.

Integration points:
    - 00_SYSTEM/engines/doc_assembly_engine.py — reportlab styles/fonts
    - 00_SYSTEM/engines/filing_assembly_pipeline.py — COURT_FORMATS, CASE_INFO
    - 00_SYSTEM/legal_ai/caption_generator.py — court caption blocks

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
import math
import re
import textwrap
from collections import OrderedDict
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional dependency: reportlab
# ---------------------------------------------------------------------------
_HAS_REPORTLAB = False
try:
    from reportlab.lib.pagesizes import letter  # type: ignore[import-untyped]
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle  # type: ignore
    from reportlab.lib.units import inch  # type: ignore
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY  # type: ignore
    from reportlab.platypus import (  # type: ignore
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        PageBreak,
        Table,
        TableStyle,
        KeepTogether,
    )
    from reportlab.lib import colors  # type: ignore
    from reportlab.pdfbase import pdfmetrics  # type: ignore
    from reportlab.pdfbase.ttfonts import TTFont  # type: ignore

    _HAS_REPORTLAB = True
except ImportError:
    logger.info("reportlab not available — HTML fallback will be used for PDF generation")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DB_PATH = Path(__file__).resolve().parents[2] / "litigation_context.db"

WORDS_PER_PAGE = 250

CASE_INFO = {
    "plaintiff": "ANDREW J. PIGORS",
    "defendant": "EMILY A. WATSON",
    "case_name": "Pigors v. Watson",
    "trial_case_no": "2024-001507-DC",
    "coa_case_no": "366810",
    "court_14th": "14th Judicial Circuit Court, Muskegon County",
    "court_coa": "Michigan Court of Appeals",
    "court_msc": "Michigan Supreme Court",
    "court_wdmi": (
        "United States District Court, "
        "Western District of Michigan, Southern Division"
    ),
    "judge": "Hon. Jenny L. McNeill",
}


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------
class CourtType(str, Enum):
    """Supported court jurisdictions."""

    CIRCUIT_14TH = "14th_circuit"
    COA = "coa"
    MSC = "msc"
    FEDERAL = "federal"
    JTC = "jtc"
    ADMIN = "admin"


class ElementType(str, Enum):
    """Parsed Markdown element types."""

    HEADING = "heading"
    PARAGRAPH = "paragraph"
    BOLD = "bold"
    ITALIC = "italic"
    NUMBERED_LIST = "numbered_list"
    BULLET_LIST = "bullet_list"
    BLOCKQUOTE = "blockquote"
    HORIZONTAL_RULE = "horizontal_rule"
    TABLE = "table"
    CODE_BLOCK = "code_block"
    EMPTY = "empty"


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------
@dataclass
class PDFConfig:
    """Configuration for court-formatted PDF output.

    All measurements are in inches unless otherwise noted.
    Line spacing is a multiplier (2.0 = double-spaced).
    """

    font_family: str = "Times New Roman"
    font_size: int = 12
    line_spacing: float = 2.0
    margin_top: float = 1.0
    margin_bottom: float = 1.0
    margin_left: float = 1.0
    margin_right: float = 1.0
    page_width: float = 8.5
    page_height: float = 11.0
    page_numbering: bool = True
    page_number_position: str = "bottom_center"
    court_type: str = "14th_circuit"
    court_rule: str = "MCR 2.119"
    include_caption: bool = True
    include_certificate_of_service: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Serialize configuration to dictionary."""
        return asdict(self)

    @property
    def content_width_inches(self) -> float:
        """Usable content width after margins."""
        return self.page_width - self.margin_left - self.margin_right

    @property
    def content_height_inches(self) -> float:
        """Usable content height after margins."""
        return self.page_height - self.margin_top - self.margin_bottom


@dataclass
class PDFResult:
    """Result of a PDF generation operation.

    Attributes:
        output_path: Absolute path to the generated file.
        page_count: Number of pages in the output.
        word_count: Total word count of the source text.
        file_size_bytes: Size of the output file in bytes.
        method: Generation method used ('reportlab' or 'html_fallback').
        warnings: Any compliance or formatting warnings.
        generated_at: ISO-8601 timestamp of generation.
        sha256: Hex digest of the output file.
    """

    output_path: str = ""
    page_count: int = 0
    word_count: int = 0
    file_size_bytes: int = 0
    method: str = "html_fallback"
    warnings: List[str] = field(default_factory=list)
    generated_at: str = ""
    sha256: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize result to dictionary."""
        return asdict(self)


@dataclass
class ParsedElement:
    """A single parsed Markdown element.

    Attributes:
        element_type: The type of element (heading, paragraph, etc.).
        text: Raw text content of the element.
        level: Heading level (1-4) or list nesting depth.
        children: Sub-elements (e.g., table rows).
        meta: Arbitrary metadata for the element.
    """

    element_type: ElementType = ElementType.PARAGRAPH
    text: str = ""
    level: int = 0
    children: List[Dict[str, Any]] = field(default_factory=list)
    meta: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize element to dictionary."""
        return {
            "element_type": self.element_type.value,
            "text": self.text,
            "level": self.level,
            "children": self.children,
            "meta": self.meta,
        }


# ---------------------------------------------------------------------------
# LitigationPDFGenerator
# ---------------------------------------------------------------------------
class LitigationPDFGenerator:
    """Generate court-formatted PDFs from Markdown filing documents.

    Supports Michigan state courts (14th Circuit, COA, MSC), Federal
    (WDMI), JTC, and administrative agencies.  Uses reportlab when
    available; otherwise generates a print-ready HTML file.

    Usage::

        gen = LitigationPDFGenerator()
        result = gen.generate(markdown_text, "output.pdf", court_type="coa")
        print(result.page_count, result.method)

    Integration:
        - Court formats aligned with filing_assembly_pipeline.COURT_FORMATS
        - reportlab styles aligned with doc_assembly_engine._build_pdf_styles
    """

    # Court-specific configurations
    COURT_CONFIGS: Dict[str, PDFConfig] = {
        "14th_circuit": PDFConfig(
            line_spacing=2.0,
            court_type="14th_circuit",
            court_rule="MCR 2.119",
        ),
        "coa": PDFConfig(
            line_spacing=2.0,
            court_type="coa",
            court_rule="MCR 7.212",
        ),
        "msc": PDFConfig(
            line_spacing=2.0,
            court_type="msc",
            court_rule="MCR 7.306",
        ),
        "federal": PDFConfig(
            line_spacing=2.0,
            court_type="federal",
            court_rule="FRCP + Local Rules WDMI",
        ),
        "jtc": PDFConfig(
            line_spacing=2.0,
            court_type="jtc",
            court_rule="MCR 9.116",
        ),
        "admin": PDFConfig(
            line_spacing=1.5,
            court_type="admin",
            court_rule="Agency Rules",
        ),
    }

    def __init__(self, default_config: Optional[PDFConfig] = None) -> None:
        """Initialize the PDF generator.

        Args:
            default_config: Optional default configuration.  If not provided,
                the 14th_circuit configuration is used.
        """
        self._default_config = default_config or self.COURT_CONFIGS["14th_circuit"]
        self._generation_count = 0
        self._total_pages_generated = 0
        self._total_words_processed = 0
        self._errors: List[str] = []
        self._reportlab_available = _HAS_REPORTLAB
        logger.info(
            "LitigationPDFGenerator initialized (reportlab=%s)",
            self._reportlab_available,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(
        self,
        markdown_text: str,
        output_path: Union[str, Path],
        court_type: str = "14th_circuit",
        config: Optional[PDFConfig] = None,
    ) -> PDFResult:
        """Generate a court-formatted PDF from Markdown text.

        Args:
            markdown_text: Raw Markdown source for the filing.
            output_path: Destination file path (.pdf or .html).
            court_type: Court jurisdiction key (see COURT_CONFIGS).
            config: Optional override configuration.

        Returns:
            PDFResult with output path, page count, method, and warnings.
        """
        output_path = Path(output_path)
        cfg = config or self.COURT_CONFIGS.get(court_type, self._default_config)
        warnings: List[str] = []

        if not markdown_text or not markdown_text.strip():
            warnings.append("Empty markdown input — generating blank document")

        # Parse markdown into structured elements
        elements = self._parse_markdown(markdown_text)
        formatted = self._apply_court_formatting(elements, cfg)
        word_count = self._calculate_word_count(markdown_text)

        try:
            if self._reportlab_available and str(output_path).lower().endswith(".pdf"):
                result = self._generate_reportlab(
                    markdown_text, formatted, output_path, cfg, word_count
                )
            else:
                if str(output_path).lower().endswith(".pdf"):
                    output_path = output_path.with_suffix(".html")
                    warnings.append(
                        "reportlab not available — generated HTML fallback at "
                        f"{output_path}"
                    )
                result = self._generate_html_fallback(
                    markdown_text, formatted, output_path, cfg, word_count
                )
        except Exception as exc:
            logger.error("PDF generation failed: %s", exc, exc_info=True)
            self._errors.append(str(exc))
            return PDFResult(
                output_path=str(output_path),
                word_count=word_count,
                method="error",
                warnings=[f"Generation failed: {exc}"],
                generated_at=datetime.now(timezone.utc).isoformat(),
            )

        result.warnings.extend(warnings)
        self._generation_count += 1
        self._total_pages_generated += result.page_count
        self._total_words_processed += result.word_count

        return result

    def generate_from_file(
        self,
        md_path: Union[str, Path],
        output_path: Union[str, Path],
        court_type: str = "14th_circuit",
        config: Optional[PDFConfig] = None,
    ) -> PDFResult:
        """Generate a PDF from a Markdown file on disk.

        Args:
            md_path: Path to the source .md file.
            output_path: Destination file path.
            court_type: Court jurisdiction key.
            config: Optional override configuration.

        Returns:
            PDFResult with output metadata.
        """
        md_path = Path(md_path)
        if not md_path.exists():
            return PDFResult(
                output_path=str(output_path),
                method="error",
                warnings=[f"Source file not found: {md_path}"],
                generated_at=datetime.now(timezone.utc).isoformat(),
            )

        try:
            text = md_path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            logger.error("Failed to read %s: %s", md_path, exc)
            return PDFResult(
                output_path=str(output_path),
                method="error",
                warnings=[f"Read error: {exc}"],
                generated_at=datetime.now(timezone.utc).isoformat(),
            )

        return self.generate(text, output_path, court_type=court_type, config=config)

    def batch_generate(
        self, inputs: List[Dict[str, Any]]
    ) -> List[PDFResult]:
        """Generate multiple PDFs from a batch specification.

        Args:
            inputs: List of dicts, each with keys:
                - 'markdown_text' or 'md_path': Source content.
                - 'output_path': Destination path.
                - 'court_type' (optional): Court key.
                - 'config' (optional): PDFConfig instance.

        Returns:
            List of PDFResult, one per input.
        """
        results: List[PDFResult] = []
        for idx, spec in enumerate(inputs):
            try:
                court = spec.get("court_type", "14th_circuit")
                cfg = spec.get("config")
                out_path = spec.get("output_path", f"output_{idx}.pdf")

                if "md_path" in spec:
                    result = self.generate_from_file(
                        spec["md_path"], out_path, court_type=court, config=cfg
                    )
                else:
                    text = spec.get("markdown_text", "")
                    result = self.generate(
                        text, out_path, court_type=court, config=cfg
                    )
                results.append(result)
            except Exception as exc:
                logger.error("Batch item %d failed: %s", idx, exc)
                results.append(
                    PDFResult(
                        output_path=str(spec.get("output_path", f"output_{idx}.pdf")),
                        method="error",
                        warnings=[f"Batch error: {exc}"],
                        generated_at=datetime.now(timezone.utc).isoformat(),
                    )
                )
        return results

    def validate_output(self, pdf_path: Union[str, Path]) -> List[str]:
        """Check a generated PDF for court-compliance issues.

        Args:
            pdf_path: Path to the PDF or HTML file to validate.

        Returns:
            List of warning/error strings.  Empty list means compliant.
        """
        issues: List[str] = []
        pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            return [f"File not found: {pdf_path}"]

        size = pdf_path.stat().st_size
        if size == 0:
            issues.append("Output file is empty (0 bytes)")
            return issues

        if size < 500:
            issues.append(f"Output file suspiciously small ({size} bytes)")

        if pdf_path.suffix.lower() == ".html":
            try:
                content = pdf_path.read_text(encoding="utf-8", errors="replace")
                if "Times New Roman" not in content:
                    issues.append("HTML missing Times New Roman font specification")
                if "double" not in content.lower() and "line-height: 2" not in content:
                    issues.append("HTML may not be double-spaced")
                if "margin" not in content.lower():
                    issues.append("HTML missing margin specifications")
            except OSError as exc:
                issues.append(f"Could not read HTML for validation: {exc}")

        elif pdf_path.suffix.lower() == ".pdf":
            try:
                header = pdf_path.read_bytes()[:1024]
                if not header.startswith(b"%PDF"):
                    issues.append("File does not have valid PDF header")
            except OSError as exc:
                issues.append(f"Could not read PDF for validation: {exc}")

        return issues

    def get_stats(self) -> Dict[str, Any]:
        """Return generator statistics.

        Returns:
            Dict with generation counts, totals, and capability flags.
        """
        return {
            "generator": "LitigationPDFGenerator",
            "version": "1.0.0",
            "reportlab_available": self._reportlab_available,
            "generation_count": self._generation_count,
            "total_pages_generated": self._total_pages_generated,
            "total_words_processed": self._total_words_processed,
            "error_count": len(self._errors),
            "supported_courts": list(self.COURT_CONFIGS.keys()),
            "db_path": str(DB_PATH),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    # ------------------------------------------------------------------
    # Markdown Parsing
    # ------------------------------------------------------------------

    def _parse_markdown(self, text: str) -> List[ParsedElement]:
        """Parse Markdown text into a list of structured elements.

        Handles headings (#-####), bold, italic, numbered/bullet lists,
        blockquotes, horizontal rules, pipe tables, and fenced code blocks.

        Args:
            text: Raw Markdown string.

        Returns:
            Ordered list of ParsedElement instances.
        """
        elements: List[ParsedElement] = []
        if not text:
            return elements

        lines = text.split("\n")
        i = 0
        in_code_block = False
        code_lines: List[str] = []

        while i < len(lines):
            line = lines[i]

            # Fenced code blocks ```
            if line.strip().startswith("```"):
                if in_code_block:
                    elements.append(
                        ParsedElement(
                            element_type=ElementType.CODE_BLOCK,
                            text="\n".join(code_lines),
                        )
                    )
                    code_lines = []
                    in_code_block = False
                else:
                    in_code_block = True
                    lang = line.strip().lstrip("`").strip()
                    if lang:
                        code_lines.append(f"[{lang}]")
                i += 1
                continue

            if in_code_block:
                code_lines.append(line)
                i += 1
                continue

            stripped = line.strip()

            # Empty lines
            if not stripped:
                elements.append(ParsedElement(element_type=ElementType.EMPTY))
                i += 1
                continue

            # Horizontal rules (page breaks)
            if re.match(r"^(-{3,}|_{3,}|\*{3,})$", stripped):
                elements.append(
                    ParsedElement(element_type=ElementType.HORIZONTAL_RULE)
                )
                i += 1
                continue

            # Headings
            heading_match = re.match(r"^(#{1,4})\s+(.+)$", stripped)
            if heading_match:
                level = len(heading_match.group(1))
                title = heading_match.group(2).strip()
                elements.append(
                    ParsedElement(
                        element_type=ElementType.HEADING,
                        text=title,
                        level=level,
                    )
                )
                i += 1
                continue

            # Blockquotes
            if stripped.startswith(">"):
                quote_lines: List[str] = []
                while i < len(lines) and lines[i].strip().startswith(">"):
                    quote_lines.append(
                        lines[i].strip().lstrip(">").strip()
                    )
                    i += 1
                elements.append(
                    ParsedElement(
                        element_type=ElementType.BLOCKQUOTE,
                        text="\n".join(quote_lines),
                    )
                )
                continue

            # Numbered lists
            num_match = re.match(r"^(\d+)\.\s+(.+)$", stripped)
            if num_match:
                elements.append(
                    ParsedElement(
                        element_type=ElementType.NUMBERED_LIST,
                        text=num_match.group(2),
                        level=1,
                        meta={"number": int(num_match.group(1))},
                    )
                )
                i += 1
                continue

            # Bullet lists
            if re.match(r"^[-*+]\s+", stripped):
                bullet_text = re.sub(r"^[-*+]\s+", "", stripped)
                elements.append(
                    ParsedElement(
                        element_type=ElementType.BULLET_LIST,
                        text=bullet_text,
                        level=1,
                    )
                )
                i += 1
                continue

            # Pipe tables
            if "|" in stripped and stripped.startswith("|"):
                table_rows: List[Dict[str, Any]] = []
                while i < len(lines) and "|" in lines[i].strip():
                    row_text = lines[i].strip()
                    # Skip separator rows (|---|---|)
                    if re.match(r"^\|[\s\-:|]+\|$", row_text):
                        i += 1
                        continue
                    cells = [
                        c.strip()
                        for c in row_text.strip("|").split("|")
                    ]
                    table_rows.append({"cells": cells})
                    i += 1
                elements.append(
                    ParsedElement(
                        element_type=ElementType.TABLE,
                        children=table_rows,
                    )
                )
                continue

            # Default: paragraph
            para_lines: List[str] = []
            while (
                i < len(lines)
                and lines[i].strip()
                and not lines[i].strip().startswith("#")
                and not lines[i].strip().startswith(">")
                and not re.match(r"^(-{3,}|_{3,}|\*{3,})$", lines[i].strip())
                and not re.match(r"^\d+\.\s+", lines[i].strip())
                and not re.match(r"^[-*+]\s+", lines[i].strip())
                and not lines[i].strip().startswith("```")
                and not (
                    "|" in lines[i].strip()
                    and lines[i].strip().startswith("|")
                )
            ):
                para_lines.append(lines[i].strip())
                i += 1

            if para_lines:
                elements.append(
                    ParsedElement(
                        element_type=ElementType.PARAGRAPH,
                        text=" ".join(para_lines),
                    )
                )
                continue

            # Safety fallback
            i += 1

        # Handle unclosed code block
        if in_code_block and code_lines:
            elements.append(
                ParsedElement(
                    element_type=ElementType.CODE_BLOCK,
                    text="\n".join(code_lines),
                )
            )

        return elements

    def _apply_court_formatting(
        self, elements: List[ParsedElement], config: PDFConfig
    ) -> List[ParsedElement]:
        """Apply court-specific formatting rules to parsed elements.

        Args:
            elements: List of parsed Markdown elements.
            config: Court formatting configuration.

        Returns:
            Modified list of elements with court formatting applied.
        """
        formatted: List[ParsedElement] = []
        for elem in elements:
            # All headings become uppercase for court filings
            if elem.element_type == ElementType.HEADING:
                if elem.level <= 2:
                    elem.text = elem.text.upper()
                formatted.append(elem)
            elif elem.element_type == ElementType.EMPTY:
                # Collapse multiple empty lines
                if formatted and formatted[-1].element_type != ElementType.EMPTY:
                    formatted.append(elem)
            else:
                formatted.append(elem)
        return formatted

    # ------------------------------------------------------------------
    # Inline Formatting Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _md_inline_to_html(text: str) -> str:
        """Convert Markdown inline formatting to HTML tags.

        Handles **bold**, *italic*, and `code` spans.

        Args:
            text: Markdown text with inline formatting.

        Returns:
            HTML string with <strong>, <em>, <code> tags.
        """
        # Bold: **text**
        text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
        # Italic: *text*
        text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
        # Inline code: `text`
        text = re.sub(r"`(.+?)`", r"<code>\1</code>", text)
        return text

    @staticmethod
    def _md_inline_to_reportlab(text: str) -> str:
        """Convert Markdown inline formatting to reportlab XML tags.

        Args:
            text: Markdown text with inline formatting.

        Returns:
            String with <b>, <i> tags for reportlab Paragraph.
        """
        text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
        text = re.sub(r"\*(.+?)\*", r"<i>\1</i>", text)
        text = re.sub(r"`(.+?)`", r"<font face='Courier'>\1</font>", text)
        return text

    @staticmethod
    def _strip_markdown(text: str) -> str:
        """Strip all Markdown formatting from text.

        Args:
            text: Markdown text.

        Returns:
            Plain text with formatting removed.
        """
        text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
        text = re.sub(r"\*(.+?)\*", r"\1", text)
        text = re.sub(r"`(.+?)`", r"\1", text)
        return text

    # ------------------------------------------------------------------
    # Word / Page Counting
    # ------------------------------------------------------------------

    @staticmethod
    def _calculate_word_count(text: str) -> int:
        """Count words in text, stripping Markdown formatting.

        Args:
            text: Raw Markdown text.

        Returns:
            Integer word count.
        """
        clean = re.sub(r"[#*`>|\-_]", " ", text)
        clean = re.sub(r"\s+", " ", clean).strip()
        return len(clean.split()) if clean else 0

    @staticmethod
    def _estimate_page_count(word_count: int, words_per_page: int = WORDS_PER_PAGE) -> int:
        """Estimate page count from word count.

        Args:
            word_count: Total words.
            words_per_page: Baseline words per double-spaced page.

        Returns:
            Estimated page count (minimum 1).
        """
        if word_count <= 0:
            return 1
        return max(1, math.ceil(word_count / words_per_page))

    # ------------------------------------------------------------------
    # File hashing
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Caption Block
    # ------------------------------------------------------------------

    def _build_caption_text(self, config: PDFConfig) -> str:
        """Build a court caption block as plain text.

        Args:
            config: PDF configuration with court_type.

        Returns:
            Multi-line caption string.
        """
        court_map = {
            "14th_circuit": CASE_INFO["court_14th"],
            "coa": CASE_INFO["court_coa"],
            "msc": CASE_INFO["court_msc"],
            "federal": CASE_INFO["court_wdmi"],
            "jtc": "Michigan Judicial Tenure Commission",
            "admin": "Administrative Agency",
        }
        case_no_map = {
            "14th_circuit": CASE_INFO["trial_case_no"],
            "coa": CASE_INFO["coa_case_no"],
            "msc": CASE_INFO["trial_case_no"],
            "federal": "TBD",
            "jtc": CASE_INFO["trial_case_no"],
            "admin": CASE_INFO["trial_case_no"],
        }
        court_name = court_map.get(config.court_type, court_map["14th_circuit"])
        case_no = case_no_map.get(config.court_type, CASE_INFO["trial_case_no"])

        caption = (
            f"STATE OF MICHIGAN\n"
            f"IN THE {court_name.upper()}\n"
            f"\n"
            f"{CASE_INFO['plaintiff']},\n"
            f"    Plaintiff,\n"
            f"                                Case No. {case_no}\n"
            f"v.\n"
            f"                                {CASE_INFO['judge']}\n"
            f"{CASE_INFO['defendant']},\n"
            f"    Defendant.\n"
            f"{'_' * 40}/\n"
        )
        return caption

    # ------------------------------------------------------------------
    # Certificate of Service
    # ------------------------------------------------------------------

    @staticmethod
    def _build_certificate_of_service() -> str:
        """Build a Certificate of Service block.

        Returns:
            Multi-line Certificate of Service text.
        """
        today = datetime.now().strftime("%B %d, %Y")
        return (
            f"\n\nCERTIFICATE OF SERVICE\n\n"
            f"I, Andrew J. Pigors, hereby certify that on {today}, "
            f"I served a true and correct copy of the foregoing document "
            f"upon all parties of record by first-class U.S. mail, "
            f"postage prepaid, and/or electronic service as permitted "
            f"by the court rules, addressed as follows:\n\n"
            f"Emily A. Watson\n"
            f"[Address on file with the Court]\n\n"
            f"Dated: {today}\n\n"
            f"____________________________\n"
            f"Andrew J. Pigors, Pro Se\n"
            f"[Address on file with the Court]\n"
            f"[Phone on file with the Court]\n"
        )

    # ------------------------------------------------------------------
    # reportlab Generation
    # ------------------------------------------------------------------

    def _register_fonts(self) -> str:
        """Register Times New Roman fonts for reportlab.

        Returns:
            Font family name to use in styles.
        """
        if not _HAS_REPORTLAB:
            return "Times-Roman"

        # Try to register system Times New Roman
        font_paths = [
            Path(r"C:\Windows\Fonts\times.ttf"),
            Path(r"C:\Windows\Fonts\Times.ttf"),
            Path(r"C:\Windows\Fonts\TIMES.TTF"),
        ]
        for fp in font_paths:
            if fp.exists():
                try:
                    pdfmetrics.registerFont(TTFont("TimesNewRoman", str(fp)))
                    return "TimesNewRoman"
                except Exception as exc:
                    logger.debug("Font registration failed for %s: %s", fp, exc)

        return "Times-Roman"

    def _build_styles(self, font_name: str, config: PDFConfig) -> Dict[str, Any]:
        """Build reportlab paragraph styles for court documents.

        Args:
            font_name: Registered font family name.
            config: PDF configuration.

        Returns:
            Dict mapping style names to ParagraphStyle instances.
        """
        if not _HAS_REPORTLAB:
            return {}

        base_leading = config.font_size * config.line_spacing
        styles: Dict[str, Any] = {}

        styles["body"] = ParagraphStyle(
            "CourtBody",
            fontName=font_name,
            fontSize=config.font_size,
            leading=base_leading,
            alignment=TA_JUSTIFY,
            spaceAfter=0,
            spaceBefore=0,
            firstLineIndent=36,
        )
        styles["heading1"] = ParagraphStyle(
            "CourtH1",
            fontName=font_name,
            fontSize=config.font_size + 2,
            leading=base_leading + 4,
            alignment=TA_CENTER,
            spaceAfter=12,
            spaceBefore=24,
            textColor=colors.black,
        )
        styles["heading2"] = ParagraphStyle(
            "CourtH2",
            fontName=font_name,
            fontSize=config.font_size + 1,
            leading=base_leading + 2,
            alignment=TA_LEFT,
            spaceAfter=8,
            spaceBefore=18,
            textColor=colors.black,
        )
        styles["heading3"] = ParagraphStyle(
            "CourtH3",
            fontName=font_name,
            fontSize=config.font_size,
            leading=base_leading,
            alignment=TA_LEFT,
            spaceAfter=6,
            spaceBefore=12,
        )
        styles["heading4"] = ParagraphStyle(
            "CourtH4",
            fontName=font_name,
            fontSize=config.font_size,
            leading=base_leading,
            alignment=TA_LEFT,
            spaceAfter=4,
            spaceBefore=8,
        )
        styles["blockquote"] = ParagraphStyle(
            "CourtBlockquote",
            fontName=font_name,
            fontSize=config.font_size - 1,
            leading=base_leading - 2,
            alignment=TA_JUSTIFY,
            leftIndent=36,
            rightIndent=36,
            spaceAfter=6,
            spaceBefore=6,
        )
        styles["numbered"] = ParagraphStyle(
            "CourtNumbered",
            fontName=font_name,
            fontSize=config.font_size,
            leading=base_leading,
            alignment=TA_LEFT,
            leftIndent=36,
            spaceAfter=4,
            firstLineIndent=-18,
        )
        styles["bullet"] = ParagraphStyle(
            "CourtBullet",
            fontName=font_name,
            fontSize=config.font_size,
            leading=base_leading,
            alignment=TA_LEFT,
            leftIndent=36,
            spaceAfter=4,
            bulletIndent=18,
        )
        styles["code"] = ParagraphStyle(
            "CourtCode",
            fontName="Courier",
            fontSize=config.font_size - 1,
            leading=config.font_size * 1.2,
            alignment=TA_LEFT,
            leftIndent=36,
            rightIndent=36,
            spaceAfter=6,
            spaceBefore=6,
        )
        styles["caption"] = ParagraphStyle(
            "CourtCaption",
            fontName=font_name,
            fontSize=config.font_size,
            leading=base_leading,
            alignment=TA_CENTER,
            spaceAfter=4,
        )
        styles["cos"] = ParagraphStyle(
            "CourtCOS",
            fontName=font_name,
            fontSize=config.font_size,
            leading=base_leading,
            alignment=TA_LEFT,
            spaceAfter=4,
        )

        return styles

    def _add_page_numbers(self, canvas_obj: Any, doc_template: Any) -> None:
        """Draw page numbers in the footer of each page.

        Called by reportlab as an onPage callback.

        Args:
            canvas_obj: reportlab Canvas instance.
            doc_template: reportlab document template.
        """
        if not _HAS_REPORTLAB:
            return
        canvas_obj.saveState()
        page_num = canvas_obj.getPageNumber()
        text = f"Page {page_num}"
        canvas_obj.setFont("Times-Roman", 10)
        canvas_obj.drawCentredString(
            letter[0] / 2, 0.5 * inch, text
        )
        canvas_obj.restoreState()

    def _generate_reportlab(
        self,
        raw_text: str,
        elements: List[ParsedElement],
        output_path: Path,
        config: PDFConfig,
        word_count: int,
    ) -> PDFResult:
        """Generate a PDF using reportlab.

        Args:
            raw_text: Original Markdown text (for COS/caption).
            elements: Parsed and formatted elements.
            output_path: Destination PDF path.
            config: Court formatting configuration.
            word_count: Pre-computed word count.

        Returns:
            PDFResult with generation metadata.
        """
        if not _HAS_REPORTLAB:
            return self._generate_html_fallback(
                raw_text, elements, output_path.with_suffix(".html"),
                config, word_count,
            )

        warnings: List[str] = []
        output_path.parent.mkdir(parents=True, exist_ok=True)

        font_name = self._register_fonts()
        styles = self._build_styles(font_name, config)

        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=letter,
            topMargin=config.margin_top * inch,
            bottomMargin=config.margin_bottom * inch,
            leftMargin=config.margin_left * inch,
            rightMargin=config.margin_right * inch,
            title=f"{CASE_INFO['case_name']} — Filing",
            author=CASE_INFO["plaintiff"],
        )

        story: List[Any] = []

        # Caption page
        if config.include_caption:
            caption_text = self._build_caption_text(config)
            for cap_line in caption_text.split("\n"):
                if cap_line.strip():
                    story.append(Paragraph(
                        html_mod.escape(cap_line),
                        styles["caption"],
                    ))
                else:
                    story.append(Spacer(1, 6))
            story.append(Spacer(1, 24))

        # Document body
        for elem in elements:
            if elem.element_type == ElementType.HEADING:
                style_key = f"heading{min(elem.level, 4)}"
                rl_text = self._md_inline_to_reportlab(elem.text)
                story.append(Paragraph(f"<b>{rl_text}</b>", styles[style_key]))

            elif elem.element_type == ElementType.PARAGRAPH:
                rl_text = self._md_inline_to_reportlab(elem.text)
                story.append(Paragraph(rl_text, styles["body"]))

            elif elem.element_type == ElementType.NUMBERED_LIST:
                num = elem.meta.get("number", 1)
                rl_text = self._md_inline_to_reportlab(elem.text)
                story.append(
                    Paragraph(f"{num}. {rl_text}", styles["numbered"])
                )

            elif elem.element_type == ElementType.BULLET_LIST:
                rl_text = self._md_inline_to_reportlab(elem.text)
                story.append(
                    Paragraph(f"\u2022 {rl_text}", styles["bullet"])
                )

            elif elem.element_type == ElementType.BLOCKQUOTE:
                rl_text = self._md_inline_to_reportlab(elem.text)
                story.append(Paragraph(rl_text, styles["blockquote"]))

            elif elem.element_type == ElementType.CODE_BLOCK:
                for code_line in elem.text.split("\n"):
                    escaped = html_mod.escape(code_line) if code_line.strip() else "&nbsp;"
                    story.append(Paragraph(escaped, styles["code"]))

            elif elem.element_type == ElementType.TABLE:
                table_data: List[List[str]] = []
                for row in elem.children:
                    table_data.append(row.get("cells", []))
                if table_data:
                    t = Table(table_data)
                    t.setStyle(TableStyle([
                        ("FONTNAME", (0, 0), (-1, -1), font_name),
                        ("FONTSIZE", (0, 0), (-1, -1), config.font_size - 1),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                        ("BACKGROUND", (0, 0), (-1, 0), colors.Color(0.9, 0.9, 0.9)),
                    ]))
                    story.append(Spacer(1, 6))
                    story.append(t)
                    story.append(Spacer(1, 6))

            elif elem.element_type == ElementType.HORIZONTAL_RULE:
                story.append(PageBreak())

            elif elem.element_type == ElementType.EMPTY:
                story.append(Spacer(1, config.font_size * 0.5))

        # Certificate of Service
        if config.include_certificate_of_service:
            story.append(PageBreak())
            cos_text = self._build_certificate_of_service()
            for cos_line in cos_text.strip().split("\n"):
                if cos_line.strip():
                    story.append(Paragraph(
                        html_mod.escape(cos_line),
                        styles["cos"],
                    ))
                else:
                    story.append(Spacer(1, 6))

        # Build the PDF
        try:
            if config.page_numbering:
                doc.build(story, onFirstPage=self._add_page_numbers,
                          onLaterPages=self._add_page_numbers)
            else:
                doc.build(story)
        except Exception as exc:
            logger.error("reportlab build failed: %s", exc)
            warnings.append(f"reportlab build error: {exc}")
            return self._generate_html_fallback(
                raw_text, elements, output_path.with_suffix(".html"),
                config, word_count,
            )

        page_count = self._estimate_page_count(word_count)
        file_size = output_path.stat().st_size if output_path.exists() else 0

        return PDFResult(
            output_path=str(output_path),
            page_count=page_count,
            word_count=word_count,
            file_size_bytes=file_size,
            method="reportlab",
            warnings=warnings,
            generated_at=datetime.now(timezone.utc).isoformat(),
            sha256=self._sha256_file(output_path),
        )

    # ------------------------------------------------------------------
    # HTML Fallback Generation
    # ------------------------------------------------------------------

    def _generate_html_fallback(
        self,
        raw_text: str,
        elements: List[ParsedElement],
        output_path: Path,
        config: PDFConfig,
        word_count: int,
    ) -> PDFResult:
        """Generate a print-ready HTML file as a PDF fallback.

        The HTML includes CSS @media print rules for court-compliant
        formatting when printed from a browser.

        Args:
            raw_text: Original Markdown text.
            elements: Parsed and formatted elements.
            output_path: Destination HTML path.
            config: Court formatting configuration.
            word_count: Pre-computed word count.

        Returns:
            PDFResult with generation metadata.
        """
        output_path = Path(output_path)
        if output_path.suffix.lower() != ".html":
            output_path = output_path.with_suffix(".html")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        warnings: List[str] = []

        css = self._build_print_css(config)
        body_html = self._elements_to_html(elements, config)

        # Caption
        caption_html = ""
        if config.include_caption:
            caption_text = self._build_caption_text(config)
            caption_html = (
                '<div class="caption">'
                + "<br>\n".join(
                    html_mod.escape(line) if line.strip() else "&nbsp;"
                    for line in caption_text.split("\n")
                )
                + "</div>\n<hr class=\"caption-rule\">\n"
            )

        # Certificate of Service
        cos_html = ""
        if config.include_certificate_of_service:
            cos_text = self._build_certificate_of_service()
            cos_html = (
                '<div class="page-break"></div>\n'
                '<div class="certificate-of-service">'
                + "<br>\n".join(
                    html_mod.escape(line) if line.strip() else "&nbsp;"
                    for line in cos_text.strip().split("\n")
                )
                + "</div>\n"
            )

        full_html = textwrap.dedent(f"""\
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{html_mod.escape(CASE_INFO['case_name'])} — Court Filing</title>
            <style>
        {css}
            </style>
        </head>
        <body>
            {caption_html}
            <div class="document-body">
        {body_html}
            </div>
            {cos_html}
            <div class="footer-note">
                <p>Generated by LitigationOS PDF Generator — {config.court_rule}</p>
                <p>Print this document using browser Print (Ctrl+P) with
                   "Background graphics" enabled for best results.</p>
            </div>
        </body>
        </html>
        """)

        try:
            output_path.write_text(full_html, encoding="utf-8")
        except OSError as exc:
            logger.error("HTML write failed: %s", exc)
            warnings.append(f"Write error: {exc}")

        page_count = self._estimate_page_count(word_count)
        file_size = output_path.stat().st_size if output_path.exists() else 0

        return PDFResult(
            output_path=str(output_path),
            page_count=page_count,
            word_count=word_count,
            file_size_bytes=file_size,
            method="html_fallback",
            warnings=warnings,
            generated_at=datetime.now(timezone.utc).isoformat(),
            sha256=self._sha256_file(output_path),
        )

    def _build_print_css(self, config: PDFConfig) -> str:
        """Build CSS for court-compliant print output.

        Args:
            config: PDF configuration.

        Returns:
            CSS string with @media print and screen rules.
        """
        line_height = config.line_spacing
        font_size = config.font_size
        margin = config.margin_top  # Assume uniform margins for simplicity

        return textwrap.dedent(f"""\
        /* Court document styling — {config.court_rule} */
        @page {{
            size: {config.page_width}in {config.page_height}in;
            margin: {margin}in;
        }}

        * {{
            box-sizing: border-box;
        }}

        body {{
            font-family: "{config.font_family}", "Times New Roman", Times, serif;
            font-size: {font_size}pt;
            line-height: {line_height};
            color: #000;
            max-width: {config.content_width_inches}in;
            margin: 0 auto;
            padding: 1em;
        }}

        h1, h2, h3, h4 {{
            font-family: "{config.font_family}", "Times New Roman", Times, serif;
            color: #000;
            page-break-after: avoid;
        }}

        h1 {{
            font-size: {font_size + 2}pt;
            text-align: center;
            text-transform: uppercase;
            margin-top: 1.5em;
            margin-bottom: 0.75em;
        }}

        h2 {{
            font-size: {font_size + 1}pt;
            text-transform: uppercase;
            margin-top: 1.25em;
            margin-bottom: 0.5em;
        }}

        h3 {{
            font-size: {font_size}pt;
            font-weight: bold;
            margin-top: 1em;
            margin-bottom: 0.5em;
        }}

        h4 {{
            font-size: {font_size}pt;
            font-style: italic;
            margin-top: 0.75em;
            margin-bottom: 0.5em;
        }}

        p {{
            text-align: justify;
            text-indent: 0.5in;
            margin: 0 0 0.1em 0;
        }}

        blockquote {{
            margin: 0.5em 0.5in;
            font-size: {font_size - 1}pt;
            line-height: {line_height * 0.75};
            text-align: justify;
        }}

        ol, ul {{
            margin-left: 0.5in;
        }}

        li {{
            margin-bottom: 0.25em;
        }}

        pre, code {{
            font-family: "Courier New", Courier, monospace;
            font-size: {font_size - 1}pt;
        }}

        pre {{
            margin: 0.5em 0.5in;
            white-space: pre-wrap;
            line-height: 1.2;
            background: #f8f8f8;
            padding: 0.5em;
            border: 1px solid #ddd;
        }}

        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 0.5em 0;
            font-size: {font_size - 1}pt;
        }}

        th, td {{
            border: 1px solid #000;
            padding: 4px 8px;
            text-align: left;
        }}

        th {{
            background-color: #f0f0f0;
            font-weight: bold;
        }}

        .caption {{
            text-align: center;
            font-size: {font_size}pt;
            line-height: {line_height};
            margin-bottom: 1em;
            white-space: pre-line;
        }}

        .caption-rule {{
            border: none;
            border-top: 2px solid #000;
            margin: 1em 0;
        }}

        .certificate-of-service {{
            margin-top: 2em;
            line-height: {line_height};
        }}

        .page-break {{
            page-break-before: always;
        }}

        .footer-note {{
            margin-top: 3em;
            padding-top: 1em;
            border-top: 1px solid #ccc;
            font-size: 9pt;
            color: #666;
            text-align: center;
            text-indent: 0;
        }}

        .footer-note p {{
            text-indent: 0;
            text-align: center;
        }}

        @media print {{
            body {{
                padding: 0;
                max-width: none;
            }}

            .footer-note {{
                display: none;
            }}

            .page-break {{
                page-break-before: always;
            }}

            a {{
                color: #000;
                text-decoration: none;
            }}

            @bottom-center {{
                content: "Page " counter(page);
                font-family: "{config.font_family}", Times, serif;
                font-size: 10pt;
            }}
        }}
        """)

    def _elements_to_html(
        self, elements: List[ParsedElement], config: PDFConfig
    ) -> str:
        """Convert parsed elements to HTML body content.

        Args:
            elements: List of parsed Markdown elements.
            config: PDF configuration.

        Returns:
            HTML string of the document body.
        """
        parts: List[str] = []

        for elem in elements:
            if elem.element_type == ElementType.HEADING:
                level = min(elem.level, 4)
                tag = f"h{level}"
                text_html = self._md_inline_to_html(html_mod.escape(elem.text))
                parts.append(f"<{tag}>{text_html}</{tag}>")

            elif elem.element_type == ElementType.PARAGRAPH:
                text_html = self._md_inline_to_html(html_mod.escape(elem.text))
                parts.append(f"<p>{text_html}</p>")

            elif elem.element_type == ElementType.NUMBERED_LIST:
                num = elem.meta.get("number", 1)
                text_html = self._md_inline_to_html(html_mod.escape(elem.text))
                parts.append(
                    f'<p style="margin-left:0.5in;text-indent:-0.25in;">'
                    f"{num}. {text_html}</p>"
                )

            elif elem.element_type == ElementType.BULLET_LIST:
                text_html = self._md_inline_to_html(html_mod.escape(elem.text))
                parts.append(
                    f'<p style="margin-left:0.5in;text-indent:-0.25in;">'
                    f"\u2022 {text_html}</p>"
                )

            elif elem.element_type == ElementType.BLOCKQUOTE:
                text_html = self._md_inline_to_html(html_mod.escape(elem.text))
                parts.append(f"<blockquote>{text_html}</blockquote>")

            elif elem.element_type == ElementType.CODE_BLOCK:
                code_html = html_mod.escape(elem.text)
                parts.append(f"<pre><code>{code_html}</code></pre>")

            elif elem.element_type == ElementType.TABLE:
                table_parts = ["<table>"]
                for row_idx, row in enumerate(elem.children):
                    cells = row.get("cells", [])
                    tag = "th" if row_idx == 0 else "td"
                    row_html = "".join(
                        f"<{tag}>{html_mod.escape(c)}</{tag}>"
                        for c in cells
                    )
                    table_parts.append(f"<tr>{row_html}</tr>")
                table_parts.append("</table>")
                parts.append("\n".join(table_parts))

            elif elem.element_type == ElementType.HORIZONTAL_RULE:
                parts.append('<div class="page-break"></div>')

            elif elem.element_type == ElementType.EMPTY:
                pass  # HTML handles spacing via CSS

        return "\n".join(parts)

    # ------------------------------------------------------------------
    # Caption Page (standalone)
    # ------------------------------------------------------------------

    def _add_caption_page(
        self, doc_story: List[Any], caption_text: str, config: PDFConfig
    ) -> None:
        """Add a standalone caption page to a reportlab story.

        Args:
            doc_story: reportlab story list to append to.
            caption_text: Caption block text.
            config: PDF configuration.
        """
        if not _HAS_REPORTLAB:
            return

        font_name = self._register_fonts()
        styles = self._build_styles(font_name, config)

        for line in caption_text.split("\n"):
            if line.strip():
                doc_story.append(
                    Paragraph(html_mod.escape(line), styles["caption"])
                )
            else:
                doc_story.append(Spacer(1, 6))

        doc_story.append(PageBreak())


# ---------------------------------------------------------------------------
# Module-level convenience functions
# ---------------------------------------------------------------------------

def generate_pdf(
    markdown_text: str,
    output_path: Union[str, Path],
    court_type: str = "14th_circuit",
    config: Optional[PDFConfig] = None,
) -> PDFResult:
    """Convenience function to generate a single PDF.

    Args:
        markdown_text: Markdown source text.
        output_path: Destination file path.
        court_type: Court jurisdiction key.
        config: Optional PDFConfig override.

    Returns:
        PDFResult with output metadata.
    """
    gen = LitigationPDFGenerator()
    return gen.generate(markdown_text, output_path, court_type=court_type, config=config)


def generate_pdf_from_file(
    md_path: Union[str, Path],
    output_path: Union[str, Path],
    court_type: str = "14th_circuit",
) -> PDFResult:
    """Convenience function to generate a PDF from a Markdown file.

    Args:
        md_path: Path to source .md file.
        output_path: Destination file path.
        court_type: Court jurisdiction key.

    Returns:
        PDFResult with output metadata.
    """
    gen = LitigationPDFGenerator()
    return gen.generate_from_file(md_path, output_path, court_type=court_type)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    if len(sys.argv) < 3:
        print("Usage: python pdf_generator.py <input.md> <output.pdf> [court_type]")
        print(f"  Court types: {', '.join(LitigationPDFGenerator.COURT_CONFIGS.keys())}")
        sys.exit(1)

    in_path = sys.argv[1]
    out_path = sys.argv[2]
    court = sys.argv[3] if len(sys.argv) > 3 else "14th_circuit"

    result = generate_pdf_from_file(in_path, out_path, court_type=court)
    print(json.dumps(result.to_dict(), indent=2))
