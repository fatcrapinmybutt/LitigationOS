@echo off
SETLOCAL ENABLEDELAYEDEXPANSION
set ROOT=%~dp0
set PYTHON=python
if exist "%ROOT%\.venv\Scripts\python.exe" set PYTHON="%ROOT%\.venv\Scripts\python.exe"
echo [LitigationOS] Using Python: %PYTHON%
if not exist "%ROOT%\config\config.json" (
  echo ERROR: config\config.json not found.
  pause
  exit /b 1
)
%PYTHON% "%ROOT%\litigationos_cli.py" ingest --config "%ROOT%\config\config.json" || goto fail
%PYTHON% "%ROOT%\litigationos_cli.py" ingest-corpus --config "%ROOT%\config\config.json" || goto fail
%PYTHON% "%ROOT%\litigationos_cli.py" run-contradictions --config "%ROOT%\config\config.json" || goto fail
%PYTHON% "%ROOT%\litigationos_cli.py" export-neo4j --config "%ROOT%\config\config.json" || goto fail
%PYTHON% "%ROOT%\litigationos_cli.py" export-html-offline --config "%ROOT%\config\config.json" || goto fail
echo [LitigationOS] COMPLETE
pause
exit /b 0
:fail
echo [LitigationOS] FAILED
pause
exit /b 1