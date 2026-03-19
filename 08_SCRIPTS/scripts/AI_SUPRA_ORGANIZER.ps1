Add-Type -AssemblyName Microsoft.VisualBasic

$sourceDrive = "F:\"
$scaffoldRoot = "$sourceDrive\LITIGATION_SCAFFOLD_AI"
$tempUnzip = "$scaffoldRoot\__UNZIP_TEMP"
$manifestPath = "$scaffoldRoot\_MANIFESTS"
$logManifest = "$manifestPath\file_manifest.json"
$logDeleted = "$manifestPath\deleted_folders.txt"
$logConflicts = "$manifestPath\deduplication_log.txt"

# Keyword→Folder map (AI-style match based on content type)
$classificationMap = @{
    "pleading"     = "$scaffoldRoot\01_COURT_DOCUMENTS\Pleadings"
    "motion"       = "$scaffoldRoot\01_COURT_DOCUMENTS\Motions"
    "affidavit"    = "$scaffoldRoot\01_COURT_DOCUMENTS\Affidavits"
    "order"        = "$scaffoldRoot\01_COURT_DOCUMENTS\Orders"
    "transcript"   = "$scaffoldRoot\01_COURT_DOCUMENTS\Hearing_Transcripts"
    "evidence"     = "$scaffoldRoot\02_EVIDENCE"
    "img"          = "$scaffoldRoot\02_EVIDENCE\Images"
    "jpg"          = "$scaffoldRoot\02_EVIDENCE\Images"
    "jpeg"         = "$scaffoldRoot\02_EVIDENCE\Images"
    "png"          = "$scaffoldRoot\02_EVIDENCE\Images"
    "gif"          = "$scaffoldRoot\02_EVIDENCE\Images"
    "pdf"          = "$scaffoldRoot\02_EVIDENCE\PDFs"
    "mp3"          = "$scaffoldRoot\02_EVIDENCE\Audio"
    "mp4"          = "$scaffoldRoot\02_EVIDENCE\Video"
    "appclose"     = "$scaffoldRoot\03_COMMUNICATION\AppClose"
    "email"        = "$scaffoldRoot\03_COMMUNICATION\Emails"
    "sms"          = "$scaffoldRoot\03_COMMUNICATION\Texts_SMS"
    "txt"          = "$scaffoldRoot\03_COMMUNICATION\Texts_SMS"
    "message"      = "$scaffoldRoot\03_COMMUNICATION\Texts_SMS"
    "police"       = "$scaffoldRoot\04_POLICE_AND_PPO\Police_Reports"
    "report"       = "$scaffoldRoot\04_POLICE_AND_PPO\Police_Reports"
    "ppo"          = "$scaffoldRoot\04_POLICE_AND_PPO\PPO_Docs"
    "show_cause"   = "$scaffoldRoot\04_POLICE_AND_PPO\PPO_Docs"
    "jail"         = "$scaffoldRoot\04_POLICE_AND_PPO\Jail_Records"
    "rent"         = "$scaffoldRoot\05_FINANCIAL\Rent_Ledgers"
    "ledger"       = "$scaffoldRoot\05_FINANCIAL\Rent_Ledgers"
    "paystub"      = "$scaffoldRoot\05_FINANCIAL\Paystubs"
    "support"      = "$scaffoldRoot\05_FINANCIAL\Child_Support"
    "bank"         = "$scaffoldRoot\05_FINANCIAL\Bank_Statements"
}

