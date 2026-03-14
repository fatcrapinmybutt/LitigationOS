"""
LitigationOS Court PDF Generator
Converts clerk-ready markdown filings to court-formatted PDFs.

Court formatting: 1" margins, 12pt Times New Roman, double-spaced body,
page numbers, case caption on each page.

Usage:
    python court_pdf_generator.py <input.md> [--output <output.pdf>]
    python court_pdf_generator.py --all  # Convert all CLERK_READY filings
"""
import sys
import os
import re
import argparse
from pathlib import Path

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle,
    KeepTogether, HRFlowable
)
from reportlab.lib import colors

# ─── CONSTANTS ────────────────────────────────────────────────────────────
REPO_ROOT = Path(r"C:\Users\andre\LitigationOS")
CLERK_READY = REPO_ROOT / "01_FILINGS" / "CLERK_READY"
OUTPUT_DIR = REPO_ROOT / "01_FILINGS" / "PDF_READY"

MARGINS = {
    'leftMargin': 1 * inch,
    'rightMargin': 1 * inch,
    'topMargin': 1 * inch,
    'bottomMargin': 1 * inch,
}

CASE_INFO = {
    'court': 'STATE OF MICHIGAN\nIN THE CIRCUIT COURT FOR THE COUNTY OF MUSKEGON\nFAMILY DIVISION',
    'case_no': 'Case No. 2024-001507-DC',
    'judge': 'Hon. Jenny L. McNeill',
    'plaintiff': 'ANDREW JAMES PIGORS,\n     Plaintiff/Father,',
    'defendant': 'EMILY A. WATSON,\n     Defendant/Mother.',
}

PPO_CASE_INFO = {
    'court': 'STATE OF MICHIGAN\nIN THE CIRCUIT COURT FOR THE COUNTY OF MUSKEGON',
    'case_no': 'Case No. 2023-5907-PP',
    'judge': 'Hon. Jenny L. McNeill',
    'plaintiff': 'EMILY A. WATSON,\n     Petitioner,',
    'defendant': 'ANDREW JAMES PIGORS,\n     Respondent.',
}


# ─── STYLES ───────────────────────────────────────────────────────────────
def build_styles():
    """Build court-compliant paragraph styles."""
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        'CourtTitle',
        parent=styles['Title'],
        fontName='Times-Bold',
        fontSize=14,
        leading=18,
        alignment=TA_CENTER,
        spaceAfter=12,
    ))

    styles.add(ParagraphStyle(
        'CourtHeading',
        parent=styles['Heading1'],
        fontName='Times-Bold',
        fontSize=12,
        leading=24,  # double-spaced
        alignment=TA_LEFT,
        spaceBefore=12,
        spaceAfter=6,
        textTransform='uppercase',
    ))

    styles.add(ParagraphStyle(
        'CourtSubHeading',
        parent=styles['Heading2'],
        fontName='Times-Bold',
        fontSize=12,
        leading=24,
        alignment=TA_LEFT,
        spaceBefore=8,
        spaceAfter=4,
    ))

    styles.add(ParagraphStyle(
        'CourtBody',
        parent=styles['Normal'],
        fontName='Times-Roman',
        fontSize=12,
        leading=24,  # double-spaced
        alignment=TA_JUSTIFY,
        firstLineIndent=0.5 * inch,
        spaceBefore=0,
        spaceAfter=0,
    ))

    styles.add(ParagraphStyle(
        'CourtBodyNoIndent',
        parent=styles['Normal'],
        fontName='Times-Roman',
        fontSize=12,
        leading=24,
        alignment=TA_JUSTIFY,
        firstLineIndent=0,
        spaceBefore=0,
        spaceAfter=0,
    ))

    styles.add(ParagraphStyle(
        'CourtNumbered',
        parent=styles['Normal'],
        fontName='Times-Roman',
        fontSize=12,
        leading=24,
        alignment=TA_JUSTIFY,
        leftIndent=0.5 * inch,
        firstLineIndent=-0.5 * inch,
        spaceBefore=0,
        spaceAfter=0,
    ))

    styles.add(ParagraphStyle(
        'CourtCaption',
        parent=styles['Normal'],
        fontName='Times-Roman',
        fontSize=12,
        leading=14,
        alignment=TA_CENTER,
        spaceBefore=0,
        spaceAfter=0,
    ))

    styles.add(ParagraphStyle(
        'CourtCaptionBold',
        parent=styles['Normal'],
        fontName='Times-Bold',
        fontSize=12,
        leading=14,
        alignment=TA_CENTER,
        spaceBefore=0,
        spaceAfter=0,
    ))

    styles.add(ParagraphStyle(
        'CourtSignature',
        parent=styles['Normal'],
        fontName='Times-Roman',
        fontSize=12,
        leading=18,
        alignment=TA_LEFT,
        leftIndent=3.5 * inch,
        spaceBefore=24,
        spaceAfter=0,
    ))

    styles.add(ParagraphStyle(
        'CourtFooter',
        parent=styles['Normal'],
        fontName='Times-Roman',
        fontSize=10,
        leading=12,
        alignment=TA_CENTER,
    ))

    styles.add(ParagraphStyle(
        'CourtBlockQuote',
        parent=styles['Normal'],
        fontName='Times-Italic',
        fontSize=11,
        leading=20,
        alignment=TA_JUSTIFY,
        leftIndent=1 * inch,
        rightIndent=1 * inch,
        spaceBefore=6,
        spaceAfter=6,
    ))

    return styles


