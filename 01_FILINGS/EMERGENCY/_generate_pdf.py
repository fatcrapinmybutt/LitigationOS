"""
Generate court-formatted PDF of the complete emergency filing package.
Times-Roman 12pt, double-spaced, 1-inch margins, page numbers.
"""
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY, TA_RIGHT
    from reportlab.lib import colors
except ImportError:
    print("Installing reportlab...")
    os.system("pip install reportlab")
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY, TA_RIGHT
    from reportlab.lib import colors


BASE = r"C:\Users\andre\LitigationOS\06_EMERGENCY\FINAL_EMERGENCY_PACKAGE"
OUTPUT = os.path.join(BASE, "EMERGENCY_FILING_PACKAGE.pdf")

FILES = [
    ("A_EMERGENCY_MOTION_RESTORE_PARENTING_TIME.md", "EMERGENCY MOTION TO RESTORE PARENTING TIME"),
    ("B_VERIFIED_AFFIDAVIT.md", "VERIFIED AFFIDAVIT OF ANDREW J. PIGORS"),
    ("C_BRIEF_IN_SUPPORT.md", "BRIEF IN SUPPORT OF EMERGENCY MOTION"),
    ("D_PROPOSED_ORDER.md", "PROPOSED ORDER"),
    ("E_CERTIFICATE_OF_SERVICE.md", "CERTIFICATE OF SERVICE"),
    ("F_FEE_WAIVER_MC20.md", "FEE WAIVER REQUEST (MC 20)"),
]


