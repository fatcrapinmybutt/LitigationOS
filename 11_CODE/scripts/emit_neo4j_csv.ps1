param(
  [string]$OutDir = "out/neo4j_export",
  [string]$COE = "out/COE.csv",
  [string]$ASL = "out/ASL.csv",
  [string]$NSC = "out/NSC_timeline.csv",
  [string]$FCC = "out/FCC_flags.json",
  [string]$VM  = "out/VM.json",
  [string]$REB = "out/REBUTTAL_PACK.csv"
)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

python tools/neo4j/litigos_to_neo4j.py emit-csv `
  --out_dir $OutDir --coe $COE --asl $ASL --nsc $NSC --fcc $FCC --vm $VM --rebuttal $REB

Write-Host "Done. See docs/NEO4J_RUNBOOK.md"
