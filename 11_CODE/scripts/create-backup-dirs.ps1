# Create Backup System Directory Structure
# Target: I:\LitigationOS-Ultimate\08-Backup-History

$basePath = "I:\LitigationOS-Ultimate\08-Backup-History"
$subdirectories = @(
    "Full-Backups",
    "Incremental-Backups", 
    "Differential-Backups",
    "Archives",
    "Logs",
    "Scripts",
    "Databases",
    "Reports",
    "Temp"
)

Write-Host "Creating backup directory structure..." -ForegroundColor Cyan
Write-Host "Base path: $basePath`n" -ForegroundColor Yellow

# Create base directory
if (Test-Path $basePath) {
    Write-Host "✓ Base directory already exists" -ForegroundColor Green
} else {
    New-Item -ItemType Directory -Path $basePath -Force | Out-Null
    Write-Host "✓ Created base directory" -ForegroundColor Green
}

# Create subdirectories
$createdCount = 0
foreach ($subdir in $subdirectories) {
    $fullPath = Join-Path -Path $basePath -ChildPath $subdir
    
    if (Test-Path $fullPath) {
        Write-Host "→ Already exists: $subdir" -ForegroundColor Gray
    } else {
        New-Item -ItemType Directory -Path $fullPath -Force | Out-Null
        Write-Host "✓ Created: $subdir" -ForegroundColor Green
        $createdCount++
    }
}

Write-Host "`n" 
Write-Host "=== Final Directory Structure ===" -ForegroundColor Cyan
Get-ChildItem -Path $basePath -Directory | Sort-Object Name | ForEach-Object {
    Write-Host "  └─ $($_.Name)"
}

Write-Host "`nTotal directories: $($(Get-ChildItem -Path $basePath -Directory | Measure-Object).Count)" -ForegroundColor Green
Write-Host "Newly created: $createdCount" -ForegroundColor Green
