# FRED-COMPLIANT ORGANIZER v2.1 – ANDREW J. PIGORS SYSTEM
# FINALIZED FOR FIELD USE – FULLY LITIGATION-AWARE

# CONFIG
$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptRoot

$sourcePath = "F:\"                     # Update as needed
$destinationRoot = "F:\LLC_Litigation_Archive"
$includeExtensions = ".pdf", ".docx", ".doc", ".txt", ".rtf", ".xlsx", ".zip"
$hashMap = @{}
$globalLog = @()

# ENSURE DESTINATION ROOT EXISTS
if (!(Test-Path $destinationRoot)) {
    New-Item -Path $destinationRoot -ItemType Directory -Force
}

# TIMESTAMPING
$timestamp = Get-Date -Format "yyyy-MM-dd_HHmmss"
$globalLogPath = Join-Path $destinationRoot "LLC_Organizer_Log_$timestamp.txt"
$logJsonPath = Join-Path $destinationRoot "Execution_Log_$timestamp.json"
$masterManifestPath = Join-Path $destinationRoot "MASTER_MANIFEST.json"
if (!(Test-Path $masterManifestPath)) { @() | ConvertTo-Json | Set-Content -Path $masterManifestPath }

# CATEGORY DETECTION FUNCTION
function Get-UseCategory {
    param($name, $content)
    $text = "$name $content".ToLower()
    switch -regex ($text) {
        "lease|rent|agreement"         { return "Lease_Agreements" }
        "invoice|payment|billing|due"  { return "Financial_Records" }
        "email|communication|message"  { return "Correspondence" }
        "court|motion|filing|show cause|hearing|custody|contempt|order" { return "Legal_Filings" }
        "repair|maintenance|leak|sewage|mold|egle|violation" { return "Property_Issues" }
        default                        { return "Manual_Review" }
    }
}

# FILE HASHING FUNCTION
function Get-FileHashSafe {
    param($file)
    try {
        return (Get-FileHash -Path $file -Algorithm SHA256).Hash
    } catch {
        Write-Warning "Cannot hash: $file"
        return $null
    }
}

# ZIP EXTRACTION FUNCTION
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

# MAIN FILE PROCESSING
$files = Get-ChildItem -Path $sourcePath -Recurse -File -Include $includeExtensions -ErrorAction SilentlyContinue

foreach ($file in $files) {
    $hash = Get-FileHashSafe -file $file.FullName
    if (-not $hash -or $hashMap.ContainsKey($hash)) { continue }

    $hashMap[$hash] = $true
    $preview = ""
    if ($file.Extension -match "\.txt|\.docx|\.rtf") {
        try { $preview = Get-Content -Path $file.FullName -TotalCount 15 -Raw } catch {}
    }

    $category = Get-UseCategory -name $file.Name -content $preview
    $targetFolder = Join-Path $destinationRoot $category
    if (!(Test-Path $targetFolder)) {
        New-Item -Path $targetFolder -ItemType Directory -Force
        Set-Content -Path (Join-Path $targetFolder "README.txt") -Value "Auto-classified by litigation system on $timestamp. Maintain file integrity. Do not delete unless directed."
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

    # ZIP HANDLER
    if ($file.Extension -eq ".zip") {
        $unpackTo = "$targetFolder\$($file.BaseName)_unzipped"
        Unpack-ZipRecursive -zipPath $destination -outputFolder $unpackTo
        $globalLog += "[$(Get-Date)] UNZIPPED: $destination → $unpackTo"
    }

    # INDIVIDUAL CATEGORY MANIFEST
    $manifestPath = Join-Path $targetFolder "manifest.json"
    $manifest = @()
    if (Test-Path $manifestPath) {
        $manifest = Get-Content $manifestPath | ConvertFrom-Json
    }

    $entry = [PSCustomObject]@{
        FileName     = $file.Name
        SHA256       = $hash
        MovedOn      = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
        OriginalPath = $file.FullName
    }

    $manifest += $entry
    $manifest | ConvertTo-Json -Depth 5 | Set-Content -Path $manifestPath -Force

    # Append to master manifest
    $master = Get-Content $masterManifestPath | ConvertFrom-Json
    $master += $entry
    $master | ConvertTo-Json -Depth 5 | Set-Content -Path $masterManifestPath
}

# FINAL LOG WRITEOUTS
$globalLog | Out-File -FilePath $globalLogPath -Encoding UTF8 -Force
$globalLog | ConvertTo-Json -Depth 3 | Out-File -FilePath $logJsonPath -Encoding UTF8

Write-Host "`n✅ SYSTEM COMPLETE. Logs saved to:`n- $globalLogPath`n- $logJsonPath"
