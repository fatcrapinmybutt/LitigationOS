@echo off
setlocal
set OUT=%~dp0RUNS
if not exist "%OUT%" mkdir "%OUT%"
call "%~dp0.venv\Scripts\activate.bat" 2>nul
python -m scripts.lo_run run --output-root "%OUT%" --mode discovery --enable-ocr --enable-rclone-pull
echo.
echo Done. Output: %OUT%
pause
