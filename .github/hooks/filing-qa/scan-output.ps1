# Filing QA — Output Scan Hook
# Catches litigation-specific errors in AI-generated content before it reaches the user.
# Patterns based on Rules 3-6, 10-14 from copilot-instructions.md v6.0

$ErrorActionPreference = 'Stop'

$LogDir  = Join-Path 'logs' 'copilot' 'filing-qa'
$LogFile = Join-Path $LogDir 'qa.log'

if ($env:SKIP_FILING_QA -eq 'true') { exit 0 }

if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

$Timestamp = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')

$Content = ''
if ([Console]::IsInputRedirected) {
    try { $Content = [Console]::In.ReadToEnd() } catch { $Content = '' }
}

if (-not $Content) { exit 0 }

$script:Violations = [System.Collections.ArrayList]::new()

function Test-Violation {
    param(
        [string]$Rule,
        [string]$Severity,
        [string]$Description,
        [string]$Pattern,
        [string]$Fix
    )
    if ($Content -match $Pattern) {
        $evidence = ($Matches[0]).Substring(0, [Math]::Min($Matches[0].Length, 80))
        [void]$script:Violations.Add(@{
            rule        = $Rule
            severity    = $Severity
            description = $Description
            evidence    = $evidence -replace '["\\]', ''
            fix         = $Fix
        })
    }
}

# Rule 2: Child's full name must never appear (MCR 8.119(H))
Test-Violation 'R2' 'CRITICAL' 'Child full name exposed' `
    '(?i)\b(L\.?\s*D\.?\s*W\w+|the child.s full name)' `
    'Use initials L.D.W. only per MCR 8.119(H)'

# Rule 4: No AI/DB references in filings
Test-Violation 'R4' 'HIGH' 'AI/DB reference in output' `
    '(?i)(LitigationOS|litigation_context\.db|evidence_quotes|impeachment_matrix|nexus_fuse|SINGULARITY|EGCP.score|readiness.score)' `
    'Strip all AI/DB references from court-facing content'

# Rule 10: Pro se — no "undersigned counsel"
Test-Violation 'R10' 'HIGH' 'Counsel language in pro se filing' `
    '(?i)(undersigned counsel|attorney for plaintiff|counsel hereby|respectfully submitted.*attorney)' `
    'Replace with "Plaintiff, appearing pro se"'

# Rule 11: Defendant name must be exact
Test-Violation 'R11' 'MEDIUM' 'Wrong defendant name variant' `
    '(?i)(Emily\s+(Tiffany|Ann|M\.|Marie)\s+Watson|Tiffany\s+Watson)' `
    'Defendant is Emily A. Watson — not Tiffany, Ann, or Marie'

# Rule 13: MCL 722.27c does not exist
Test-Violation 'R13' 'HIGH' 'Non-existent statute cited' `
    '(?i)MCL\s+722\.27c' `
    'MCL 722.27c does not exist — use MCL 722.23(j) instead'

# Rule 14: Brady v Maryland in family law context
Test-Violation 'R14' 'MEDIUM' 'Criminal doctrine in family law' `
    '(?i)Brady\s+v\.?\s+Maryland' `
    'Brady is criminal-only. Use Mathews v Eldridge for family law due process'

# Rule 12: Judge name spelling
Test-Violation 'R12' 'MEDIUM' 'Judge name misspelled' `
    '(?i)(McN[ei]l[^l]|McNeil[^l])' `
    'Two Ls: McNeill (not McNeil or McNiel)'

# Hallucination: Jane/Patricia Berry
Test-Violation 'R3' 'HIGH' 'Hallucinated person name' `
    '(?i)(Jane\s+Berry|Patricia\s+Berry)' `
    'No such person exists in this case. Judge spouse is Cavan Berry'

# Hallucination: Hardcoded separation day count (stale fast)
Test-Violation 'R9' 'MEDIUM' 'Hardcoded separation count' `
    '(?i)(5[0-9]{2}|6[0-9]{2}|7[0-9]{2}|8[0-9]{2})\s+days?\s+(of\s+)?separation' `
    'Always calculate dynamically: (today - 2025-07-29).days'

# Safety: Case number leaking to external
Test-Violation 'SAFETY' 'CRITICAL' 'Case number near external service' `
    '(?i)(2024-001507|2023-5907|366810).{0,60}(api|webhook|endpoint|curl|fetch|https?://)' `
    'Never send case numbers to external services'

# Rule 15: Pro se language enforcement — broader than R10
# Andrew is pro se. Any counsel/attorney-for language is wrong.
Test-Violation 'R15' 'ERROR' 'Counsel language in pro se filing' `
    '(?i)(undersigned\s+counsel|counsel\s+for\s+(the\s+)?(plaintiff|defendant)|attorney\s+for\s+(the\s+)?(plaintiff|defendant|petitioner|respondent)|counsel\s+for\s+(the\s+)?defendant)' `
    'Andrew is pro se. Replace with "Plaintiff, appearing pro se"'

# Rule 16: Dynamic separation counter — hardcoded day counts go stale
# Any specific number of days + "separated"/"without" should be computed from 2025-07-29.
Test-Violation 'R16' 'WARNING' 'Hardcoded separation day count' `
    '(?i)\b[1-9]\d{1,2}\s+days?\s+(separated|without\s+(contact|parenting|visitation|access|his))' `
    'Do not hardcode day counts. Calculate dynamically: (today - 2025-07-29).days'

$ViolationCount = $script:Violations.Count

if ($ViolationCount -gt 0) {
    $CriticalCount = ($script:Violations | Where-Object { $_.severity -eq 'CRITICAL' }).Count
    $ViolationsJson = ($script:Violations | ForEach-Object {
        "{`"rule`":`"$($_.rule)`",`"severity`":`"$($_.severity)`",`"description`":`"$($_.description)`",`"evidence`":`"$($_.evidence)`",`"fix`":`"$($_.fix)`"}"
    }) -join ','
    $Event = "{`"timestamp`":`"$Timestamp`",`"event`":`"filing_qa_violations`",`"count`":$ViolationCount,`"critical`":$CriticalCount,`"violations`":[$ViolationsJson]}"
    Add-Content -Path $LogFile -Value $Event

    [Console]::Error.WriteLine("⚠️ Filing QA: $ViolationCount violation(s) detected ($CriticalCount critical)")
    foreach ($v in $script:Violations) {
        [Console]::Error.WriteLine("  [$($v.severity)] $($v.description): $($v.fix)")
    }
}
else {
    $Event = "{`"timestamp`":`"$Timestamp`",`"event`":`"filing_qa_passed`",`"status`":`"clean`"}"
    Add-Content -Path $LogFile -Value $Event
}

exit 0