# ─── MARKDOWN PARSER ──────────────────────────────────────────────────────
class MarkdownToCourtPDF:
    """Converts a clerk-ready markdown filing to court-formatted PDF."""

    def __init__(self, md_path: Path, output_path: Path = None, case_info: dict = None):
        self.md_path = Path(md_path)
        self.output_path = output_path or (OUTPUT_DIR / self.md_path.with_suffix('.pdf').name)
        self.case_info = case_info or CASE_INFO
        self.styles = build_styles()
        self.story = []
        self.page_count = 0

    def _detect_case_info(self, text: str) -> dict:
        """Auto-detect which case caption to use based on content."""
        if '2023-5907-PP' in text or 'PPO' in text.upper()[:500]:
            return PPO_CASE_INFO
        return CASE_INFO

    def _add_caption(self):
        """Add the court caption block."""
        s = self.styles

        # Court name
        for line in self.case_info['court'].split('\n'):
            self.story.append(Paragraph(line, s['CourtCaption']))
        self.story.append(Spacer(1, 18))

        # Parties and case number in a table layout
        party_left = self.case_info['plaintiff'] + '\n\nv.\n\n' + self.case_info['defendant']
        party_left_paras = []
        for line in party_left.split('\n'):
            if line.strip():
                party_left_paras.append(Paragraph(line, s['CourtBodyNoIndent']))
            else:
                party_left_paras.append(Spacer(1, 6))

        case_right = [
            Paragraph(self.case_info['case_no'], s['CourtCaptionBold']),
            Spacer(1, 6),
            Paragraph(self.case_info['judge'], s['CourtCaption']),
        ]

        # Simple centered layout
        self.story.append(Paragraph(
            f"<b>{self.case_info['case_no']}</b>",
            s['CourtCaptionBold']
        ))
        self.story.append(Paragraph(self.case_info['judge'], s['CourtCaption']))
        self.story.append(Spacer(1, 12))

        for line in self.case_info['plaintiff'].split('\n'):
            self.story.append(Paragraph(line.strip(), s['CourtBodyNoIndent']))
        self.story.append(Spacer(1, 6))
        self.story.append(Paragraph('v.', s['CourtCaption']))
        self.story.append(Spacer(1, 6))
        for line in self.case_info['defendant'].split('\n'):
            self.story.append(Paragraph(line.strip(), s['CourtBodyNoIndent']))

        self.story.append(Spacer(1, 6))
        self.story.append(HRFlowable(width="100%", thickness=1, color=colors.black))
        self.story.append(Spacer(1, 12))

    def _clean_markdown(self, text: str) -> str:
        """Remove markdown artifacts that don't translate to PDF."""
        # Remove YAML front matter
        text = re.sub(r'^---\n.*?\n---\n', '', text, flags=re.DOTALL)
        # Remove HTML comments
        text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
        # Remove emoji
        text = re.sub(r'[🔴🟡🟢✅❌⚠️📋📁📄🔥💰⚡🎯🗄️🔗🤖🔒🌐📝📊🔄💡]', '', text)
        return text

    def _escape_xml(self, text: str) -> str:
        """Escape XML special characters for ReportLab paragraphs."""
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        return text

    def _apply_inline_formatting(self, text: str) -> str:
        """Convert markdown inline formatting to ReportLab XML.
        
        Order matters: code spans first (to protect their content),
        then bold+italic, bold, italic. Avoids nesting collisions.
        """
        # Code spans first — replace with placeholder to prevent bold/italic inside
        code_spans = []
        def _save_code(m):
            code_spans.append(m.group(1))
            return f'__CODE{len(code_spans)-1}__'
        text = re.sub(r'`(.+?)`', _save_code, text)
        
        # Bold+italic: ***text***
        text = re.sub(r'\*\*\*(.+?)\*\*\*', r'<b><i>\1</i></b>', text)
        # Bold: **text**
        text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
        # Italic: *text* (not inside bold)
        text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<i>\1</i>', text)
        
        # Restore code spans
        for i, code in enumerate(code_spans):
            text = text.replace(f'__CODE{i}__', f'<font face="Courier" size="10">{code}</font>')
        
        return text

    def _parse_line(self, line: str, in_blockquote: bool = False) -> tuple:
        """Parse a single markdown line and return (style_name, text, special_type)."""
        stripped = line.strip()

        if not stripped:
            return (None, None, 'blank')

        # Headers
        if stripped.startswith('# '):
            return ('CourtTitle', stripped[2:], 'title')
        if stripped.startswith('## '):
            return ('CourtHeading', stripped[3:], 'heading')
        if stripped.startswith('### '):
            return ('CourtSubHeading', stripped[4:], 'subheading')
        if stripped.startswith('#### '):
            return ('CourtSubHeading', stripped[5:], 'subheading')

        # Horizontal rule
        if stripped in ('---', '***', '___'):
            return (None, None, 'hr')

        # Blockquote
        if stripped.startswith('> '):
            return ('CourtBlockQuote', stripped[2:], 'blockquote')

        # Numbered list (court paragraph numbering)
        num_match = re.match(r'^(\d+)\.\s+(.+)', stripped)
        if num_match:
            num, text = num_match.groups()
            return ('CourtNumbered', f'{num}. {text}', 'numbered')

        # Bullet list
        bullet_match = re.match(r'^[-*+]\s+(.+)', stripped)
        if bullet_match:
            return ('CourtNumbered', f'• {bullet_match.group(1)}', 'bullet')

        # Table detection
        if '|' in stripped and stripped.startswith('|'):
            return (None, stripped, 'table_row')

        # Regular paragraph
        return ('CourtBody', stripped, 'paragraph')

    def _parse_table(self, rows: list) -> list:
        """Parse markdown table rows into ReportLab Table."""
        if len(rows) < 2:
            return []

        # Parse header
        header = [cell.strip() for cell in rows[0].split('|')[1:-1]]

        # Skip separator row (|---|---|)
        data_rows = []
        for row in rows[2:]:  # skip header + separator
            cells = [cell.strip() for cell in row.split('|')[1:-1]]
            if cells:
                data_rows.append(cells)

        if not header or not data_rows:
            return []

        # Build table
        all_rows = [header] + data_rows

        # Detect if any cell is very long (>200 chars) — use smaller font
        max_cell_len = max(len(c) for row in all_rows for c in row)
        font_size = 8 if max_cell_len > 200 else (9 if max_cell_len > 100 else 10)
        leading = font_size + 2

        # Convert to Paragraphs with word-wrap
        table_data = []
        for i, row in enumerate(all_rows):
            para_row = []
            for cell in row:
                # Truncate extremely long cells to prevent page overflow
                cell_text = cell[:500] + '...' if len(cell) > 500 else cell
                cell_escaped = self._escape_xml(cell_text)
                cell_formatted = self._apply_inline_formatting(cell_escaped)
                style = ParagraphStyle(
                    'TableCell',
                    fontName='Times-Bold' if i == 0 else 'Times-Roman',
                    fontSize=font_size,
                    leading=leading,
                    alignment=TA_LEFT,
                    wordWrap='CJK',  # aggressive word-wrapping
                )
                para_row.append(Paragraph(cell_formatted, style))
            table_data.append(para_row)

        if not table_data:
            return []

        col_count = len(header)
        avail_width = letter[0] - 2 * inch
        col_width = avail_width / col_count

        t = Table(table_data, colWidths=[col_width] * col_count, repeatRows=1)
        t.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), font_size),
            ('LEADING', (0, 0), (-1, -1), leading),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.9, 0.9, 0.9)),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))
        t.splitInRow = True  # Allow row splitting across pages

        return [Spacer(1, 6), t, Spacer(1, 6)]

    def _add_page_number(self, canvas, doc):
        """Add page number footer to each page."""
        canvas.saveState()
        canvas.setFont('Times-Roman', 10)
        page_num = canvas.getPageNumber()
        text = f"Page {page_num}"
        canvas.drawCentredString(letter[0] / 2.0, 0.5 * inch, text)
        canvas.restoreState()

    def convert(self):
        """Main conversion: markdown file → court-formatted PDF."""
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        # Read markdown
        text = self.md_path.read_text(encoding='utf-8', errors='replace')
        text = self._clean_markdown(text)
        self.case_info = self._detect_case_info(text)

        lines = text.split('\n')
        self.story = []

        # Caption
        self._add_caption()

        # Track state
        table_buffer = []
        in_table = False
        skip_caption_section = False

        for line in lines:
            style_name, content, special = self._parse_line(line)

            # Skip lines that are part of the markdown caption
            # (we already added our formatted caption)
            if content and any(marker in str(content) for marker in [
                'STATE OF MICHIGAN', 'CIRCUIT COURT', 'Case No.',
                'Plaintiff', 'Defendant', 'Petitioner', 'Respondent',
                'v.', '/Father', '/Mother'
            ]):
                continue

            # Table handling
            if special == 'table_row':
                table_buffer.append(content)
                in_table = True
                continue
            elif in_table:
                # End of table
                elements = self._parse_table(table_buffer)
                self.story.extend(elements)
                table_buffer = []
                in_table = False

            if special == 'blank':
                self.story.append(Spacer(1, 12))
                continue

            if special == 'hr':
                self.story.append(HRFlowable(width="100%", thickness=1, color=colors.black))
                self.story.append(Spacer(1, 6))
                continue

            if content is None:
                continue

            # Escape and format
            escaped = self._escape_xml(content)
            formatted = self._apply_inline_formatting(escaped)

            style = self.styles[style_name]
            try:
                self.story.append(Paragraph(formatted, style))
            except Exception:
                # Fallback: strip all XML tags and render as plain text
                plain = re.sub(r'<[^>]+>', '', formatted)
                self.story.append(Paragraph(plain, style))

        # Flush remaining table
        if table_buffer:
            elements = self._parse_table(table_buffer)
            self.story.extend(elements)

        # Build PDF
        doc = SimpleDocTemplate(
            str(self.output_path),
            pagesize=letter,
            **MARGINS,
        )
        doc.build(self.story, onFirstPage=self._add_page_number, onLaterPages=self._add_page_number)
        return self.output_path


