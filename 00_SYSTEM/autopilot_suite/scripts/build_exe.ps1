\
param(
  [string]$Venv = ".\.venv",
  [string]$Entry = "scripts\litigationos_autopilot.py",
  [string]$Name = "LitigationOS_AutopilotSuite"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $Venv)) {
  python -m venv $Venv
}
& "$Venv\Scripts\pip.exe" install -r requirements.txt
& "$Venv\Scripts\pip.exe" install pyinstaller

pyinstaller --noconfirm --clean --onefile --name $Name $Entry

Write-Host "Built: dist\$Name.exe"
