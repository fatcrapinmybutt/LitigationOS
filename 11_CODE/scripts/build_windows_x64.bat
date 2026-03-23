@echo off
setlocal enabledelayedexpansion
REM LitigationOS Mainframe x64 build helper (Windows)
REM Assumes python>=3.10 on PATH and executed from repo root.
REM Produces dist\LitigationOS_Cockpit\LitigationOS_Cockpit.exe

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

REM Build (PyInstaller)
python -m pip install pyinstaller
pyinstaller tools\pyinstaller_litigationos.spec --noconfirm

echo.
echo Build complete. Output folder:
echo   dist\LitigationOS_Cockpit\
echo.
endlocal
