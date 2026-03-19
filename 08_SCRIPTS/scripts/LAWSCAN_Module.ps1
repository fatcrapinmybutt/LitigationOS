# LAWSCAN_Module_Spinner.ps1
# Headless spinner-enabled LAWSCAN variant

$source = "F:\"
$violators = @("Emily Watson", "Cody Watson", "Lori Watson", "Albert Watson", "Shady Oaks", "Homes of America", "Mandi Martini")
$exclude = @("Andrew Pigors", "Lincoln Watson")
$extensions = "*.pdf", "*.docx", "*.txt"

$matrix = @()
$logFile = Join-Path $source "LAWSCAN_Violation_Log.txt"
$csvOut  = Join-Path $source "Violation_Matrix.csv"
$jsonOut = Join-Path $source "violations.json"

$rules = @(
    @{ Law="MCL 552.644";     Trigger="denied parenting time|refused visitation|withheld child";                    Score=10 },
    @{ Law="MCR 3.211(C)";    Trigger="failed to follow parenting schedule";                                        Score=9  },
    @{ Law="MCR 3.606";       Trigger="contempt";                                                                   Score=10 },
    @{ Law="MCR 3.206(C)";    Trigger="bad faith litigation|frivolous motion|misuse of court";                      Score=9  },
    @{ Law="MCL 600.2950";    Trigger="false ppo|no contact order abused|weaponized ppo";                           Score=10 },
    @{ Law="Benchbook PPO";   Trigger="no imminent threat|no police report|used ppo to gain custody";              Score=8  },
    @{ Law="Benchbook LT";    Trigger="constructive eviction|uninhabitable|failed to repair sewage|retaliation";   Score=9  }
)

function Extract-Text($file) {
    $ext = $file.Extension.ToLower()
    try {
        switch ($ext) {
            ".pdf"  { return (pdftotext $file.FullName - | Out-String) }
            ".docx" { return (Get-Content $file.FullName -Raw) }
            ".txt"  { return (Get-Content $file.FullName -Raw) }
            default { return "" }
        }
    } catch { return "" }
}

Set-Content $csvOut "Violator,Violation,Law,Score,Source,Date"
Add-Content $logFile "`n==== LAWSCAN STARTED $(Get-Date) ===="

# START SPINNER
$script:spin = $true
$spinnerJob = Start-Job -ScriptBlock {
    $chars = @('|','/','-','\')
    $i = 0
    while ($using:script:spin) {
        Write-Host -NoNewline "`rScanning files... $($chars[$i % $chars.Length])"
        Start-Sleep -Milliseconds 100
        $i++
    }
    Write-Host "`rScanning complete.            "
}

# MAIN SCAN
$allFiles = Get-ChildItem $source -Recurse -File -Include $extensions
foreach ($file in $allFiles) {
    $text = Extract-Text $file
    if (-not $text) { continue }

    foreach ($name in $violators) {
        if ($text -match [Regex]::Escape($name)) {
            foreach ($rule in $rules) {
                if ($text -match $rule.Trigger -and ($text -notmatch ($exclude -join "|"))) {
                    $entry = [PSCustomObject]@{
                        Violator  = $name
                        Violation = $rule.Trigger
                        Law       = $rule.Law
                        Score     = $rule.Score
                        Source    = $file.Name
                        Date      = $file.CreationTime.ToString("yyyy-MM-dd")
                    }

                    $matrix += $entry
                    Add-Content $logFile ("[{0}] {1} | {2} | Score: {3} | File: {4}" -f (Get-Date -Format "HH:mm:ss"), $name, $rule.Law, $rule.Score, $file.Name)

                    Add-Content $csvOut (
                        "$($entry.Violator),$($entry.Violation),$($entry.Law),$($entry.Score),$($entry.Source),$($entry.Date)"
                    )
                }
            }
        }
    }
}

# STOP SPINNER
$script:spin = $false
Wait-Job $spinnerJob | Out-Null
Remove-Job $spinnerJob | Out-Null

# OUTPUT
$matrix | ConvertTo-Json -Depth 4 | Out-File -Encoding UTF8 $jsonOut
Add-Content $logFile "==== LAWSCAN COMPLETED $(Get-Date) ===="
