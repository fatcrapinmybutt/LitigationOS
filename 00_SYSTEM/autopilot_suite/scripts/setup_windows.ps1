\
param(
  [string]$Venv = ".\.venv"
)
$ErrorActionPreference = "Stop"
if (-not (Test-Path $Venv)) { python -m venv $Venv }
& "$Venv\Scripts\pip.exe" install -r requirements.txt
Write-Host "Ready. Use: $Venv\Scripts\python.exe scripts\litigationos_autopilot.py --help"
