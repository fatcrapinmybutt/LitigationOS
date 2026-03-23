# install_bin_fix_watcher_windows.ps1 (v32)
# Creates a Scheduled Task that runs bin_fix_watcher.py at logon to auto-rename misnamed downloads.
# Requires: Python in PATH.
# Safe: does not elevate; installs to CurrentUser scope.

param(
  [string]$WatchDir = "$env:USERPROFILE\Downloads",
  [int]$Interval = 3,
  [switch]$Verify
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $root
$script = Join-Path $projectRoot "tools\bin_fix_watcher.py"

if (!(Test-Path $script)) { throw "Missing $script" }

$taskName = "LitigationOS_BinFixWatcher"
$python = "python"

$verifyFlag = ""
if ($Verify) { $verifyFlag = "--verify" }

$action = New-ScheduledTaskAction -Execute $python -Argument "`"$script`" --dir `"$WatchDir`" --interval $Interval $verifyFlag"
$trigger = New-ScheduledTaskTrigger -AtLogOn
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel LeastPrivilege
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

try {
  Unregister-ScheduledTask -TaskName $taskName -Confirm:$false | Out-Null
} catch {}

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings | Out-Null
Write-Host "OK installed scheduled task: $taskName watching $WatchDir"
