@echo off
setlocal enabledelayedexpansion

set PYTHONUTF8=1
cd /d C:\Users\andre\LitigationOS\00_SYSTEM\tools

echo Starting test commands... > _test_output.txt
echo Timestamp: %date% %time% >> _test_output.txt
echo. >> _test_output.txt

echo ============================================ >> _test_output.txt
echo COMMAND 1: env-check >> _test_output.txt
echo ============================================ >> _test_output.txt
python safe_shell.py env-check >> _test_output.txt 2>&1
echo. >> _test_output.txt

echo ============================================ >> _test_output.txt
echo COMMAND 2: shadow-audit >> _test_output.txt
echo ============================================ >> _test_output.txt
python safe_shell.py shadow-audit >> _test_output.txt 2>&1
echo. >> _test_output.txt

echo ============================================ >> _test_output.txt
echo COMMAND 3: check __init__.py >> _test_output.txt
echo ============================================ >> _test_output.txt
python safe_shell.py check C:\Users\andre\LitigationOS\00_SYSTEM\org_agents\__init__.py >> _test_output.txt 2>&1
echo. >> _test_output.txt

echo ALL DONE >> _test_output.txt
