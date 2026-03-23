@echo off
TITLE Master Evidence Consolidation
COLOR 0A
echo.
echo ================================================================================
echo             MASTER EVIDENCE DATABASE CONSOLIDATION
echo ================================================================================
echo.
echo Cases: 2023-5907-PP and 2024-001507-DC
echo Target: C:\Users\andre\MASTER_CONSOLIDATED_EVIDENCE.csv
echo.
echo Starting consolidation...
echo.

cd /d C:\Users\andre
python RUN_CONSOLIDATION_FINAL.py

echo.
echo ================================================================================
echo Check the output files:
echo   - MASTER_CONSOLIDATED_EVIDENCE.csv
echo   - EVIDENCE_INDEX.md
echo   - TIMELINE_MASTER.csv
echo   - HARM_LEDGER.csv
echo ================================================================================
echo.
pause
