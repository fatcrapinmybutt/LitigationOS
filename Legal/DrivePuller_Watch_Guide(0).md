# DrivePuller Watch

To keep your evidence index fresh:
1) Edit `scripts/schedule_drivepuller_watch.ps1` to set paths.
2) Run it in an elevated PowerShell. It creates a Windows Scheduled Task that POSTs
   to `/api/drive/ingest/bulk` hourly.

You can delete or modify the task anytime via Task Scheduler.
