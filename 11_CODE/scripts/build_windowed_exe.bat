@echo off
SETLOCAL ENABLEDELAYEDEXPANSION
set ROOT=%~dp0..
cd /d "%ROOT%"
if not exist .venv\Scripts\python.exe (
  python -m venv .venv || exit /b 1
)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -r requirements-gui.txt
python -m pip install pyinstaller
pyinstaller --clean --noconfirm build\pyinstaller_windowed.spec || exit /b 1
echo Build complete: dist\LitigationOS\LitigationOS.exe
pause
