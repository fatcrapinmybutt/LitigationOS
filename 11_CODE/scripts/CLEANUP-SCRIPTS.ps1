# LitigationOS File Cleanup & Organization Scripts
# PowerShell script suite for maintaining clean project structure
# Run as Administrator

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ===================================================================
# CONFIGURATION
# ===================================================================

$ProjectRoot = "C:\Projects\LitigationOS"
$BackupPath = "D:\LitigationOS_Backups"
$LogPath = Join-Path $ProjectRoot "logs"
$ReportPath = Join-Path $ProjectRoot "reports"

# Create log and report directories
@($LogPath, $ReportPath) | ForEach-Object {
    if (-not (Test-Path $_)) {
        New-Item -ItemType Directory -Path $_ -Force | Out-Null
    }
}

# ===================================================================
# UTILITY FUNCTIONS
# ===================================================================

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$Level] $Message"
    
    Write-Host $logMessage
    
    $logFile = Join-Path $LogPath "cleanup-$(Get-Date -Format 'yyyy-MM').log"
    Add-Content -Path $logFile -Value $logMessage
}

function Get-DirectorySize {
    param([string]$Path)
    
    if (-not (Test-Path $Path)) {
        return 0
    }
    
    try {
        $size = (Get-ChildItem -Path $Path -Recurse -ErrorAction SilentlyContinue | 
                 Measure-Object -Property Length -Sum).Sum
        return [math]::Round(($size / 1MB), 2)
    }
    catch {
        return 0
    }
}

function Get-DirectoryFileCount {
    param([string]$Path)
    
    if (-not (Test-Path $Path)) {
        return 0
    }
    
    try {
        return (Get-ChildItem -Path $Path -Recurse -ErrorAction SilentlyContinue | Measure-Object).Count
    }
    catch {
        return 0
    }
}

# ===================================================================
# DUPLICATE DETECTION
# ===================================================================

function Find-DuplicateFiles {
    <#
    .SYNOPSIS
    Find duplicate files by hash comparison
    
    .PARAMETER Path
    Root directory to scan
    
    .PARAMETER OutputReport
    File to save duplicate report
    #>
    
    param(
        [string]$Path = $ProjectRoot,
        [string]$OutputReport = (Join-Path $ReportPath "duplicates-$(Get-Date -Format 'yyyyMMdd').txt")
    )
    
    Write-Log "Starting duplicate file detection in: $Path"
    
    $fileHashes = @{}
    $duplicates = @{}
    
    Get-ChildItem -Path $Path -Recurse -File -ErrorAction SilentlyContinue | 
        Where-Object { $_.FullName -notmatch '\\\.git\\' -and $_.FullName -notmatch '\\node_modules\\' } |
        ForEach-Object {
            try {
                $hash = (Get-FileHash -Path $_.FullName -Algorithm MD5 -ErrorAction SilentlyContinue).Hash
                
                if ($hash) {
                    if ($fileHashes.ContainsKey($hash)) {
                        $fileHashes[$hash] += @($_.FullName)
                    }
                    else {
                        $fileHashes[$hash] = @($_.FullName)
                    }
                }
            }
            catch {
                # Skip files that can't be hashed
            }
        }
    
    # Extract duplicates
    $duplicates = $fileHashes.GetEnumerator() | Where-Object { $_.Value.Count -gt 1 }
    
    # Generate report
    $report = @"
Duplicate Files Report
Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
Search Path: $Path

========================================

"@
    
    if ($duplicates.Count -eq 0) {
        $report += "✓ No duplicate files found`n"
        Write-Log "No duplicate files found"
    }
    else {
        $report += "Found $($duplicates.Count) sets of duplicate files:`n`n"
        
        $duplicates | ForEach-Object {
            $report += "Hash: $($_.Name)`n"
            $report += "Instances: $($_.Value.Count)`n"
            $_.Value | ForEach-Object {
                $size = (Get-Item $_).Length / 1MB
                $report += "  - $_ (${size} MB)`n"
            }
            $report += "`n"
        }
    }
    
    Set-Content -Path $OutputReport -Value $report
    Write-Log "Duplicate report saved to: $OutputReport"
    
    return $duplicates
}

# ===================================================================
# CLEANUP OPERATIONS
# ===================================================================

function Remove-CacheDirectories {
    <#
    .SYNOPSIS
    Remove cache and temporary directories that can be regenerated
    #>
    
    param([string]$Path = $ProjectRoot)
    
    Write-Log "Removing cache directories..."
    
    $cachePatterns = @(
        ".vscode",
        ".idea",
        "node_modules",
        "__pycache__",
        ".pytest_cache",
        ".eslintcache",
        "dist",
        "build",
        ".tox",
        "*.egg-info",
        ".gradle"
    )
    
    $removed = 0
    $totalSize = 0
    
    foreach ($pattern in $cachePatterns) {
        Get-ChildItem -Path $Path -Recurse -Directory -Filter $pattern -ErrorAction SilentlyContinue |
            ForEach-Object {
                $size = Get-DirectorySize $_.FullName
                Write-Host "  Removing: $($_.FullName) (${size} MB)"
                Remove-Item -Path $_.FullName -Recurse -Force -ErrorAction SilentlyContinue
                $removed++
                $totalSize += $size
            }
    }
    
    Write-Log "Removed $removed cache directories (${totalSize} MB freed)"
}

