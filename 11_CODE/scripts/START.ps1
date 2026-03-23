\
param(
  [int]$Port = 8787
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Write-Info($msg) { Write-Host "[START] $msg" -ForegroundColor Cyan }
function Write-Warn($msg) { Write-Host "[WARN]  $msg" -ForegroundColor Yellow }
function Write-Err($msg)  { Write-Host "[ERR]   $msg" -ForegroundColor Red }

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)  # ...\scripts -> project root
Set-Location $Root

Write-Info "Project root: $Root"

# Ensure .env exists
if (!(Test-Path ".\.env")) {
  if (Test-Path ".\.env.example") {
    Copy-Item ".\.env.example" ".\.env" -Force
    Write-Info "Created .env from .env.example. Edit .env if you want to change ports/paths/secrets."
  } else {
    Write-Warn ".env.example not found; continuing without .env."
  }
}

# Load .env into process environment (simple KEY=VALUE lines)
if (Test-Path ".\.env") {
  Get-Content ".\.env" | ForEach-Object {
    $line = $_.Trim()
    if ($line -eq "" -or $line.StartsWith("#")) { return }
    if ($line -match "^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)\s*$") {
      $k = $Matches[1]
      $v = $Matches[2]
      # strip optional quotes
      if (($v.StartsWith('"') -and $v.EndsWith('"')) -or ($v.StartsWith("'") -and $v.EndsWith("'"))) {
        $v = $v.Substring(1, $v.Length-2)
      }
      [System.Environment]::SetEnvironmentVariable($k, $v, "Process")
    }
  }
}

# Override port if passed
[System.Environment]::SetEnvironmentVariable("WEBHOOK_PORT", "$Port", "Process")

# Ensure Node exists (try winget LTS if missing)
try {
  $nodeVer = & node --version 2>$null
  Write-Info "Node: $nodeVer"
} catch {
  Write-Warn "Node.js not found. Attempting 'winget install OpenJS.NodeJS.LTS' (free) ..."
  $winget = Get-Command winget -ErrorAction SilentlyContinue
  if ($null -eq $winget) {
    Write-Err "winget not available. Install Node.js LTS, then rerun START.ps1."
    exit 1
  }
  & winget install OpenJS.NodeJS.LTS -e --accept-package-agreements --accept-source-agreements
  $nodeVer = & node --version
  Write-Info "Node installed: $nodeVer"
}

# Install dependencies if needed
if (!(Test-Path ".\node_modules")) {
  Write-Info "Installing npm dependencies..."
  & npm install
} else {
  Write-Info "node_modules exists; skipping npm install."
}

Write-Info "Starting webhook gateway on http://127.0.0.1:$Port ..."
Write-Info "Press Ctrl+C to stop."

& npm run gateway
