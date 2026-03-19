# START_HERE — CAPSTONE_PORTFOLIO_STACK_v2026-01-23.7

## Required placement (exact)
You must end up with THIS folder existing:
`F:\CAPSTONE\packs\CAPSTONE_PORTFOLIO_STACK_v2026-01-23.7\`

Inside it, you must see:
- `scripts\00_LAUNCH_STUDIO.cmd`
- `studio\backend\app.py`
- `studio\ui\index.html`

## Fastest safe method (recommended): World-First extractor
1) Put this file anywhere (Desktop is fine):
`WORLDFIRST_SELFEXTRACT_CAPSTONE_PORTFOLIO_STACK_v2026-01-23.7.py`
2) Run (PowerShell or CMD):
`python WORLDFIRST_SELFEXTRACT_CAPSTONE_PORTFOLIO_STACK_v2026-01-23.7.py --out F:/CAPSTONE/packs`
3) Confirm folder exists:
`F:\CAPSTONE\packs\CAPSTONE_PORTFOLIO_STACK_v2026-01-23.7\`

## Manual method
1) Create folder: `F:\CAPSTONE\packs\`
2) Extract `CAPSTONE_PORTFOLIO_STACK_v2026-01-23.7.zip` so it creates:
`F:\CAPSTONE\packs\CAPSTONE_PORTFOLIO_STACK_v2026-01-23.7\...`
3) IMPORTANT: do NOT run .cmd from inside a zip viewer. You must fully extract first.

## Launch Studio (double-click)
`F:\CAPSTONE\packs\CAPSTONE_PORTFOLIO_STACK_v2026-01-23.7\scripts\00_LAUNCH_STUDIO.cmd`
It will:
- verify the folder is writable
- find python (python OR py)
- create `.venv` in the pack root
- install deps
- start Studio at http://127.0.0.1:8787

## If it still fails (automatic diagnosis)
Double-click:
`scripts\90_DIAGNOSE.cmd`
Then upload:
`diagnostics\diagnose.log`
