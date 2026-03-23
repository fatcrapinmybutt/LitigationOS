\
Param(
  [string]$TargetBat = "$(Resolve-Path ".\scripts\PIGGY_ONE_CLICK_RUN.bat")",
  [string]$IconIco   = "$(Resolve-Path ".\assets\piggy.ico")",
  [string]$ShortcutPath = "$(Join-Path ([Environment]::GetFolderPath('Desktop')) 'LitigationOS Scrape+Compile.lnk')"
)

$WScriptShell = New-Object -ComObject WScript.Shell
$Shortcut = $WScriptShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $TargetBat
$Shortcut.WorkingDirectory = (Split-Path $TargetBat)
$Shortcut.IconLocation = $IconIco
$Shortcut.Save()

Write-Output "OK: Created shortcut at $ShortcutPath"
