# ROLodex_ProgressReport.ps1
# Full Violation Summary Report Generator for ROLodex System

$rolodexPath = "F:\ROLodex_Core.json"
$txtReport   = "F:\Progress_Timeline.txt"
$csvReport   = "F:\Progress_Summary.csv"
$logPath     = "F:\ROLodex_Log.txt"

# Step 1: Validate input
if (!(Test-Path $rolodexPath)) {
    Write-Host "❌ ROLodex_Core.json not found at $rolodexPath."
    return
}

# Step 2: Load entries
$entries = Get-Content $rolodexPath -Raw | ConvertFrom-Json
$total = $entries.Count
$high = 0
$violatorStats = @{}

# Step 3: Create timeline TXT and CSV report
Set-Content $txtReport "=== ROLodex Violation Timeline Report ===`n"
Set-Content $csvReport "Date,Violator,Law,Trigger,Score,RecommendedAction"

foreach ($entry in $entries | Sort-Object date) {
    $txt = "[$($entry.date)] $($entry.violator) → $($entry.law) | $($entry.trigger)`n➤ Score: $($entry.score) | Action: $($entry.recommended_action)`n"
    Add-Content $txtReport $txt

    Add-Content $csvReport "$($entry.date),$($entry.violator),$($entry.law),$($entry.trigger),$($entry.score),$($entry.recommended_action)"

    if ($entry.Score -ge 9) { $high++ }

    if ($violatorStats.ContainsKey($entry.violator)) {
        $violatorStats[$entry.violator] += 1
    } else {
        $violatorStats[$entry.violator] = 1
    }
}

# Step 4: Append summary
Add-Content $txtReport "`n=== Summary ==="
Add-Content $txtReport "Total Violations: $total"
Add-Content $txtReport "High-Severity (≥9): $high"
Add-Content $txtReport "Violator Breakdown:"

foreach ($key in $violatorStats.Keys) {
    Add-Content $txtReport "${key}: $($violatorStats[$key])"
}

# Step 5: Output result
Write-Host "✅ Progress report generated successfully:"
Write-Host "📄 Timeline: $txtReport"
Write-Host "📊 Summary:  $csvReport"

# Step 6: Auto-open reports
Start-Process notepad.exe "$txtReport"
Start-Process "excel.exe" "$csvReport"
