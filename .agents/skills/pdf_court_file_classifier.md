# PDF Court File Classifier v13.0.0

## LitigationOS Skill Module — Real Court File vs AI-Generated Draft Detection

---

## Purpose and Scope

This skill classifies PDF documents into two categories:
1. **Real Court Files** — Authentic documents filed with or issued by a court (orders, opinions, motions with file stamps, subpoenas, docket entries).
2. **AI-Generated Drafts** — Documents produced by LLMs or AI tools, often markdown-to-PDF conversions, attorney work product drafts, or template outputs.

Accurate classification is essential because:
- Real court files are **evidence** and must be preserved with chain-of-custody integrity.
- AI drafts are **work product** and must never be presented as court-issued documents.
- Mixing the two in evidence chains corrupts the litigation record.
- Michigan courts require authentic copies per MCR 2.507 and MCL 600.2137.

---

## Input Requirements

| Field | Type | Description |
|-------|------|-------------|
| `pdf_path` | `FilePath` | Path to the PDF file to classify |
| `batch_paths` | `List[FilePath]` | Optional batch of PDFs for bulk classification |
| `confidence_threshold` | `float` | Minimum confidence for classification (default: `0.85`) |
| `extract_metadata` | `bool` | Whether to extract and return PDF metadata (default: `true`) |

---

## Processing Methodology

### Phase 1: Structural Analysis

Examine the PDF structure for indicators of origin:

**Real Court File Indicators (+score):**
| Indicator | Weight | Detection Method |
|-----------|--------|------------------|
| Scanned image layers (raster content) | +0.20 | Check for XObject Image streams |
| Inconsistent DPI across pages | +0.10 | Compare MediaBox vs actual raster resolution |
| Skew/rotation artifacts | +0.15 | Detect non-zero rotation in page dictionary |
| JBIG2 or CCITT compression (fax-style) | +0.10 | Check stream filter entries |
| File stamps visible in raster | +0.15 | OCR header region for "FILED" text patterns |
| Multiple scan artifacts (dust, lines) | +0.05 | Edge detection on rendered pages |
| Non-uniform page sizes | +0.05 | Compare MediaBox dimensions across pages |

**AI-Generated Draft Indicators (+score):**
| Indicator | Weight | Detection Method |
|-----------|--------|------------------|
| Clean text extraction (no OCR needed) | +0.20 | Check if text layer matches rendered content |
| Uniform font usage (1–2 fonts) | +0.15 | Count unique font references in page resources |
| Perfect text alignment | +0.10 | Analyze text positioning coordinates |
| PDF producer is a converter tool | +0.15 | Check `/Producer` metadata for pandoc, wkhtmltopdf, Chrome, md-to-pdf, etc. |
| Creation and modification dates identical | +0.05 | Compare `/CreationDate` and `/ModDate` |
| No embedded images or signatures | +0.10 | Check for absence of XObject Image streams |
| Markdown artifacts in text | +0.10 | Search for `##`, `**`, `- [ ]`, backticks in extracted text |
| Hyperlinks in document body | +0.05 | Check for URI annotations |
| Uniform margins and spacing | +0.05 | Analyze text BBox positioning |

### Phase 2: Content Pattern Analysis

Extract text (via text layer or OCR) and analyze for court-document patterns:

**Real Court File Content Patterns:**
```
- Case number format: /\d{2}-\d{4,6}-(FC|FH|DM|CC|CZ|GC|AH|AV)/
- Court header: "STATE OF MICHIGAN", "IN THE CIRCUIT COURT", "PROBATE COURT"
- Judge line: /HON\.\s+[A-Z\s]+,?\s*(JUDGE|J\.)/i
- File stamp: /FILED\s+\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}/
- Clerk signature: /CLERK|DEPUTY CLERK/i
- Proof of Service: /PROOF OF SERVICE|CERTIFICATE OF SERVICE/i
- Michigan statute references: /MCL\s+\d{3}\.\d+|MCR\s+\d\.\d{3}/
- Bar number: /P\d{5}/
- Formal caption with parties: /Plaintiff.*vs?\..*Defendant/is
```

**AI Draft Content Patterns:**
```
- Template placeholders: /\[INSERT\]|\[NAME\]|\[DATE\]|\{.*\}/
- LLM artifacts: /As an AI|I cannot|Here is|Note:|Disclaimer:/
- Markdown residue: /^#{1,3}\s|^\*\*.*\*\*$|^- \[[ x]\]/m
- Perfect enumeration: consistent numbered lists without court-style paragraph numbering
- Absence of handwritten signatures in image analysis
- No case-specific party names (generic references)
```