def sanitize(text):
    """Replace special characters with ASCII equivalents."""
    replacements = {
        '\u2014': '--',
        '\u2013': '-',
        '\u2018': "'",
        '\u2019': "'",
        '\u201c': '"',
        '\u201d': '"',
        '\u2026': '...',
        '\u00a7': 'Sec.',
        '\u00b6': 'P',
        '\u2022': '*',
        '\u25cf': '*',
        '\u2713': '[X]',
        '\u2717': '[ ]',
        '\u2610': '[ ]',
        '\u2611': '[X]',
        '\ud83d\uded1': '[!]',
        '\ud83d\udcc4': '[DOC]',
        '\ud83d\udcc5': '[DATE]',
        '\ud83d\udd0d': '[SEARCH]',
        '\u2705': '[OK]',
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    # Remove any remaining non-ASCII
    cleaned = []
    for ch in text:
        if ord(ch) < 128:
            cleaned.append(ch)
        elif ord(ch) < 256:
            cleaned.append(ch)
        else:
            cleaned.append(' ')
    return ''.join(cleaned)


def read_md(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()


def escape_xml(text):
    """Escape XML special characters for ReportLab paragraphs."""
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    return text


def add_page_number(canvas, doc):
    """Add page number to bottom center of each page."""
    canvas.saveState()
    canvas.setFont('Times-Roman', 10)
    page_num = canvas.getPageNumber()
    text = f"Page {page_num}"
    canvas.drawCentredString(4.25 * inch, 0.5 * inch, text)
    canvas.restoreState()


def md_to_flowables(md_text, styles):
    """Convert markdown text to ReportLab flowables."""
    flowables = []
    lines = md_text.split('\n')
    
    i = 0
    in_table = False
    table_rows = []
    
    while i < len(lines):
        line = lines[i].rstrip()
        
        # Skip horizontal rules
        if line.strip() == '---' or line.strip() == '___':
            flowables.append(Spacer(1, 6))
            i += 1
            continue
        
        # Skip empty lines
        if not line.strip():
            flowables.append(Spacer(1, 6))
            i += 1
            continue
        
        # Handle tables
        if '|' in line and line.strip().startswith('|'):
            if not in_table:
                in_table = True
                table_rows = []
            
            cells = [c.strip() for c in line.split('|')]
            cells = [c for c in cells if c]  # Remove empty from split
            
            # Skip separator rows (|---|---|)
            if cells and all(set(c.strip()).issubset({'-', ':', ' '}) for c in cells):
                i += 1
                continue
            
            table_rows.append(cells)
            i += 1
            
            # Check if next line is still table
            if i < len(lines) and '|' in lines[i] and lines[i].strip().startswith('|'):
                continue
            else:
                # End of table, render it
                in_table = False
                if table_rows:
                    # Sanitize and escape all cells
                    clean_rows = []
                    for row in table_rows:
                        clean_row = []
                        for cell in row:
                            cell_text = sanitize(cell)
                            cell_text = cell_text.replace('**', '')
                            clean_row.append(Paragraph(escape_xml(cell_text), styles['TableCell']))
                        clean_rows.append(clean_row)
                    
                    if clean_rows:
                        # Normalize column count
                        max_cols = max(len(r) for r in clean_rows)
                        for row in clean_rows:
                            while len(row) < max_cols:
                                row.append(Paragraph('', styles['TableCell']))
                        
                        col_width = (6.5 * inch) / max_cols
                        t = Table(clean_rows, colWidths=[col_width] * max_cols)
                        t.setStyle(TableStyle([
                            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                            ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.9, 0.9, 0.9)),
                            ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
                            ('FONTNAME', (0, 1), (-1, -1), 'Times-Roman'),
                            ('FONTSIZE', (0, 0), (-1, -1), 10),
                            ('TOPPADDING', (0, 0), (-1, -1), 4),
                            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                            ('LEFTPADDING', (0, 0), (-1, -1), 4),
                            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ]))
                        flowables.append(Spacer(1, 6))
                        flowables.append(t)
                        flowables.append(Spacer(1, 6))
                    table_rows = []
                continue
        
        # Clean the line
        raw = sanitize(line)
        
        # Headers
        if raw.startswith('######'):
            text = raw[6:].strip().replace('**', '')
            flowables.append(Spacer(1, 4))
            flowables.append(Paragraph(escape_xml(text), styles['Heading6']))
            i += 1
            continue
        elif raw.startswith('#####'):
            text = raw[5:].strip().replace('**', '')
            flowables.append(Spacer(1, 4))
            flowables.append(Paragraph(escape_xml(text), styles['Heading5']))
            i += 1
            continue
        elif raw.startswith('####'):
            text = raw[4:].strip().replace('**', '')
            flowables.append(Spacer(1, 6))
            flowables.append(Paragraph(escape_xml(text), styles['Heading4']))
            i += 1
            continue
        elif raw.startswith('###'):
            text = raw[3:].strip().replace('**', '')
            flowables.append(Spacer(1, 8))
            flowables.append(Paragraph(escape_xml(text), styles['Heading3']))
            i += 1
            continue
        elif raw.startswith('##'):
            text = raw[2:].strip().replace('**', '')
            flowables.append(Spacer(1, 10))
            flowables.append(Paragraph(escape_xml(text), styles['Heading2']))
            i += 1
            continue
        elif raw.startswith('#'):
            text = raw[1:].strip().replace('**', '')
            flowables.append(Spacer(1, 12))
            flowables.append(Paragraph(escape_xml(text), styles['Heading1']))
            i += 1
            continue
        
        # Checkbox lines
        if raw.strip().startswith('[ ]') or raw.strip().startswith('[X]') or raw.strip().startswith('[x]'):
            text = raw.strip()
            text = text.replace('**', '')
            flowables.append(Paragraph(escape_xml(text), styles['Body']))
            i += 1
            continue
        
        # Indented/bulleted items
        if raw.strip().startswith('- ') or raw.strip().startswith('* '):
            indent_level = len(raw) - len(raw.lstrip())
            text = raw.strip()[2:]  # Remove bullet
            text = process_inline(text)
            style_name = 'Bullet2' if indent_level >= 4 else 'Bullet'
            flowables.append(Paragraph(f"* {text}", styles[style_name]))
            i += 1
            continue
        
        # Numbered items (like "1. " or "(a)")
        if raw.strip() and (raw.strip()[0].isdigit() or raw.strip().startswith('(')):
            text = process_inline(raw.strip())
            flowables.append(Paragraph(text, styles['Body']))
            i += 1
            continue
        
        # Block quotes
        if raw.strip().startswith('>'):
            text = raw.strip()[1:].strip()
            text = process_inline(text)
            flowables.append(Paragraph(text, styles['BlockQuote']))
            i += 1
            continue
        
        # Regular paragraph
        text = process_inline(raw.strip())
        if text:
            flowables.append(Paragraph(text, styles['Body']))
        
        i += 1
    
    return flowables


