"""
LitigationOS Typst Filing Pipeline (U07)
End-to-end conversion: GOLDEN_SET markdown → court-ready PDF

Converts markdown court filings into Typst markup, selects correct court
formatting per filing lane, compiles via the Typst binary, and assembles
complete filing packets.

Usage:
    from pipeline import TypstPipeline
    pipe = TypstPipeline()
    pdf = pipe.compile_document("path/to/motion.md", "F10")
    packet = pipe.compile_packet("F10")
    all_pdfs = pipe.compile_all()

CLI:
    python -m pipeline F10              # compile one packet
    python -m pipeline --all            # compile everything
    python -m pipeline --doc F10 10_COA_EMERGENCY_MOTION.md
"""

import os
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Optional

# ─────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parents[3]  # C:\Users\andre\LitigationOS
GOLDEN_SET = REPO_ROOT / "05_FILINGS" / "GOLDEN_SET"
TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
TYPST_BIN = (
    shutil.which("typst")
    or r"C:\Users\andre\AppData\Local\Microsoft\WinGet\Links\typst.exe"
)

SEPARATION_ANCHOR = date(2025, 7, 29)

PLAINTIFF = "ANDREW JAMES PIGORS"
DEFENDANT = "EMILY A. WATSON"
JUDGE = "HON. JENNY L. McNEILL"
CHILD = "L.D.W."

CHILD_NAME_RE = re.compile(
    r"\b(?:Lincoln\s+(?:Dean\s+)?(?:Watson|Pigors|Watson[- ]Pigors))\b",
    re.IGNORECASE,
)

# ─────────────────────────────────────────────────────────────
# FILING METADATA — actual case details
# ─────────────────────────────────────────────────────────────

FILING_METADATA = {
    "F01": {
        "case_number": "2024-001507-DC",
        "court": "MICHIGAN SUPREME COURT",
        "title": "COMPLAINT FOR SUPERINTENDING CONTROL",
        "judge": JUDGE,
        "subdir": "F01_MSC_PETITION",
    },
    "F02": {
        "case_number": "NEW",
        "court": "UNITED STATES DISTRICT COURT, WESTERN DISTRICT OF MICHIGAN",
        "title": "COMPLAINT — FAIR HOUSING ACT VIOLATIONS",
        "judge": "",
        "subdir": "F02_FAIR_HOUSING",
    },
    "F03": {
        "case_number": "2024-001507-DC",
        "court": "MICHIGAN SUPREME COURT",
        "title": "APPLICATION FOR SUPERINTENDING CONTROL — DISQUALIFICATION",
        "judge": JUDGE,
        "subdir": "F03_DISQUALIFICATION",
    },
    "F04": {
        "case_number": "NEW",
        "court": "UNITED STATES DISTRICT COURT, WESTERN DISTRICT OF MICHIGAN",
        "title": "COMPLAINT — 42 USC §1983",
        "judge": "",
        "subdir": "F04_FEDERAL_1983",
    },
    "F05": {
        "case_number": "2024-001507-DC",
        "court": "MICHIGAN SUPREME COURT",
        "title": "COMPLAINT FOR ORIGINAL ACTION",
        "judge": JUDGE,
        "subdir": "F05_MSC_ORIGINAL",
    },
    "F06": {
        "case_number": "JTC COMPLAINT",
        "court": "JUDICIAL TENURE COMMISSION",
        "title": "FORMAL COMPLAINT — HON. JENNY L. McNEILL",
        "judge": "",
        "subdir": "F06_JTC_COMPLAINT",
    },
    "F08": {
        "case_number": "2023-5907-PP",
        "court": "14TH JUDICIAL CIRCUIT COURT, MUSKEGON COUNTY",
        "title": "MOTION TO TERMINATE PERSONAL PROTECTION ORDER",
        "judge": JUDGE,
        "subdir": "F08_PPO_TERMINATION",
    },
    "F09": {
        "case_number": "366810",
        "court": "MICHIGAN COURT OF APPEALS",
        "title": "APPELLANT'S BRIEF ON APPEAL",
        "judge": "",
        "subdir": "F09_COA_BRIEF",
    },
    "F10": {
        "case_number": "366810",
        "court": "MICHIGAN COURT OF APPEALS",
        "title": "EMERGENCY MOTION TO RESTORE PARENTING TIME",
        "judge": "",
        "subdir": "F10_COA_EMERGENCY",
    },
}

# ─────────────────────────────────────────────────────────────
# COURT FORMAT RULES — per filing lane
# ─────────────────────────────────────────────────────────────

@dataclass
class CourtFormat:
    court_type: str
    font_size: str = "12pt"
    line_spacing: str = "double"
    margins: str = "1in"
    font: str = "Times New Roman"

COURT_FORMATS = {
    "F01": CourtFormat("MSC"),
    "F02": CourtFormat("Federal", font_size="14pt"),
    "F03": CourtFormat("MSC"),
    "F04": CourtFormat("Federal", font_size="14pt"),
    "F05": CourtFormat("MSC"),
    "F06": CourtFormat("JTC", line_spacing="single"),
    "F08": CourtFormat("Circuit"),
    "F09": CourtFormat("COA"),
    "F10": CourtFormat("COA"),
}

