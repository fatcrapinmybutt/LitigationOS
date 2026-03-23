Param(
  [Parameter(Mandatory=$false)][ValidateSet("BuildOnly","BuildAndOpen")][string]$Mode="BuildOnly",
  [Parameter(Mandatory=$false)][int]$Retry=0
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Log($msg) {
  $ts = Get-Date -Format "yyyy-MM-ddTHH:mm:ss"
  Write-Host "[$ts] $msg"
}

# Root = ...\SuperBloom_STACK_v2026-01-23.1\
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = Resolve-Path (Join-Path $ScriptDir "..")
Set-Location $Root

$OutDir = Join-Path $Root "OUT\CYCLE_06"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$Venv = Join-Path $Root ".venv"
$PyExe = Join-Path $Venv "Scripts\python.exe"
$PipExe = Join-Path $Venv "Scripts\pip.exe"

# --- Attempt 1: create venv + install deps
try {
  if (-not (Test-Path $PyExe)) {
    Write-Log "Creating venv at $Venv"
    python -m venv $Venv
  } else {
    Write-Log "Venv already exists: $Venv"
  }

  Write-Log "Upgrading pip"
  & $PyExe -m pip install --upgrade pip | Out-Host

  Write-Log "Installing requirements"
  & $PipExe install -r (Join-Path $Root "SCRIPTS\requirements.txt") | Out-Host
} catch {
  Write-Log "Dependency install failed: $($_.Exception.Message)"
  if ($Retry -lt 1) {
    Write-Log "Retrying dependency install with no-cache-dir"
    & $PyExe -m pip install --upgrade pip --no-cache-dir | Out-Host
    & $PipExe install --no-cache-dir -r (Join-Path $Root "SCRIPTS\requirements.txt") | Out-Host
  } else {
    throw
  }
}

# --- Input discovery (Attempt 1: adjacent; Attempt 2: bounded scan on F:\)
function Find-Input($fileName) {
  $candidates = @(
    (Join-Path $Root $fileName),
    (Join-Path $Root "..\$fileName"),
    (Join-Path $Root "INPUTS\$fileName"),
    (Join-Path $Root "SOURCES\$fileName"),
    (Join-Path $Root "UPLOADS\$fileName")
  )
  foreach ($c in $candidates) {
    if (Test-Path $c) { return (Resolve-Path $c).Path }
  }

  # bounded scan (Attempt 2)
  $drive = "F:\"
  if (Test-Path $drive) {
    Write-Log "Scanning $drive for $fileName (bounded)..."
    $found = Get-ChildItem -LiteralPath $drive -Recurse -File -Filter $fileName -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($found) { return $found.FullName }
  }
  return $null
}

$ScaoZip = Find-Input "SCAO FORMS.zip"
$McrZip  = Find-Input "michigan-court-rules.zip"

if (-not $ScaoZip) { throw "Missing required input: SCAO FORMS.zip (place it near the pack or anywhere under F:\)" }
if (-not $McrZip)  { throw "Missing required input: michigan-court-rules.zip (place it near the pack or anywhere under F:\)" }

Write-Log "Inputs:"
Write-Log "  SCAO: $ScaoZip"
Write-Log "  MCR : $McrZip"

# Build
Write-Log "Running builder"
& $PyExe (Join-Path $Root "SCRIPTS\sb_cycle06_builder.py") `
  --scao-forms-zip $ScaoZip `
  --michigan-court-rules-zip $McrZip `
  --out-dir $OutDir | Out-Host

if ($Mode -eq "BuildAndOpen") {
  $Viewer = Join-Path $Root "VIEWERS\SuperBloom_ERD_Superset_v2026-01-23.1.html"
  if (Test-Path $Viewer) {
    Write-Log "Opening viewer"
    Start-Process $Viewer | Out-Null
  }
}

Write-Log "DONE"
