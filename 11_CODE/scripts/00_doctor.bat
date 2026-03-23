@echo off
setlocal
cd /d "%~dp0.."
echo === SUPERGRAPH DOCTOR ===
python APP\doctor.py
pause
