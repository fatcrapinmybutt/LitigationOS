# ============================================================
# INSTALL_DEDUP_RIGHT_CLICK.ps1
# ============================================================
# Double-click this file to install a right-click context menu
# option: "Deduplicate This Folder (LitigationOS)"
#
# What it does:
#   - Adds a right-click menu item on folders
#   - Adds a right-click menu item on folder backgrounds
#   - Clicking runs content-based dedup (peeks inside files)
#   - Duplicates are MOVED to I:\DEDUP_ARCHIVE\ (never deleted)
#   - JSON report saved to 00_SYSTEM\backups\dedup_reports\
#
# To UNINSTALL, run with: -Uninstall flag
#   powershell -ExecutionPolicy Bypass -File INSTALL_DEDUP_RIGHT_CLICK.ps1 -Uninstall
# ============================================================

param(
    [switch]$Uninstall
)

# Require elevation
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Yellow
    Write-Host "  ELEVATING TO ADMINISTRATOR..." -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "This script modifies the Windows Registry to add a right-click menu."
    Write-Host "It requires Administrator privileges. Relaunching elevated..."
    Write-Host ""

    $scriptPath = $MyInvocation.MyCommand.Path
    if ($Uninstall) {
        Start-Process powershell -Verb RunAs -ArgumentList "-ExecutionPolicy Bypass -File `"$scriptPath`" -Uninstall"
    } else {
        Start-Process powershell -Verb RunAs -ArgumentList "-ExecutionPolicy Bypass -File `"$scriptPath`""
    }
    exit
}

# === CONFIGURATION ===
$PYTHON_EXE = "python"
$DEDUP_SCRIPT = "C:\Users\andre\LitigationOS\00_SYSTEM\dedup_folder.py"
$ICON_TEXT = "🔍 Deduplicate Folder (LitigationOS)"
$ICON_TEXT_BG = "🔍 Deduplicate This Folder (LitigationOS)"
$ICON_TEXT_DRY = "📋 Dedup Preview (Dry Run)"

# Registry paths (HKCU so no admin needed for the keys themselves, but we use HKCR for broader compatibility)
$REG_FOLDER = "Registry::HKEY_CLASSES_ROOT\Directory\shell\LitigationOS_Dedup"
$REG_FOLDER_CMD = "$REG_FOLDER\command"
$REG_FOLDER_DRY = "Registry::HKEY_CLASSES_ROOT\Directory\shell\LitigationOS_DedupDry"
$REG_FOLDER_DRY_CMD = "$REG_FOLDER_DRY\command"
$REG_BG = "Registry::HKEY_CLASSES_ROOT\Directory\Background\shell\LitigationOS_Dedup"
$REG_BG_CMD = "$REG_BG\command"

# === UNINSTALL ===
if ($Uninstall) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  UNINSTALLING DEDUP CONTEXT MENU" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""

    $removed = 0
    foreach ($key in @($REG_FOLDER, $REG_FOLDER_DRY, $REG_BG)) {
        if (Test-Path $key) {
            Remove-Item -Path $key -Recurse -Force
            Write-Host "  REMOVED: $key" -ForegroundColor Green
            $removed++
        } else {
            Write-Host "  NOT FOUND: $key" -ForegroundColor DarkGray
        }
    }

    Write-Host ""
    if ($removed -gt 0) {
        Write-Host "  Uninstall complete. $removed registry keys removed." -ForegroundColor Green
    } else {
        Write-Host "  Nothing to uninstall." -ForegroundColor Yellow
    }
    Write-Host ""
    Write-Host "Press any key to close..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit
}

# === INSTALL ===
Write-Host ""
Write-Host "========================================================" -ForegroundColor Green
Write-Host "  LITIGATIONOS FOLDER DEDUPLICATOR — CONTEXT MENU INSTALL" -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  This will add right-click options to all folders:" -ForegroundColor White
Write-Host "    1. 'Deduplicate Folder' — runs content-based dedup" -ForegroundColor Cyan
Write-Host "    2. 'Dedup Preview (Dry Run)' — shows what WOULD happen" -ForegroundColor Cyan
Write-Host "    3. Background right-click — dedup current folder" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Duplicates go to: I:\DEDUP_ARCHIVE\" -ForegroundColor Yellow
Write-Host "  Reports go to: 00_SYSTEM\backups\dedup_reports\" -ForegroundColor Yellow
Write-Host "  Script: $DEDUP_SCRIPT" -ForegroundColor DarkGray
Write-Host ""

