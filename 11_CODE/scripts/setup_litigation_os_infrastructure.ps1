# LitigationOS Infrastructure Setup Script
# Phase 1: Create folder structure and verify sources

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$logPath = "C:\Users\andre\Desktop\LITIGATION_OS\12-Logs"
$logFile = "$logPath\upscale_start_$timestamp.log"

# Create log directory if it doesn't exist
if (-not (Test-Path $logPath)) {
    $null = New-Item -ItemType Directory -Path $logPath -Force
}

# Start logging
$logContent = @()
$logContent += "=== LITIGATION_OS INFRASTRUCTURE SETUP ==="
$logContent += "Start Time: $(Get-Date)"
$logContent += ""

# Task 1: Check I:\ drive
$logContent += "=== TASK 1: I:\ DRIVE CHECK ==="
$idrivePath = "I:\"
$idriveAccessible = Test-Path -Path $idrivePath
$logContent += "I:\ Drive Accessible: $idriveAccessible"

if (-not $idriveAccessible) {
    $logContent += "WARNING: I:\ drive is NOT accessible. Cannot create target structure."
    $logContent += "Available drives:"
    $drives = Get-PSDrive -PSProvider FileSystem
    foreach ($drive in $drives) {
        $logContent += "  - $($drive.Name): (Provider: FileSystem)"
    }
}

# Task 2: Verify source paths
$logContent += ""
$logContent += "=== TASK 2: SOURCE VERIFICATION ==="
$sources = @(
    @{ Path = "C:\Users\andre\Desktop\LITIGATION_OS"; Name = "LITIGATION_OS Root" },
    @{ Path = "C:\Users\andre\Desktop\LITIGATION_OS\ALL_PC_EVIDENCE_EXTRACTED"; Name = "ALL_PC_EVIDENCE_EXTRACTED" },
    @{ Path = "G:\CAPSTONE"; Name = "G:\CAPSTONE" },
    @{ Path = "F:\"; Name = "F:\ Drive" }
)

foreach ($source in $sources) {
    $exists = Test-Path -Path $source.Path
    $status = if ($exists) { "EXISTS" } else { "MISSING" }
    $logContent += "$($source.Name): $status"
    
    if ($exists) {
        try {
            $itemCount = (Get-ChildItem -Path $source.Path -ErrorAction Stop | Measure-Object).Count
            $logContent += "  - Item count: $itemCount"
        } catch {
            $logContent += "  - Could not count items"
        }
    }
}

# Task 3: Create folder structure if I: drive is accessible
$logContent += ""
$logContent += "=== TASK 3: FOLDER STRUCTURE CREATION ==="

$folders = @(
    "I:\LitigationOS-Ultimate\01-Desktop-Copy\",
    "I:\LitigationOS-Ultimate\02-F-Drive-Archives\",
    "I:\LitigationOS-Ultimate\03-G-Drive-CAPSTONE\",
    "I:\LitigationOS-Ultimate\04-Unified-Evidence\",
    "I:\LitigationOS-Ultimate\05-Unified-Databases\",
    "I:\LitigationOS-Ultimate\06-Unified-AI-Agents\",
    "I:\LitigationOS-Ultimate\07-Master-Index\",
    "I:\LitigationOS-Ultimate\08-Backup-History\",
    "I:\LitigationOS-Ultimate\09-Visualizations\",
    "I:\LitigationOS-Ultimate\10-Documentation\",
    "I:\LitigationOS-Ultimate\11-Scripts\",
    "I:\LitigationOS-Ultimate\12-Logs\"
)

if ($idriveAccessible) {
    foreach ($folder in $folders) {
        try {
            if (-not (Test-Path $folder)) {
                $null = New-Item -ItemType Directory -Path $folder -Force
                $logContent += "Created: $folder"
            } else {
                $logContent += "Already exists: $folder"
            }
        } catch {
            $logContent += "Failed to create: $folder - Error: $($_.Exception.Message)"
        }
    }
} else {
    $logContent += "SKIPPED: I:\ drive not accessible - cannot create folders"
}

# Task 4: File counting for C:\Users\andre\Desktop\LITIGATION_OS
$logContent += ""
$logContent += "=== TASK 4: C:\Users\andre\Desktop\LITIGATION_OS ANALYSIS ==="

$litigationPath = "C:\Users\andre\Desktop\LITIGATION_OS"
try {
    $items = Get-ChildItem -Path $litigationPath -Recurse
    $itemCount = ($items | Measure-Object).Count
    $totalSize = ($items | Measure-Object -Sum -Property Length).Sum
    $sizeMB = $totalSize / 1MB
    $sizeGB = $sizeMB / 1024
    
    $logContent += "Total Items: $itemCount"
    $logContent += "Total Size: $([math]::Round($sizeMB, 2)) MB"
    $logContent += "Total Size: $([math]::Round($sizeGB, 2)) GB"
} catch {
    $logContent += "Error analyzing directory: $($_.Exception.Message)"
}

# Task 5: Summary
$logContent += ""
$logContent += "=== SUMMARY ==="
$logContent += "I:\ Drive Accessible: $idriveAccessible"
$logContent += "C:\Users\andre\Desktop\LITIGATION_OS: EXISTS"
if (Test-Path "C:\Users\andre\Desktop\LITIGATION_OS\ALL_PC_EVIDENCE_EXTRACTED") {
    $logContent += "ALL_PC_EVIDENCE_EXTRACTED: EXISTS"
} else {
    $logContent += "ALL_PC_EVIDENCE_EXTRACTED: MISSING"
}
if (Test-Path "G:\CAPSTONE") {
    $logContent += "G:\CAPSTONE: EXISTS"
} else {
    $logContent += "G:\CAPSTONE: NOT ACCESSIBLE"
}
if (Test-Path "F:\") {
    $logContent += "F:\ Drive: EXISTS"
} else {
    $logContent += "F:\ Drive: NOT ACCESSIBLE"
}

$logContent += ""
$logContent += "End Time: $(Get-Date)"

# Write log file
$logContent | Out-File -FilePath $logFile -Encoding UTF8

# Display results
$logContent | ForEach-Object { Write-Host $_ }

Write-Host ""
Write-Host "Log saved to: $logFile"
