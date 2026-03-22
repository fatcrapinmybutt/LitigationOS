---
description: "Evidence processing pipeline — OCR, drive scanning, lane assignment, dedup, Bates stamps, quality gates. Apply when ingesting, classifying, or processing evidence files."
applyTo: "**/*.{py,sql,md}"
---

# Evidence Processing Memory

Operational procedures for the 16-phase evidence pipeline. OCR, drive scanning, lane assignment, deduplication, and quality gates.

## Drive Scanning Order

Scan drives in priority order (highest-value evidence first):
1. **C:\Users\andre\LitigationOS\** — Central repo (court filings, analyses, tools)
2. **I:\** — Sorted evidence, organized files, dedup target (~30 GB SD card)
3. **D:\** — DB archives, evidence trove (6,783+ files discovered)
4. **F:\** — Backups, index files (58 GB USB flash)
5. **G:\** — Evidence (58 GB USB flash)
6. **J:\** — Centralization target, 2TB USB (exFAT — read-only for evidence)

## MEEK Lane Assignment

MEEK signals route evidence to case lanes. Detection priority: **E → D → F → C → A → B**

| Lane | MEEK Signal | Keywords/Patterns |
|------|-------------|-------------------|
| **E** (Misconduct) | MEEK4 | McNeill, judicial, bias, JTC, canon, misconduct, benchbook, ex parte |
| **D** (PPO) | MEEK3 | PPO, protection order, 5907, contempt, stalking, harassment |
| **F** (Appellate) | MEEK5 | COA, 366810, appeal, appellant, appellee, brief, appendix |
| **C** (Convergence) | — | Multi-lane, conspiracy, federal, §1983, convergence |
| **A** (Custody) | MEEK2 | Custody, parenting, 001507, Watson, child, visitation, FOC |
| **B** (Housing) | MEEK1 | Shady Oaks, eviction, housing, trailer, 002760, habitability |

`LaneCrossContaminationError` (non-fatal, skip-item) raised when wrong-lane evidence detected.

## OCR Pipeline (Phases 4a-4e)

```
Phase 4a: PDF extraction (PyMuPDF/pdfplumber → text + metadata)
Phase 4b: DOCX extraction (python-docx → paragraphs + tables + metadata)
Phase 4c: Structured data (CSV/JSON/JSONL → parsed records)
Phase 4d: Atomization (split documents into evidence atoms — 71,109 in DB)
Phase 4e: Archive extraction (ZIP/RAR → explode → classify contents)
```

### Quality Gates
- **OCR confidence**: ≥85% character confidence for text extraction
- **Lane assignment**: Every document MUST have exactly one primary lane
- **Dedup**: Content-based comparison (NOT hash-only — peek inside per user preference)
- **Metadata**: file_path, file_size, modified_date, sha256, page_count required

## Deduplication Rules (USER MANDATE: No Hashing Alone)

Andrew explicitly said: "no hashing — peek at the document to ensure they are the same."

1. **Stage 1**: SHA-256 hash for initial clustering (group potential duplicates)
2. **Stage 2**: Open and compare actual content (first 1000 chars + last 500 chars)
3. **Stage 3**: If content matches, move duplicate to `I:\` dedup folder — NEVER DELETE
4. **Stage 4**: Record in dedup_clusters table with both file paths + match confidence

## Bates Stamping Protocol

- Format: `PIGORS-{LANE}-{NNNNNN}` (e.g., PIGORS-A-000001)
- Sequential within each lane
- Register in `bates_registry` table (currently EMPTY — needs population)
- Stamp appears at bottom-right of each page
- Cross-reference in exhibit index

## Evidence Categories (20 Types)

Legal, Police Reports, Court Orders, Financial, Medical, Communications, Photos, Videos, Audio, Social Media, Government Records, Housing/Property, Employment, Education, App Exports, Transcripts, Forensic, Administrative, Correspondence, Unknown

## Output Destinations

| Phase | Output Table | Output Directory |
|-------|-------------|-----------------|
| Phase 1 (Inventory) | discovery_engine | 03_EVIDENCE/ |
| Phase 3 (Classify) | documents | 01_EXTRACTS/ |
| Phase 4 (Extract) | atoms, pages | 01_EXTRACTS/ |
| Phase 5 (Brain Feed) | 00_SYSTEM/brains/*.db | 00_SYSTEM/brains/ |
| Phase 6 (Gap Analysis) | evidence_gaps | 05_REPORTS/ |
