# LitigationOS Toolchain + Runner Kit (Windows) — v2026-02-08

This kit installs the minimum tools needed to run the LitigationOS compiler runtime and produce:
- Neo4j CSV exports (`neo4j_nodes.csv`, `neo4j_edges.csv`)
- `graph.graphml` (Gephi-ready)
- Action report + compile reports

## 0) What you need (minimum)

### Required
- Windows 10/11
- PowerShell 7 (you already have this)
- Python 3.11+ (recommended) or 3.10+
- Internet access long enough to install Python packages (one-time)

### Python packages (minimum)
- pandas
- networkx
- PyPDF2

> These are installed into a project-local virtual environment (no admin required).

## 1) Recommended folder layout

Pick a project folder, example:
`C:\Users\andre\Desktop\THE_LITIGATION_OPERATING_SYSTEM\TOOLS\compiler_runtime\`

Inside that folder, place:
- `litigationos_compiler_runtime.py`
- `requirements.txt`
- this runner kit scripts (`bootstrap_windows.ps1`, `run_cycle0.ps1`, `check_tools.ps1`)

If you downloaded the runtime ZIP:
`LitigationOS_CompilerRuntime_v1_2_0_FULL.zip`
extract it into that folder.

## 2) One-command setup (creates venv + installs packages)

In PowerShell:

```powershell
cd "C:\Users\andre\Desktop\THE_LITIGATION_OPERATING_SYSTEM\TOOLS\compiler_runtime"
Set-ExecutionPolicy -Scope Process Bypass -Force
.\bootstrap_windows.ps1
```

## 3) Run “Cycle 0” against your attachment directory

```powershell
.\run_cycle0.ps1 -InDir "C:\path\to\your\attachments" -OutDir ".\out_cycle0"
```

Dry run:

```powershell
.\run_cycle0.ps1 -InDir "C:\path\to\your\attachments" -OutDir ".\out_cycle0" -DryRun
```

Fail-hard:

```powershell
.\run_cycle0.ps1 -InDir "C:\path\to\your\attachments" -OutDir ".\out_cycle0" -FailHard
```

## 4) Optional tools (recommended)

### Neo4j Desktop
- Load `neo4j_nodes.csv` + `neo4j_edges.csv` via:
  - `LOAD CSV` (safe, iterative) OR
  - `neo4j-admin database import` (bulk load; requires creating a new DB)

### Gephi
- Open `graph.graphml` and run layouts (ForceAtlas2, etc.)

### OCR toolchain (for scan-heavy exhibit binders)
Not required for the current runtime, but you will want this next:
- Tesseract OCR
- Poppler (for `pdf2image`)
- Python extras: `pytesseract`, `pdf2image`, `pillow`, `opencv-python`, `pymupdf`

Use `requirements_extras_ocr.txt` in this kit when you’re ready.

## 5) Diagnostics

```powershell
.\check_tools.ps1
```

Prints versions and confirms the venv is active.
