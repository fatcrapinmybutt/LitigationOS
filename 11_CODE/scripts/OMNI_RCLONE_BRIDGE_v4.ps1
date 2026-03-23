# OMNI_RCLONE_BRIDGE_v5.ps1
# =========================================================================================
# GOOGLE DRIVE ⇆ C:\Users\andre\Downloads ⇆ D:\ ⇆ E:\
# Fixes: PowerShell colon parsing, missing function order, low-space hard stop, task install.
# =========================================================================================

# ---------- SELF-ELEVATE (runs once) ----------
# Comment this block out if you always start PowerShell as Admin.
$IsAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()
).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $IsAdmin) {
  Write-Host "[OMNI] Elevating to Administrator..." -ForegroundColor Cyan
  $psi = New-Object System.Diagnostics.ProcessStartInfo "PowerShell";
  $psi.Arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`"";
  $psi.Verb = "runas";
  try { [Diagnostics.Process]::Start($psi) | Out-Null; exit } catch { Write-Warning "Elevation cancelled."; }
}

# ---------- SETTINGS ----------
$ErrorActionPreference = 'Stop'

# Remote (Google Drive by default)
$RemoteName        = 'omni'
$RemoteRoot        = 'omni-root'
$AssumeGoogleDrive = $true

# Scope (exactly per your requirements)
$PathC             = 'C:\Users\andre\Downloads'  # Only this path from C:
$PathD             = 'D:\'                        # Entire drive
$PathE             = 'E:\'                        # Entire drive

# Remote subfolders
$RemoteC           = 'mirrors/C-Downloads'
$RemoteD           = 'mirrors/D'
$RemoteE           = 'mirrors/E'

# Optional canonical registry file (copied if present)
$CanonicalRegistry = Join-Path $PathC 'OMNI_SYSTEM_REGISTRY_2025-10-05.json'

# Behavior / perf
$DoMountRemote     = $true
$MountLetter       = 'R:'
$ScheduleEveryMins = 15
$RcAddr            = '127.0.0.1:5572'
$RcUser            = 'omni'
$RcPass            = 'bridge'

$Transfers         = 8
$Checkers          = 10
$Retry             = 5
$LowLevelRetries   = 20
$ModifyWindow      = '3s'
$Bandwidth         = ''           # e.g. '10M'; '' = unlimited
$DriveStopOnULimit = $true
$DryRun            = $false
$ForceResync       = $false

# Safety
$MaxDeletePercent  = '50%'
$PauseFile         = Join-Path $PathC 'OMNI_BRIDGE_PAUSE'
$EnforceMinFree    = $false       # true = hard stop; false = warn
$MinFreeGB_C       = 2
$MinFreeGB_D       = 2
$MinFreeGB_E       = 2

# Excludes
$Excludes = @(
  '$RECYCLE.BIN/**', 'System Volume Information/**',
  'pagefile.sys', 'swapfile.sys', 'hiberfil.sys',
  'Thumbs.db', '*.tmp', '*/Temp/**', '*/~$*',
  '*.lnk', '*.crdownload', '*.partial', '*.lock'
)

# Work dirs
$WorkDir    = "$env:USERPROFILE\OMNI_RCLONE_BRIDGE"
$BinDir     = Join-Path $WorkDir 'bin'
$LogDir     = Join-Path $WorkDir 'logs'
$StateDir   = Join-Path $WorkDir 'state'
$ConfDir    = Join-Path $WorkDir '.rclone'
$ReportDir  = Join-Path $WorkDir 'reports'
$RcloneUrl  = 'https://downloads.rclone.org/rclone-current-windows-amd64.zip'
New-Item -ItemType Directory -Force -Path $WorkDir,$BinDir,$LogDir,$StateDir,$ConfDir,$ReportDir | Out-Null
$RcloneConf = Join-Path $ConfDir 'rclone.conf'
$env:RCLONE_CONFIG = $RcloneConf

# ---------- HELPERS ----------
function Note($m,$c='Gray'){ Write-Host $m -ForegroundColor $c }
function Die($m){ Write-Host "[FATAL] $m" -ForegroundColor Red; throw $m }
function Rotate-Logs($Prefix,$Keep=12){
  $files = Get-ChildItem -Path $LogDir -Filter "$Prefix*.log" -ErrorAction SilentlyContinue |
           Sort-Object LastWriteTime -Descending
  if ($files.Count -gt $Keep){ $files | Select-Object -Skip $Keep | % { Remove-Item $_.FullName -ErrorAction SilentlyContinue } }
}
function Drive-FreeGB($root){
  try{
    if (-not (Test-Path $root)) { return $null }
    $d = Get-PSDrive -Name ($root.Substring(0,1)) -ErrorAction SilentlyContinue
    if ($null -eq $d) { return $null }
    return [math]::Round($d.Free/1GB,2)
  }catch{ return $null }
}
function Ensure-Dir($p){ if (-not (Test-Path $p)) { New-Item -ItemType Directory -Force -Path $p | Out-Null } }

# Fix rclone download cases when EXE is in use
function Get-Rclone {
  $p = (Get-Command rclone.exe -ErrorAction SilentlyContinue).Path
  if ($p){ return $p }
  $local = Join-Path $BinDir 'rclone.exe'
  if (Test-Path $local){ return $local }
  Note "[OMNI] Downloading rclone…" 'Cyan'
  $zip = Join-Path $env:TEMP ('rclone-portable_' + [Guid]::NewGuid().ToString() + '.zip')
  Invoke-WebRequest -Uri $RcloneUrl -OutFile $zip
  $tmp = Join-Path $env:TEMP ('rclone-unzip_' + [Guid]::NewGuid().ToString())
  New-Item -ItemType Directory -Force -Path $tmp | Out-Null
  Expand-Archive -Path $zip -DestinationPath $tmp -Force
  Remove-Item $zip -Force
  $exe = Get-ChildItem $tmp -Recurse -Filter rclone.exe | Select-Object -First 1
  if (-not $exe){ Die "Could not find rclone.exe in the archive." }
  Copy-Item -Path $exe.FullName -Destination $local -Force
  Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
  return $local
}
$rclone = Get-Rclone

# Create baseline conf if missing
if (-not (Test-Path $RcloneConf)) {
  if ($env:RCLONE_CONFIG_BASE64) {
    [IO.File]::WriteAllBytes($RcloneConf, [Convert]::FromBase64String($env:RCLONE_CONFIG_BASE64))
    Note "[OMNI] rclone.conf written from RCLONE_CONFIG_BASE64." 'Cyan'
  } else {
@"
[$RemoteName]
type = $([string]::Copy($(if($AssumeGoogleDrive){"drive"}else{"drive"})))
scope = drive
# Finish OAuth once:
#   `"$rclone --config `"$RcloneConf`" config`"
"@ | Set-Content -Encoding UTF8 $RcloneConf
    Note "[OMNI] Stub rclone.conf created (Google Drive). Run: `"$rclone --config `"$RcloneConf`" config`"" 'Yellow'
  }
}

