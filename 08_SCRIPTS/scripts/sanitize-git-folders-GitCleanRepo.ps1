# PowerShell Script: sanitize-git-folders-GitCleanRepo.ps1
param (
    [string]$TargetPath = "F:\GitCleanRepo"
)

Write-Host "Scanning and sanitizing folder/file names under: $TargetPath`n"

$invalidPattern = '[^a-zA-Z0-9 _.\-]'

# Rename Folders
Get-ChildItem -Path $TargetPath -Recurse -Directory | ForEach-Object {
    $newName = $_.Name -replace $invalidPattern, '_'
    if ($_.Name -ne $newName) {
        $newPath = Join-Path -Path $_.Parent.FullName -ChildPath $newName
        Rename-Item -Path $_.FullName -NewName $newName -Force
        Write-Host "[DIR] Renamed: $($_.FullName) -> $newPath"
    }
}

# Rename Files
Get-ChildItem -Path $TargetPath -Recurse -File | ForEach-Object {
    $newName = $_.Name -replace $invalidPattern, '_'
    if ($_.Name -ne $newName) {
        $newPath = Join-Path -Path $_.Directory.FullName -ChildPath $newName
        Rename-Item -Path $_.FullName -NewName $newName -Force
        Write-Host "[FILE] Renamed: $($_.FullName) -> $newPath"
    }
}

Write-Host "`nSanitization complete."
