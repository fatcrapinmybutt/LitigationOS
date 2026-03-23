# EMERGENCY BACKUP SCRIPT
$SourcePath = "C:\Users\andre\Desktop\LITIGATION_OS\ALL_PC_EVIDENCE_EXTRACTED"
$DestPath = "I:\EMERGENCY_BACKUP\ALL_PC_EVIDENCE_EXTRACTED"
$LogPath = "I:\EMERGENCY_BACKUP\LOGS"
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$LogFile = Join-Path $LogPath "backup_$Timestamp.txt"

Write-Host "LITIGATION EVIDENCE EMERGENCY BACKUP" -ForegroundColor Cyan
Write-Host "Source: $SourcePath"
Write-Host "Destination: $DestPath"

New-Item -ItemType Directory -Path $DestPath -Force -ErrorAction SilentlyContinue | Out-Null
New-Item -ItemType Directory -Path $LogPath -Force -ErrorAction SilentlyContinue | Out-Null

Write-Host "`nStarting backup..."
$startTime = Get-Date

robocopy $SourcePath $DestPath /E /Z /R:3 /W:5 /MT:8 /LOG:$LogFile /TEE /NP

$duration = (Get-Date) - $startTime

Write-Host "`nVerifying..."
$sourceCount = (Get-ChildItem $SourcePath -Recurse -File -ErrorAction SilentlyContinue).Count
$destCount = (Get-ChildItem $DestPath -Recurse -File -ErrorAction SilentlyContinue).Count

if ($sourceCount -eq $destCount) {
    Write-Host "✅ SUCCESS: $destCount files backed up!" -ForegroundColor Green
} else {
    Write-Host "⚠️ WARNING: Count mismatch (Source: $sourceCount, Backup: $destCount)" -ForegroundColor Yellow
}

Write-Host "`nDuration: $($duration.ToString())"
Write-Host "Log: $LogFile"
