param(
  [string]$TaskName = "TRUE_MASTER_DAILY_PLAN",
  [string]$Time = "03:00"
)
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$py = "python"
$script = Join-Path $here "TRUE_MASTER_ORCHESTRATOR_v3.py"
$args = "--mode plan --drives auto --zip-cyclepack"
$action = New-ScheduledTaskAction -Execute $py -Argument "`"$script`" $args" -WorkingDirectory $here
$trigger = New-ScheduledTaskTrigger -Daily -At $Time
Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Description "TRUE_MASTER daily PLAN run (non-destructive) + zipped cyclepack" -Force
Write-Host "Installed scheduled task: $TaskName at $Time"
