@echo off
setlocal
cd /d %~dp0
call .venv\Scripts\activate

echo Enter plan JSON path to validate
set /p PLANP=PLAN_PATH:
python gdrive_scoped_organizer.py --validate "%PLANP%"
pause
