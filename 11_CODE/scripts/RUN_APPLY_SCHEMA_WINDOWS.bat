@echo off
setlocal
cd /d %~dp0\..
if not exist .venv\Scripts\python.exe (
  echo ERROR: venv missing. Create it:
  echo   python -m venv .venv
  echo   .\.venv\Scripts\Activate.ps1
  echo   python -m pip install -r requirements.txt
  exit /b 2
)
.venv\Scripts\python.exe run_pipeline.py apply-schema --cypher-dir cypher --out out\stats
if errorlevel 1 exit /b %errorlevel%
echo.
echo PASS: schema applied (see out\stats\neo4j_apply_report.json)
endlocal
