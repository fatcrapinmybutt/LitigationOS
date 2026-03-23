param(
  [string]$TaskName = "TRUE_MASTER_DAILY_PLAN"
)
Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
Write-Host "Uninstalled scheduled task: $TaskName"
