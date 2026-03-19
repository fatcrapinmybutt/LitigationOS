# ROLodex_EvidenceSystem.ps1
# Unified Evidence → ROLodex → Timeline Export Engine

# ===[ CONFIGURATION ]===
$source = "F:\"
$violators = @("Emily Watson", "Cody Watson", "Lori Watson", "Albert Watson", "Shady Oaks", "Homes of America", "Mandi Martini")
$exclude   = @("Andrew Pigors", "Lincoln Watson")
$extensions = "*.pdf", "*.docx", "*.txt", "*.csv"

# ===[ FILE OUTPUTS ]===
$evidenceJson = Join-Path $source "EvidenceLibrary.json"
$rolodexJson  = Join-Path $source "ROLodex_Core.json"
$csvOut       = Join-Path $source "ROLodex_Timeline.csv"
$txtOut       = Join-Path $source "ROLodex_Timeline.txt"
$htmlOut      = Join-Path $source "ROLodex_Dashboard.html"
$logFile      = Join-Path $source "ROLodex_Log.txt"

# ===[ TRIGGER MAP ]===
$triggers = @(
    @{ Match="withheld parenting time";            Law="MCL 552.644";      Score=10 },
    @{ Match="denied visitation";                  Law="MCL 552.644";      Score=9 },
    @{ Match="refused to exchange child";          Law="MCL 552.644";      Score=10 },
    @{ Match="filed frivolous ppo";                Law="MCL 600.2950";     Score=10 },
    @{ Match="used ppo to gain custody";           Law="Benchbook PPO";    Score=9 },
    @{ Match="coached child before handoff";       Law="Alienation";       Score=8 },
    @{ Match="bad faith litigation";               Law="MCR 3.206(C)";     Score=9 },
    @{ Match="constructive eviction";              Law="Benchbook LT";     Score=9 },
    @{ Match="retaliatory eviction";               Law="Benchbook LT";     Score=10 },
    @{ Match="failed to follow parenting schedule";Law="MCR 3.211(C)";     Score=9 },
    @{ Match="contempt";                           Law="MCR 3.606";        Score=10 },
    @{ Match="false allegations";                  Law="MCL 600.2950";     Score=9 },
    @{ Match="harassment during exchanges";        Law="PPO Abuse";        Score=9 },
    @{ Match="no imminent threat";                 Law="Benchbook PPO";    Score=8 },
    @{ Match="MCL";                                Law="Statutory";        Score=5 },
    @{ Match="MCR";                                Law="Court Rule";       Score=5 }
)

# ===[ OCR + TEXT EXTRACTION ]===
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
# ===[ ENHANCED SCAN BLOCK – PART 2 ]===

function Get-SHA256($filePath) {
    try {
        $stream = [System.IO.File]::OpenRead($filePath)
        $sha256 = [System.Security.Cryptography.SHA256]::Create()
        $hashBytes = $sha256.ComputeHash($stream)
        $stream.Close()
        return ($hashBytes | ForEach-Object { $_.ToString("x2") }) -join ''
    } catch {
        return "HASH_ERROR"
    }
}

function Get-ContextSnippet($lines, $matchIndex) {
    $start = [Math]::Max(0, $matchIndex - 1)
    $end = [Math]::Min($lines.Length - 1, $matchIndex + 1)
    return ($lines[$start..$end] -join " ").Trim()
}

$results = @()
$allFiles = Get-ChildItem $source -Recurse -File -Include $extensions
$total = $allFiles.Count
$count = 0
$globalStart = Get-Date

Set-Content $logFile "==== ROLodex System Scan Started $(Get-Date) ===="
Set-Content $csvOut "Violator,Trigger,Law,Score,Source,Date,Excerpt,RecommendedAction"

foreach ($file in $allFiles) {
    $count++
    $fileStart = Get-Date
    Write-Progress -Activity "Scanning Files..." -Status "$count of $total" -PercentComplete (($count / $total) * 100)

    $text = Extract-Text $file
    if (-not $text) { continue }
    $lines = $text -split "`n"
    $hash = Get-SHA256 $file.FullName
    $fileDate = $file.CreationTime.ToString("yyyy-MM-dd")

    foreach ($violator in $violators) {
        if ($text -match [Regex]::Escape($violator)) {
            foreach ($trigger in $triggers) {
                for ($i = 0; $i -lt $lines.Length; $i++) {
                    if ($lines[$i] -match $trigger.Match -or $lines[$i] -like "*$($trigger.Match)*") {
                        if ($lines[$i] -notmatch ($exclude -join "|")) {
                            $context = Get-ContextSnippet $lines $i
                            $recAction = switch ($trigger.Law) {
                                "MCL 552.644"     { "Motion for Contempt" }
                                "MCR 3.606"       { "Contempt Sanction" }
                                "MCR 3.206(C)"    { "Request Sanctions" }
                                "MCL 600.2950"    { "PPO Dismissal" }
                                "Benchbook LT"    { "Retaliation Report" }
                                "Benchbook PPO"   { "Judicial Notice / PPO Strike" }
                                default           { "Flag for Review" }
                            }

                            $obj = [PSCustomObject]@{
                                Violator           = $violator
                                Trigger            = $trigger.Match
                                Law                = $trigger.Law
                                Score              = $trigger.Score
                                Source             = $file.Name
                                Date               = $fileDate
                                Excerpt            = $context
                                FileHash           = $hash
                                RecommendedAction  = $recAction
                            }

                            $results += $obj
                            Add-Content $logFile "[+] $($violator) triggered $($trigger.Match) in $($file.Name)"
                            Add-Content $csvOut "$($obj.Violator),$($obj.Trigger),$($obj.Law),$($obj.Score),$($obj.Source),$($obj.Date),""$($obj.Excerpt)"",$($obj.RecommendedAction)"
                        }
                    }
                }
            }
        }
    }

    $fileElapsed = (Get-Date) - $fileStart
    Add-Content $logFile "🕒 Processed $($file.Name) in $([int]$fileElapsed.TotalSeconds)s"
}

