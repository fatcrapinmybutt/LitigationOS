# LitigationOS Dedup â€” Context Menu Wrapper
# Called by Windows Explorer right-click â†’ "Find Duplicates (LitigationOS)"
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
