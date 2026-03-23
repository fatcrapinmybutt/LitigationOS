param(
  [string]$OfflineDir = "03_SEEDS/sample_offline",
  [string]$OutDir = "05_OUTPUTS"
)
$ErrorActionPreference = "Stop"
python 04_CODE/scao_autopilot_cli.py --mode OFFLINE --offline-dir $OfflineDir --outdir $OutDir
