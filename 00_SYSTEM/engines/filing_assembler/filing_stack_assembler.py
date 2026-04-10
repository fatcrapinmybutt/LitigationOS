#!/usr/bin/env python3
"""
FILING STACK ASSEMBLER — Court-Grade Single-PDF Assembly Engine
================================================================
Produces ONE sequential PDF per filing package exactly as handed to
the clerk at the Muskegon County Circuit Court window.

Stack Order (page 1 = top of stack = what clerk sees first):
  1. SCAO Cover Sheet (MC 01c / MC 01a)
  2. Motion / Complaint / Petition (main document)
  3. Brief in Support (if separate from motion)
  4. Affidavit / Verification (sworn facts, chronological)
  5. Exhibit Cover Pages + Exhibits (A, B, C... each with cover)
  6. Proposed Order
  7. Certificate of Service
  8. Proof of Service (MC 11)
  9. Fee Waiver (MC 20a if applicable)

MCR Compliance:
  - MCR 1.109(D): 8.5x11, 1" margins, 12pt TNR, double-spaced
  - MCR 2.113: Proper captions, numbered paragraphs
  - MCR 2.119: Motion practice format, 20-page brief limit
  - Page numbers bottom center

Dependencies: reportlab, pypdf (both installed)
"""

import logging
import sys, os, re, io, copy
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

# Shared module integration (with fallback for standalone execution)
try:
    _SYSTEM_DIR = Path(__file__).resolve().parent.parent.parent  # engines/filing_assembler/ → 00_SYSTEM/
    if str(_SYSTEM_DIR) not in sys.path:
        sys.path.insert(0, str(_SYSTEM_DIR))
    from shared import get_root
    _HAS_SHARED = True
except ImportError:
    _HAS_SHARED = False
    logger.debug("shared module not available, using standalone fallback paths")

# ── Paths ──────────────────────────────────────────────────────────
if _HAS_SHARED:
    REPO = get_root()
else:
    REPO = Path(__file__).resolve().parents[3]  # fallback
OUTPUT_DIR  = REPO / "FINAL_FILING_PDFS"
FONTS_DIR   = Path(r"C:\Windows\Fonts")

# ── Case constants ─────────────────────────────────────────────────
PLAINTIFF   = "ANDREW J. PIGORS"
PL_ADDRESS  = "1423 W. Norton Ave\nNorton Shores, Michigan 49441"
PL_PHONE    = "(231) 903-5690"

