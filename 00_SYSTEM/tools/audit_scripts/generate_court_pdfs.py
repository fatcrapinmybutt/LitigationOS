#!/usr/bin/env python3
"""
Court-Ready PDF Package Generator for LitigationOS
===================================================
Generates two court-compliant PDF filing packages:
  Package 1: Housing (F1 + F2) — Shady Oaks / Homes of America / Alden Global
  Package 2: Custody/Bypass (F3-F10) — organized by court

Formatting: MCR 1.109 compliant (12pt Times New Roman, 1" margins, double-spaced)
"""

import os
import sys
import re

# Force UTF-8 stdout
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

import markdown2
from weasyprint import HTML, CSS
import fitz  # PyMuPDF for page counting and post-processing

BASE = r"C:\Users\andre\Desktop\LITIGATION_FILING_PACKAGE"
OUTPUT_DIR = os.path.join(BASE, "PDF_PACKAGES")

# ============================================================
# COURT-COMPLIANT CSS (MCR 1.109 / LCivR 10.1 / MCR 7.212)
# ============================================================
COURT_CSS = """
@page {
    size: letter;
    margin: 1in;
    @bottom-center {
        content: "Page " counter(page);
        font-family: "Times New Roman", Times, serif;
        font-size: 10pt;
        color: black;
    }
}

body {
    font-family: "Times New Roman", Times, serif;
    font-size: 12pt;
    line-height: 2;
    color: black;
    text-align: justify;
    orphans: 3;
    widows: 3;
}

/* Headings - court style */
h1 {
    font-size: 14pt;
    font-weight: bold;
    text-align: center;
    text-transform: uppercase;
    page-break-after: avoid;
    margin-top: 12pt;
    margin-bottom: 12pt;
    line-height: 1.5;
}

h2 {
    font-size: 13pt;
    font-weight: bold;
    text-align: left;
    page-break-after: avoid;
    margin-top: 12pt;
    margin-bottom: 6pt;
    line-height: 1.5;
}

h3 {
    font-size: 12pt;
    font-weight: bold;
    text-align: left;
    page-break-after: avoid;
    margin-top: 10pt;
    margin-bottom: 6pt;
    line-height: 1.5;
}

h4, h5, h6 {
    font-size: 12pt;
    font-weight: bold;
    page-break-after: avoid;
    margin-top: 8pt;
    margin-bottom: 4pt;
    line-height: 1.5;
}

p {
    margin-top: 0;
    margin-bottom: 6pt;
    text-indent: 0;
}

/* Block quotes - indented citations */
blockquote {
    margin-left: 0.5in;
    margin-right: 0.5in;
    font-size: 11pt;
    line-height: 1.5;
    font-style: italic;
    border-left: 2pt solid #666;
    padding-left: 12pt;
}

blockquote p {
    text-indent: 0;
}

/* Tables */
table {
    border-collapse: collapse;
    width: 100%;
    margin: 12pt 0;
    font-size: 10pt;
    line-height: 1.4;
    page-break-inside: avoid;
}

th, td {
    border: 1px solid #333;
    padding: 4pt 6pt;
    text-align: left;
    vertical-align: top;
}

th {
    background-color: #e8e8e8;
    font-weight: bold;
    font-size: 10pt;
}

/* Lists */
ul, ol {
    margin-top: 6pt;
    margin-bottom: 6pt;
    padding-left: 0.4in;
}

li {
    margin-bottom: 4pt;
    line-height: 1.8;
}

li p {
    text-indent: 0;
    margin-bottom: 2pt;
}

/* Horizontal rules */
hr {
    border: none;
    border-top: 1pt solid black;
    margin: 12pt 0;
}

/* Code blocks (for case citations etc) */
code {
    font-family: "Courier New", Courier, monospace;
    font-size: 10pt;
    background: #f5f5f5;
    padding: 1pt 3pt;
}

pre {
    font-family: "Courier New", Courier, monospace;
    font-size: 9pt;
    background: #f5f5f5;
    padding: 8pt;
    border: 1px solid #ccc;
    white-space: pre-wrap;
    line-height: 1.3;
    page-break-inside: avoid;
}

/* Strong emphasis */
strong { font-weight: bold; }
em { font-style: italic; }

/* Cover page styling */
.cover-page {
    page-break-after: always;
    text-align: center;
    padding-top: 1.5in;
}

.cover-page h1 {
    font-size: 18pt;
    text-transform: uppercase;
    margin-bottom: 0.5in;
    letter-spacing: 1pt;
}

.cover-page .subtitle {
    font-size: 14pt;
    margin-bottom: 0.3in;
}

.cover-page .case-info {
    font-size: 12pt;
    margin-top: 0.5in;
    line-height: 1.8;
}

.cover-page .filer-info {
    margin-top: 1.5in;
    font-size: 11pt;
    line-height: 1.6;
}

/* Filing divider pages */
.filing-divider {
    page-break-before: always;
    text-align: center;
    padding-top: 2.5in;
    font-size: 16pt;
    font-weight: bold;
    text-transform: uppercase;
    letter-spacing: 1pt;
}

.filing-divider .court-name {
    font-size: 12pt;
    font-weight: normal;
    margin-top: 0.3in;
    text-transform: none;
    color: #333;
}

/* Exhibit header */
.exhibit-header {
    page-break-before: always;
    text-align: center;
    padding-top: 2in;
    font-size: 16pt;
    font-weight: bold;
    text-transform: uppercase;
    border: 2pt solid black;
    margin: 0 1in;
    padding: 1.5in 0.5in 0.5in 0.5in;
}

.exhibit-label {
    font-size: 20pt;
    font-weight: bold;
    margin-bottom: 0.3in;
}

.exhibit-desc {
    font-size: 14pt;
    font-weight: normal;
    margin-top: 0.3in;
}

/* Table of contents */
.toc {
    page-break-after: always;
}

.toc h2 {
    text-align: center;
    font-size: 14pt;
    margin-bottom: 24pt;
}

.toc-entry {
    margin: 6pt 0;
    line-height: 1.5;
}

.toc-entry .page-ref {
    float: right;
}

/* Section for each filing's content */
.filing-content {
    page-break-before: always;
}

/* Signature block */
.signature-block {
    margin-top: 1in;
    margin-left: 3in;
    line-height: 1.5;
}
"""


