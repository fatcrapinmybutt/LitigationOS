param(
  [string]$OutDir = "05_OUTPUTS"
)
$ErrorActionPreference = "Stop"
python 04_CODE/scao_autopilot_cli.py --mode FULL --outdir $OutDir
