import os, io, tempfile
from typing import Optional

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    HAVE_RL = True
except Exception:
    HAVE_RL = False

try:
    import PyPDF2
    HAVE_PYPDF = True
except Exception:
    HAVE_PYPDF = False

def _overlay_pdf(width, height, stamp_bottom_right: Optional[str], stamp_top_right: Optional[str]) -> bytes:
    buf = io.BytesIO()
    if not HAVE_RL:
        return b""
    c = canvas.Canvas(buf, pagesize=(width, height))
    font_size = 10
    c.setFont("Helvetica", font_size)
    margin = 0.35 * inch
    if stamp_bottom_right:
        text = stamp_bottom_right
        tw = c.stringWidth(text, "Helvetica", font_size)
        c.drawString(width - tw - margin, margin, text)
    if stamp_top_right:
        text2 = stamp_top_right
        tw2 = c.stringWidth(text2, "Helvetica", font_size)
        c.drawString(width - tw2 - margin, height - (margin + 12), text2)
    c.showPage()
    c.save()
    return buf.getvalue()

def stamp_pdf(src_pdf: str, out_pdf: str, bottom_right: Optional[str]=None, top_right: Optional[str]=None) -> str:
    """
    Stamps text onto each page. Requires reportlab + PyPDF2. If unavailable, copies through.
    """
    if not (HAVE_PYPDF and HAVE_RL):
        # pass-through
        import shutil
        shutil.copyfile(src_pdf, out_pdf)
        return out_pdf
    reader = PyPDF2.PdfReader(open(src_pdf, "rb"))
    writer = PyPDF2.PdfWriter()
    for page in reader.pages:
        mb = page.mediabox
        width = float(mb.width)
        height = float(mb.height)
        ov_bytes = _overlay_pdf(width, height, bottom_right, top_right)
        if ov_bytes:
            ov_reader = PyPDF2.PdfReader(io.BytesIO(ov_bytes))
            ov_page = ov_reader.pages[0]
            page.merge_page(ov_page)
        writer.add_page(page)
    with open(out_pdf, "wb") as f:
        writer.write(f)
    return out_pdf
