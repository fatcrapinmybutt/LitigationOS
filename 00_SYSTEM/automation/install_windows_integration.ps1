<# 
    LitigationOS Windows Integration Installer
    ============================================
    Run as Administrator: 
      powershell -ExecutionPolicy Bypass -File install_windows_integration.ps1
    
    Installs:
    1. Right-click context menu: "LitigationOS Dedupe" (folders)
    2. Right-click context menu: "Organize by File Type" (folders)
    3. 10 OMEGA-ELITE context menu tools (folders)
    4. Scheduled task: Daily drive maintenance at 3:00 AM
    5. Scheduled task: Weekly deep dedup at Sunday 4:00 AM
#>

$ErrorActionPreference = "Stop"
$PYTHON = "python"
$AUTOMATION_DIR = "C:\Users\andre\LitigationOS\00_SYSTEM\automation"

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  LitigationOS Windows Integration Installer" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# ── 1. RIGHT-CLICK CONTEXT MENU (Directory Background) ──────────────────────
Write-Host "[1/3] Installing right-click context menu entries..." -ForegroundColor Yellow

$menuRoot = "HKCU:\Software\Classes\Directory\Background\shell"
$menuDirect = "HKCU:\Software\Classes\Directory\shell"

# ── Core Tools ───────────────────────────────────────────────────────────────

# Dedupe
$dedupeKey = "$menuRoot\LitigationOS_Dedupe"
New-Item -Path $dedupeKey -Force | Out-Null
Set-ItemProperty -Path $dedupeKey -Name "(Default)" -Value "🔍 LitigationOS: Deduplicate"
Set-ItemProperty -Path $dedupeKey -Name "Icon" -Value "shell32.dll,145"
New-Item -Path "$dedupeKey\command" -Force | Out-Null
Set-ItemProperty -Path "$dedupeKey\command" -Name "(Default)" -Value "$PYTHON `"$AUTOMATION_DIR\dedupe_target.py`" `"%V`""

$dedupeDirect = "$menuDirect\LitigationOS_Dedupe"
New-Item -Path $dedupeDirect -Force | Out-Null
Set-ItemProperty -Path $dedupeDirect -Name "(Default)" -Value "🔍 LitigationOS: Deduplicate"
Set-ItemProperty -Path $dedupeDirect -Name "Icon" -Value "shell32.dll,145"
New-Item -Path "$dedupeDirect\command" -Force | Out-Null
Set-ItemProperty -Path "$dedupeDirect\command" -Name "(Default)" -Value "$PYTHON `"$AUTOMATION_DIR\dedupe_target.py`" `"%1`""

Write-Host "  ✅ Deduplicate" -ForegroundColor Green

# Organize by Type
$orgKey = "$menuRoot\LitigationOS_Organize"
New-Item -Path $orgKey -Force | Out-Null
Set-ItemProperty -Path $orgKey -Name "(Default)" -Value "📂 LitigationOS: Organize by Type"
Set-ItemProperty -Path $orgKey -Name "Icon" -Value "shell32.dll,4"
New-Item -Path "$orgKey\command" -Force | Out-Null
Set-ItemProperty -Path "$orgKey\command" -Name "(Default)" -Value "$PYTHON `"$AUTOMATION_DIR\organize_by_type.py`" `"%V`""

$orgDirect = "$menuDirect\LitigationOS_Organize"
New-Item -Path $orgDirect -Force | Out-Null
Set-ItemProperty -Path $orgDirect -Name "(Default)" -Value "📂 LitigationOS: Organize by Type"
Set-ItemProperty -Path $orgDirect -Name "Icon" -Value "shell32.dll,4"
New-Item -Path "$orgDirect\command" -Force | Out-Null
Set-ItemProperty -Path "$orgDirect\command" -Name "(Default)" -Value "$PYTHON `"$AUTOMATION_DIR\organize_by_type.py`" `"%1`""

Write-Host "  ✅ Organize by Type" -ForegroundColor Green

# ── 10 OMEGA-ELITE-MASTER Context Menu Tools ────────────────────────────────

$omegaTools = @(
    @{Name="Ω1_FileForensics"; Label="⚡ Ω1: File Forensics Scan"; Script="omega_01_file_forensics.py"; Icon="shell32.dll,22"},
    @{Name="Ω2_LegalAudit"; Label="⚖️ Ω2: Legal Document Audit"; Script="omega_02_legal_audit.py"; Icon="shell32.dll,43"},
    @{Name="Ω3_EvidenceHarvest"; Label="🔬 Ω3: Evidence Harvester"; Script="omega_03_evidence_harvest.py"; Icon="shell32.dll,172"},
    @{Name="Ω4_CitationExtract"; Label="📜 Ω4: Citation Extractor"; Script="omega_04_citation_extract.py"; Icon="shell32.dll,70"},
    @{Name="Ω5_HashVerify"; Label="🔐 Ω5: SHA-256 Integrity Verify"; Script="omega_05_hash_verify.py"; Icon="shell32.dll,47"},
    @{Name="Ω6_TimelineBuilder"; Label="📅 Ω6: Timeline Builder"; Script="omega_06_timeline_builder.py"; Icon="shell32.dll,238"},
    @{Name="Ω7_RedactionScan"; Label="🔒 Ω7: PII Redaction Scanner"; Script="omega_07_redaction_scan.py"; Icon="shell32.dll,48"},
    @{Name="Ω8_ExhibitStamper"; Label="📑 Ω8: Bates/Exhibit Stamper"; Script="omega_08_exhibit_stamper.py"; Icon="shell32.dll,246"},
    @{Name="Ω9_ContradictionScan"; Label="💥 Ω9: Contradiction Scanner"; Script="omega_09_contradiction_scan.py"; Icon="shell32.dll,219"},
    @{Name="Ω10_CourtPackager"; Label="📦 Ω10: Court Filing Packager"; Script="omega_10_court_packager.py"; Icon="shell32.dll,165"}
)

