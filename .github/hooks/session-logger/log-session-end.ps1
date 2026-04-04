# Session Logger — Session End Hook
# Logs session end event

$ErrorActionPreference = 'Stop'

$LogDir = Join-Path 'logs' 'copilot'
$LogFile = Join-Path $LogDir 'session.log'
$LogLevel = if ($env:LOG_LEVEL) { $env:LOG_LEVEL } else { 'INFO' }

# Skip if disabled
if ($env:SKIP_LOGGING -eq 'true') { exit 0 }
if ($LogLevel -eq 'ERROR') { exit 0 }

if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

$Timestamp = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
$Event = "{`"timestamp`":`"$Timestamp`",`"event`":`"sessionEnd`",`"level`":`"$LogLevel`"}"

Add-Content -Path $LogFile -Value $Event