function Remove-OldBackups {
    <#
    .SYNOPSIS
    Remove backup folders older than retention policy
    
    .PARAMETER BackupPath
    Path containing backup folders
    
    .PARAMETER DaysToRetain
    Keep backups younger than this many days
    #>
    
    param(
        [string]$BackupPath = $BackupPath,
        [int]$DaysToRetain = 21
    )
    
    Write-Log "Removing backups older than $DaysToRetain days..."
    
    if (-not (Test-Path $BackupPath)) {
        Write-Log "Backup path not found: $BackupPath" "WARN"
        return
    }
    
    $cutoffDate = (Get-Date).AddDays(-$DaysToRetain)
    $removed = 0
    $totalSize = 0
    
    Get-ChildItem -Path $BackupPath -Directory | 
        Where-Object { $_.LastWriteTime -lt $cutoffDate } |
        ForEach-Object {
            $size = Get-DirectorySize $_.FullName
            Write-Host "  Removing: $($_.Name) (${size} MB, last modified: $($_.LastWriteTime))"
            Remove-Item -Path $_.FullName -Recurse -Force -ErrorAction SilentlyContinue
            $removed++
            $totalSize += $size
        }
    
    Write-Log "Removed $removed old backups (${totalSize} MB freed)"
}

function Remove-TemporaryFiles {
    <#
    .SYNOPSIS
    Remove temporary and lock files
    #>
    
    param([string]$Path = $ProjectRoot)
    
    Write-Log "Removing temporary files..."
    
    $tempPatterns = @(
        "*.tmp",
        "*.temp",
        "*.lock",
        "*.swp",
        "*.swo",
        "*~",
        "Thumbs.db",
        ".DS_Store"
    )
    
    $removed = 0
    $totalSize = 0
    
    foreach ($pattern in $tempPatterns) {
        Get-ChildItem -Path $Path -Recurse -File -Filter $pattern -ErrorAction SilentlyContinue |
            ForEach-Object {
                $size = $_.Length / 1MB
                Write-Host "  Removing: $($_.FullName)"
                Remove-Item -Path $_.FullName -Force -ErrorAction SilentlyContinue
                $removed++
                $totalSize += $size
            }
    }
    
    Write-Log "Removed $removed temporary files (${totalSize} MB freed)"
}

# ===================================================================
# DIRECTORY ANALYSIS & REPORTING
# ===================================================================

function Generate-StorageReport {
    <#
    .SYNOPSIS
    Generate comprehensive storage analysis report
    #>
    
    param([string]$OutputFile = (Join-Path $ReportPath "storage-$(Get-Date -Format 'yyyyMMdd').txt"))
    
    Write-Log "Generating storage report..."
    
    $report = @"
LitigationOS Storage Analysis Report
Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')

========================================
DIRECTORY STRUCTURE
========================================

"@
    
    if (Test-Path $ProjectRoot) {
        Get-ChildItem -Path $ProjectRoot -Directory | Sort-Object Name | ForEach-Object {
            $size = Get-DirectorySize $_.FullName
            $fileCount = Get-DirectoryFileCount $_.FullName
            $report += "$($_.Name)/: ${size} MB ($fileCount files)`n"
        }
    }
    
    $report += @"

========================================
DRIVE SPACE ANALYSIS
========================================

"@
    
    @("C:", "D:", "E:", "F:", "G:", "H:") | ForEach-Object {
        if (Test-Path $_) {
            try {
                $volume = Get-Volume -DriveLetter $_[0] -ErrorAction SilentlyContinue
                if ($volume) {
                    $used = [math]::Round(($volume.Size - $volume.SizeRemaining) / 1GB, 2)
                    $free = [math]::Round(($volume.SizeRemaining / 1GB), 2)
                    $total = [math]::Round(($volume.Size / 1GB), 2)
                    $report += "$_  Used: ${used} GB  Free: ${free} GB  Total: ${total} GB`n"
                }
            }
            catch {
                # Skip drives that can't be queried
            }
        }
    }
    
    $report += @"

========================================
CLEANUP RECOMMENDATIONS
========================================

1. Cache directories (.vscode, node_modules, __pycache__)
   Size: [Run Remove-CacheDirectories to see]
   Recommendation: Remove if builds regenerate them

2. Old backups (> 21 days old)
   Recommendation: Remove per retention policy

3. Temporary files (*.tmp, *.lock, *.swp)
   Recommendation: Always remove safe

4. Duplicate files
   Recommendation: See duplicates report

"@
    
    Set-Content -Path $OutputFile -Value $report
    Write-Log "Storage report saved to: $OutputFile"
}

