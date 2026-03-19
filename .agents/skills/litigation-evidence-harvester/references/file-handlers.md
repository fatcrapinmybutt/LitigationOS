# File Handlers — litigation-evidence-harvester

## File Type Handler Reference

This reference documents the processing pipeline for each file type encountered
in the Pigors v Watson evidence collection (427,956+ files).

---

## Handler Matrix

| Handler ID | File Types | Method | OCR | Metadata Extraction |
|-----------|-----------|--------|-----|---------------------|
| FH-001 | .txt, .md, .csv, .tsv | Direct read (UTF-8) | No | File system metadata |
| FH-002 | .html, .htm | HTML parser (strip tags) | No | Meta tags + file system |
| FH-003 | .docx | python-docx / docx2txt | No | Document properties |
| FH-004 | .xlsx, .xls | openpyxl / xlrd | No | Workbook properties |
| FH-005 | .pdf (text) | PyPDF2 / pdfplumber | No | PDF metadata |
| FH-006 | .pdf (image) | Tesseract + pdf2image | Yes | PDF metadata + OCR |
| FH-007 | .jpg, .jpeg | Tesseract | Yes | EXIF data |
| FH-008 | .png | Tesseract | Yes | PNG metadata |
| FH-009 | .tif, .tiff | Tesseract | Yes | TIFF tags |
| FH-010 | .eml | email.parser | No* | Email headers |
| FH-011 | .msg | msg-extractor | No* | MAPI properties |
| FH-012 | .rtf | striprtf / unrtf | No | Limited metadata |
| FH-013 | .json, .jsonl | JSON parser | No | File system metadata |
| FH-014 | .xml | XML parser | No | XML attributes |
| FH-015 | .zip, .rar | Archive extraction | N/A | Archive metadata |

*Email handlers process body text directly; attachments are extracted and
processed by their respective handlers.

---

## FH-001: Plain Text Handler

### Input: .txt, .md, .csv, .tsv
### Processing Pipeline
```
1. Detect encoding (UTF-8, UTF-16, ASCII, Latin-1)
2. Read file content
3. If CSV/TSV: parse into structured rows
4. Extract text content
5. Compute SHA-256 hash
6. Record metadata:
   - File path, size, creation date, modification date
   - Encoding detected
   - Line count, word count
7. Pass text to atom extraction pipeline
```

### Common Issues
- Encoding detection failure → try multiple encodings, fall back to Latin-1
- Large CSV files (> 100MB) → stream processing, don't load into memory
- Malformed CSV → use error-tolerant parser with logging

---

## FH-005: PDF Text Handler

### Input: .pdf (with extractable text layer)
### Detection: Try text extraction first; if < 10 chars per page → route to FH-006 (OCR)
### Processing Pipeline
```
1. Open PDF with pdfplumber
2. For each page:
   a. Extract text
   b. If text length < 10 chars → flag for OCR (FH-006)
   c. Extract tables (if present)
   d. Record page dimensions
3. Concatenate text with page break markers
4. Compute SHA-256 hash of original PDF
5. Record metadata:
   - PDF metadata (author, title, creation date, producer)
   - Page count, text extraction confidence
6. Pass text to atom extraction pipeline
```

### Michigan Court Filing PDFs
- Michigan e-filed documents are typically text-searchable PDFs
- Older court records may be scanned (image-only) → route to FH-006
- SCAO forms are often form-fillable PDFs → extract field values

---

## FH-006: PDF Image Handler (OCR)

### Input: .pdf (image-only or mixed)
### Processing Pipeline
```
1. Convert PDF pages to images (300 DPI minimum)
2. Pre-processing per page:
   a. Deskew (correct rotation)
   b. Denoise (remove speckles)
   c. Contrast enhancement
   d. Binarization (convert to B&W)
3. OCR with Tesseract (English model)
4. For each page:
   a. Record OCR confidence score
   b. If confidence < 80% → add to manual review queue
   c. If confidence < 50% → flag as UNRELIABLE
5. Post-processing:
   a. Spell-check correction (legal dictionary)
   b. Entity recognition (names, dates, case numbers)
   c. Format normalization
6. Compute SHA-256 of original PDF
7. Record metadata:
   - OCR confidence per page and overall
   - Pre-processing steps applied
   - Time to process
8. Pass text to atom extraction pipeline
```

### OCR Quality Factors
| Factor | Impact on OCR | Mitigation |
|--------|--------------|------------|
| Faded text | Reduced accuracy | Contrast enhancement |
| Handwriting | Poor accuracy (< 60%) | Manual review queue |
| Multi-column | Layout confusion | Column detection pre-processing |
| Stamps/seals | Noise in text area | Region masking |
| Color paper | Binarization issues | Adaptive thresholding |
| Small font | Character confusion | Upscaling before OCR |

---

## FH-007/008/009: Image Handlers (JPEG, PNG, TIFF)

### Processing Pipeline
```
1. Validate image integrity (not corrupted)
2. Extract EXIF/metadata:
   - Camera model, date taken, GPS coordinates (if present)
   - Image dimensions, color depth
3. Image classification:
   a. Document scan → OCR pipeline (same as FH-006 step 2+)
   b. Photograph → description extraction + metadata only
   c. Screenshot → OCR pipeline
4. If document/screenshot:
   a. Pre-process (deskew, denoise, contrast)
   b. OCR with Tesseract
   c. Record confidence
5. Compute SHA-256 of original image
6. Pass results to atom extraction pipeline
```

### Photo Evidence Handling (Lane B — Housing Conditions)
- Housing condition photos are HIGH priority
- Extract: date, location (if GPS), visual description
- Classify by condition type: mold, structural, plumbing, electrical, etc.
- Link to specific habitability claims under MCL 554.139

---

## FH-010/011: Email Handlers (EML, MSG)

### Processing Pipeline
```
1. Parse email headers:
   - From, To, CC, BCC
   - Date sent
   - Subject line
   - Message-ID (for threading)
   - In-Reply-To / References (for conversation chains)
2. Extract body text (prefer plain text over HTML)
3. If HTML body only → strip tags, preserve structure
4. Extract attachments:
   a. Save each attachment separately
   b. Route to appropriate handler by file type
   c. Link attachment to parent email
5. Compute SHA-256 of original email file
6. Record metadata:
   - All headers
   - Attachment count and types
   - Thread position (if determinable)
7. Pass body text to atom extraction pipeline
8. Process attachments through their respective handlers
```

### Email Authentication for Court (MRE 901)
- Emails require authentication under MRE 901(b)(1) (testimony of witness with knowledge)
- Header analysis can support authentication (MRE 901(b)(9) — system/process)
- Print headers with email body for exhibit preparation
- Preserve original .eml/.msg files for hash verification

---

## FH-015: Archive Handler (ZIP, RAR)

### Processing Pipeline
```
1. Validate archive integrity
2. Compute SHA-256 of archive file
3. Extract contents to temporary directory
4. Enumerate extracted files
5. For each extracted file:
   a. Determine handler by file type
   b. Process through appropriate handler
   c. Record parent archive relationship
6. Log extraction manifest:
   - Archive file path
   - Extracted file count
   - File types present
   - Any extraction errors
7. Clean up temporary directory after processing
```

### Known Archives in Collection
- conversations.json(1)(1).rar / .zip — Communication records
- HarvesterFleet_CGPT_Fleet_v2026-02-18.zip — Agent fleet data
- Harvester_Agents50_Pack.zip — Agent configurations
- HIGHCOURTMAX.zip — Court records compilation
- GRAPH MASTER OMEGA.rar — Graph data
