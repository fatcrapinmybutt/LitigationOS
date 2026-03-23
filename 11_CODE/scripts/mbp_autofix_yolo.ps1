param(
  [Parameter(Mandatory=$true)] [string] $Repo,
  [Parameter(Mandatory=$true)] [string] $Corpus,
  [int] $MaxContinues = 10,
  [switch] $AllowAllPaths,
  [switch] $AllowAllUrls
)

Set-Location $Repo

powershell -ExecutionPolicy Bypass -File tools\mbp_run.ps1 -Repo $Repo -Corpus $Corpus
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$dest = python tools\prompt_packet_builder.py --repo $Repo
Write-Host "Prompt packet at: $dest"

$cp = Get-Command "copilot" -ErrorAction SilentlyContinue
if ($null -eq $cp) {
  Write-Host "copilot CLI not found on PATH."
  exit 2
}

$prompt = Get-Content (Join-Path $dest "PROMPT_PATCH.md") -Raw

# Build flags according to Copilot CLI docs (autopilot + yolo + max continues; optional allow flags)
$flags = @("--autopilot","--yolo","--max-autopilot-continues",$MaxContinues,"-p",$prompt)
if ($AllowAllPaths) { $flags = @("--allow-all-paths") + $flags }
if ($AllowAllUrls)  { $flags = @("--allow-all-urls") + $flags }

Write-Host "Starting Copilot CLI (YOLO autopilot)..."
& copilot @flags
if ($LASTEXITCODE -ne 0) {
  Write-Host "Copilot CLI returned non-zero exit code."
}

powershell -ExecutionPolicy Bypass -File tools\mbp_run.ps1 -Repo $Repo -Corpus $Corpus
exit $LASTEXITCODE
