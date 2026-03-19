# Evidence_Extractor_Core.ps1
# High-Level OCR + Text Scanner for Legal Evidence Extraction (Tier 1 Only)

$source = "F:\"
$violators = @("Emily Watson", "Cody Watson", "Lori Watson", "Albert Watson", "Shady Oaks", "Homes of America", "Mandi Martini")
$exclude = @("Andrew Pigors", "Lincoln Watson")
$extensions = "*.pdf", "*.docx", "*.txt", "*.csv"

$log = Join-Path $source "Evidence_Extraction_Log.txt"
$jsonOut = Join-Path $source "EvidenceLibrary.json"
$csvOut  = Join-Path $source "EvidenceMatrix.csv"

$triggers = @(
    @{ Match="withheld parenting time";            Law="MCL 552.644";      Score=10 },
    @{ Match="denied visitation";                  Law="MCL 552.644";      Score=9 },
    @{ Match="refused to exchange child";          Law="MCL 552.644";      Score=10 },
    @{ Match="instructed child to call someone else dad"; Law="Alienation"; Score=9 },
    @{ Match="coached child before handoff";       Law="Alienation";       Score=8 },
    @{ Match="filed frivolous ppo";                Law="MCL 600.2950";     Score=10 },
    @{ Match="used ppo to gain custody";           Law="Benchbook PPO";    Score=9 },
    @{ Match="bad faith litigation";               Law="MCR 3.206(C)";     Score=9 },
    @{ Match="contempt";                           Law="MCR 3.606";        Score=10 },
    @{ Match="false allegations";                  Law="MCL 600.2950";     Score=9 },
    @{ Match="constructive eviction";              Law="Benchbook LT";     Score=9 },
    @{ Match="retaliatory eviction";               Law="Benchbook LT";     Score=10 },
    @{ Match="threatened with court action";       Law="MCR 3.206(C)";     Score=8 },
    @{ Match="harassment during exchanges";        Law="PPO Abuse";        Score=9 },
    @{ Match="used cps maliciously";               Law="Parental Misuse";  Score=9 },
    @{ Match="failed to follow parenting schedule";Law="MCR 3.211(C)";     Score=9 },
    @{ Match="MCL";                                Law="Statutory";        Score=5 },
    @{ Match="MCR";                                Law="Court Rule";       Score=5 }
)

function Extract-OCRText($file) {
    $tempDir = Join-Path $env:TEMP "ocr_temp"
    if (!(Test-Path $tempDir)) { New-Item -ItemType Directory -Path $tempDir | Out-Null }
    $txtOut = Join-Path $tempDir "page_ocr.txt"
    pdftoppm $file.FullName "$tempDir\page" -png -gray

    $text = ""
    Get-ChildItem "$tempDir\page*.png" | ForEach-Object {
        tesseract $_.FullName $txtOut -l eng | Out-Null
        $pageText = Get-Content "$txtOut.txt" -Raw
        $text += "`n" + $pageText
        Remove-Item $_.FullName -Force
        Remove-Item "$txtOut.txt" -Force -ErrorAction SilentlyContinue
    }
    return $text
}

function Extract-Text($file) {
    try {
        switch ($file.Extension.ToLower()) {
            ".pdf" {
                $text = pdftotext $file.FullName -layout - | Out-String
                if ($text.Length -lt 50) { $text = Extract-OCRText $file }
                return $text
            }
            ".docx" { return (Get-Content $file.FullName -Raw) }
            ".txt"  { return (Get-Content $file.FullName -Raw) }
            ".csv"  { return (Get-Content $file.FullName -Raw) }
            default { return "" }
        }
    } catch { return "" }
}

# Spinner thread
$script:spin = $true
$spinnerJob = Start-Job -ScriptBlock {
    $s = 0; $chars = @('|','/','-','\')
    while ($using:script:spin) {
        Write-Host -NoNewline "`rScanning... $($chars[$s % $chars.Length])"
        Start-Sleep -Milliseconds 100
        $s++
    }
}

# Main scan
$all = Get-ChildItem $source -Recurse -File -Include $extensions
$results = @()

Set-Content $log "==== Evidence Scan Started $(Get-Date) ===="
Set-Content $csvOut "Violator,Trigger,Law,Score,Source,Date,Excerpt"

foreach ($file in $all) {
    $text = Extract-Text $file
    if (-not $text) { continue }

    foreach ($violator in $violators) {
        if ($text -match [Regex]::Escape($violator)) {
            foreach ($trigger in $triggers) {
                if ($text -match $trigger.Match -and ($text -notmatch ($exclude -join "|"))) {
                    $date = $file.CreationTime.ToString("yyyy-MM-dd")
                    $matchLine = ($text -split "`n" | Where-Object { $_ -match $trigger.Match })[0]
                    $obj = [PSCustomObject]@{
                        Violator = $violator
                        Trigger  = $trigger.Match
                        Law      = $trigger.Law
                        Score    = $trigger.Score
                        Source   = $file.Name
                        Date     = $date
                        Excerpt  = $matchLine.Trim()
                    }
                    $results += $obj

                    Add-Content $log ("[{0}] {1} violated {2} via '{3}' in {4}" -f (Get-Date -Format "HH:mm:ss"), $violator, $trigger.Law, $trigger.Match, $file.Name)
                    Add-Content $csvOut "$($obj.Violator),$($obj.Trigger),$($obj.Law),$($obj.Score),$($obj.Source),$($obj.Date),""$($obj.Excerpt)"""
                }
            }
        }
    }
}

# Save JSON + stop spinner
$results | ConvertTo-Json -Depth 4 | Out-File -Encoding UTF8 $jsonOut
$script:spin = $false
Wait-Job $spinnerJob | Out-Null
Remove-Job $spinnerJob | Out-Null
Write-Host "`rScan Complete. $($results.Count) records stored.       "
