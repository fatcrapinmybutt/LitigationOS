"""PDF Production Engine — Bates stamping, form filling, MD→PDF, exhibit covers.

Provides the missing PDF production capabilities that turn LitigationOS
evidence and filings into court-ready PDF packages:

1. **Bates Stamping**: Overlay Bates numbers onto existing PDF pages (pikepdf + reportlab)
2. **Form Filling**: Fill SCAO court form AcroForm fields programmatically (pikepdf)
3. **Markdown to PDF**: Convert filing markdown to court-formatted PDF (reportlab)
4. **Exhibit Covers**: Generate professional exhibit cover/separator pages (reportlab)

All methods are stateless — they accept file paths and return output paths.
"""

from __future__ import annotations

import io
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pikepdf
from reportlab.lib.colors import Color, black, white
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)

logger = logging.getLogger(__name__)

# MBP LLC brand pink
_MBP_PINK = Color(1.0, 0.078, 0.576)  # #FF1493
_COURT_FONT = "Times-Roman"
_COURT_FONT_BOLD = "Times-Bold"
_COURT_FONT_SIZE = 12
_COURT_LEADING = 24  # double-spaced


# ---------------------------------------------------------------------------
# 1. BATES STAMPING
# ---------------------------------------------------------------------------


def stamp_bates_on_pdf(
    input_pdf: str | Path,
    output_pdf: str | Path,
    start_number: int = 1,
    prefix: str = "PIGORS",
    position: str = "bottom-right",
    font_size: int = 10,
) -> Tuple[Path, int]:
    """Overlay Bates numbers on every page of a PDF.

    Creates a transparent overlay with the Bates number using reportlab,
    then merges it onto each page using pikepdf.

    Args:
        input_pdf: Source PDF file.
        output_pdf: Destination stamped PDF.
        start_number: First Bates number.
        prefix: Bates prefix (e.g. "PIGORS").
        position: One of "bottom-right", "bottom-left", "bottom-center".
        font_size: Stamp font size in points.

    Returns:
        Tuple of (output path, next available Bates number).
    """
    input_pdf = Path(input_pdf)
    output_pdf = Path(output_pdf)
    output_pdf.parent.mkdir(parents=True, exist_ok=True)

    if not input_pdf.exists():
        raise FileNotFoundError(f"PDF not found: {input_pdf}")

    src = pikepdf.Pdf.open(str(input_pdf))
    num_pages = len(src.pages)

    for i, page in enumerate(src.pages):
        bates_num = f"{prefix}-{start_number + i:06d}"
        overlay_bytes = _create_bates_overlay(
            bates_num, page, position, font_size
        )
        overlay_pdf = pikepdf.Pdf.open(io.BytesIO(overlay_bytes))
        overlay_page = overlay_pdf.pages[0]

        # Merge overlay onto existing page
        page_obj = page.obj
        if "/Resources" not in page_obj:
            page_obj["/Resources"] = pikepdf.Dictionary()

        # Use pikepdf's page overlay method
        page.add_overlay(overlay_page)

    src.save(str(output_pdf))
    src.close()

    next_num = start_number + num_pages
    logger.info(
        "Stamped %d pages: %s-%06d through %s-%06d → %s",
        num_pages, prefix, start_number, prefix, next_num - 1, output_pdf,
    )
    return output_pdf, next_num


def _create_bates_overlay(
    bates_text: str,
    page: Any,
    position: str,
    font_size: int,
) -> bytes:
    """Create a single-page transparent PDF with the Bates number."""
    # Get page dimensions
    mediabox = page.mediabox
    page_width = float(mediabox[2]) - float(mediabox[0])
    page_height = float(mediabox[3]) - float(mediabox[1])

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(page_width, page_height))

    c.setFont("Courier", font_size)
    c.setFillColor(black)

    margin = 36  # 0.5 inch
    y_pos = margin - font_size  # just inside bottom margin
    if y_pos < 10:
        y_pos = 10

    if position == "bottom-right":
        x_pos = page_width - margin - c.stringWidth(bates_text, "Courier", font_size)
    elif position == "bottom-left":
        x_pos = margin
    else:  # bottom-center
        x_pos = (page_width - c.stringWidth(bates_text, "Courier", font_size)) / 2

    c.drawString(x_pos, y_pos, bates_text)
    c.save()
    return buf.getvalue()


