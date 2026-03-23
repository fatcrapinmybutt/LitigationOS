param(
  [Parameter(Mandatory=$true)] [string] $Repo,
  [Parameter(Mandatory=$true)] [string] $Corpus
)

Set-Location $Repo

# 1) Run MBP once
powershell -ExecutionPolicy Bypass -File tools\mbp_run.ps1 -Repo $Repo -Corpus $Corpus
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

# 2) Build prompt packet from newest run
$dest = python tools\prompt_packet_builder.py --repo $Repo
Write-Host "Prompt packet at: $dest"

# 3) Run Copilot CLI interactively using the PATCH prompt (safe mode; approvals required)
$cp = Get-Command "copilot" -ErrorAction SilentlyContinue
if ($null -eq $cp) {
  Write-Host "copilot CLI not found on PATH."
  exit 2
}

$prompt = Get-Content (Join-Path $dest "PROMPT_PATCH.md") -Raw
Write-Host "Starting Copilot CLI (interactive, approvals required)..."
# Start a session and feed prompt via -p if supported. If not, user can paste.
& copilot -p $prompt
if ($LASTEXITCODE -ne 0) {
  Write-Host "Copilot CLI returned non-zero exit code."
}

# 4) Rerun MBP to verify
powershell -ExecutionPolicy Bypass -File tools\mbp_run.ps1 -Repo $Repo -Corpus $Corpus
exit $LASTEXITCODE
