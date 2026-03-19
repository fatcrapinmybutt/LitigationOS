@echo off
setlocal
cd /d %~dp0

echo OrganizerStudio launcher

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

python -m pip install -r requirements_studio.txt
if errorlevel 1 (
  echo Attempt 1 failed. Attempt 2
  python -m pip install -r requirements_studio.txt
  if errorlevel 1 (
    echo ERROR: dependency install failed twice
    pause
    exit /b 1
  )
)

python OrganizerStudio_GUI.py
pause
