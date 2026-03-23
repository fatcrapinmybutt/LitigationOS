# COMPREHENSIVE ZIP EXTRACTION SCRIPT FOR JUDICIAL EVIDENCE
# Extracts ALL ZIP files, organizes by category, creates master inventory

$ErrorActionPreference = "Continue"
$Global:ExtractionLog = @()
$Global:FileInventory = @()
$Global:ErrorLog = @()
$Global:ProcessedZips = @{}
$Global:ExtractedFiles = 0

# Target directories
$OutputRoot = "C:\Users\andre\Desktop\ALL_PC_EVIDENCE_EXTRACTED"
$InventoryCSV = "C:\Users\andre\Desktop\FULL_PC_JUDICIAL_ANALYSIS_2026-02-10_010049\01_ZIP_FILES_INVENTORY.csv"

# Category mappings
$CategoryKeywords = @{
    'Court_Documents' = @('court', 'filing', 'docket', 'motion', 'petition', 'complaint', 'answer', 'brief', 'pleading', 'summons')
    'Judicial_Orders' = @('order', 'judgment', 'ruling', 'decision', 'decree', 'signed')
    'Custody_Materials' = @('custody', 'parenting', 'visitation', 'placement', 'timeshare', 'children')
    'ExParte_Documents' = @('exparte', 'ex parte', 'emergency', 'urgent', 'suspension')
    'Discovery_Materials' = @('discovery', 'interrogatory', 'production', 'subpoena', 'deposition', 'request')
    'Transcripts' = @('transcript', 'hearing', 'testimony', 'proceeding', 'record')
    'Communications' = @('email', 'text', 'message', 'correspondence', 'letter', 'communication')
    'Financial_Documents' = @('financial', 'bank', 'tax', 'income', 'expense', 'asset', 'debt', 'child support', 'alimony')
    'Medical_Psychological' = @('medical', 'health', 'psychological', 'psych', 'evaluation', 'assessment', 'therapy', 'healthwest')
    'PPO_Documents' = @('ppo', 'protection', 'restraining', 'injunction')
    'Scanned_Documents' = @('scanned', 'scan')
    'JTC_Documents' = @('jtc', 'juvenile')
}

# Create category directories
foreach ($category in $CategoryKeywords.Keys) {
    $dir = Join-Path $OutputRoot $category
    New-Item -Path $dir -ItemType Directory -Force | Out-Null
}
$UncategorizedDir = Join-Path $OutputRoot "Uncategorized"
New-Item -Path $UncategorizedDir -ItemType Directory -Force | Out-Null

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "COMPREHENSIVE JUDICIAL EVIDENCE EXTRACTION" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Load ZIP inventory
Write-Host "[1/6] Loading ZIP inventory..." -ForegroundColor Yellow
$ZipInventory = Import-Csv $InventoryCSV
$TotalZips = $ZipInventory.Count
Write-Host "Found: $TotalZips ZIP files (Total: $([math]::Round(($ZipInventory | Measure-Object -Property SizeMB -Sum).Sum, 2)) MB)" -ForegroundColor Green

# Sort by size (largest first)
$ZipInventory = $ZipInventory | Sort-Object {[decimal]$_.SizeMB} -Descending

# Function to categorize file
function Get-FileCategory {
    param([string]$FileName)
    
    $FileNameLower = $FileName.ToLower()
    
    foreach ($category in $CategoryKeywords.Keys) {
        foreach ($keyword in $CategoryKeywords[$category]) {
            if ($FileNameLower -contains $keyword -or $FileNameLower -like "*$keyword*") {
                return $category
            }
        }
    }
    return 'Uncategorized'
}

