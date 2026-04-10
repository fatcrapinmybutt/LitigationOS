import os
from pathlib import Path
from pypdf import PdfReader

def extract_pdf_text(pdf_path):
    """Extract text from PDF, return text and page count."""
    try:
        reader = PdfReader(pdf_path)
        num_pages = len(reader.pages)
        text = ""
        
        # Try to extract text from all pages
        for page_num, page in enumerate(reader.pages):
            extracted = page.extract_text()
            if extracted:
                text += f"--- PAGE {page_num + 1} ---\n{extracted}\n\n"
        
        return text, num_pages, bool(text.strip())
    except Exception as e:
        return f"[ERROR: {str(e)}]", 0, False

# Process main folder
main_folder = r"D:\LitigationOS_Extracted\evidence_zips\LITIGATION_OS__SCANNED_EVIDENCE__ANALYSIS\ANALYSIS\EXTRACTED\14_rusco_martini_emails"
nested_folder = r"D:\LitigationOS_Extracted\evidence_zips\LITIGATION_OS__SCANNED_EVIDENCE__ANALYSIS\ANALYSIS\EXTRACTED\NESTED_FROM_SCANNED300\SCANNEDruscomartiniemailsscannd_0028"

print("=" * 80)
print("MAIN FOLDER: 14_rusco_martini_emails")
print("=" * 80)

pdf_files = sorted(Path(main_folder).glob("*.pdf"))
for pdf_file in pdf_files:
    print(f"\n>>> FILE: {pdf_file.name} ({pdf_file.stat().st_size / 1024:.2f} KB)")
    text, num_pages, has_text = extract_pdf_text(str(pdf_file))
    print(f"    Pages: {num_pages} | Has extractable text: {has_text}")
    if has_text and len(text) < 2000:
        print(text)
    elif has_text:
        print(text[:1500])
    else:
        print("    [IMAGE-ONLY PDF - OCR NEEDED]")

print("\n" + "=" * 80)
print("NESTED FOLDER: SCANNEDruscomartiniemailsscannd_0028")
print("=" * 80)

pdf_files = sorted(Path(nested_folder).glob("*.pdf"))
for pdf_file in pdf_files:
    print(f"\n>>> FILE: {pdf_file.name} ({pdf_file.stat().st_size / 1024:.2f} KB)")
    text, num_pages, has_text = extract_pdf_text(str(pdf_file))
    print(f"    Pages: {num_pages} | Has extractable text: {has_text}")
    if has_text and len(text) < 2000:
        print(text)
    elif has_text:
        print(text[:1500])
    else:
        print("    [IMAGE-ONLY PDF - OCR NEEDED]")
