$basePath = "F:\ULTIMATE-FRED-PRIME"
if (!(Test-Path $basePath)) {
    New-Item -ItemType Directory -Path $basePath -Force | Out-Null
    Write-Host "Created root: $basePath" -ForegroundColor Green
} else {
    Write-Host "Root exists: $basePath" -ForegroundColor Cyan
}

$folderPath = Join-Path $basePath "Benchbooks"
if (!(Test-Path $folderPath)) {
    New-Item -ItemType Directory -Path $folderPath -Force | Out-Null
    Write-Host "Created folder: Benchbooks" -ForegroundColor Green
} else { Write-Host "Exists: Benchbooks" -ForegroundColor Yellow }

$folderPath = Join-Path $basePath "Cores"
if (!(Test-Path $folderPath)) {
    New-Item -ItemType Directory -Path $folderPath -Force | Out-Null
    Write-Host "Created folder: Cores" -ForegroundColor Green
} else { Write-Host "Exists: Cores" -ForegroundColor Yellow }

$folderPath = Join-Path $basePath "Engines"
if (!(Test-Path $folderPath)) {
    New-Item -ItemType Directory -Path $folderPath -Force | Out-Null
    Write-Host "Created folder: Engines" -ForegroundColor Green
} else { Write-Host "Exists: Engines" -ForegroundColor Yellow }

$folderPath = Join-Path $basePath "Evidence"
if (!(Test-Path $folderPath)) {
    New-Item -ItemType Directory -Path $folderPath -Force | Out-Null
    Write-Host "Created folder: Evidence" -ForegroundColor Green
} else { Write-Host "Exists: Evidence" -ForegroundColor Yellow }

$folderPath = Join-Path $basePath "GUI"
if (!(Test-Path $folderPath)) {
    New-Item -ItemType Directory -Path $folderPath -Force | Out-Null
    Write-Host "Created folder: GUI" -ForegroundColor Green
} else { Write-Host "Exists: GUI" -ForegroundColor Yellow }

$folderPath = Join-Path $basePath "Logs"
if (!(Test-Path $folderPath)) {
    New-Item -ItemType Directory -Path $folderPath -Force | Out-Null
    Write-Host "Created folder: Logs" -ForegroundColor Green
} else { Write-Host "Exists: Logs" -ForegroundColor Yellow }

$folderPath = Join-Path $basePath "Matrix"
if (!(Test-Path $folderPath)) {
    New-Item -ItemType Directory -Path $folderPath -Force | Out-Null
    Write-Host "Created folder: Matrix" -ForegroundColor Green
} else { Write-Host "Exists: Matrix" -ForegroundColor Yellow }

$folderPath = Join-Path $basePath "Modules"
if (!(Test-Path $folderPath)) {
    New-Item -ItemType Directory -Path $folderPath -Force | Out-Null
    Write-Host "Created folder: Modules" -ForegroundColor Green
} else { Write-Host "Exists: Modules" -ForegroundColor Yellow }

$folderPath = Join-Path $basePath "Pipelines"
if (!(Test-Path $folderPath)) {
    New-Item -ItemType Directory -Path $folderPath -Force | Out-Null
    Write-Host "Created folder: Pipelines" -ForegroundColor Green
} else { Write-Host "Exists: Pipelines" -ForegroundColor Yellow }

$folderPath = Join-Path $basePath "Plugins"
if (!(Test-Path $folderPath)) {
    New-Item -ItemType Directory -Path $folderPath -Force | Out-Null
    Write-Host "Created folder: Plugins" -ForegroundColor Green
} else { Write-Host "Exists: Plugins" -ForegroundColor Yellow }

$folderPath = Join-Path $basePath "Protocols"
if (!(Test-Path $folderPath)) {
    New-Item -ItemType Directory -Path $folderPath -Force | Out-Null
    Write-Host "Created folder: Protocols" -ForegroundColor Green
} else { Write-Host "Exists: Protocols" -ForegroundColor Yellow }

$folderPath = Join-Path $basePath "Scanners"
if (!(Test-Path $folderPath)) {
    New-Item -ItemType Directory -Path $folderPath -Force | Out-Null
    Write-Host "Created folder: Scanners" -ForegroundColor Green
} else { Write-Host "Exists: Scanners" -ForegroundColor Yellow }