# Create folder scaffold
$folders = @(
    "$scaffoldRoot\00_UNCLASSIFIED_MANUAL_REVIEW",
    "$scaffoldRoot\01_COURT_DOCUMENTS\Pleadings",
    "$scaffoldRoot\01_COURT_DOCUMENTS\Orders",
    "$scaffoldRoot\01_COURT_DOCUMENTS\Motions",
    "$scaffoldRoot\01_COURT_DOCUMENTS\Affidavits",
    "$scaffoldRoot\01_COURT_DOCUMENTS\Hearing_Transcripts",
    "$scaffoldRoot\02_EVIDENCE\Screenshots",
    "$scaffoldRoot\02_EVIDENCE\PDFs",
    "$scaffoldRoot\02_EVIDENCE\Audio",
    "$scaffoldRoot\02_EVIDENCE\Video",
    "$scaffoldRoot\02_EVIDENCE\Images",
    "$scaffoldRoot\03_COMMUNICATION\AppClose",
    "$scaffoldRoot\03_COMMUNICATION\Emails",
    "$scaffoldRoot\03_COMMUNICATION\Texts_SMS",
    "$scaffoldRoot\04_POLICE_AND_PPO\Police_Reports",
    "$scaffoldRoot\04_POLICE_AND_PPO\PPO_Docs",
    "$scaffoldRoot\04_POLICE_AND_PPO\Jail_Records",
    "$scaffoldRoot\05_FINANCIAL\Rent_Ledgers",
    "$scaffoldRoot\05_FINANCIAL\Child_Support",
    "$scaffoldRoot\05_FINANCIAL\Paystubs",
    "$scaffoldRoot\05_FINANCIAL\Bank_Statements",
    "$scaffoldRoot\06_MISC",
    "$manifestPath",
    "$tempUnzip"
)
$folders | ForEach-Object { New-Item -Path $_ -ItemType Directory -Force | Out-Null }

# Clear logs
"" | Set-Content $logManifest
"" | Set-Content $logDeleted
"" | Set-Content $logConflicts
$manifest = @{}

# Unzip everything
Get-ChildItem -Path $sourceDrive -Recurse -Filter *.zip | ForEach-Object {
    try {
        $zipName = $_.BaseName
        $unzipTarget = Join-Path $tempUnzip $zipName
        Expand-Archive -Path $_.FullName -DestinationPath $unzipTarget -Force
        Write-Host " Unzipped: $($_.FullName)"
    } catch {
        Write-Warning " Failed to unzip: $($_.FullName)"
    }
}

# AI-Sort and move
$allFiles = Get-ChildItem -Path $sourceDrive, $tempUnzip -Recurse -File
foreach ($file in $allFiles) {
    $fileName = $file.Name.ToLower()
    $destFolder = "$scaffoldRoot\00_UNCLASSIFIED_MANUAL_REVIEW"

    foreach ($key in $classificationMap.Keys) {
        if ($fileName -like "*$key*") {
            $destFolder = $classificationMap[$key]
            break
        }
    }

    $destPath = Join-Path $destFolder $file.Name
    $i = 1
    while (Test-Path $destPath) {
        $base = [System.IO.Path]::GetFileNameWithoutExtension($file.Name)
        $ext = $file.Extension
        $destPath = Join-Path $destFolder "$base ($i)$ext"
        $i++
        Add-Content $logConflicts "Conflict renamed: $($file.FullName) -> $destPath"
    }

    try {
        Move-Item -Path $file.FullName -Destination $destPath -Force
        $manifest[$file.FullName] = $destPath
    } catch {
        Write-Warning " Failed to move: $($file.FullName)"
    }
}

# Save manifest
$manifest | ConvertTo-Json -Depth 5 | Set-Content $logManifest

# Delete empty folders → Recycle Bin
$allDirs = Get-ChildItem -Path $sourceDrive -Recurse -Directory | Sort-Object -Property FullName -Descending
foreach ($dir in $allDirs) {
    if (-not (Get-ChildItem -Path $dir.FullName -Recurse)) {
        try {
            [Microsoft.VisualBasic.FileIO.FileSystem]::DeleteDirectory($dir.FullName, 'OnlyErrorDialogs', 'SendToRecycleBin')
            Add-Content $logDeleted "$($dir.FullName)"
        } catch {
            Write-Warning " Could not delete: $($dir.FullName)"
        }
    }
}

# Clean temp
Remove-Item -Path $tempUnzip -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "`n COMPLETE!"
Write-Host "Output: $scaffoldRoot"
Write-Host "Logs saved to: $manifestPath"