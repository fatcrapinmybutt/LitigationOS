param(
  [string]$TaskNameFast = "LitigationOS_Harvest_FAST_3xDaily",
  [string]$TaskNameFull = "LitigationOS_Harvest_FULL_Daily",
  [string]$ExePath = "$PSScriptRoot\..\dist\LitigationOS\LitigationOS.exe",
  [string]$WorkingDir = (Resolve-Path "$PSScriptRoot\..").Path,
  [string]$ConfigPath = "$PSScriptRoot\..\config\config.json"
)
$ExePath = (Resolve-Path $ExePath).Path
$WorkingDir = (Resolve-Path $WorkingDir).Path
$ConfigPath = (Resolve-Path $ConfigPath).Path
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Hours 6)
$principal = New-ScheduledTaskPrincipal -UserId $env:UserName -LogonType S4U -RunLevel Highest

# FAST 06/12/18
$fastTriggers=@()
foreach($t in @("06:00","12:00","18:00")){ $fastTriggers += New-ScheduledTaskTrigger -Daily -At $t }
$fastArg = "--config `"$ConfigPath`" --fast"
$fastAction = New-ScheduledTaskAction -Execute $ExePath -Argument $fastArg -WorkingDirectory $WorkingDir
$fastTask = New-ScheduledTask -Action $fastAction -Trigger $fastTriggers -Settings $settings -Principal $principal
Register-ScheduledTask -TaskName $TaskNameFast -InputObject $fastTask -Force | Out-Null

# FULL 02:00
$fullTriggers=@(New-ScheduledTaskTrigger -Daily -At "02:00")
$fullArg = "--config `"$ConfigPath`""
$fullAction = New-ScheduledTaskAction -Execute $ExePath -Argument $fullArg -WorkingDirectory $WorkingDir
$fullTask = New-ScheduledTask -Action $fullAction -Trigger $fullTriggers -Settings $settings -Principal $principal
Register-ScheduledTask -TaskName $TaskNameFull -InputObject $fullTask -Force | Out-Null

Write-Host "Installed: $TaskNameFast (FAST 06/12/18) and $TaskNameFull (FULL 02:00)"
