Param(
  [string]$RootId = "1nqkaatEssrhh8mTZceGaNvT7Ah5K_ryl",
  [string]$Dest = "$env:USERPROFILE\Downloads\LitigationOS\gdrive_mirror\EDS-USB"
)

New-Item -ItemType Directory -Force -Path $Dest | Out-Null

# Snapshot
rclone lsjson --recursive --hash --fast-list `
  --drive-root-folder-id $RootId `
  gdrive_sa: `
  | Out-File -Encoding utf8 "$Dest\remote_inventory.json"

# Copy with Drive export formats
rclone copy `
  --progress `
  --drive-root-folder-id $RootId `
  --drive-export-formats "pdf,docx,xlsx,pptx" `
  gdrive_sa: `
  "$Dest\mirror"

Write-Host "OK: $Dest"
