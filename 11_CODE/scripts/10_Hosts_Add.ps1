param(
  [Parameter(Mandatory=$true)][string]$BaseDir
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$hostsPath = "$env:WINDIR\System32\drivers\etc\hosts"
if (-not (Test-Path $hostsPath)) { throw "Hosts file not found at: $hostsPath" }

$required = @(
  "127.0.0.1`tcase.test",
  "127.0.0.1`tapi.case.test",
  "127.0.0.1`tcite.case.test"
)

$content = Get-Content -Path $hostsPath -ErrorAction Stop
$missing = @()
foreach ($line in $required) {
  $host = ($line -split "\s+")[1]
  $present = $false
  foreach ($c in $content) {
    if ($c -match "^\s*127\.0\.0\.1\s+$([regex]::Escape($host))(\s|$)") { $present = $true; break }
  }
  if (-not $present) { $missing += $line }
}

if ($missing.Count -eq 0) {
  Write-Host "Hosts entries already present."
  exit 0
}

Write-Host "Appending to hosts file:"
$missing | ForEach-Object { Write-Host "  $_" }

Add-Content -Path $hostsPath -Value "`r`n# Capstone dev hosts`r`n" -Encoding ASCII
foreach ($m in $missing) {
  Add-Content -Path $hostsPath -Value $m -Encoding ASCII
}

Write-Host "Hosts update complete."
