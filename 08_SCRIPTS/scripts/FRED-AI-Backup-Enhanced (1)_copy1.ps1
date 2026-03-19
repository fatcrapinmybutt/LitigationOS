
# ==========================================================
# 🔐 FRED-AI v3.0 – Enhanced Bi-Weekly Backup System
# Description: Safely zips FRED directory with logging, size report, and cleanup rotation
# Author: AJP Legal Systems / ChatGPT-AI Legal Automation
# ==========================================================

# Configuration
$source = "F:\FRED"
$backupDir = "F:\FRED\Backups"
$logFile = Join-Path $backupDir "backup_log.txt"
$dateStamp = Get-Date -Format "yyyy-MM-dd_HHmm"
$backupName = "FRED_Backup_$dateStamp.zip"
$backupPath = Join-Path $backupDir $backupName
$retainCount = 8  # Max number of backups to keep

# Ensure backup directory exists
if (-not (Test-Path $backupDir)) {
    New-Item -ItemType Directory -Path $backupDir | Out-Null
}

# Start Logging
$logEntry = @()
$logEntry += "==========================================="
$logEntry += "📦 FRED-AI Backup Log - $(Get-Date)"
$logEntry += "Backup File: $backupName"

try {
    # Create ZIP backup
    Add-Type -AssemblyName 'System.IO.Compression.FileSystem'
    [System.IO.Compression.ZipFile]::CreateFromDirectory($source, $backupPath)

    # Calculate size
    $sizeMB = "{0:N2}" -f ((Get-Item $backupPath).Length / 1MB)
    $logEntry += "Size: $sizeMB MB"
    $logEntry += "✅ Backup completed successfully."

    # Cleanup old backups beyond retention limit
    $existingBackups = Get-ChildItem -Path $backupDir -Filter "FRED_Backup_*.zip" | Sort-Object LastWriteTime -Descending
    if ($existingBackups.Count -gt $retainCount) {
        $toDelete = $existingBackups | Select-Object -Skip $retainCount
        foreach ($item in $toDelete) {
            Remove-Item $item.FullName -Force
            $logEntry += "🗑️ Deleted old backup: $($item.Name)"
        }
    }
}
catch {
    $logEntry += "❌ Error: $_"
}

# Write log
$logEntry | Out-File -Append -Encoding UTF8 $logFile
Write-Host ($logEntry -join "`n")
