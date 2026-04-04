# Governance Audit — Prompt Scan Hook
# Scans user prompts for threat patterns before agent processing

$ErrorActionPreference = 'Stop'

$LogDir = Join-Path 'logs' 'copilot' 'governance'
$LogFile = Join-Path $LogDir 'audit.log'
$GovernanceLevel = if ($env:GOVERNANCE_LEVEL) { $env:GOVERNANCE_LEVEL } else { 'standard' }
$BlockOnThreat = if ($env:BLOCK_ON_THREAT) { $env:BLOCK_ON_THREAT } else { 'false' }

# Skip if disabled
if ($env:SKIP_GOVERNANCE_AUDIT -eq 'true') { exit 0 }

if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

$Timestamp = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')

# Read prompt from stdin if available
$Prompt = ''
if ([Console]::IsInputRedirected) {
    try { $Prompt = [Console]::In.ReadToEnd() } catch { $Prompt = '' }
}

# Threat pattern detection
$script:Threats = [System.Collections.ArrayList]::new()

function Test-ThreatPattern {
    param(
        [string]$Category,
        [double]$Severity,
        [string]$Description,
        [string]$Pattern
    )
    if ($Prompt -match $Pattern) {
        $evidence = $Matches[0] -replace '["\\]', ''
        [void]$script:Threats.Add(@{
            category    = $Category
            severity    = $Severity
            description = $Description
            evidence    = $evidence
        })
    }
}

if ($Prompt) {
    # Data exfiltration
    Test-ThreatPattern 'data_exfiltration' 0.85 'Potential data exfiltration' 'send.*(records|data|files).*(external|api|endpoint|webhook)'
    Test-ThreatPattern 'data_exfiltration' 0.9 'Curl/wget to external host' '(curl|wget|fetch).*https?://'

    # Privilege escalation
    Test-ThreatPattern 'privilege_escalation' 0.9 'Elevated privileges' '(sudo|chmod 777|add.*sudoers|run as admin)'
    Test-ThreatPattern 'privilege_escalation' 0.85 'Service account manipulation' '(create.*service.*account|modify.*permissions)'

    # System destruction
    Test-ThreatPattern 'system_destruction' 0.95 'Recursive deletion' '(rm -rf /|del /s /q|format c:|drop database)'
    Test-ThreatPattern 'system_destruction' 0.9 'System file modification' '(modify.*system32|edit.*/etc/passwd)'

    # Prompt injection
    Test-ThreatPattern 'prompt_injection' 0.8 'Prompt injection attempt' '(ignore.*previous.*instructions|disregard.*rules|you are now|new instructions)'

    # Credential exposure
    Test-ThreatPattern 'credential_exposure' 0.95 'Hardcoded credentials' '(api[_\-]?key|secret[_\-]?key|password|aws_access).*=.*[''""][A-Za-z0-9]'

    # Litigation-specific: child name exposure
    Test-ThreatPattern 'child_privacy' 0.95 'Child full name in prompt' '(?i)\b(L\.?\s*D\.?\s*W\w{3,})\b'

    # Litigation-specific: case number to external service
    Test-ThreatPattern 'data_exfiltration' 0.95 'Case number near external URL' '(?i)(2024-001507|2023-5907|366810).{0,80}(curl|wget|fetch|https?://)'
}

$ThreatCount = $script:Threats.Count

if ($ThreatCount -gt 0) {
    $ThreatsJson = ($script:Threats | ForEach-Object {
        "{`"category`":`"$($_.category)`",`"severity`":$($_.severity),`"description`":`"$($_.description)`",`"evidence`":`"$($_.evidence)`"}"
    }) -join ','
    $Event = "{`"timestamp`":`"$Timestamp`",`"event`":`"threat_detected`",`"governance_level`":`"$GovernanceLevel`",`"threat_count`":$ThreatCount,`"threats`":[$ThreatsJson]}"
    Add-Content -Path $LogFile -Value $Event

    # Block if configured
    if ($GovernanceLevel -eq 'strict' -or $GovernanceLevel -eq 'locked' -or
       ($GovernanceLevel -eq 'standard' -and $BlockOnThreat -eq 'true')) {
        [Console]::Error.WriteLine("⚠️ Governance audit: $ThreatCount threat(s) detected. Prompt blocked.")
        exit 1
    }
}
else {
    $Event = "{`"timestamp`":`"$Timestamp`",`"event`":`"prompt_scanned`",`"governance_level`":`"$GovernanceLevel`",`"status`":`"clean`"}"
    Add-Content -Path $LogFile -Value $Event
}

exit 0
