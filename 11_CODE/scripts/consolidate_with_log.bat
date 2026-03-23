@echo off
REM Evidence Consolidation Batch Runner
cd /d C:\Users\andre

echo === EVIDENCE CONSOLIDATION START === > consolidation_progress.log
echo Start Time: %date% %time% >> consolidation_progress.log
echo. >> consolidation_progress.log

echo Running quick_consolidate.py... >> consolidation_progress.log
python quick_consolidate.py >> consolidation_progress.log 2>&1
echo Quick consolidate return code: %ERRORLEVEL% >> consolidation_progress.log
echo. >> consolidation_progress.log

echo Running consolidate_evidence.py... >> consolidation_progress.log
python consolidate_evidence.py >> consolidation_progress.log 2>&1
echo Comprehensive consolidate return code: %ERRORLEVEL% >> consolidation_progress.log
echo. >> consolidation_progress.log

echo === CONSOLIDATION COMPLETE === >> consolidation_progress.log
echo End Time: %date% %time% >> consolidation_progress.log
echo. >> consolidation_progress.log

echo Checking output files... >> consolidation_progress.log
if exist MASTER_CONSOLIDATED_EVIDENCE.csv (
    echo [✓] MASTER_CONSOLIDATED_EVIDENCE.csv created >> consolidation_progress.log
) else (
    echo [✗] MASTER_CONSOLIDATED_EVIDENCE.csv NOT FOUND >> consolidation_progress.log
)

if exist EVIDENCE_INDEX.md (
    echo [✓] EVIDENCE_INDEX.md created >> consolidation_progress.log
) else (
    echo [✗] EVIDENCE_INDEX.md NOT FOUND >> consolidation_progress.log
)

if exist TIMELINE_MASTER.csv (
    echo [✓] TIMELINE_MASTER.csv created >> consolidation_progress.log
) else (
    echo [✗] TIMELINE_MASTER.csv NOT FOUND >> consolidation_progress.log
)

if exist HARM_LEDGER.csv (
    echo [✓] HARM_LEDGER.csv created >> consolidation_progress.log
) else (
    echo [✗] HARM_LEDGER.csv NOT FOUND >> consolidation_progress.log
)

echo. >> consolidation_progress.log
echo === BATCH SCRIPT COMPLETE === >> consolidation_progress.log