# Verify dedup script exists
if (-not (Test-Path $DEDUP_SCRIPT)) {
    Write-Host "  ERROR: Dedup script not found at $DEDUP_SCRIPT" -ForegroundColor Red
    Write-Host "  Press any key to close..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

# Verify Python is available
try {
    $pyVer = & $PYTHON_EXE --version 2>&1
    Write-Host "  Python: $pyVer" -ForegroundColor DarkGray
} catch {
    Write-Host "  ERROR: Python not found. Install Python 3.10+ first." -ForegroundColor Red
    Write-Host "  Press any key to close..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

# Verify I: drive
if (-not (Test-Path "I:\")) {
    Write-Host "  WARNING: I:\ drive not found. Duplicates will fail to move." -ForegroundColor Yellow
    Write-Host "  Continuing anyway — you can mount I: later." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "  Installing registry keys..." -ForegroundColor White

# === 1. Right-click on a FOLDER → Deduplicate ===
New-Item -Path $REG_FOLDER -Force | Out-Null
Set-ItemProperty -Path $REG_FOLDER -Name "(Default)" -Value $ICON_TEXT
Set-ItemProperty -Path $REG_FOLDER -Name "Icon" -Value "shell32.dll,22"
Set-ItemProperty -Path $REG_FOLDER -Name "Position" -Value "Bottom"

New-Item -Path $REG_FOLDER_CMD -Force | Out-Null
$cmd = "powershell.exe -ExecutionPolicy Bypass -NoProfile -Command `"& {Start-Process powershell -ArgumentList '-ExecutionPolicy Bypass -NoProfile -Command `"cd C:\Users\andre\LitigationOS; python 00_SYSTEM\dedup_folder.py \`\"%V\`\"; Write-Host \`\"\`\"; Write-Host \`\"Press any key to close...\`\"; `$null = `$Host.UI.RawUI.ReadKey(\`\"NoEcho,IncludeKeyDown\`\")`"' -Verb RunAs}`""
Set-ItemProperty -Path $REG_FOLDER_CMD -Name "(Default)" -Value $cmd
Write-Host "    [OK] Folder right-click: Deduplicate" -ForegroundColor Green

# === 2. Right-click on a FOLDER → Dry Run ===
New-Item -Path $REG_FOLDER_DRY -Force | Out-Null
Set-ItemProperty -Path $REG_FOLDER_DRY -Name "(Default)" -Value $ICON_TEXT_DRY
Set-ItemProperty -Path $REG_FOLDER_DRY -Name "Icon" -Value "shell32.dll,23"
Set-ItemProperty -Path $REG_FOLDER_DRY -Name "Position" -Value "Bottom"

New-Item -Path $REG_FOLDER_DRY_CMD -Force | Out-Null
$cmdDry = "powershell.exe -ExecutionPolicy Bypass -NoProfile -Command `"& {Start-Process powershell -ArgumentList '-ExecutionPolicy Bypass -NoProfile -Command `"cd C:\Users\andre\LitigationOS; python 00_SYSTEM\dedup_folder.py \`\"%V\`\" --dry-run; Write-Host \`\"\`\"; Write-Host \`\"Press any key to close...\`\"; `$null = `$Host.UI.RawUI.ReadKey(\`\"NoEcho,IncludeKeyDown\`\")`"' -Verb RunAs}`""
Set-ItemProperty -Path $REG_FOLDER_DRY_CMD -Name "(Default)" -Value $cmdDry
Write-Host "    [OK] Folder right-click: Dry Run Preview" -ForegroundColor Green

# === 3. Right-click on folder BACKGROUND → Deduplicate current folder ===
New-Item -Path $REG_BG -Force | Out-Null
Set-ItemProperty -Path $REG_BG -Name "(Default)" -Value $ICON_TEXT_BG
Set-ItemProperty -Path $REG_BG -Name "Icon" -Value "shell32.dll,22"
Set-ItemProperty -Path $REG_BG -Name "Position" -Value "Bottom"

New-Item -Path $REG_BG_CMD -Force | Out-Null
$cmdBg = "powershell.exe -ExecutionPolicy Bypass -NoProfile -Command `"& {Start-Process powershell -ArgumentList '-ExecutionPolicy Bypass -NoProfile -Command `"cd C:\Users\andre\LitigationOS; python 00_SYSTEM\dedup_folder.py \`\"%V\`\"; Write-Host \`\"\`\"; Write-Host \`\"Press any key to close...\`\"; `$null = `$Host.UI.RawUI.ReadKey(\`\"NoEcho,IncludeKeyDown\`\")`"' -Verb RunAs}`""
Set-ItemProperty -Path $REG_BG_CMD -Name "(Default)" -Value $cmdBg
Write-Host "    [OK] Background right-click: Deduplicate This Folder" -ForegroundColor Green

# === DONE ===
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  INSTALLATION COMPLETE" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Right-click any folder to see:" -ForegroundColor White
Write-Host "    - 'Deduplicate Folder (LitigationOS)'" -ForegroundColor Cyan
Write-Host "    - 'Dedup Preview (Dry Run)'" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Right-click empty space inside a folder to see:" -ForegroundColor White
Write-Host "    - 'Deduplicate This Folder (LitigationOS)'" -ForegroundColor Cyan
Write-Host ""
Write-Host "  To uninstall: run this script with -Uninstall" -ForegroundColor DarkGray
Write-Host ""
Write-Host "Press any key to close..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
