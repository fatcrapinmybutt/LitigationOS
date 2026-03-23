Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

param(
  [Parameter(Mandatory=$false)][string]$LocalRoot = "",
  [Parameter(Mandatory=$false)][string]$RemoteName = "",
  [Parameter(Mandatory=$false)][string]$RemotePath = "",
  [Parameter(Mandatory=$false)][ValidateSet("bisync","sync","copy")][string]$Mode = "bisync",
  [Parameter(Mandatory=$false)][string]$ExtraArgs = ""
)

function Resolve-RcloneExe {
  if ($env:RCLONE_EXE -and (Test-Path $env:RCLONE_EXE)) { return $env:RCLONE_EXE }
  $cmd = Get-Command rclone -ErrorAction SilentlyContinue
  if ($cmd) { return $cmd.Source }
  $candidates = @(
    (Join-Path $PSScriptRoot "rclone.exe"),
    (Join-Path $PSScriptRoot "rclone\rclone.exe"),
    "C:\Users\andre\Rclone\rclone.exe"
  )
  foreach ($c in $candidates) { if (Test-Path $c) { return $c } }
  return ""
}

$rclone = Resolve-RcloneExe
if (-not $rclone) {
  Write-Host "ERROR: rclone.exe not found. Set `$env:RCLONE_EXE or put rclone.exe in project root." -ForegroundColor Red
  exit 2
}

if (-not $LocalRoot) { $LocalRoot = $env:RCLONE_LOCAL }
if (-not $RemoteName) { $RemoteName = $env:RCLONE_REMOTE }
if (-not $RemotePath) { $RemotePath = $env:RCLONE_DEST }

if (-not $LocalRoot -or -not (Test-Path $LocalRoot)) {
  Write-Host "ERROR: LocalRoot missing or does not exist. Provide -LocalRoot or set RCLONE_LOCAL." -ForegroundColor Red
  exit 2
}
if (-not $RemoteName -or -not $RemotePath) {
  Write-Host "ERROR: RemoteName/RemotePath missing. Provide -RemoteName/-RemotePath or set RCLONE_REMOTE/RCLONE_DEST." -ForegroundColor Red
  exit 2
}

$remoteSpec = "$RemoteName`:$RemotePath"
$logDir = Join-Path $PSScriptRoot "RUNS"
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir | Out-Null }
$logFile = Join-Path $logDir ("rclone_" + (Get-Date -Format "yyyyMMdd_HHmmss") + ".log")

$common = @(
  "--log-file", $logFile,
  "--log-level", "INFO",
  "--fast-list",
  "--create-empty-src-dirs"
)

switch ($Mode) {
  "bisync" {
    $args = @("bisync", $LocalRoot, $remoteSpec, "--resync") + $common
  }
  "sync" {
    $args = @("sync", $LocalRoot, $remoteSpec) + $common
  }
  "copy" {
    $args = @("copy", $LocalRoot, $remoteSpec) + $common
  }
}

if ($ExtraArgs) {
  # Allow user to pass a raw string of extra args (e.g. "--exclude *.tmp --transfers 8")
  $args += ($ExtraArgs -split "\s+")
}

Write-Host ("Running: " + $rclone + " " + ($args -join " "))
& $rclone @args
$code = $LASTEXITCODE
Write-Host ("rclone exit code: " + $code + " | log: " + $logFile)
exit $code
