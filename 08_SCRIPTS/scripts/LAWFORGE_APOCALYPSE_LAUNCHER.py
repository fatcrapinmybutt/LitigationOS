#!/usr/bin/env python3
# LAWFORGE_APOCALYPSE_LAUNCHER.py
# FINAL DEPLOYER — Tier 7 Canon Strikeback

import os, re, json, pdfplumber, docx
from tqdm import tqdm
from datetime import datetime
from lexnlp.extract.en.segments.sentences import get_sentence_list
from lexnlp.extract.en.entities.nltk_re import get_persons

DRIVES = ["F:/", "D:/", "E:/", "Z:/"]
CANON_PATTERNS = {
    "Canon 1": r"(abuse of power|manipulat|coerc|fabricat)",
    "Canon 2A": r"(bias|favored|one-sided|frivolous|ignored)",
    "Canon 3B(6)": r"(muted|denied to speak|cut off|no argument)",
    "Canon 3B(7)": r"(ex parte|secret|no notice|off record)",
    "Canon 3C(1)(a)": r"(disqualify|conflict of interest|prejudic)"
}

violations = []

def extract_text(pdf_path):
    try:
        with pdfplumber.open(pdf_path) as pdf:
            return "\n".join(p.extract_text() or '' for p in pdf.pages)
    except Exception as e:
        return ""

def scan_pdf(file_path):
    text = extract_text(file_path)
    found = []
    if not text: return []
    sentences = list(get_sentence_list(text))
    persons = list(set(get_persons(text)))
    for canon, pat in CANON_PATTERNS.items():
        for sent in sentences:
            if re.search(pat, sent, re.IGNORECASE):
                found.append({
                    "canon": canon,
                    "match": sent.strip(),
                    "persons": persons
                })
    return found

def scan_all():
    for drive in DRIVES:
        for root, _, files in os.walk(drive):
            for f in files:
                if f.lower().endswith(".pdf"):
                    path = os.path.join(root, f)
                    result = scan_pdf(path)
                    if result:
                        violations.append({
                            "file": path,
                            "violations": result
                        })

def save_json():
    with open("violations_log.json", "w", encoding="utf-8") as f:
        json.dump(violations, f, indent=2)

def generate_affidavit():
    doc = docx.Document()
    doc.add_heading("Affidavit of Canon Violations", level=1)
    doc.add_paragraph("Affiant: Andrew J. Pigors")
    doc.add_paragraph(f"Date: {datetime.now().strftime('%Y-%m-%d')}\n")
    for v in violations:
        doc.add_heading(f"File: {v['file']}", level=2)
        for match in v['violations']:
            doc.add_paragraph(f"{match['canon']}: {match['match']}")
            if match['persons']:
                doc.add_paragraph(f"Involving: {', '.join(match['persons'])}")
    doc.add_paragraph("\nI swear under MCR 2.114(B) that this is true.")
    doc.add_paragraph("Signature: _____________________")
    doc.add_paragraph("Date: _____________________")
    doc.save("Canon_Violation_Affidavit.docx")

def generate_index():
    with open("exhibit_index.txt", "w", encoding="utf-8") as f:
        for i, entry in enumerate(violations, 1):
            f.write(f"Exhibit {i}: {entry['file']}\n")

def main():
    print("Scanning for Canon violations...")
    scan_all()
    print(f"Found in {len(violations)} files.")
    save_json()
    generate_affidavit()
    generate_index()
    print("Generated: affidavit, JSON log, exhibit index.")

if __name__ == "__main__":
    main()