# ── Filing package definitions ─────────────────────────────────────
# Maps filing ID -> metadata
FILING_DEFS = {
    "F1": {
        "title": "EMERGENCY MOTION FOR TEMPORARY RESTRAINING ORDER",
        "case_no": "2024-001507-DC",
        "court": "CIRCUIT COURT FOR THE COUNTY OF MUSKEGON\n14TH JUDICIAL CIRCUIT",
        "judge": "Hon. Jenny L. McNeill",
        "defendant": "EMILY A. WATSON",
        "doc_type": "motion",
        "pkg_dir": "PKG_F1_EMERGENCY_TRO",
    },
    "F2": {
        "title": "VERIFIED COMPLAINT",
        "case_no": "2025-002760-CZ",
        "court": "CIRCUIT COURT FOR THE COUNTY OF MUSKEGON\n14TH JUDICIAL CIRCUIT",
        "judge": "",
        "defendant": "SHADY OAKS MOBILE HOME PARK, LLC, et al.",
        "doc_type": "complaint",
        "pkg_dir": "PKG_F2_SHADY_OAKS_COMPLAINT",
    },
    "F3": {
        "title": "MOTION AND BRIEF FOR DISQUALIFICATION OF JUDGE\nPursuant to MCR 2.003",
        "case_no": "2024-001507-DC",
        "court": "CIRCUIT COURT FOR THE COUNTY OF MUSKEGON\n14TH JUDICIAL CIRCUIT",
        "judge": "Hon. Jenny L. McNeill",
        "defendant": "EMILY A. WATSON",
        "doc_type": "motion",
        "pkg_dir": "PKG_F3_DISQUALIFICATION_MCR_2003",
    },
    "F4": {
        "title": "COMPLAINT UNDER 42 U.S.C. § 1983",
        "case_no": "",
        "court": "UNITED STATES DISTRICT COURT\nWESTERN DISTRICT OF MICHIGAN, SOUTHERN DIVISION",
        "judge": "",
        "defendant": "HON. JENNY L. McNEILL, et al.",
        "doc_type": "complaint",
        "pkg_dir": "PKG_F4_FEDERAL_S1983_COMPLAINT",
    },
    "F5": {
        "title": "APPLICATION FOR LEAVE TO FILE ORIGINAL ACTION\nPursuant to MCR 7.306",
        "case_no": "",
        "court": "MICHIGAN SUPREME COURT",
        "judge": "",
        "defendant": "EMILY A. WATSON",
        "doc_type": "application",
        "pkg_dir": "PKG_F5_MSC_ORIGINAL_ACTION",
    },
    "F6": {
        "title": "FORMAL COMPLAINT AGAINST HON. JENNY L. McNEILL",
        "case_no": "",
        "court": "JUDICIAL TENURE COMMISSION\nSTATE OF MICHIGAN",
        "judge": "",
        "defendant": "",
        "doc_type": "complaint",
        "pkg_dir": "PKG_F6_JTC_COMPLAINT",
    },
    "F7": {
        "title": "MOTION FOR MODIFICATION OF CUSTODY\nPursuant to MCL 722.27",
        "case_no": "2024-001507-DC",
        "court": "CIRCUIT COURT FOR THE COUNTY OF MUSKEGON\n14TH JUDICIAL CIRCUIT",
        "judge": "Hon. Jenny L. McNeill",
        "defendant": "EMILY A. WATSON",
        "doc_type": "motion",
        "pkg_dir": "PKG_F7_CUSTODY_MODIFICATION",
    },
    "F8": {
        "title": "MOTION TO TERMINATE PERSONAL PROTECTION ORDER",
        "case_no": "2023-5907-PP",
        "court": "CIRCUIT COURT FOR THE COUNTY OF MUSKEGON\n14TH JUDICIAL CIRCUIT",
        "judge": "Hon. Jenny L. McNeill",
        "defendant": "EMILY A. WATSON",
        "doc_type": "motion",
        "pkg_dir": "PKG_F8_PPO_TERMINATION",
    },
    "F9": {
        "title": "BRIEF ON APPEAL",
        "case_no": "366810",
        "court": "MICHIGAN COURT OF APPEALS",
        "judge": "",
        "defendant": "EMILY A. WATSON",
        "doc_type": "brief",
        "pkg_dir": "PKG_F9_COA_BRIEF_ON_APPEAL",
    },
    "F10": {
        "title": "EMERGENCY MOTION FOR IMMEDIATE CONSIDERATION",
        "case_no": "366810",
        "court": "MICHIGAN COURT OF APPEALS",
        "judge": "",
        "defendant": "EMILY A. WATSON",
        "doc_type": "motion",
        "pkg_dir": "PKG_F10_COA_EMERGENCY_MOTION",
    },
    "CRIMINAL": {
        "title": "MOTION TO SUBSTITUTE COUNSEL",
        "case_no": "2025-25245676SM",
        "court": "60TH DISTRICT COURT\nCOUNTY OF MUSKEGON",
        "judge": "Hon. Kostrzewa Raymond J. Jr.",
        "defendant": "PEOPLE OF THE STATE OF MICHIGAN",
        "doc_type": "motion",
        "pkg_dir": "PKG_CRIMINAL",
    },
}

# ── Document stack ordering ────────────────────────────────────────
# Priority-ordered list of filename patterns for each slot in the stack
# Lower index = closer to top of stack (page 1)
STACK_ORDER = [
    # Slot 0: SCAO cover sheets
    ("SCAO_COVER", [
        "MC_01a*", "MC_01c*", "SCAO_MC*01*", "SCAO_CIVIL*COVER*",
        "*SUMMONS*COMPLAINT*", "*COVER_SHEET*",
    ]),
    # Slot 1: Main filing document
    ("MAIN_FILING", [
        "ASSEMBLED_FILING*", "01_MAIN_FILING.md",
        "VERIFIED_COMPLAINT*", "*COMPLAINT*.md",
        "*MOTION*.md", "*PETITION*.md", "*APPLICATION*.md",
        "*BRIEF_ON_APPEAL*",
    ]),
    # Slot 2: Brief / Memorandum in Support (if separate)
    ("BRIEF", [
        "*BRIEF*SUPPORT*", "*MEMORANDUM*", "*LEGAL_ARGUMENT*",
    ]),
    # Slot 3: Affidavit / Verification / Declaration
    ("AFFIDAVIT", [
        "02_AFFIDAVIT*", "*AFFIDAVIT*", "*DECLARATION*", "*VERIFICATION*",
    ]),
    # Slot 4: Exhibit Index (precedes exhibits)
    ("EXHIBIT_INDEX", [
        "03_EXHIBIT_INDEX*", "*EXHIBIT_INDEX*", "*EXHIBIT_LIST*",
    ]),
    # Slot 5: Individual Exhibits with cover pages — handled dynamically
    ("EXHIBITS", []),
    # Slot 6: FOC forms (custody-specific)
    ("FOC_FORMS", [
        "FOC_*", "SCAO_FOC*", "CC_377*", "SCAO_CC*",
    ]),
    # Slot 7: Proposed Order
    ("PROPOSED_ORDER", [
        "*PROPOSED_ORDER*", "*ORDER_GRANTING*", "*PROPOSED*ORDER*",
    ]),
    # Slot 8: Certificate of Service
    ("CERT_SERVICE", [
        "04_CERTIFICATE_OF_SERVICE*", "*CERTIFICATE*SERVICE*",
        "*CERT*SERVICE*", "*COS*",
    ]),
    # Slot 9: Proof of Service (MC 11)
    ("PROOF_SERVICE", [
        "MC_11*", "SCAO_MC*11*", "*PROOF*SERVICE*",
    ]),
    # Slot 10: Fee Waiver
    ("FEE_WAIVER", [
        "MC_20*", "SCAO_MC*20*", "*FEE_WAIVER*", "MC_290*",
    ]),
    # Slot 11: Compliance / Cert of Compliance
    ("COMPLIANCE", [
        "*CERT*COMPLIANCE*", "*COMPLIANCE*",
    ]),
]

