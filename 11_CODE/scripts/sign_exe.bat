@echo off
SETLOCAL ENABLEDELAYEDEXPANSION
set ROOT=%~dp0..
set EXE=%ROOT%\dist\LitigationOS\LitigationOS.exe
if not exist "%EXE%" (
  echo ERROR: EXE not found: %EXE%
  exit /b 1
)
if "%SIGN_CERT_PFX%"=="" (
  echo SIGN_CERT_PFX not set.
  echo Example (Cert Store auto): signtool sign /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 /a "%EXE%"
  pause
  exit /b 1
)
if "%SIGN_CERT_PASS%"=="" (
  echo SIGN_CERT_PASS not set.
  pause
  exit /b 1
)
signtool sign /f "%SIGN_CERT_PFX%" /p "%SIGN_CERT_PASS%" /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 "%EXE%"
pause
