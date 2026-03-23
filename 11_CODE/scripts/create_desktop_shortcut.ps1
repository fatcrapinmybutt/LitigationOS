param(
  [string]$ExePath = "$PSScriptRoot\..\dist\LitigationOS\LitigationOS.exe",
  [string]$ShortcutName = "LitigationOS.lnk"
)
$ExePath = (Resolve-Path $ExePath).Path
$Desktop = [Environment]::GetFolderPath("Desktop")
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut((Join-Path $Desktop $ShortcutName))
$Shortcut.TargetPath = $ExePath
$Shortcut.WorkingDirectory = (Split-Path $ExePath -Parent)
$Shortcut.Save()
Write-Host "Shortcut created: $Desktop\$ShortcutName"
