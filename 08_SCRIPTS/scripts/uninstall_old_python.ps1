
# Uninstall all Python versions, delete residual folders, and clean environment variables
Get-WmiObject -Class Win32_Product | Where-Object { $_.Name -like "Python*" } | ForEach-Object {
    Write-Output "Uninstalling $($_.Name)..."
    $_.Uninstall()
}

Start-Sleep -Seconds 10

$paths = @(
    "C:\Users\$env:USERNAME\AppData\Local\Programs\Python",
    "C:\Python*",
    "F:\Python*",
    "F:\Scripts",
    "C:\Users\$env:USERNAME\AppData\Roaming\Python",
    "$env:LOCALAPPDATA\Programs\Python",
    "$env:LOCALAPPDATA\pip"
)

foreach ($path in $paths) {
    if (Test-Path $path) {
        Write-Output "Deleting: $path"
        Remove-Item -Recurse -Force -Path $path
    }
}

$envVars = [System.Environment]::GetEnvironmentVariable("Path", [System.EnvironmentVariableTarget]::User)
$cleanedVars = $envVars -split ";" | Where-Object { $_ -notmatch "Python|Scripts" }
[System.Environment]::SetEnvironmentVariable("Path", ($cleanedVars -join ";"), [System.EnvironmentVariableTarget]::User)

Write-Output "✅ All old Python versions and related paths removed."
