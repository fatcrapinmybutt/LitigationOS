from datetime import datetime
from pathlib import Path

# Generate script filename
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
filename = f"Organize_F_Drive_{timestamp}.ps1"

# PowerShell script content
script_content = r'''
# ORGANIZE_F_DRIVE.PS1 — FULLY AUTOMATED LEGAL-LEVEL FILE CLASSIFIER
# ---------------------------------------------------------------

param(
    [switch]$DryRun = $false,
    [switch]$PreserveName = $false,
    [switch]$UpdateAI = $true
)

# === CONFIG ===
$root = "F:\"
$stagingRoot = "$root\_Git_Staging"
$classifiedRoot = "$root\01_CLASSIFIED"
$aiCachePath = "$stagingRoot\00_SYSTEM_CORE\CENTRAL_DASHBOARD\AI_CACHE\label_training.json"
$refinementLogPath = "$stagingRoot\00_SYSTEM_CORE\CENTRAL_DASHBOARD\METRICS\reclassification_audit.json"
$priorityAuditPath = "$stagingRoot\00_SYSTEM_CORE\CENTRAL_DASHBOARD\METRICS\dashboard_priority_flags.json"
$classifiedLogPath = "$stagingRoot\00_SYSTEM_CORE\CENTRAL_DASHBOARD\METRICS\classified_log.json"
$moveLogPath = "$stagingRoot\00_SYSTEM_CORE\CENTRAL_DASHBOARD\METRICS\move_log.json"
$statuteMapPath = "$stagingRoot\00_SYSTEM_CORE\CENTRAL_DASHBOARD\METRICS\statute_routing_reference.json"

# === EXTENSION MAP ===
$fileTypeMap = @{
    "pdf"="PDFs"; "docx"="Word"; "xlsx"="Excel"; "csv"="CSV"; "txt"="Text"; "json"="JSON"
    "mp4"="Videos"; "mov"="Videos"; "jpg"="Images"; "jpeg"="Images"; "png"="Images"
    "gif"="Images"; "zip"="Archives"; "rar"="Archives"; "7z"="Archives"; "html"="Web"
    "xml"="Markup"; "log"="Logs"
}

# === LABEL REGEX MAP ===
function Get-RegexLabel($name) {
    switch -Regex ($name) {
        'pp[o|f]' { return 'ppo_case' }
        'emily|watson' { return 'opposing_party_emily' }
        'custody|motion|modification' { return 'custody_motion' }
        'appclose|co-parent' { return 'appclose_log' }
        'benchbook|rule' { return 'benchbook_procedure' }
        'foc|form|foc10' { return 'foc_filing' }
        'report|officer|police|welfare|check' { return 'police_report' }
        'alienation|video|mp4|vod' { return 'alienation_video' }
        'statute|mcl|mcr' { return 'statutory_reference' }
        default { return 'unclassified' }
    }
}

# === LOAD AI CACHE & STATUTE MAP ===
$aiCache = @{}
if (Test-Path $aiCachePath) {
    (Get-Content $aiCachePath -Raw | ConvertFrom-Json) | ForEach-Object {
        $key = "$($_.fileName)|$($_.extension)"
        $aiCache[$key] = $_.label
    }
}
$statuteMap = @{}
if (Test-Path $statuteMapPath) {
    $statuteMap = Get-Content $statuteMapPath -Raw | ConvertFrom-Json
}

# === LOG CONTAINERS ===
$classifiedLog = @()
$moveLog = @()
$reclassificationAudit = @()
$priorityDashboard = @()

# === SKIP FOLDERS ===
$skipDirs = @('System Volume Information', 'Program Files', 'ProgramData', 'Recycle.Bin', '$RECYCLE.BIN', 'node_modules', '.git')

# === MAIN CLASSIFIER ===
function Classify-And-Move($file) {
    $ext = $file.Extension.ToLower().TrimStart('.')
    $name = $file.BaseName.ToLower()
    $dateFolder = $file.LastWriteTime.ToString("yyyy-MM")
    $timestamp = Get-Date -Format yyyyMMdd_HHmmss
    $aiKey = "$($file.BaseName)|$ext"
    $regexLabel = Get-RegexLabel $name
    $aiLabel = if ($aiCache.ContainsKey($aiKey)) { $aiCache[$aiKey] } else { $null }
    $label = if ($aiLabel) { $aiLabel } else { $regexLabel }

    if ($aiLabel -and ($aiLabel -ne $regexLabel)) {
        $reclassificationAudit += [PSCustomObject]@{ File = $file.Name; OriginalLabel = $regexLabel; ReclassifiedAs = $aiLabel; Timestamp = (Get-Date).ToString("s") }
        $priorityDashboard += [PSCustomObject]@{ File = $file.Name; Priority = "HIGH"; Reason = "Label conflict"; Timestamp = (Get-Date).ToString("s") }
    }

    if ($UpdateAI -and !$aiCache.ContainsKey($aiKey)) {
        $aiCache[$aiKey] = $label
    }

    $typeFolder = if ($fileTypeMap.ContainsKey($ext)) { $fileTypeMap[$ext] } else { "Misc" }
    $destDir = Join-Path $classifiedRoot "$label\$typeFolder\$dateFolder"
    if (-not (Test-Path $destDir)) { New-Item -ItemType Directory -Path $destDir -Force | Out-Null }

    $newName = if ($PreserveName) { $file.Name } else { "${label}_$timestamp$($file.Extension)" }
    $destPath = Join-Path $destDir $newName

    $classifiedLog += [PSCustomObject]@{ File = $file.Name; NewPath = $destPath; Label = $label }
    $moveLog += [PSCustomObject]@{ File = $file.Name; From = $file.FullName; To = $destPath; Timestamp = (Get-Date).ToString("s") }

    if (-not $DryRun) {
        Move-Item -Path $file.FullName -Destination $destPath -Force
    }
}

# === EXECUTE CLASSIFICATION ===
Write-Host "`n🔍 Scanning F:\ and classifying files..."
Get-ChildItem -Path $root -Recurse -File -ErrorAction SilentlyContinue | Where-Object {
    foreach ($skip in $skipDirs) { if ($_.FullName -like "*\$skip*") { return $false } }
    return $true
} | ForEach-Object {
    try {
        Classify-And-Move $_
    } catch {
        Write-Warning "⚠️ Failed to process $($_.FullName)"
    }
}

# === WRITE OUTPUT LOGS ===
$aiCache.GetEnumerator() | ForEach-Object {
    [PSCustomObject]@{
        fileName = ($_.Key -split '\|')[0]
        extension = ($_.Key -split '\|')[1]
        label = $_.Value
    }
} | ConvertTo-Json -Depth 5 | Set-Content $aiCachePath
$classifiedLog | ConvertTo-Json -Depth 5 | Set-Content $classifiedLogPath
$moveLog | ConvertTo-Json -Depth 5 | Set-Content $moveLogPath
$reclassificationAudit | ConvertTo-Json -Depth 5 | Set-Content $refinementLogPath
$priorityDashboard | ConvertTo-Json -Depth 5 | Set-Content $priorityAuditPath

Write-Host "`n✅ COMPLETE: All files classified, moved, and logged."
'''

# Save the script
output_path = Path("/mnt/data") / filename
with open(output_path, "w", encoding="utf-8") as f:
    f.write(script_content)

output_path.name
