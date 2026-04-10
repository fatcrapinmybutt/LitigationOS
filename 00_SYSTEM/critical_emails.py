from pathlib import Path
from pypdf import PdfReader
import re

main_folder = r"D:\LitigationOS_Extracted\evidence_zips\LITIGATION_OS__SCANNED_EVIDENCE__ANALYSIS\ANALYSIS\EXTRACTED\14_rusco_martini_emails"

print("=" * 120)
print("CRITICAL EMAIL EVIDENCE - FULL TEXT EXTRACTION FOR LITIGATION")
print("=" * 120)

# Critical files
critical_files = [
    "ruscomartiniemailsscannd_0013.pdf",  # Martini ineffectiveness
    "ruscomartiniemailsscannd_0015.pdf",  # More Martini ineffectiveness
    "ruscomartiniemailsscannd_0017.pdf",  # Rusco ex parte forwarding to Martini
    "ruscomartiniemailsscannd_0024.pdf",  # Duplicate of 0017 with warrant context
]

for filename in critical_files:
    filepath = Path(main_folder) / filename
    if filepath.exists():
        reader = PdfReader(str(filepath))
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        
        print(f"\n{'='*120}")
        print(f"FILE: {filename}")
        print(f"{'='*120}")
        print(text)
        print("\n")
