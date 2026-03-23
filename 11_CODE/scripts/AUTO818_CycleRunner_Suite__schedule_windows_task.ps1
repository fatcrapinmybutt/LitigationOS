param(
  [Parameter(Mandatory=$true)][string]$InputZip,
  [Parameter(Mandatory=$true)][string]$Canon,
  [string]$TaskName = "AUTO818_CycleRunner",
  [int]$Minutes = 30
)

$ScriptPath = (Resolve-Path ".\run_windows.ps1").Path
$Action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-ExecutionPolicy Bypass -File `"$ScriptPath`" -InputZip `"$InputZip`" -Canon `"$Canon`" -WorkDir `"$PWD`""
$Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes $Minutes) -RepetitionDuration ([TimeSpan]::MaxValue)
Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Force

Write-Host "Scheduled task created: $TaskName (every $Minutes minutes)"