function Analyze-DirectoryStructure {
    <#
    .SYNOPSIS
    Verify project directory structure is correct
    #>
    
    Write-Log "Analyzing directory structure..."
    
    $expectedDirs = @(
        "source",
        "data",
        "docs",
        "infra",
        "tests",
        "archive",
        "logs",
        "reports"
    )
    
    $issues = @()
    
    foreach ($dir in $expectedDirs) {
        $path = Join-Path $ProjectRoot $dir
        if (-not (Test-Path $path)) {
            Write-Log "Missing directory: $path" "WARN"
            $issues += "Missing: $dir"
        }
    }
    
    # Check for unexpected root directories (likely scattered files)
    $unexpected = Get-ChildItem -Path $ProjectRoot -Directory -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -notin $expectedDirs }
    
    if ($unexpected) {
        Write-Log "Found unexpected directories: $($unexpected -join ', ')" "WARN"
        $issues += "Unexpected directories found"
    }
    
    if ($issues.Count -eq 0) {
        Write-Log "✓ Directory structure is correct"
        return $true
    }
    else {
        Write-Log "✗ Directory structure issues found:" "ERROR"
        $issues | ForEach-Object { Write-Log "  - $_" "ERROR" }
        return $false
    }
}

# ===================================================================
# MAIN CLEANUP ROUTINES
# ===================================================================

function Invoke-WeeklyCleanup {
    <#
    .SYNOPSIS
    Run weekly cleanup routine
    #>
    
    Write-Log "Starting WEEKLY cleanup routine"
    Write-Host "`n=== WEEKLY CLEANUP ===" -ForegroundColor Cyan
    
    Remove-CacheDirectories
    Remove-TemporaryFiles
    Generate-StorageReport
    Analyze-DirectoryStructure
    
    Write-Log "WEEKLY cleanup complete"
    Write-Host "`n✓ Weekly cleanup complete`n" -ForegroundColor Green
}

function Invoke-MonthlyCleanup {
    <#
    .SYNOPSIS
    Run monthly cleanup routine
    #>
    
    Write-Log "Starting MONTHLY cleanup routine"
    Write-Host "`n=== MONTHLY CLEANUP ===" -ForegroundColor Cyan
    
    # Weekly tasks
    Remove-CacheDirectories
    Remove-TemporaryFiles
    
    # Monthly tasks
    Remove-OldBackups
    Find-DuplicateFiles
    Generate-StorageReport
    
    Write-Log "MONTHLY cleanup complete"
    Write-Host "`n✓ Monthly cleanup complete`n" -ForegroundColor Green
}

function Invoke-QuarterlyCleanup {
    <#
    .SYNOPSIS
    Run quarterly cleanup routine
    #>
    
    Write-Log "Starting QUARTERLY cleanup routine"
    Write-Host "`n=== QUARTERLY CLEANUP ===" -ForegroundColor Cyan
    
    # Monthly tasks
    Remove-CacheDirectories
    Remove-TemporaryFiles
    Remove-OldBackups
    Find-DuplicateFiles
    
    # Quarterly tasks
    Write-Log "Quarterly comprehensive analysis" "INFO"
    Generate-StorageReport
    Analyze-DirectoryStructure
    
    Write-Log "QUARTERLY cleanup complete"
    Write-Host "`n✓ Quarterly cleanup complete`n" -ForegroundColor Green
}

# ===================================================================
# SCRIPT ENTRY POINT
# ===================================================================

if ($PSBoundParameters.Count -eq 0) {
    # Show menu if no parameters
    Write-Host "`nLitigationOS Cleanup Scripts" -ForegroundColor Cyan
    Write-Host "==============================`n"
    Write-Host "Usage:"
    Write-Host "  .\CLEANUP-SCRIPTS.ps1 -WeeklyCleanup"
    Write-Host "  .\CLEANUP-SCRIPTS.ps1 -MonthlyCleanup"
    Write-Host "  .\CLEANUP-SCRIPTS.ps1 -QuarterlyCleanup"
    Write-Host "  .\CLEANUP-SCRIPTS.ps1 -FindDuplicates"
    Write-Host "  .\CLEANUP-SCRIPTS.ps1 -GenerateReport"
    Write-Host "  .\CLEANUP-SCRIPTS.ps1 -AnalyzeStructure"
    Write-Host ""
    Write-Host "Or call functions directly in PowerShell."
    Write-Host ""
}

# Make functions available
Write-Host "Functions loaded. Available commands:" -ForegroundColor Green
Write-Host "  Invoke-WeeklyCleanup"
Write-Host "  Invoke-MonthlyCleanup"
Write-Host "  Invoke-QuarterlyCleanup"
Write-Host "  Find-DuplicateFiles"
Write-Host "  Generate-StorageReport"
Write-Host "  Analyze-DirectoryStructure"
Write-Host ""
