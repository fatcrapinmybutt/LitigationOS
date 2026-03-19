@echo off
setlocal
set "ROOT=%~dp0"
cd /d "%ROOT%..\"
where pwsh >nul 2>nul
if %ERRORLEVEL%==0 (
  pwsh -NoProfile -ExecutionPolicy Bypass -File "%ROOT%REPACK.ps1"
) else (
  powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT%REPACK.ps1"
)
