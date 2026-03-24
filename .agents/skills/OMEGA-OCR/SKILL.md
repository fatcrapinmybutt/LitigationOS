---
name: OMEGA-OCR
description: >-
  OCR pipeline skill for LitigationOS. Tiered OCR stack: PaddleOCR (primary) + Marker
  (academic) + Surya (handwriting). PDF→text, image→text, handwriting detection,
  confidence scoring, batch processing, quality validation, and integration with evidence
  pipeline phases 4a-4e. Handles scanned court orders, handwritten notes, photographs
  of documents, and multi-page PDF extraction for litigation evidence.
category: engineering
version: "1.0.0"
triggers:
  - OCR
  - optical character recognition
  - PDF to text
  - image to text
  - scanned document
  - handwriting
  - PaddleOCR
  - Marker
  - Surya
  - text extraction
  - scan
  - digitize
lanes:
  - "ALL (evidence processing is cross-lane)"
court: "14th Judicial Circuit; Michigan COA; all courts"
case: Pigors v Watson
metadata:
  tier: "3 (Engineering)"
  author: andrew-pigors + copilot-omega
  jurisdiction: Michigan
---

# 👁️ OMEGA-OCR v1.0

> **OCR Pipeline for Litigation Evidence**
> PaddleOCR · Marker · Surya · PDF/Image→Text · Confidence Scoring
> Pipeline Phases: 4a-4e (Extraction) · All Lanes

## Module OCR1: Tiered OCR Stack

### Architecture
```
Input Document
  │
  ├─ Is it a text-layer PDF? ──YES──→ PyMuPDF direct extract (fastest)
  │                                      ↓
  │                               Confidence check: text coverage > 90%?
  │                                 YES → done    NO → fall through to OCR
  │
  ├─ Is it a scanned PDF/image? ──→ Tier 1: PaddleOCR (primary)
  │                                      ↓
  │                               Confidence < 80%?
  │                                 YES → Tier 2: Marker (academic docs)
  │                                      ↓
  │                               Confidence < 70%?
  │                                 YES → Tier 3: Surya (handwriting)
  │                                      ↓
  │                               Confidence < 50%?
  │                                 YES → Flag for manual review
  │
  └─ Is it a photograph? ──→ Pre-process (deskew, denoise, enhance)
                                 ↓
                             Then enter OCR tier stack above
```

### Tier Details

| Tier | Engine | Best For | Speed | Accuracy |
|------|--------|----------|-------|----------|
| **0** | PyMuPDF | Text-layer PDFs | ⚡ Instant | 99%+ |
| **1** | PaddleOCR | Printed docs, forms, typed | Fast | 90-98% |
| **2** | Marker | Academic, multi-column, tables | Medium | 85-95% |
| **3** | Surya | Handwritten notes, signatures | Slow | 70-90% |
| **4** | Manual | Degraded, damaged documents | N/A | Human |

### Installation (Local-Only — no cloud APIs)
```python
# PaddleOCR
pip install paddleocr paddlepaddle

# Marker (PDF → markdown with layout preservation)
pip install marker-pdf

# Surya (handwriting + layout detection)
pip install surya-ocr

# PyMuPDF (PDF text extraction + rendering)
pip install PyMuPDF
```

## Module OCR2: PDF Processing Pipeline

### Phase 4a: PDF Text Extraction
```python
import fitz  # PyMuPDF

def extract_pdf_text(pdf_path: str) -> dict:
    """Extract text from PDF, detect if OCR needed."""
    doc = fitz.open(pdf_path)
    pages = []
    needs_ocr = False
    
    for page_num, page in enumerate(doc):
        text = page.get_text()
        char_count = len(text.strip())
        
        # Heuristic: if page has images but <50 chars, needs OCR
        images = page.get_images()
        if images and char_count < 50:
            needs_ocr = True
            
        pages.append({
            'page': page_num + 1,
            'text': text,
            'char_count': char_count,
            'has_images': bool(images),
            'needs_ocr': images and char_count < 50
        })
    
    return {
        'total_pages': len(pages),
        'needs_ocr': needs_ocr,
        'pages': pages
    }
```

### Phase 4b: OCR Execution
```python
from paddleocr import PaddleOCR

ocr = PaddleOCR(use_angle_cls=True, lang='en', use_gpu=False)

def ocr_page(image_path: str) -> dict:
    """Run PaddleOCR on a page image."""
    result = ocr.ocr(image_path, cls=True)
    
    lines = []
    total_confidence = 0
    
    for line in result[0]:
        bbox, (text, confidence) = line
        lines.append({
            'text': text,
            'confidence': confidence,
            'bbox': bbox
        })
        total_confidence += confidence
    
    avg_confidence = total_confidence / len(lines) if lines else 0
    
    return {
        'text': '\n'.join(l['text'] for l in lines),
        'avg_confidence': avg_confidence,
        'line_count': len(lines),
        'lines': lines
    }
```

## Module OCR3: Image Pre-Processing

### Enhancement Pipeline (for degraded documents)
```
Input Image
  │
  ├─ 1. Deskew (correct rotation)
  │     └─ Detect text angle → rotate to 0°
  │
  ├─ 2. Denoise (remove scanning artifacts)
  │     └─ Gaussian blur + bilateral filter
  │
  ├─ 3. Binarize (convert to black/white)
  │     └─ Adaptive thresholding (Otsu's method)
  │
  ├─ 4. Enhance contrast
  │     └─ CLAHE (Contrast Limited Adaptive Histogram Equalization)
  │
  └─ 5. Scale (ensure minimum DPI)
        └─ Upscale to 300 DPI if below
```

