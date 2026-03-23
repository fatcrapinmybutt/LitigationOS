@echo off
setlocal enabledelayedexpansion
REM PIGGY_ONE_CLICK_RUN.bat — v2026-01-14.2
REM One-click: venv -> install deps -> run pipeline

cd /d "%~dp0\.."

set PY=python
where %PY% >nul 2>nul
if errorlevel 1 (
  echo FAIL: python not found on PATH. Install Python 3.11+ and re-run.
  exit /b 1
)

set VENV=.venv
if not exist "%VENV%\Scripts\python.exe" (
  echo Creating venv...
  %PY% -m venv "%VENV%"
  if errorlevel 1 exit /b 1
)

echo Installing/upgrading deps...
"%VENV%\Scripts\python.exe" -m pip install --upgrade pip >nul
"%VENV%\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 exit /b 1

REM Optional env override for ChatGPT export zip/folder
REM set CHATGPT_EXPORT_ZIP=C:\path\chatgpt-export.zip

set EXTRA=
if not "%CHATGPT_EXPORT_ZIP%"=="" (
  set EXTRA=--chatgpt-export "%CHATGPT_EXPORT_ZIP%"
)

REM Optional: set GDRIVE_SYNC=1 to enable
set GSYNC=
if "%GDRIVE_SYNC%"=="1" (
  set GSYNC=--gdrive-sync
)

echo Running...
"%VENV%\Scripts\python.exe" RUN_ALL_SCRAPE_COMPILE.py --config "config\defaults.json" %GSYNC% %EXTRA% --run
echo Done.
endlocal
