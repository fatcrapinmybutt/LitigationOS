import pypdfium2 as pdfium
import sys

path = r"C:\Users\andre\Desktop\Assault_Battery_From_Attorney_Reports.pdf"
doc = pdfium.PdfDocument(path)
print(f"Pages: {len(doc)}")
for i in range(len(doc)):
    page = doc[i]
    text = page.get_textpage().get_text_range()
    sep = "=" * 60
    print(f"\n{sep}\nPAGE {i+1}\n{sep}\n{text}")
