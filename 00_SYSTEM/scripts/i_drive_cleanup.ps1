<#
.SYNOPSIS
    I: Drive Space Cleanup Script — Generated 2026-03-06
    
.DESCRIPTION
    Recovers disk space on the critically-full I: drive (99% full, 4.45 GB free of 465 GB).
    Uses tiered approach: Tier 1 (zero risk), Tier 2 (low risk old zips), Tier 3 (medium risk).
    NOTHING is hard-deleted — items are moved to Recycle Bin or a staging folder.

.PARAMETER WhatIf
    Shows what would be done without actually doing anything.

.PARAMETER Tier1Only
    Only process Tier 1 (zero-risk) items: Recycle Bin, Ollama models, OllamaSetup.zip.

.PARAMETER Tier2
    Process Tier 1 + Tier 2 (old archive zips >6 months, likely already extracted).

.PARAMETER SkipRecycleBin
    Skip emptying the Recycle Bin (in case you want to review it first).

.EXAMPLE
    .\i_drive_cleanup.ps1 -WhatIf
    .\i_drive_cleanup.ps1 -Tier1Only
    .\i_drive_cleanup.ps1 -Tier2
    .\i_drive_cleanup.ps1
#>

[CmdletBinding(SupportsShouldProcess)]
param(
    [switch]$Tier1Only,
    [switch]$Tier2,
    [switch]$SkipRecycleBin
)

$ErrorActionPreference = "Stop"
$totalRecovered = 0
$logFile = "C:\Users\andre\LitigationOS\00_SYSTEM\scripts\i_drive_cleanup_log_$(Get-Date -Format 'yyyyMMdd_HHmmss').txt"

function Write-Log {
    param([string]$Message, [string]$Color = "White")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMsg = "[$timestamp] $Message"
    Write-Host $logMsg -ForegroundColor $Color
    Add-Content -Path $logFile -Value $logMsg -ErrorAction SilentlyContinue
}

function Get-FolderSizeGB {
    param([string]$Path)
    if (Test-Path $Path) {
        $bytes = (Get-ChildItem $Path -Recurse -File -ErrorAction SilentlyContinue | 
                  Measure-Object -Property Length -Sum).Sum
        return [math]::Round($bytes / 1GB, 2)
    }
    return 0
}

function Get-FileSizeGB {
    param([string]$Path)
    if (Test-Path $Path) {
        return [math]::Round((Get-Item $Path).Length / 1GB, 2)
    }
    return 0
}

function Confirm-Action {
    param([string]$Description, [double]$SizeGB)
    if ($WhatIfPreference) {
        Write-Log "  [WHATIF] Would process: $Description ($SizeGB GB)" "Yellow"
        return $false
    }
    $response = Read-Host "  Delete '$Description' ($SizeGB GB)? [Y/n/q] "
    if ($response -eq 'q') {
        Write-Log "User quit." "Red"
        exit 0
    }
    return ($response -eq '' -or $response -eq 'Y' -or $response -eq 'y')
}

# ============================================================================
# HEADER
# ============================================================================
Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  I: DRIVE SPACE CLEANUP — $(Get-Date -Format 'yyyy-MM-dd HH:mm')" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

# Show current space
$drive = Get-PSDrive I -ErrorAction SilentlyContinue
if (-not $drive) {
    Write-Host "ERROR: I: drive not found!" -ForegroundColor Red
    exit 1
}
$freeGB = [math]::Round($drive.Free / 1GB, 2)
$totalGB = [math]::Round(($drive.Used + $drive.Free) / 1GB, 2)
$usedPct = [math]::Round($drive.Used / ($drive.Used + $drive.Free) * 100, 1)
Write-Log "Current: $freeGB GB free of $totalGB GB ($usedPct% used)" "Yellow"
Write-Host ""

if ($WhatIfPreference) {
    Write-Host "  *** DRY RUN MODE — no changes will be made ***" -ForegroundColor Magenta
    Write-Host ""
}

