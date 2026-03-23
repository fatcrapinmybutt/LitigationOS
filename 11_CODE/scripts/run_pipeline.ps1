param(
  [string]$ConfigPath = "$(Split-Path -Parent $MyInvocation.MyCommand.Path)\..\pipeline_config.json"
)
$ErrorActionPreference="Stop"
function Expand-EnvVars([string]$s){ return [Environment]::ExpandEnvironmentVariables($s) }

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path (Join-Path $Root "..")
$Cfg = Get-Content $ConfigPath -Raw | ConvertFrom-Json

$CanonicalLocal = Expand-EnvVars $Cfg.canonical_local_root
$RunsDst = Join-Path $CanonicalLocal $Cfg.canonical_subdir_runs
$GraphDst = Join-Path $CanonicalLocal $Cfg.canonical_subdir_graphrag
$NeoDst  = Join-Path $CanonicalLocal $Cfg.canonical_subdir_neo4j

New-Item -ItemType Directory -Force -Path $CanonicalLocal,$RunsDst,$GraphDst,$NeoDst | Out-Null

$Venv = Join-Path $ProjectRoot ".venv"
$Python = Join-Path $Venv "Scripts\python.exe"
$Pip = Join-Path $Venv "Scripts\pip.exe"
if (!(Test-Path $Python)) {
  python -m venv $Venv
  & $Pip install -r (Join-Path $ProjectRoot "requirements.txt")
}

$Args=@("gdrive_organizer.py","--root-id",$Cfg.root_id,"--max-iters","$($Cfg.max_iters)")
if ($Cfg.apply -eq $true){ $Args+="--apply" }
if ($Cfg.emit_inventory -eq $true){ $Args+="--emit-inventory" }
if ($Cfg.emit_dupes -eq $true){ $Args+="--emit-dupes" }
if ($Cfg.purge_empty_folders -eq $true){ $Args+="--purge-empty-folders" }
if ($Cfg.export_google_native -eq $true){
  $Args+="--export-google-native"; $Args+="--export-target"; $Args+="$($Cfg.export_target)"
}

Push-Location $ProjectRoot
& $Python @Args
Pop-Location

$RunsSrc = Join-Path $ProjectRoot "runs"
if (Test-Path $RunsSrc){ robocopy $RunsSrc $RunsDst /MIR /R:2 /W:2 /NFL /NDL /NP | Out-Null }

$LatestRunFile = Join-Path $RunsSrc "latest_run.txt"
$Latest = (Test-Path $LatestRunFile) ? (Get-Content $LatestRunFile -Raw).Trim() : ""
$Inv = ""
if ($Latest -ne ""){
  $InvCandidate = Join-Path (Join-Path $RunsSrc $Latest) "inventory.jsonl"
  if (Test-Path $InvCandidate){ $Inv = $InvCandidate }
}

if ($Cfg.graphrag_enabled -eq $true -and $Inv -ne ""){
  $Out = Join-Path $GraphDst $Latest
  New-Item -ItemType Directory -Force -Path $Out | Out-Null
  Push-Location $ProjectRoot
  & $Python "graphrag_export.py" "--inventory" $Inv "--out" $Out "--root-id" $Cfg.root_id
  Pop-Location
}

if ($Cfg.neo4j_enabled -eq $true -and $Inv -ne ""){
  $Out = Join-Path $NeoDst $Latest
  New-Item -ItemType Directory -Force -Path $Out | Out-Null
  Copy-Item $Inv (Join-Path $Out "inventory.jsonl") -Force
  Push-Location $ProjectRoot
  & $Python "neo4j_importer.py" "--inventory" $Inv "--config" $ConfigPath "--root-id" $Cfg.root_id
  Pop-Location
}

if ($Cfg.rclone_enabled -eq $true -and $Cfg.rclone_remote_dst -ne ""){
  $Rclone = $Cfg.rclone_exe
  $Flags=@(); foreach($x in $Cfg.rclone_flags){ $Flags += "$x" }
  $LogDir = Join-Path $CanonicalLocal "rclone_logs"
  New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
  $LogFile = Join-Path $LogDir ("rclone_" + (Get-Date -Format "yyyyMMdd_HHmmss") + ".log")
  & $Rclone sync $CanonicalLocal $Cfg.rclone_remote_dst @Flags --log-file $LogFile
}
