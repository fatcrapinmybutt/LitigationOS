@echo off
setlocal enabledelayedexpansion
cd /d %~dp0

echo [GDRIVE 00_SETUP] Create venv and install deps (2 attempts)
if not exist .venv (
  python -m venv .venv
  if errorlevel 1 (
    echo ERROR: venv creation failed
    pause
    exit /b 1
  )
)

call .venv\Scripts\activate
python -m pip install --upgrade pip

python -m pip install -r requirements.txt
if errorlevel 1 (
  echo Attempt 1 failed. Attempt 2
  python -m pip install -r requirements.txt
  if errorlevel 1 (
    echo ERROR: requirements install failed twice
    pause
    exit /b 1
  )
)

echo Setup complete
pause