def read_md(filepath):
    """Read markdown file with UTF-8."""
    if not os.path.exists(filepath):
        return ""
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()


def md_to_html(md_content):
    """Convert markdown to HTML."""
    if not md_content or len(md_content.strip()) < 10:
        return ""
    html = markdown2.markdown(md_content, extras=[
        'tables', 'fenced-code-blocks', 'footnotes',
        'header-ids', 'cuddled-lists', 'markdown-in-html',
        'strike', 'break-on-newline'
    ])
    return html


def clean_markdown_for_court(md_content):
    """Pre-process markdown to improve court document rendering."""
    # Remove any HTML comments
    md_content = re.sub(r'<!--.*?-->', '', md_content, flags=re.DOTALL)
    # Remove excessive blank lines (max 2)
    md_content = re.sub(r'\n{4,}', '\n\n\n', md_content)
    # Convert markdown [PLACEHOLDER] markers to bold red text
    md_content = re.sub(r'\[([A-Z_]+(?:\s*[-—]\s*[A-Z_]+)*)\]', 
                        r'**[\1]**', md_content)
    return md_content


def build_cover_page(title, subtitle, case_numbers, parties_text, court_text):
    """Generate cover page HTML."""
    return f"""
    <div class="cover-page">
        <h1>{title}</h1>
        <div class="subtitle">{subtitle}</div>
        <hr style="width: 50%; margin: 0.3in auto;">
        <div class="case-info">
            <p><strong>{court_text}</strong></p>
            <p><strong>{case_numbers}</strong></p>
            <br>
            <p style="white-space: pre-line;">{parties_text}</p>
        </div>
        <div class="filer-info">
            <p><strong>Filed by:</strong></p>
            <p>Andrew James Pigors, <em>Pro Se</em></p>
            <p>1977 Whitehall Road, Lot 17</p>
            <p>North Muskegon, MI 49445</p>
            <p>(231) 903-5690</p>
            <p>andrewjpigors@gmail.com</p>
        </div>
    </div>
    """