# ─────────────────────────────────────────────────────────────
# DOCUMENT TYPE DETECTION
# ─────────────────────────────────────────────────────────────

DOC_TYPE_PATTERNS = [
    ("certificate_of_service", re.compile(r"certificate.of.service", re.I)),
    ("fee_waiver", re.compile(r"fee.waiver|mc.?20", re.I)),
    ("proposed_order", re.compile(r"proposed.order|^PO_", re.I)),
    ("exhibit_index", re.compile(r"exhibit.index", re.I)),
    ("affidavit", re.compile(r"affidavit", re.I)),
    ("brief", re.compile(r"brief", re.I)),
    ("complaint", re.compile(r"complaint", re.I)),
    ("motion", re.compile(r"motion|emergency", re.I)),
    ("petition", re.compile(r"petition", re.I)),
]


def detect_doc_type(filename: str, content: str = "") -> str:
    """Detect document type from filename, falling back to content inspection."""
    name_lower = filename.lower()
    for doc_type, pattern in DOC_TYPE_PATTERNS:
        if pattern.search(name_lower):
            return doc_type
    for doc_type, pattern in DOC_TYPE_PATTERNS:
        if content and pattern.search(content[:500]):
            return doc_type
    return "general"


# ─────────────────────────────────────────────────────────────
# TYPST CHARACTER ESCAPING
# ─────────────────────────────────────────────────────────────

# Characters that have special meaning in Typst markup
_TYPST_SPECIAL = {
    "#": "\\#",
    "$": "\\$",
    "@": "\\@",
}

# Characters that only need escaping in specific contexts
_TYPST_ANGLE = {
    "<": "\\<",
    ">": "\\>",
}


def escape_typst(text: str) -> str:
    """Escape special Typst characters in raw text content.

    Handles #, $, @, <, > — the five characters with syntactic
    meaning in Typst that could appear in legal prose.
    """
    for char, escaped in _TYPST_SPECIAL.items():
        text = text.replace(char, escaped)
    for char, escaped in _TYPST_ANGLE.items():
        text = text.replace(char, escaped)
    return text


def sanitize_child_name(text: str) -> str:
    """Replace child's full name with L.D.W. per MCR 8.119(H)."""
    return CHILD_NAME_RE.sub("L.D.W.", text)


def compute_separation_days() -> int:
    """Compute days since last contact with L.D.W. (July 29, 2025)."""
    return (date.today() - SEPARATION_ANCHOR).days


# ─────────────────────────────────────────────────────────────
# MARKDOWN → TYPST CONVERTER
# ─────────────────────────────────────────────────────────────