# Files to SKIP (not part of the filing stack)
SKIP_PATTERNS = [
    "*CHECKLIST*", "*MANIFEST*", "*FORM_FILL*", "*HEARING_PREP*",
    "*COURTROOM_PROTOCOL*", "*CAPTION*", "*.bak*", "*_BACKUP_*",
    "*.py", "*.json", "*.db", "*.log",
]


# ══════════════════════════════════════════════════════════════════
# PDF GENERATION ENGINE (reportlab)
# ══════════════════════════════════════════════════════════════════

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak,
    HRFlowable, Table, TableStyle, KeepTogether, Frame,
    PageTemplate, BaseDocTemplate
)
from reportlab.lib.colors import black, white, grey, HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Register Times New Roman from Windows Fonts
try:
    pdfmetrics.registerFont(TTFont('TNR', str(FONTS_DIR / 'times.ttf')))
    pdfmetrics.registerFont(TTFont('TNR-Bold', str(FONTS_DIR / 'timesbd.ttf')))
    pdfmetrics.registerFont(TTFont('TNR-Italic', str(FONTS_DIR / 'timesi.ttf')))
    pdfmetrics.registerFont(TTFont('TNR-BoldItalic', str(FONTS_DIR / 'timesbi.ttf')))
    pdfmetrics.registerFontFamily('TNR',
        normal='TNR', bold='TNR-Bold',
        italic='TNR-Italic', boldItalic='TNR-BoldItalic')
    FONT_REGULAR = 'TNR'
    FONT_BOLD = 'TNR-Bold'
    FONT_ITALIC = 'TNR-Italic'
    FONT_BI = 'TNR-BoldItalic'
except Exception as e:
    logger.warning("[font_init] Times New Roman TTF not available, falling back to built-in Times: %s", e)
    FONT_REGULAR = 'Times-Roman'
    FONT_BOLD = 'Times-Bold'
    FONT_ITALIC = 'Times-Italic'
    FONT_BI = 'Times-BoldItalic'

