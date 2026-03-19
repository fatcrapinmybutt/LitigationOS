# PublicLitigationOS — Local Harvest Runner (v2.0)

This pack is a **local-first, free** harvesting + indexing runner for your LitigationOS corpora:
- **Find / inventory** court docs (PDF/DOCX/TXT/CSV/images), including inside **ZIP archives**.
- **Extract text**, render PDFs to images when needed, and do **local OCR** when there is no text layer.
- Build:
  - **FTS index (SQLite)** for keyword search
  - **Vector index (Qdrant)** for semantic search (optional but recommended)
- Emit court-grade working artifacts: `inventory.csv`, `timeline.csv`, `quotes.jsonl`, `neg_connotations.csv`, `violations.csv`, `manifest.*`, `run_ledger.jsonl`, and a `NEXT_PROMPT.md` for the LLM synthesis phase.

## One command (Windows)

1) Unzip this pack to a folder you trust (e.g., `C:\Users\andre\LitigationOS_AutoHarvest\`).
2) In Gemini CLI **Shell mode** (or any PowerShell), run:

```text
!cmd /c RUN.cmd
```

That’s it. The runner will:
- Create a safe **HARVEST_ROOT hub** containing junctions to your high-signal directories (no `.cache` / system junk).
- Create a Python venv and install dependencies (all free).
- Start Qdrant via Docker if available (otherwise it uses SQLite-only FTS).
- Run harvest and write outputs into `./.out/<RUN_ID>/`.

## Outputs

After a run, open:
- `./.out/<RUN_ID>/DASHBOARD.md`
- `./.out/<RUN_ID>/NEXT_PROMPT.md` (paste into Gemini/Copilot/ChatGPT to start the litigation-grade synthesis)

## Safety & scope

This runner intentionally **skips** known noise/corrosion:
- OS directories, caches, `.git`, build outputs, node_modules, venvs, docker layers, browser caches
- huge binaries and corrupted archives (logged + skipped)

See `config/harvest_config.json` for the exact allow/deny rules.

## Licensing

All included components are **free/open-source**. See `licenses/THIRD_PARTY.md`.

