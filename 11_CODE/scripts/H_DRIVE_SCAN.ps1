# H:\ Drive Comprehensive Scan Script
# Scans for all PDF, TXT, and MD files

$outputDir = "C:\users\andre\LITIGATIONOS_MASTER\OMNI_HARVEST_20260216_0357\00_MANIFESTS"

# Create output directory if it doesn't exist
if (-not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
}

Write-Host "=== H:\ DRIVE COMPREHENSIVE SCAN ===" -ForegroundColor Cyan
Write-Host "Output Directory: $outputDir" -ForegroundColor Yellow
Write-Host "Target: H:\ drive (all PDFs, TXT, MD files)" -ForegroundColor Yellow
Write-Host ""

# Initialize arrays
$allFiles = @()
$scanStats = @{
    PDFs = 0
    TXTs = 0
    MDs = 0
    TotalSize = 0
    Errors = 0
}

# Scan for each file type
Write-Host "Scanning H:\ drive..." -ForegroundColor Green

# PDF Files
Write-Host "`n[1/3] Scanning for PDF files..." -ForegroundColor Cyan
try {
    $pdfFiles = Get-ChildItem -Path "H:\" -Filter "*.pdf" -Recurse -File -ErrorAction SilentlyContinue
    $scanStats.PDFs = $pdfFiles.Count
    Write-Host "  Found: $($pdfFiles.Count) PDF files" -ForegroundColor Green
} catch {
    Write-Host "  Error scanning PDFs: $_" -ForegroundColor Red
    $scanStats.Errors++
    $pdfFiles = @()
}

# TXT Files
Write-Host "`n[2/3] Scanning for TXT files..." -ForegroundColor Cyan
try {
    $txtFiles = Get-ChildItem -Path "H:\" -Filter "*.txt" -Recurse -File -ErrorAction SilentlyContinue
    $scanStats.TXTs = $txtFiles.Count
    Write-Host "  Found: $($txtFiles.Count) TXT files" -ForegroundColor Green
} catch {
    Write-Host "  Error scanning TXTs: $_" -ForegroundColor Red
    $scanStats.Errors++
    $txtFiles = @()
}

# MD Files
Write-Host "`n[3/3] Scanning for MD files..." -ForegroundColor Cyan
try {
    $mdFiles = Get-ChildItem -Path "H:\" -Filter "*.md" -Recurse -File -ErrorAction SilentlyContinue
    $scanStats.MDs = $mdFiles.Count
    Write-Host "  Found: $($mdFiles.Count) MD files" -ForegroundColor Green
} catch {
    Write-Host "  Error scanning MDs: $_" -ForegroundColor Red
    $scanStats.Errors++
    $mdFiles = @()
}

# Combine all files
$allFiles = @($pdfFiles) + @($txtFiles) + @($mdFiles)
$totalFiles = $allFiles.Count
Write-Host "`n=== SCAN COMPLETE ===" -ForegroundColor Cyan
Write-Host "Total files found: $totalFiles" -ForegroundColor Yellow

if ($totalFiles -eq 0) {
    Write-Host "`nNo files found on H:\ drive. Exiting." -ForegroundColor Red
    exit 1
}

# Process files and create structured data
Write-Host "`nProcessing file data..." -ForegroundColor Cyan
$processedData = @()

foreach ($file in $allFiles) {
    $extension = $file.Extension.ToLower().TrimStart('.')
    $sizeKB = [math]::Round($file.Length / 1KB, 2)
    $sizeMB = [math]::Round($file.Length / 1MB, 2)
    
    $scanStats.TotalSize += $file.Length
    
    $processedData += [PSCustomObject]@{
        FilePath = $file.FullName
        FileName = $file.Name
        Extension = $extension
        SizeBytes = $file.Length
        SizeKB = $sizeKB
        SizeMB = $sizeMB
        DateModified = $file.LastWriteTime
        DateCreated = $file.CreationTime
        Directory = $file.DirectoryName
    }
}

