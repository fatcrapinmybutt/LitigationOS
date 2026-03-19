$watchPath = "F:\FRED_EVIDENCE"
$tailGlobalLog = $true
$categoryCount = @{}
$manifestHashSet = @{}

Write-Host "`n📡 LITIGATION MONITOR – FRED_CEPS_SUPREME ACTIVE"
Write-Host "🧠 Watching: $watchPath"

# Load all known hashes from manifest.json files
$manifests = Get-ChildItem -Path $watchPath -Recurse -Filter manifest.json -ErrorAction SilentlyContinue

foreach ($manifestFile in $manifests) {
    try {
        $data = Get-Content $manifestFile.FullName | ConvertFrom-Json
        foreach ($entry in $data) {
            if ($entry.SHA256 -and !$manifestHashSet.ContainsKey($entry.SHA256)) {
                $manifestHashSet[$entry.SHA256] = $true
            }
        }
    } catch {
        Write-Warning "⚠️ Could not parse manifest: $($manifestFile.FullName)"
    }
}

# Real-time file creation detection
$watcher = New-Object IO.FileSystemWatcher $watchPath -Property @{
    IncludeSubdirectories = $true
    EnableRaisingEvents   = $true
}

Register-ObjectEvent -InputObject $watcher -EventName Created -Action {
    $path = $Event.SourceEventArgs.FullPath
    $category = ($path -replace [regex]::Escape("$watchPath\"), "").Split('\')[0]

    if ($categoryCount.ContainsKey($category)) {
        $categoryCount[$category]++
    } else {
        $categoryCount[$category] = 1
    }

    Write-Host "[CREATED] $path"

    # Check for hash presence in manifest
    try {
        $hash = (Get-FileHash -Path $path -Algorithm SHA256).Hash
        if ($manifestHashSet.ContainsKey($hash)) {
            Write-Warning "⚠️ Duplicate SHA256 detected in: $path"
        } else {
            $manifestHashSet[$hash] = $true
        }
    } catch {
        Write-Warning "⚠️ Could not hash: $path"
    }
} | Out-Null

# Live tail of GLOBAL_EVIDENCE_LOG
if ($tailGlobalLog) {
    $logFile = Get-ChildItem "$watchPath\GLOBAL_EVIDENCE_LOG_*.txt" -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending | Select-Object -First 1

    if ($logFile) {
        Write-Host "`n📖 Tailing Log: $($logFile.FullName)`n"
        Start-Job -ScriptBlock {
            Get-Content $using:logFile.FullName -Wait -Tail 20
        } | Out-Null
    } else {
        Write-Warning "No GLOBAL_EVIDENCE_LOG found yet. Tailer will wait..."
    }
}

# Display live stats every 10 seconds
while ($true) {
    Start-Sleep -Seconds 10
    Clear-Host
    Write-Host "📊 LIVE CATEGORY COUNTS (updated @ $(Get-Date -Format 'HH:mm:ss')):`n"
    foreach ($key in ($categoryCount.Keys | Sort-Object)) {
        Write-Host ("{0,-30} : {1,3}" -f $key, $categoryCount[$key])
    }

    Write-Host "`n🔁 Monitoring $watchPath ... Press [Ctrl+C] to stop."
}
