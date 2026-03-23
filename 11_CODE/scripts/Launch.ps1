#requires -Version 5.1
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Log([string]$msg) {
  $ts = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
  Write-Host "[$ts] $msg"
}

function Ensure-Dir([string]$p) {
  if (!(Test-Path $p)) { New-Item -ItemType Directory -Path $p | Out-Null }
}

function Run-With-Retry([scriptblock]$Action, [int]$MaxAttempts=2) {
  for ($i=1; $i -le $MaxAttempts; $i++) {
    try { & $Action; return } catch {
      Write-Log "Attempt $i failed: $($_.Exception.Message)"
      if ($i -eq $MaxAttempts) { throw }
      Start-Sleep -Seconds 2
    }
  }
}

$ROOT = "F:\LITIGATIONOS_ENTERPRISE"
$ONECLICK = Join-Path $ROOT "_ONECLICK"
$VENV = Join-Path $ROOT "_venv"
$RUNS = Join-Path $ROOT "08_RUNS"
$LOGS = Join-Path $ROOT "_logs"

Ensure-Dir $ROOT; Ensure-Dir $ONECLICK; Ensure-Dir $VENV; Ensure-Dir $RUNS; Ensure-Dir $LOGS

# Mirror files into _ONECLICK if needed
try {
  $thisDir = Split-Path -Parent $MyInvocation.MyCommand.Path
  if ((Resolve-Path $thisDir).Path -ne (Resolve-Path $ONECLICK).Path) {
    Write-Log "Copying OneClick files into $ONECLICK"
    Copy-Item -Path (Join-Path $thisDir "*") -Destination $ONECLICK -Recurse -Force
  }
} catch { }

# Standard folders
$stableFolders = @(
  "00_INBOX\ZIPS","01_CODE","02_AUTHORITY","03_FORMS","04_LOCAL_PACKETS",
  "05_HARVEST","06_GRAPH","07_VIEWER"
)
foreach ($sf in $stableFolders) { Ensure-Dir (Join-Path $ROOT $sf) }

$PY = "python"
try { & $PY --version | Out-Null } catch { throw "Python not found on PATH. Install Python 3.10+ and retry." }

$VENV_PY = Join-Path $VENV "Scripts\python.exe"
$PIP = Join-Path $VENV "Scripts\pip.exe"

if (!(Test-Path $VENV_PY)) {
  Write-Log "Creating venv: $VENV"
  & $PY -m venv $VENV
}

Write-Log "Upgrading pip"
& $VENV_PY -m pip install --upgrade pip wheel setuptools

Write-Log "Installing requirements"
& $PIP install -r (Join-Path $ONECLICK "requirements.txt")

Run-With-Retry -MaxAttempts 2 -Action {
  Write-Log "Running orchestrator..."
  & $VENV_PY (Join-Path $ONECLICK "governor\run_enterprise.py") --root $ROOT
}

Write-Log "DONE"