# Export 1: Complete Manifest (all files)
Write-Host "`nCreating H_DRIVE_COMPLETE_MANIFEST.csv..." -ForegroundColor Cyan
$processedData | Sort-Object DateModified -Descending | 
    Export-Csv -Path "$outputDir\H_DRIVE_COMPLETE_MANIFEST.csv" -NoTypeInformation
Write-Host "  ✓ Created H_DRIVE_COMPLETE_MANIFEST.csv" -ForegroundColor Green

# Export 2: PDF Manifest
Write-Host "Creating H_DRIVE_PDFS.csv..." -ForegroundColor Cyan
$processedData | Where-Object { $_.Extension -eq 'pdf' } | 
    Sort-Object DateModified -Descending | 
    Export-Csv -Path "$outputDir\H_DRIVE_PDFS.csv" -NoTypeInformation
Write-Host "  ✓ Created H_DRIVE_PDFS.csv ($($scanStats.PDFs) files)" -ForegroundColor Green

# Export 3: TXT Manifest
Write-Host "Creating H_DRIVE_TXT.csv..." -ForegroundColor Cyan
$processedData | Where-Object { $_.Extension -eq 'txt' } | 
    Sort-Object DateModified -Descending | 
    Export-Csv -Path "$outputDir\H_DRIVE_TXT.csv" -NoTypeInformation
Write-Host "  ✓ Created H_DRIVE_TXT.csv ($($scanStats.TXTs) files)" -ForegroundColor Green

# Export 4: MD Manifest
Write-Host "Creating H_DRIVE_MD.csv..." -ForegroundColor Cyan
$processedData | Where-Object { $_.Extension -eq 'md' } | 
    Sort-Object DateModified -Descending | 
    Export-Csv -Path "$outputDir\H_DRIVE_MD.csv" -NoTypeInformation
Write-Host "  ✓ Created H_DRIVE_MD.csv ($($scanStats.MDs) files)" -ForegroundColor Green

# Export 5: Priority Files (Top 100 by size and recency)
Write-Host "`nCreating H_DRIVE_PRIORITY_FILES.csv..." -ForegroundColor Cyan

# Calculate priority score: larger files + more recent = higher priority
$priorityData = $processedData | ForEach-Object {
    $daysOld = (Get-Date) - $_.DateModified
    $recencyScore = [math]::Max(0, 1000 - $daysOld.TotalDays)
    $sizeScore = $_.SizeMB * 10
    
    $_ | Add-Member -NotePropertyName "PriorityScore" -NotePropertyValue ($recencyScore + $sizeScore) -PassThru
    $_ | Add-Member -NotePropertyName "DaysOld" -NotePropertyValue ([math]::Round($daysOld.TotalDays, 0)) -PassThru
}

$priorityData | Sort-Object PriorityScore -Descending | 
    Select-Object -First 100 | 
    Export-Csv -Path "$outputDir\H_DRIVE_PRIORITY_FILES.csv" -NoTypeInformation
Write-Host "  ✓ Created H_DRIVE_PRIORITY_FILES.csv (Top 100 priority files)" -ForegroundColor Green

# Export 6: Summary Report (Markdown)
Write-Host "`nCreating H_DRIVE_SCAN_SUMMARY.md..." -ForegroundColor Cyan

$totalSizeGB = [math]::Round($scanStats.TotalSize / 1GB, 2)
$avgSizeMB = [math]::Round(($scanStats.TotalSize / $totalFiles) / 1MB, 2)

$top10Files = $priorityData | Sort-Object PriorityScore -Descending | Select-Object -First 10

$summaryContent = @"
# H:\ Drive Scan Summary Report
**Generated:** $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

## Scan Overview
- **Target Drive:** H:\
- **File Types Scanned:** PDF, TXT, MD
- **Total Files Found:** $totalFiles
- **Total Size:** $totalSizeGB GB

