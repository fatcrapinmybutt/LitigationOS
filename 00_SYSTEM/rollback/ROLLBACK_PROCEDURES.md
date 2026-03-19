# OPERATION OMEGA — Rollback Procedures
Generated: 2026-03-04 16:59:02

## Database Restore
1. Stop all pipeline processes
2. Decompress: `7z x C:\Users\andre\SAFETY_SNAPSHOT_DB\litigation_context.db.7z -oC:\Users\andre\LitigationOS\ -y`
3. Verify: `python integrity_checker.py`

## Config Restore
- Copy from `H:\SAFETY_SNAPSHOT\configs\` back to original locations
- config.py → `00_SYSTEM\pipeline\config.py`
- START.ps1 → `13_TOOLS\START.ps1`
- .env files → respective directories

## Filing Restore
- Copy from `H:\SAFETY_SNAPSHOT\filings\` → `06_FILINGS\`

## Agent Restore
- Copy from `H:\SAFETY_SNAPSHOT\configs\.agents\` → `.agents\`

## Distillation Rollback
- Original zips preserved in `I:\DISTILLED_ORIGINALS\` (30-day hold)
- Re-extract from originals if master folder is corrupted
- All moves logged in `consolidation_log` table

## Emergency: Full System Restore
1. Restore DB from 7z backup (see above)
2. Restore all configs from H:\SAFETY_SNAPSHOT\configs\
3. Restore filings from H:\SAFETY_SNAPSHOT\filings\
4. Run integrity_checker.py to validate

## NEVER DELETE (under any circumstance)
- litigation_context.db
- 06_EMERGENCY/
- 01_COA_366810/ through 05_BAR_BARNES/
- .agents/ (agent definitions)
- skills/ (permanent skill library)
