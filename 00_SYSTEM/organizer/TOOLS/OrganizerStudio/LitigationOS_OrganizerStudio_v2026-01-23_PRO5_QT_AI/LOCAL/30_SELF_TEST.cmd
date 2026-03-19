@echo off
setlocal
cd /d %~dp0
call .venv\Scripts\activate

echo [30_SELF_TEST] Attempt 1
python self_test.py
if errorlevel 1 (
  echo Attempt 1 failed. Attempt 2
  python self_test.py
)

pause
