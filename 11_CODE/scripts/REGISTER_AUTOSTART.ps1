
# Register Litigation OS Tray for Windows auto-start
$startup = [Environment]::GetFolderPath("Startup")
$target = Join-Path $startup "Litigation_OS_Tray.lnk"

$wsh = New-Object -ComObject WScript.Shell
$shortcut = $wsh.CreateShortcut($target)
$shortcut.TargetPath = Join-Path $PSScriptRoot "LITIGATION_OS_TRAY.bat"
$shortcut.WorkingDirectory = $PSScriptRoot
$shortcut.Save()

Write-Host "Litigation OS Tray registered for auto-start."
