# LitigationOS Autopilot (Alpha) — local-first drive scout + manifest builder

This pack gives you a **single entrypoint CLI** that can:
- discover drives (Windows) or roots (macOS/Linux)
- recursively scan for litigation-relevant files (PDF/DOCX/ZIP/etc.)
- detect "SCANNED" bundles and other high-signal folders
- emit an append-only **run folder** with:
  - RUN.json (summary)
  - RUN_LEDGER.jsonl (event log)
  - manifest_files.csv + manifest_files.jsonl (full inventory)
  - missing_deps.json (auto-acquire plan for external tools)

It is designed to be the **front door** of a full LitigationOS pipeline:
inventory → unpack → OCR → convert → chunk → index → graph → compile.

## What it does *not* do (yet)
- It does not automatically OCR/convert PDFs *unless* you enable those stages later.
- It does not upload anywhere unless you explicitly configure it.

## Quick start (Windows)
1) Install Python 3.11+ (or use `uv`, see below).
2) Unzip this folder.
3) From PowerShell:
   ```powershell
   python -m autopilot scan --auto
   ```

### Optional: use uv (recommended)
Install uv once, then:
```powershell
uv run -m autopilot scan --auto
```

## Quick start (macOS/Linux)
```bash
python3 -m autopilot scan --roots "$HOME" --auto
```

## Output layout
By default output goes under:
`./out/<RUN_ID>/`

## Safety / scope
Default scan **excludes** OS/system dirs and common caches unless you pass `--include-system`.

## Next steps
Once this manifest is trustworthy, you plug in:
- OCRmyPDF for scanned PDFs
- Docling/Marker for PDF→MD
- Tika for broad extraction
- GraphRAG + Neo4j bulk import for the graph brain
- Pandoc for court-formatted DOCX/PDF compilation