### Court Document Special Handling
```
Court orders:    → Standard OCR (usually typed)
Handwritten:     → Surya tier (handwriting specialization)
Carbon copies:   → High contrast enhancement first
Fax copies:      → Denoise heavily, then PaddleOCR
Photographs:     → Full pre-processing pipeline
Stamps/seals:    → Region detection, separate OCR pass
```

## Module OCR4: Batch Processing

### Evidence Drive Scanning
```python
def batch_ocr_evidence(drive_paths: list, output_db: str):
    """Batch OCR all PDF/image evidence across drives."""
    
    # Supported formats
    EXTENSIONS = {'.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.tif', '.bmp'}
    
    # Scan drives for evidence files
    for drive in drive_paths:
        for root, dirs, files in os.walk(drive):
            for f in files:
                ext = os.path.splitext(f)[1].lower()
                if ext in EXTENSIONS:
                    full_path = os.path.join(root, f)
                    process_evidence_file(full_path, output_db)
    
    # Process priorities:
    # 1. Court orders and legal documents
    # 2. Police reports and agency records
    # 3. Financial documents
    # 4. Correspondence
    # 5. Photographs and screenshots
```

### Pipeline Integration (Phases 4a-4e)
```
Phase 4a: Extract text from text-layer PDFs (PyMuPDF)
Phase 4b: OCR scanned PDFs and images (PaddleOCR → Marker → Surya)
Phase 4c: Extract structured data (tables, forms, fields)
Phase 4d: Atomize into evidence atoms (paragraph-level chunks)
Phase 4e: Archive originals + store extracted text in DB
```

## Module OCR5: Quality Validation

### Confidence Scoring
```
Per-page confidence levels:
  95-100%: Excellent — no review needed
  80-94%:  Good — spot-check recommended
  60-79%:  Fair — review all extracted text
  40-59%:  Poor — manual correction required
  <40%:    Failed — flag for manual transcription

Aggregate document confidence:
  = weighted average of page confidences
  Weight by page importance (first/last pages higher weight for legal docs)
```

### Common OCR Error Patterns (Legal Documents)
| Error | Example | Fix |
|-------|---------|-----|
| Section symbol | § → S, s | Post-process regex |
| Paragraph symbol | ¶ → P, 11 | Post-process regex |
| Case citations | "Mich" → "Much" | Legal dictionary validation |
| Statute numbers | "552.605" → "552,605" | Period vs comma correction |
| Court abbreviations | "MCR" → "MCF" | Legal abbreviation dictionary |
| Docket numbers | "2024-001507-DC" → garbled | Pattern matching validation |

### Post-OCR Validation Script
```python
def validate_legal_ocr(text: str) -> dict:
    """Validate OCR output for legal document accuracy."""
    issues = []
    
    # Check for common legal patterns that should be present
    patterns = {
        'case_number': r'\d{4}-\d{6}-[A-Z]{2}',
        'mcl_citation': r'MCL \d{3}\.\d+',
        'mcr_citation': r'MCR \d+\.\d+',
        'date': r'\d{1,2}/\d{1,2}/\d{4}',
        'section_symbol': r'§',
    }
    
    for name, pattern in patterns.items():
        matches = re.findall(pattern, text)
        if not matches:
            issues.append(f"No {name} pattern found — may be OCR error")
    
    return {'issues': issues, 'quality': 'good' if not issues else 'review'}
```

## Module OCR6: Database Integration

### Storage Schema
```sql
CREATE TABLE IF NOT EXISTS ocr_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_path TEXT NOT NULL,
    source_hash TEXT,
    page_number INTEGER,
    extracted_text TEXT,
    confidence REAL,
    ocr_engine TEXT,
    processing_time_ms INTEGER,
    needs_review BOOLEAN DEFAULT 0,
    reviewed BOOLEAN DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX idx_ocr_source ON ocr_results(source_path);
CREATE INDEX idx_ocr_confidence ON ocr_results(confidence);

-- FTS5 for full-text search of OCR results
CREATE VIRTUAL TABLE IF NOT EXISTS ocr_fts USING fts5(
    extracted_text, source_path,
    content='ocr_results',
    content_rowid='id'
);
```

### Query Patterns
```sql
-- Find low-confidence pages needing review
SELECT source_path, page_number, confidence
FROM ocr_results WHERE confidence < 0.80 AND NOT reviewed
ORDER BY confidence ASC;

-- Search OCR text for evidence
SELECT source_path, page_number, snippet(ocr_fts, 0, '<b>', '</b>', '...', 32)
FROM ocr_fts WHERE ocr_fts MATCH 'custody OR withholding OR parenting';

-- OCR processing statistics
SELECT ocr_engine, COUNT(*) as pages, AVG(confidence) as avg_conf
FROM ocr_results GROUP BY ocr_engine;
```

## Global Rules

### Anti-Hallucination
- NEVER fabricate OCR output — always extract from actual documents
- Report actual confidence scores, not inflated numbers
- If OCR fails, flag for manual review — don't guess at content

### Append-Only Evidence
- NEVER modify original documents
- Store OCR results alongside originals, never in-place
- Maintain SHA-256 hash of original for provenance chain

### Integration Points
- Evidence pipeline → Phase 4a-4e integration
- Evidence atoms → OMEGA-EVIDENCE for exhibit management
- Legal documents → OMEGA-LITIGATION-SUPREME for filing
- Database → litigation_context.db via managed_db()
