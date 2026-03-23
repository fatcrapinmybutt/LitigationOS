@echo off
setlocal
REM LitigationOS Autopilot — PEAK Windows launcher
REM Creates a local venv and installs python deps for extraction (if needed)

python bootstrap.py -- run --auto --profile peak --stages inventory,unpack,ocr,convert,chunk %*
if errorlevel 1 (
  echo.
  echo Autopilot PEAK failed. Inspect ./out/RUN_*/RUN_LEDGER.jsonl
  exit /b 1
)
endlocal
