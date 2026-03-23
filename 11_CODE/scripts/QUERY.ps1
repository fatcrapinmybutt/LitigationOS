param(
  [string]$RunDir = "",
  [string]$Query = ""
)
$ErrorActionPreference="Stop"
$root = Resolve-Path (Join-Path $PSScriptRoot "..")
if (!$RunDir) {
  $out = Join-Path $root ".out"
  $latest = Get-ChildItem $out -Directory | Sort-Object LastWriteTime -Descending | Select-Object -First 1
  if (!$latest) { throw "No runs found in $out" }
  $RunDir = $latest.FullName
}
if (!$Query) { throw "Provide -Query '...'" }

$venv = Join-Path $root ".venv"
. (Join-Path $venv "Scripts\Activate.ps1")

python -m litos_harvest.query --run-dir "$RunDir" --query "$Query"
