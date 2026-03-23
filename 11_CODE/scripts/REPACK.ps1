$ErrorActionPreference="Stop"
$root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $root

$venv = Join-Path $root ".venv"
if (Test-Path $venv) {
  . (Join-Path $venv "Scripts\Activate.ps1")
}

python (Join-Path $root "scripts\REPACK.py")
Write-Host "Done. Output: REPACKED.zip" -ForegroundColor Green
