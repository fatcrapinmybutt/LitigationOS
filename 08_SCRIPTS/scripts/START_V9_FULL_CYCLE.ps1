param(
  [string]$Config = ".\CONFIG\litigationos_mi_appellate_docforge_v9_accel.jsonc"
)
$ErrorActionPreference = "Stop"
python .\RUNTIME\mi_appellate_docforge_v9_orchestrator.py --config $Config full-cycle --purpose timeline --query "order hearing filed served custody parenting ppo contempt"
