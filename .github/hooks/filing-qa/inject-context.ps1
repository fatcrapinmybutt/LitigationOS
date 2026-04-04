# Filing QA — Session Start Context Injection
# Injects dynamic separation counter and session awareness at start

$ErrorActionPreference = 'Stop'

$LogDir  = Join-Path 'logs' 'copilot' 'filing-qa'
$LogFile = Join-Path $LogDir 'qa.log'

if ($env:SKIP_FILING_QA -eq 'true') { exit 0 }

if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

$Timestamp = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')

# Dynamic separation counter (Rule 9: never hardcode)
$LastContact = [datetime]::Parse('2025-07-29')
$Today = [datetime]::UtcNow.Date
$SeparationDays = ($Today - $LastContact).Days

# Session context payload
$Context = @{
    timestamp       = $Timestamp
    event           = 'session_context_injected'
    separation_days = $SeparationDays
    last_contact    = '2025-07-29'
    active_lanes    = @('A:custody', 'C:federal', 'D:PPO', 'E:misconduct', 'F:appellate', 'CRIMINAL')
    dismissed_lanes = @('B:housing')
}

$ContextJson = $Context | ConvertTo-Json -Compress
Add-Content -Path $LogFile -Value $ContextJson

# Output context for the session to consume
Write-Output "SEPARATION_DAYS=$SeparationDays"
Write-Output "LAST_CONTACT=2025-07-29"

exit 0
