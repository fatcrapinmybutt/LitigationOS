# Example: mount Google Drive via rclone and ingest
# Pre-req: rclone config named 'gdrive' already set up
# Run as Admin if using WinFSP mount
rclone mount gdrive: X: --vfs-cache-mode full --volname "GDriveLitigation" --network-mode

# After mount, in a new PowerShell:
#   Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/drive/ingest?path=X:\LITIGATION_INTAKE
