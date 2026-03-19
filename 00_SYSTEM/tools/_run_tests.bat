@echo off
set PYTHONUTF8=1
cd /d C:\Users\andre\LitigationOS\00_SYSTEM\tools

echo ============================================ > _test_output.txt 2>&1
echo COMMAND 1: env-check >> _test_output.txt 2>&1
echo ============================================ >> _test_output.txt 2>&1
python safe_shell.py env-check >> _test_output.txt 2>&1
echo. >> _test_output.txt 2>&1
echo EXIT CODE: %ERRORLEVEL% >> _test_output.txt 2>&1
echo. >> _test_output.txt 2>&1

echo ============================================ >> _test_output.txt 2>&1
echo COMMAND 2: shadow-audit >> _test_output.txt 2>&1
echo ============================================ >> _test_output.txt 2>&1
python safe_shell.py shadow-audit >> _test_output.txt 2>&1
echo. >> _test_output.txt 2>&1
echo EXIT CODE: %ERRORLEVEL% >> _test_output.txt 2>&1
echo. >> _test_output.txt 2>&1

echo ============================================ >> _test_output.txt 2>&1
echo COMMAND 3: check __init__.py >> _test_output.txt 2>&1
echo ============================================ >> _test_output.txt 2>&1
python safe_shell.py check C:\Users\andre\LitigationOS\00_SYSTEM\org_agents\__init__.py >> _test_output.txt 2>&1
echo. >> _test_output.txt 2>&1
echo EXIT CODE: %ERRORLEVEL% >> _test_output.txt 2>&1
echo. >> _test_output.txt 2>&1

echo ALL DONE >> _test_output.txt 2>&1
