@echo off
REM launch_GovernorPillar.bat - Governor Pillar Master Launcher

setlocal ENABLEDELAYEDEXPANSION

set PYTHON_EXE=python
set BASE_DIR=F:\LitigationOS
set SCRIPT=%BASE_DIR%\governor\governor_pillar_master.py

echo Governor Pillar Master Launcher
echo -------------------------------
echo Base dir: %BASE_DIR%
echo.

if not exist "%SCRIPT%" (
  echo [ERROR] governor_pillar_master.py not found at %SCRIPT%
  echo Make sure the LitigationOS folder structure is correct.
  pause
  exit /b 1
)

cd /d "%BASE_DIR%"
echo Starting interactive Governor Pillar...
"%PYTHON_EXE%" "%SCRIPT%"
echo.
pause
endlocal
