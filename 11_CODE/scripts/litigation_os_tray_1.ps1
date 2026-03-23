
# Litigation OS Tray Controller with Health Indicator + Auto-Start
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$icon = New-Object System.Windows.Forms.NotifyIcon
$icon.Icon = [System.Drawing.SystemIcons]::Application
$icon.Text = "Litigation OS (Initializing)"
$icon.Visible = $true

$menu = New-Object System.Windows.Forms.ContextMenuStrip
$startItem = $menu.Items.Add("Start Litigation OS")
$stopItem  = $menu.Items.Add("Stop Litigation OS")
$healthItem = $menu.Items.Add("Health: Unknown")
$exitItem  = $menu.Items.Add("Exit Tray")

function Update-Health {
    try {
        docker ps --format "{{.Names}}" | Out-String | ForEach-Object {
            if ($_ -match "litigationos-neo4j") {
                $icon.Text = "Litigation OS (Running)"
                $healthItem.Text = "Health: Running"
            } else {
                $icon.Text = "Litigation OS (Stopped)"
                $healthItem.Text = "Health: Stopped"
            }
        }
    } catch {
        $icon.Text = "Litigation OS (Docker Offline)"
        $healthItem.Text = "Health: Docker Offline"
    }
}

$timer = New-Object System.Windows.Forms.Timer
$timer.Interval = 5000
$timer.Add_Tick({ Update-Health })
$timer.Start()

$startItem.Add_Click({
    Start-Process powershell -ArgumentList "-ExecutionPolicy Bypass -File `"$PSScriptRoot\start_litigation_os.ps1`""
})

$stopItem.Add_Click({
    docker compose down
    Update-Health
})

$exitItem.Add_Click({
    docker compose down
    $timer.Stop()
    $icon.Visible = $false
    $icon.Dispose()
    [System.Windows.Forms.Application]::Exit()
})

$icon.ContextMenuStrip = $menu
Update-Health
[System.Windows.Forms.Application]::Run()
