@echo off
setlocal
cd /d %~dp0
call .venv\Scripts\activate

echo Enter UNDO JSON path (printed after apply as UNDO_PATH=)
set /p UNDOP=UNDO_PATH:
echo SAFETY GATE: Type UNDO to proceed
set /p CONFIRM=CONFIRM:
if /i not "%CONFIRM%"=="UNDO" (
  echo Cancelled
  pause
  exit /b 0
)
python gdrive_scoped_organizer.py --mode undo --undo "%UNDOP%"
pause