## File Type Breakdown
| File Type | Count | Percentage |
|-----------|-------|------------|
| PDF       | $($scanStats.PDFs) | $([math]::Round(($scanStats.PDFs / $totalFiles) * 100, 1))% |
| TXT       | $($scanStats.TXTs) | $([math]::Round(($scanStats.TXTs / $totalFiles) * 100, 1))% |
| MD        | $($scanStats.MDs) | $([math]::Round(($scanStats.MDs / $totalFiles) * 100, 1))% |

## Statistics
- **Average File Size:** $avgSizeMB MB
- **Largest File:** $($processedData | Sort-Object SizeBytes -Descending | Select-Object -First 1 | ForEach-Object { "$($_.FileName) ($($_.SizeMB) MB)" })
- **Most Recent File:** $($processedData | Sort-Object DateModified -Descending | Select-Object -First 1 | ForEach-Object { "$($_.FileName) ($(Get-Date $_.DateModified -Format 'yyyy-MM-dd'))" })
- **Oldest File:** $($processedData | Sort-Object DateModified | Select-Object -First 1 | ForEach-Object { "$($_.FileName) ($(Get-Date $_.DateModified -Format 'yyyy-MM-dd'))" })

## Top 10 Priority Files
*Priority based on file size and recency*

| Rank | File Name | Type | Size (MB) | Date Modified | Priority Score |
|------|-----------|------|-----------|---------------|----------------|
"@

$rank = 1
foreach ($file in $top10Files) {
    $summaryContent += "`n| $rank | $($file.FileName) | $($file.Extension.ToUpper()) | $($file.SizeMB) | $(Get-Date $file.DateModified -Format 'yyyy-MM-dd') | $([math]::Round($file.PriorityScore, 0)) |"
    $rank++
}

$summaryContent += @"


## Deliverables Created
1. ✅ **H_DRIVE_PDFS.csv** - All PDF files ($($scanStats.PDFs) files)
2. ✅ **H_DRIVE_TXT.csv** - All TXT files ($($scanStats.TXTs) files)
3. ✅ **H_DRIVE_MD.csv** - All MD files ($($scanStats.MDs) files)
4. ✅ **H_DRIVE_COMPLETE_MANIFEST.csv** - Combined manifest ($totalFiles files)
5. ✅ **H_DRIVE_PRIORITY_FILES.csv** - Top 100 priority files for extraction
6. ✅ **H_DRIVE_SCAN_SUMMARY.md** - This summary report

## Next Steps
1. Review priority files in **H_DRIVE_PRIORITY_FILES.csv**
2. Extract high-priority PDFs and documents
3. Process text files for analysis
4. Archive markdown documentation

## Notes
- All manifests sorted by date modified (most recent first)
- Priority scoring: (1000 - days_old) + (size_MB * 10)
- Files with errors during scan: $($scanStats.Errors)
- Excludes system/hidden files

---
*Scan completed successfully*
"@

$summaryContent | Out-File -FilePath "$outputDir\H_DRIVE_SCAN_SUMMARY.md" -Encoding UTF8
Write-Host "  ✓ Created H_DRIVE_SCAN_SUMMARY.md" -ForegroundColor Green

# Final Summary
Write-Host "`n=== ALL DELIVERABLES CREATED ===" -ForegroundColor Green
Write-Host "Location: $outputDir" -ForegroundColor Yellow
Write-Host ""
Write-Host "Files created:" -ForegroundColor Cyan
Write-Host "  1. H_DRIVE_PDFS.csv" -ForegroundColor White
Write-Host "  2. H_DRIVE_TXT.csv" -ForegroundColor White
Write-Host "  3. H_DRIVE_MD.csv" -ForegroundColor White
Write-Host "  4. H_DRIVE_COMPLETE_MANIFEST.csv" -ForegroundColor White
Write-Host "  5. H_DRIVE_PRIORITY_FILES.csv" -ForegroundColor White
Write-Host "  6. H_DRIVE_SCAN_SUMMARY.md" -ForegroundColor White
Write-Host ""
Write-Host "Scan complete! Total: $totalFiles files ($totalSizeGB GB)" -ForegroundColor Green