def stamp_bates_batch(
    pdf_files: List[str | Path],
    output_dir: str | Path,
    start_number: int = 1,
    prefix: str = "PIGORS",
) -> List[Dict[str, Any]]:
    """Bates-stamp a batch of PDFs with sequential numbering.

    Args:
        pdf_files: Ordered list of PDF paths.
        output_dir: Directory for stamped output.
        start_number: First Bates number.
        prefix: Bates prefix.

    Returns:
        List of dicts: {input, output, start, end, page_count}.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    results = []
    current = start_number

    for pdf in pdf_files:
        pdf = Path(pdf)
        out = output_dir / f"BATES_{pdf.name}"
        try:
            out_path, current = stamp_bates_on_pdf(
                pdf, out, start_number=current, prefix=prefix
            )
            results.append({
                "input": str(pdf),
                "output": str(out_path),
                "start": f"{prefix}-{current - (current - results[-1]['page_count'] if results else start_number):06d}" if not results else f"{prefix}-{current - _count_pages(pdf):06d}",
                "end": f"{prefix}-{current - 1:06d}",
                "page_count": _count_pages(pdf),
            })
        except Exception as e:
            logger.error("Failed to stamp %s: %s", pdf, e)
            results.append({"input": str(pdf), "error": str(e)})

    return results


def _count_pages(pdf_path: Path) -> int:
    """Count pages in a PDF without fully reading it."""
    try:
        with pikepdf.Pdf.open(str(pdf_path)) as p:
            return len(p.pages)
    except Exception:
        return 0


# ---------------------------------------------------------------------------
# 2. PDF FORM FILLING (SCAO AcroForm)
# ---------------------------------------------------------------------------


def fill_pdf_form(
    template_pdf: str | Path,
    output_pdf: str | Path,
    field_values: Dict[str, str],
    flatten: bool = True,
) -> Path:
    """Fill AcroForm fields in a PDF template.

    Uses pikepdf to set field values. Works with Michigan SCAO forms that
    have standard AcroForm field definitions.

    Args:
        template_pdf: Path to the form template PDF.
        output_pdf: Destination filled PDF.
        field_values: Dict mapping field names to values.
        flatten: If True, flatten form fields (makes them non-editable).

    Returns:
        Path to the output PDF.
    """
    template_pdf = Path(template_pdf)
    output_pdf = Path(output_pdf)
    output_pdf.parent.mkdir(parents=True, exist_ok=True)

    if not template_pdf.exists():
        raise FileNotFoundError(f"Template not found: {template_pdf}")

    pdf = pikepdf.Pdf.open(str(template_pdf))

    if "/AcroForm" not in pdf.Root:
        logger.warning("No AcroForm found in %s — cannot fill fields", template_pdf)
        pdf.save(str(output_pdf))
        pdf.close()
        return output_pdf

    filled_count = 0
    for page in pdf.pages:
        if "/Annots" not in page:
            continue
        for annot in page["/Annots"]:
            annot_obj = annot.resolve() if hasattr(annot, 'resolve') else annot
            if "/T" not in annot_obj:
                continue
            field_name = str(annot_obj["/T"])
            if field_name in field_values:
                value = field_values[field_name]
                annot_obj["/V"] = pikepdf.String(value)
                # Also set the appearance string for display
                if "/AP" in annot_obj:
                    try:
                        del annot_obj["/AP"]
                    except Exception:
                        pass
                # Set NeedAppearances flag so viewers regenerate
                if "/AcroForm" in pdf.Root:
                    pdf.Root["/AcroForm"]["/NeedAppearances"] = pikepdf.Name("/true")
                filled_count += 1

    if flatten:
        _flatten_form(pdf)

    pdf.save(str(output_pdf))
    pdf.close()
    logger.info("Filled %d fields in %s → %s", filled_count, template_pdf, output_pdf)
    return output_pdf


def _flatten_form(pdf: pikepdf.Pdf) -> None:
    """Flatten form fields so they appear as static text."""
    try:
        for page in pdf.pages:
            if "/Annots" not in page:
                continue
            annots_to_keep = []
            for annot in page["/Annots"]:
                annot_obj = annot.resolve() if hasattr(annot, 'resolve') else annot
                ft = annot_obj.get("/FT")
                if ft and str(ft) in ("/Tx", "/Ch", "/Btn"):
                    # Set read-only flag
                    flags = int(annot_obj.get("/Ff", 0))
                    annot_obj["/Ff"] = pikepdf.Object.parse(str(flags | 1))
                annots_to_keep.append(annot)
            page["/Annots"] = pikepdf.Array(annots_to_keep)
    except Exception as e:
        logger.warning("Flatten failed (non-critical): %s", e)


def get_form_fields(pdf_path: str | Path) -> List[Dict[str, str]]:
    """Extract all AcroForm field names and current values from a PDF.

    Args:
        pdf_path: Path to the PDF.

    Returns:
        List of dicts: {name, value, type}.
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    pdf = pikepdf.Pdf.open(str(pdf_path))
    fields = []

    for page in pdf.pages:
        if "/Annots" not in page:
            continue
        for annot in page["/Annots"]:
            annot_obj = annot.resolve() if hasattr(annot, 'resolve') else annot
            if "/T" not in annot_obj:
                continue
            field_name = str(annot_obj["/T"])
            field_value = str(annot_obj.get("/V", ""))
            field_type = str(annot_obj.get("/FT", "unknown"))
            fields.append({
                "name": field_name,
                "value": field_value,
                "type": field_type,
            })

    pdf.close()
    return fields


# ---------------------------------------------------------------------------
# 3. MARKDOWN TO PDF
# ---------------------------------------------------------------------------