def build_toc(filings):
    """Build a table of contents."""
    html = '<div class="toc">\n'
    html += '<h2>TABLE OF CONTENTS</h2>\n'
    for i, f in enumerate(filings, 1):
        html += f'<div class="toc-entry"><strong>{f["id"]}.</strong> {f["title"]}</div>\n'
        if f.get('court_note'):
            html += f'<div class="toc-entry" style="margin-left: 0.5in; font-size: 11pt; color: #555;"><em>{f["court_note"]}</em></div>\n'
    html += '</div>\n'
    return html


def build_filing_section(filing, base_dir):
    """Build complete HTML for one filing including all supporting docs."""
    pkg_dir = os.path.join(base_dir, filing['dir'])
    
    # Filing divider page
    court_note = f'<div class="court-name">{filing.get("court_note", "")}</div>' if filing.get('court_note') else ''
    html = f'<div class="filing-divider">{filing["id"]}<br>{filing["title"]}{court_note}</div>\n'
    
    # Main filing content
    main_md = read_md(os.path.join(pkg_dir, '01_MAIN_FILING.md'))
    main_md = clean_markdown_for_court(main_md)
    html += '<div class="filing-content">\n'
    html += md_to_html(main_md)
    html += '</div>\n'
    
    # Affidavit (Exhibit A)
    aff_md = read_md(os.path.join(pkg_dir, '02_AFFIDAVIT.md'))
    if aff_md and len(aff_md.strip()) > 50:
        html += '<div class="exhibit-header">'
        html += '<div class="exhibit-label">EXHIBIT A</div>'
        html += '<div class="exhibit-desc">AFFIDAVIT OF ANDREW JAMES PIGORS</div>'
        html += '</div>\n'
        html += '<div class="filing-content">\n'
        html += md_to_html(clean_markdown_for_court(aff_md))
        html += '</div>\n'
    
    # Exhibit Index
    exhibit_md = read_md(os.path.join(pkg_dir, '03_EXHIBIT_INDEX.md'))
    if exhibit_md and len(exhibit_md.strip()) > 50:
        html += '<div style="page-break-before: always;">\n'
        html += '<h2 style="text-align: center;">EXHIBIT INDEX</h2>\n'
        html += md_to_html(clean_markdown_for_court(exhibit_md))
        html += '</div>\n'
    
    # Certificate of Service
    cert_md = read_md(os.path.join(pkg_dir, '04_CERTIFICATE_OF_SERVICE.md'))
    if cert_md and len(cert_md.strip()) > 50:
        html += '<div style="page-break-before: always;">\n'
        html += md_to_html(clean_markdown_for_court(cert_md))
        html += '</div>\n'
    
    return html