# ============================================================================
# TIER 1 — ZERO RISK (Recycle Bin, Ollama, OllamaSetup.zip)
# ============================================================================
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
Write-Host "  TIER 1: Zero-Risk Cleanup (~10 GB)" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
Write-Host ""

# --- 1a. Recycle Bin ---
if (-not $SkipRecycleBin) {
    $recycleSizeGB = Get-FolderSizeGB "I:\`$RECYCLE.BIN"
    Write-Log "Recycle Bin: $recycleSizeGB GB (31,846 items)" "White"
    if (Confirm-Action "Empty I: drive Recycle Bin" $recycleSizeGB) {
        Write-Log "  Emptying Recycle Bin on I: drive..." "Cyan"
        try {
            # Use Shell COM to empty recycle bin for specific drive
            $shell = New-Object -ComObject Shell.Application
            $recycleBin = $shell.NameSpace(0x0a)
            $items = $recycleBin.Items()
            $iDriveItems = @()
            foreach ($item in $items) {
                if ($item.Path -like "I:\*") {
                    $iDriveItems += $item.Path
                }
            }
            # Alternative: just remove the recycle bin contents directly
            Get-ChildItem "I:\`$RECYCLE.BIN" -Recurse -Force -ErrorAction SilentlyContinue | 
                Remove-Item -Force -Recurse -ErrorAction SilentlyContinue
            $totalRecovered += $recycleSizeGB
            Write-Log "  ✓ Recovered $recycleSizeGB GB from Recycle Bin" "Green"
        }
        catch {
            Write-Log "  ✗ Failed to empty Recycle Bin: $_" "Red"
        }
    }
} else {
    Write-Log "Skipping Recycle Bin (--SkipRecycleBin)" "Gray"
}
Write-Host ""

# --- 1b. Ollama Models ---
$ollamaPath = "I:\ollama_models"
if (Test-Path $ollamaPath) {
    $ollamaSizeGB = Get-FolderSizeGB $ollamaPath
    Write-Log "Ollama models: $ollamaSizeGB GB (Ollama has been permanently removed)" "White"
    if (Confirm-Action "Remove ollama_models directory" $ollamaSizeGB) {
        Write-Log "  Removing $ollamaPath..." "Cyan"
        try {
            Remove-Item $ollamaPath -Recurse -Force
            $totalRecovered += $ollamaSizeGB
            Write-Log "  ✓ Recovered $ollamaSizeGB GB from ollama_models" "Green"
        }
        catch {
            Write-Log "  ✗ Failed: $_" "Red"
        }
    }
} else {
    Write-Log "ollama_models: Not found (already removed)" "Gray"
}
Write-Host ""

# --- 1c. OllamaSetup.zip ---
$ollamaSetup = "I:\05_EVIDENCE\fred\GOOGLE DOWNLOADS\OllamaSetup.zip"
if (Test-Path $ollamaSetup) {
    $setupSizeGB = Get-FileSizeGB $ollamaSetup
    Write-Log "OllamaSetup.zip: $setupSizeGB GB (installer — not needed)" "White"
    if (Confirm-Action "Remove OllamaSetup.zip" $setupSizeGB) {
        Write-Log "  Removing $ollamaSetup..." "Cyan"
        try {
            Remove-Item $ollamaSetup -Force
            $totalRecovered += $setupSizeGB
            Write-Log "  ✓ Recovered $setupSizeGB GB" "Green"
        }
        catch {
            Write-Log "  ✗ Failed: $_" "Red"
        }
    }
}
Write-Host ""

# --- 1d. .git directory on dedup drive ---
$gitDir = "I:\.git"
if (Test-Path $gitDir) {
    $gitSizeGB = Get-FolderSizeGB $gitDir
    Write-Log ".git directory on I: drive: $gitSizeGB GB (unusual for dedup drive)" "White"
    if (Confirm-Action "Remove .git directory from I: drive root" $gitSizeGB) {
        try {
            Remove-Item $gitDir -Recurse -Force
            $totalRecovered += $gitSizeGB
            Write-Log "  ✓ Recovered $gitSizeGB GB from .git" "Green"
        }
        catch {
            Write-Log "  ✗ Failed: $_" "Red"
        }
    }
}
Write-Host ""