def markdown_to_pdf(
    markdown_text: str,
    output_pdf: str | Path,
    title: Optional[str] = None,
    case_caption: Optional[str] = None,
    page_numbers: bool = True,
) -> Path:
    """Convert markdown text to a court-formatted PDF.

    Parses markdown headings, bold, italic, lists, and blockquotes into
    reportlab flowables with Michigan court formatting (Times New Roman,
    12pt, double-spaced, 1-inch margins).

    Args:
        markdown_text: Raw markdown content.
        output_pdf: Output PDF path.
        title: Optional document title for header.
        case_caption: Optional case caption block.
        page_numbers: Whether to add page numbers.

    Returns:
        Path to the output PDF.
    """
    output_pdf = Path(output_pdf)
    output_pdf.parent.mkdir(parents=True, exist_ok=True)

    styles = getSampleStyleSheet()
    body = ParagraphStyle(
        "CourtBody", parent=styles["Normal"],
        fontName=_COURT_FONT, fontSize=_COURT_FONT_SIZE, leading=_COURT_LEADING,
        spaceAfter=6,
    )
    heading1 = ParagraphStyle(
        "CourtH1", parent=styles["Heading1"],
        fontName=_COURT_FONT_BOLD, fontSize=14, leading=28,
        spaceAfter=12, spaceBefore=18,
    )
    heading2 = ParagraphStyle(
        "CourtH2", parent=styles["Heading2"],
        fontName=_COURT_FONT_BOLD, fontSize=12, leading=24,
        spaceAfter=8, spaceBefore=14,
    )
    heading3 = ParagraphStyle(
        "CourtH3", parent=styles["Heading3"],
        fontName=_COURT_FONT_BOLD, fontSize=12, leading=24,
        spaceAfter=6, spaceBefore=10,
    )
    blockquote_style = ParagraphStyle(
        "CourtBlockquote", parent=body,
        leftIndent=36, rightIndent=36,
        fontName="Times-Italic", fontSize=11,
    )
    list_item = ParagraphStyle(
        "CourtListItem", parent=body,
        leftIndent=36, bulletIndent=18,
    )

    flowables: list = []

    # Case caption
    if case_caption:
        caption_style = ParagraphStyle(
            "Caption", parent=body,
            alignment=1,  # center
            fontName=_COURT_FONT_BOLD, fontSize=12,
            spaceAfter=18,
        )
        for line in case_caption.strip().split("\n"):
            flowables.append(Paragraph(line.strip(), caption_style))
        flowables.append(Spacer(1, 18))

    # Title
    if title:
        title_style = ParagraphStyle(
            "DocTitle", parent=heading1,
            alignment=1, fontSize=14, spaceAfter=24,
        )
        flowables.append(Paragraph(_escape_xml(title), title_style))
        flowables.append(Spacer(1, 12))

    # Parse markdown into flowables
    lines = markdown_text.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            flowables.append(Spacer(1, 6))
            i += 1
            continue

        # Headings
        if stripped.startswith("### "):
            text = _md_inline_to_xml(stripped[4:])
            flowables.append(Paragraph(text, heading3))
        elif stripped.startswith("## "):
            text = _md_inline_to_xml(stripped[3:])
            flowables.append(Paragraph(text, heading2))
        elif stripped.startswith("# "):
            text = _md_inline_to_xml(stripped[2:])
            flowables.append(Paragraph(text, heading1))
        # Horizontal rule
        elif stripped in ("---", "***", "___"):
            flowables.append(Spacer(1, 6))
            flowables.append(
                Table(
                    [[""]],
                    colWidths=[6.5 * inch],
                    style=TableStyle([("LINEABOVE", (0, 0), (-1, 0), 1, black)]),
                )
            )
            flowables.append(Spacer(1, 6))
        # Blockquote
        elif stripped.startswith("> "):
            text = _md_inline_to_xml(stripped[2:])
            flowables.append(Paragraph(text, blockquote_style))
        # List items
        elif stripped.startswith("- ") or stripped.startswith("* "):
            text = _md_inline_to_xml(stripped[2:])
            flowables.append(Paragraph(f"• {text}", list_item))
        elif re.match(r"^\d+\.\s", stripped):
            num_match = re.match(r"^(\d+)\.\s(.+)", stripped)
            if num_match:
                text = _md_inline_to_xml(num_match.group(2))
                flowables.append(
                    Paragraph(f"{num_match.group(1)}. {text}", list_item)
                )
        # Page break marker
        elif stripped == "<!-- pagebreak -->":
            flowables.append(PageBreak())
        # Normal paragraph
        else:
            text = _md_inline_to_xml(stripped)
            flowables.append(Paragraph(text, body))

        i += 1

    # Build with page numbers
    if page_numbers:
        doc = SimpleDocTemplate(
            str(output_pdf), pagesize=letter,
            leftMargin=inch, rightMargin=inch,
            topMargin=inch, bottomMargin=inch,
        )
        doc.build(flowables, onFirstPage=_add_page_number, onLaterPages=_add_page_number)
    else:
        doc = SimpleDocTemplate(
            str(output_pdf), pagesize=letter,
            leftMargin=inch, rightMargin=inch,
            topMargin=inch, bottomMargin=inch,
        )
        doc.build(flowables)

    logger.info("Generated PDF from markdown: %s", output_pdf)
    return output_pdf


def markdown_file_to_pdf(
    markdown_path: str | Path,
    output_pdf: str | Path,
    **kwargs: Any,
) -> Path:
    """Read a markdown file and convert to PDF.

    Args:
        markdown_path: Source ``.md`` file.
        output_pdf: Destination PDF.
        **kwargs: Passed to :func:`markdown_to_pdf`.

    Returns:
        Path to the output PDF.
    """
    md_path = Path(markdown_path)
    if not md_path.exists():
        raise FileNotFoundError(f"Markdown file not found: {md_path}")
    text = md_path.read_text(encoding="utf-8")
    return markdown_to_pdf(text, output_pdf, **kwargs)


