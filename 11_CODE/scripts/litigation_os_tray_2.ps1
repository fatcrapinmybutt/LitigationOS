
# Litigation OS Tray Controller with Health Indicator + Auto-Start + Notifications
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

$global:lastState = "Unknown"

function Notify($title, $msg) {
    $icon.BalloonTipTitle = $title
    $icon.BalloonTipText  = $msg
    $icon.ShowBalloonTip(3000)
}

function Update-Health {
    try {
        $names = docker ps --format "{{.Names}}"
        if ($names -match "litigationos-neo4j") {
            if ($global:lastState -ne "Running") {
                Notify "Litigation OS" "System is now RUNNING."
                $global:lastState = "Running"
            }
            $icon.Text = "Litigation OS (Running)"
            $healthItem.Text = "Health: Running"
        } else {
            if ($global:lastState -ne "Stopped") {
                Notify "Litigation OS" "System is STOPPED."
                $global:lastState = "Stopped"
            }
            $icon.Text = "Litigation OS (Stopped)"
            $healthItem.Text = "Health: Stopped"
        }
    } catch {
        if ($global:lastState -ne "Docker Offline") {
            Notify "Litigation OS" "Docker is OFFLINE."
            $global:lastState = "Docker Offline"
        }
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