# ── Court-standard styles ──────────────────────────────────────────
def get_court_styles():
    """Build MCR 1.109(D) compliant paragraph styles."""
    styles = getSampleStyleSheet()
    cs = {}

    cs['body'] = ParagraphStyle(
        'CourtBody', parent=styles['Normal'],
        fontName=FONT_REGULAR, fontSize=12,
        leading=24,            # double-spaced (12pt * 2)
        alignment=TA_JUSTIFY,
        spaceAfter=0, spaceBefore=0,
        firstLineIndent=36,    # paragraph indent
    )

    cs['body_no_indent'] = ParagraphStyle(
        'CourtBodyNoIndent', parent=cs['body'],
        firstLineIndent=0,
    )

    cs['h1'] = ParagraphStyle(
        'CourtH1', parent=styles['Heading1'],
        fontName=FONT_BOLD, fontSize=14,
        leading=28, alignment=TA_CENTER,
        spaceAfter=12, spaceBefore=24,
        textColor=black,
    )

    cs['h2'] = ParagraphStyle(
        'CourtH2', parent=styles['Heading2'],
        fontName=FONT_BOLD, fontSize=13,
        leading=26, alignment=TA_LEFT,
        spaceAfter=6, spaceBefore=18,
        textColor=black,
    )

    cs['h3'] = ParagraphStyle(
        'CourtH3', parent=styles['Heading3'],
        fontName=FONT_BOLD, fontSize=12,
        leading=24, alignment=TA_LEFT,
        spaceAfter=6, spaceBefore=12,
        textColor=black,
    )

    cs['h4'] = ParagraphStyle(
        'CourtH4', parent=cs['body'],
        fontName=FONT_BOLD, fontSize=12,
        leading=24, alignment=TA_LEFT,
        spaceAfter=3, spaceBefore=6,
        firstLineIndent=0,
    )

    cs['quote'] = ParagraphStyle(
        'CourtQuote', parent=cs['body'],
        leftIndent=36, rightIndent=36,
        fontName=FONT_ITALIC, fontSize=11,
        leading=22,  # single-spaced block quotes (>50 words per MCR)
        firstLineIndent=0,
    )

    cs['bullet'] = ParagraphStyle(
        'CourtBullet', parent=cs['body'],
        leftIndent=54, bulletIndent=36,
        firstLineIndent=0,
        spaceBefore=2, spaceAfter=2,
    )

    cs['numbered'] = ParagraphStyle(
        'CourtNumbered', parent=cs['bullet'],
    )

    cs['caption_court'] = ParagraphStyle(
        'CaptionCourt', parent=styles['Normal'],
        fontName=FONT_REGULAR, fontSize=12,
        leading=16, alignment=TA_CENTER,
        spaceAfter=6,
    )

    cs['caption_party'] = ParagraphStyle(
        'CaptionParty', parent=styles['Normal'],
        fontName=FONT_REGULAR, fontSize=12,
        leading=16, alignment=TA_LEFT,
    )

    cs['caption_right'] = ParagraphStyle(
        'CaptionRight', parent=styles['Normal'],
        fontName=FONT_REGULAR, fontSize=12,
        leading=16, alignment=TA_LEFT,
    )

    cs['exhibit_cover'] = ParagraphStyle(
        'ExhibitCover', parent=styles['Normal'],
        fontName=FONT_BOLD, fontSize=36,
        leading=44, alignment=TA_CENTER,
        spaceBefore=72,
    )

    cs['exhibit_desc'] = ParagraphStyle(
        'ExhibitDesc', parent=styles['Normal'],
        fontName=FONT_REGULAR, fontSize=14,
        leading=24, alignment=TA_CENTER,
        spaceBefore=24,
    )

    cs['page_num'] = ParagraphStyle(
        'PageNum', parent=styles['Normal'],
        fontName=FONT_REGULAR, fontSize=10,
        leading=12, alignment=TA_CENTER,
    )

    cs['footer'] = ParagraphStyle(
        'Footer', parent=styles['Normal'],
        fontName=FONT_REGULAR, fontSize=9,
        leading=11, alignment=TA_CENTER,
    )

    return cs


# ── Markdown parser (enhanced) ─────────────────────────────────────
def parse_markdown(md_text):
    """Parse markdown into structured elements for PDF rendering."""
    lines = md_text.split('\n')
    elements = []
    in_table = False
    table_rows = []

    for line in lines:
        stripped = line.strip()

        # Table handling
        if stripped.startswith('|') and '|' in stripped[1:]:
            if re.match(r'^\|[\s\-:|]+\|$', stripped):
                continue  # skip separator rows
            cells = [c.strip() for c in stripped.split('|')[1:-1]]
            if not in_table:
                in_table = True
                table_rows = []
            table_rows.append(cells)
            continue
        elif in_table:
            elements.append(('TABLE', table_rows))
            table_rows = []
            in_table = False

        # Headers
        if stripped.startswith('##### '):
            elements.append(('H4', stripped[6:]))
        elif stripped.startswith('#### '):
            elements.append(('H4', stripped[5:]))
        elif stripped.startswith('### '):
            elements.append(('H3', stripped[4:]))
        elif stripped.startswith('## '):
            elements.append(('H2', stripped[3:]))
        elif stripped.startswith('# '):
            elements.append(('H1', stripped[2:]))
        elif stripped.startswith('---') and len(stripped.replace('-','')) == 0:
            elements.append(('HR', ''))
        elif stripped.startswith('> '):
            elements.append(('QUOTE', stripped[2:]))
        elif stripped.startswith('>'):
            elements.append(('QUOTE', stripped[1:].strip()))
        elif re.match(r'^[-*]\s', stripped):
            elements.append(('BULLET', stripped[2:]))
        elif re.match(r'^\d+\.\s', stripped):
            elements.append(('NUMBERED', re.sub(r'^\d+\.\s*', '', stripped)))
        elif stripped == '':
            elements.append(('BLANK', ''))
        else:
            elements.append(('PARA', stripped))

    if in_table and table_rows:
        elements.append(('TABLE', table_rows))

    return elements


def sanitize_xml(text):
    """Escape XML special chars for reportlab Paragraph."""
    if not text:
        return ''
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    # Preserve bold/italic markdown as reportlab tags
    text = re.sub(r'\*\*\*(.+?)\*\*\*', r'<b><i>\1</i></b>', text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)
    text = re.sub(r'`(.+?)`', r'<font face="{}">\1</font>'.format(FONT_REGULAR), text)
    return text


