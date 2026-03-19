# AUTORUN_v0009 — Desktop launcher + autonomous pipeline (offline-first)

## Run once (recommended)
From the bundle root (folder that contains `TOOLS/`):

```powershell
python .\TOOLS\litos_governor_autonomous.py --bundle-root .
```

This writes a new run to:
- `BRAIN/RUNS/RUN_YYYYMMDD_HHMMSS_UTC_xxxxxxxx/`
and an event log to:
- `LOGS/runs/<run_slug>.jsonl`

## Resume an interrupted run
```powershell
python .\TOOLS\litos_governor_autonomous.py --bundle-root . --run-id <RUN_SLUG> --resume
```

## Desktop launcher (.bat)
Create a file on your desktop named `LitigationOS_Run.bat` with:

```bat
@echo off
cd /d "F:\LitigationOS\LITIGATIONOS__MASTERv1.0"
python TOOLS\litos_governor_autonomous.py --bundle-root .
pause
```

Notes:
- Adjust the `cd /d` path to wherever you store the bundle.
- This launcher does not modify inputs. It only writes new run outputs under `BRAIN/RUNS` and logs under `LOGS/`.

## What it does (autonomous)
1) Extract PDFs (if present under `SOURCES/original`)
2) Build forms catalog from `SOURCES/original/all michigan court form links ALL JURISDICTIONS.md`
3) Build authority snapshot (candidate-only; QuoteLock gate remains OPEN)
4) Brain ingest (atoms→signals→scores→deltas→gates→actions→vehicles + graph export)
5) Validate graph contracts (CSV schemas + referential)

## Outputs you will care about immediately
- `DOCS/INGEST_REPORT_<RUN_SLUG>.md`
- `BRAIN/EXPORTS/LATEST_RUN.json`
- `BRAIN/RUNS/<RUN_SLUG>/graph/nodes.csv` and `edges.csv`
