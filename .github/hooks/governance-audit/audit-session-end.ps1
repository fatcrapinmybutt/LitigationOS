# Governance Audit — Session End Hook
# Logs session end with threat summary

$ErrorActionPreference = 'Stop'

$LogDir = Join-Path 'logs' 'copilot' 'governance'
$LogFile = Join-Path $LogDir 'audit.log'

# Skip if disabled
if ($env:SKIP_GOVERNANCE_AUDIT -eq 'true') { exit 0 }

if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

# Count threats from this session
$ThreatCount = 0
$TotalEvents = 0
if (Test-Path $LogFile) {
    $ThreatCount = @(Select-String -Path $LogFile -Pattern '"event":"threat_detected"' -SimpleMatch).Count
    $TotalEvents = (Get-Content $LogFile | Measure-Object -Line).Lines
}

$Timestamp = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
$Event = "{`"timestamp`":`"$Timestamp`",`"event`":`"session_end`",`"total_events`":$TotalEvents,`"threats_detected`":$ThreatCount}"

Add-Content -Path $LogFile -Value $Event
