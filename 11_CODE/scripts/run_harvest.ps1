param(
  [string]$OutDir = "$env:USERPROFILE\Downloads\LitigationOS_OUT",
  [string[]]$Roots = @("C:\Users\$env:USERNAME\Downloads")
)
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$root = Resolve-Path (Join-Path $here "..") | Select-Object -ExpandProperty Path
Set-Location $root
python tools\litigationosctl.py harvest --roots $Roots --out-dir $OutDir --unzip --bin-probe --carve-embedded --fastsig --page-pinpoints --authority-triples --audit-signals --exact-dup --near-dup --lsh-threshold 0.85 --materialize-dupes copy
Write-Host "Done. Output: $OutDir"