# MUST come before any call that uses them:
function RemotePath([string]$sub) { return "$($RemoteName):`"$RemoteRoot/$sub`"" }
function RemoteExists {
  $remotes = & $rclone --config $RcloneConf listremotes 2>$null
  return ($remotes -split "`r?`n") -contains "$($RemoteName):"
}
function RcCommonFlags(){
  $args = @('--config',$RcloneConf,'--retries',$Retry,'--low-level-retries',$LowLevelRetries,'--checkers',$Checkers,'--transfers',$Transfers,'--fast-list')
  if ($Bandwidth) { $args += @('--bwlimit',$Bandwidth) }
  if ($DriveStopOnULimit) { $args += @('--drive-stop-on-upload-limit') }
  if ($DryRun) { $args += @('--dry-run') }
  foreach($ex in $Excludes){ $args += @('--exclude',$ex) }
  return ,$args
}
function Invoke-Rclone([string[]]$Args,[string]$LogPrefix){
  $common = RcCommonFlags
  $ts = Get-Date -Format 'yyyyMMdd_HHmmss'
  $log = Join-Path $LogDir "$LogPrefix`_$ts.log"
  Rotate-Logs $LogPrefix
  & $rclone @common @Args --log-file=$log --log-level INFO
  return $log
}

# ---------- PRECHECKS ----------
# Pause gate
if (Test-Path $PauseFile) {
  Note "[OMNI] Pause file present at $PauseFile — skipping sync setup." 'Yellow'
  return
}

