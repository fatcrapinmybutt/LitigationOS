@echo off
REM launch_LexVaultStatus.bat - Build LexVault manifest and show summary

setlocal ENABLEDELAYEDEXPANSION

set PYTHON_EXE=python
set BASE_DIR=F:\LitigationOS
set SCRIPT=%BASE_DIR%\governor\lexvault_manifest_builder.py

echo LexVault Manifest Builder
echo -------------------------
echo Base dir: %BASE_DIR%
echo.

if not exist "%SCRIPT%" (
  echo [ERROR] lexvault_manifest_builder.py not found at %SCRIPT%
  echo Make sure the LitigationOS folder structure is correct.
  pause
  exit /b 1
)

cd /d "%BASE_DIR%"
echo Building LexVault manifest and printing summary...
"%PYTHON_EXE%" "%SCRIPT%" --base-dir "%BASE_DIR%" --summary
echo.
pause
endlocal
