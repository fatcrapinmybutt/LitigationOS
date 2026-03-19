# Δ∞ (Delta-Infinity) — FormOS → Full Filing-Stack Factory

Date: 2026-02-28

This blueprint defines the components required to reach “I need it all” status.

## A) Truth Spine (storage + provenance)
1. CAS Vault (sha256 content-addressed objects)
2. Central DB (SQLite baseline; compatible with Neo4j export)
3. Append-only versioning (no overwrite; new artifacts get new IDs)
4. Line/page anchors (PDF page markers + OCR layout anchors if possible)

## B) Form is Spec (instruction compiler)
For every discovered form version:
- store verbatim instruction text (native extract + OCR fallback)
- segment into InstructionAtoms: page, bbox(optional), text, type
- compile into RequirementsGraph: requirement_id → triggers → satisfy_by artifact types

## C) Doctype Schema Registry (court-required sections)
Maintain a registry of doc-types by jurisdiction/court level:
- Trial: motion, affidavit, proposed order, notice of hearing, proof of service, exhibit index
- COA: brief, appendix/record excerpts, original action complaint, motion, certificate blocks
- MSC: application for leave, motion, answer, appendices, certificate blocks
Each doctype has a JSON Schema + required blocks list.

## D) Evidence Atoms + citation weaving
1. EvidenceAtomization generates evidence atoms from PDFs/images/emails/logs.
2. Draft generators insert citations: Exhibit label + doc_id + sha256 + page marker(s).

## E) StackAssembler (one form at a time)
For each form:
- lead doc (filled PDF or generated pleading)
- required attachments/separate sheets
- required companion forms
- proof/certificate of service
- index to attachments
- exhibit covers + labels
- stack manifest with requirement satisfaction map

## F) Linters (reject-reason realism)
- MiFILE checks: 25MB, OCR, page size, encryption, metadata, attachment indexing
- Motion/brief rules: required sections, page limits, certificate presence
- Stack completeness: required folders + required documents exist
- Satisfaction: every requirement satisfied with a concrete artifact

## G) AutoConverge Loop
Repeat cycles until:
- no new forms discovered
- missing requirements == 0
- all lint reports pass
- OCR queue empty
- coverage stable across N cycles

## Output: Heavy Export
Every run emits a CyclePack ZIP with manifests + Neo4j CSV export + coverage reports.
