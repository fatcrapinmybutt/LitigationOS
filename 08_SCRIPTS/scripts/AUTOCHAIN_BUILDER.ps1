
Write-Host "Creating folders for ULTIMATE-FRED-PRIME..." -ForegroundColor Green

$folders = @(
    "FRED-PRIME-AUTOCHAIN-GUI\_ENGINES\Motion_Packet_Generator_Engine",
    "FRED-PRIME-AUTOCHAIN-GUI\_ENGINES\Violation_Response_Engine",
    "FRED-PRIME-AUTOCHAIN-GUI\_CORES\Evidence_Weighing_Core",
    "FRED-PRIME-AUTOCHAIN-GUI\_WORKFLOWS\Contempt_Trigger_Workflow",
    "FRED-PRIME-AUTOCHAIN-GUI\_PLUGINS\AppClose_Analyzer_Plugin",
    "FRED-PRIME-AUTOCHAIN-GUI\_DASHBOARDS\Trigger_Heatmap_Dashboard",
    "FRED-PRIME-AUTOCHAIN-GUI\_PIPELINES\Statute_Breach_Pipeline",
    "FRED-PRIME-AUTOCHAIN-GUI\_MASTERLISTS\Case_Masterlist",
    "FRED-PRIME-AUTOCHAIN-GUI\_SYSTEMS\Test_Simulation_System",
    "FRED-PRIME-AUTOCHAIN-GUI\_SYSTEMS\Automation_Trigger_Daemon"
)

foreach ($folder in $folders) {
    New-Item -Path $folder -ItemType Directory -Force | Out-Null
    Write-Host "Created: $folder"
}

Write-Host "Done. Now manually paste the module_task.py files into each folder." -ForegroundColor Yellow
Pause
