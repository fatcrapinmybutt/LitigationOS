# Session Logger — Prompt Submission Hook
# Logs prompt submission events (no prompt content for privacy)

$ErrorActionPreference = 'Stop'

$LogDir = Join-Path 'logs' 'copilot'
$PromptLog = Join-Path $LogDir 'prompts.log'
$LogLevel = if ($env:LOG_LEVEL) { $env:LOG_LEVEL } else { 'INFO' }

# Skip if disabled
if ($env:SKIP_LOGGING -eq 'true') { exit 0 }
if ($LogLevel -eq 'ERROR') { exit 0 }

if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

$Timestamp = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
$Event = "{`"timestamp`":`"$Timestamp`",`"event`":`"promptSubmitted`",`"level`":`"$LogLevel`"}"

Add-Content -Path $PromptLog -Value $Event
