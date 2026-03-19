from datetime import datetime
from pathlib import Path

# Generate a clean PowerShell script file (no Python headers, pure .ps1)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
filename = f"Ultimate_Legal_Classifier_CLEAN_{timestamp}.ps1"

script_content = r'''
# CLEAN POWERFUL LEGAL CLASSIFIER SCRIPT (.ps1 ONLY)

# === CONFIGURATION ===
$benchbookScanRoot = "F:\"
$benchbookTargetDir = "F:\Benchbook_Project"
$stagingRoot = "F:\_Git_Staging"
$pdftotextExe = '"C:\Program Files\Glyph & Cog\XpdfReader-win64\pdftotext.exe"'

# Output paths
$matrixOutput = "$benchbookTargetDir\benchbook_matrix.json"
$statuteMapOutput = "$benchbookTargetDir\statute_map.json"
$aiCachePath = "$stagingRoot\00_SYSTEM_CORE\CENTRAL_DASHBOARD\AI_CACHE\label_training.json"
$refinementLogPath = "$stagingRoot\00_SYSTEM_CORE\CENTRAL_DASHBOARD\METRICS\reclassification_audit.json"
$priorityAuditPath = "$stagingRoot\00_SYSTEM_CORE\CENTRAL_DASHBOARD\METRICS\dashboard_priority_flags.json"
$moveLogPath = "$stagingRoot\00_SYSTEM_CORE\CENTRAL_DASHBOARD\METRICS\move_log.json"
$classifiedLogPath = "$stagingRoot\00_SYSTEM_CORE\CENTRAL_DASHBOARD\METRICS\classified_log.json"
$statuteRefPath = "$stagingRoot\00_SYSTEM_CORE\CENTRAL_DASHBOARD\METRICS\statute_routing_reference.json"

# === PREP ===
$requiredDirs = @($benchbookTargetDir, "$stagingRoot\00_SYSTEM_CORE\CENTRAL_DASHBOARD\AI_CACHE", "$stagingRoot\00_SYSTEM_CORE\CENTRAL_DASHBOARD\METRICS", "$stagingRoot\01_CLASSIFIED")
foreach ($dir in $requiredDirs) { if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null } }

# === SCAN & OCR BENCHBOOKS ===
Write-Host "`n🔍 Scanning for PDFs and performing OCR..."
Get-ChildItem -Path $benchbookScanRoot -Recurse -Filter *.pdf | ForEach-Object {
    $pdfPath = $_.FullName
    $ocrTxtPath = "$benchbookTargetDir\$($_.BaseName).txt"
    $cmd = "$pdftotextExe -f 1 -l 1 `"$pdfPath`" `"$ocrTxtPath`""
    try { Invoke-Expression $cmd } catch { Write-Warning "OCR failed for $($_.Name)" }
}

# === EXTRACT MCL / MCR ===
$benchbookMatrix = @{}
Get-ChildItem -Path $benchbookTargetDir -Filter *.txt | ForEach-Object {
    $filePath = $_.FullName
    $content = Get-Content $filePath -Raw
    $matches = Select-String -InputObject $content -Pattern 'MCL\s\d+\.\d+[a-z]*|\bMCR\s\d+\.\d+[a-z]*' -AllMatches
    if ($matches.Matches.Count -gt 0) {
        $label = ($_.BaseName).ToLower() -replace '[^a-z0-9]', '_'
        if (-not $benchbookMatrix.ContainsKey($label)) { $benchbookMatrix[$label] = @() }
        foreach ($match in $matches.Matches) {
            $ref = $match.Value.Trim()
            if ($benchbookMatrix[$label] -notcontains $ref) { $benchbookMatrix[$label] += $ref }
        }
    }
}
$benchbookMatrix | ConvertTo-Json -Depth 5 | Set-Content $matrixOutput

# === ROUTING MAP ===
$labelStatuteMap = @{}
foreach ($entry in $benchbookMatrix.GetEnumerator()) {
    $label = $entry.Key
    $statutes = $entry.Value
    foreach ($statute in $statutes) {
        $shortLabel = switch -Regex ($label) {
            'custody'        { 'custody_motion' }
            'alienation'     { 'alienation_video' }
            'police|report'  { 'police_report' }
            'benchbook'      { 'benchbook_procedure' }
            'foc|form'       { 'foc_filing' }
            'appclose|parent' { 'appclose_log' }
            'pp[o|f]'        { 'ppo_case' }
            default          { 'misc_procedure' }
        }
        if (-not $labelStatuteMap.ContainsKey($shortLabel)) { $labelStatuteMap[$shortLabel] = @() }
        if ($labelStatuteMap[$shortLabel] -notcontains $statute) { $labelStatuteMap[$shortLabel] += $statute }
    }
}
$labelStatuteMap | ConvertTo-Json -Depth 5 | Set-Content $statuteMapOutput

Write-Host "`n✅ OCR complete, statute references parsed and routed. Ready for classifier integration."
'''

# Save clean .ps1 script
output_path = Path("/mnt/data") / filename
with open(output_path, "w", encoding="utf-8") as f:
    f.write(script_content)

output_path.name
