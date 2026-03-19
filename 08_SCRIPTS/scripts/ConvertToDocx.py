
from docx import Document
from pathlib import Path

folders = [
    "F:/OMNILITIGATION_SYSTEM/AffidavitDrafts/",
    "F:/OMNILITIGATION_SYSTEM/VerifiedComplaints/",
    "F:/OMNILITIGATION_SYSTEM/ProposedOrders/",
    "F:/OMNILITIGATION_SYSTEM/MotionsToShowCause/"
]

def convert_txt_to_docx(folder_path):
    folder = Path(folder_path)
    for txt_file in folder.glob("*.txt"):
        doc = Document()
        with open(txt_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        for line in lines:
            doc.add_paragraph(line.strip())
        docx_file = txt_file.with_suffix(".docx")
        doc.save(docx_file)
        print(f"✅ Converted: {docx_file}")

def main():
    for folder in folders:
        convert_txt_to_docx(folder)
    print("📄 All litigation drafts converted to DOCX.")

if __name__ == "__main__":
    main()
