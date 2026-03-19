
# ================================================
# 🔐 FRED-AI v2.0 – Automated Backup Script
# Description: Zips the full FRED directory into a date-stamped archive
# Author: AJP Legal Systems / ChatGPT-AI Legal Automation
# ================================================

$source = "F:\FRED"
$backupDir = "F:\FRED\Backups"
$dateStamp = Get-Date -Format "yyyy-MM-dd_HHmm"
$backupName = "FRED_Backup_$dateStamp.zip"
$backupPath = Join-Path $backupDir $backupName

# Ensure backup directory exists
if (-not (Test-Path $backupDir)) {
    New-Item -ItemType Directory -Path $backupDir | Out-Null
}

# Create ZIP backup
Add-Type -AssemblyName 'System.IO.Compression.FileSystem'
[System.IO.Compression.ZipFile]::CreateFromDirectory($source, $backupPath)

Write-Host "✅ Backup created: $backupPath"
