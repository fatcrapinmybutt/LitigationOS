# CONFIG
$sourcePath = "F:\"                     # Your SSD
$destinationRoot = "F:\LLC_Litigation_Archive"
$includeExtensions = ".pdf", ".docx", ".doc", ".txt", ".rtf", ".xlsx", ".zip"
$hashMap = @{}
$globalLog = @()

# TIMESTAMP
$timestamp = Get-Date -Format "yyyy-MM-dd_HHmmss"
$globalLogPath = Join-Path $destinationRoot "LLC_Organizer_Log_$timestamp.txt"

# CATEGORY DETECTION FUNCTION
function Get-UseCategory {
    param($name, $content)
    $text = "$name $content".ToLower()
    switch -regex ($text) {
        "lease|rent|agreement"         { return "Lease_Agreements" }
        "invoice|payment|billing|due"  { return "Financial_Records" }
        "email|communication|message"  { return "Correspondence" }
        "court|motion|filing|show cause|hearing" { return "Legal_Filings" }
        "repair|maintenance|leak|sewage|mold"    { return "Property_Issues" }
        default                        { return "Uncategorized" }
    }
}

# DEDUPLICATION
function Get-FileHashSafe {
    param($file)
    try {
        return (Get-FileHash -Path $file -Algorithm SHA256).Hash
    } catch {
        Write-Warning "Cannot hash: $file"
        return $null
    }
}

# UNZIP FUNCTION
function Unpack-ZipRecursive {
    param($zipPath, $outputFolder)
    try {
        Expand-Archive -Path $zipPath -DestinationPath $outputFolder -Force
        Get-ChildItem -Path $outputFolder -Recurse -Filter *.zip | ForEach-Object {
            $nestedFolder = "$($_.DirectoryName)\$($_.BaseName)_unzipped"
            Unpack-ZipRecursive -zipPath $_.FullName -outputFolder $nestedFolder
        }
    } catch {
        Write-Warning "Zip failed: $zipPath"
    }
}

# MAIN PROCESS
$files = Get-ChildItem -Path $sourcePath -Recurse -File -Include $includeExtensions -ErrorAction SilentlyContinue

foreach ($file in $files) {
    $hash = Get-FileHashSafe -file $file.FullName
    if (-not $hash -or $hashMap.ContainsKey($hash)) { continue }

    $hashMap[$hash] = $true
    $preview = ""
    if ($file.Extension -match "\.txt|\.docx|\.rtf") {
        try { $preview = Get-Content -Path $file.FullName -TotalCount 15 -ErrorAction Stop -Raw } catch {}
    }

    $category = Get-UseCategory -name $file.Name -content $preview
    $targetFolder = Join-Path $destinationRoot $category
    if (!(Test-Path -Path $targetFolder)) {
        New-Item -Path $targetFolder -ItemType Directory -Force
    }

    $destination = Join-Path $targetFolder $file.Name
    try {
        Move-Item -Path $file.FullName -Destination $destination -Force
        Write-Host "Moved: $($file.FullName) → $destination"
        $globalLog += "[$(Get-Date)] MOVED: $($file.FullName) → $destination"
    } catch {
        Write-Warning "Could not move: $($file.FullName)"
        $globalLog += "[$(Get-Date)] ERROR: Failed to move $($file.FullName)"
        continue
    }

    # ZIP EXTRACTION
    if ($file.Extension -eq ".zip") {
        $unpackTo = "$targetFolder\$($file.BaseName)_unzipped"
        Unpack-ZipRecursive -zipPath $destination -outputFolder $unpackTo
        $globalLog += "[$(Get-Date)] UNZIPPED: $destination → $unpackTo"
    }

    # Add to manifest for the current folder
    $manifestPath = Join-Path $targetFolder "manifest.json"
    $manifest = @()

    if (Test-Path $manifestPath) {
        $manifest = Get-Content $manifestPath | ConvertFrom-Json
    }

    $manifest += [PSCustomObject]@{
        FileName     = $file.Name
        SHA256       = $hash
        MovedOn      = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
        OriginalPath = $file.FullName
    }

    $manifest | ConvertTo-Json -Depth 5 | Set-Content -Path $manifestPath -Force
}

# WRITE GLOBAL LOG
$globalLog | Out-File -FilePath $globalLogPath -Encoding UTF8 -Force
Write-Host "`n✅ All done. Full log written to: $globalLogPath"
