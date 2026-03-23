param(
  [string]$TaskName = "LitigationOS_Harvest_4xDaily",
  [string]$ExePath = "$PSScriptRoot\..\dist\LitigationOS\LitigationOS.exe",
  [string]$WorkingDir = (Resolve-Path "$PSScriptRoot\..").Path,
  [string]$ConfigPath = "$PSScriptRoot\..\config\config.json"
)
$ExePath = (Resolve-Path $ExePath).Path
$WorkingDir = (Resolve-Path $WorkingDir).Path
$ConfigPath = (Resolve-Path $ConfigPath).Path
$times = @("00:00","06:00","12:00","18:00")
$triggers = @()
foreach ($t in $times) { $triggers += New-ScheduledTaskTrigger -Daily -At $t }
$arg = "--config `"$ConfigPath`" --fast"
$action = New-ScheduledTaskAction -Execute $ExePath -Argument $arg -WorkingDirectory $WorkingDir
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Hours 6)
$principal = New-ScheduledTaskPrincipal -UserId $env:UserName -LogonType S4U -RunLevel Highest
$task = New-ScheduledTask -Action $action -Trigger $triggers -Settings $settings -Principal $principal
Register-ScheduledTask -TaskName $TaskName -InputObject $task -Force | Out-Null
Write-Host "Scheduled Task installed: $TaskName"
Write-Host "EXE: $ExePath"
Write-Host "Args: $arg"