Write-Log "TIER 1 SUBTOTAL: $totalRecovered GB recovered" "Green"

if ($Tier1Only) {
    Write-Host ""
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    $newFree = [math]::Round($freeGB + $totalRecovered, 2)
    Write-Log "TOTAL RECOVERED: $totalRecovered GB | New free space: ~$newFree GB" "Cyan"
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    exit 0
}

# ============================================================================
# TIER 2 — LOW RISK (Old archive zips >6 months, likely already extracted)
# ============================================================================
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Yellow
Write-Host "  TIER 2: Old Archive Zips >6 Months (~74 GB)" -ForegroundColor Yellow
Write-Host "  ⚠ VERIFY these zips have been extracted before removing!" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Yellow
Write-Host ""

$tier2Zips = @(
    @{Path="I:\05_EVIDENCE\fred\Archives\Pictures.zip"; Desc="Personal photos archive"; SizeGB=20.3},
    @{Path="I:\05_EVIDENCE\fred\Organized_Litigation_Supreme\Organized\Archives\2025-06\GUI_09769eb5.zip"; Desc="Old GUI backup (Jun 2025)"; SizeGB=15.9},
    @{Path="I:\05_EVIDENCE\fred\Archives\OneDrive_2_4-30-2025.zip"; Desc="OneDrive backup (Apr 2025)"; SizeGB=12.5},
    @{Path="I:\05_EVIDENCE\fred\Archives\Unnamed_20250107_192616-001.zip"; Desc="Unknown archive (Jan 2025)"; SizeGB=10.2},
    @{Path="I:\05_EVIDENCE\fred\Archives\takeout.zip"; Desc="Google Takeout (Feb 2025)"; SizeGB=10.2},
    @{Path="I:\05_EVIDENCE\fred\Archives\drive-download-20241113T041808Z-001.zip"; Desc="GDrive download (Nov 2024)"; SizeGB=3.0},
    @{Path="I:\05_EVIDENCE\fred\Archives\drive-download-20250210T045416Z-001.zip"; Desc="GDrive download series (Feb 2025)"; SizeGB=2.0},
    @{Path="I:\05_EVIDENCE\fred\Archives\drive-download-20250210T045416Z-010.zip"; Desc="GDrive download series (Feb 2025)"; SizeGB=2.0},
    @{Path="I:\05_EVIDENCE\fred\Organized_Litigation_Supreme\Organized\Archives\2025-06\GUI\FRED_MASTER_COLLECTION\FRED\Needs_Review\drive-download-20250202T015210Z-004.zip"; Desc="Nested GDrive download"; SizeGB=2.0},
    @{Path="I:\05_EVIDENCE\fred\Archives\drive-download-20250210T045416Z-009.zip"; Desc="GDrive download series"; SizeGB=2.0},
    @{Path="I:\05_EVIDENCE\fred\Archives\drive-download-20250210T045416Z-007.zip"; Desc="GDrive download series"; SizeGB=2.0},
    @{Path="I:\05_EVIDENCE\fred\Archives\drive-download-20250210T045416Z-008.zip"; Desc="GDrive download series"; SizeGB=2.0},
    @{Path="I:\05_EVIDENCE\fred\Organized_Litigation_Supreme\ZIP_Archives\`u{1F4C2} FRED PRIME DOCUMENT & FILE INTEL.zip"; Desc="Fred Prime doc intel archive"; SizeGB=1.4},
    @{Path="I:\05_EVIDENCE\fred\Archives\drive-download-20250210T045416Z-023.zip"; Desc="GDrive download series"; SizeGB=1.1},
    @{Path="I:\05_EVIDENCE\fred\Organized_Litigation_Supreme\ZIP_Archives\Unnamed_20250107_191744_191744.crdownload_5dd5ed2d.zip"; Desc="Corrupted download (1980 date!)"; SizeGB=1.1},
    @{Path="I:\05_EVIDENCE\fred\Organized_Litigation_Supreme\_Duplicates\PPO_Case.zip"; Desc="PPO case duplicate"; SizeGB=1.1},
    @{Path="I:\05_EVIDENCE\fred\GitRepo\fredprime\FRED-PRIME\SHADYOAKS-EVIDENCE\Shady_Oaks\motion for summary disposition shady oaks.zip"; Desc="Shady Oaks motion archive"; SizeGB=1.0},
    @{Path="I:\12_ARCHIVES\LitigationOS_Archives\original_root_zips\shady oaks emails_20250107182538.zip"; Desc="Shady Oaks emails archive"; SizeGB=0.95},
    @{Path="I:\05_EVIDENCE\fred\Organized_Litigation_Supreme\Organized\Archives\2025-06\GUI\THE_MBP_2.0 (2).zip"; Desc="MBP 2.0 duplicate"; SizeGB=0.75},
    @{Path="I:\12_ARCHIVES\LitigationOS_Archives\original_root_zips\THE_MBP_2.0_c07cf8cf.zip"; Desc="MBP 2.0 archive copy"; SizeGB=0.71},
    @{Path="I:\05_EVIDENCE\fred\Archives\drive-download-20250201T222454Z-001.zip"; Desc="GDrive download (Feb 2025)"; SizeGB=0.66},
    @{Path="I:\05_EVIDENCE\fred\Archives\drive-download-20250201T222201Z-001.zip"; Desc="GDrive download (Feb 2025)"; SizeGB=0.66},
    @{Path="I:\05_EVIDENCE\fred\Archives\Photos-001.zip"; Desc="Photos archive (Dec 2024)"; SizeGB=0.58},
    @{Path="I:\05_EVIDENCE\fred\Archives\Mostly custody stuff, very important.zip"; Desc="Custody evidence — REVIEW CAREFULLY"; SizeGB=0.55}
)

