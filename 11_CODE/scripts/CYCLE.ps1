param(
  [int]$MaxCycles = 25
)
$ErrorActionPreference="Stop"
$root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $root

for ($i=1; $i -le $MaxCycles; $i++) {
  Write-Host "`n=== Cycle $i/$MaxCycles ===`n" -ForegroundColor Cyan
  & (Join-Path $PSScriptRoot "RUN.ps1")
  # Convergence heuristic: stop if inventory hasn't changed (hash comparison)
  $out = Join-Path $root ".out"
  $latest = Get-ChildItem $out -Directory | Sort-Object LastWriteTime -Descending | Select-Object -First 1
  if (!$latest) { break }
  $inv = Join-Path $latest.FullName "inventory.csv"
  if (!(Test-Path $inv)) { continue }
  $hash = (Get-FileHash $inv -Algorithm SHA256).Hash
  $stateFile = Join-Path $root ".work\cycle_state.json"
  $prev = $null
  if (Test-Path $stateFile) { $prev = (Get-Content $stateFile -Raw | ConvertFrom-Json).inventory_sha256 }
  $state = @{ inventory_sha256 = $hash; ts = (Get-Date).ToString("o") } | ConvertTo-Json
  Set-Content -Path $stateFile -Value $state -Encoding UTF8
  if ($prev -and $prev -eq $hash) {
    Write-Host "Convergence: inventory unchanged. Stopping." -ForegroundColor Green
    break
  }
}