def process_inline(text):
    """Process inline markdown formatting to ReportLab XML."""
    # Handle bold
    result = text
    # Simple bold replacement: **text** -> <b>text</b>
    while '**' in result:
        first = result.find('**')
        second = result.find('**', first + 2)
        if second == -1:
            break
        inner = result[first+2:second]
        result = result[:first] + '<b>' + inner + '</b>' + result[second+2:]
    
    # Handle italic: *text* -> <i>text</i> (but not ** which we already handled)
    parts = []
    idx = 0
    while idx < len(result):
        if result[idx] == '*' and (idx == 0 or result[idx-1] != '*') and (idx + 1 < len(result) and result[idx+1] != '*'):
            end = result.find('*', idx + 1)
            if end != -1 and result[end-1:end+1] != '**':
                inner = result[idx+1:end]
                parts.append('<i>' + inner + '</i>')
                idx = end + 1
                continue
        parts.append(result[idx])
        idx += 1
    result = ''.join(parts)
    
    # Escape any remaining problematic chars (but preserve our XML tags)
    # We need to be careful not to double-escape
    temp = result
    temp = temp.replace('&', '&amp;')
    # Restore our tags
    temp = temp.replace('&lt;b&gt;', '<b>').replace('&lt;/b&gt;', '</b>')
    temp = temp.replace('&lt;i&gt;', '<i>').replace('&lt;/i&gt;', '</i>')
    
    return temp


def build_styles():
    """Build paragraph styles for court document formatting."""
    styles = {}
    
    styles['Heading1'] = ParagraphStyle(
        'Heading1',
        fontName='Times-Bold',
        fontSize=14,
        leading=28,
        alignment=TA_CENTER,
        spaceAfter=12,
        spaceBefore=12,
    )
    
    styles['Heading2'] = ParagraphStyle(
        'Heading2',
        fontName='Times-Bold',
        fontSize=12,
        leading=24,
        alignment=TA_LEFT,
        spaceAfter=8,
        spaceBefore=10,
        underline=True,
    )
    
    styles['Heading3'] = ParagraphStyle(
        'Heading3',
        fontName='Times-Bold',
        fontSize=12,
        leading=24,
        alignment=TA_LEFT,
        spaceAfter=6,
        spaceBefore=8,
    )
    
    styles['Heading4'] = ParagraphStyle(
        'Heading4',
        fontName='Times-Bold',
        fontSize=11,
        leading=22,
        alignment=TA_LEFT,
        spaceAfter=4,
        spaceBefore=6,
    )
    
    styles['Heading5'] = ParagraphStyle(
        'Heading5',
        fontName='Times-Bold',
        fontSize=11,
        leading=22,
        alignment=TA_LEFT,
        spaceAfter=4,
        spaceBefore=4,
    )
    
    styles['Heading6'] = ParagraphStyle(
        'Heading6',
        fontName='Times-Bold',
        fontSize=10,
        leading=20,
        alignment=TA_LEFT,
        spaceAfter=4,
        spaceBefore=4,
    )
    
    styles['Body'] = ParagraphStyle(
        'Body',
        fontName='Times-Roman',
        fontSize=12,
        leading=24,  # Double-spaced (12pt * 2)
        alignment=TA_JUSTIFY,
        spaceAfter=6,
        firstLineIndent=0,
    )
    
    styles['Bullet'] = ParagraphStyle(
        'Bullet',
        fontName='Times-Roman',
        fontSize=12,
        leading=24,
        alignment=TA_LEFT,
        spaceAfter=4,
        leftIndent=36,
        firstLineIndent=-18,
    )
    
    styles['Bullet2'] = ParagraphStyle(
        'Bullet2',
        fontName='Times-Roman',
        fontSize=12,
        leading=24,
        alignment=TA_LEFT,
        spaceAfter=4,
        leftIndent=72,
        firstLineIndent=-18,
    )
    
    styles['BlockQuote'] = ParagraphStyle(
        'BlockQuote',
        fontName='Times-Italic',
        fontSize=11,
        leading=22,
        alignment=TA_JUSTIFY,
        spaceAfter=6,
        leftIndent=36,
        rightIndent=36,
    )
    
    styles['Caption'] = ParagraphStyle(
        'Caption',
        fontName='Times-Roman',
        fontSize=12,
        leading=18,
        alignment=TA_CENTER,
        spaceAfter=4,
    )
    
    styles['CaptionBold'] = ParagraphStyle(
        'CaptionBold',
        fontName='Times-Bold',
        fontSize=12,
        leading=18,
        alignment=TA_CENTER,
        spaceAfter=4,
    )
    
    styles['SignatureLine'] = ParagraphStyle(
        'SignatureLine',
        fontName='Times-Roman',
        fontSize=12,
        leading=24,
        alignment=TA_LEFT,
        spaceAfter=4,
        leftIndent=216,
    )
    
    styles['TableCell'] = ParagraphStyle(
        'TableCell',
        fontName='Times-Roman',
        fontSize=10,
        leading=14,
        alignment=TA_LEFT,
    )
    
    styles['DocTitle'] = ParagraphStyle(
        'DocTitle',
        fontName='Times-Bold',
        fontSize=16,
        leading=24,
        alignment=TA_CENTER,
        spaceAfter=24,
        spaceBefore=72,
    )
    
    return styles


