# LitigationOS Incremental Backup Script
# Run after each phase checkpoint
param([string]$Phase = "UNKNOWN")

$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$backupDir = "D:\BACKUPS\PHASE_${Phase}_${ts}"
New-Item -ItemType Directory -Path $backupDir -Force | Out-Null

# Always backup the database
$dbSrc = "C:\Users\andre\litigation_context.db"
if (Test-Path $dbSrc) {
    $dbDst = "$backupDir\litigation_context.db.zip"
    Compress-Archive -Path $dbSrc -DestinationPath $dbDst -CompressionLevel Optimal
    Write-Host "DB backup: $dbDst ($([math]::Round((Get-Item $dbDst).Length/1MB))MB)"
}

# Backup changed filings
$filingDirs = @("C:\Users\andre\Desktop\COURT_PACKETS_v3", "C:\Users\andre\Scans\litigation-os")
foreach ($d in $filingDirs) {
    if (Test-Path $d) {
        $name = Split-Path $d -Leaf
        Compress-Archive -Path $d -DestinationPath "$backupDir\${name}.zip" -CompressionLevel Optimal
        Write-Host "Backed up: $name"
    }
}

# Log
"Phase: $Phase`nTimestamp: $ts`nBackupDir: $backupDir" | Out-File "$backupDir\BACKUP_LOG.txt"
Write-Host "Incremental backup complete: $backupDir"
