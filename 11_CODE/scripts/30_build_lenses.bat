@echo off
setlocal
cd /d "%~dp0.."
echo === BUILD LENSES.JSON (dynamic) ===
python TOOLS\build_lenses.py
pause
