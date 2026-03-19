@echo off
setlocal
cd /d %~dp0
call .venv\Scripts\activate

echo Enter plan JSON path to apply
set /p PLANP=PLAN_PATH:
echo SAFETY GATE: Type APPLY to proceed
set /p CONFIRM=CONFIRM:
if /i not "%CONFIRM%"=="APPLY" (
  echo Cancelled
  pause
  exit /b 0
)
python gdrive_scoped_organizer.py --mode apply --plan "%PLANP%"
pause
