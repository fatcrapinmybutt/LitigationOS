#requires -Version 5.1
param(
  [Parameter(Position=0)][ValidateSet('doctor','enable','disable','lsjson','sync','mount')][string]$Command = 'doctor',
  [string]$Root = '',
  [string]$Mountpoint = '',
  [switch]$ForceOffline
)

function Resolve-Root {
  param([string]$r)
  if ($r -and (Test-Path $r)) { return (Resolve-Path $r).Path }
  $here = Split-Path -Parent $MyInvocation.MyCommand.Path
  $guess = Resolve-Path (Join-Path $here '..\..\..')
  return $guess.Path
}

function Read-Json($path) {
  if (!(Test-Path $path)) { return $null }
  try { return (Get-Content $path -Raw | ConvertFrom-Json) } catch { return $null }
}

function Write-Json($path,$obj) {
  $dir = Split-Path -Parent $path
  if (!(Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
  ($obj | ConvertTo-Json -Depth 8) | Set-Content -Encoding UTF8 -Path $path
}

function Find-Rclone($root) {
  $bin1 = Join-Path $root 'APP\Tools\RcloneBridge\bin\rclone.exe'
  if (Test-Path $bin1) { return $bin1 }
  $hit = (Get-Command rclone -ErrorAction SilentlyContinue)
  if ($hit) { return $hit.Source }
  return $null
}

function Ensure-RunDir($root) {
  $stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMdd_HHmmss')
  $run = Join-Path $root ("RUNS\RUN_${stamp}_RCLONE")
  New-Item -ItemType Directory -Force -Path (Join-Path $run 'LOGS') | Out-Null
  New-Item -ItemType Directory -Force -Path (Join-Path $run 'REPORTS') | Out-Null
  return $run
}

$Root = Resolve-Root $Root
$runDir = Ensure-RunDir $Root
$polPath = Join-Path $Root 'CONFIG\network_policy.json'
$pol = Read-Json $polPath
if ($null -eq $pol) {
  $pol = [pscustomobject]@{ OnlineUpdateMode = $false; default = 'deny'; requireNetworkBroker = $true; allowlist = @(); killSwitch = [pscustomobject]@{enabled=$true; flagFile='CONFIG/network_off.flag'} }
}

function Allowlist-SetTool($pol,[string]$id,[bool]$enabled) {
  $found = $false
  foreach ($e in $pol.allowlist) {
    if ($e.type -eq 'tool' -and $e.id -eq $id) { $e.enabled = $enabled; $found = $true }
  }
  if (-not $found) {
    $pol.allowlist += [pscustomobject]@{ id=$id; enabled=$enabled; type='tool'; target='rclone'; ports=@(); purpose='Operator-controlled rclone operations'; module='storage.rclone' }
  }
}

function Allowlist-ToolEnabled($pol,[string]$id) {
  foreach ($e in $pol.allowlist) { if ($e.type -eq 'tool' -and $e.id -eq $id) { return [bool]$e.enabled } }
  return $false
}

$killFlag = Join-Path $Root ($pol.killSwitch.flagFile)

if ($Command -eq 'enable') {
  $pol.OnlineUpdateMode = $true
  Allowlist-SetTool $pol 'rclone' $true
  if (Test-Path $killFlag) { Remove-Item -Force $killFlag -ErrorAction SilentlyContinue }
  Write-Json $polPath $pol
  "Enabled: OnlineUpdateMode=true; allowlist tool rclone=true" | Tee-Object -FilePath (Join-Path $runDir 'REPORTS\enable.txt')
  exit 0
}

if ($Command -eq 'disable') {
  Allowlist-SetTool $pol 'rclone' $false
  if ($ForceOffline) { $pol.OnlineUpdateMode = $false }
  Write-Json $polPath $pol
  "Disabled: allowlist tool rclone=false" | Tee-Object -FilePath (Join-Path $runDir 'REPORTS\disable.txt')
  exit 0
}

$rclone = Find-Rclone $Root

"LitigationOS root: $Root" | Tee-Object -FilePath (Join-Path $runDir 'REPORTS\doctor.txt')
"rclone: $rclone" | Tee-Object -Append -FilePath (Join-Path $runDir 'REPORTS\doctor.txt')
"OnlineUpdateMode: $($pol.OnlineUpdateMode); allowlist rclone: $(Allowlist-ToolEnabled $pol 'rclone'); kill_switch: $(Test-Path $killFlag)" | Tee-Object -Append -FilePath (Join-Path $runDir 'REPORTS\doctor.txt')

if ($Command -eq 'doctor') { exit 0 }

if (Test-Path $killFlag) { "BLOCKED: kill switch active (CONFIG/network_off.flag)"; exit 2 }
if (-not $pol.OnlineUpdateMode) { "BLOCKED: OnlineUpdateMode=false (run enable)"; exit 2 }
if (-not (Allowlist-ToolEnabled $pol 'rclone')) { "BLOCKED: allowlist tool 'rclone' disabled (run enable)"; exit 2 }
if (-not $rclone) { "ERROR: rclone not found (PATH or APP\\Tools\\RcloneBridge\\bin\\rclone.exe)"; exit 3 }

$rcConf = Join-Path $Root 'CONFIG\rclone.conf'
if (-not (Test-Path $rcConf)) { "NOTE: missing CONFIG\\rclone.conf (create via 'rclone config')" }

# Minimal ops: pass through to rclone with config and logging.
$logFile = Join-Path $runDir 'LOGS\rclone_stdout.log'

switch ($Command) {
  'lsjson' {
    & $rclone --config $rcConf lsjson --recursive | Out-File -Encoding UTF8 (Join-Path $runDir 'REPORTS\lsjson.json')
    exit $LASTEXITCODE
  }
  'sync' {
    $mirrorBase = Join-Path $Root 'DATA\INBOX\gdrive_mirror\MyDrive'
    New-Item -ItemType Directory -Force -Path $mirrorBase | Out-Null
    & $rclone --config $rcConf sync --dry-run | Out-File -Encoding UTF8 $logFile
    exit $LASTEXITCODE
  }
  'mount' {
    if (-not $Mountpoint) { "mount requires -Mountpoint"; exit 2 }
    & $rclone --config $rcConf mount $Mountpoint | Out-File -Encoding UTF8 $logFile
    exit $LASTEXITCODE
  }
  default { "Unknown command"; exit 2 }
}