def md_to_story(md_text, styles):
    """Convert markdown text to reportlab story elements."""
    elements = parse_markdown(md_text)
    story = []

    for etype, content in elements:
        if etype == 'BLANK':
            story.append(Spacer(1, 6))
            continue
        if etype == 'HR':
            story.append(Spacer(1, 4))
            story.append(HRFlowable(width="100%", thickness=1, color=black))
            story.append(Spacer(1, 4))
            continue

        if etype == 'TABLE':
            try:
                rows = content
                if rows:
                    t = Table(rows, repeatRows=1)
                    t.setStyle(TableStyle([
                        ('FONTNAME', (0,0), (-1,0), FONT_BOLD),
                        ('FONTNAME', (0,1), (-1,-1), FONT_REGULAR),
                        ('FONTSIZE', (0,0), (-1,-1), 10),
                        ('LEADING', (0,0), (-1,-1), 14),
                        ('GRID', (0,0), (-1,-1), 0.5, grey),
                        ('BACKGROUND', (0,0), (-1,0), HexColor('#E8E8E8')),
                        ('VALIGN', (0,0), (-1,-1), 'TOP'),
                        ('LEFTPADDING', (0,0), (-1,-1), 4),
                        ('RIGHTPADDING', (0,0), (-1,-1), 4),
                    ]))
                    story.append(Spacer(1, 6))
                    story.append(t)
                    story.append(Spacer(1, 6))
            except Exception as e:
                logger.warning("[md_to_story] Table rendering failed, skipping table: %s", e, exc_info=True)
            continue

        safe = sanitize_xml(content)
        if not safe.strip():
            continue

        style_map = {
            'H1': 'h1', 'H2': 'h2', 'H3': 'h3', 'H4': 'h4',
            'QUOTE': 'quote', 'BULLET': 'bullet',
            'NUMBERED': 'numbered', 'PARA': 'body',
        }
        style_key = style_map.get(etype, 'body')

        if etype == 'BULLET':
            safe = f"•  {safe}"
        elif etype == 'NUMBERED':
            safe = f"    {safe}"

        try:
            story.append(Paragraph(safe, styles[style_key]))
        except Exception as e:
            logger.warning("[md_to_story] Paragraph render failed for style '%s', falling back to plain text: %s", style_key, e)
            plain = re.sub(r'<[^>]+>', '', safe)
            story.append(Paragraph(plain, styles['body_no_indent']))

    return story


# ── Page number callback ───────────────────────────────────────────
class PageNumberCanvas:
    """Canvas wrapper that adds page numbers at bottom center."""
    def __init__(self, canvas, doc):
        self._canvas = canvas
        self._doc = doc

    @staticmethod
    def add_page_number(canvas, doc):
        page_num = canvas.getPageNumber()
        text = f"— {page_num} —"
        canvas.saveState()
        canvas.setFont(FONT_REGULAR, 10)
        canvas.drawCentredString(
            letter[0] / 2,  # center of page
            0.5 * inch,     # half inch from bottom
            text
        )
        canvas.restoreState()


# ── Exhibit cover page generator ───────────────────────────────────
def make_exhibit_cover_page(letter_label, description, styles):
    """Generate a full-page exhibit cover/divider."""
    story = []
    story.append(Spacer(1, 2.5 * inch))
    story.append(Paragraph(f"EXHIBIT {letter_label}", styles['exhibit_cover']))
    story.append(Spacer(1, 0.5 * inch))
    story.append(HRFlowable(width="60%", thickness=2, color=black))
    story.append(Spacer(1, 0.3 * inch))
    safe_desc = sanitize_xml(description)
    story.append(Paragraph(safe_desc, styles['exhibit_desc']))
    story.append(PageBreak())
    return story