def generate_package(config):
    """Generate one complete PDF package."""
    title = config['title']
    output_path = config['output_path']
    filings = config['filings']
    
    print(f"\n{'='*60}")
    print(f"  GENERATING: {title}")
    print(f"  Output: {output_path}")
    print(f"  Filings: {len(filings)}")
    print(f"{'='*60}")
    
    # Build full HTML document
    html_parts = []
    html_parts.append('<!DOCTYPE html>\n<html lang="en">\n<head>\n')
    html_parts.append('<meta charset="utf-8">\n')
    html_parts.append(f'<title>{title}</title>\n')
    html_parts.append('</head>\n<body>\n')
    
    # Cover page
    html_parts.append(build_cover_page(
        config['title'], config.get('subtitle', ''),
        config['case_numbers'], config['parties'], config['court']
    ))
    
    # Table of contents
    html_parts.append(build_toc(filings))
    
    # Each filing
    for filing in filings:
        print(f"  Processing: {filing['dir']}...")
        html_parts.append(build_filing_section(filing, BASE))
    
    html_parts.append('</body>\n</html>')
    html_content = ''.join(html_parts)
    
    # Save HTML for debugging
    html_path = output_path.replace('.pdf', '.html')
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"  HTML intermediate: {html_path}")
    
    # Render PDF
    print(f"  Rendering PDF with WeasyPrint (this may take a minute)...")
    try:
        doc = HTML(string=html_content, base_url=BASE)
        doc.write_pdf(output_path, stylesheets=[CSS(string=COURT_CSS)])
    except Exception as e:
        print(f"  ERROR during PDF rendering: {e}")
        print(f"  Trying fallback with simpler CSS...")
        # Fallback: simpler CSS
        simple_css = """
        @page { size: letter; margin: 1in; }
        body { font-family: serif; font-size: 12pt; line-height: 2; }
        h1 { font-size: 14pt; text-align: center; font-weight: bold; }
        h2 { font-size: 13pt; font-weight: bold; }
        h3 { font-size: 12pt; font-weight: bold; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid black; padding: 4pt; }
        .cover-page { page-break-after: always; text-align: center; padding-top: 2in; }
        .filing-divider { page-break-before: always; text-align: center; padding-top: 3in; font-size: 16pt; font-weight: bold; }
        .exhibit-header { page-break-before: always; text-align: center; padding-top: 2in; font-size: 16pt; font-weight: bold; border: 2pt solid black; }
        .filing-content { page-break-before: always; }
        .toc { page-break-after: always; }
        """
        doc = HTML(string=html_content, base_url=BASE)
        doc.write_pdf(output_path, stylesheets=[CSS(string=simple_css)])
    
    # Report results
    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    pdf = fitz.open(output_path)
    page_count = pdf.page_count
    pdf.close()
    
    print(f"\n  ✅ COMPLETE: {output_path}")
    print(f"     Pages: {page_count}")
    print(f"     Size:  {size_mb:.1f} MB")
    
    return {'path': output_path, 'pages': page_count, 'size_mb': size_mb}


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    print("=" * 60)
    print("  LITIGATIONOS COURT-READY PDF GENERATOR")
    print("  MCR 1.109 Compliant | 12pt | 1\" Margins | Double-Spaced")
    print("=" * 60)
    
    # ============================================================
    # PACKAGE 1: HOUSING
    # Shady Oaks MHP LLC / Homes of America LLC / Alden Global
    # Case No. 2025-002760-CZ
    # ============================================================
    pkg1_config = {
        'title': 'MASTER FILING PACKAGE — HOUSING',
        'subtitle': 'Shady Oaks MHP / Homes of America / Alden Global Capital',
        'case_numbers': 'Case No. 2025-002760-CZ',
        'parties': ('ANDREW JAMES PIGORS,\n'
                     '    Plaintiff,\n\n'
                     'v.\n\n'
                     'SHADY OAKS MHP LLC, HOMES OF AMERICA LLC,\n'
                     'ALDEN GLOBAL CAPITAL LLC,\n'
                     '    Defendants.'),
        'court': '14th Circuit Court, Muskegon County, Michigan',
        'output_path': os.path.join(OUTPUT_DIR, 'PACKAGE_1_HOUSING_SHADY_OAKS.pdf'),
        'filings': [
            {
                'dir': 'PKG_F1_EMERGENCY_TRO',
                'id': 'F1',
                'title': 'EMERGENCY TEMPORARY RESTRAINING ORDER',
                'court_note': '14th Circuit Court — Emergency Filing'
            },
            {
                'dir': 'PKG_F2_SHADY_OAKS_COMPLAINT',
                'id': 'F2',
                'title': 'VERIFIED COMPLAINT (NINE COUNTS)',
                'court_note': '14th Circuit Court — Civil Division'
            },
        ]
    }
    
    # ============================================================
    # PACKAGE 2: CUSTODY / BYPASS MUSKEGON
    # Organized by court: Federal → MSC → COA → JTC → 14th Circuit
    # ============================================================
    pkg2_config = {
        'title': 'MASTER FILING PACKAGE — CUSTODY & BYPASS',
        'subtitle': 'Pigors v. Watson — Multi-Court Filing Strategy',
        'case_numbers': 'Cases: 2024-001507-DC | 2023-5907-PP | COA 366810',
        'parties': ('ANDREW JAMES PIGORS,\n'
                     '    Plaintiff / Appellant,\n\n'
                     'v.\n\n'
                     'EMILY A. WATSON,\n'
                     '    Defendant / Appellee,\n\n'
                     'Hon. JENNY L. McNEILL,\n'
                     '    Respondent (§1983, MSC, JTC)'),
        'court': 'USDC WDMI • MSC • COA • JTC • 14th Circuit Court',
        'output_path': os.path.join(OUTPUT_DIR, 'PACKAGE_2_CUSTODY_BYPASS.pdf'),
        'filings': [
            # --- FEDERAL COURT (highest jurisdiction first) ---
            {
                'dir': 'PKG_F4_FEDERAL_S1983_COMPLAINT',
                'id': 'F4',
                'title': '42 U.S.C. §1983 CIVIL RIGHTS COMPLAINT',
                'court_note': 'United States District Court, Western District of Michigan'
            },
            # --- MICHIGAN SUPREME COURT ---
            {
                'dir': 'PKG_F5_MSC_ORIGINAL_ACTION',
                'id': 'F5',
                'title': 'COMPLAINT FOR SUPERINTENDING CONTROL',
                'court_note': 'Michigan Supreme Court — Original Jurisdiction'
            },
            # --- COURT OF APPEALS ---
            {
                'dir': 'PKG_F9_COA_BRIEF_ON_APPEAL',
                'id': 'F9',
                'title': 'BRIEF ON APPEAL — COA No. 366810',
                'court_note': 'Michigan Court of Appeals'
            },
            {
                'dir': 'PKG_F10_COA_EMERGENCY_MOTION',
                'id': 'F10',
                'title': 'EMERGENCY MOTION FOR IMMEDIATE STAY',
                'court_note': 'Michigan Court of Appeals'
            },
            # --- JUDICIAL TENURE COMMISSION ---
            {
                'dir': 'PKG_F6_JTC_COMPLAINT',
                'id': 'F6',
                'title': 'REQUEST FOR INVESTIGATION',
                'court_note': 'Judicial Tenure Commission, Detroit (Physical Mail Only)'
            },
            # --- 14TH CIRCUIT (Disqualification — must file locally) ---
            {
                'dir': 'PKG_F3_DISQUALIFICATION_MCR_2003',
                'id': 'F3',
                'title': 'MOTION FOR DISQUALIFICATION — MCR 2.003',
                'court_note': '14th Circuit Court, Family Division'
            },
            # --- 14TH CIRCUIT (Custody modification) ---
            {
                'dir': 'PKG_F7_CUSTODY_MODIFICATION',
                'id': 'F7',
                'title': 'MOTION TO MODIFY CUSTODY / PARENTING TIME',
                'court_note': '14th Circuit Court, Family Division'
            },
            # --- 14TH CIRCUIT (PPO termination) ---
            {
                'dir': 'PKG_F8_PPO_TERMINATION',
                'id': 'F8',
                'title': 'MOTION TO TERMINATE PERSONAL PROTECTION ORDER',
                'court_note': '14th Circuit Court, Family Division'
            },
        ]
    }
    
    # Generate both packages
    results = []
    
    result1 = generate_package(pkg1_config)
    results.append(('HOUSING', result1))
    
    result2 = generate_package(pkg2_config)
    results.append(('CUSTODY', result2))
    
    # Final summary
    print(f"\n{'='*60}")
    print(f"  ✅ ALL PACKAGES GENERATED SUCCESSFULLY")
    print(f"{'='*60}")
    for name, r in results:
        print(f"  {name}: {r['pages']} pages, {r['size_mb']:.1f} MB")
        print(f"    → {r['path']}")
    print(f"\n  Output directory: {OUTPUT_DIR}")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
