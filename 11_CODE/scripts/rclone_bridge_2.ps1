Param(
  [Parameter(Mandatory=$true)][string]$Root,
  [Parameter(Mandatory=$false)][string]$Mode = "doctor",
  [Parameter(Mandatory=$false)][string]$RemotePath = "",
  [Parameter(Mandatory=$false)][string]$MountPoint = "",
  [Parameter(Mandatory=$false)][switch]$Recursive,
  [Parameter(Mandatory=$false)][switch]$DryRun,
  [Parameter(Mandatory=$false)][string]$RcloneExe = ""
)

function Fail($msg){ Write-Host "FAIL: $msg" -ForegroundColor Red; exit 2 }

$rootPath = (Resolve-Path $Root).Path
if((Split-Path $rootPath -Leaf) -ne "LITIGATIONOS__MASTERv1.0"){ Fail "Root must be LITIGATIONOS__MASTERv1.0" }
if($rootPath.Length -ge 2 -and $rootPath.Substring(1,1) -eq ":" -and $rootPath.Substring(0,1).ToUpper() -eq "C"){ Fail "Root on C: is excluded by policy" }

$policyPath = Join-Path $rootPath "CONFIG\network_policy.json"
if(!(Test-Path $policyPath)){ Fail "Missing $policyPath" }
$policy = Get-Content $policyPath -Raw | ConvertFrom-Json
$killFlag = Join-Path $rootPath "CONFIG\network_off.flag"
if($policy.killSwitch.enabled -and (Test-Path $killFlag)){ Fail "Network kill-switch is active" }

function PolicyAllowsRclone(){
  if(-not $policy.OnlineUpdateMode){ return $false }
  foreach($e in $policy.allowlist){
    if($e.type -eq "tool" -and $e.id -eq "rclone" -and $e.enabled){ return $true }
  }
  return $false
}

function FindRclone(){
  if($RcloneExe -ne ""){
    if(Test-Path $RcloneExe){ return (Resolve-Path $RcloneExe).Path }
    Fail "--RcloneExe not found: $RcloneExe"
  }
  $cand = @(
    (Join-Path $rootPath "APP\Tools\RcloneBridge\bin\rclone.exe"),
    (Join-Path $rootPath "APP\Tools\RcloneBridge\bin\rclone" )
  )
  foreach($c in $cand){ if(Test-Path $c){ return (Resolve-Path $c).Path } }
  $p = (Get-Command rclone -ErrorAction SilentlyContinue)
  if($p){ return $p.Source }
  Fail "rclone not found. Install rclone or place rclone.exe in APP\Tools\RcloneBridge\bin\"
}

$cfgPath = Join-Path $rootPath "CONFIG\rclone_bridge.json"
if(!(Test-Path $cfgPath)){ Fail "Missing $cfgPath" }
$cfg = Get-Content $cfgPath -Raw | ConvertFrom-Json
$remoteName = $cfg.remote.name
if([string]::IsNullOrWhiteSpace($remoteName)){
  $remoteName = Read-Host "Enter rclone remote name (e.g., gdrive, drive, ESD-USB)"
  if([string]::IsNullOrWhiteSpace($remoteName)){ Fail "Remote name required" }
  $cfg.remote.name = $remoteName
  $cfg | ConvertTo-Json -Depth 8 | Set-Content $cfgPath -Encoding UTF8
}

$rclone = FindRclone

if($Mode -eq "doctor"){
  Write-Host "OK"; Write-Host "root=$rootPath"; Write-Host "rclone=$rclone"; Write-Host "remote=$remoteName";
  $allow = PolicyAllowsRclone
  if($allow){ Write-Host "policy=ALLOW" } else { Write-Host "policy=DENY (enable OnlineUpdateMode + allowlist rclone)" }
  exit 0
}

if(-not (PolicyAllowsRclone)){
  Fail "rclone blocked by policy. Edit CONFIG\network_policy.json: OnlineUpdateMode=true and allowlist{id:rclone}.enabled=true"
}

$ts = (Get-Date).ToUniversalTime().ToString("yyyyMMdd_HHmmss")
$runDir = Join-Path $rootPath ("RUNS\RUN_{0}_RCLONE" -f $ts)
$logDir = Join-Path $runDir "LOGS"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$outLog = Join-Path $logDir "rclone_stdout.log"

function Exec($args){
  $cmdLine = "$rclone $args"
  Add-Content -Path $outLog -Value ("[{0}] EXEC {1}" -f (Get-Date).ToUniversalTime().ToString("s"), $cmdLine)
  & $rclone @args 2>&1 | Tee-Object -FilePath $outLog -Append | Out-Host
  return $LASTEXITCODE
}

if($Mode -eq "lsjson"){
  $src = "$remoteName:`/$RemotePath".TrimEnd("/")
  $args = @("lsjson", $src)
  if($Recursive){ $args += "--recursive" }
  $args += "--files-only"
  $rc = Exec($args)
  if($rc -ne 0){ Fail "rclone lsjson failed rc=$rc (see $outLog)" }
  exit 0
}

if($Mode -eq "sync"){
  $src = "$remoteName:`/$RemotePath".TrimEnd("/")
  $dst = Join-Path $rootPath ("DATA\INBOX\gdrive_mirror\{0}" -f $remoteName)
  New-Item -ItemType Directory -Force -Path $dst | Out-Null
  $args = @("sync", $src, $dst, "--create-empty-src-dirs", "--progress")
  if($DryRun){ $args += "--dry-run" }
  $rc = Exec($args)
  if($rc -ne 0){ Fail "rclone sync failed rc=$rc (see $outLog)" }
  exit 0
}

if($Mode -eq "mount"){
  if([string]::IsNullOrWhiteSpace($MountPoint)){ Fail "MountPoint required for mount mode" }
  if(!(Test-Path $MountPoint)){ Fail "MountPoint does not exist. Create it first." }
  $src = "$remoteName:`/$RemotePath".TrimEnd("/")
  $args = @("mount", $src, $MountPoint, "--vfs-cache-mode", "writes")
  $rc = Exec($args)
  exit $rc
}

Fail "Unknown Mode: $Mode"