def _escape_xml(text: str) -> str:
    """Escape XML special chars for reportlab Paragraph."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _md_inline_to_xml(text: str) -> str:
    """Convert inline markdown (bold, italic, code) to reportlab XML."""
    text = _escape_xml(text)
    # Bold: **text** or __text__
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"__(.+?)__", r"<b>\1</b>", text)
    # Italic: *text* or _text_
    text = re.sub(r"\*(.+?)\*", r"<i>\1</i>", text)
    text = re.sub(r"(?<!\w)_(.+?)_(?!\w)", r"<i>\1</i>", text)
    # Code: `text`
    text = re.sub(r"`(.+?)`", r"<font name='Courier' size='10'>\1</font>", text)
    return text


def _add_page_number(canvas_obj: canvas.Canvas, doc: Any) -> None:
    """Add centered page number at bottom of each page."""
    canvas_obj.saveState()
    canvas_obj.setFont(_COURT_FONT, 10)
    page_num = canvas_obj.getPageNumber()
    text = f"Page {page_num}"
    canvas_obj.drawCentredString(letter[0] / 2, 0.5 * inch, text)
    canvas_obj.restoreState()


# ---------------------------------------------------------------------------
# 4. EXHIBIT COVER PAGES
# ---------------------------------------------------------------------------


def create_exhibit_cover(
    exhibit_label: str,
    exhibit_title: str,
    output_pdf: str | Path,
    case_caption: Optional[str] = None,
    bates_range: Optional[str] = None,
    case_number: str = "2024-001507-DC",
    party_name: str = "Andrew James Pigors",
) -> Path:
    """Generate a professional exhibit cover/separator page as PDF.

    Creates a single-page PDF with exhibit label, title, case info,
    and optional Bates range — suitable for inserting before each
    exhibit in a court filing package.

    Args:
        exhibit_label: e.g. "Exhibit A", "Exhibit 1".
        exhibit_title: Descriptive title of the exhibit.
        output_pdf: Output PDF path.
        case_caption: Full case caption (multi-line).
        bates_range: e.g. "PIGORS-000001 through PIGORS-000015".
        case_number: Court case number.
        party_name: Sponsoring party name.

    Returns:
        Path to the output PDF.
    """
    output_pdf = Path(output_pdf)
    output_pdf.parent.mkdir(parents=True, exist_ok=True)

    c = canvas.Canvas(str(output_pdf), pagesize=letter)
    width, height = letter

    # Tab on the right side for exhibit label
    tab_width = 1.5 * inch
    tab_height = 0.6 * inch
    tab_x = width - tab_width - 0.5 * inch
    tab_y = height - 1.5 * inch

    c.setFillColor(_MBP_PINK)
    c.roundRect(tab_x, tab_y, tab_width, tab_height, 6, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont(_COURT_FONT_BOLD, 14)
    c.drawCentredString(tab_x + tab_width / 2, tab_y + tab_height / 2 - 5, exhibit_label)

    # Case caption area
    y = height - 2.5 * inch
    c.setFillColor(black)

    if case_caption:
        c.setFont(_COURT_FONT, 11)
        for line in case_caption.strip().split("\n"):
            c.drawCentredString(width / 2, y, line.strip())
            y -= 16
    else:
        c.setFont(_COURT_FONT_BOLD, 11)
        c.drawCentredString(width / 2, y, f"Case No. {case_number}")
        y -= 20

    # Horizontal line
    y -= 10
    c.setStrokeColor(black)
    c.setLineWidth(1.5)
    c.line(inch, y, width - inch, y)
    y -= 30

    # Exhibit label (large, centered)
    c.setFont(_COURT_FONT_BOLD, 28)
    c.drawCentredString(width / 2, y, exhibit_label.upper())
    y -= 40

    # Exhibit title
    c.setFont(_COURT_FONT, 16)
    # Wrap long titles
    words = exhibit_title.split()
    current_line = ""
    for word in words:
        test = f"{current_line} {word}".strip()
        if c.stringWidth(test, _COURT_FONT, 16) < (width - 2 * inch):
            current_line = test
        else:
            c.drawCentredString(width / 2, y, current_line)
            y -= 22
            current_line = word
    if current_line:
        c.drawCentredString(width / 2, y, current_line)
        y -= 30

    # Horizontal line
    c.setLineWidth(0.5)
    c.line(2 * inch, y, width - 2 * inch, y)
    y -= 30

    # Metadata
    c.setFont(_COURT_FONT, 11)
    c.drawString(1.5 * inch, y, f"Offered by: {party_name}")
    y -= 18
    c.drawString(1.5 * inch, y, f"Case No.: {case_number}")
    y -= 18
    if bates_range:
        c.drawString(1.5 * inch, y, f"Bates Range: {bates_range}")
        y -= 18
    c.drawString(1.5 * inch, y, f"Date: {datetime.now().strftime('%B %d, %Y')}")

    # Footer — MBP LLC branding
    c.setFont("Helvetica", 8)
    c.setFillColor(Color(0.5, 0.5, 0.5))
    c.drawCentredString(width / 2, 0.4 * inch, "Prepared by MBP LLC — LitigationOS")

    c.save()
    logger.info("Created exhibit cover: %s → %s", exhibit_label, output_pdf)
    return output_pdf


def create_exhibit_covers_batch(
    exhibits: List[Dict[str, str]],
    output_dir: str | Path,
    case_caption: Optional[str] = None,
    case_number: str = "2024-001507-DC",
) -> List[Path]:
    """Generate exhibit covers for a batch of exhibits.

    Args:
        exhibits: List of dicts with keys: label, title, bates_range (optional).
        output_dir: Directory for cover PDFs.
        case_caption: Shared caption block.
        case_number: Case number.

    Returns:
        List of output PDF paths.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = []

    for ex in exhibits:
        label = ex.get("label", "Exhibit")
        safe_label = re.sub(r"[^\w]", "_", label)
        out = output_dir / f"COVER_{safe_label}.pdf"
        try:
            path = create_exhibit_cover(
                exhibit_label=label,
                exhibit_title=ex.get("title", ""),
                output_pdf=out,
                case_caption=case_caption,
                bates_range=ex.get("bates_range"),
                case_number=case_number,
            )
            paths.append(path)
        except Exception as e:
            logger.error("Failed to create cover for %s: %s", label, e)

    return paths


# ---------------------------------------------------------------------------
# 5. FILING PACKAGE ASSEMBLY
# ---------------------------------------------------------------------------


