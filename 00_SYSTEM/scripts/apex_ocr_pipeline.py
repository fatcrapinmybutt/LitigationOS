#!/usr/bin/env python3
"""
APEX OCR Pipeline v1.1
Processes 958+ image-only PDFs via Tesseract OCR → brain DB
Two-pass: fast PyMuPDF text check → Tesseract OCR on image-only pages
"""
import sys
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace', buffering=1)

import sqlite3
import json
import os
import re
import hashlib
from pathlib import Path
from datetime import datetime

try:
    import fitz  # PyMuPDF
except ImportError:
    print("ERROR: PyMuPDF not installed. Run: pip install PyMuPDF")
    sys.exit(1)

try:
    from PIL import Image
    import pytesseract
except ImportError:
    print("ERROR: Pillow or pytesseract not installed.")
    print("  pip install Pillow pytesseract")
    print("  Also install Tesseract-OCR: https://github.com/UB-Mannheim/tesseract/wiki")
    sys.exit(1)

BRAIN_DB = r'C:\Users\andre\LitigationOS\00_SYSTEM\brains\chat_intelligence_brain.db'
TESSERACT_CMD = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

# MEEK lane detection patterns (same as apex_chat_extractor.py)
MEEK_PATTERNS = {
    'E': re.compile(r'(?i)(mcneill|judicial.?misconduct|jtc|bias|ex\s*parte|canon|disqualif)', re.IGNORECASE),
    'D': re.compile(r'(?i)(ppo|protection.?order|stalking|threat|harass|restrain)', re.IGNORECASE),
    'F': re.compile(r'(?i)(appell|coa|msc|366810|supreme.?court|brief|leave.?to.?appeal)', re.IGNORECASE),
    'A': re.compile(r'(?i)(custody|parenting.?time|visitation|child|l\.?d\.?w|best.?interest|watson)', re.IGNORECASE),
    'B': re.compile(r'(?i)(shady.?oaks|evict|housing|property|rent|lease|lockout|title)', re.IGNORECASE),
}

def detect_lanes(text):
    lanes = []
    for lane_id in ['E', 'D', 'F', 'A', 'B']:
        if MEEK_PATTERNS[lane_id].search(text[:2000]):
            lanes.append(lane_id)
    if len(lanes) >= 2:
        lanes = ['C'] + lanes  # Convergence
    return ','.join(lanes) if lanes else ''

def score_relevance(text):
    legal_terms = [
        'court', 'judge', 'order', 'motion', 'filed', 'hearing', 'custody',
        'plaintiff', 'defendant', 'attorney', 'counsel', 'statute', 'mcr',
        'mcl', 'violation', 'evidence', 'testimony', 'witness', 'affidavit',
        'appeal', 'brief', 'petition', 'complaint', 'docket', 'case no',
        'pigors', 'watson', 'mcneill', 'barnes', 'muskegon', 'circuit'
    ]
    text_lower = text.lower()
    hits = sum(1 for t in legal_terms if t in text_lower)
    return min(1.0, hits / 8.0)

def classify_document(text):
    text_lower = text[:3000].lower()
    if any(w in text_lower for w in ['transcript', 'proceedings', 'q.', 'a.', 'the court:']):
        return 'transcript'
    if any(w in text_lower for w in ['order', 'it is ordered', 'it is hereby']):
        return 'order'
    if any(w in text_lower for w in ['motion', 'moves this court', 'respectfully']):
        return 'motion'
    if any(w in text_lower for w in ['affidavit', 'sworn', 'subscribed']):
        return 'affidavit'
    if any(w in text_lower for w in ['police', 'incident report', 'officer']):
        return 'police_report'
    if any(w in text_lower for w in ['notice', 'you are hereby notified']):
        return 'notice'
    return 'document'

def setup_db():
    db = sqlite3.connect(BRAIN_DB)
    db.execute('PRAGMA busy_timeout=60000')
    db.execute('PRAGMA journal_mode=WAL')
    db.execute('PRAGMA cache_size=-32000')
    return db

