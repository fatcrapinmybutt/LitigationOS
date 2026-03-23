@echo off
REM launch_evidence_rag_lane_dryrun.bat - Core v4

setlocal ENABLEDELAYEDEXPANSION

set PYTHON_EXE=python
set BASE_DIR=F:\LitigationOS
set SCRIPT_DIR=%BASE_DIR%\code

echo Evidence RAG lane DRY-RUN launcher (Core v4)
echo -------------------------------------------
echo Expected assertions file:
echo   %BASE_DIR%\inputs\assertions.txt
echo.

if not exist "%BASE_DIR%\inputs\assertions.txt" (
  echo [ERROR] assertions file not found at %BASE_DIR%\inputs\assertions.txt
  echo Create it (one assertion per line) and re-run.
  pause
  exit /b 1
)

cd /d "%SCRIPT_DIR%"
echo Running pipeline in DRY-RUN mode...
"%PYTHON_EXE%" "%SCRIPT_DIR%\run_evidence_rag_lane.py" --base-dir "%BASE_DIR%" --assertions-path "%BASE_DIR%\inputs\assertions.txt" --dry-run
echo.
echo Done (DRY-RUN). Check:
echo   %BASE_DIR%\logs
echo.
pause
endlocal
