# Governance Audit — Session Start Hook
# Logs session start event for governance audit trail

$ErrorActionPreference = 'Stop'

$LogDir = Join-Path 'logs' 'copilot' 'governance'
$LogFile = Join-Path $LogDir 'audit.log'
$GovernanceLevel = if ($env:GOVERNANCE_LEVEL) { $env:GOVERNANCE_LEVEL } else { 'standard' }

# Skip if disabled
if ($env:SKIP_GOVERNANCE_AUDIT -eq 'true') { exit 0 }

# Ensure log directory exists
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

# Log session start
$Timestamp = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
$Cwd = (Get-Location).Path -replace '\\', '\\'
$Event = "{`"timestamp`":`"$Timestamp`",`"event`":`"session_start`",`"governance_level`":`"$GovernanceLevel`",`"cwd`":`"$Cwd`"}"

Add-Content -Path $LogFile -Value $Event
