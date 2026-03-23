@echo off
cd C:\Users\andre
echo Starting quick consolidation... > consolidation_log.txt
python quick_consolidate.py >> consolidation_log.txt 2>&1
echo. >> consolidation_log.txt
echo ========================================== >> consolidation_log.txt
echo Starting comprehensive consolidation... >> consolidation_log.txt
python consolidate_evidence.py >> consolidation_log.txt 2>&1
echo Done. >> consolidation_log.txt
