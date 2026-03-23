param(
  [Parameter(Mandatory=$true)] [string] $Repo,
  [Parameter(Mandatory=$true)] [string] $Corpus
)

Set-Location $Repo

# Standard run uses kernel v4+ CLI; policy file expected in kernel/policy
$contract = Join-Path $Repo "kernel\contract\OutputContract_v1.yaml"
$policy   = Join-Path $Repo "kernel\policy\mbp_pass_gates_v2.yaml"

Write-Host "Running MBP governor..."
python -m kernel.mbp.cli --root $Corpus --out (Join-Path $Repo "out") --contract $contract --policy $policy --transparency-log (Join-Path $Repo "out\transparency_log.jsonl")
exit $LASTEXITCODE