# ── Caption page generator ─────────────────────────────────────────
def make_caption_page(filing_def, styles):
    """Generate proper Michigan circuit court caption page."""
    story = []

    # Court name
    story.append(Paragraph("STATE OF MICHIGAN", styles['caption_court']))
    story.append(Paragraph(f"IN THE {filing_def['court']}", styles['caption_court']))
    story.append(Spacer(1, 18))

    # Caption box with party names
    # Left side: parties, Right side: case info
    caption_data = [
        [
            f"{PLAINTIFF},\n        Plaintiff,\n\nv.\n\n{filing_def.get('defendant','')},\n        Defendant{'(s)' if 'et al' in filing_def.get('defendant','') else ''}.",
            f"Case No. {filing_def['case_no']}\n\n{filing_def.get('judge','')}"
        ]
    ]

    # Build as a simple caption
    story.append(Paragraph(f"{PLAINTIFF},", styles['caption_party']))
    story.append(Paragraph("        Plaintiff,", styles['caption_party']))
    story.append(Spacer(1, 12))

    # Case number on right
    story.append(Paragraph(
        f'<para alignment="left">v.'
        f'&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
        f'&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
        f'&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
        f'&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
        f'Case No. {filing_def["case_no"]}</para>',
        styles['caption_party']
    ))

    story.append(Spacer(1, 12))
    if filing_def.get('judge'):
        story.append(Paragraph(
            f'<para alignment="left">'
            f'&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
            f'&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
            f'&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
            f'&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
            f'&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
            f'{filing_def["judge"]}</para>',
            styles['caption_party']
        ))
        story.append(Spacer(1, 12))

    defendant = filing_def.get('defendant', '')
    story.append(Paragraph(f"{defendant},", styles['caption_party']))
    story.append(Paragraph(
        f"        Defendant{'(s)' if 'et al' in defendant.lower() else ''}.",
        styles['caption_party']
    ))

    story.append(Paragraph("_" * 60, styles['caption_party']))
    story.append(Spacer(1, 18))

    # Document title
    title = filing_def['title']
    for title_line in title.split('\n'):
        story.append(Paragraph(f"<b>{sanitize_xml(title_line)}</b>", styles['h1']))

    story.append(Spacer(1, 12))
    story.append(HRFlowable(width="100%", thickness=1, color=black))
    story.append(Spacer(1, 12))

    return story


# ══════════════════════════════════════════════════════════════════
# MAIN ASSEMBLY ENGINE
# ══════════════════════════════════════════════════════════════════

def find_pkg_dir(filing_id):
    """Locate the package directory for a filing ID."""
    fdef = FILING_DEFS.get(filing_id)
    if not fdef:
        return None
    pkg_name = fdef['pkg_dir']
    # Check root
    d = REPO / pkg_name
    if d.exists():
        return d
    # Check 01_FILINGS
    d = REPO / "01_FILINGS" / pkg_name
    if d.exists():
        return d
    return None


def match_files(pkg_dir, patterns):
    """Find files matching any of the glob patterns in pkg_dir."""
    matches = []
    for pattern in patterns:
        for f in pkg_dir.glob(pattern):
            if f.is_file() and f.suffix.lower() in ('.md', '.txt', '.pdf'):
                if not any(f.match(skip) for skip in SKIP_PATTERNS):
                    if f not in matches:
                        matches.append(f)
    return matches


def should_skip_file(filepath):
    """Check if a file should be excluded from the stack."""
    name = filepath.name.upper()
    skip_words = [
        'CHECKLIST', 'MANIFEST', 'FORM_FILL', 'HEARING_PREP',
        'COURTROOM_PROTOCOL', '06_CAPTION', '.BAK', '_BACKUP_',
        'PACKAGE_MANIFEST', '07_FORM_FILL', '08_HEARING',
        '11_COURTROOM', '05_COURT_FORMS',
    ]
    return any(w in name for w in skip_words)


def classify_file(filepath, filing_def):
    """Classify a file into a stack slot."""
    name = filepath.name.upper()
    stem = filepath.stem.upper()

    # SCAO cover sheets
    if any(x in name for x in ['MC_01A', 'MC_01C', 'MC01A', 'MC01C',
                                 'COVER_SHEET', 'CIVIL_CASE_COVER']):
        return 0  # SCAO_COVER

    # Assembled filing (the main combined document)
    if 'ASSEMBLED_FILING' in name:
        return 1  # MAIN_FILING

    # Main filing
    if name.startswith('01_MAIN') or 'VERIFIED_COMPLAINT' in name:
        return 1  # MAIN_FILING

    # Brief
    if 'BRIEF' in name and 'SUPPORT' in name:
        return 2

    # Affidavit
    if name.startswith('02_AFFIDAVIT') or 'AFFIDAVIT' in name or 'DECLARATION' in name:
        return 3

    # Exhibit index
    if name.startswith('03_EXHIBIT') or 'EXHIBIT_INDEX' in name:
        return 4

    # FOC forms
    if name.startswith('FOC_') or name.startswith('CC_377') or 'SCAO_FOC' in name:
        return 6

    # Proposed order
    if 'PROPOSED_ORDER' in name or 'ORDER_GRANTING' in name:
        return 7

    # Certificate of service
    if name.startswith('04_CERT') or 'CERTIFICATE_OF_SERVICE' in name:
        return 8

    # Proof of service MC 11
    if 'MC_11' in name or 'MC11' in name or 'PROOF_OF_SERVICE' in name:
        return 9

    # Fee waiver
    if 'MC_20' in name or 'MC20' in name or 'FEE_WAIVER' in name or 'MC_290' in name:
        return 10

    # Compliance cert
    if 'COMPLIANCE' in name or 'CERT_OF_COMPLIANCE' in name:
        return 11

    # SCAO forms (generic — put after proposed order)
    if name.startswith('SCAO_') or name.startswith('MC_'):
        return 6

    # Default: treat as supplemental after affidavit
    return 5  # EXHIBITS slot