# Remote ready?
if (-not (RemoteExists)) {
  Note "[OMNI] Remote '$RemoteName' not found in $RcloneConf." 'Yellow'
  Note "       Finish OAuth: `"$rclone --config `"$RcloneConf`" config`"" 'Yellow'
  return
}

# Free space: warn or enforce
$freeC = Drive-FreeGB $PathC; $freeD = Drive-FreeGB $PathD; $freeE = Drive-FreeGB $PathE
function Check-Free($label,$free,$min){
  if ($null -eq $free) { Note "[$label] drive not found or offline — will skip this mirror." 'Yellow'; return $false }
  if ($free -lt $min) {
    $msg = "[$label] low free space: $free GB (< $min GB)"
    if ($EnforceMinFree) { Die $msg } else { Note $msg 'Yellow' }
  } else {
    Note "[$label] free space OK: $free GB" 'DarkGray'
  }
  return $true
}
$UseC = Check-Free 'C:' $freeC $MinFreeGB_C
$UseD = Check-Free 'D:' $freeD $MinFreeGB_D
$UseE = Check-Free 'E:' $freeE $MinFreeGB_E

# ---------- RC API ----------
try {
  Start-Process -WindowStyle Hidden -FilePath $rclone -ArgumentList @(
    '--config',$RcloneConf,'rcd',
    '--rc-addr',$RcAddr,'--rc-user',$RcUser,'--rc-pass',$RcPass,
    '--log-file',(Join-Path $LogDir 'rcd.log'),'--log-level','INFO'
  ) -ErrorAction SilentlyContinue | Out-Null
  Start-Sleep -Seconds 1
  Note "[OMNI] RC API: http://$RcAddr (user: $RcUser)" 'Cyan'
} catch {}

# ---------- Ensure remote folders ----------
Invoke-Rclone -Args @('mkdir',(RemotePath 'registry')) -LogPrefix 'mkdir_registry' | Out-Null
if ($UseC){ Invoke-Rclone -Args @('mkdir',(RemotePath $RemoteC)) -LogPrefix 'mkdir_C' | Out-Null }
if ($UseD){ Invoke-Rclone -Args @('mkdir',(RemotePath $RemoteD)) -LogPrefix 'mkdir_D' | Out-Null }
if ($UseE){ Invoke-Rclone -Args @('mkdir',(RemotePath $RemoteE)) -LogPrefix 'mkdir_E' | Out-Null }

# ---------- Push registry (optional) ----------
if (Test-Path $CanonicalRegistry) {
  Note "[OMNI] Uploading canonical registry..." 'Cyan'
  Invoke-Rclone -Args @('copyto',$CanonicalRegistry,(RemotePath 'registry/OMNI_SYSTEM_REGISTRY_2025-10-05.json'),'--checksum','--copy-links') -LogPrefix 'copy_registry' | Out-Null
}

# ---------- BISYNC SET ----------
$Pairs = @()
if ($UseC){ $Pairs += @{ Src=$PathC; Dst=(RemotePath $RemoteC); State=(Join-Path $StateDir 'C_downloads'); Name='C' } }
if ($UseD){ $Pairs += @{ Src=$PathD; Dst=(RemotePath $RemoteD); State=(Join-Path $StateDir 'D_drive');     Name='D' } }
if ($UseE){ $Pairs += @{ Src=$PathE; Dst=(RemotePath $RemoteE); State=(Join-Path $StateDir 'E_drive');     Name='E' } }
$Pairs | % { Ensure-Dir $_.State }

