---
goal: "Content-based dedup across 6 drives and canonical file taxonomy migration"
version: 1.0
date_created: 2026-03-12
last_updated: 2026-03-12
owner: Andrew Pigors
status: 'Planned'
tags: [infrastructure, data, drives, dedup]
---

# Introduction

![Status: Planned](https://img.shields.io/badge/status-Planned-blue)

Perform content-based deduplication across 6 drives (1.47M files, 526 GB), establish a canonical file taxonomy, and execute safe migration with rollback capability. No files are ever deleted — duplicates move to `I:\LitigationOS_Dedup\`.

## 1. Requirements & Constraints

- **REQ-001**: Full drive inventory of all 1.47M files with SHA-256 hashes
- **REQ-002**: Content-based comparison (not just hashing) per Andrew's directive
- **REQ-003**: Safe migration with checkpoint/rollback per 1,000-file wave
- **CON-001**: NO HARD DELETIONS — move duplicates to I:\ drive only
- **CON-002**: Content-based comparison required — "peek inside the document"
- **CON-003**: I: drive is slow USB — batch operations, minimize random access
- **SEC-001**: SHA-256 manifests before and after each wave

## 2. Implementation Steps

### Implementation Phase 1 — Full Drive Inventory

- GOAL-001: Build complete file inventory across all 6 drives

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-001 | Expand `drive_file_index` from 159K → 1.47M rows (full 6-drive scan) | | |
| TASK-002 | Compute SHA-256 hash for every file (batched, priority: C→D→F→G→H→I) | | |
| TASK-003 | Detect MIME types via extension mapping + magic bytes for ambiguous files | | |
| TASK-004 | Index file metadata: size, created, modified, path depth, parent directory | | |
| TASK-005 | Generate drive inventory summary report per drive | | |

### Implementation Phase 2 — Hash-Based Dedup (Phase 1 Dedup)

- GOAL-002: Identify byte-identical duplicates via SHA-256

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-006 | Query `drive_file_index` for SHA-256 clusters (same hash, multiple paths) | | |
| TASK-007 | For each cluster, designate canonical file (prefer C:\ > canonical taxonomy path) | | |
| TASK-008 | Generate dedup plan: list of files to move with source → dest mapping | | |
| TASK-009 | Execute wave 1: move first 1,000 hash-duplicates to `I:\LitigationOS_Dedup\` | | |
| TASK-010 | Verify integrity: SHA-256 of moved files matches original | | |
| TASK-011 | Continue waves until all hash-duplicates processed | | |

### Implementation Phase 3 — Content-Based Dedup (Phase 2 Dedup)

- GOAL-003: Identify near-duplicates by comparing actual document content

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-012 | Build content extractor: PDF → text (pdfplumber), DOCX → text (python-docx), MD/TXT → direct read | | |
| TASK-013 | For files with different hashes but same name/size, extract and compare content | | |
| TASK-014 | Compute text similarity (normalized edit distance or Jaccard) — threshold ≥0.95 = near-duplicate | | |
| TASK-015 | For near-duplicate clusters, designate canonical (newest version, canonical location) | | |
| TASK-016 | Execute content-based dedup waves (1,000 files per wave) | | |

### Implementation Phase 4 — Taxonomy & Migration

- GOAL-004: Establish canonical taxonomy and migrate remaining files

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-017 | Define canonical taxonomy mapping (file type → directory) — get Andrew's approval | | |
| TASK-018 | Identify orphan files (not in canonical location, not duplicates) | | |
| TASK-019 | Generate migration plan: orphan → canonical location mapping | | |
| TASK-020 | Execute migration waves (1,000 files per wave) with checkpoint | | |
| TASK-021 | Update all DB references (evidence paths, filing paths) to canonical locations | | |
| TASK-022 | Build unified search index across all canonical locations | | |

### Implementation Phase 5 — Verification & Reporting

- GOAL-005: Post-migration integrity verification

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-023 | Generate post-migration SHA-256 manifest | | |
| TASK-024 | Compare pre/post manifests: verify zero data loss | | |
| TASK-025 | Verify all DB references point to existing files | | |
| TASK-026 | Generate final report: files moved, space reclaimed, orphans resolved | | |

## 3. Alternatives

- **ALT-001**: Hash-only dedup — rejected: Andrew requires content comparison
- **ALT-002**: Use `rdfind` or `fdupes` — rejected: no content-based comparison, Linux-only
- **ALT-003**: Centralize all files to one drive — rejected: I: is slow USB, C: is limited space

## 4. Dependencies

- **DEP-001**: `pdfplumber` — PDF text extraction
- **DEP-002**: `python-docx` — DOCX text extraction
- **DEP-003**: All 6 drives mounted and accessible (C, D, F, G, H, I)
- **DEP-004**: I: drive has ≥100 GB free for dedup archive

## 5. Files

- **FILE-001**: `00_SYSTEM/engines/dedup_engine.py` — core dedup engine (NEW)
- **FILE-002**: `00_SYSTEM/engines/content_comparator.py` — content extraction and comparison (NEW)
- **FILE-003**: `00_SYSTEM/engines/taxonomy_migrator.py` — file migration engine (NEW)
- **FILE-004**: `00_SYSTEM/pipeline/drive_organizer_v4.py` — existing organizer (REFERENCE)
- **FILE-005**: `reorg_move_log.jsonl` — existing move log (APPEND)

## 6. Testing

- **TEST-001**: Hash dedup correctly identifies 10 synthetic duplicate sets
- **TEST-002**: Content comparator correctly identifies near-duplicates (≥0.95 similarity)
- **TEST-003**: Migration wave of 100 files completes with valid checkpoint
- **TEST-004**: Rollback correctly restores files from `reorg_move_log.jsonl`
- **TEST-005**: Post-migration manifest matches pre-migration for canonical files

## 7. Risks & Assumptions

- **RISK-001**: I: drive may disconnect during wave — mitigate with per-wave checkpoints
- **RISK-002**: Content extraction may fail on corrupted PDFs — mitigate with skip + log
- **RISK-003**: 1.47M files may take days to fully process — mitigate with incremental waves
- **ASSUMPTION-001**: All 6 drives remain connected during processing
- **ASSUMPTION-002**: I: drive has sufficient space for dedup archive

## 8. Related Specifications / Further Reading

- [spec/spec-infrastructure-drive-reorganization.md](/spec/spec-infrastructure-drive-reorganization.md)
