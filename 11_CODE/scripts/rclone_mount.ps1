# Example rclone mounts. Adjust remote names and paths.
# Requires: rclone installed and remotes configured (rclone config)

# Google Drive to G:
# rclone mount gdrive: G: --vfs-cache-mode writes --network-mode

# Dropbox to D:
# rclone mount dropbox: D: --vfs-cache-mode writes --network-mode

# OneDrive to O:
# rclone mount onedrive: O: --vfs-cache-mode writes --network-mode

# To sync cloud to a local mirror folder (faster indexing):
# rclone sync gdrive:/Litigation C:\Data\Cloud\GDrive_Litigation --progress

Write-Host "Edit this file with your remotes, then run in an elevated PowerShell."
