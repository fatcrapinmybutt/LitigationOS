# LitigationOS Autopilot — PEAK Pack (v0.2)

This is a **local-first, self-assembling** CLI scaffold that runs on **your machine** and can:
- auto-discover Windows drives (or POSIX roots)
- recursively scan for litigation-relevant files
- auto-detect **SCANNED** bundles / high-signal folders
- optionally unpack archives into a run staging area (never touching originals)
- optionally OCR scanned PDFs (if `ocrmypdf` is installed)
- optionally convert PDFs/DOCX/TXT into Markdown
- chunk outputs into line-addressable shards for downstream GraphRAG/Neo4j
- emit append-only run artifacts: manifests, ledgers, reports, and an acquire-plan

## 0) One-command entry (recommended)
### Windows
Double-click:
- `RUN_PEAK_WINDOWS.bat`

or:
```powershell
python bootstrap.py run --auto --profile peak
```

### macOS/Linux
```bash
python3 bootstrap.py run --auto --profile peak
```

`bootstrap.py` will (optionally) create a local `.venv` and install **free, open-source** Python deps needed for extraction.

## 1) Core commands
- Inventory only (fast, stdlib-only):
```bash
python -m autopilot scan --auto
```

- Full pipeline (best-effort; stages run only if deps exist):
```bash
python -m autopilot run --auto --profile peak --stages inventory,unpack,ocr,convert,chunk
```

- Doctor (prints missing tools + recommended installers):
```bash
python -m autopilot doctor
```

## 2) Output (append-only)
By default, all outputs go under:
`./out/<RUN_ID>/`

Key files:
- `RUN.json` — run summary/config/counts
- `RUN_LEDGER.jsonl` — append-only event log
- `manifest_files.csv` + `manifest_files.jsonl` — discovered file inventory
- `manifest_outputs.jsonl` — produced artifacts inventory (unpacked/ocr/md/shards)
- `missing_deps.json` — AcquirePlan (what to install to unlock more stages)
- `REPORT.txt` — human-friendly summary

## 3) Safety
- Default excludes OS/system/caches unless `--include-system`
- Never modifies originals; all derived work goes into `out/<RUN_ID>/`

## 4) What “PEAK” means here
- faster scanner (os.scandir recursion)
- more aggressive high-signal detection
- concurrency for hashing/extraction
- delta-friendly outputs (stable IDs + manifests + ledgers)

## 5) Next integrations
This pack intentionally keeps the “heavy engines” external:
- OCR: `ocrmypdf`
- PDF→rich layout MD: Docling / Marker (optional, can be plugged in later)
- Graph: GraphRAG + Neo4j import (next cycle)

