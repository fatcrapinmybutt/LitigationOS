@echo off
setlocal
REM LitigationOS Autopilot — Windows launcher
REM Requires python in PATH. If you prefer uv: uv run -m autopilot scan --auto

python -m autopilot scan --auto %*
if errorlevel 1 (
  echo.
  echo Autopilot failed. See ./out/RUN_*/RUN_LEDGER.jsonl for details.
  exit /b 1
)
endlocal