def assemble_filing_package(
    main_document: str | Path,
    exhibits: List[Dict[str, Any]],
    output_pdf: str | Path,
    case_caption: Optional[str] = None,
    case_number: str = "2024-001507-DC",
    bates_prefix: str = "PIGORS",
    bates_start: int = 1,
    add_covers: bool = True,
    add_bates: bool = True,
) -> Dict[str, Any]:
    """Assemble a complete court filing package as a single merged PDF.

    Takes a main document (MD or PDF) and exhibits, generates cover pages,
    applies Bates stamps, and merges everything into one PDF.

    Args:
        main_document: Main filing (Markdown .md or PDF .pdf).
        exhibits: List of dicts: {path, label, title}.
        output_pdf: Final merged output path.
        case_caption: Case caption for covers.
        case_number: Case number.
        bates_prefix: Prefix for Bates stamps.
        bates_start: Starting Bates number.
        add_covers: Whether to generate exhibit covers.
        add_bates: Whether to apply Bates stamps.

    Returns:
        Dict with package info: {output, page_count, bates_range, exhibits}.
    """
    from pypdf import PdfReader, PdfWriter

    main_doc = Path(main_document)
    output_pdf = Path(output_pdf)
    output_pdf.parent.mkdir(parents=True, exist_ok=True)

    temp_dir = output_pdf.parent / "_temp_assembly"
    temp_dir.mkdir(exist_ok=True)

    pdfs_to_merge: List[Path] = []
    manifest: List[Dict[str, Any]] = []

    # 1. Convert main document to PDF if needed
    if main_doc.suffix.lower() == ".md":
        main_pdf = temp_dir / "main_document.pdf"
        markdown_file_to_pdf(main_doc, main_pdf, case_caption=case_caption)
        pdfs_to_merge.append(main_pdf)
        manifest.append({"type": "main_document", "source": str(main_doc)})
    elif main_doc.suffix.lower() == ".pdf":
        pdfs_to_merge.append(main_doc)
        manifest.append({"type": "main_document", "source": str(main_doc)})
    else:
        raise ValueError(f"Unsupported main document format: {main_doc.suffix}")

    # 2. Process exhibits
    for ex in exhibits:
        ex_path = Path(ex["path"])
        if not ex_path.exists():
            logger.warning("Exhibit not found, skipping: %s", ex_path)
            continue

        # Add cover page
        if add_covers:
            label = ex.get("label", f"Exhibit {len(manifest)}")
            cover_path = temp_dir / f"cover_{label.replace(' ', '_')}.pdf"
            create_exhibit_cover(
                exhibit_label=label,
                exhibit_title=ex.get("title", ex_path.stem),
                output_pdf=cover_path,
                case_caption=case_caption,
                case_number=case_number,
                bates_range=ex.get("bates_range"),
            )
            pdfs_to_merge.append(cover_path)

        # Add the exhibit itself
        if ex_path.suffix.lower() == ".md":
            ex_pdf = temp_dir / f"exhibit_{ex_path.stem}.pdf"
            markdown_file_to_pdf(ex_path, ex_pdf)
            pdfs_to_merge.append(ex_pdf)
        elif ex_path.suffix.lower() == ".pdf":
            pdfs_to_merge.append(ex_path)
        else:
            logger.warning("Unsupported exhibit format %s, skipping", ex_path.suffix)
            continue

        manifest.append({
            "type": "exhibit",
            "label": ex.get("label", ""),
            "title": ex.get("title", ""),
            "source": str(ex_path),
        })

    # 3. Merge all PDFs
    merged_path = temp_dir / "merged_unBATES.pdf" if add_bates else output_pdf
    writer = PdfWriter()
    for pdf in pdfs_to_merge:
        try:
            reader = PdfReader(str(pdf))
            for page in reader.pages:
                writer.add_page(page)
        except Exception as e:
            logger.error("Failed to read %s: %s", pdf, e)

    with open(str(merged_path), "wb") as f:
        writer.write(f)

    total_pages = len(writer.pages)

    # 4. Apply Bates stamps
    if add_bates and merged_path != output_pdf:
        _, next_bates = stamp_bates_on_pdf(
            merged_path, output_pdf,
            start_number=bates_start, prefix=bates_prefix,
        )
        bates_range = f"{bates_prefix}-{bates_start:06d} through {bates_prefix}-{next_bates - 1:06d}"
    else:
        next_bates = bates_start
        bates_range = None

    # 5. Cleanup temp files
    try:
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
    except Exception:
        pass

    result = {
        "output": str(output_pdf),
        "page_count": total_pages,
        "bates_range": bates_range,
        "bates_next": next_bates,
        "exhibits": manifest,
        "exhibit_count": sum(1 for m in manifest if m["type"] == "exhibit"),
    }
    logger.info("Assembled filing package: %d pages, %d exhibits → %s",
                total_pages, result["exhibit_count"], output_pdf)
    return result


# ---------------------------------------------------------------------------
# 6. TABLE OF CONTENTS
# ---------------------------------------------------------------------------


def _toc_dot_leader(title: str, page_num: int, width: float) -> str:
    """Build a title . . . . page string with dot leaders for TOC/TOA rows."""
    dots = " . " * 40
    return f"{title}{dots}{page_num}"


