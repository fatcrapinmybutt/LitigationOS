# Simple H:\ Drive Scanner
$ErrorActionPreference = "Continue"
$outputDir = "C:\users\andre\LITIGATIONOS_MASTER\OMNI_HARVEST_20260216_0357\00_MANIFESTS"

# Ensure output directory exists
New-Item -ItemType Directory -Path $outputDir -Force -ErrorAction SilentlyContinue | Out-Null

Write-Output "Starting H:\ drive scan..."
Write-Output "Output: $outputDir"

# Check if H:\ exists
if (-not (Test-Path "H:\")) {
    Write-Output "ERROR: H:\ drive not accessible"
    Write-Output "Available drives:"
    Get-PSDrive -PSProvider FileSystem | Format-Table Name, Root -AutoSize
    exit 1
}

Write-Output "H:\ drive found. Scanning..."

# Scan with progress
$results = @()
$extensions = @('*.pdf', '*.txt', '*.md')

foreach ($ext in $extensions) {
    Write-Output "Scanning for $ext..."
    $files = @(Get-ChildItem -Path "H:\" -Filter $ext -Recurse -File -ErrorAction SilentlyContinue)
    Write-Output "  Found: $($files.Count) files"
    
    foreach ($f in $files) {
        $results += [PSCustomObject]@{
            FilePath = $f.FullName
            FileName = $f.Name
            Extension = $f.Extension.TrimStart('.').ToLower()
            SizeBytes = $f.Length
            SizeMB = [math]::Round($f.Length / 1MB, 2)
            DateModified = $f.LastWriteTime
            Directory = $f.DirectoryName
        }
    }
}

Write-Output "Total files found: $($results.Count)"

if ($results.Count -eq 0) {
    Write-Output "No files found. Exiting."
    exit 0
}

# Export manifests
$results | Export-Csv "$outputDir\H_DRIVE_COMPLETE_MANIFEST.csv" -NoTypeInformation
$results | Where-Object {$_.Extension -eq 'pdf'} | Export-Csv "$outputDir\H_DRIVE_PDFS.csv" -NoTypeInformation
$results | Where-Object {$_.Extension -eq 'txt'} | Export-Csv "$outputDir\H_DRIVE_TXT.csv" -NoTypeInformation
$results | Where-Object {$_.Extension -eq 'md'} | Export-Csv "$outputDir\H_DRIVE_MD.csv" -NoTypeInformation

# Priority files (top 100 by size and recency)
$priority = $results | ForEach-Object {
    $daysOld = ((Get-Date) - $_.DateModified).TotalDays
    $score = ([math]::Max(0, 1000 - $daysOld)) + ($_.SizeMB * 10)
    $_ | Add-Member -NotePropertyName "PriorityScore" -NotePropertyValue $score -PassThru
} | Sort-Object PriorityScore -Descending | Select-Object -First 100

$priority | Export-Csv "$outputDir\H_DRIVE_PRIORITY_FILES.csv" -NoTypeInformation

Write-Output "SUCCESS: All manifests created"
Write-Output "Files: H_DRIVE_COMPLETE_MANIFEST.csv, H_DRIVE_PDFS.csv, H_DRIVE_TXT.csv, H_DRIVE_MD.csv, H_DRIVE_PRIORITY_FILES.csv"