function Run-Bisync($p,[bool]$Resync){
  $args = @(
    'bisync', $p.Src, $p.Dst,
    '--create-empty-src-dirs','--check-access',
    '--workdir', $p.State,
    '--track-renames','--track-renames-strategy','modtime',
    '--modify-window', $ModifyWindow,
    '--max-delete', $MaxDeletePercent
  )
  if ($Resync -or $ForceResync){ $args += '--resync' }
  Note ("[OMNI] Bisync{2}: {0} <-> {1}" -f $p.Src,$p.Dst,($(if($Resync -or $ForceResync){" (RESYNC)"}else{" (steady)"}))) 'Cyan'
  Invoke-Rclone -Args $args -LogPrefix ("bisync_{0}" -f $p.Name) | Out-Null
}

# Bootstrap pass, then steady pass
$Pairs | % { Run-Bisync $_ $true }
$Pairs | % { Run-Bisync $_ $false }

# ---------- MOUNT (optional) ----------
if ($DoMountRemote) {
  try { & $rclone cmount stop $MountLetter 2>$null | Out-Null } catch {}
  Note "[OMNI] Mounting $($RemoteName):`"$RemoteRoot`" as $MountLetter ..." 'Cyan'
  Start-Process -WindowStyle Hidden -FilePath $rclone -ArgumentList @(
    '--config',$RcloneConf,'mount',"$($RemoteName):`"$RemoteRoot`"",$MountLetter,
    '--vfs-cache-mode','full','--vfs-cache-max-size','2G',
    '--dir-cache-time','30s','--poll-interval','15s',
    '--rc','--rc-addr',$RcAddr,
    '--log-file',(Join-Path $LogDir 'mount.log'),'--log-level','INFO'
  ) | Out-Null
}

# ---------- SCHEDULE ----------
$TaskName  = 'OMNI-Rclone-Bridge'
$TaskBatch = Join-Path $WorkDir 'run_bridge_cycle.bat'

# Put a private rclone next to the BAT so scheduler context is consistent
$RclonePortable = Join-Path $BinDir 'rclone.exe'
if (-not (Test-Path $RclonePortable)) { Copy-Item -Path $rclone -Destination $RclonePortable -Force }

# Common flags for BAT
$common = @("--retries $Retry --low-level-retries $LowLevelRetries --checkers $Checkers --transfers $Transfers --fast-list --modify-window $ModifyWindow --max-delete $MaxDeletePercent")
if ($Bandwidth){ $common += " --bwlimit $Bandwidth" }
if ($DriveStopOnULimit){ $common += " --drive-stop-on-upload-limit" }
foreach($ex in $Excludes){ $common += " --exclude `"$ex`"" }
if ($DryRun){ $common += " --dry-run" }
$CommonFlags = $common -join ''

# BAT body
$bat = @()
$bat += '@echo off'
$bat += 'setlocal ENABLEDELAYEDEXPANSION'
$bat += "set RCLONE=""%~dp0bin\rclone.exe"""
$bat += "IF EXIST ""$PauseFile"" ( echo Bridge paused via $PauseFile & exit /b 0 )"
if (Test-Path $CanonicalRegistry) {
  $bat += "`"%~dp0bin\rclone.exe`" --config `"$RcloneConf`" copyto `"$CanonicalRegistry`" `"{0}`" --checksum --copy-links $CommonFlags --log-file `"{1}`" --log-level INFO" -f (RemotePath 'registry/OMNI_SYSTEM_REGISTRY_2025-10-05.json'), (Join-Path $LogDir 'sched_copy_registry.log')
}
if ($UseC){ $bat += "`"%~dp0bin\rclone.exe`" --config `"$RcloneConf`" bisync `"$PathC`" `"{0}`" --create-empty-src-dirs --check-access --workdir `"{1}`" --track-renames --track-renames-strategy modtime $CommonFlags --log-file `"{2}`" --log-level INFO" -f (RemotePath $RemoteC), (Join-Path $StateDir 'C_downloads'), (Join-Path $LogDir 'sched_bisync_C.log') }
if ($UseD){ $bat += "`"%~dp0bin\rclone.exe`" --config `"$RcloneConf`" bisync `"$PathD`" `"{0}`" --create-empty-src-dirs --check-access --workdir `"{1}`" --track-renames --track-renames-strategy modtime $CommonFlags --log-file `"{2}`" --log-level INFO" -f (RemotePath $RemoteD), (Join-Path $StateDir 'D_drive'), (Join-Path $LogDir 'sched_bisync_D.log') }
if ($UseE){ $bat += "`"%~dp0bin\rclone.exe`" --config `"$RcloneConf`" bisync `"$PathE`" `"{0}`" --create-empty-src-dirs --check-access --workdir `"{1}`" --track-renames --track-renames-strategy modtime $CommonFlags --log-file `"{2}`" --log-level INFO" -f (RemotePath $RemoteE), (Join-Path $StateDir 'E_drive'), (Join-Path $LogDir 'sched_bisync_E.log') }
$bat += 'endlocal'
Set-Content -Encoding ASCII -Path $TaskBatch -Value ($bat -join "`r`n")

