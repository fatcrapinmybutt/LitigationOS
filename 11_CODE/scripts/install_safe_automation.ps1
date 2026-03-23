<# 
Installs a scheduled task that runs Drive Integrity Toolkit SAFE MODE 4x/day.
Task name: DriveIntegrityToolkit-SafeScan

Usage:
  powershell -ExecutionPolicy Bypass -File .\install_safe_automation.ps1 -Drives F,H,I,J
#>

[CmdletBinding()]
param(
  [Parameter(Mandatory=$false)]
  [string[]]$Drives = @('F','H','I','J')
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Test-IsAdmin {
  $id = [Security.Principal.WindowsIdentity]::GetCurrent()
  $p = New-Object Security.Principal.WindowsPrincipal($id)
  return $p.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

if (-not (Test-IsAdmin)) { throw "Run as Administrator." }

$taskName = "DriveIntegrityToolkit-SafeScan"
$scriptPath = Join-Path $PSScriptRoot "drive_integrity_safe.ps1"
if (-not (Test-Path -LiteralPath $scriptPath)) { throw "Missing script: $scriptPath" }

$driveArg = ($Drives | ForEach-Object { $_.Trim().TrimEnd(':') } | Where-Object { $_ }) -join ","
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument ("-NoProfile -ExecutionPolicy Bypass -File `"{0}`" -Drives {1}" -f $scriptPath, $driveArg)

# 4 times/day: 00:00, 06:00, 12:00, 18:00
$triggers = @(
  New-ScheduledTaskTrigger -Daily -At 12:00AM,
  New-ScheduledTaskTrigger -Daily -At 06:00AM,
  New-ScheduledTaskTrigger -Daily -At 12:00PM,
  New-ScheduledTaskTrigger -Daily -At 06:00PM
)

$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew -StartWhenAvailable

# Replace if exists
try { Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue | Out-Null } catch {}

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $triggers -Principal $principal -Settings $settings | Out-Null

Write-Output "Installed scheduled task: $taskName"
Write-Output "It will run 4x/day as SYSTEM with highest privileges."
