\
#requires -Version 7.0
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function RepoRoot {
  $p = Resolve-Path .
  while ($p -and -not (Test-Path (Join-Path $p ".git"))) {
    $parent = Split-Path $p -Parent
    if ($parent -eq $p) { break }
    $p = $parent
  }
  if (-not (Test-Path (Join-Path $p ".git"))) {
    return (Resolve-Path .)
  }
  return $p
}

$root = RepoRoot
Set-Location $root

$docsDir = Join-Path $root "docs"
$mapPath = Join-Path $docsDir "REPO_MAP.md"
New-Item -ItemType Directory -Force -Path $docsDir | Out-Null

$tops = Get-ChildItem -Directory -Force | Where-Object { $_.Name -ne ".git" } | Sort-Object Name

$entryCandidates = @("README.md","package.json","pyproject.toml","requirements.txt","*.sln","*.csproj",".vscode/tasks.json","tooling","skills","schemas","apps","engines")
$entries = @()
foreach ($pat in $entryCandidates) {
  $found = Get-ChildItem -Path $root -Recurse -Force -ErrorAction SilentlyContinue -Filter $pat | Select-Object -First 200
  foreach ($f in $found) {
    $entries += $f.FullName.Substring($root.Path.Length).TrimStart('\','/')
  }
}
$entries = $entries | Sort-Object -Unique

$md = @()
$md += "# Repo Map"
$md += ""
$md += "Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
$md += ""
$md += "## Top-level structure"
$md += ""
$md += "| Directory | Notes |"
$md += "|---|---|"
foreach ($d in $tops) { $md += "| `$($d.Name)/` | |" }
$md += ""
$md += "## Discovered entrypoints & key files (no guessing)"
$md += ""
foreach ($e in $entries) { $md += "- `$e`" }
$md += ""
$md += "## Next steps"
$md += ""
$md += "1) Open each entrypoint above and extract actual run/build/test commands from file content."
$md += "2) Add a component table: name, path, purpose, inputs, outputs."
$md += "3) Keep this file updated when components change."
$md += ""

$md -join "`n" | Set-Content -Path $mapPath -Encoding UTF8
Write-Output "Wrote $mapPath"
