"""Extract text from POST_EVICTION_Addendum .docx file."""
import sys
try:
    from docx import Document
except ImportError:
    print("ERROR: python-docx not installed. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "python-docx", "-q"])
    from docx import Document

docx_path = r"C:\Users\andre\LitigationOS\01_EVIDENCE\HOUSING\POST_EVICTION_Addendum_Facts_Timeline_Damages_2026-02-21.docx"

doc = Document(docx_path)
for i, para in enumerate(doc.paragraphs, 1):
    if para.text.strip():
        print(f"{i}. {para.text}")
