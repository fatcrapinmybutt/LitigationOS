Add-Type -AssemblyName PresentationFramework

$XAML = @"
<Window xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
        Title="Duplicate Finder Progress" Height="160" Width="420"
        WindowStartupLocation="CenterScreen" ResizeMode="NoResize">
    <Grid Margin="10">
        <TextBlock Name="StatusText" FontSize="14" Margin="0,0,0,10" Text="Starting scan..."/>
        <ProgressBar Name="MainProgressBar" Height="25" Minimum="0" Maximum="100" Margin="0,40,0,0"/>
    </Grid>
</Window>
"@

$reader = New-Object System.Xml.XmlNodeReader ([xml]$XAML)
$gui = [Windows.Markup.XamlReader]::Load($reader)
$ProgressBar = $gui.FindName("MainProgressBar")
$StatusText = $gui.FindName("StatusText")

Start-Job -ScriptBlock {
    $syncHash = $using:gui.Dispatcher.Invoke([scriptblock]{
        [hashtable]::Synchronized(@{
            Bar = $using:ProgressBar
            Text = $using:StatusText
        })
    })

    function Set-Progress($pct, $text) {
        $syncHash.Text.Dispatcher.Invoke([action]{
            $syncHash.Text.Text = $text
            $syncHash.Bar.Value = $pct
        })
    }

    $Drives = @("C:\", "D:\", "F:\")
    $OutputCsv = "$env:USERPROFILE\Desktop\DuplicateFilesReport.csv"
    $DeleteMode = $false

    function Get-FileHashSafe {
        param($filePath)
        try { Get-FileHash -Path $filePath -Algorithm SHA256 } catch { $null }
    }

    function Test-FileReadable {
        param([string]$Path)
        try {
            if ((Get-Item $Path).Length -eq 0) { return $false }
            $stream = [System.IO.File]::Open($Path, 'Open', 'Read', 'Read')
            $stream.Close()
            return $true
        } catch { return $false }
    }

    $allFiles = @()
    foreach ($drive in $Drives) {
        try {
            $allFiles += Get-ChildItem -Path $drive -Recurse -File -ErrorAction SilentlyContinue
        } catch {}
    }

    $sizeGroups = $allFiles | Group-Object Length | Where-Object { $_.Count -gt 1 }
    $duplicateResults = @()
    $totalGroups = $sizeGroups.Count
    $groupIndex = 0

    foreach ($group in $sizeGroups) {
        $groupIndex++
        $pct = [math]::Round(($groupIndex / $totalGroups) * 100, 1)
        Set-Progress -pct $pct -text "Processing group $groupIndex of $totalGroups..."

        $fileHashes = @{}
        foreach ($file in $group.Group) {
            $hashResult = Get-FileHashSafe -filePath $file.FullName
            if ($hashResult) {
                $hash = $hashResult.Hash
                if (-not $fileHashes.ContainsKey($hash)) { $fileHashes[$hash] = @() }
                $fileHashes[$hash] += $file.FullName
            }
        }

        foreach ($hash in $fileHashes.Keys) {
            if ($fileHashes[$hash].Count -gt 1) {
                $files = $fileHashes[$hash]
                $keeper = $files | Where-Object { Test-FileReadable $_ } | Select-Object -First 1
                if (-not $keeper) { continue }
                $toDelete = $files | Where-Object { $_ -ne $keeper }

                if ($DeleteMode) {
                    foreach ($path in $toDelete) {
                        try { Remove-Item -Path $path -Force } catch {}
                    }
                }

                $duplicateResults += [PSCustomObject]@{
                    Hash  = $hash
                    Size  = $group.Name
                    Count = $files.Count
                    Files = ($files -join "`n")
                }
            }
        }
    }

    $duplicateResults | Select-Object Hash, Size, Count, Files |
        Export-Csv -Path $OutputCsv -NoTypeInformation -Encoding UTF8

    Set-Progress -pct 100 -text "✅ Done! Saved to $OutputCsv"

} | Out-Null

$gui.ShowDialog() | Out-Null
