# SUPERPIN — FORM_OS: HARVEST + FORM-INSTRUCTIONS + STACKFACTORY (ALL JURISDICTIONS)
DATE: 2026-02-28
COMMAND: `FORM_OS:HARVEST_AND_BUILD_ALL@CONVERGE`
TARGET: VS Code Copilot CLI (agent-based multi-pass; do not stop until convergence)

## What you are building
A production “FormOS” subsystem inside LitigationOS that:
1) Recursively ingests ALL local litigation files (including ZIPs, nested folders) into a **content-addressed vault**,
2) Detects court forms across **ALL jurisdictions** (state/federal/tribal/territory) by scanning the local corpus,
3) Extracts **every instruction on each form** “word-for-word” to the highest fidelity possible:
   - native PDF text extraction pass (page-marked),
   - fallback OCR pass when native text is missing/low-quality,
4) Stores each form’s extracted instructions into the central DB, with provenance + hashes,
5) Builds a per-form “FormSpec” and “Composition/ComplianceProfile” by combining:
   - text extracted from the form itself (instructions + authority statements),
   - global jurisdiction filing rules (e.g., for MI: MiFILE standards + MCR 1.109 + motion rules),
   - appellate doc-type rules (COA/MSC equivalents),
6) Generates Akoma Ntoso (LegalDocML AKN 3.0) templates + FieldMaps for each form version,
7) Produces “Clerk Stacks” (filing bundles) **one form at a time**: lead doc + required attachments + proof of service + exhibit index + companion forms,
8) Outputs a flattened, deduped folder plan (“cascading planes”) so each form has its full 100% rule-abiding stack beside it.

## Hard constraints
- Central DB is the source of truth.
- Append-only: never overwrite prior artifacts; create new versions.
- Deterministic IDs and SHA-256 for every file + extracted text.
- Do not emit extracted copyrighted form text into chat. Extract+store locally.
- Convergence loop: ingest → extract → spec → template → validate → coverage report → fix → repeat until PASS.

## Definition of Done
DONE == TRUE only if:
- For every discovered court form file, there is:
  - a FormRecord row,
  - a FormInstruction row with page-marked text (or OCR output) + hash,
  - a FormSpec row (requirements list derived from instructions),
  - an Akoma Ntoso Template artifact,
  - a ComplianceProfile artifact,
  - and canonical vault placement in cascading planes structure.
- Coverage report shows 100% coverage of discovered forms in the local corpus.
- Validators pass (XML well-formed, required sections present, IDs stable).

## Build plan (agents)
Implement an internal agent swarm (async tasks):
1) IntakeAgent: recursive scan + ZIP explode + file classification
2) DedupAgent: SHA-256 CAS store; hardlink/copy into vault
3) TextExtractAgent: PDF/DOCX/TXT extraction (multi-pass); per-page markers
4) OCRAgent: PDFs with low text density (optional if OCR installed)
5) FormDetectAgent: detect “forms” vs “evidence” vs “orders” via heuristics + filename patterns + page structure
6) InstructionAgent: extract instruction blocks from form text and store word-for-word slices + page anchors
7) SpecAgent: convert instructions to structured requirements (JSON) and required companion docs
8) ComplianceAgent: attach jurisdiction rule requirements (MI: MiFILE+MCR; others pluggable rulebanks)
9) AKNAgent: generate AKN templates and FieldMaps per form version
10) StackAgent: build filing stack folder + manifest per form and per case (when case context exists)

## MUST implement this now
Write the full code with error handling. Provide working demo on a sample folder. Then iterate until all tests pass.

END SUPERPIN.
