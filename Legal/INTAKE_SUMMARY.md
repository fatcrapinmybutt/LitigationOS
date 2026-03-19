# Intake Summary — Uploaded Archives (Run: intake_20260120_045126)

## 1) What was ingested (inventory-only, no content alteration)
This run **did not modify** any uploaded file. It produced **inventory artifacts** for ZIP archives currently present in `/mnt/data`.

Artifacts produced:
- `zip_inventory.csv` — one row per zip: byte size, entry count, extension mix, integrity test (`testzip_ok`).
- `zip_inventory.json` — same data in structured form.

## 2) Current archive set (high-level)
The uploaded set includes:
- **Court rulebook pack** (`COURT RULES.zip`) — mixed PDFs/TXT/JSON/JSONL/MD/YML and a nested ZIP.
- **Scanned evidence bundles** — multiple ZIPs containing only PDFs (dockets/notices/proofs; transcripts; judge orders; ex parte suspension packet; filings; emails).
- **Existing LitigationOS addendum zips** (previous bundles) — scripts, schemas, docs.

## 3) Integrity status
All listed archives returned `testzip_ok = True` in this run.

## 4) Next deterministic steps (recommended)
### Step A — Decompose each ZIP into a stable work tree (append-only)
Target extraction layout (example):
- `work/zips_extracted/<zip_stem>/...`

Rules:
- Do not rename originals.
- Extract with overwrite disabled.
- Record a manifest of extracted paths and sizes.

### Step B — Format-aware text harvesting
- PDFs with embedded text: `pdftotext` extraction.
- Scanned PDFs: OCR lane (Tesseract) with page-level provenance.

### Step C — Record Spine bootstrap
- Build a **Register-of-Actions (ROA) spine** from file-stamps and captions.
- Link each discovered order/notice/transcript to:
  - hearing date
  - court level
  - case number
  - judge
  - docket/ROA position

### Step D — Lane routing
Send documents to lanes:
- Ex parte lane
- Contempt lane
- PPO lane
- COA/MSC lane
- JTC lane

Each lane emits a `lane_report.json` with: issues, procedural posture, deadlines, proof obligations.

