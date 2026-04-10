import os
import re
from pathlib import Path
from pypdf import PdfReader
from collections import defaultdict

def extract_email_metadata(text):
    """Extract email metadata (date, from, to, subject)."""
    patterns = {
        'from': r'From:\s*(.+?)(?:\nSent:|To:|$)',
        'to': r'To:\s*(.+?)(?:\nCc:|Subject:|$)',
        'subject': r'Subject:\s*(.+?)(?:\n|$)',
        'date': r'(Mon|Tue|Wed|Thu|Fri|Sat|Sun),\s+(\w+\s+\d+,\s+\d{4})\s+at\s+([\d:]+\s+[AP]M)',
    }
    
    metadata = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
        if match:
            metadata[key] = match.group(1) if key != 'date' else f"{match.group(2)} {match.group(3)}"
    
    return metadata

def extract_key_quotes(text):
    """Extract important quotes and statements."""
    quotes = []
    
    # Key phrases to extract
    key_phrases = [
        r'All prosecutor is asking.*?(?=\n\n|\Z)',
        r'You will not interrupt.*?(?=\n\n|\Z)',
        r'Judge could still decide otherwise',
        r'I do not accept filing',
        r'The Judge does not look at them until they are admitted',
        r'off.?record',
        r'ex parte',
        r'chambers',
    ]
    
    for pattern in key_phrases:
        matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
        quotes.extend(matches)
    
    return quotes

# Process PDFs
main_folder = r"D:\LitigationOS_Extracted\evidence_zips\LITIGATION_OS__SCANNED_EVIDENCE__ANALYSIS\ANALYSIS\EXTRACTED\14_rusco_martini_emails"

print("=" * 100)
print("RUSCO + MARTINI EMAIL EVIDENCE - COMPREHENSIVE ANALYSIS")
print("=" * 100)

emails_by_date = defaultdict(list)
ex_parte_evidence = []
ineffective_assistance = []
judge_interference = []

pdf_files = sorted(Path(main_folder).glob("*.pdf"))

for pdf_file in pdf_files:
    reader = PdfReader(str(pdf_file))
    full_text = ""
    for page in reader.pages:
        full_text += page.extract_text() + "\n"
    
    metadata = extract_email_metadata(full_text)
    quotes = extract_key_quotes(full_text)
    
    # Flag ex parte issues
    if 'mandi martini' in full_text.lower() and 'rusco' in full_text.lower():
        if 'judge' in full_text.lower() or 'court' in full_text.lower():
            ex_parte_evidence.append({
                'file': pdf_file.name,
                'summary': f"Communication involving Martini + Rusco about court/judge matters",
                'date': metadata.get('date', 'N/A'),
                'from': metadata.get('from', 'N/A'),
            })
    
    # Flag Martini's ineffective assistance
    if 'mandi martini' in full_text.lower():
        if any(phrase in full_text.lower() for phrase in ['not interrupt', 'lecture', 'no mood', 'jail']):
            ineffective_assistance.append({
                'file': pdf_file.name,
                'excerpt': [q for q in quotes if q][:1],
                'date': metadata.get('date', 'N/A'),
            })
    
    # Flag judge interference via Rusco
    if 'rusco' in full_text.lower() and 'order' in full_text.lower():
        judge_interference.append({
            'file': pdf_file.name,
            'date': metadata.get('date', 'N/A'),
            'subject': metadata.get('subject', 'N/A'),
        })

print("\n1. EX PARTE EVIDENCE (Judge''s Secretary + Opposing Counsel)")
print("-" * 100)
for item in ex_parte_evidence:
    print(f"FILE: {item['file']}")
    print(f"  Date: {item['date']}")
    print(f"  Summary: {item['summary']}")
    print()

print("\n2. MANDI MARTINI''S INEFFECTIVE ASSISTANCE")
print("-" * 100)
for item in ineffective_assistance:
    print(f"FILE: {item['file']}")
    print(f"  Date: {item['date']}")
    if item['excerpt']:
        print(f"  Key Quote: {item['excerpt'][0][:150]}...")
    print()

print("\n3. JUDGE INTERFERENCE THROUGH SECRETARY")
print("-" * 100)
for item in judge_interference:
    print(f"FILE: {item['file']}")
    print(f"  Date: {item['date']}")
    print(f"  Subject: {item['subject']}")
    print()
