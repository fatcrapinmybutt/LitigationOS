$Action = New-ScheduledTaskAction -Execute "python.exe" -Argument "F:\GOLDEN_OS\golden_main.py"
$Trigger = New-ScheduledTaskTrigger -AtStartup
Register-ScheduledTask -Action $Action -Trigger $Trigger -TaskName "GOLDEN_OS_BOOT" -Description "Run GOLDEN_OS on boot" -User "SYSTEM" -RunLevel Highest -Force
