import pdfplumber
import os

pdf_folder = r"D:\LitigationOS_Extracted\evidence_zips\LITIGATION_OS__SCANNED_EVIDENCE__ANALYSIS\ANALYSIS\EXTRACTED\13_jtc"
files = sorted([f for f in os.listdir(pdf_folder) if f.endswith('.pdf')])

print(f"Found {len(files)} PDF files\n")
print("="*100)

for pdf_file in files:
    pdf_path = os.path.join(pdf_folder, pdf_file)
    print(f"\n### {pdf_file} ###\n")
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            print(f"Pages: {len(pdf.pages)}")
            
            full_text = ""
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"
            
            if full_text.strip():
                # Show first 1000 chars and last 500 chars
                preview = full_text[:1200]
                print("\n--- EXTRACTED TEXT (first 1200 chars) ---")
                print(preview)
                if len(full_text) > 1200:
                    print(f"\n... [Content continues] ...\n")
                    print("--- END OF DOCUMENT (last 500 chars) ---")
                    print(full_text[-500:])
                print(f"\nTotal text length: {len(full_text)} characters")
            else:
                print("[No text extracted]")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "="*100)
