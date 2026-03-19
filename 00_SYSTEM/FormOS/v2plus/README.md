# FormOS Upgrade v2 (LitigationOS)
Generated: 2026-02-28

This is an upgrade of the prior FormOS pack.

## What's new (v2)
- Single CLI entrypoint: `tooling/formos_cli.py` with subcommands:
  - `ingest` (scan roots, explode zips, CAS-dedup into Vault/00_OBJECTS, DB insert)
  - `extract` (PDF/DOCX/TXT extraction with per-page outputs + needs_ocr scoring)
  - `detect-forms` (improved heuristics; extracts MI-style form codes where possible)
  - `instructions` (captures instruction-heavy spans + stores full text)
  - `specs` (compiles instructions into `requirements.json` with structured requirement objects)
  - `akn` (generates AKN template shells based on doctype guess + placeholders)
  - `stacks` (builds a per-form rule-abiding stack folder scaffold + manifest)
  - `coverage` (coverage report with missing tasks)
- Upgraded SQLite schema: `tooling/schema_v2.sql`
- Rules plugin system with MI sample rulebank: `rules/mi_rulebank.yaml`
- Vault plane spec: `docs/FOLDER_PLANES_v2.md`
- Audit notes: `docs/AUDIT_NOTES.md`

## Running (local)
1) Copy `config/formos_config.example.json` to `config/formos_config.json` and edit paths.
2) Initialize DB:
   `python tooling/formos_cli.py init-db --config config/formos_config.json --schema tooling/schema_v2.sql`
3) Optional: load rulebanks:
   `python tooling/formos_cli.py load-rulebanks --config config/formos_config.json --paths rules/mi_rulebank.yaml`
4) Pipeline:
   `python tooling/formos_cli.py ingest --config config/formos_config.json`
   `python tooling/formos_cli.py extract --config config/formos_config.json`
   `python tooling/formos_cli.py detect-forms --config config/formos_config.json`
   `python tooling/formos_cli.py instructions --config config/formos_config.json`
   `python tooling/formos_cli.py specs --config config/formos_config.json`
   `python tooling/formos_cli.py akn --config config/formos_config.json`
   `python tooling/formos_cli.py stacks --config config/formos_config.json --case-id YOUR_CASE_ID`
   `python tooling/formos_cli.py coverage --config config/formos_config.json --out Vault/90_REPORTS/coverage_v2.json`

## OCR
OCR is optional. If `enable_ocr=true` and `ocr_tool` exists in PATH (e.g., `ocrmypdf`),
FormOS can OCR PDFs flagged `needs_ocr=1`. OCR output is stored locally; it is never printed to chat.

## Safety note
This toolkit extracts and stores text from documents you already have locally or are authorized to download.
It does not publish extracted form text to chat outputs.


## Added in v2plus
- tooling/mifile_lint.py (basic PDF preflight)
- tooling/pdf_fieldmap_extract.py (AcroForm field extraction → fields.json)
- tooling/export_neo4j_from_formos_db.py (SQLite → Neo4j CSV)
- tooling/build_cyclepack.py (zip outputs + manifest)
