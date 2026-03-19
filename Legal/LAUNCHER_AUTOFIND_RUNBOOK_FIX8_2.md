# Launcher Autofind Runbook (FIX8)
Build stamp (local): 2026-01-20 06:22:28

## Objective
You can double-click a launcher without tracking paths.
The launcher finds the correct root by locating a marker file:

- Marker: `F:\L3\.litos_root.json`

## Files
- `LAUNCH_AUTOFIND.bat`  
  Runs `python L3\tl\run_autonomous.py` and opens key outputs on success.
- `OPEN_DOCS_AUTOFIND.bat`  
  Opens primary blueprint documents.
- `CREATE_DESKTOP_SHORTCUTS.bat`  
  Creates Desktop shortcuts pointing to the BAT files.

## Discovery rules (in priority order)
1) Environment variable `LITIGATIONOS_ROOT`
2) `F:\L3`
3) Relative to the launcher pack extraction folder
4) Shallow drive search for `X:\L3\.litos_root.json` on drives D:..Z:
5) Shallow search of common folders on drives D:..Z:

No deep recursion is used.

## Recommended workflow
1) Extract pack to a short path (example): `C:\L3pack\`
2) Run `INSTALL_TO_F.bat`
3) Run `CREATE_DESKTOP_SHORTCUTS.bat`
4) Use Desktop shortcut: **LitigationOS Blueprint (Autofind)**

## Notes
- This does not require saving paths in memory. The marker file is the single source of truth.
- You can relocate the folder as long as the marker and required entrypoints remain intact.
