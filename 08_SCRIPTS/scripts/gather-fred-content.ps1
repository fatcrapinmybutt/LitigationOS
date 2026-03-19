# PowerShell Script: gather-fred-content.ps1
# Description: Recursively searches all of F:\ for folders/files with "FRED" in the name
#              and copies them into F:\FRED_MASTER_COLLECTION safely.

$SourceRoot = "F:\"
$TargetRoot = "F:\FRED_MASTER_COLLECTION"

# Ensure the target directory exists
if (!(Test-Path $TargetRoot)) {
    New-Item -ItemType Directory -Path $TargetRoot | Out-Null
}

Write-Host "`n🔍 Scanning ENTIRE F:\ drive for 'FRED' folders and files..."

# Find all items with "FRED" in the name, excluding the destination itself
$items = Get-ChildItem -Path $SourceRoot -Recurse -Force -ErrorAction SilentlyContinue |
    Where-Object {
        $_.Name -match 'FRED' -and $_.FullName -notlike "$TargetRoot*"
    }

foreach ($item in $items) {
    try {
        $destination = Join-Path -Path $TargetRoot -ChildPath $item.Name

        if ($item.PSIsContainer) {
            Copy-Item -Path $item.FullName -Destination $destination -Recurse -Force
            Write-Host "[DIR] Copied: $($item.FullName) -> $destination"
        } else {
            Copy-Item -Path $item.FullName -Destination $destination -Force
            Write-Host "[FILE] Copied: $($item.FullName) -> $destination"
        }
    } catch {
        Write-Warning "❌ ERROR copying $($item.FullName): $($_.Exception.Message)"
    }
}

Write-Host "`n✅ FRED_MASTER_COLLECTION assembled at: $TargetRoot"