### Phase 3: Metadata Forensics

Examine PDF internal metadata:

```
Producer Field Analysis:
  REAL indicators:    "Xerox", "Canon", "Ricoh", "HP", "FUJITSU", "Kofax", "Adobe Acrobat"
  AI DRAFT indicators: "pandoc", "wkhtmltopdf", "Chromium", "md-to-pdf", "LibreOffice",
                        "Microsoft Print to PDF", "pdflatex", "WeasyPrint", "Prince"

Creator Field Analysis:
  REAL indicators:    "Acrobat", "Scanner", "PaperStream", "ScanSnap"
  AI DRAFT indicators: "Writer", "Docs", "Claude", "GPT", "Copilot"

Timestamp Analysis:
  REAL: Creation dates during business hours, dates correlate with docket entries
  AI:   Creation dates at unusual hours, recent creation for old case dates
```

### Phase 4: Confidence Scoring

Aggregate all indicator scores into a final classification:

```python
# Pseudocode
real_score = sum(real_indicators)      # Range: 0.0 – 1.0
draft_score = sum(draft_indicators)    # Range: 0.0 – 1.0

if real_score > draft_score and real_score >= confidence_threshold:
    classification = "REAL_COURT_FILE"
    confidence = real_score
elif draft_score > real_score and draft_score >= confidence_threshold:
    classification = "AI_GENERATED_DRAFT"
    confidence = draft_score
else:
    classification = "UNCERTAIN"
    confidence = max(real_score, draft_score)
```

---

## Output Format

```json
{
  "classifier": "pdf_court_file_classifier_v13",
  "file": "Lane_A\\orders\\2024-03-15_order.pdf",
  "classification": "REAL_COURT_FILE",
  "confidence": 0.94,
  "scores": {
    "real_court_file": 0.94,
    "ai_generated_draft": 0.08
  },
  "indicators": {
    "real": [
      {"indicator": "scanned_image_layers", "weight": 0.20, "detected": true},
      {"indicator": "file_stamp_present", "weight": 0.15, "detected": true},
      {"indicator": "case_number_found", "weight": 0.15, "detected": true, "value": "24-1847-FC"},
      {"indicator": "judge_signature", "weight": 0.10, "detected": true, "value": "HON. SMITH, J."}
    ],
    "draft": [
      {"indicator": "clean_text_extraction", "weight": 0.20, "detected": false}
    ]
  },
  "metadata": {
    "producer": "FUJITSU fi-7160",
    "creator": "PaperStream Capture",
    "creation_date": "2024-03-15T09:42:00",
    "page_count": 3,
    "file_size_bytes": 487201
  },
  "extracted_court_data": {
    "case_number": "24-1847-FC",
    "court": "Washtenaw County Circuit Court",
    "judge": "HON. SMITH",
    "filed_date": "2024-03-15",
    "document_type": "ORDER"
  }
}
```

---

## Integration Points

| Skill | Integration |
|-------|-------------|
| `convergence_dedup_engine` | Classification informs canonical selection — real court files preferred |
| `case_lane_router` | Classified documents are tagged before routing to lanes |
| `evidence_chain_builder` | Only `REAL_COURT_FILE` documents enter evidence chains |
| `filing_optimizer` | AI drafts flagged for formatting review before filing |
| `scan_ingester` (engine) | Ingester calls classifier on every PDF ingested |
| `doc_classifier` (engine) | Coordinates with existing document classifier for type sub-classification |

---

## Michigan-Specific Legal References

- **MCR 2.507(G)** — Requirements for copies of court orders
- **MCL 600.2137** — Best Evidence Rule; real court files satisfy original-document requirements
- **MCL 600.2108** — Judicial notice of court records
- **MCR 1.109(D)(1)** — E-filing format requirements for Michigan courts
- **MCR 8.119(D)** — Court records and access; defines what constitutes an official record
- **MCL 750.248** — Forgery of court documents; misclassification risks fraud implications

---

## Edge Cases

1. **Hybrid documents**: Real court orders that were scanned, OCR'd, and then re-formatted. Classify as `REAL_COURT_FILE` if file stamp and case number are present.
2. **Court-generated electronic orders**: Some Michigan courts issue orders as native PDFs (not scanned). These have clean text but contain authentic court metadata. Check for TrueFiling or MiFile producer strings.
3. **Attorney-prepared proposed orders**: These are drafts but may contain case numbers and judge names. Classify as `AI_GENERATED_DRAFT` unless a file stamp is detected.
4. **Redacted documents**: Redaction tools may strip metadata. Fall back to content pattern analysis.
