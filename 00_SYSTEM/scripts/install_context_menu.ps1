<#
.SYNOPSIS
    Registers Windows Explorer right-click context menu options for LitigationOS dedup.
.DESCRIPTION
    Adds "Find Duplicates" to the right-click menu for files and folders.
    Uses content_dedup_engine.py --target mode to search all drives.
.NOTES
    Run as Administrator: .\install_context_menu.ps1 -Install
    Remove:              .\install_context_menu.ps1 -Uninstall
#>
param(
    [switch]$Install,
    [switch]$Uninstall
)

$ErrorActionPreference = "Stop"
$PYTHON = "python"
$ENGINE = "C:\Users\andre\LitigationOS\00_SYSTEM\scripts\content_dedup_engine.py"

# Wrapper script that opens a terminal window with results
$WRAPPER = "C:\Users\andre\LitigationOS\00_SYSTEM\scripts\dedup_context_menu.ps1"

# Registry paths
$FILE_KEY = "HKCU:\SOFTWARE\Classes\*\shell\LitOSDedup"
$DIR_KEY  = "HKCU:\SOFTWARE\Classes\Directory\shell\LitOSDedup"

function Install-ContextMenu {
    Write-Host "Installing LitigationOS Dedup context menu..." -ForegroundColor Cyan

    # Create wrapper script
    $wrapperContent = @'
# LitigationOS Dedup — Context Menu Wrapper
# Called by Windows Explorer right-click → "Find Duplicates (LitigationOS)"
param([string]$Target)

$host.UI.RawUI.WindowTitle = "LitigationOS Dedup - Finding Duplicates..."
$host.UI.RawUI.BackgroundColor = "DarkBlue"
$host.UI.RawUI.ForegroundColor = "White"
Clear-Host

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  LitigationOS Content-Based Deduplication Engine" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Target: $Target" -ForegroundColor Yellow
Write-Host "  Searching all drives (C:, D:, F:, G:, H:, I:)..." -ForegroundColor Gray
Write-Host ""

$engine = "C:\Users\andre\LitigationOS\00_SYSTEM\scripts\content_dedup_engine.py"

try {
    python $engine --target "$Target" 2>&1 | ForEach-Object {
        if ($_ -match 'EXACT') {
            Write-Host $_ -ForegroundColor Red
        } elseif ($_ -match 'SIM:') {
            Write-Host $_ -ForegroundColor Yellow
        } elseif ($_ -match 'No duplicates') {
            Write-Host $_ -ForegroundColor Green
        } else {
            Write-Host $_
        }
    }
} catch {
    Write-Host "ERROR: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Press any key to close..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
'@
    Set-Content -Path $WRAPPER -Value $wrapperContent -Encoding UTF8
    Write-Host "  Created wrapper: $WRAPPER" -ForegroundColor Green

    # Command that opens PowerShell with the wrapper
    $cmdFile = "powershell.exe -ExecutionPolicy Bypass -NoProfile -File `"$WRAPPER`" -Target `"%1`""
    $cmdDir  = "powershell.exe -ExecutionPolicy Bypass -NoProfile -File `"$WRAPPER`" -Target `"%V`""

    # Register for files (*)
    if (-not (Test-Path $FILE_KEY)) { New-Item -Path $FILE_KEY -Force | Out-Null }
    Set-ItemProperty -Path $FILE_KEY -Name "(Default)" -Value "Find Duplicates (LitigationOS)"
    Set-ItemProperty -Path $FILE_KEY -Name "Icon" -Value "shell32.dll,14"
    New-Item -Path "$FILE_KEY\command" -Force | Out-Null
    Set-ItemProperty -Path "$FILE_KEY\command" -Name "(Default)" -Value $cmdFile
    Write-Host "  Registered file context menu" -ForegroundColor Green

    # Register for directories
    if (-not (Test-Path $DIR_KEY)) { New-Item -Path $DIR_KEY -Force | Out-Null }
    Set-ItemProperty -Path $DIR_KEY -Name "(Default)" -Value "Find Duplicates (LitigationOS)"
    Set-ItemProperty -Path $DIR_KEY -Name "Icon" -Value "shell32.dll,14"
    New-Item -Path "$DIR_KEY\command" -Force | Out-Null
    Set-ItemProperty -Path "$DIR_KEY\command" -Name "(Default)" -Value $cmdDir
    Write-Host "  Registered directory context menu" -ForegroundColor Green

    Write-Host ""
    Write-Host "SUCCESS: Right-click → 'Find Duplicates (LitigationOS)' is now available!" -ForegroundColor Green
    Write-Host "  Works on files AND folders in Windows Explorer." -ForegroundColor Gray
}

function Uninstall-ContextMenu {
    Write-Host "Removing LitigationOS Dedup context menu..." -ForegroundColor Yellow
    if (Test-Path $FILE_KEY) {
        Remove-Item -Path $FILE_KEY -Recurse -Force
        Write-Host "  Removed file context menu" -ForegroundColor Green
    }
    if (Test-Path $DIR_KEY) {
        Remove-Item -Path $DIR_KEY -Recurse -Force
        Write-Host "  Removed directory context menu" -ForegroundColor Green
    }
    if (Test-Path $WRAPPER) {
        Remove-Item -Path $WRAPPER -Force
        Write-Host "  Removed wrapper script" -ForegroundColor Green
    }
    Write-Host "Context menu uninstalled." -ForegroundColor Green
}

if ($Install) {
    Install-ContextMenu
} elseif ($Uninstall) {
    Uninstall-ContextMenu
} else {
    Write-Host "Usage:"
    Write-Host "  .\install_context_menu.ps1 -Install    # Add right-click dedup option"
    Write-Host "  .\install_context_menu.ps1 -Uninstall  # Remove right-click dedup option"
}
