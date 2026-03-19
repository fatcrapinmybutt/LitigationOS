"""
Generate court-ready PDFs from McNeill Disqualification markdown files.
Uses reportlab with Times New Roman, 12pt, 1" margins, double-spaced.
"""
import sys, os, re, io
sys.stdout.reconfigure(encoding='utf-8')

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak,
    Table, TableStyle, HRFlowable
)
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Register Times New Roman if available, fallback to Times-Roman (built-in)
FONT_NAME = 'Times-Roman'
FONT_BOLD = 'Times-Bold'
FONT_ITALIC = 'Times-Italic'

try:
    tnr_path = r'C:\Windows\Fonts\times.ttf'
    tnr_bold = r'C:\Windows\Fonts\timesbd.ttf'
    tnr_italic = r'C:\Windows\Fonts\timesi.ttf'
    if os.path.exists(tnr_path):
        pdfmetrics.registerFont(TTFont('TimesNewRoman', tnr_path))
        pdfmetrics.registerFont(TTFont('TimesNewRoman-Bold', tnr_bold))
        pdfmetrics.registerFont(TTFont('TimesNewRoman-Italic', tnr_italic))
        FONT_NAME = 'TimesNewRoman'
        FONT_BOLD = 'TimesNewRoman-Bold'
        FONT_ITALIC = 'TimesNewRoman-Italic'
        print("  Using Times New Roman TTF")
except Exception as e:
    print(f"  Using built-in Times-Roman (TNR load failed: {e})")

PAGE_W, PAGE_H = letter
MARGIN = 1 * inch
FONT_SIZE = 12
LEADING = FONT_SIZE * 2  # double-spaced


def build_styles():
    """Create court-document paragraph styles."""
    styles = {}
    styles['Normal'] = ParagraphStyle(
        'Normal', fontName=FONT_NAME, fontSize=FONT_SIZE,
        leading=LEADING, alignment=TA_JUSTIFY,
        spaceAfter=6, spaceBefore=0
    )
    styles['Center'] = ParagraphStyle(
        'Center', parent=styles['Normal'], alignment=TA_CENTER,
        leading=FONT_SIZE * 1.4
    )
    styles['Heading1'] = ParagraphStyle(
        'H1', fontName=FONT_BOLD, fontSize=14,
        leading=14 * 2, alignment=TA_CENTER,
        spaceAfter=12, spaceBefore=18,
        textColor=colors.black
    )
    styles['Heading2'] = ParagraphStyle(
        'H2', fontName=FONT_BOLD, fontSize=FONT_SIZE,
        leading=LEADING, alignment=TA_LEFT,
        spaceAfter=6, spaceBefore=14,
        underline=True
    )
    styles['Heading3'] = ParagraphStyle(
        'H3', fontName=FONT_BOLD, fontSize=FONT_SIZE,
        leading=LEADING, alignment=TA_LEFT,
        spaceAfter=4, spaceBefore=10
    )
    styles['CaseHeader'] = ParagraphStyle(
        'CaseHeader', fontName=FONT_NAME, fontSize=FONT_SIZE,
        leading=FONT_SIZE * 1.5, alignment=TA_CENTER,
        spaceAfter=2, spaceBefore=2
    )
    styles['Indented'] = ParagraphStyle(
        'Indented', parent=styles['Normal'],
        leftIndent=0.5 * inch, rightIndent=0.5 * inch,
        fontSize=11, leading=11 * 1.8
    )
    return styles


def add_page_number(canvas_obj, doc):
    """Add page number footer."""
    canvas_obj.saveState()
    canvas_obj.setFont(FONT_NAME, 10)
    page_num = canvas_obj.getPageNumber()
    text = f"Page {page_num}"
    canvas_obj.drawCentredString(PAGE_W / 2, 0.5 * inch, text)
    canvas_obj.restoreState()


def md_to_elements(md_text, styles):
    """Convert markdown text to reportlab flowable elements."""
    elements = []
    lines = md_text.split('\n')
    i = 0
    in_case_header = False
    header_lines = []

    while i < len(lines):
        line = lines[i].rstrip()

        # Skip blank lines
        if not line.strip():
            if in_case_header and header_lines:
                # Flush case header block
                for hl in header_lines:
                    elements.append(Paragraph(escape_html(hl), styles['CaseHeader']))
                header_lines = []
                in_case_header = False
            i += 1
            continue

        # Horizontal rule
        if line.strip() in ('---', '___', '***'):
            if in_case_header and header_lines:
                for hl in header_lines:
                    elements.append(Paragraph(escape_html(hl), styles['CaseHeader']))
                header_lines = []
            elements.append(HRFlowable(width="100%", thickness=1, color=colors.black,
                                        spaceAfter=6, spaceBefore=6))
            in_case_header = False
            i += 1
            continue

        # Headings
        if line.startswith('# '):
            in_case_header = False
            text = format_inline(line[2:].strip())
            elements.append(Paragraph(text, styles['Heading1']))
            # Check if next lines are case header (STATE OF MICHIGAN etc.)
            if i + 1 < len(lines) and 'STATE OF MICHIGAN' in lines[min(i+1, len(lines)-1)].upper():
                in_case_header = True
            i += 1
            continue

        if line.startswith('## '):
            in_case_header = False
            text = format_inline(line[3:].strip())
            elements.append(Paragraph(text, styles['Heading2']))
            i += 1
            continue

        if line.startswith('### '):
            in_case_header = False
            text = format_inline(line[4:].strip())
            elements.append(Paragraph(text, styles['Heading3']))
            i += 1
            continue

        # Case header detection (centered court info at top)
        if in_case_header or (i < 20 and line.strip().startswith('STATE OF MICHIGAN')):
            in_case_header = True
            header_lines.append(line)
            i += 1
            continue

        # Detect case caption block (party names, case number)
        upper_line = line.strip().upper()
        if i < 30 and any(k in upper_line for k in ['PLAINTIFF', 'DEFENDANT', 'CASE NO', 'HON.']):
            elements.append(Paragraph(escape_html(line), styles['CaseHeader']))
            i += 1
            continue

        if i < 30 and line.strip().startswith('v.'):
            elements.append(Paragraph(escape_html(line), styles['CaseHeader']))
            i += 1
            continue

        if i < 35 and line.strip().startswith('____'):
            elements.append(Paragraph(escape_html(line), styles['CaseHeader']))
            i += 1
            continue

        # Numbered paragraphs and regular text
        text = format_inline(line)
        elements.append(Paragraph(text, styles['Normal']))
        i += 1

    # Flush any remaining header
    if header_lines:
        for hl in header_lines:
            elements.append(Paragraph(escape_html(hl), styles['CaseHeader']))

    return elements


