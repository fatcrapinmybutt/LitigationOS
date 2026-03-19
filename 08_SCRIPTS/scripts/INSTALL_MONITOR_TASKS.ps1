$taskName = "LITIGATION_GUI_BOOT"
$taskDesc = "Launch GUI_TOGGLE_DASHBOARD on user login"

$action = New-ScheduledTaskAction -Execute "python.exe" -Argument "F:\SYSTEM\GUI_TOGGLE_DASHBOARD.py"
$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Description $taskDesc -Settings $settings -User "$env:USERNAME" -RunLevel Highest -Force
Write-Host "GUI Autostart Task Registered."
