# Start Here — LitigationOS Blueprint Pack (ShortPaths)

This is the **short-path** edition designed to avoid Windows extraction failures caused by long file paths.

## Step 1 — Extract safely
1) Create a short destination folder, e.g.:
   - `C:\L3pack` (recommended)
   - or `F:\L3pack`
2) Extract the ZIP into that folder using **7-Zip** or Windows Explorer.

## Step 2 — Open the blueprint
- Open: `L3\INDEX.md`
- Then open: `L3\LitigationOS_BLUEPRINT_README_v2026-01-19.3.md`

## Step 3 — Use the mapping when you see “long-name” references
- `PATH_MAP.csv` maps **old (long)** paths to **new (short)** paths.
- If any document refers to a folder like `docs/` or `model/`, use this mapping table:

| Long folder name | Short folder name |
|---|---|
| `docs/` | `d/` |
| `diagrams/` | `g/` |
| `model/` | `mdl/` |
| `neo4j/` | `n4j/` |
| `schemas/` | `sch/` |
| `templates/` | `tpl/` |
| `validation_reports/` | `vr/` |
| `savepoints/` | `sp/` |
| `tools/` | `tl/` |

## Step 4 — Optional regeneration (Python)
If you want to re-run the C3 generators on your machine:

PowerShell (from your extraction folder, e.g., `C:\L3pack`):
```powershell
python .\L3\tl\c3_generate_all.py --root .\L3
```

If Python is not available, install **Python 3.x** first, then re-run the command above.


---
## FIX7 Addendum — Canonical root = F:\L3\ (one top folder on F:)

**Install**: run `INSTALL_TO_F.bat` to copy everything into `F:\L3\`.

**Run**: `RUN_L3.bat` executes: `python F:\L3\tl\c3_generate_all.py --root F:\L3`

**Docs**: `OPEN_DOCS.bat` opens the primary blueprint documents.

Core rule is recorded in: `L3\CORE_DIRECTIVE_APPEND_CANONICAL_ROOTS_F.md`.


---
## FIX10 Addendum — Single EXE + Headless + SavePoint Browser
- Launch GUI: `LAUNCH_GUI.bat`
- Headless run: `RUN_HEADLESS.bat`
- Build single EXE: `L3\gui\BUILD_GUI_EXE_ONEFILE.bat`
- GUI has a SavePoints tab for browsing `sp/` checkpoints.