def build_caption(styles):
    """Build the standard court caption."""
    caption = []
    caption.append(Paragraph("STATE OF MICHIGAN", styles['CaptionBold']))
    caption.append(Paragraph("IN THE 14TH CIRCUIT COURT FOR THE COUNTY OF MUSKEGON", styles['CaptionBold']))
    caption.append(Spacer(1, 12))
    
    # Build caption table
    caption_data = [
        [Paragraph("ANDREW J. PIGORS,", styles['Caption']),
         Paragraph("Case No. 2024-001507-DC", styles['Caption'])],
        [Paragraph("Plaintiff/Father, Pro Se", styles['Caption']),
         Paragraph("Hon. Jenny L. McNeill", styles['Caption'])],
        [Paragraph("", styles['Caption']), Paragraph("", styles['Caption'])],
        [Paragraph("v.", styles['Caption']), Paragraph("", styles['Caption'])],
        [Paragraph("", styles['Caption']), Paragraph("", styles['Caption'])],
        [Paragraph("EMILY M. WATSON,", styles['Caption']), Paragraph("", styles['Caption'])],
        [Paragraph("Defendant/Mother.", styles['Caption']), Paragraph("", styles['Caption'])],
    ]
    
    t = Table(caption_data, colWidths=[3.25*inch, 3.25*inch])
    t.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LINEBELOW', (0, -1), (-1, -1), 1, colors.black),
    ]))
    caption.append(t)
    caption.append(Spacer(1, 12))
    
    return caption


def main():
    styles = build_styles()
    
    doc = SimpleDocTemplate(
        OUTPUT,
        pagesize=letter,
        leftMargin=1*inch,
        rightMargin=1*inch,
        topMargin=1*inch,
        bottomMargin=1*inch,
    )
    
    all_flowables = []
    
    for idx, (filename, title) in enumerate(FILES):
        filepath = os.path.join(BASE, filename)
        
        if idx > 0:
            all_flowables.append(PageBreak())
        
        # Add document title page header
        all_flowables.append(Paragraph(title, styles['DocTitle']))
        all_flowables.append(Spacer(1, 12))
        
        # Read and convert markdown
        md_text = read_md(filepath)
        flowables = md_to_flowables(md_text, styles)
        all_flowables.extend(flowables)
    
    # Build the PDF
    doc.build(all_flowables, onFirstPage=add_page_number, onLaterPages=add_page_number)
    
    print(f"PDF generated successfully: {OUTPUT}")
    print(f"Total documents: {len(FILES)}")
    
    # File size
    size = os.path.getsize(OUTPUT)
    print(f"File size: {size:,} bytes ({size/1024:.1f} KB)")


if __name__ == '__main__':
    main()
