<# 
RUN_ONE_COMMAND.ps1 — single entrypoint runner
- Finds pack root automatically (walks up looking for pyproject.toml + src/litos_harvest)
- Creates/uses venv in .work\venv
- Installs requirements
- Optionally starts Qdrant via Docker (if available) OR uses in-process fallback (SQLite FTS only)
- Runs harvest
#>

param(
  [Parameter(Mandatory=$false)]
  [string[]]$Roots = @("$PWD"),
  [Parameter(Mandatory=$false)]
  [string[]]$Include = @("SCANNED"),
  [Parameter(Mandatory=$false)]
  [string]$Out = "$PWD\out",
  [Parameter(Mandatory=$false)]
  [switch]$NoDockerQdrant,
  [Parameter(Mandatory=$false)]
  [int]$Workers = 4
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Find-PackRoot([string]$start) {
  $cur = (Resolve-Path $start).Path
  while ($true) {
    $pyproj = Join-Path $cur "pyproject.toml"
    $sentinel = Join-Path $cur "src\litos_harvest\main.py"
    if ((Test-Path $pyproj) -and (Test-Path $sentinel)) { return $cur }
    $parent = Split-Path $cur -Parent
    if ($parent -eq $cur -or [string]::IsNullOrWhiteSpace($parent)) { break }
    $cur = $parent
  }
  throw "Pack root not found. Run this from inside the extracted pack folder."
}

function Ensure-Dir([string]$p) {
  if (-not (Test-Path $p)) { New-Item -ItemType Directory -Force -Path $p | Out-Null }
}

function Have-Command([string]$name) {
  $null -ne (Get-Command $name -ErrorAction SilentlyContinue)
}

function Write-Section([string]$t) {
  Write-Host ""
  Write-Host ("=" * 80)
  Write-Host $t
  Write-Host ("=" * 80)
}

$packRoot = Find-PackRoot $PWD
Write-Section "Pack root: $packRoot"
Set-Location $packRoot

$workDir = Join-Path $packRoot ".work"
$venvDir = Join-Path $workDir "venv"
Ensure-Dir $workDir

# Create venv
if (-not (Test-Path (Join-Path $venvDir "Scripts\python.exe"))) {
  Write-Section "Creating venv"
  python -m venv $venvDir
}

$py = Join-Path $venvDir "Scripts\python.exe"
$pip = Join-Path $venvDir "Scripts\pip.exe"

Write-Section "Upgrading pip"
& $py -m pip install --upgrade pip wheel setuptools | Out-Host

Write-Section "Installing requirements"
& $pip install -r "requirements.txt" | Out-Host

# Qdrant (optional)
$qdrantUrl = "http://localhost:6333"
$useQdrant = $true

if ($NoDockerQdrant) { $useQdrant = $false }

if ($useQdrant -and (Have-Command "docker")) {
  Write-Section "Ensuring Qdrant is running via Docker"
  $name = "litos-qdrant"
  $running = (docker ps --format "{{.Names}}" | Select-String -SimpleMatch $name) -ne $null
  if (-not $running) {
    $exists = (docker ps -a --format "{{.Names}}" | Select-String -SimpleMatch $name) -ne $null
    if ($exists) { docker rm -f $name | Out-Null }
    docker run -d --name $name -p 6333:6333 -p 6334:6334 -v "$workDir\qdrant_storage:/qdrant/storage" qdrant/qdrant | Out-Null
    Start-Sleep -Seconds 2
  }
} else {
  $useQdrant = $false
}

# Build args
Ensure-Dir $Out
$rootsArg = ($Roots | ForEach-Object { "`"$($_)`"" }) -join ","
$includeArg = ($Include | ForEach-Object { "`"$($_)`"" }) -join ","

Write-Section "Running harvest"
$args = @(
  "-m","litos_harvest.main",
  "harvest",
  "--roots", $rootsArg,
  "--include", $includeArg,
  "--out", $Out,
  "--workers", "$Workers"
)

if (-not $useQdrant) {
  $args += @("--no-qdrant")
}

& $py @args

Write-Section "DONE"
Write-Host "Output folder: $Out"
