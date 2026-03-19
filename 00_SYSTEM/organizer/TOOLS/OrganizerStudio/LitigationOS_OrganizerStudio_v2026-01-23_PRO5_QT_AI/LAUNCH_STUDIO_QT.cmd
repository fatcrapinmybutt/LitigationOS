@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

echo OrganizerStudio QT launcher

set "VENV=%~dp0.venv"
set "PY=%VENV%\Scripts\python.exe"

if not exist "%PY%" (
  echo Creating venv at "%VENV%"...
  py -3.12 -m venv "%VENV%" >nul 2>nul
  if errorlevel 1 (
    python -m venv "%VENV%"
  )
  if errorlevel 1 (
    echo ERROR: venv creation failed
    pause
    exit /b 1
  )
)

echo Using: "%PY%"

"%PY%" -m pip install --upgrade pip
if errorlevel 1 (
  echo ERROR: pip upgrade failed
  pause
  exit /b 1
)

"%PY%" -m pip install -r requirements_min.txt
if errorlevel 1 (
  echo Attempt 1 failed. Attempt 2
  "%PY%" -m pip install -r requirements_min.txt
  if errorlevel 1 (
    echo ERROR: dependency install failed twice
    pause
    exit /b 1
  )
)

"%PY%" -u OrganizerStudio_Qt.py
set "RC=%ERRORLEVEL%"

if not "%RC%"=="0" (
  echo.
  echo ERROR: OrganizerStudio_Qt.py exited with code %RC%
  echo.
  echo If this was a PySide6/Qt DLL issue, check:
  echo   F:\LitigationOS\_OrganizeAI\STUDIO\logs\startup.log
  echo.
  pause
  exit /b %RC%
)

exit /b 0
