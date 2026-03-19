# ==========================================================
# 📁 F:\ Drive Analyzer – MHLOP Grade / Safe Characters Only
# ==========================================================

$source = "F:\"
$output = "$env:TEMP\f_drive_analysis.txt"
$largeFileThreshold = 100MB

$report = @()
$totalSize = 0
$typeStats = @{}
$largeFiles = @()

Write-Host "[*] Scanning F:\ drive..."

try {
    $files = Get-ChildItem -Path $source -Recurse -File -ErrorAction Stop
} catch {
    Write-Host "[ERROR] Cannot scan F:\ - $_"
    exit
}

foreach ($file in $files) {
    $ext = ($file.Extension.ToLower() -replace '^\.', '')
    $sizeMB = [math]::Round($file.Length / 1MB, 2)
    $totalSize += $file.Length

    # Count extensions
    if ($ext -ne "") {
        if ($typeStats.ContainsKey($ext)) {
            $typeStats[$ext] += 1
        } else {
            $typeStats[$ext] = 1
        }
    }

    # Flag large files
    if ($file.Length -gt $largeFileThreshold) {
        $largeFiles += "$($file.FullName)  -  $sizeMB MB"
    }
}

# Summary
$report += "============================================================="
$report += "             F:\\ DRIVE ANALYSIS REPORT"
$report += "============================================================="
$report += "Path Scanned     : F:\"
$report += "Total Files      : $($files.Count)"
$report += "Total Size       : $([math]::Round($totalSize / 1GB, 2)) GB"
$report += ""

# Filetype Breakdown
$report += "File Type Breakdown (by extension):"
foreach ($key in ($typeStats.Keys | Sort-Object { $typeStats[$_] } -Descending)) {
    $report += "  .$key  : $($typeStats[$key]) file(s)"
}
$report += ""

# Large Files
$report += "Files Over ${largeFileThreshold} (100MB+):"
if ($largeFiles.Count -eq 0) {
    $report += "  None"
} else {
    $largeFiles | Sort-Object | ForEach-Object { $report += "  $_" }
}
$report += ""

# Timestamps
$report += "Oldest File      : $((($files | Sort-Object LastWriteTime)[0]).FullName)"
$report += "Newest File      : $((($files | Sort-Object LastWriteTime -Descending)[0]).FullName)"
$report += "Scan Completed   : $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
$report += "============================================================="

# Save to file and open
$report | Out-File -FilePath $output -Encoding UTF8
Start-Process notepad.exe $output