# Function to extract ZIP recursively
function Extract-ZipRecursive {
    param(
        [string]$ZipPath,
        [string]$DestinationBase,
        [int]$Depth = 0,
        [string]$ParentZip = ""
    )
    
    if ($Depth -gt 5) {
        Write-Host "  [WARNING] Max recursion depth reached for: $ZipPath" -ForegroundColor Yellow
        return
    }
    
    # Check if already processed
    if ($Global:ProcessedZips.ContainsKey($ZipPath)) {
        return
    }
    $Global:ProcessedZips[$ZipPath] = $true
    
    if (-not (Test-Path $ZipPath)) {
        $Global:ErrorLog += "[ERROR] ZIP not found: $ZipPath"
        return
    }
    
    try {
        $ZipName = [System.IO.Path]::GetFileNameWithoutExtension($ZipPath)
        $Category = Get-FileCategory -FileName $ZipName
        $CategoryDir = Join-Path $OutputRoot $Category
        
        # Create unique extraction folder
        $ExtractDir = Join-Path $CategoryDir $ZipName
        $Counter = 1
        while (Test-Path $ExtractDir) {
            $ExtractDir = Join-Path $CategoryDir "$ZipName`_$Counter"
            $Counter++
        }
        
        New-Item -Path $ExtractDir -ItemType Directory -Force | Out-Null
        
        # Extract ZIP
        $Indent = "  " * $Depth
        Write-Host "$Indent[EXTRACT] $ZipName => $Category\" -ForegroundColor Cyan
        
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        [System.IO.Compression.ZipFile]::ExtractToDirectory($ZipPath, $ExtractDir)
        
        # Log extraction
        $ZipSize = (Get-Item $ZipPath).Length / 1MB
        $Global:ExtractionLog += [PSCustomObject]@{
            ZipPath = $ZipPath
            ExtractedTo = $ExtractDir
            Category = $Category
            SizeMB = [math]::Round($ZipSize, 2)
            Depth = $Depth
            ParentZip = $ParentZip
            Status = "SUCCESS"
        }
        
        # Process extracted files
        $ExtractedItems = Get-ChildItem -Path $ExtractDir -Recurse
        
        foreach ($item in $ExtractedItems) {
            if (-not $item.PSIsContainer) {
                $Global:ExtractedFiles++
                
                # Add to file inventory
                $Global:FileInventory += [PSCustomObject]@{
                    FullPath = $item.FullName
                    FileName = $item.Name
                    Extension = $item.Extension
                    SizeKB = [math]::Round($item.Length / 1KB, 2)
                    Category = $Category
                    SourceZip = $ZipPath
                    LastWriteTime = $item.LastWriteTime
                }
                
                # Check for nested ZIPs
                if ($item.Extension -eq '.zip') {
                    Write-Host "$Indent  [NESTED] Found ZIP: $($item.Name)" -ForegroundColor Magenta
                    Extract-ZipRecursive -ZipPath $item.FullName -DestinationBase $OutputRoot -Depth ($Depth + 1) -ParentZip $ZipPath
                }
            }
        }
        
    } catch {
        $ErrMsg = $_.Exception.Message
        Write-Host "$Indent[ERROR] Failed to extract $ZipPath`: $ErrMsg" -ForegroundColor Red
        $Global:ErrorLog += "[ERROR] $ZipPath`: $ErrMsg"
        $Global:ExtractionLog += [PSCustomObject]@{
            ZipPath = $ZipPath
            ExtractedTo = ""
            Category = ""
            SizeMB = 0
            Depth = $Depth
            ParentZip = $ParentZip
            Status = "FAILED: $ErrMsg"
        }
    }
}

# Extract all ZIPs
Write-Host ""
Write-Host "[2/6] Extracting ALL ZIP files (prioritized by size)..." -ForegroundColor Yellow
$ProcessedCount = 0

foreach ($zip in $ZipInventory) {
    $ProcessedCount++
    $Percent = [math]::Round(($ProcessedCount / $TotalZips) * 100, 1)
    Write-Host "[$ProcessedCount/$TotalZips - $Percent%] Processing: $($zip.FullName)" -ForegroundColor White
    
    Extract-ZipRecursive -ZipPath $zip.FullName -DestinationBase $OutputRoot
    
    # Progress indicator
    if ($ProcessedCount % 50 -eq 0) {
        Write-Host "  >> $ProcessedCount ZIPs processed, $($Global:ExtractedFiles) files extracted..." -ForegroundColor Gray
    }
}

# Generate category statistics
Write-Host ""
Write-Host "[3/6] Analyzing extracted files by category..." -ForegroundColor Yellow
$CategoryStats = $Global:FileInventory | Group-Object Category | ForEach-Object {
    $TotalSize = ($_.Group | Measure-Object -Property SizeKB -Sum).Sum
    [PSCustomObject]@{
        Category = $_.Name
        FileCount = $_.Count
        TotalSizeMB = [math]::Round($TotalSize / 1024, 2)
    }
} | Sort-Object FileCount -Descending

Write-Host ""
Write-Host "CATEGORY BREAKDOWN:" -ForegroundColor Green
$CategoryStats | Format-Table -AutoSize

# Export master inventory
Write-Host ""
Write-Host "[4/6] Creating master inventory..." -ForegroundColor Yellow
$MasterInventoryPath = Join-Path $OutputRoot "MASTER_EXTRACTION_INVENTORY.csv"
$Global:FileInventory | Export-Csv -Path $MasterInventoryPath -NoTypeInformation
Write-Host "Saved: $MasterInventoryPath" -ForegroundColor Green

# Export extraction log
$ExtractionLogPath = Join-Path $OutputRoot "EXTRACTION_LOG.csv"
$Global:ExtractionLog | Export-Csv -Path $ExtractionLogPath -NoTypeInformation
Write-Host "Saved: $ExtractionLogPath" -ForegroundColor Green

