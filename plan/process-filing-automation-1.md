---
goal: "Build filing auto-assembler, SCAO form filler, and pre-filing QA pipeline"
version: 1.0
date_created: 2026-03-12
last_updated: 2026-03-12
owner: Andrew Pigors
status: 'Planned'
tags: [process, filing, automation]
---

# Introduction

![Status: Planned](https://img.shields.io/badge/status-Planned-blue)

Automate filing packet assembly, SCAO court form population, and quality gating for all 12 filing packages. Integrates with PDF tooling for final output and the existing `FilingProductionPipeline`.

## 1. Requirements & Constraints

- **REQ-001**: Auto-assemble complete filing packets from component files
- **REQ-002**: Auto-populate 20+ SCAO forms from case metadata in DB
- **REQ-003**: 50+ automated QA checks per filing with GO/NO-GO gate
- **CON-001**: SCAO forms are PDF fillable — use PDF form-filling libraries
- **CON-002**: Some forms require notarization — flag but cannot automate
- **CON-003**: Must handle missing data gracefully (flag, don't crash)
- **GUD-001**: Use `pdfrw` or `PyPDF2` for PDF form field population

## 2. Implementation Steps

### Implementation Phase 1 — Filing Packet Builder

- GOAL-001: Build the filing packet assembly engine

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-001 | Create `00_SYSTEM/engines/filing_packet_builder.py` — `FilingPacketBuilder` class | | |
| TASK-002 | Implement builder pattern: add_motion, add_brief, add_exhibits, add_proposed_order | | |
| TASK-003 | Implement auto-generate proof of service (MC 12) from party data in DB | | |
| TASK-004 | Implement auto-generate cover sheet from case metadata | | |
| TASK-005 | Implement auto-generate fee waiver (MC 20) when IFP status = True | | |
| TASK-006 | Build packet manifest: JSON listing all components with page counts and checksums | | |

### Implementation Phase 2 — SCAO Form Filler

- GOAL-002: Auto-populate SCAO court forms from database

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-007 | Create `00_SYSTEM/engines/scao_form_filler.py` — form filling engine | | |
| TASK-008 | Map SCAO form fields to DB columns for MC 12 (Proof of Service) | | |
| TASK-009 | Map fields for MC 20 (Fee Waiver/IFP Application) | | |
| TASK-010 | Map fields for CC 79 (Summons), CC 88 (Complaint Cover), CC 298 (COA) | | |
| TASK-011 | Implement PDF form filling via `pdfrw` or `PyPDF2` | | |
| TASK-012 | Handle field overflow: truncate with "..." and log warning | | |
| TASK-013 | Validate filled forms: check all required fields are populated | | |

### Implementation Phase 3 — Pre-Filing QA Pipeline

- GOAL-003: Build comprehensive quality gate with 50+ checks

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-014 | Create `00_SYSTEM/engines/prefiling_qa_v2.py` — enhanced QA engine | | |
| TASK-015 | Implement 10 readiness dimensions with weighted scoring (see spec) | | |
| TASK-016 | Implement checks: placeholder scan, citation verify, party name consistency | | |
| TASK-017 | Implement checks: case number format, page limits, signature blocks | | |
| TASK-018 | Implement checks: PoS completeness, exhibit references, formatting compliance | | |
| TASK-019 | Implement GO/NO-GO decision logic with override capability | | |
| TASK-020 | Generate detailed QA report per filing with fix suggestions | | |

### Implementation Phase 4 — Integration & Batch Processing

- GOAL-004: Integrate all components and process all 12 filing packages

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-021 | Integrate packet builder + form filler + QA into `FilingProductionPipeline` | | |
| TASK-022 | Process 3 clerk-ready filings: assemble, fill forms, QA, generate report | | |
| TASK-023 | Process all 12 filing packages (PKG01-12) in batch mode | | |
| TASK-024 | Create `tests/test_filing_automation.py` — unit + integration tests | | |
| TASK-025 | Validate: all generated forms are valid, fillable PDFs | | |

## 3. Alternatives

- **ALT-001**: Use Docassemble — rejected: requires server, not local-first
- **ALT-002**: Manual form filling in Adobe — rejected: too slow (30 min per form)
- **ALT-003**: Use reportlab to recreate forms — rejected: forms must match SCAO originals

## 4. Dependencies

- **DEP-001**: `pdfrw` or `PyPDF2` — PDF form field population
- **DEP-002**: `Jinja2` — template rendering
- **DEP-003**: SCAO form PDFs downloaded to `02_Court_Forms/` (currently blocked — needs internet)
- **DEP-004**: PDF tooling plan (companion) for final conversion

## 5. Files

- **FILE-001**: `00_SYSTEM/engines/filing_packet_builder.py` (NEW)
- **FILE-002**: `00_SYSTEM/engines/scao_form_filler.py` (NEW)
- **FILE-003**: `00_SYSTEM/engines/prefiling_qa_v2.py` (NEW)
- **FILE-004**: `00_SYSTEM/engines/prefiling_qa_engine.py` (REFERENCE — existing)
- **FILE-005**: `00_SYSTEM/engines/filing_production_pipeline.py` (MODIFY — add integration)
- **FILE-006**: `tests/test_filing_automation.py` (NEW)

## 6. Testing

- **TEST-001**: Packet builder produces complete packet with all required components
- **TEST-002**: MC 12 form fills correctly with party names and addresses
- **TEST-003**: QA catches known issues (13 placeholders in clerk-ready filings)
- **TEST-004**: Readiness scores match within ±5 of manual assessment
- **TEST-005**: Batch processing of 12 packages completes without errors

## 7. Risks & Assumptions

- **RISK-001**: SCAO form field names may change between versions — mitigate with field name mapping config
- **RISK-002**: Some forms may not be fillable (scanned images) — mitigate with OCR detection
- **ASSUMPTION-001**: SCAO form PDFs are available in `02_Court_Forms/`
- **ASSUMPTION-002**: Party address data is current in `litigation_context.db`

## 8. Related Specifications / Further Reading

- [spec/spec-process-filing-automation.md](/spec/spec-process-filing-automation.md)
- [spec/spec-infrastructure-pdf-tooling.md](/spec/spec-infrastructure-pdf-tooling.md)
- [plan/infrastructure-pdf-tooling-1.md](/plan/infrastructure-pdf-tooling-1.md)
