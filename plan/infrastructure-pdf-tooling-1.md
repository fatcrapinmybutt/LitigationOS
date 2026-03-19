---
goal: "Build MD-to-PDF filing generation pipeline with court-specific templates"
version: 1.0
date_created: 2026-03-12
last_updated: 2026-03-12
owner: Andrew Pigors
status: 'Planned'
tags: [infrastructure, filing, pdf]
---

# Introduction

![Status: Planned](https://img.shields.io/badge/status-Planned-blue)

Build a PDF generation pipeline that converts Markdown filing drafts into court-compliant PDF documents. This unblocks 40+ physical filing tasks and 12 PDF generation todos. Integrates with the existing `FilingProductionPipeline`.

## 1. Requirements & Constraints

- **REQ-001**: Convert MD → HTML → PDF with court-specific CSS templates
- **REQ-002**: Support 5 court types: Circuit, COA, MSC, Federal, JTC
- **REQ-003**: Auto-generate TOC and TOA from document structure
- **CON-001**: Must use Python-only libraries (weasyprint primary, reportlab fallback)
- **CON-002**: Output ≤25 MB per document (MiFILE limit)
- **CON-003**: Never set CWD to repo root (22 shadow modules)
- **SEC-001**: No file system paths in PDF metadata
- **GUD-001**: Store templates in `00_SYSTEM/engines/templates/pdf/`

## 2. Implementation Steps

### Implementation Phase 1 — Dependencies & Templates

- GOAL-001: Install PDF tooling and create court-specific CSS templates

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-001 | Install weasyprint: `pip install weasyprint` in pytools_venv | | |
| TASK-002 | Install fallback: `pip install reportlab markdown Jinja2 pdfplumber` | | |
| TASK-003 | Create `00_SYSTEM/engines/templates/pdf/base.css` — shared styles (margins, fonts, spacing) | | |
| TASK-004 | Create `circuit.css` — 14th Circuit (1" margins, TNR 12pt, double-space, centered page numbers) | | |
| TASK-005 | Create `coa.css` — Court of Appeals (MCR 7.212(C), 14pt headings, TOC/TOA styling) | | |
| TASK-006 | Create `msc.css`, `federal.css`, `jtc.css` — remaining court types | | |
| TASK-007 | Create `caption_block.html` Jinja2 template for case captions | | |
| TASK-008 | Create `footer.html` and `toc.html` Jinja2 templates | | |

### Implementation Phase 2 — Core Generator

- GOAL-002: Build the PDF generation engine with MD→HTML→PDF pipeline

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-009 | Create `00_SYSTEM/engines/pdf_generator.py` — `PDFGenerator` class | | |
| TASK-010 | Implement `generate()`: single file MD → HTML (via markdown lib) → PDF (via weasyprint) | | |
| TASK-011 | Implement TOC generation: parse H1-H4 headings, inject TOC page with correct page refs | | |
| TASK-012 | Implement TOA generation: parse `[CITE: ...]` markers, build authority table | | |
| TASK-013 | Implement caption block: pull case metadata from `litigation_context.db` via Jinja2 | | |
| TASK-014 | Implement page numbering and header/footer injection | | |
| TASK-015 | Implement Bates numbering for exhibit pages | | |
| TASK-016 | Implement DRAFT watermark mode | | |

### Implementation Phase 3 — Batch & Integration

- GOAL-003: Build batch generation and integrate with existing pipeline

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-017 | Implement `batch_generate()`: process entire directory of filings | | |
| TASK-018 | Create `pdf_generation_log` table in `litigation_context.db` | | |
| TASK-019 | Integrate with `FilingProductionPipeline` — add PDF step after QA | | |
| TASK-020 | Generate PDFs for all 3 clerk-ready filings as validation | | |
| TASK-021 | Generate PDFs for all 12 filing packages (PKG01-12) | | |

### Implementation Phase 4 — Testing & Validation

- GOAL-004: Comprehensive testing and validation of generated PDFs

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-022 | Create `tests/test_pdf_generator.py` — unit tests for template rendering | | |
| TASK-023 | Create integration test: full pipeline from MD to validated PDF | | |
| TASK-024 | Verify PDF compliance: margins ±0.1", fonts, spacing, page numbers | | |
| TASK-025 | Verify TOC page references match actual content pages | | |
| TASK-026 | Verify all 12 generated PDFs are valid and openable | | |

## 3. Alternatives

- **ALT-001**: Use `wkhtmltopdf` — rejected: requires external binary installation, harder to distribute
- **ALT-002**: Use `fpdf2` — rejected: limited CSS support, poor table rendering
- **ALT-003**: Use pandoc — rejected: requires Haskell runtime, heavy dependency
- **ALT-004**: Use `reportlab` only — considered as fallback: more control but more code, no CSS support

## 4. Dependencies

- **DEP-001**: `weasyprint` ≥60.0 — HTML/CSS to PDF engine
- **DEP-002**: `reportlab` ≥4.0 — fallback PDF generation
- **DEP-003**: `markdown` ≥3.5 — Markdown to HTML conversion
- **DEP-004**: `Jinja2` ≥3.1 — template rendering
- **DEP-005**: `pdfplumber` ≥0.10 — PDF reading for verification tests

## 5. Files

- **FILE-001**: `00_SYSTEM/engines/pdf_generator.py` — core PDF generation engine (NEW)
- **FILE-002**: `00_SYSTEM/engines/templates/pdf/base.css` — shared CSS (NEW)
- **FILE-003**: `00_SYSTEM/engines/templates/pdf/circuit.css` — Circuit Court CSS (NEW)
- **FILE-004**: `00_SYSTEM/engines/templates/pdf/coa.css` — COA CSS (NEW)
- **FILE-005**: `00_SYSTEM/engines/templates/pdf/msc.css` — MSC CSS (NEW)
- **FILE-006**: `00_SYSTEM/engines/templates/pdf/federal.css` — Federal CSS (NEW)
- **FILE-007**: `00_SYSTEM/engines/templates/pdf/caption_block.html` — caption template (NEW)
- **FILE-008**: `00_SYSTEM/engines/filing_production_pipeline.py` — add PDF integration (MODIFY)
- **FILE-009**: `tests/test_pdf_generator.py` — tests (NEW)

## 6. Testing

- **TEST-001**: Unit test — template rendering produces valid HTML for each court type
- **TEST-002**: Unit test — TOC generation includes all H1-H4 headings
- **TEST-003**: Integration test — MD file → PDF with correct margins and fonts
- **TEST-004**: Integration test — batch generation of 3 clerk-ready filings succeeds
- **TEST-005**: Validation test — generated PDF text is selectable (not rasterized)
- **TEST-006**: Validation test — no file system paths in PDF metadata

## 7. Risks & Assumptions

- **RISK-001**: weasyprint may have rendering differences from browser CSS — mitigate with extensive visual testing
- **RISK-002**: Complex Markdown tables may not render well — mitigate with custom CSS for tables
- **RISK-003**: TOC page numbers may be off by 1 due to dynamic content — mitigate with two-pass rendering
- **ASSUMPTION-001**: weasyprint installs cleanly on Windows 10/11 with Python 3.12
- **ASSUMPTION-002**: Existing Markdown filings follow consistent heading structure

## 8. Related Specifications / Further Reading

- [spec/spec-infrastructure-pdf-tooling.md](/spec/spec-infrastructure-pdf-tooling.md)
- [spec/spec-process-filing-automation.md](/spec/spec-process-filing-automation.md)
- [weasyprint documentation](https://doc.courtbouillon.org/weasyprint/)
