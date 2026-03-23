param(
  [Parameter(Mandatory=$true)] [string] $Repo,
  [Parameter(Mandatory=$true)] [string] $Corpus,
  [ValidateSet("safe","yolo")] [string] $Mode = "safe",
  [int] $MaxContinues = 10,
  [switch] $AllowAllPaths,
  [switch] $AllowAllUrls
)

Set-Location $Repo

$contract = Join-Path $Repo "kernel\contract\OutputContract_v1.yaml"
$policy   = Join-Path $Repo "kernel\policy\mbp_pass_gates_v3.yaml"
$outdir   = Join-Path $Repo "out"

Write-Host "1) Running MBP (emit prompt packet on FAILSOFT)..."
python -m kernel.mbp.cli --root $Corpus --out $outdir --contract $contract --policy $policy --emit-prompt-packet
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$runs = Get-ChildItem $outdir -Directory | Sort-Object LastWriteTime -Descending
if ($runs.Count -eq 0) { Write-Host "No runs in out/"; exit 2 }
$run = $runs[0].FullName
$val = Join-Path $run "artifacts\ValidationReport.json"
$json = Get-Content $val -Raw | ConvertFrom-Json

if ($json.pack_readiness -eq "ANALYSIS_READY") {
  Write-Host "PASS: analysis-ready."
  exit 0
}

$pp = Join-Path $run "copilot_prompt_packet\PROMPT_PATCH.md"
if (-not (Test-Path $pp)) { Write-Host "Missing prompt packet."; exit 2 }

Write-Host "2) FAILSOFT → invoking Copilot CLI..."
$flags = @("--repo",$Repo,"--prompt-file",$pp)
if ($Mode -eq "yolo") {
  $flags += @("--mode","yolo","--max-continues",$MaxContinues)
  if ($AllowAllPaths) { $flags += "--allow-all-paths" }
  if ($AllowAllUrls)  { $flags += "--allow-all-urls" }
} else {
  $flags += @("--mode","safe")
}

python tools\run_copilot_driver.py @flags
Write-Host "Copilot driver exit:" $LASTEXITCODE

Write-Host "3) Rerunning MBP..."
python -m kernel.mbp.cli --root $Corpus --out $outdir --contract $contract --policy $policy --emit-prompt-packet
exit $LASTEXITCODE