class MarkdownToTypst:
    """Converts markdown legal documents to Typst markup.

    Handles headings, bold, italic, lists, numbered lists, tables,
    blockquotes, horizontal rules, links, and inline formatting.
    The output is raw Typst content (no template wrapper) suitable
    for insertion into a template document.
    """

    # Pre-compiled patterns for inline formatting
    _BOLD_ITALIC_RE = re.compile(r"\*\*\*(.+?)\*\*\*")
    _BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
    _ITALIC_RE = re.compile(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)")
    _LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
    _INLINE_CODE_RE = re.compile(r"`([^`]+)`")
    _UNDERSCORE_LINE_RE = re.compile(r"_{2,}")  # fill-line underscores
    _MD_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$")
    _NUMBERED_LIST_RE = re.compile(r"^\s*(\d+)\.\s+(.+)$")
    _BULLET_LIST_RE = re.compile(r"^\s*[-*+]\s+(.+)$")
    _CHECKBOX_RE = re.compile(r"^\s*-\s+\[([ xX])\]\s+(.+)$")
    _BLOCKQUOTE_RE = re.compile(r"^>\s*(.*)$")
    _TABLE_SEP_RE = re.compile(r"^\|[-:| ]+\|$")
    _TABLE_ROW_RE = re.compile(r"^\|(.+)\|$")
    _HR_RE = re.compile(r"^-{3,}$|^\*{3,}$|^_{3,}$")
    _SECTION_NUMBER_RE = re.compile(r"^([IVXLC]+\.\s+|[A-Z]\.\s+|\d+\.\s+)")

    def convert(self, md_content: str) -> str:
        """Convert markdown content to Typst markup."""
        md_content = sanitize_child_name(md_content)
        lines = md_content.split("\n")
        output_lines: list[str] = []
        i = 0
        while i < len(lines):
            line = lines[i]

            # Horizontal rule
            if self._HR_RE.match(line.strip()):
                i += 1
                continue

            # Heading
            m = self._MD_HEADING_RE.match(line)
            if m:
                level = len(m.group(1))
                text = m.group(2).strip()
                text = self._convert_inline(text)
                prefix = "=" * level
                output_lines.append(f"{prefix} {text}")
                output_lines.append("")
                i += 1
                continue

            # Table block
            if self._TABLE_ROW_RE.match(line.strip()):
                table_lines = []
                while i < len(lines) and self._TABLE_ROW_RE.match(lines[i].strip()):
                    if not self._TABLE_SEP_RE.match(lines[i].strip()):
                        table_lines.append(lines[i])
                    i += 1
                output_lines.append(self._convert_table(table_lines))
                output_lines.append("")
                continue

            # Blockquote
            bq_match = self._BLOCKQUOTE_RE.match(line)
            if bq_match:
                bq_lines = []
                while i < len(lines) and self._BLOCKQUOTE_RE.match(lines[i]):
                    m2 = self._BLOCKQUOTE_RE.match(lines[i])
                    bq_lines.append(m2.group(1) if m2 else "")
                    i += 1
                quoted_text = self._convert_inline(" ".join(bq_lines))
                output_lines.append(f"#quote[{quoted_text}]")
                output_lines.append("")
                continue

            # Checkbox list item
            cb_match = self._CHECKBOX_RE.match(line)
            if cb_match:
                checked = cb_match.group(1).lower() == "x"
                text = self._convert_inline(cb_match.group(2))
                symbol = "☑" if checked else "☐"
                output_lines.append(f"- {symbol} {text}")
                i += 1
                continue

            # Numbered list
            nl_match = self._NUMBERED_LIST_RE.match(line)
            if nl_match:
                text = self._convert_inline(nl_match.group(2))
                output_lines.append(f"+ {text}")
                i += 1
                continue

            # Bullet list
            bl_match = self._BULLET_LIST_RE.match(line)
            if bl_match:
                text = self._convert_inline(bl_match.group(1))
                output_lines.append(f"- {text}")
                i += 1
                continue

            # Blank line
            if line.strip() == "":
                output_lines.append("")
                i += 1
                continue

            # Regular paragraph — collect contiguous non-blank lines
            para_lines = []
            while i < len(lines) and lines[i].strip() != "":
                current = lines[i]
                # Stop at headings, lists, tables, HRs, blockquotes
                if (self._MD_HEADING_RE.match(current)
                        or self._NUMBERED_LIST_RE.match(current)
                        or self._BULLET_LIST_RE.match(current)
                        or self._TABLE_ROW_RE.match(current.strip())
                        or self._HR_RE.match(current.strip())
                        or self._BLOCKQUOTE_RE.match(current)
                        or self._CHECKBOX_RE.match(current)):
                    break
                para_lines.append(current)
                i += 1

            if para_lines:
                para_text = " ".join(l.strip() for l in para_lines)
                para_text = self._convert_inline(para_text)
                output_lines.append(para_text)
                output_lines.append("")
                continue

            i += 1

        return "\n".join(output_lines)

    def _convert_inline(self, text: str) -> str:
        """Convert markdown inline formatting to Typst equivalents."""
        # Escape underscore fill-lines FIRST (before italic conversion)
        # Sequences like ________ are signature/fill lines, not italic markers
        text = self._UNDERSCORE_LINE_RE.sub(
            lambda m: "#line(length: " + str(max(1, len(m.group(0)) // 5)) + "in, stroke: 0.5pt)",
            text,
        )

        # First, handle links before escaping (URLs have special chars)
        text = self._LINK_RE.sub(r'#link("\2")[\1]', text)

        # Handle inline code
        text = self._INLINE_CODE_RE.sub(r"`\1`", text)

        # Bold+Italic (***text***) → *_text_* in Typst
        text = self._BOLD_ITALIC_RE.sub(r"*_\1_*", text)

        # Bold (**text**) → *text* in Typst
        text = self._BOLD_RE.sub(r"*\1*", text)

        # Italic (*text*) → _text_ in Typst
        # Careful: don't catch already-converted Typst bold markers
        text = self._ITALIC_RE.sub(r"_\1_", text)

        # Escape remaining special chars in non-markup text
        # Only escape # $ @ < > that aren't part of Typst commands
        text = self._escape_non_markup(text)

        return text

    def _escape_non_markup(self, text: str) -> str:
        """Escape Typst special characters that aren't part of markup commands."""
        result = []
        i = 0
        while i < len(text):
            ch = text[i]
            if ch == "#" and i + 1 < len(text) and text[i + 1].isalpha():
                # This looks like a Typst command (#link, #quote, etc.) — keep it
                result.append(ch)
            elif ch == "#":
                result.append("\\#")
            elif ch == "$":
                result.append("\\$")
            elif ch == "@":
                result.append("\\@")
            elif ch == "<":
                result.append("\\<")
            elif ch == ">":
                result.append("\\>")
            else:
                result.append(ch)
            i += 1
        return "".join(result)

    def _convert_table(self, rows: list[str]) -> str:
        """Convert markdown table rows to Typst table syntax."""
        if not rows:
            return ""

        parsed: list[list[str]] = []
        for row in rows:
            cells = [c.strip() for c in row.strip().strip("|").split("|")]
            parsed.append(cells)

        if not parsed:
            return ""

        ncols = max(len(r) for r in parsed)
        col_spec = ", ".join(["1fr"] * ncols)

        parts = [f"#table(columns: ({col_spec}),"]

        # First row as header
        if parsed:
            for cell in parsed[0]:
                safe = self._convert_inline(cell)
                parts.append(f"  table.header([*{safe}*]),")

        # Data rows
        for row in parsed[1:]:
            for cell in row:
                safe = self._convert_inline(cell)
                parts.append(f"  [{safe}],")

        parts.append(")")
        return "\n".join(parts)


# ─────────────────────────────────────────────────────────────
# TYPST DOCUMENT BUILDERS
# ─────────────────────────────────────────────────────────────

class TypstDocumentBuilder:
    """Builds complete Typst source documents using the template library.

    Each build method generates a full .typ file that imports the
    appropriate template and renders the converted markdown content
    with correct court formatting.
    """

    def __init__(self, templates_dir: Path):
        self.templates_dir = templates_dir
        self.converter = MarkdownToTypst()

    def build_motion(self, md_content: str, filing_id: str, meta: dict,
                     fmt: CourtFormat) -> str:
        """Build a Typst motion document."""
        body = self.converter.convert(md_content)
        filing_date = datetime.now().strftime("%B %d, %Y")
        sep_days = compute_separation_days()

        court_name = self._court_for_caption(meta)
        judge = meta.get("judge", "") or JUDGE

        lines = [
            '// Generated by LitigationOS Typst Pipeline',
            f'// Filing: {filing_id} — {meta.get("title", "")}',
            f'// Date: {filing_date}',
            f'// Separation days: {sep_days}',
            '',
            '#import "motion.typ": motion, irac, wherefore',
            '#import "caption.typ": numbered-paras, exhibit-ref, cite-case, now-comes',
            '#import "certificate-of-service.typ": certificate-of-service',
            '',
            '#show: motion.with(',
            f'  case-number: "{meta.get("case_number", "")}",',
            f'  court: "{court_name}",',
            f'  judge: "{judge}",',
            f'  plaintiff: "{PLAINTIFF}",',
            f'  defendant: "{DEFENDANT}",',
            f'  document-title: "{self._escape_title(meta.get("title", ""))}",',
            f'  date: "{filing_date}",',
            ')',
            '',
            self._apply_format_overrides(fmt),
            '',
            body,
            '',
            '// Certificate of Service',
            '#certificate-of-service(',
            f'  date: "{filing_date}",',
            '  method: "first-class U.S. Mail, postage prepaid",',
            ')',
        ]
        return "\n".join(lines)

    def build_brief(self, md_content: str, filing_id: str, meta: dict,
                    fmt: CourtFormat) -> str:
        """Build a Typst brief document (COA/MSC)."""
        body = self.converter.convert(md_content)
        filing_date = datetime.now().strftime("%B %d, %Y")
        sep_days = compute_separation_days()

        court_name = self._court_for_caption(meta)

        lines = [
            '// Generated by LitigationOS Typst Pipeline',
            f'// Filing: {filing_id} — {meta.get("title", "")}',
            f'// Date: {filing_date}',
            f'// Separation days: {sep_days}',
            '',
            '#import "brief.typ": brief, index-of-authorities, creac',
            '#import "caption.typ": numbered-paras, exhibit-ref, cite-case',
            '#import "certificate-of-service.typ": certificate-of-service',
            '',
            '#show: brief.with(',
            f'  case-number: "{meta.get("case_number", "")}",',
            f'  court: "{court_name}",',
            f'  judge: "{meta.get("judge", "")}",',
            f'  plaintiff: "{PLAINTIFF}",',
            f'  defendant: "{DEFENDANT}",',
            f'  document-title: "{self._escape_title(meta.get("title", ""))}",',
            f'  date: "{filing_date}",',
            '  show-toc: true,',
            '  show-ioa: false,',
            ')',
            '',
            self._apply_format_overrides(fmt),
            '',
            body,
        ]
        return "\n".join(lines)

    def build_certificate_of_service(self, md_content: str, filing_id: str,
                                     meta: dict, fmt: CourtFormat) -> str:
        """Build a standalone Certificate of Service."""
        filing_date = datetime.now().strftime("%B %d, %Y")

        lines = [
            '// Generated by LitigationOS Typst Pipeline — Certificate of Service',
            f'// Filing: {filing_id}',
            '',
            '#import "caption.typ": court-page',
            '#import "certificate-of-service.typ": certificate-of-service',
            '',
            '#show: court-page',
            '',
            self._apply_format_overrides(fmt),
            '',
            '#certificate-of-service(',
            f'  date: "{filing_date}",',
            '  method: "first-class U.S. Mail, postage prepaid",',
            '  parties: (',
            '    (',
            '      name: "Emily A. Watson",',
            '      address: "2160 Garland Dr\\nNorton Shores, MI 49441",',
            '    ),',
            '    (',
            '      name: "Muskegon County Circuit Court\\nClerk of the Court",',
            '      address: "990 Terrace St\\nMuskegon, MI 49442",',
            '    ),',
            '  ),',
            ')',
        ]
        return "\n".join(lines)

    def build_proposed_order(self, md_content: str, filing_id: str, meta: dict,
                            fmt: CourtFormat) -> str:
        """Build a Typst proposed order document."""
        body = self.converter.convert(md_content)
        court_name = self._court_for_caption(meta)
        judge = meta.get("judge", "") or JUDGE

        lines = [
            '// Generated by LitigationOS Typst Pipeline — Proposed Order',
            f'// Filing: {filing_id}',
            '',
            '#import "proposed-order.typ": proposed-order, order-item, further-ordered',
            '',
            '#show: proposed-order.with(',
            f'  case-number: "{meta.get("case_number", "")}",',
            f'  court: "{court_name}",',
            f'  judge: "{judge}",',
            f'  plaintiff: "{PLAINTIFF}",',
            f'  defendant: "{DEFENDANT}",',
            f'  document-title: "{self._escape_title(meta.get("title", "ORDER"))}",',
            ')',
            '',
            self._apply_format_overrides(fmt),
            '',
            body,
        ]
        return "\n".join(lines)

    def build_fee_waiver(self, md_content: str, filing_id: str, meta: dict,
                         fmt: CourtFormat) -> str:
        """Build a fee waiver (MC 20) document."""
        body = self.converter.convert(md_content)
        filing_date = datetime.now().strftime("%B %d, %Y")
        court_name = self._court_for_caption(meta)

        lines = [
            '// Generated by LitigationOS Typst Pipeline — Fee Waiver MC 20',
            f'// Filing: {filing_id}',
            '',
            '#import "caption.typ": court-page, caption, pro-se-signature',
            '',
            '#show: court-page',
            '',
            self._apply_format_overrides(fmt),
            '',
            '#caption(',
            f'  case-number: "{meta.get("case_number", "")}",',
            f'  court: "{court_name}",',
            f'  judge: "{meta.get("judge", JUDGE)}",',
            f'  plaintiff: "{PLAINTIFF}",',
            f'  defendant: "{DEFENDANT}",',
            '  document-title: "REQUEST TO WAIVE FEES (MC 20)",',
            ')',
            '',
            body,
            '',
            f'#pro-se-signature(date: "{filing_date}")',
        ]
        return "\n".join(lines)

    def build_affidavit(self, md_content: str, filing_id: str, meta: dict,
                        fmt: CourtFormat) -> str:
        """Build an affidavit document."""
        body = self.converter.convert(md_content)
        filing_date = datetime.now().strftime("%B %d, %Y")
        court_name = self._court_for_caption(meta)

        lines = [
            '// Generated by LitigationOS Typst Pipeline — Affidavit',
            f'// Filing: {filing_id}',
            '',
            '#import "caption.typ": court-page, caption, pro-se-signature, numbered-paras',
            '',
            '#show: court-page',
            '',
            self._apply_format_overrides(fmt),
            '',
            '#caption(',
            f'  case-number: "{meta.get("case_number", "")}",',
            f'  court: "{court_name}",',
            f'  judge: "{meta.get("judge", JUDGE)}",',
            f'  plaintiff: "{PLAINTIFF}",',
            f'  defendant: "{DEFENDANT}",',
            '  document-title: "AFFIDAVIT OF ANDREW JAMES PIGORS",',
            ')',
            '',
            body,
            '',
            '== VERIFICATION',
            '',
            f'I, {PLAINTIFF}, declare under penalty of perjury under the laws of '
            'the State of Michigan that the foregoing statements are true and '
            'correct to the best of my knowledge, information, and belief.',
            '',
            f'#pro-se-signature(date: "{filing_date}")',
        ]
        return "\n".join(lines)

    def build_exhibit_index(self, md_content: str, filing_id: str, meta: dict,
                            fmt: CourtFormat) -> str:
        """Build an exhibit index document."""
        body = self.converter.convert(md_content)
        filing_date = datetime.now().strftime("%B %d, %Y")
        court_name = self._court_for_caption(meta)

        lines = [
            '// Generated by LitigationOS Typst Pipeline — Exhibit Index',
            f'// Filing: {filing_id}',
            '',
            '#import "caption.typ": court-page, caption, pro-se-signature',
            '',
            '#show: court-page',
            '',
            self._apply_format_overrides(fmt),
            '',
            '#caption(',
            f'  case-number: "{meta.get("case_number", "")}",',
            f'  court: "{court_name}",',
            f'  judge: "{meta.get("judge", JUDGE)}",',
            f'  plaintiff: "{PLAINTIFF}",',
            f'  defendant: "{DEFENDANT}",',
            '  document-title: "INDEX OF EXHIBITS",',
            ')',
            '',
            body,
            '',
            f'#pro-se-signature(date: "{filing_date}")',
        ]
        return "\n".join(lines)

    def build_general(self, md_content: str, filing_id: str, meta: dict,
                      fmt: CourtFormat) -> str:
        """Build a generic court document (complaint, petition, letter, etc.)."""
        body = self.converter.convert(md_content)
        filing_date = datetime.now().strftime("%B %d, %Y")
        court_name = self._court_for_caption(meta)
        title = meta.get("title", "DOCUMENT")

        # JTC complaints use letter format (single-spaced)
        if fmt.court_type == "JTC":
            return self._build_jtc_letter(body, filing_id, meta, fmt, filing_date)

        lines = [
            '// Generated by LitigationOS Typst Pipeline',
            f'// Filing: {filing_id} — {title}',
            '',
            '#import "caption.typ": court-page, caption, pro-se-signature, numbered-paras',
            '#import "certificate-of-service.typ": certificate-of-service',
            '',
            '#show: court-page',
            '',
            self._apply_format_overrides(fmt),
            '',
            '#caption(',
            f'  case-number: "{meta.get("case_number", "")}",',
            f'  court: "{court_name}",',
            f'  judge: "{meta.get("judge", JUDGE)}",',
            f'  plaintiff: "{PLAINTIFF}",',
            f'  defendant: "{DEFENDANT}",',
            f'  document-title: "{self._escape_title(title)}",',
            ')',
            '',
            body,
            '',
            f'#pro-se-signature(date: "{filing_date}")',
            '',
            '#certificate-of-service(',
            f'  date: "{filing_date}",',
            '  method: "first-class U.S. Mail, postage prepaid",',
            ')',
        ]
        return "\n".join(lines)

    def _build_jtc_letter(self, body: str, filing_id: str, meta: dict,
                          fmt: CourtFormat, filing_date: str) -> str:
        """Build JTC complaint as a formal letter (not court caption format)."""
        lines = [
            '// Generated by LitigationOS Typst Pipeline — JTC Complaint (Letter)',
            f'// Filing: {filing_id}',
            '',
            '#set page(paper: "us-letter", margin: 1in)',
            f'#set text(font: "{fmt.font}", size: {fmt.font_size})',
            '#set par(leading: 0.85em, first-line-indent: 0pt, spacing: 0.85em)',
            '',
            f'#align(right)[{filing_date}]',
            '',
            'Judicial Tenure Commission \\',
            '3034 W. Grand Blvd., Suite 8-450 \\',
            'Detroit, MI 48202',
            '',
            '*Re: Formal Complaint Against Hon. Jenny L. McNeill (P58235)* \\',
            '*14th Judicial Circuit Court, Muskegon County*',
            '',
            'Dear Commissioners:',
            '',
            body,
            '',
            'Respectfully submitted,',
            '',
            '#v(0.4in)',
            '#line(length: 3in, stroke: 0.5pt)',
            f'*{PLAINTIFF}*  \\',
            'Complainant \\',
            '1977 Whitehall Rd, Lot 17 \\',
            'North Muskegon, MI 49445 \\',
            '(231) 903-5690 \\',
            'andrewjpigors\\@gmail.com',
        ]
        return "\n".join(lines)

    def _apply_format_overrides(self, fmt: CourtFormat) -> str:
        """Generate Typst set rules for court-specific formatting overrides."""
        parts = []
        if fmt.font_size != "12pt":
            parts.append(f'#set text(size: {fmt.font_size})')
        if fmt.line_spacing == "single":
            parts.append('#set par(leading: 0.85em, spacing: 0.85em)')
        if fmt.margins != "1in":
            parts.append(f'#set page(margin: {fmt.margins})')
        return "\n".join(parts)

    def _court_for_caption(self, meta: dict) -> str:
        """Get court name formatted for the caption template."""
        court = meta.get("court", "")
        if "CIRCUIT" in court.upper():
            return "CIRCUIT COURT FOR THE COUNTY OF MUSKEGON"
        if "SUPREME" in court.upper():
            return court
        if "APPEALS" in court.upper():
            return court
        if "DISTRICT COURT" in court.upper():
            return court
        if "TENURE" in court.upper():
            return court
        return court

    @staticmethod
    def _escape_title(title: str) -> str:
        """Escape Typst-special characters in a document title."""
        title = title.replace('"', '\\"')
        title = title.replace("§", "\\u{00A7}")
        return title


# ─────────────────────────────────────────────────────────────
# TYPST COMPILER
# ─────────────────────────────────────────────────────────────

class TypstCompiler:
    """Wraps the Typst binary for compilation."""

    def __init__(self, typst_bin: str = TYPST_BIN, templates_dir: Path = TEMPLATE_DIR):
        self.typst_bin = typst_bin
        self.templates_dir = templates_dir
        if not Path(self.typst_bin).exists():
            raise FileNotFoundError(
                f"Typst binary not found at {self.typst_bin}. "
                "Install via: winget install typst"
            )

    def compile(self, typst_source: str, output_pdf: Path,
                source_name: str = "pipeline_gen.typ") -> Path:
        """Write Typst source to a temp file in templates dir, compile to PDF.

        The .typ file is written INTO the templates directory so that
        relative #import paths resolve correctly (e.g., #import "motion.typ").

        Returns the Path to the generated PDF.
        """
        output_pdf = Path(output_pdf)
        output_pdf.parent.mkdir(parents=True, exist_ok=True)

        typ_path = self.templates_dir / source_name
        try:
            typ_path.write_text(typst_source, encoding="utf-8")

            result = subprocess.run(
                [self.typst_bin, "compile", str(typ_path), str(output_pdf)],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(self.templates_dir),
            )

            if result.returncode != 0:
                stderr = result.stderr.strip()
                raise RuntimeError(
                    f"Typst compilation failed (exit {result.returncode}):\n{stderr}"
                )

            if not output_pdf.exists():
                raise RuntimeError(
                    f"Typst exited successfully but PDF not found at {output_pdf}"
                )

            size_kb = output_pdf.stat().st_size / 1024
            if size_kb < 1:
                raise RuntimeError(
                    f"Generated PDF is suspiciously small ({size_kb:.1f} KB)"
                )

            return output_pdf

        finally:
            if typ_path.exists():
                typ_path.unlink()


# ─────────────────────────────────────────────────────────────
# PIPELINE — the main orchestrator
# ─────────────────────────────────────────────────────────────

class TypstPipeline:
    """End-to-end markdown → court-ready PDF pipeline.

    Usage:
        pipe = TypstPipeline()

        # Single document
        pdf = pipe.compile_document("path/to/motion.md", "F10")

        # Full packet
        results = pipe.compile_packet("F10")

        # Everything
        all_results = pipe.compile_all()
    """

    def __init__(
        self,
        golden_set_path: Optional[Path] = None,
        templates_path: Optional[Path] = None,
        output_base: Optional[Path] = None,
    ):
        self.golden_set = Path(golden_set_path) if golden_set_path else GOLDEN_SET
        self.templates = Path(templates_path) if templates_path else TEMPLATE_DIR
        self.output_base = Path(output_base) if output_base else self.golden_set
        self.builder = TypstDocumentBuilder(self.templates)
        self.compiler = TypstCompiler(templates_dir=self.templates)

    def get_filing_metadata(self, filing_id: str) -> dict:
        """Get case metadata for a filing (case number, court, judge, etc.)."""
        fid = filing_id.upper()
        if fid not in FILING_METADATA:
            raise ValueError(
                f"Unknown filing ID: {filing_id}. "
                f"Valid IDs: {sorted(FILING_METADATA.keys())}"
            )
        return dict(FILING_METADATA[fid])

    def get_court_format(self, filing_id: str) -> CourtFormat:
        """Get court formatting rules for a filing."""
        fid = filing_id.upper()
        return COURT_FORMATS.get(fid, CourtFormat("Circuit"))

    def discover_packet_documents(self, filing_id: str) -> list[Path]:
        """Find all markdown documents in a filing packet directory."""
        meta = self.get_filing_metadata(filing_id)
        packet_dir = self.golden_set / meta["subdir"]
        if not packet_dir.exists():
            raise FileNotFoundError(f"Packet directory not found: {packet_dir}")

        md_files = sorted(packet_dir.glob("*.md"))
        return [f for f in md_files if f.name.upper() != "README.MD"]

    def compile_document(
        self,
        md_path: str,
        filing_id: str,
        output_dir: Optional[str] = None,
    ) -> str:
        """Convert a single markdown document to court-formatted PDF.

        Args:
            md_path: Path to the markdown file (absolute or relative to GOLDEN_SET)
            filing_id: Filing identifier (F01-F10)
            output_dir: Output directory for PDF (default: packet_dir/PDF/)

        Returns:
            Absolute path to the generated PDF
        """
        md_file = Path(md_path)
        if not md_file.is_absolute():
            meta = self.get_filing_metadata(filing_id)
            md_file = self.golden_set / meta["subdir"] / md_path

        if not md_file.exists():
            raise FileNotFoundError(f"Markdown file not found: {md_file}")

        md_content = md_file.read_text(encoding="utf-8")
        meta = self.get_filing_metadata(filing_id)
        fmt = self.get_court_format(filing_id)

        doc_type = detect_doc_type(md_file.name, md_content)

        typst_source = self._build_typst_source(md_content, doc_type, filing_id,
                                                 meta, fmt)

        if output_dir:
            out_dir = Path(output_dir)
        else:
            out_dir = md_file.parent / "PDF"

        pdf_name = md_file.stem + ".pdf"
        output_pdf = out_dir / pdf_name

        source_name = f"_pipeline_{filing_id}_{md_file.stem}.typ"

        result = self.compiler.compile(typst_source, output_pdf,
                                        source_name=source_name)
        return str(result)

    def compile_packet(
        self,
        filing_id: str,
        output_dir: Optional[str] = None,
    ) -> dict:
        """Compile all documents in a filing packet.

        Args:
            filing_id: Filing identifier (F01-F10)
            output_dir: Output directory for PDFs

        Returns:
            Dict of {filename: pdf_path} for successfully compiled documents,
            plus "_errors" key for any failures.
        """
        docs = self.discover_packet_documents(filing_id)
        meta = self.get_filing_metadata(filing_id)

        if output_dir:
            out_dir = Path(output_dir)
        else:
            out_dir = self.golden_set / meta["subdir"] / "PDF"

        results = {}
        errors = {}

        for md_file in docs:
            try:
                pdf_path = self.compile_document(
                    str(md_file), filing_id, str(out_dir)
                )
                results[md_file.name] = pdf_path
            except Exception as exc:
                errors[md_file.name] = str(exc)

        if errors:
            results["_errors"] = errors

        return results

    def compile_all(self, output_dir: Optional[str] = None) -> dict:
        """Compile ALL golden set packets.

        Returns:
            Nested dict: {filing_id: {filename: pdf_path, ...}, ...}
        """
        all_results = {}
        for filing_id in sorted(FILING_METADATA.keys()):
            try:
                meta = FILING_METADATA[filing_id]
                packet_dir = self.golden_set / meta["subdir"]
                if not packet_dir.exists():
                    all_results[filing_id] = {"_error": f"Directory not found: {packet_dir}"}
                    continue
                all_results[filing_id] = self.compile_packet(filing_id, output_dir)
            except Exception as exc:
                all_results[filing_id] = {"_error": str(exc)}
        return all_results

    def markdown_to_typst(self, md_content: str, doc_type: str,
                          filing_id: str) -> str:
        """Convert markdown content to Typst markup with correct court formatting.

        This is the public API for getting the raw Typst source without
        compiling to PDF — useful for inspection and debugging.
        """
        meta = self.get_filing_metadata(filing_id)
        fmt = self.get_court_format(filing_id)
        return self._build_typst_source(md_content, doc_type, filing_id, meta, fmt)

    def _build_typst_source(self, md_content: str, doc_type: str,
                            filing_id: str, meta: dict,
                            fmt: CourtFormat) -> str:
        """Route to the correct builder method based on document type."""
        # Insert dynamic content
        md_content = self._inject_dynamic_content(md_content)

        # Select builder
        builder_map = {
            "motion": self.builder.build_motion,
            "brief": self.builder.build_brief,
            "certificate_of_service": self.builder.build_certificate_of_service,
            "proposed_order": self.builder.build_proposed_order,
            "fee_waiver": self.builder.build_fee_waiver,
            "affidavit": self.builder.build_affidavit,
            "exhibit_index": self.builder.build_exhibit_index,
            "complaint": self.builder.build_general,
            "petition": self.builder.build_general,
            "general": self.builder.build_general,
        }

        build_fn = builder_map.get(doc_type, self.builder.build_general)
        return build_fn(md_content, filing_id, meta, fmt)

    def _inject_dynamic_content(self, md_content: str) -> str:
        """Replace dynamic placeholders with computed values."""
        today = datetime.now()
        sep_days = compute_separation_days()

        # Replace date placeholders
        md_content = re.sub(
            r"_+,\s*2026",
            f"{today.strftime('%B %d')}, 2026",
            md_content,
        )
        md_content = re.sub(
            r"Dated:\s*_+",
            f"Dated: {today.strftime('%B %d, %Y')}",
            md_content,
        )

        # Replace separation day references with actual count
        md_content = re.sub(
            r"\bover\s+\*?\*?eight months\*?\*?",
            f"over *{sep_days} days* (since July 29, 2025)",
            md_content,
            flags=re.IGNORECASE,
        )

        # Ensure child's name compliance
        md_content = sanitize_child_name(md_content)

        return md_content


# ─────────────────────────────────────────────────────────────
# REPORTING
# ─────────────────────────────────────────────────────────────

def format_compile_report(results: dict, filing_id: str) -> str:
    """Format compilation results into a human-readable report."""
    lines = [
        f"═══ Typst Pipeline Report: {filing_id} ═══",
        f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Separation days: {compute_separation_days()}",
        "",
    ]

    successes = {k: v for k, v in results.items() if not k.startswith("_")}
    errors = results.get("_errors", {})

    lines.append(f"Compiled: {len(successes)} documents")
    if errors:
        lines.append(f"Errors: {len(errors)} documents")
    lines.append("")

    for name, path in sorted(successes.items()):
        size_kb = Path(path).stat().st_size / 1024 if Path(path).exists() else 0
        lines.append(f"  ✓ {name}")
        lines.append(f"    → {path} ({size_kb:.1f} KB)")

    if errors:
        lines.append("")
        lines.append("ERRORS:")
        for name, err in sorted(errors.items()):
            lines.append(f"  ✗ {name}")
            lines.append(f"    → {err}")

    lines.append("")
    lines.append("═" * 50)
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────
# CLI ENTRY POINT
# ─────────────────────────────────────────────────────────────

def main():
    """CLI entry point for the Typst Pipeline."""
    import sys

    args = sys.argv[1:]
    if not args:
        print("Usage:")
        print("  python pipeline.py F10             # compile one packet")
        print("  python pipeline.py --all            # compile everything")
        print("  python pipeline.py --doc F10 file.md  # compile one document")
        print("  python pipeline.py --list F10       # list packet documents")
        sys.exit(0)

    pipe = TypstPipeline()

    if args[0] == "--all":
        print("Compiling ALL golden set packets...")
        results = pipe.compile_all()
        for fid, packet_results in sorted(results.items()):
            print(format_compile_report(packet_results, fid))
        sys.exit(0)

    if args[0] == "--list":
        if len(args) < 2:
            print("Usage: python pipeline.py --list F10")
            sys.exit(1)
        fid = args[1].upper()
        docs = pipe.discover_packet_documents(fid)
        print(f"Documents in {fid}:")
        for d in docs:
            dtype = detect_doc_type(d.name)
            print(f"  {d.name}  [{dtype}]")
        sys.exit(0)

    if args[0] == "--doc":
        if len(args) < 3:
            print("Usage: python pipeline.py --doc F10 file.md")
            sys.exit(1)
        fid = args[1].upper()
        md_name = args[2]
        try:
            pdf = pipe.compile_document(md_name, fid)
            print(f"Compiled: {pdf}")
        except Exception as exc:
            print(f"Error: {exc}")
            sys.exit(1)
        sys.exit(0)

    # Default: compile a packet
    fid = args[0].upper()
    try:
        results = pipe.compile_packet(fid)
        print(format_compile_report(results, fid))
    except Exception as exc:
        print(f"Error compiling {fid}: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
