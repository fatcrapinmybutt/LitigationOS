param(
  [string]$Root = (Resolve-Path "$PSScriptRoot\..").Path
)
$ErrorActionPreference = "Stop"
try { python --version | Out-Null } catch { winget install -e --id Python.Python.3.12 }
$venvPy = Join-Path $Root ".venv\Scripts\python.exe"
if (!(Test-Path $venvPy)) { python -m venv (Join-Path $Root ".venv") }
& $venvPy -m pip install --upgrade pip
& $venvPy -m pip install -r (Join-Path $Root "studio\requirements-studio.txt")
& $venvPy -m pip install pyinstaller
Push-Location $Root
& $venvPy -m PyInstaller --noconfirm --onefile --name "LitigOS_Studio_Launcher" (Join-Path $Root "launcher\studio_launcher.py")
Pop-Location
Write-Host "[OK] EXE built at: $Root\dist\LitigOS_Studio_Launcher.exe"
