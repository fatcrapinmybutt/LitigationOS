$source = "F:\"

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
    if (-not (Test-Path -Path $targetDir)) {
        New-Item -Path $targetDir -ItemType Directory | Out-Null
    }

    foreach ($pattern in $groups[$folder]) {
        Get-ChildItem -Path $source -Filter $pattern -File | ForEach-Object {
            $destination = Join-Path -Path $targetDir -ChildPath $_.Name
            Move-Item -Path $_.FullName -Destination $destination -Force -ErrorAction SilentlyContinue
        }
    }
}