def get_image_only_pdfs(db):
    """Find PDFs that were marked as image-only (no text extracted) by prior harvest"""
    rows = db.execute("""
        SELECT DISTINCT file_source FROM chat_intelligence 
        WHERE extraction_method IN ('pymupdf', 'pymupdf_v1')
        AND (content LIKE '%[IMAGE-ONLY%' OR content LIKE '%no text extracted%'
             OR length(content) < 50)
        AND file_source IS NOT NULL
    """).fetchall()
    return [r[0] for r in rows if r[0] and os.path.exists(r[0])]

def scan_for_image_pdfs(search_dirs=None):
    """Alternatively, scan directories for PDFs and check if they have extractable text"""
    if search_dirs is None:
        search_dirs = [
            r'C:\Users\andre\LitigationOS\03_EVIDENCE',
            r'C:\Users\andre\LitigationOS\04_COURT_FILINGS',
            r'C:\Users\andre\LitigationOS\07_PDF',
            r'C:\Users\andre\LitigationOS\01_FILINGS',
            r'C:\Users\andre\LitigationOS\01_Pleadings',
            r'C:\Users\andre\LitigationOS\02_FILINGS',
        ]
    
    image_pdfs = []
    checked = 0
    for d in search_dirs:
        if not os.path.exists(d):
            continue
        for root, dirs, files in os.walk(d):
            for f in files:
                if not f.lower().endswith('.pdf'):
                    continue
                path = os.path.join(root, f)
                checked += 1
                try:
                    doc = fitz.open(path)
                    total_text = ''
                    for page_num in range(min(3, len(doc))):
                        total_text += doc[page_num].get_text()
                    doc.close()
                    if len(total_text.strip()) < 50:
                        image_pdfs.append(path)
                except:
                    continue
    
    print(f"Scanned {checked} PDFs, found {len(image_pdfs)} image-only")
    return image_pdfs

def ocr_pdf(pdf_path, max_pages=20, dpi=300):
    """Extract text from image-only PDF using Tesseract OCR"""
    if os.path.exists(TESSERACT_CMD):
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
    
    doc = fitz.open(pdf_path)
    pages_text = []
    
    for page_num in range(min(max_pages, len(doc))):
        page = doc[page_num]
        # Render page to image at specified DPI
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        pix = page.get_pixmap(matrix=mat)
        
        # Convert to PIL Image
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        
        # OCR with Tesseract
        try:
            text = pytesseract.image_to_string(img, lang='eng',
                config='--oem 3 --psm 6')
            if text.strip():
                pages_text.append(f"[Page {page_num + 1}]\n{text.strip()}")
        except Exception as e:
            pages_text.append(f"[Page {page_num + 1}] OCR error: {e}")
    
    doc.close()
    return '\n\n'.join(pages_text)