$folderPath = Join-Path $basePath "Scripts"
if (!(Test-Path $folderPath)) {
    New-Item -ItemType Directory -Path $folderPath -Force | Out-Null
    Write-Host "Created folder: Scripts" -ForegroundColor Green
} else { Write-Host "Exists: Scripts" -ForegroundColor Yellow }

$folderPath = Join-Path $basePath "Systems"
if (!(Test-Path $folderPath)) {
    New-Item -ItemType Directory -Path $folderPath -Force | Out-Null
    Write-Host "Created folder: Systems" -ForegroundColor Green
} else { Write-Host "Exists: Systems" -ForegroundColor Yellow }

$folderPath = Join-Path $basePath "Triggers"
if (!(Test-Path $folderPath)) {
    New-Item -ItemType Directory -Path $folderPath -Force | Out-Null
    Write-Host "Created folder: Triggers" -ForegroundColor Green
} else { Write-Host "Exists: Triggers" -ForegroundColor Yellow }

$folderPath = Join-Path $basePath "Validators"
if (!(Test-Path $folderPath)) {
    New-Item -ItemType Directory -Path $folderPath -Force | Out-Null
    Write-Host "Created folder: Validators" -ForegroundColor Green
} else { Write-Host "Exists: Validators" -ForegroundColor Yellow }

$folderPath = Join-Path $basePath "Workflows"
if (!(Test-Path $folderPath)) {
    New-Item -ItemType Directory -Path $folderPath -Force | Out-Null
    Write-Host "Created folder: Workflows" -ForegroundColor Green
} else { Write-Host "Exists: Workflows" -ForegroundColor Yellow }

$folderPath = Join-Path $basePath "Dashboards"
if (!(Test-Path $folderPath)) {
    New-Item -ItemType Directory -Path $folderPath -Force | Out-Null
    Write-Host "Created folder: Dashboards" -ForegroundColor Green
} else { Write-Host "Exists: Dashboards" -ForegroundColor Yellow }

$folderPath = Join-Path $basePath "Masterlists"
if (!(Test-Path $folderPath)) {
    New-Item -ItemType Directory -Path $folderPath -Force | Out-Null
    Write-Host "Created folder: Masterlists" -ForegroundColor Green
} else { Write-Host "Exists: Masterlists" -ForegroundColor Yellow }

$folderPath = Join-Path $basePath "Index"
if (!(Test-Path $folderPath)) {
    New-Item -ItemType Directory -Path $folderPath -Force | Out-Null
    Write-Host "Created folder: Index" -ForegroundColor Green
} else { Write-Host "Exists: Index" -ForegroundColor Yellow }

$folderPath = Join-Path $basePath "Agents"
if (!(Test-Path $folderPath)) {
    New-Item -ItemType Directory -Path $folderPath -Force | Out-Null
    Write-Host "Created folder: Agents" -ForegroundColor Green
} else { Write-Host "Exists: Agents" -ForegroundColor Yellow }

$folderPath = Join-Path $basePath "AutoBackup"
if (!(Test-Path $folderPath)) {
    New-Item -ItemType Directory -Path $folderPath -Force | Out-Null
    Write-Host "Created folder: AutoBackup" -ForegroundColor Green
} else { Write-Host "Exists: AutoBackup" -ForegroundColor Yellow }

$folderPath = Join-Path $basePath "Installer"
if (!(Test-Path $folderPath)) {
    New-Item -ItemType Directory -Path $folderPath -Force | Out-Null
    Write-Host "Created folder: Installer" -ForegroundColor Green
} else { Write-Host "Exists: Installer" -ForegroundColor Yellow }

$folderPath = Join-Path $basePath "LegalDocs"
if (!(Test-Path $folderPath)) {
    New-Item -ItemType Directory -Path $folderPath -Force | Out-Null
    Write-Host "Created folder: LegalDocs" -ForegroundColor Green
} else { Write-Host "Exists: LegalDocs" -ForegroundColor Yellow }

$folderPath = Join-Path $basePath "AI_Core"
if (!(Test-Path $folderPath)) {
    New-Item -ItemType Directory -Path $folderPath -Force | Out-Null
    Write-Host "Created folder: AI_Core" -ForegroundColor Green
} else { Write-Host "Exists: AI_Core" -ForegroundColor Yellow }
