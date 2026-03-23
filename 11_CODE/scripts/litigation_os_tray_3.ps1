
# Litigation OS Tray Controller with Colored Status Icons
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$base = $PSScriptRoot
$icons = @{
    Running   = "$base\ICONS\status_running.ico"
    Stopped   = "$base\ICONS\status_stopped.ico"
    Starting  = "$base\ICONS\status_starting.ico"
    Offline   = "$base\ICONS\status_offline.ico"
}

$icon = New-Object System.Windows.Forms.NotifyIcon
$icon.Icon = New-Object System.Drawing.Icon($icons.Starting)
$icon.Text = "Litigation OS (Initializing)"
$icon.Visible = $true

$menu = New-Object System.Windows.Forms.ContextMenuStrip
$startItem = $menu.Items.Add("Start Litigation OS")
$stopItem  = $menu.Items.Add("Stop Litigation OS")
$healthItem = $menu.Items.Add("Health: Initializing")
$exitItem  = $menu.Items.Add("Exit Tray")

$global:lastState = "Starting"

function Set-State($state, $label) {
    if ($global:lastState -ne $state) {
        $icon.Icon = New-Object System.Drawing.Icon($icons[$state])
        $icon.Text = "Litigation OS ($label)"
        $healthItem.Text = "Health: $label"
        $global:lastState = $state
    }
}

function Update-Health {
    try {
        $names = docker ps --format "{{.Names}}"
        if ($names -match "litigationos-neo4j") {
            Set-State "Running" "Running"
        } else {
            Set-State "Stopped" "Stopped"
        }
    } catch {
        Set-State "Offline" "Docker Offline"
    }
}

$timer = New-Object System.Windows.Forms.Timer
$timer.Interval = 5000
$timer.Add_Tick({ Update-Health })
$timer.Start()

$startItem.Add_Click({
    Set-State "Starting" "Starting"
    Start-Process powershell -ArgumentList "-ExecutionPolicy Bypass -File `"$PSScriptRoot\start_litigation_os.ps1`""
})

$stopItem.Add_Click({
    docker compose down
    Set-State "Stopped" "Stopped"
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
