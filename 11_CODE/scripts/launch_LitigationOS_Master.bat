@echo off
REM launch_LitigationOS_Master.bat - Top-level LitigationOS launcher (v4)
setlocal ENABLEDELAYEDEXPANSION
set PYTHON_EXE=python

REM Optional override:
REM set LITIGATIONOS_BASE_DIR=D:\LitigationOS

set BASE_DIR=F:\LitigationOS
if not "%LITIGATIONOS_BASE_DIR%"=="" (
  set BASE_DIR=%LITIGATIONOS_BASE_DIR%
)

set SCRIPT=%BASE_DIR%\code\litigationos_master_launcher.py

echo LitigationOS Master Launcher (v4)
echo Base dir: %BASE_DIR%
echo.

if not exist "%SCRIPT%" (
  echo [ERROR] Missing: %SCRIPT%
  echo If installed elsewhere, set LITIGATIONOS_BASE_DIR then re-run.
  pause
  exit /b 1
)

cd /d "%BASE_DIR%"
"%PYTHON_EXE%" "%SCRIPT%" --base-dir "%BASE_DIR%"
echo.
pause
endlocal
