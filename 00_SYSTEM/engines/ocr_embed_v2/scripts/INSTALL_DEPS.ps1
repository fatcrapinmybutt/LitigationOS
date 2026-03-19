param()
$ErrorActionPreference="Stop"
$root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $root

$py = $null
try { $py = (Get-Command py -ErrorAction Stop).Source } catch { }
if ($py) { $pythonCmd = "py -3" } else { $pythonCmd = "python" }

$venv = Join-Path $root ".venv"
if (!(Test-Path $venv)) { & $pythonCmd -m venv $venv }

. (Join-Path $venv "Scripts\Activate.ps1")
python -m pip install --upgrade pip wheel setuptools
pip install -r (Join-Path $root "requirements.txt")
pip install -e $root
Write-Host "Dependencies installed." -ForegroundColor Green