def escape_html(text):
    """Escape HTML entities for reportlab."""
    return (text
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;'))


def format_inline(text):
    """Convert markdown inline formatting to reportlab XML."""
    # Escape HTML first
    text = escape_html(text)

    # Bold+italic ***text*** or ___text___
    text = re.sub(r'\*\*\*(.+?)\*\*\*', r'<b><i>\1</i></b>', text)

    # Bold **text**
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)

    # Italic *text* (but not already processed bold)
    text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<i>\1</i>', text)

    # Underline (markdown doesn't have native, but handle if present)
    text = re.sub(r'__(.+?)__', r'<u>\1</u>', text)

    return text


def convert_md_to_pdf(md_path, pdf_path, styles):
    """Convert a single markdown file to a court-ready PDF."""
    with open(md_path, 'r', encoding='utf-8') as f:
        md_text = f.read()

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN,
        title=os.path.basename(md_path).replace('.md', '').replace('_', ' '),
        author='Andrew J. Pigors'
    )

    elements = md_to_elements(md_text, styles)

    if not elements:
        elements.append(Paragraph("(Document empty)", styles['Normal']))

    doc.build(elements, onFirstPage=add_page_number, onLaterPages=add_page_number)


def combine_pdfs(pdf_paths, output_path):
    """Combine multiple PDFs into one filing package."""
    try:
        from PyPDF2 import PdfMerger
        merger = PdfMerger()
        for p in pdf_paths:
            if os.path.exists(p):
                merger.append(p)
        merger.write(output_path)
        merger.close()
        return True
    except ImportError:
        try:
            from PyPDF2 import PdfFileMerger
            merger = PdfFileMerger()
            for p in pdf_paths:
                if os.path.exists(p):
                    merger.append(p)
            merger.write(output_path)
            merger.close()
            return True
        except ImportError:
            print("  PyPDF2 not available — skipping combined PDF")
            return False


def main():
    pkg_dir = r'C:\Users\andre\LitigationOS\02_TRIAL_14TH\FULL_14TH_STACK\DISQUALIFY_PACKAGE'
    pdf_dir = os.path.join(pkg_dir, 'PDF_OUTPUT')
    os.makedirs(pdf_dir, exist_ok=True)

    styles = build_styles()

    # Filing order for combined package
    filing_order = [
        'MOTION_TO_DISQUALIFY_FINAL.md',
        'BRIEF_IN_SUPPORT.md',
        'EXHIBIT_LIST.md',
        'PROPOSED_ORDER.md',
        'CERTIFICATE_OF_SERVICE.md',
        'FILING_CHECKLIST.md',
    ]

    md_files = [f for f in os.listdir(pkg_dir) if f.endswith('.md')]
    # Add any .md files not in filing_order
    for f in sorted(md_files):
        if f not in filing_order:
            filing_order.append(f)

    generated_pdfs = []
    print(f'\nGenerating court-ready PDFs in: {pdf_dir}\n')

    for md_name in filing_order:
        md_path = os.path.join(pkg_dir, md_name)
        if not os.path.exists(md_path):
            continue

        pdf_name = md_name.replace('.md', '.pdf')
        pdf_path = os.path.join(pdf_dir, pdf_name)

        try:
            convert_md_to_pdf(md_path, pdf_path, styles)
            sz = os.path.getsize(pdf_path)
            print(f'  OK: {pdf_name} ({sz/1024:.1f} KB)')
            generated_pdfs.append(pdf_path)
        except Exception as e:
            print(f'  FAIL: {pdf_name}: {e}')

    # Generate combined filing package
    if generated_pdfs:
        combined_path = os.path.join(pdf_dir, 'COMBINED_FILING_PACKAGE.pdf')
        print(f'\nBuilding combined filing package...')
        if combine_pdfs(generated_pdfs, combined_path):
            sz = os.path.getsize(combined_path)
            print(f'  OK: COMBINED_FILING_PACKAGE.pdf ({sz/1024:.1f} KB)')
        else:
            print('  Combined PDF skipped (no merger available)')

    print(f'\nTotal PDFs generated: {len(generated_pdfs)}')
    print(f'Output directory: {pdf_dir}')


if __name__ == '__main__':
    main()
