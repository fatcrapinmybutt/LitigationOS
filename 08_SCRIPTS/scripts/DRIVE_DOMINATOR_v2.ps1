# DRIVE_DOMINATOR_v2.ps1
# Tactical file sort with logging, duplicate detection, and recursion
# Author: Andrew Pigors
# Date: 2025-05-11
# Location: F:\

$source = "F:\"
$logFile = Join-Path $source "Dominator_Log.txt"
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Add-Content $logFile "`n==== Run Started at $timestamp ===="

$groups = @{
    'PDFs'           = @('*.pdf')
    'Word_Documents' = @('*.doc', '*.docx')
    'Spreadsheets'   = @('*.xls', '*.xlsx', '*.csv')
    'Presentations'  = @('*.ppt', '*.pptx')
    'Images'         = @('*.jpg', '*.jpeg', '*.png', '*.gif', '*.bmp')
    'Archives'       = @('*.zip', '*.rar', '*.7z', '*.gz', '*.tar')
    'Scripts'        = @('*.ps1', '*.py', '*.bat', '*.sh')
    'Videos'         = @('*.mp4', '*.mov', '*.avi', '*.mkv')
    'Audio'          = @('*.mp3', '*.wav', '*.ogg')
    'Text_Files'     = @('*.txt', '*.md', '*.log')
}

foreach ($folder in $groups.Keys) {
    $targetDir = Join-Path -Path $source -ChildPath $folder
    if (-not (Test-Path $targetDir)) {
        New-Item -Path $targetDir -ItemType Directory | Out-Null
        Add-Content $logFile "Created folder: $targetDir"
    }

    foreach ($pattern in $groups[$folder]) {
        Get-ChildItem -Path $source -Filter $pattern -File -Recurse | ForEach-Object {
            $baseName = $_.BaseName
            $ext = $_.Extension
            $destination = Join-Path $targetDir $_.Name
            $i = 1

            while (Test-Path $destination) {
                $destination = Join-Path $targetDir "$baseName`_copy$i$ext"
                $i++
            }

            Move-Item $_.FullName $destination -Force -ErrorAction SilentlyContinue
            Add-Content $logFile "Moved: $($_.FullName) -> $destination"
        }
    }
}

Add-Content $logFile "==== Run Completed at $(Get-Date -Format "HH:mm:ss") ===="
