
# Litigation OS Tray Controller
# Provides tray icon with Start/Stop/Quit controls

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$icon = New-Object System.Windows.Forms.NotifyIcon
$icon.Icon = [System.Drawing.SystemIcons]::Application
$icon.Text = "Litigation OS"
$icon.Visible = $true

$menu = New-Object System.Windows.Forms.ContextMenuStrip

$startItem = $menu.Items.Add("Start Litigation OS")
$stopItem  = $menu.Items.Add("Stop Litigation OS")
$exitItem  = $menu.Items.Add("Exit Tray")

$startItem.Add_Click({
    Start-Process powershell -ArgumentList "-ExecutionPolicy Bypass -File `"$PSScriptRoot\start_litigation_os.ps1`""
})

$stopItem.Add_Click({
    docker compose down
    [System.Windows.Forms.MessageBox]::Show("Litigation OS stopped.","Litigation OS")
})

$exitItem.Add_Click({
    docker compose down
    $icon.Visible = $false
    $icon.Dispose()
    [System.Windows.Forms.Application]::Exit()
})

$icon.ContextMenuStrip = $menu

[System.Windows.Forms.Application]::Run()
