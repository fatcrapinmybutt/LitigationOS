Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Assert-Admin {
  $currentIdentity = [Security.Principal.WindowsIdentity]::GetCurrent()
  $principal = New-Object Security.Principal.WindowsPrincipal($currentIdentity)
  if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw "This step requires an elevated PowerShell (Run as Administrator)."
  }
}

function Write-Stage($msg) {
  Write-Host ""
  Write-Host ("=" * 78)
  Write-Host $msg
  Write-Host ("=" * 78)
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BaseDir = "F:\CAPSTONE"

Write-Stage "CAPSTONE_BRIDGE_PACK v2026-01-23.1 — Orchestrator"
Write-Host "BaseDir: $BaseDir"
Write-Host "ScriptDir: $ScriptDir"

# Step 1: hosts setup (admin)
Write-Stage "1/6 — Hosts setup (case.test, api.case.test, cite.case.test)"
Assert-Admin
& (Join-Path $ScriptDir "10_Hosts_Add.ps1") -BaseDir $BaseDir

# Step 2: clone + docker up
Write-Stage "2/6 — Clone Capstone + docker compose up"
& (Join-Path $ScriptDir "20_Clone_And_DockerUp.ps1") -BaseDir $BaseDir

# Step 3: create databases
Write-Stage "3/6 — Create Postgres databases"
& (Join-Path $ScriptDir "30_Create_Databases.ps1") -BaseDir $BaseDir

# Step 4: init dev db + ingest fixtures (optional but recommended)
Write-Stage "4/6 — Init dev DB + ingest fixtures + rebuild search index (may take a while)"
& (Join-Path $ScriptDir "40_Init_Dev_Db_And_Ingest.ps1") -BaseDir $BaseDir

# Step 5: run server (starts in foreground inside container)
Write-Stage "5/6 — Start dev server (fab run) in container"
Write-Host "This step will attach to the container and run the dev server. Press Ctrl+C to stop."
& (Join-Path $ScriptDir "50_Run_Server.ps1") -BaseDir $BaseDir

Write-Stage "6/6 — Done"