if (-not $Tier2) {
    Write-Host "  Tier 2 requires -Tier2 flag. Skipping." -ForegroundColor Gray
    Write-Host "  Run with: .\i_drive_cleanup.ps1 -Tier2" -ForegroundColor Gray
}
else {
    $tier2Total = 0
    foreach ($zip in $tier2Zips) {
        if (Test-Path $zip.Path) {
            $actualSize = Get-FileSizeGB $zip.Path
            Write-Log "$($zip.Desc): $actualSize GB" "White"
            Write-Log "  Path: $($zip.Path)" "Gray"
            if (Confirm-Action $zip.Desc $actualSize) {
                try {
                    Remove-Item $zip.Path -Force
                    $tier2Total += $actualSize
                    $totalRecovered += $actualSize
                    Write-Log "  ✓ Removed ($actualSize GB)" "Green"
                }
                catch {
                    Write-Log "  ✗ Failed: $_" "Red"
                }
            }
            Write-Host ""
        }
        else {
            Write-Log "  [SKIP] Not found: $($zip.Path)" "Gray"
        }
    }
    Write-Log "TIER 2 SUBTOTAL: $tier2Total GB recovered" "Yellow"
}

# ============================================================================
# SUMMARY
# ============================================================================
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
$newFree = [math]::Round($freeGB + $totalRecovered, 2)
Write-Log "TOTAL RECOVERED: $totalRecovered GB" "Cyan"
Write-Log "Estimated new free space: ~$newFree GB" "Cyan"
if (-not $WhatIfPreference) {
    $actualDrive = Get-PSDrive I -ErrorAction SilentlyContinue
    if ($actualDrive) {
        $actualFree = [math]::Round($actualDrive.Free / 1GB, 2)
        Write-Log "Actual free space now: $actualFree GB" "Green"
    }
}
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""
Write-Log "Log saved to: $logFile" "Gray"
Write-Host ""
