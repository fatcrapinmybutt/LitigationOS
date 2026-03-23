# PowerShell script to copy generated artifacts to F:\Litigation_OS\MCR_20251001\
$src = "/mnt/data/mcr_outputs"
$destRoot = "F:\Litigation_OS\MCR_20251001\"
New-Item -ItemType Directory -Path $destRoot -Force | Out-Null
Get-ChildItem -Path "/mnt/data/mcr_outputs" -File | ForEach-Object {
    $dest = Join-Path $destRoot $_.Name
    Copy-Item -Path $_.FullName -Destination $dest -Force
    Write-Output ("Copied {0} -> {1}" -f $_.FullName, $dest)
}
Write-Output "All artifacts copied to $destRoot (if F: is available)."
