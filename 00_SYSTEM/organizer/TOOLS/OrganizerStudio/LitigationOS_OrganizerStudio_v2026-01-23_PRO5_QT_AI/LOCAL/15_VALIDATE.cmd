@echo off
setlocal
cd /d %~dp0
call .venv\Scripts\activate

for /f "usebackq delims=" %%A in (`python -c "from pathlib import Path; p=Path(r'F:\LitigationOS\_OrganizeAI\LAST_RUN.txt'); print(p.read_text().strip() if p.exists() else '')"`) do set LAST=%%A
if "%LAST%"=="" (
  echo Could not find LAST_RUN.txt.
  echo Enter the RUN folder path (e.g., F:\LitigationOS\_OrganizeAI\RUN_20260122_120000)
  set /p RUNDIR=RUN_DIR:
) else (
  set RUNDIR=%LAST%
)

python plan_validator.py --plan "%RUNDIR%\plan.csv"
pause