foreach ($tool in $omegaTools) {
    $bgKey = "$menuRoot\LitigationOS_$($tool.Name)"
    New-Item -Path $bgKey -Force | Out-Null
    Set-ItemProperty -Path $bgKey -Name "(Default)" -Value $tool.Label
    Set-ItemProperty -Path $bgKey -Name "Icon" -Value $tool.Icon
    New-Item -Path "$bgKey\command" -Force | Out-Null
    Set-ItemProperty -Path "$bgKey\command" -Name "(Default)" -Value "$PYTHON `"$AUTOMATION_DIR\$($tool.Script)`" `"%V`""

    $dirKey = "$menuDirect\LitigationOS_$($tool.Name)"
    New-Item -Path $dirKey -Force | Out-Null
    Set-ItemProperty -Path $dirKey -Name "(Default)" -Value $tool.Label
    Set-ItemProperty -Path $dirKey -Name "Icon" -Value $tool.Icon
    New-Item -Path "$dirKey\command" -Force | Out-Null
    Set-ItemProperty -Path "$dirKey\command" -Name "(Default)" -Value "$PYTHON `"$AUTOMATION_DIR\$($tool.Script)`" `"%1`""

    Write-Host "  ✅ $($tool.Label)" -ForegroundColor Green
}

# ── 2. SCHEDULED TASKS ─────────────────────────────────────────────────────
Write-Host ""
Write-Host "[2/3] Installing scheduled tasks..." -ForegroundColor Yellow

# Daily maintenance at 3:00 AM
$dailyAction = New-ScheduledTaskAction `
    -Execute $PYTHON `
    -Argument "`"$AUTOMATION_DIR\scheduled_maintenance.py`"" `
    -WorkingDirectory $AUTOMATION_DIR

$dailyTrigger = New-ScheduledTaskTrigger -Daily -At "3:00AM"
$dailySettings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable:$false

try {
    Register-ScheduledTask `
        -TaskName "LitigationOS_DailyMaintenance" `
        -Action $dailyAction `
        -Trigger $dailyTrigger `
        -Settings $dailySettings `
        -Description "LitigationOS: Daily file organization, dedup, and drive ingestion" `
        -Force | Out-Null
    Write-Host "  ✅ Daily maintenance (3:00 AM)" -ForegroundColor Green
} catch {
    Write-Host "  ⚠️ Daily task needs admin: $($_.Exception.Message)" -ForegroundColor DarkYellow
}

# Weekly deep dedup Sunday 4:00 AM
$weeklyAction = New-ScheduledTaskAction `
    -Execute $PYTHON `
    -Argument "`"$AUTOMATION_DIR\dedupe_target.py`" `"C:\Users\andre\LitigationOS`"" `
    -WorkingDirectory $AUTOMATION_DIR

$weeklyTrigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At "4:00AM"

try {
    Register-ScheduledTask `
        -TaskName "LitigationOS_WeeklyDedup" `
        -Action $weeklyAction `
        -Trigger $weeklyTrigger `
        -Settings $dailySettings `
        -Description "LitigationOS: Weekly deep SHA-256 deduplication scan" `
        -Force | Out-Null
    Write-Host "  ✅ Weekly deep dedup (Sunday 4:00 AM)" -ForegroundColor Green
} catch {
    Write-Host "  ⚠️ Weekly task needs admin: $($_.Exception.Message)" -ForegroundColor DarkYellow
}

# ── 3. VERIFY ───────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "[3/3] Verifying installation..." -ForegroundColor Yellow

$regCheck = Test-Path "$menuRoot\LitigationOS_Dedupe"
$taskCheck = Get-ScheduledTask -TaskName "LitigationOS_DailyMaintenance" -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  INSTALLATION COMPLETE" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Context menus:    $(if($regCheck){'✅ INSTALLED'}else{'❌ FAILED'})" 
Write-Host "  Scheduled tasks:  $(if($taskCheck){'✅ INSTALLED'}else{'⚠️ Run as Admin'})" 
Write-Host ""
Write-Host "  Right-click any folder to access 12 LitigationOS tools." -ForegroundColor White
Write-Host "  Maintenance runs automatically — you never need to organize again." -ForegroundColor White
Write-Host "================================================" -ForegroundColor Cyan
