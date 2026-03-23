\
@echo off
setlocal
cd /d "%~dp0..\"
echo.
echo === SUPERGRAPH AUTO-PRELOAD (SQLite + Viewer) ===
echo.
python preload_all.py --port 8799
