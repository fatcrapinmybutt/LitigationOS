@echo off
setlocal ENABLEDELAYEDEXPANSION

rem === PublicLitigationOS Harvest Runner (Windows) ===
rem Runs from the folder this file is in.

set "ROOT=%~dp0"
cd /d "%ROOT%"

rem Prefer PowerShell 7 if available, else Windows PowerShell
where pwsh >nul 2>nul
if %ERRORLEVEL%==0 (
  set "PS=pwsh -NoProfile -ExecutionPolicy Bypass"
) else (
  set "PS=powershell -NoProfile -ExecutionPolicy Bypass"
)

%PS% -File "%ROOT%scripts\RUN.ps1"
exit /b %ERRORLEVEL%
