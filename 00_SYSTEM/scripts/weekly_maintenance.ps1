<#
.SYNOPSIS
    LitigationOS Weekly Maintenance — PowerShell Wrapper
.DESCRIPTION
    Runs the weekly_maintenance.py health check and optionally registers
    a Windows Scheduled Task for automatic Sunday 2:00 AM execution.
.EXAMPLE
    .\weekly_maintenance.ps1                 # Quick scan (default)
    .\weekly_maintenance.ps1 -Full           # Full scan
    .\weekly_maintenance.ps1 -Register       # Register scheduled task
    .\weekly_maintenance.ps1 -Unregister     # Remove scheduled task
#>

[CmdletBinding()]
param(
    [switch]$Full,
    [switch]$Register,
    [switch]$Unregister
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$PythonScript = Join-Path $ScriptDir "weekly_maintenance.py"
$TaskName = "LitigationOS_Weekly"
$LogDir = "C:\Users\andre\LitigationOS\00_SYSTEM\logs"

# ── Register / Unregister scheduled task ────────────────────────────────────
if ($Register) {
    Write-Host "[+] Registering scheduled task: $TaskName" -ForegroundColor Cyan
    # One-liner equivalent:
    # schtasks /create /tn "LitigationOS_Weekly" /tr "python C:\Users\andre\LitigationOS\00_SYSTEM\scripts\weekly_maintenance.py --full" /sc weekly /d SUN /st 02:00 /f
    $action = New-ScheduledTaskAction `
        -Execute "python" `
        -Argument "`"$PythonScript`" --full" `
        -WorkingDirectory "C:\Users\andre\LitigationOS"
    $trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At 2am
    $settings = New-ScheduledTaskSettingsSet `
        -StartWhenAvailable `
        -DontStopOnIdleEnd `
        -ExecutionTimeLimit (New-TimeSpan -Hours 1)
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Description "LitigationOS weekly health check — drives, DB, deadlines, filings, agents, backups, gaps" `
        -Force
    Write-Host "[OK] Task registered. Runs every Sunday at 2:00 AM." -ForegroundColor Green
    Write-Host "     Manual run: schtasks /run /tn `"$TaskName`"" -ForegroundColor Gray
    exit 0
}

if ($Unregister) {
    Write-Host "[-] Removing scheduled task: $TaskName" -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
    Write-Host "[OK] Task removed." -ForegroundColor Green
    exit 0
}

# ── Run maintenance ─────────────────────────────────────────────────────────
if (-not (Test-Path $PythonScript)) {
    Write-Error "Python script not found at: $PythonScript"
    exit 1
}

# Ensure log directory exists
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

$mode = if ($Full) { "--full" } else { "--quick" }
$timestamp = Get-Date -Format "yyyy-MM-dd_HHmmss"
$logFile = Join-Path $LogDir "weekly_maintenance_$timestamp.log"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  LitigationOS Weekly Maintenance" -ForegroundColor Cyan
Write-Host "  Mode: $($Full ? 'FULL' : 'QUICK')" -ForegroundColor Cyan
Write-Host "  Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

try {
    python $PythonScript $mode 2>&1 | Tee-Object -FilePath $logFile
    $exitCode = $LASTEXITCODE
}
catch {
    Write-Error "Failed to run maintenance script: $_"
    $exitCode = 1
}

Write-Host ""
if ($exitCode -eq 0) {
    Write-Host "[OK] Maintenance complete. Log: $logFile" -ForegroundColor Green
} else {
    Write-Host "[FAIL] Maintenance exited with code $exitCode. Check log: $logFile" -ForegroundColor Red
}

exit $exitCode

<#
── QUICK REFERENCE ───────────────────────────────────────────────────────────

Register as scheduled task (one-liner):
  schtasks /create /tn "LitigationOS_Weekly" /tr "python C:\Users\andre\LitigationOS\00_SYSTEM\scripts\weekly_maintenance.py --full" /sc weekly /d SUN /st 02:00 /f

Manual run from CLI:
  python C:\Users\andre\LitigationOS\00_SYSTEM\scripts\weekly_maintenance.py --quick
  python C:\Users\andre\LitigationOS\00_SYSTEM\scripts\weekly_maintenance.py --full

Force run scheduled task:
  schtasks /run /tn "LitigationOS_Weekly"

Check task status:
  schtasks /query /tn "LitigationOS_Weekly" /v
#>
