# CORE DIRECTIVE APPEND — CANONICAL ROOTS + PATHLENGTH GUARD (v2026-01-19.3_FIX7_FROOT)
Build stamp (local): 2026-01-20 06:15:51

## Canonical storage roots
1) **Canonical long-term store**: `F:\L3\`
   - All LitigationOS Blueprint/Contracts artifacts should be stored under **one** top-level folder on `F:`:
     - Top folder: `F:\L3\`
     - Internal structure may contain subfolders as needed (schemas, templates, docs, etc.).
2) **Local Desktop staging / launch location**:
   - Preferred: `C:\Users\andre\desktop\` (as provided)
   - Fallback: `%USERPROFILE%\Desktop\`

## PathLengthGuard (mandatory for ZIP deliverables)
- All delivered ZIPs must:
  - use short directory names (`sch`, `tpl`, `vr`, `mdl`, `n4j`, `tl`, etc.)
  - include `PATH_MAP.csv` mapping `old_path -> new_path`
  - keep top-level extraction root short (example: `L3\`)

## Launcher requirement (mandatory)
- Every pack must include:
  1) `INSTALL_TO_F.bat` — installs/copies the pack into `F:\L3\` without destructive mirroring.
  2) `RUN_L3.bat` — runs the deterministic regeneration pipeline against `F:\L3\`.
  3) `OPEN_DOCS.bat` — opens the primary docs/entrypoints from `F:\L3\`.

## Appendix: expected runtime entrypoints
- Generator: `F:\L3\tl\c3_generate_all.py`
- Index: `F:\L3\INDEX.md`
- Start: `F:\START_HERE.md` (or copied into `F:\L3\START_HERE.md`)