def convert_all_clerk_ready():
    """Convert all markdown filings in CLERK_READY to PDF."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    results = []

    md_files = sorted(CLERK_READY.glob('*.md'))
    for md_file in md_files:
        if md_file.name == 'QA_REPORT.md':
            continue  # Skip QA report — not a filing

        print(f"Converting: {md_file.name}")
        try:
            converter = MarkdownToCourtPDF(md_file)
            output = converter.convert()
            size_kb = output.stat().st_size / 1024
            results.append((md_file.name, output.name, size_kb, 'OK'))
            print(f"  → {output.name} ({size_kb:.1f} KB)")
        except Exception as e:
            results.append((md_file.name, 'FAILED', 0, str(e)))
            print(f"  → FAILED: {e}")

    print(f"\n{'='*60}")
    print(f"Converted {sum(1 for r in results if r[3] == 'OK')}/{len(results)} filings")
    for name, out, size, status in results:
        print(f"  {name} → {out} ({size:.1f} KB) [{status}]")

    return results


def main():
    parser = argparse.ArgumentParser(description='Convert clerk-ready markdown to court PDF')
    parser.add_argument('input', nargs='?', help='Input markdown file path')
    parser.add_argument('--output', '-o', help='Output PDF path')
    parser.add_argument('--all', action='store_true', help='Convert all CLERK_READY filings')
    args = parser.parse_args()

    if args.all:
        convert_all_clerk_ready()
    elif args.input:
        md_path = Path(args.input)
        output_path = Path(args.output) if args.output else None
        converter = MarkdownToCourtPDF(md_path, output_path)
        result = converter.convert()
        print(f"Generated: {result} ({result.stat().st_size / 1024:.1f} KB)")
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
