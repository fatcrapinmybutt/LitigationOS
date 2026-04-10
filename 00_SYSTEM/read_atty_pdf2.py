import sys
try:
    import fitz  # PyMuPDF
    path = r"C:\Users\andre\Desktop\Assault_Battery_From_Attorney_Reports.pdf"
    doc = fitz.open(path)
    print(f"Pages: {len(doc)}")
    for i, page in enumerate(doc):
        text = page.get_text()
        sep = "=" * 60
        print(f"\n{sep}\nPAGE {i+1} ({len(text)} chars)\n{sep}\n{text[:3000]}")
except Exception as e:
    print(f"Error: {e}")