def generate_toc(
    entries: List[Dict[str, Any]],
    output_pdf: str | Path,
    title: str = "TABLE OF CONTENTS",
    case_caption: Optional[str] = None,
) -> Path:
    """Generate a court-formatted Table of Contents PDF.

    Args:
        entries: List of dicts with keys ``title`` (str), ``page`` (int),
            and ``level`` (0 = main heading, 1 = subheading, 2 = exhibit).
        output_pdf: Destination PDF path.
        title: Heading text printed at the top of the TOC.
        case_caption: Optional case caption printed above the title.

    Returns:
        Path to the generated TOC PDF.
    """
    output_pdf = Path(output_pdf)
    output_pdf.parent.mkdir(parents=True, exist_ok=True)

    width, height = letter
    styles = getSampleStyleSheet()

    # --- custom paragraph styles for dot-leader rows -------------------
    toc_base = ParagraphStyle(
        "TOCBase",
        parent=styles["Normal"],
        fontName=_COURT_FONT,
        fontSize=_COURT_FONT_SIZE,
        leading=_COURT_LEADING,
    )
    toc_bold = ParagraphStyle(
        "TOCBold",
        parent=toc_base,
        fontName=_COURT_FONT_BOLD,
    )
    toc_sub = ParagraphStyle(
        "TOCSub",
        parent=toc_base,
        leftIndent=0.5 * inch,
    )
    toc_exhibit = ParagraphStyle(
        "TOCExhibit",
        parent=toc_base,
        leftIndent=1.0 * inch,
    )
    heading_style = ParagraphStyle(
        "TOCHeading",
        parent=styles["Normal"],
        fontName=_COURT_FONT_BOLD,
        fontSize=14,
        leading=20,
        alignment=1,  # center
        spaceAfter=12,
    )
    caption_style = ParagraphStyle(
        "TOCCaption",
        parent=styles["Normal"],
        fontName=_COURT_FONT,
        fontSize=11,
        leading=14,
        alignment=1,
        spaceAfter=6,
    )

    story: List[Any] = []

    if case_caption:
        story.append(Paragraph(case_caption.replace("\n", "<br/>"), caption_style))
        story.append(Spacer(1, 12))

    story.append(Paragraph(title, heading_style))
    story.append(Spacer(1, 6))

    # Build table rows: [title_with_dots, page_number]
    table_data: List[List[Any]] = []
    row_styles: List[Tuple[str, Tuple[int, int], Tuple[int, int], Any]] = []
    level_style_map = {0: toc_bold, 1: toc_sub, 2: toc_exhibit}

    for idx, entry in enumerate(entries):
        lvl = entry.get("level", 0)
        style = level_style_map.get(lvl, toc_base)
        entry_title = entry.get("title", "")
        page_num = entry.get("page", 0)
        dots = " . " * max(1, 30 - len(entry_title) // 2)
        cell_text = Paragraph(f"{entry_title}{dots}", style)
        page_para = Paragraph(
            str(page_num),
            ParagraphStyle("PageNum", parent=toc_base, alignment=2),
        )
        table_data.append([cell_text, page_para])

    if not table_data:
        table_data.append([Paragraph("(No entries)", toc_base), Paragraph("", toc_base)])

    col_widths = [width - 2.5 * inch, 0.75 * inch]
    toc_table = Table(table_data, colWidths=col_widths)
    toc_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ("LINEBELOW", (0, -1), (-1, -1), 0.5, black),
    ]))
    story.append(toc_table)

    def _toc_footer(canvas_obj: canvas.Canvas, doc: Any) -> None:
        canvas_obj.saveState()
        canvas_obj.setFont("Helvetica", 8)
        canvas_obj.setFillColor(Color(0.5, 0.5, 0.5))
        canvas_obj.drawCentredString(
            width / 2, 0.4 * inch, "Prepared by MBP LLC — LitigationOS",
        )
        canvas_obj.restoreState()

    doc = SimpleDocTemplate(
        str(output_pdf),
        pagesize=letter,
        leftMargin=1.0 * inch,
        rightMargin=1.0 * inch,
        topMargin=1.0 * inch,
        bottomMargin=0.75 * inch,
    )
    doc.build(story, onFirstPage=_toc_footer, onLaterPages=_toc_footer)
    logger.info("Generated TOC (%d entries) → %s", len(entries), output_pdf)
    return output_pdf


# ---------------------------------------------------------------------------
# 7. TABLE OF AUTHORITIES
# ---------------------------------------------------------------------------


_TOA_TYPE_ORDER = ["case", "statute", "rule", "other"]
_TOA_TYPE_HEADINGS = {
    "case": "Cases",
    "statute": "Statutes",
    "rule": "Court Rules",
    "other": "Other Authorities",
}


