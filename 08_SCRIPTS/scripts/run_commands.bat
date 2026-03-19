@echo off
setlocal enabledelayedexpansion

set PYTHONUTF8=1

cd /d C:\Users\andre\LitigationOS\00_SYSTEM\tools

echo === STEP 1: Current Directory ===
cd

echo.
echo === STEP 2: Running env-check ===
python safe_shell.py env-check
echo Exit code: %ERRORLEVEL%

echo.
echo === STEP 3: Running shadow-audit ===
python safe_shell.py shadow-audit
echo Exit code: %ERRORLEVEL%

echo.
echo === STEP 4: Running check command ===
python safe_shell.py check C:\Users\andre\LitigationOS\00_SYSTEM\org_agents\__init__.py
echo Exit code: %ERRORLEVEL%

endlocal
pause
