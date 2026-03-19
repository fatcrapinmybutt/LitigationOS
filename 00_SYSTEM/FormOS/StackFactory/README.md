# LitigationOS FormOS Harvest + StackFactory (SUPERPIN Pack)
Generated: 2026-02-28

## Purpose
A Copilot-ready blueprint + runnable baseline script to:

1) Recursively ingest **local** litigation corpora (including ZIPs), deduplicate into a content-addressed store,
2) Detect and extract **court forms** (PDF/DOCX), and extract **word-for-word instructions** as text when possible,
3) Build per-form `FormInstruction` records (page-marked text, provenance, hashes),
4) Generate `FormSpec` (requirements) + compliance profile stubs,
5) Generate Akoma Ntoso template shells for each form + store in the central DB,
6) Produce a flattened, deduped vault folder layout ("cascading planes").

## What's inside
- `COPILOT_SUPERPIN_FORM_OS.md` — paste into VS Code Copilot CLI
- `tooling/form_os_orchestrator.py` — baseline working script (scan + unzip + dedup + extract + store)
- `tooling/schema.sql` — SQLite schema
- `config/form_os_config.example.json` — config example
- `docs/FOLDER_PLANES.md` — vault folder plan
- `docs/LEGAL_NOTE.md` — local extraction/copyright note
- `manifest.json` — sha256 for each file in this pack