def generate_toa(
    authorities: List[Dict[str, str]],
    output_pdf: str | Path,
    title: str = "TABLE OF AUTHORITIES",
    case_caption: Optional[str] = None,
) -> Path:
    """Generate a court-formatted Table of Authorities PDF.

    Authorities are grouped by type (Cases, Statutes, Court Rules, Other)
    and sorted alphabetically within each group.  Case names are italicised
    per Bluebook convention.

    Args:
        authorities: List of dicts with keys ``citation`` (str),
            ``type`` (case | statute | rule | other), and ``pages`` (str).
        output_pdf: Destination PDF path.
        title: Heading text printed at the top.
        case_caption: Optional case caption printed above the title.

    Returns:
        Path to the generated TOA PDF.
    """
    output_pdf = Path(output_pdf)
    output_pdf.parent.mkdir(parents=True, exist_ok=True)

    width, _height = letter
    styles = getSampleStyleSheet()

    heading_style = ParagraphStyle(
        "TOAHeading",
        parent=styles["Normal"],
        fontName=_COURT_FONT_BOLD,
        fontSize=14,
        leading=20,
        alignment=1,
        spaceAfter=12,
    )
    caption_style = ParagraphStyle(
        "TOACaption",
        parent=styles["Normal"],
        fontName=_COURT_FONT,
        fontSize=11,
        leading=14,
        alignment=1,
        spaceAfter=6,
    )
    group_heading = ParagraphStyle(
        "TOAGroupHeading",
        parent=styles["Normal"],
        fontName=_COURT_FONT_BOLD,
        fontSize=_COURT_FONT_SIZE,
        leading=_COURT_LEADING,
        spaceBefore=12,
        spaceAfter=4,
        underlineWidth=0.5,
    )
    cite_style = ParagraphStyle(
        "TOACite",
        parent=styles["Normal"],
        fontName=_COURT_FONT,
        fontSize=_COURT_FONT_SIZE,
        leading=_COURT_LEADING,
        leftIndent=0.25 * inch,
    )
    cite_italic = ParagraphStyle(
        "TOACiteItalic",
        parent=cite_style,
        fontName="Times-Italic",
    )
    page_style = ParagraphStyle(
        "TOAPage",
        parent=cite_style,
        alignment=2,  # right
    )

    # Group authorities by type
    grouped: Dict[str, List[Dict[str, str]]] = {t: [] for t in _TOA_TYPE_ORDER}
    for auth in authorities:
        atype = auth.get("type", "other").lower()
        if atype not in grouped:
            atype = "other"
        grouped[atype].append(auth)

    story: List[Any] = []

    if case_caption:
        story.append(Paragraph(case_caption.replace("\n", "<br/>"), caption_style))
        story.append(Spacer(1, 12))

    story.append(Paragraph(title, heading_style))
    story.append(Spacer(1, 6))

    for atype in _TOA_TYPE_ORDER:
        items = grouped.get(atype, [])
        if not items:
            continue
        items.sort(key=lambda a: a.get("citation", "").lower())

        story.append(Paragraph(_TOA_TYPE_HEADINGS[atype], group_heading))

        table_data: List[List[Any]] = []
        for item in items:
            citation = item.get("citation", "")
            pages = item.get("pages", "")
            dots = " . " * max(1, 28 - len(citation) // 2)
            style = cite_italic if atype == "case" else cite_style
            cell = Paragraph(f"{citation}{dots}", style)
            page_cell = Paragraph(pages, page_style)
            table_data.append([cell, page_cell])

        col_widths = [width - 2.75 * inch, 1.0 * inch]
        auth_table = Table(table_data, colWidths=col_widths)
        auth_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 1),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ]))
        story.append(auth_table)

    if not any(grouped.values()):
        story.append(Paragraph("(No authorities cited)", cite_style))

    def _toa_footer(canvas_obj: canvas.Canvas, doc: Any) -> None:
        canvas_obj.saveState()
        canvas_obj.setFont("Helvetica", 8)
        canvas_obj.setFillColor(Color(0.5, 0.5, 0.5))
        canvas_obj.drawCentredString(
            width / 2, 0.4 * inch, "Prepared by MBP LLC — LitigationOS",
        )
        canvas_obj.restoreState()

    doc = SimpleDocTemplate(
        str(output_pdf),
        pagesize=letter,
        leftMargin=1.0 * inch,
        rightMargin=1.0 * inch,
        topMargin=1.0 * inch,
        bottomMargin=0.75 * inch,
    )
    doc.build(story, onFirstPage=_toa_footer, onLaterPages=_toa_footer)
    logger.info("Generated TOA (%d authorities) → %s", len(authorities), output_pdf)
    return output_pdf


# ---------------------------------------------------------------------------
# 8. PDF METADATA
# ---------------------------------------------------------------------------


def embed_pdf_metadata(
    input_pdf: str | Path,
    output_pdf: Optional[str | Path] = None,
    title: Optional[str] = None,
    author: str = "Andrew James Pigors",
    subject: Optional[str] = None,
    keywords: Optional[str] = None,
    case_number: str = "2024-001507-DC",
    court: str = "14th Circuit Court, Muskegon County, Michigan",
    creator: str = "LitigationOS by MBP LLC",
) -> Path:
    """Embed XMP / docinfo metadata into a PDF using pikepdf.

    Sets standard PDF metadata fields (Title, Author, Subject, Keywords,
    Creator, Producer, CreationDate, ModDate) plus custom litigation
    fields (CaseNumber, Court).

    Args:
        input_pdf: Source PDF.
        output_pdf: Destination PDF.  If *None*, the file is overwritten
            in-place.
        title: Document title (``/Title``).
        author: Author name (``/Author``).
        subject: Document subject (``/Subject``).
        keywords: Comma-separated keywords (``/Keywords``).
        case_number: Michigan case number stored as ``/CaseNumber``.
        court: Court name stored as ``/Court``.
        creator: Creator application name (``/Creator``).

    Returns:
        Path to the output PDF.
    """
    input_pdf = Path(input_pdf)
    if output_pdf is None:
        output_pdf = input_pdf
    else:
        output_pdf = Path(output_pdf)
    output_pdf.parent.mkdir(parents=True, exist_ok=True)

    if not input_pdf.exists():
        raise FileNotFoundError(f"PDF not found: {input_pdf}")

    overwrite = input_pdf.resolve() == output_pdf.resolve()
    pdf = pikepdf.Pdf.open(
        str(input_pdf), allow_overwriting_input=overwrite,
    )

    now_str = datetime.now().strftime("D:%Y%m%d%H%M%S")

    with pdf.open_metadata() as meta:
        if title:
            meta["dc:title"] = title
        meta["dc:creator"] = [author]
        if subject:
            meta["dc:description"] = subject
        if keywords:
            meta["pdf:Keywords"] = keywords
        meta["pdf:Producer"] = creator
        meta["xmp:CreatorTool"] = creator
        meta["xmp:ModifyDate"] = datetime.now().isoformat()

    # Also set legacy docinfo for maximum compatibility
    info = pdf.docinfo
    if title:
        info["/Title"] = title
    info["/Author"] = author
    if subject:
        info["/Subject"] = subject
    if keywords:
        info["/Keywords"] = keywords
    info["/Creator"] = creator
    info["/Producer"] = creator
    info["/CreationDate"] = now_str
    info["/ModDate"] = now_str
    # Custom litigation fields
    info["/CaseNumber"] = case_number
    info["/Court"] = court

    pdf.save(str(output_pdf))
    pdf.close()
    logger.info("Embedded metadata → %s", output_pdf)
    return output_pdf


