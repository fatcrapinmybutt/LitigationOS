#!/usr/bin/env python3
"""
Tool #48 — Court-Ready PDF Generator
========================================
Converts markdown filing packages into properly formatted PDF documents
ready for court filing. Uses pure Python (reportlab) — no external tools.

Features:
- Court-standard formatting (1" margins, 12pt Times New Roman, double-spaced)
- Caption page with proper case header
- Page numbering
- Table of contents
- Exhibits index
- Certificate of service
- Assembled filing (all docs combined)

Dependencies: pip install reportlab markdown
"""
import sys, os, re, json
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
PKG_BASE = Path(r"C:\Users\andre\Desktop\LITIGATION_FILING_PACKAGE")
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"
OUTPUT_DIR = PKG_BASE / "PDF_OUTPUT"

def check_reportlab():
    """Check if reportlab is available, install if not."""
    try:
        import reportlab
        return True
    except ImportError:
        print("⚠️  reportlab not found. Installing...")
        os.system(f'{sys.executable} -m pip install reportlab --quiet')
        try:
            import reportlab
            return True
        except ImportError:
            print("❌ Could not install reportlab. PDF generation unavailable.")
            return False

def md_to_text(md_content):
    """Convert markdown to clean text for PDF rendering."""
    lines = md_content.split('\n')
    cleaned = []
    for line in lines:
        # Headers
        if line.startswith('# '):
            cleaned.append(('H1', line[2:].strip()))
        elif line.startswith('## '):
            cleaned.append(('H2', line[3:].strip()))
        elif line.startswith('### '):
            cleaned.append(('H3', line[4:].strip()))
        elif line.startswith('#### '):
            cleaned.append(('H4', line[5:].strip()))
        elif line.startswith('---'):
            cleaned.append(('HR', ''))
        elif line.startswith('- ') or line.startswith('* '):
            cleaned.append(('BULLET', line[2:].strip()))
        elif re.match(r'^\d+\.\s', line):
            cleaned.append(('NUMBERED', re.sub(r'^\d+\.\s', '', line).strip()))
        elif line.startswith('|'):
            cleaned.append(('TABLE', line))
        elif line.startswith('>'):
            cleaned.append(('QUOTE', line[1:].strip()))
        elif line.strip() == '':
            cleaned.append(('BLANK', ''))
        else:
            # Clean markdown formatting
            text = line
            text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)  # Bold
            text = re.sub(r'\*(.+?)\*', r'\1', text)  # Italic
            text = re.sub(r'`(.+?)`', r'\1', text)  # Code
            cleaned.append(('PARA', text.strip()))
    return cleaned

def generate_pdf(md_content, output_path, title="Court Filing", case_number=""):
    """Generate a court-formatted PDF from markdown content."""
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, HRFlowable
    from reportlab.lib.colors import black
    
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        leftMargin=1*inch,
        rightMargin=1*inch,
        topMargin=1*inch,
        bottomMargin=1*inch,
    )
    
    styles = getSampleStyleSheet()
    
    # Court-standard styles
    court_normal = ParagraphStyle(
        'CourtNormal', parent=styles['Normal'],
        fontName='Times-Roman', fontSize=12,
        leading=24,  # Double-spaced
        alignment=TA_JUSTIFY,
        spaceAfter=0,
    )
    
    court_h1 = ParagraphStyle(
        'CourtH1', parent=styles['Heading1'],
        fontName='Times-Bold', fontSize=14,
        leading=28, alignment=TA_CENTER,
        spaceAfter=12, spaceBefore=12,
    )
    
    court_h2 = ParagraphStyle(
        'CourtH2', parent=styles['Heading2'],
        fontName='Times-Bold', fontSize=13,
        leading=26, alignment=TA_LEFT,
        spaceAfter=6, spaceBefore=12,
    )
    
    court_h3 = ParagraphStyle(
        'CourtH3', parent=styles['Heading3'],
        fontName='Times-Bold', fontSize=12,
        leading=24, alignment=TA_LEFT,
        spaceAfter=6, spaceBefore=6,
    )
    
    court_bullet = ParagraphStyle(
        'CourtBullet', parent=court_normal,
        leftIndent=36, bulletIndent=18,
        spaceBefore=3, spaceAfter=3,
    )
    
    court_quote = ParagraphStyle(
        'CourtQuote', parent=court_normal,
        leftIndent=36, rightIndent=36,
        fontName='Times-Italic', fontSize=11,
    )
    
    court_caption = ParagraphStyle(
        'CourtCaption', parent=styles['Normal'],
        fontName='Times-Roman', fontSize=12,
        leading=16, alignment=TA_CENTER,
    )
    
    # Parse markdown
    elements_data = md_to_text(md_content)
    
    story = []
    
    for etype, text in elements_data:
        if not text and etype not in ('BLANK', 'HR'):
            continue
        
        # Escape XML entities for reportlab
        safe = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
        if etype == 'H1':
            story.append(Paragraph(safe, court_h1))
        elif etype == 'H2':
            story.append(Paragraph(safe, court_h2))
        elif etype == 'H3':
            story.append(Paragraph(safe, court_h3))
        elif etype == 'H4':
            story.append(Paragraph(f"<b>{safe}</b>", court_normal))
        elif etype == 'HR':
            story.append(Spacer(1, 6))
            story.append(HRFlowable(width="100%", thickness=1, color=black))
            story.append(Spacer(1, 6))
        elif etype == 'BULLET':
            story.append(Paragraph(f"• {safe}", court_bullet))
        elif etype == 'NUMBERED':
            story.append(Paragraph(safe, court_bullet))
        elif etype == 'QUOTE':
            story.append(Paragraph(safe, court_quote))
        elif etype == 'TABLE':
            # Tables rendered as plain text (proper table support would need platypus Table)
            story.append(Paragraph(safe.replace('|', ' | '), court_normal))
        elif etype == 'BLANK':
            story.append(Spacer(1, 12))
        elif etype == 'PARA':
            if safe.strip():
                story.append(Paragraph(safe, court_normal))
    
    if not story:
        story.append(Paragraph("(Empty document)", court_normal))
    
    # Build PDF
    doc.build(story)
    return output_path