def main():
    print("=" * 60)
    print("APEX OCR Pipeline v1.0")
    print(f"Tesseract path: {TESSERACT_CMD}")
    print(f"Tesseract exists: {os.path.exists(TESSERACT_CMD)}")
    print("=" * 60)
    
    if not os.path.exists(TESSERACT_CMD):
        # Try to find tesseract
        for candidate in [
            r'C:\Program Files\Tesseract-OCR\tesseract.exe',
            r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
            r'C:\Users\andre\AppData\Local\Programs\Tesseract-OCR\tesseract.exe',
        ]:
            if os.path.exists(candidate):
                pytesseract.pytesseract.tesseract_cmd = candidate
                print(f"Found Tesseract at: {candidate}")
                break
        else:
            print("WARNING: Tesseract not found. Will attempt system PATH.")
    
    db = setup_db()
    
    # First try to get image-only PDFs from prior harvest
    image_pdfs = get_image_only_pdfs(db)
    print(f"From prior harvest: {len(image_pdfs)} image-only PDFs")
    
    # If few found from harvest, also scan directories for image-only PDFs
    # 958 image-only PDFs were identified by harvest-pdf-apex, so always scan
    if len(image_pdfs) < 1000:
        print("Scanning directories for additional image-only PDFs...")
        scanned = scan_for_image_pdfs()
        # Merge, dedup
        existing = set(image_pdfs)
        for p in scanned:
            if p not in existing:
                image_pdfs.append(p)
        print(f"Total image-only PDFs to OCR: {len(image_pdfs)}")
    
    # Check which are already OCR'd
    already_done = set()
    rows = db.execute("""SELECT DISTINCT file_source FROM chat_intelligence 
        WHERE extraction_method = 'ocr_tesseract'""").fetchall()
    already_done = {r[0] for r in rows}
    
    todo = [p for p in image_pdfs if p not in already_done]
    print(f"Already OCR'd: {len(already_done)}, remaining: {len(todo)}")
    
    if not todo:
        print("Nothing to OCR!")
        db.close()
        return
    
    # Process in batches
    success = 0
    failed = 0
    batch = []
    batch_size = 25
    
    for i, pdf_path in enumerate(todo):
        print(f"[{i+1}/{len(todo)}] OCR: {os.path.basename(pdf_path)}...", end=' ')
        
        try:
            text = ocr_pdf(pdf_path)
            if len(text.strip()) < 20:
                print("(no text extracted)")
                failed += 1
                continue
            
            lanes = detect_lanes(text)
            relevance = score_relevance(text)
            doc_type = classify_document(text)
            
            # Truncate to reasonable size for DB
            content = text[:10000]
            
            batch.append((
                'ocr_document',           # source_platform
                hashlib.md5(pdf_path.encode()).hexdigest()[:16],  # conversation_id
                os.path.basename(pdf_path),  # conversation_title
                content,                    # content
                'ocr_text',                 # content_type
                0,                          # is_user_truth (documents, not user statements)
                relevance,                  # lane_confidence (reusing as relevance proxy)
                '',                         # timestamp_utc
                pdf_path,                   # file_source
                'ocr_tesseract',           # extraction_method
                relevance,                  # legal_relevance_score
                '',                         # entities_json
                '',                         # date_references
                '',                         # key_claims
            ))
            
            success += 1
            print(f"OK ({len(text)} chars, {lanes or 'no lane'}, {relevance:.2f})")
            
        except Exception as e:
            print(f"ERROR: {e}")
            failed += 1
        
        # Batch insert
        if len(batch) >= batch_size:
            db.executemany("""INSERT OR IGNORE INTO chat_intelligence 
                (source_platform, conversation_id, conversation_title,
                 content, content_type, is_user_truth, lane_confidence,
                 timestamp_utc, file_source, extraction_method,
                 legal_relevance_score, entities_json, date_references, key_claims)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", batch)
            db.commit()
            print(f"  Batch committed: {len(batch)} records")
            batch = []
    
    # Final batch
    if batch:
        db.executemany("""INSERT OR IGNORE INTO chat_intelligence 
            (source_platform, conversation_id, conversation_title,
             content, content_type, is_user_truth, lane_confidence,
             timestamp_utc, file_source, extraction_method,
             legal_relevance_score, entities_json, date_references, key_claims)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", batch)
        db.commit()
    
    # Summary
    total = db.execute("SELECT COUNT(*) FROM chat_intelligence").fetchone()[0]
    ocr_count = db.execute("SELECT COUNT(*) FROM chat_intelligence WHERE extraction_method = 'ocr_tesseract'").fetchone()[0]
    
    print("\n" + "=" * 60)
    print(f"OCR Pipeline Complete!")
    print(f"  Processed: {success + failed}")
    print(f"  Success: {success}")
    print(f"  Failed: {failed}")
    print(f"  OCR records in brain DB: {ocr_count}")
    print(f"  Total brain DB records: {total}")
    print("=" * 60)
    
    db.close()

if __name__ == '__main__':
    main()
