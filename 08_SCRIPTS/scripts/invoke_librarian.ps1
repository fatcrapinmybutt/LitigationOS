# invoke_librarian.ps1
# The Librarian Engine – Rename, Tag, Move Files, and Build Evidence Architecture
# Authoritative, loss-proof, court-grade. Powershell-only version.

param(
    [switch]$Verbose,
    [switch]$Silent
)

# === PATH DEFINITIONS ===
$SourcePath      = "F:\LITIGATION_FILES\litigation_files\raw_uploads"
$DestinationRoot = "F:\LITIGATION_FILES\litigation_files"
$LogRoot         = Join-Path $DestinationRoot '..\data\logs'
$TimelinePath    = Join-Path $DestinationRoot '..\data\timelines\evidence_timeline.csv'
$RolodexDir      = Join-Path $DestinationRoot '..\data\rolodex'
$ExhibitIndex    = Join-Path $DestinationRoot '..\data\exhibits\exhibit_index.csv'

# === CREATE REQUIRED FOLDERS ===
$folders = @(
    $DestinationRoot,
    "$DestinationRoot\custody",
    "$DestinationRoot\ppo",
    "$DestinationRoot\contempt",
    "$DestinationRoot\housing",
    "$DestinationRoot\police",
    "$DestinationRoot\medical",
    "$DestinationRoot\unsorted",
    $LogRoot,
    Split-Path $TimelinePath -Parent,
    $RolodexDir,
    Split-Path $ExhibitIndex -Parent
)
foreach ($f in $folders) { if (!(Test-Path $f)) { New-Item -ItemType Directory -Path $f | Out-Null } }

# === LOG FILES INITIALIZATION ===
$LogPath = Join-Path $LogRoot 'LIBRARIAN_MOVE_LOG.csv'
$ErrorLog = Join-Path $LogRoot 'LIBRARIAN_ERRORS.log'
if (!(Test-Path $LogPath)) {
    "Timestamp,OriginalName,NewName,TargetFolder,Reason" `n | Out-File -FilePath $LogPath -Encoding UTF8
}

# === HELPER FUNCTIONS ===
function Get-Category { param($n)  
    switch -regex ($n) {
        'AppClose|custody|parenting' { 'custody'; break }
        'ppo|showcause|violation|threat' { 'ppo'; break }
        'contempt|compliance|order' { 'contempt'; break }
        'rent|housing|sewage|ledger' { 'housing'; break }
        'police|report|incident' { 'police'; break }
        'corewell|doctor|medical' { 'medical'; break }
        default { 'unsorted' }
    }
}

function Get-RenamedFile { param($f)
    $base  = [IO.Path]::GetFileNameWithoutExtension($f.Name)
    $ext   = $f.Extension
    $safe  = $base -replace '[^\w\-]','_'
    $date  = $f.LastWriteTime.ToString('yyyy-MM-dd')
    return "$date`_$safe$ext"
}

# === MAIN FILE PROCESSING ===
$files = Get-ChildItem -Path $SourcePath -File -Recurse -Force
if (-not $Silent) { Write-Host "Found $($files.Count) files in source." }
if ($files.Count -eq 0 -and -not $Silent) { Write-Warning "No files to process in raw_uploads." }

$counts = @{}; $dup=0; $mv=0; $err=0
foreach ($file in $files) {
    try {
        $cat    = Get-Category $file.Name
        $counts[$cat] = ($counts[$cat] + 0)
        $newNm  = Get-RenamedFile $file
        $dest   = Join-Path -Path $DestinationRoot -ChildPath $cat
        $target = Join-Path -Path $dest -ChildPath $newNm
        if (Test-Path $target) {
            "$((Get-Date).ToString('s')),$($file.Name),$newNm,$cat,DUPLICATE" | Out-File -Append $LogPath
            $dup++ ; continue
        }
        Move-Item $file.FullName $target
        "$((Get-Date).ToString('s')),$($file.Name),$newNm,$cat,MOVED" | Out-File -Append $LogPath
        $counts[$cat]++; $mv++
        if ($Verbose) { Write-Host "Moved $($file.Name) → $cat\$newNm" }
    } catch {
        "[ERROR] $($file.Name): $($_.Exception.Message)" | Out-File -Append $ErrorLog
        $err++
    }
}

if (-not $Silent) {
    Write-Host "`n=== Summary ==="
    Write-Host "Moved: $mv | Duplicates: $dup | Errors: $err"
    Write-Host "Category breakdown:"
    $counts.GetEnumerator() | ForEach-Object { Write-Host "  $_.Key : $_.Value" }
}

# === MODULE: build_evidence_timeline ===
# Generates chronological CSV from move log
Import-Csv $LogPath |
    Sort-Object {[datetime]$_.Timestamp} |
    Select-Object Timestamp,OriginalName,NewName,TargetFolder |
    Export-Csv -Path $TimelinePath -NoTypeInformation
if ($Verbose) { Write-Host "Timeline exported to $TimelinePath" }

# === MODULE: auto_rolodex ===
# Emits JSON metadata per log entry
Import-Csv $LogPath | ForEach-Object {
    $m = [PSCustomObject]@{
        OriginalName = $_.OriginalName; NewName = $_.NewName;
        Timestamp    = $_.Timestamp;  Category = $_.TargetFolder;
        Reason       = $_.Reason
    }
    $json = $m | ConvertTo-Json -Depth 3
    $fn   = ($_.Timestamp + '_' + $_.NewName) -replace '[\\/:*?"<>|]','_'
    $path = Join-Path $RolodexDir ($fn + '.json')
    $json | Out-File $path -Encoding UTF8
    if ($Verbose) { Write-Host "Rolodex entry: $path" }
}

# === MODULE: auto_exhibit_index_v2 ===
# Builds exhibit index CSV
$metaFiles = Get-ChildItem -Path $RolodexDir -Filter '*.json'
$recs = $metaFiles | ForEach-Object {
    $d = Get-Content $_.FullName | ConvertFrom-Json
    [PSCustomObject]@{
        Orig    = $d.OriginalName; New = $d.NewName;
        Path    = $_.FullName; Category = $d.Category;
        Timestamp = $d.Timestamp
    }
}
for ($i=0; $i -lt $recs.Count; $i++) {
    $recs[$i] | Add-Member -NotePropertyName ExhibitID -NotePropertyValue ([char](65+$i))
}
$recs |
    Select-Object ExhibitID,Orig,New,Category,Path,Timestamp |
    Export-Csv -Path $ExhibitIndex -NoTypeInformation
if ($Verbose) { Write-Host "Exhibit index written to $ExhibitIndex" }