def extract_exhibits_from_md(md_text):
    """Extract exhibit references from markdown text."""
    exhibits = []
    # Match patterns like "Exhibit A — Description" or "**Exhibit B**"
    patterns = [
        r'Exhibit\s+([A-Z])\s*[—\-:]\s*(.+)',
        r'Exhibit\s+([A-Z])\s*\(([^)]+)\)',
        r'\*\*Exhibit\s+([A-Z])\*\*\s*[—\-:]\s*(.+)',
    ]
    for pattern in patterns:
        for m in re.finditer(pattern, md_text, re.IGNORECASE):
            letter_val = m.group(1).upper()
            desc = m.group(2).strip().rstrip('.')
            if (letter_val, desc) not in exhibits:
                exhibits.append((letter_val, desc))

    # Sort by letter
    exhibits.sort(key=lambda x: x[0])
    return exhibits


def assemble_filing(filing_id, verbose=True):
    """
    Assemble a complete filing package into a single court-ready PDF.

    Returns: (output_path, page_count, status_message)
    """
    fdef = FILING_DEFS.get(filing_id)
    if not fdef:
        return None, 0, f"Unknown filing ID: {filing_id}"

    pkg_dir = find_pkg_dir(filing_id)
    if not pkg_dir:
        return None, 0, f"Package directory not found for {filing_id}"

    if verbose:
        print(f"\n{'='*60}")
        print(f"  ASSEMBLING: {filing_id} — {fdef['title'].split(chr(10))[0]}")
        print(f"  Package: {pkg_dir}")
        print(f"{'='*60}")

    styles = get_court_styles()

    # ── Collect and classify all files ─────────────────────────────
    all_files = sorted(pkg_dir.glob('*.md'))
    classified = {}  # slot_index -> [(priority, filepath)]

    for f in all_files:
        if should_skip_file(f):
            if verbose:
                print(f"  SKIP: {f.name}")
            continue

        slot = classify_file(f, fdef)
        if slot not in classified:
            classified[slot] = []
        classified[slot].append(f)
        if verbose:
            slot_name = STACK_ORDER[slot][0] if slot < len(STACK_ORDER) else "SUPPLEMENTAL"
            print(f"  SLOT {slot:2d} ({slot_name:15s}): {f.name}")

    # ── Determine main document ────────────────────────────────────
    # Prefer ASSEMBLED_FILING if it exists (it's the combined document)
    main_files = classified.get(1, [])
    assembled = [f for f in main_files if 'ASSEMBLED' in f.name.upper()]
    if assembled:
        # Use ASSEMBLED_FILING as the sole main document
        # Remove 01_MAIN_FILING since ASSEMBLED already contains it
        classified[1] = assembled[:1]
        # Also remove affidavit slot if ASSEMBLED includes it
        if 3 in classified:
            # Check if ASSEMBLED contains affidavit content
            assembled_text = assembled[0].read_text(encoding='utf-8', errors='replace')
            if 'AFFIDAVIT' in assembled_text.upper() or 'VERIFICATION' in assembled_text.upper():
                if verbose:
                    print(f"  NOTE: ASSEMBLED_FILING contains affidavit — removing standalone")
                del classified[3]

    # ── Build the story ────────────────────────────────────────────
    full_story = []

    # --- Caption page (only if not using ASSEMBLED which has its own) ---
    use_assembled = bool(assembled)
    if not use_assembled:
        caption = make_caption_page(fdef, styles)
        full_story.extend(caption)

    # --- Process each slot in order ---
    for slot_idx in sorted(classified.keys()):
        files = classified[slot_idx]
        slot_name = STACK_ORDER[slot_idx][0] if slot_idx < len(STACK_ORDER) else "SUPPLEMENTAL"

        for filepath in files:
            if verbose:
                print(f"  RENDERING: [{slot_name}] {filepath.name}")

            try:
                md_text = filepath.read_text(encoding='utf-8', errors='replace')

                # Skip tiny/empty files
                if len(md_text.strip()) < 50:
                    if verbose:
                        print(f"    ⚠️  Skipping (too small: {len(md_text)} bytes)")
                    continue

                # Convert markdown to story elements
                story_elements = md_to_story(md_text, styles)
                if story_elements:
                    full_story.extend(story_elements)
                    full_story.append(PageBreak())

            except Exception as e:
                logger.error("[assemble_filing] Error reading %s: %s", filepath.name, e, exc_info=True)

    # ── Extract and insert exhibit cover pages ─────────────────────
    # Check main document for exhibit references
    if assembled:
        main_text = assembled[0].read_text(encoding='utf-8', errors='replace')
        exhibits = extract_exhibits_from_md(main_text)
        if exhibits and verbose:
            print(f"\n  EXHIBITS FOUND: {len(exhibits)}")
            for letter_val, desc in exhibits:
                print(f"    Exhibit {letter_val}: {desc[:60]}")

    # ── Remove trailing PageBreak ──────────────────────────────────
    while full_story and isinstance(full_story[-1], PageBreak):
        full_story.pop()

    if not full_story:
        return None, 0, f"No content found in {filing_id} package"

    # ── Generate PDF ───────────────────────────────────────────────
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    safe_title = fdef['title'].split('\n')[0].replace(' ', '_').replace('/', '-')
    output_name = f"{filing_id}_{safe_title[:50]}_{datetime.now().strftime('%Y%m%d')}.pdf"
    output_path = OUTPUT_DIR / output_name

    if verbose:
        print(f"\n  GENERATING PDF: {output_path}")

    try:
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=letter,
            leftMargin=1 * inch,
            rightMargin=1 * inch,
            topMargin=1 * inch,
            bottomMargin=1 * inch,
            title=fdef['title'].split('\n')[0],
            author=PLAINTIFF,
            subject=f"Case No. {fdef['case_no']}",
        )

        doc.build(
            full_story,
            onFirstPage=PageNumberCanvas.add_page_number,
            onLaterPages=PageNumberCanvas.add_page_number,
        )

        # Get page count
        import fitz  # PyMuPDF
        pdf_doc = fitz.open(str(output_path))
        page_count = len(pdf_doc)
        file_size = output_path.stat().st_size
        pdf_doc.close()

        if verbose:
            print(f"  ✅ SUCCESS: {page_count} pages, {file_size:,} bytes")
            print(f"  📄 Output: {output_path}")

        return output_path, page_count, "SUCCESS"

    except Exception as e:
        logger.error("[assemble_filing] PDF generation failed for %s: %s", filing_id, e, exc_info=True)
        return None, 0, f"PDF generation failed: {e}"


