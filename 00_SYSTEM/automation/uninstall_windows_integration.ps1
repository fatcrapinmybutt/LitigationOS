<# 
    LitigationOS Windows Integration UNINSTALLER
    Run: powershell -ExecutionPolicy Bypass -File uninstall_windows_integration.ps1
#>
$ErrorActionPreference = "SilentlyContinue"

Write-Host "Removing LitigationOS context menu entries..." -ForegroundColor Yellow

$paths = @(
    "HKCU:\Software\Classes\Directory\Background\shell",
    "HKCU:\Software\Classes\Directory\shell"
)

$keys = @(
    "LitigationOS_Dedupe", "LitigationOS_Organize",
    "LitigationOS_Ω1_FileForensics", "LitigationOS_Ω2_LegalAudit",
    "LitigationOS_Ω3_EvidenceHarvest", "LitigationOS_Ω4_CitationExtract",
    "LitigationOS_Ω5_HashVerify", "LitigationOS_Ω6_TimelineBuilder",
    "LitigationOS_Ω7_RedactionScan", "LitigationOS_Ω8_ExhibitStamper",
    "LitigationOS_Ω9_ContradictionScan", "LitigationOS_Ω10_CourtPackager"
)

foreach ($basePath in $paths) {
    foreach ($key in $keys) {
        $full = "$basePath\$key"
        if (Test-Path $full) {
            Remove-Item -Path $full -Recurse -Force
            Write-Host "  Removed: $key" -ForegroundColor Green
        }
    }
}

Write-Host "`nRemoving scheduled tasks..." -ForegroundColor Yellow
Unregister-ScheduledTask -TaskName "LitigationOS_DailyMaintenance" -Confirm:$false -ErrorAction SilentlyContinue
Unregister-ScheduledTask -TaskName "LitigationOS_WeeklyDedup" -Confirm:$false -ErrorAction SilentlyContinue
Write-Host "  Removed scheduled tasks" -ForegroundColor Green

Write-Host "`n✅ Uninstall complete." -ForegroundColor Cyan
