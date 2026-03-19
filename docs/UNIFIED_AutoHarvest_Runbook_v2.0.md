# UNIFIED AutoHarvest Runbook (v2.0)

## Goal
Turn a messy litigation corpus into a **searchable, auditable record spine**: inventory + timeline + searchable text + semantic vectors.

## Minimal steps
1) Trust this folder in Gemini CLI (Trusted Folders unlock tools, extensions, and local settings). 
2) Run `RUN.cmd`.
3) Open `.out/<RUN_ID>/DASHBOARD.md` and paste `NEXT_PROMPT.md` into your LLM.

## Troubleshooting
- If Qdrant didn't start: install Docker Desktop and re-run. Qdrant quickstart uses `docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant`.
- If OCR didn't run: install Tesseract and re-run (scripts/INSTALL_TESSERACT.ps1).
- If the corpus is huge: trim targets list in config/harvest_config.json or raise max_files/max_mb.

## Determinism / auditability
- Every run writes `run_ledger.jsonl` + `inventory.csv` + hashed IDs.
- The hub is junction-based; original files are untouched.

