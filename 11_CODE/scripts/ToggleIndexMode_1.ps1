#requires -Version 7.0
<#
ToggleIndexMode.ps1

Switch between:
- perf : exclude common heavy dirs from search + file watchers
- max  : clear those excludes for maximum workspace indexing/context

Usage:
  pwsh tooling/ai/ToggleIndexMode.ps1 -Mode perf
  pwsh tooling/ai/ToggleIndexMode.ps1 -Mode max
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

[CmdletBinding()]
param(
  [ValidateSet("perf","max")]
  [string]$Mode
)

$settingsPath = Join-Path (Resolve-Path .) ".vscode/settings.json"
if (-not (Test-Path $settingsPath)) {
  throw "Missing .vscode/settings.json (apply pack first)."
}

$cfg = Get-Content -Raw -Path $settingsPath -Encoding UTF8 | ConvertFrom-Json -Depth 100

$perfSearch = @{
  "**/node_modules" = $true
  "**/.venv" = $true
  "**/venv" = $true
  "**/__pycache__" = $true
  "**/dist" = $true
  "**/build" = $true
  "**/out" = $true
  "**/coverage" = $true
}
$perfWatch = @{
  "**/node_modules/**" = $true
  "**/.venv/**" = $true
  "**/venv/**" = $true
  "**/__pycache__/**" = $true
  "**/dist/**" = $true
  "**/build/**" = $true
  "**/out/**" = $true
  "**/coverage/**" = $true
}

if ($Mode -eq "perf") {
  $cfg.search = $cfg.search ?? [pscustomobject]@{}
  $cfg.search.exclude = $perfSearch
  $cfg.files = $cfg.files ?? [pscustomobject]@{}
  $cfg.files.watcherExclude = $perfWatch
  Write-Output "Index mode set to PERF (lighter search + watcher load)."
} else {
  if ($cfg.search -and $cfg.search.exclude) { $cfg.search.PSObject.Properties.Remove("exclude") }
  if ($cfg.files -and $cfg.files.watcherExclude) { $cfg.files.PSObject.Properties.Remove("watcherExclude") }
  Write-Output "Index mode set to MAX (no search/watcher excludes)."
}

$cfg | ConvertTo-Json -Depth 100 | Set-Content -Path $settingsPath -Encoding UTF8
