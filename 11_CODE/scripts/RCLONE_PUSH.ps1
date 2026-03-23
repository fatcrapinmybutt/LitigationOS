# RCLONE_PUSH.ps1
# Sync OUTPUTS to Google Drive remote named "gdrive"
rclone copy \"F:\\LITIGATION_OS\\OUTPUTS\" \"gdrive:LITIGATION_OS$/OUTPUTS\" --checksum --log-file=\"F:\\LITIGATION_OS\\SYSTEM\\logs\\rclone_push.log\"
