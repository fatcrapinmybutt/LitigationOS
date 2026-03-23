#requires -Version 7.0
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$extFile = Join-Path (Resolve-Path .) ".vscode/extensions.json"
if (-not (Test-Path $extFile)) {
  throw "Missing $extFile. Apply the pack first."
}

$cfg = Get-Content -Raw -Path $extFile -Encoding UTF8 | ConvertFrom-Json -Depth 10
$recs = @($cfg.recommendations)
if (-not $recs -or $recs.Count -eq 0) {
  Write-Output "No recommendations found."
  exit 0
}

foreach ($e in $recs) {
  Write-Output "Installing $e ..."
  try {
    & code --install-extension $e --force | Out-Host
  } catch {
    Write-Warning "Failed to install $e: $($_.Exception.Message)"
  }
}
Write-Output "Done."