# ---------------------------------------------------------------------------
# 9. E-FILING PREPARATION
# ---------------------------------------------------------------------------


def prepare_for_efiling(
    input_pdf: str | Path,
    output_pdf: str | Path,
    max_file_size_mb: float = 25.0,
    naming_convention: str = "mifile",
    case_number: str = "2024-001507-DC",
    document_type: str = "Motion",
    filing_date: Optional[str] = None,
) -> Dict[str, Any]:
    """Prepare a PDF for Michigan e-filing (MiFILE).

    Validates size, text-searchability, and page count, then renames the
    file per MiFILE naming convention and embeds standard metadata.

    Args:
        input_pdf: Source PDF to prepare.
        output_pdf: Destination directory **or** file path.
        max_file_size_mb: Maximum allowed file size (MiFILE default 25 MB).
        naming_convention: Naming scheme (currently only ``"mifile"``).
        case_number: Michigan case number used in the filename.
        document_type: Document type label (e.g. ``"Motion"``,
            ``"Brief"``, ``"Exhibit"``).
        filing_date: Filing date as ``YYYY-MM-DD``.  Defaults to today.

    Returns:
        Dict with keys ``output``, ``file_size_mb``, ``page_count``,
        ``is_text_searchable``, ``warnings``, and ``compliant``.
    """
    input_pdf = Path(input_pdf)
    output_pdf = Path(output_pdf)

    if not input_pdf.exists():
        raise FileNotFoundError(f"PDF not found: {input_pdf}")

    warnings: List[str] = []

    # --- resolve filing date -----------------------------------------------
    if filing_date is None:
        filing_date = datetime.now().strftime("%Y-%m-%d")
    date_clean = filing_date.replace("-", "")

    # --- build MiFILE-compliant filename -----------------------------------
    case_clean = re.sub(r"[^A-Za-z0-9]", "", case_number)
    doc_clean = re.sub(r"[^A-Za-z0-9]", "", document_type)
    efile_name = f"{case_clean}_{doc_clean}_{date_clean}.pdf"

    if output_pdf.is_dir() or not str(output_pdf).lower().endswith(".pdf"):
        output_pdf.mkdir(parents=True, exist_ok=True)
        final_path = output_pdf / efile_name
    else:
        output_pdf.parent.mkdir(parents=True, exist_ok=True)
        final_path = output_pdf

    # --- file size check ---------------------------------------------------
    file_size_bytes = input_pdf.stat().st_size
    file_size_mb = round(file_size_bytes / (1024 * 1024), 2)
    if file_size_mb > max_file_size_mb:
        warnings.append(
            f"File size {file_size_mb} MB exceeds {max_file_size_mb} MB limit"
        )

    # --- page count & text-searchability -----------------------------------
    page_count = 0
    is_text_searchable = False
    try:
        reader_pdf = pikepdf.Pdf.open(str(input_pdf))
        page_count = len(reader_pdf.pages)
        # Check text on first page
        if page_count > 0:
            first_page = reader_pdf.pages[0]
            try:
                content = first_page.get("/Contents")
                if content is not None:
                    raw = content.read_bytes() if hasattr(content, "read_bytes") else b""
                    # Text operators in PDF content streams
                    if any(op in raw for op in [b"Tj", b"TJ", b"Tf"]):
                        is_text_searchable = True
            except Exception:
                pass
        reader_pdf.close()
    except Exception as exc:
        warnings.append(f"Could not read PDF structure: {exc}")

    if not is_text_searchable:
        warnings.append("PDF may not be text-searchable (image-only); consider OCR")

    # --- embed metadata & copy to final path --------------------------------
    import shutil
    shutil.copy2(str(input_pdf), str(final_path))
    embed_pdf_metadata(
        final_path,
        title=f"{document_type} — {case_number}",
        case_number=case_number,
        subject=document_type,
        keywords=f"{document_type}, {case_number}, Michigan, e-filing",
    )

    # --- add bookmarks if multi-section ------------------------------------
    if page_count > 1:
        try:
            pdf = pikepdf.Pdf.open(str(final_path))
            with pdf.open_outline() as outline:
                if len(outline.root) == 0:
                    outline.root.append(
                        pikepdf.OutlineItem(document_type, 0)
                    )
            pdf.save(str(final_path))
            pdf.close()
        except Exception as exc:
            warnings.append(f"Could not add bookmarks: {exc}")

    compliant = len(warnings) == 0 or all(
        "text-searchable" in w for w in warnings
    )

    result = {
        "output": str(final_path),
        "file_size_mb": file_size_mb,
        "page_count": page_count,
        "is_text_searchable": is_text_searchable,
        "warnings": warnings,
        "compliant": compliant,
    }
    logger.info(
        "E-filing prep: %d pages, %.2f MB, searchable=%s, compliant=%s → %s",
        page_count, file_size_mb, is_text_searchable, compliant, final_path,
    )
    return result