# Try Scheduled Task; if it fails, install Startup shortcut instead
$ScheduledOK = $false
try {
  $A = New-ScheduledTaskAction -Execute $TaskBatch
  $T = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes $ScheduleEveryMins) -RepetitionDuration ([TimeSpan]::MaxValue)
  $S = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -StartWhenAvailable
  if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
  }
  Register-ScheduledTask -Action $A -Trigger $T -Settings $S -TaskName $TaskName -Description "OMNI rclone bridge (Downloads + D: + E: ⇆ Google Drive)" | Out-Null
  $ScheduledOK = $true
  Note "[OMNI] Scheduled Task '$TaskName' registered (every $ScheduleEveryMins min)." 'Green'
} catch {
  Note "[OMNI] Scheduled Task registration failed; falling back to Startup shortcut." 'Yellow'
}

if (-not $ScheduledOK) {
  $Startup = [Environment]::GetFolderPath('Startup')
  $lnk = Join-Path $Startup 'OMNI_Rclone_Bridge.lnk'
  $ws = New-Object -ComObject WScript.Shell
  $s  = $ws.CreateShortcut($lnk)
  $s.TargetPath = $TaskBatch
  $s.WorkingDirectory = $WorkDir
  $s.WindowStyle = 7
  $s.Save()
  Note "[OMNI] Startup shortcut installed: $lnk" 'Green'
}

# ---------- FINAL ----------
Write-Host ""
Write-Host "OMNI rclone bridge — READY" -ForegroundColor Green
Write-Host ("Remote:         {0}  (root: {1})" -f $RemoteName,$RemoteRoot)
Write-Host ("RC API:         http://{0}  (user: {1})" -f $RcAddr,$RcUser)
Write-Host ("Logs:           {0}" -f $LogDir)
Write-Host ("State:          {0}" -f $StateDir)
if ($DoMountRemote){ Write-Host ("Mounted:        {0}" -f $MountLetter) }
if ($ScheduledOK){ Write-Host ("Scheduled Task: {0}  (every {1} min)" -f $TaskName,$ScheduleEveryMins) }
Write-Host ""
Write-Host "Mirrors:" -ForegroundColor Cyan
if ($UseC){ Write-Host ("  {0}  ⇆  {1}" -f $PathC, (RemotePath $RemoteC)) }
if ($UseD){ Write-Host ("  {0}  ⇆  {1}" -f $PathD, (RemotePath $RemoteD)) }
if ($UseE){ Write-Host ("  {0}  ⇆  {1}" -f $PathE, (RemotePath $RemoteE)) }
Write-Host ""
Write-Host "Controls:" -ForegroundColor Yellow
Write-Host ("  • Pause:  create file  {0}" -f $PauseFile)
Write-Host ("  • Resume: delete the file above")
Write-Host ("  • Force a cycle now:  & `"{0}`"" -f $TaskBatch)
Write-Host ("  • Finish OAuth (once):  `"{0}`" --config `"{1}`" config" -f $rclone,$RcloneConf)
