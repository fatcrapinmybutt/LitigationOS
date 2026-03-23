param(
  [switch]$Install,
  [switch]$Uninstall,
  [int]$EveryMinutes = 60,
  [string]$OutputRoot = ""
)

$ErrorActionPreference = "Stop"

function Ensure-OutputRoot {
  if ([string]::IsNullOrWhiteSpace($OutputRoot)) {
    $OutputRoot = (Join-Path (Get-Location) "RUNS")
  }
  if (!(Test-Path $OutputRoot)) { New-Item -ItemType Directory -Path $OutputRoot | Out-Null }
  return $OutputRoot
}

$taskName = "LitigationOS_HarvestEngine"
$cwd = (Get-Location).Path
$py = Join-Path $cwd ".venv\Scripts\python.exe"
if (!(Test-Path $py)) {
  # fallback to system python
  $py = "python"
}
$OutputRoot = Ensure-OutputRoot

$tr = "$py -m scripts.lo_run run --output-root `"$OutputRoot`" --mode scheduled --enable-ocr --enable-rclone-pull"
$startIn = $cwd

if ($Install) {
  # Create task: repeat every N minutes
  $cmd = "schtasks /Create /F /TN `"$taskName`" /SC MINUTE /MO $EveryMinutes /TR `"$tr`" /RL HIGHEST /RU `"$env:USERNAME`" /NP"
  Write-Host $cmd
  cmd.exe /c $cmd | Out-Host
  Write-Host "Installed: $taskName"
  exit 0
}

if ($Uninstall) {
  $cmd = "schtasks /Delete /F /TN `"$taskName`""
  Write-Host $cmd
  cmd.exe /c $cmd | Out-Host
  Write-Host "Removed: $taskName"
  exit 0
}

Write-Host "Use -Install or -Uninstall"
exit 1
