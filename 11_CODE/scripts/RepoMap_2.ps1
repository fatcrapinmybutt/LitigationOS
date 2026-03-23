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
    throw "Not inside a git repository. Run this from a repo root."
  }
  return $p
}

$root = RepoRoot
Set-Location $root

$docsDir = Join-Path $root "docs"
$mapPath = Join-Path $docsDir "REPO_MAP.md"
New-Item -ItemType Directory -Force -Path $docsDir | Out-Null

# Top-level directories (excluding .git)
$tops = Get-ChildItem -Directory -Force | Where-Object { $_.Name -ne ".git" } | Sort-Object Name

# Entry-point heuristics: common files
$entryCandidates = @(
  "README.md",
  "package.json",
  "pyproject.toml",
  "requirements.txt",
  "*.sln",
  "*.csproj",
  "tooling",
  "skills",
  "schemas",
  "apps",
  "engines",
  ".vscode"
)

$entries = @()
foreach ($pat in $entryCandidates) {
  $found = Get-ChildItem -Path $root -Recurse -Force -ErrorAction SilentlyContinue -Filter $pat | Select-Object -First 50
  foreach ($f in $found) {
    $entries += $f.FullName.Substring($root.Path.Length).TrimStart('\','/')
  }
}
$entries = $entries | Sort-Object -Unique

# Build a concise map (no guessing commands)
$md = @()
$md += "# Repo Map — LitigationOS"
$md += ""
$md += "Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
$md += ""
$md += "## Top-level structure"
$md += ""
$md += "| Directory | Notes |"
$md += "|---|---|"
foreach ($d in $tops) {
  $md += "| `$($d.Name)/` | |"
}
$md += ""
$md += "## Likely entrypoints & key files (discovered)"
$md += ""
foreach ($e in $entries) {
  $md += "- `$e`"
}
$md += ""
$md += "## Next: fill in meaning (agent workflow)"
$md += ""
$md += "1) Open each discovered file above and extract actual build/test/run commands (do not guess)."
$md += "2) Add a component table: name, path, purpose, inputs, outputs."
$md += "3) Keep this file updated whenever components change."
$md += ""

$md -join "`n" | Set-Content -Path $mapPath -Encoding UTF8
Write-Output "Wrote $mapPath"