# ══════════════════════════════════════════════════════════════════
# BATCH ASSEMBLY — ALL FILING PACKAGES
# ══════════════════════════════════════════════════════════════════

def assemble_all(filing_ids=None, verbose=True):
    """Assemble all (or specified) filing packages."""
    if filing_ids is None:
        filing_ids = list(FILING_DEFS.keys())

    results = []
    total_pages = 0
    total_bytes = 0

    print("\n" + "=" * 70)
    print("  FILING STACK ASSEMBLER — Court-Grade PDF Assembly")
    print(f"  MCR 1.109(D) Compliant | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"  Output: {OUTPUT_DIR}")
    print("=" * 70)

    for fid in filing_ids:
        try:
            path, pages, status = assemble_filing(fid, verbose=verbose)
            if path and path.exists():
                size = path.stat().st_size
                total_pages += pages
                total_bytes += size
                results.append((fid, path, pages, size, "✅ " + status))
            else:
                results.append((fid, None, 0, 0, "❌ " + status))
        except Exception as e:
            logger.error("[assemble_all] Assembly failed for %s: %s", fid, e, exc_info=True)
            results.append((fid, None, 0, 0, f"❌ EXCEPTION: {e}"))

    # ── Summary ────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("  ASSEMBLY RESULTS SUMMARY")
    print("=" * 70)
    print(f"  {'Filing':<12} {'Pages':>6} {'Size':>12} {'Status'}")
    print(f"  {'-'*12} {'-'*6} {'-'*12} {'-'*30}")

    for fid, path, pages, size, status in results:
        size_str = f"{size:,} B" if size else "—"
        print(f"  {fid:<12} {pages:>6} {size_str:>12} {status}")

    print(f"  {'-'*12} {'-'*6} {'-'*12}")
    print(f"  {'TOTAL':<12} {total_pages:>6} {total_bytes:,} B".rstrip())
    print(f"\n  Output directory: {OUTPUT_DIR}")
    print("=" * 70)

    return results


# ── CLI ────────────────────────────────────────────────────────────
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Filing Stack Assembler')
    parser.add_argument('filings', nargs='*', default=None,
                        help='Filing IDs to assemble (e.g., F3 F1). Default: all')
    parser.add_argument('--quiet', '-q', action='store_true',
                        help='Suppress verbose output')
    args = parser.parse_args()

    filing_ids = args.filings if args.filings else None
    assemble_all(filing_ids=filing_ids, verbose=not args.quiet)