# Create markdown inventory
Write-Host ""
Write-Host "[5/6] Creating MASTER_EXTRACTION_INVENTORY.md..." -ForegroundColor Yellow
$MarkdownPath = Join-Path $OutputRoot "MASTER_EXTRACTION_INVENTORY.md"
$Markdown = @"
# MASTER EXTRACTION INVENTORY - JUDICIAL EVIDENCE
**Generated:** $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

## EXTRACTION SUMMARY
- **Total ZIP Files Processed:** $TotalZips
- **Total Files Extracted:** $($Global:ExtractedFiles)
- **Successful Extractions:** $($Global:ExtractionLog | Where-Object {$_.Status -eq 'SUCCESS'} | Measure-Object | Select-Object -ExpandProperty Count)
- **Failed Extractions:** $($Global:ErrorLog.Count)

## CATEGORY BREAKDOWN

"@

foreach ($stat in $CategoryStats) {
    $Markdown += "### $($stat.Category)`n"
    $Markdown += "- **Files:** $($stat.FileCount)`n"
    $Markdown += "- **Total Size:** $($stat.TotalSizeMB) MB`n`n"
}

$Markdown += @"

## FILE EXTENSIONS FOUND

"@

$ExtensionStats = $Global:FileInventory | Group-Object Extension | Sort-Object Count -Descending | Select-Object -First 20
foreach ($ext in $ExtensionStats) {
    $Markdown += "- **$($ext.Name)**: $($ext.Count) files`n"
}

$Markdown += @"

## TOP 20 LARGEST FILES

| File Name | Size (MB) | Category | Source ZIP |
|-----------|-----------|----------|------------|
"@

$TopFiles = $Global:FileInventory | Sort-Object SizeKB -Descending | Select-Object -First 20
foreach ($file in $TopFiles) {
    $SizeMB = [math]::Round($file.SizeKB / 1024, 2)
    $ShortZip = Split-Path $file.SourceZip -Leaf
    $Markdown += "| $($file.FileName) | $SizeMB | $($file.Category) | $ShortZip |`n"
}

if ($Global:ErrorLog.Count -gt 0) {
    $Markdown += @"

## ERRORS ENCOUNTERED

"@
    foreach ($err in $Global:ErrorLog) {
        $Markdown += "- $err`n"
    }
}

$Markdown | Out-File -FilePath $MarkdownPath -Encoding UTF8
Write-Host "Saved: $MarkdownPath" -ForegroundColor Green

# Create summary text file
Write-Host ""
Write-Host "[6/6] Creating EXTRACTION_SUMMARY.txt..." -ForegroundColor Yellow
$SummaryPath = Join-Path $OutputRoot "EXTRACTION_SUMMARY.txt"
$Summary = @"
========================================
JUDICIAL EVIDENCE EXTRACTION SUMMARY
========================================
Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

EXTRACTION STATISTICS
---------------------
Total ZIP Files Found: $TotalZips
Total ZIP Files Processed: $ProcessedCount
Total Files Extracted: $($Global:ExtractedFiles)
Successful Extractions: $($Global:ExtractionLog | Where-Object {$_.Status -eq 'SUCCESS'} | Measure-Object | Select-Object -ExpandProperty Count)
Failed Extractions: $($Global:ErrorLog.Count)

CATEGORY COUNTS
---------------
"@

foreach ($stat in $CategoryStats) {
    $Summary += "$($stat.Category): $($stat.FileCount) files ($($stat.TotalSizeMB) MB)`n"
}

$Summary += @"

TOP FILE EXTENSIONS
-------------------
"@

foreach ($ext in $ExtensionStats | Select-Object -First 10) {
    $Summary += "$($ext.Name): $($ext.Count) files`n"
}

$Summary += @"

EXTRACTION LOCATION
-------------------
$OutputRoot

INVENTORY FILES
---------------
- MASTER_EXTRACTION_INVENTORY.csv (detailed file list)
- MASTER_EXTRACTION_INVENTORY.md (formatted report)
- EXTRACTION_LOG.csv (extraction operations log)
- EXTRACTION_SUMMARY.txt (this file)

========================================
EXTRACTION COMPLETE
========================================
"@

$Summary | Out-File -FilePath $SummaryPath -Encoding UTF8
Write-Host "Saved: $SummaryPath" -ForegroundColor Green

# Display final summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "EXTRACTION COMPLETE" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Total ZIPs Processed: $ProcessedCount" -ForegroundColor White
Write-Host "Total Files Extracted: $($Global:ExtractedFiles)" -ForegroundColor White
Write-Host "Output Location: $OutputRoot" -ForegroundColor White
Write-Host ""
Write-Host "Review MASTER_EXTRACTION_INVENTORY.md for complete details" -ForegroundColor Green
