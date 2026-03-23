@echo off
echo Starting ZIP extraction in background...
echo Log file: C:\Users\andre\Scans\extracts_full\EXTRACTION_LOG.txt
echo.
start /B python "C:\Users\andre\Scans\extracts_full\final_extraction.py" > "C:\Users\andre\Scans\extracts_full\stdout.txt" 2> "C:\Users\andre\Scans\extracts_full\stderr.txt"
echo.
echo Process started. Check EXTRACTION_LOG.txt for progress.
echo Output: C:\users\andre\LITIGATIONOS_MASTER\OMNI_HARVEST_20260216_0357\07_EXTRACTIONS\