# Save final JSON
$results | ConvertTo-Json -Depth 4 | Out-File -Encoding UTF8 $evidenceJson
$elapsed = (Get-Date) - $globalStart
Add-Content $logFile "✅ Completed full scan in $([int]$elapsed.TotalMinutes) minute(s), $([int]$elapsed.TotalSeconds) second(s)"
# ===[ PART 3: BUILD ROLODEX CORE ]===

if (!(Test-Path $evidenceJson)) {
    Write-Host "❌ EvidenceLibrary.json not found. Cannot continue ROLodex build."
    return
}

$rolodex = @()
$evidence = Get-Content $evidenceJson -Raw | ConvertFrom-Json
$total = $evidence.Count
$count = 0

foreach ($entry in $evidence) {
    $count++
    Write-Progress -Activity "Linking to ROLodex" `
                   -Status "$count of $total entries" `
                   -PercentComplete (($count / $total) * 100)

    $rolodexEntry = [PSCustomObject]@{
        type              = "legal_violation"
        violator          = $entry.Violator
        trigger           = $entry.Trigger
        law               = $entry.Law
        score             = $entry.Score
        source            = $entry.Source
        date              = $entry.Date
        excerpt           = $entry.Excerpt
        file_hash         = $entry.FileHash
        recommended_action= $entry.RecommendedAction
        rolodex_tag       = if ($entry.Score -ge 9) { "HIGH_PRIORITY" } else { "LOW_PRIORITY" }
    }

    $rolodex += $rolodexEntry
}

# Merge with existing ROLodex_Core.json if exists
if (Test-Path $rolodexJson) {
    $existing = Get-Content $rolodexJson -Raw | ConvertFrom-Json
    $rolodex += $existing
}

# Final sort by date
$rolodex | Sort-Object date | ConvertTo-Json -Depth 4 | Out-File -Encoding UTF8 $rolodexJson
Add-Content $logFile "📇 ROLodex_Core.json generated with $($rolodex.Count) total entries"
# ===[ PART 4: EXPORTS — TXT, CSV, HTML ]===

if (!(Test-Path $rolodexJson)) {
    Write-Host "❌ ROLodex_Core.json missing. Cannot generate exports."
    return
}

$entries = Get-Content $rolodexJson -Raw | ConvertFrom-Json
Set-Content $txtOut "=== ROLodex Violation Timeline ===`n"
Set-Content $csvOut "Date,Violator,Law,Trigger,Score,RecommendedAction,Excerpt"

$rows = ""

foreach ($item in $entries | Sort-Object date, score -Descending) {
    $line = "[$($item.date)] [$($item.score)] $($item.violator) violated $($item.law): $($item.trigger)"
    $line += "`n➤ Action: $($item.recommended_action)"
    $line += "`n➤ Source: $($item.source)"
    $line += "`n➤ Excerpt: $($item.excerpt)`n"
    Add-Content $txtOut $line

    Add-Content $csvOut (
        "$($item.date),$($item.violator),$($item.law),$($item.trigger),$($item.score),$($item.recommended_action),""$($item.excerpt)"""
    )

    $rows += "<tr>
        <td>$($item.date)</td>
        <td>$($item.violator)</td>
        <td>$($item.law)</td>
        <td>$($item.trigger)</td>
        <td>$($item.score)</td>
        <td>$($item.recommended_action)</td>
        <td><code>$($item.excerpt)</code></td>
    </tr>`n"
}

# === HTML DASHBOARD ===
$html = @"
<html><head>
<title>ROLodex Dashboard</title>
<style>
body { font-family: Arial; }
table { border-collapse: collapse; width: 100%; }
th, td { border: 1px solid #ccc; padding: 6px; }
th { background-color: #f2f2f2; }
code { background-color: #f9f9f9; display: block; padding: 4px; }
</style>
</head><body>
<h2>ROLodex Dashboard – Violations Summary</h2>
<table>
<tr><th>Date</th><th>Violator</th><th>Law</th><th>Trigger</th><th>Score</th><th>Action</th><th>Excerpt</th></tr>
$rows
</table>
</body></html>
"@

Add-Content $txtReport "`n=== Summary ==="
Add-Content $txtReport "Total Violations: $total"
Add-Content $txtReport "High-Severity (≥9): $high"
Add-Content $txtReport "Violator Breakdown:"

foreach ($key in $violatorStats.Keys) {
    Add-Content $txtReport "$key: $($violatorStats[$key])"
}

Write-Host "✅ Progress report generated:"
Write-Host "📄 $txtReport"
Write-Host "📊 $csvReport"

# Automatically open the reports
Start-Process notepad.exe $txtReport
Start-Process "excel.exe" $csvReport


