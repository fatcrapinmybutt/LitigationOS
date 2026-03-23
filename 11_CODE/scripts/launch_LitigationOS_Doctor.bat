@echo off
REM launch_LitigationOS_Doctor.bat - One-click readiness gate (v4)
setlocal ENABLEDELAYEDEXPANSION
set PYTHON_EXE=python

set BASE_DIR=F:\LitigationOS
if not "%LITIGATIONOS_BASE_DIR%"=="" (
  set BASE_DIR=%LITIGATIONOS_BASE_DIR%
)

set SCRIPT=%BASE_DIR%\code\doctor.py

echo LitigationOS Doctor (v4)
echo Base dir: %BASE_DIR%
echo.

if not exist "%SCRIPT%" (
  echo [ERROR] Missing: %SCRIPT%
  pause
  exit /b 1
)

cd /d "%BASE_DIR%"
"%PYTHON_EXE%" "%SCRIPT%" --base-dir "%BASE_DIR%"
echo.
pause
endlocal
