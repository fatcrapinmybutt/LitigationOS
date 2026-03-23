param(
  [string]$ApiUrl = "http://127.0.0.1:8000/api/drive/ingest/bulk",
  [string[]]$Paths = @("X:\LITIGATION_INTAKE"),
  [string]$TaskName = "DrivePullerWatchHourly"
)
$payload = ($Paths | ConvertTo-Json -Depth 3)
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoLogo -NoProfile -WindowStyle Hidden -Command Invoke-RestMethod -Method Post -Uri $ApiUrl -ContentType 'application/json' -Body '$payload' | Out-Null"
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(5) -RepetitionInterval (New-TimeSpan -Hours 1) -RepetitionDuration (New-TimeSpan -Days 3650)
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Force
Write-Host "✅ Scheduled $TaskName to hit $ApiUrl hourly."
