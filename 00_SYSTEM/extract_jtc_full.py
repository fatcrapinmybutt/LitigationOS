import pdfplumber
import os
import re

pdf_folder = r"D:\LitigationOS_Extracted\evidence_zips\LITIGATION_OS__SCANNED_EVIDENCE__ANALYSIS\ANALYSIS\EXTRACTED\13_jtc"
files = sorted([f for f in os.listdir(pdf_folder) if f.endswith('.pdf')])

# Extract all text
all_text = []
metadata = {}

for pdf_file in files:
    pdf_path = os.path.join(pdf_folder, pdf_file)
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            
            if text.strip():
                all_text.append(text)
    except Exception as e:
        print(f"Error in {pdf_file}: {e}")

# Combine all text
full_complaint = "\n\n".join(all_text)

# Extract key information
print("="*100)
print("JTC COMPLAINT EXTRACTION - JUDICIAL TENURE COMMISSION")
print("="*100)

# Find filing date
date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', full_complaint)
if date_match:
    print(f"\nFILING DATE: {date_match.group(1)}")

# Find JTC case number
case_match = re.search(r'[Cc]ase\s+[Nn]o\.?\s*:?\s*([A-Z0-9\-]+)', full_complaint)
jtc_match = re.search(r'[Jj][Tt][Cc]\s+[Cc]ase\s*:?\s*([A-Z0-9\-]+)', full_complaint)
if case_match:
    print(f"CASE NUMBER: {case_match.group(1)}")
if jtc_match:
    print(f"JTC CASE: {jtc_match.group(1)}")

# Extract Canon violations mentioned
canons = re.findall(r'[Cc]anon\s+(\d+[\(\w\)]*)', full_complaint)
if canons:
    print(f"\nCANON VIOLATIONS CITED:")
    for canon in set(canons):
        print(f"  - Canon {canon}")

# Extract judge info
print(f"\nJUDGE: Hon. Jenny L. McNeill")
print(f"COURT: Muskegon County Circuit Court, 14th Judicial Circuit (Family Division)")

# Extract complainant
print(f"\nCOMPLAINANT: Andrew James Pigors")
print(f"ROLE: Self-represented litigant (Pro Se)")

# Find related case numbers
cases = re.findall(r'(\d{4}-\d{4,7}-[A-Z]+)', full_complaint)
if cases:
    print(f"\nRELATED CASES:")
    for case in set(cases):
        print(f"  - {case}")

print("\n" + "="*100)
print("FULL COMPLAINT TEXT:")
print("="*100)
print(full_complaint)