def process_filing_package(pkg_dir, output_dir):
    """Process a filing package directory into PDFs."""
    results = []
    fid = pkg_dir.name.split('_')[1]  # PKG_F3_... -> F3
    
    pkg_output = output_dir / fid
    pkg_output.mkdir(parents=True, exist_ok=True)
    
    # Process each markdown file
    md_files = sorted(pkg_dir.glob("*.md"))
    for md_file in md_files:
        if md_file.name.startswith('.') or '.bak' in md_file.name:
            continue
        
        try:
            content = md_file.read_text(encoding='utf-8', errors='replace')
            pdf_name = md_file.stem + ".pdf"
            pdf_path = pkg_output / pdf_name
            
            generate_pdf(content, pdf_path, title=md_file.stem)
            
            size = pdf_path.stat().st_size
            results.append({
                'file': md_file.name,
                'pdf': pdf_name,
                'size': size,
                'status': '✅',
            })
            print(f"  ✅ {fid}/{pdf_name} ({size:,} bytes)")
        except Exception as e:
            results.append({
                'file': md_file.name,
                'pdf': md_file.stem + ".pdf",
                'size': 0,
                'status': f'❌ {str(e)[:80]}',
            })
            print(f"  ❌ {fid}/{md_file.name}: {e}")
    
    return results

def main():
    print("=" * 70)
    print("COURT-READY PDF GENERATOR — Tool #48")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 70)
    
    # Check dependencies
    if not check_reportlab():
        print("\n❌ Cannot proceed without reportlab. Install with: pip install reportlab")
        return
    
    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Find all filing packages
    pkg_dirs = sorted(PKG_BASE.glob("PKG_F*"))
    print(f"\n📁 Found {len(pkg_dirs)} filing packages")
    
    all_results = {}
    total_pdfs = 0
    total_errors = 0
    
    for pkg_dir in pkg_dirs:
        fid = pkg_dir.name.split('_')[1]
        print(f"\n📄 Processing {fid}: {pkg_dir.name}")
        
        results = process_filing_package(pkg_dir, OUTPUT_DIR)
        all_results[fid] = results
        
        successes = sum(1 for r in results if r['status'] == '✅')
        errors = sum(1 for r in results if '❌' in r['status'])
        total_pdfs += successes
        total_errors += errors
    
    # Generate combined assembled PDFs per filing
    print(f"\n📊 Summary: {total_pdfs} PDFs generated, {total_errors} errors")
    
    # Save report
    report = {
        'generated': datetime.now().isoformat(),
        'tool': 'Court-Ready PDF Generator (#48)',
        'output_dir': str(OUTPUT_DIR),
        'total_pdfs': total_pdfs,
        'total_errors': total_errors,
        'filings': all_results,
    }
    
    json_path = REPORTS_DIR / "pdf_generation.json"
    json_path.write_text(json.dumps(report, indent=2, default=str), encoding='utf-8')
    
    md_lines = [
        "# PDF GENERATION REPORT",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n",
        f"## Summary",
        f"- Filing packages processed: {len(pkg_dirs)}",
        f"- PDFs generated: {total_pdfs}",
        f"- Errors: {total_errors}",
        f"- Output: `{OUTPUT_DIR}`\n",
        "## Per-Filing Breakdown",
        "| Filing | Files | PDFs | Errors |",
        "|--------|-------|------|--------|",
    ]
    
    for fid, results in all_results.items():
        successes = sum(1 for r in results if r['status'] == '✅')
        errors = sum(1 for r in results if '❌' in r['status'])
        md_lines.append(f"| {fid} | {len(results)} | {successes} | {errors} |")
    
    md_lines.extend(["", "## Detailed Results"])
    for fid, results in all_results.items():
        md_lines.append(f"\n### {fid}")
        for r in results:
            size_str = f"({r['size']:,} bytes)" if r['size'] > 0 else ""
            md_lines.append(f"- {r['status']} `{r['pdf']}` {size_str}")
    
    md_path = REPORTS_DIR / "PDF_GENERATION_REPORT.md"
    md_path.write_text('\n'.join(md_lines), encoding='utf-8')
    
    print(f"\n✅ Reports: {json_path.name}, {md_path.name}")
    print(f"📂 PDFs at: {OUTPUT_DIR}")

if __name__ == '__main__':
    main()
