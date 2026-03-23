@echo off
setlocal
cd /d "%~dp0.."
echo === BUILD SQLITE CACHE ===
python APP\build_sqlite_cache.py
pause
