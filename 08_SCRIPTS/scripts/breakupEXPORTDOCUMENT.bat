@echo off
setlocal enabledelayedexpansion

:: === CONFIGURABLE OPTIONS ===
set ZIP_PATH=F:\chatgpt_export.zip
set OUTPUT_DIR=F:\ChatGPT_Packaged
set MAX_CHUNK_MB=100

:: === Create output directory if not exists ===
if not exist "%OUTPUT_DIR%" (
    echo Creating output directory at: %OUTPUT_DIR%
    mkdir "%OUTPUT_DIR%"
)

:: === Execute PowerShell command ===
echo Running PowerShell packaging script...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "& {
        param($zipPath, $outDir, $chunkMB)

        if (!(Test-Path $zipPath)) {
            Write-Error '❌ ZIP file not found.'
            exit 1
        }

        if (!(Test-Path $outDir)) {
            New-Item -ItemType Directory -Path $outDir | Out-Null
        }

        $hash = Get-FileHash -Path $zipPath -Algorithm SHA256
        Write-Host '✅ SHA-256 Hash: ' + $hash.Hash

        $timestamp = (Get-Date -Format 'yyyyMMdd_HHmmss')
        $baseName = 'ChatGPT_Export_' + $timestamp
        $destZip = Join-Path $outDir ($baseName + '.zip')

        Copy-Item -Path $zipPath -Destination $destZip -Force
        Write-Host '📦 Copied to: ' + $destZip

        if ($chunkMB -gt 0) {
            Write-Host '📤 Splitting ZIP into parts of ' + $chunkMB + ' MB...'
            $chunkSize = $chunkMB * 1MB
            $buffer = New-Object byte[] $chunkSize
            $i = 0
            $fs = [System.IO.File]::OpenRead($destZip)

            while (($read = $fs.Read($buffer, 0, $buffer.Length)) -gt 0) {
                $partName = '{0}.part{1:D3}' -f $destZip, $i
                $outStream = [System.IO.File]::OpenWrite($partName)
                $outStream.Write($buffer, 0, $read)
                $outStream.Close()
                Write-Host '➡️ Created: ' + $partName
                $i++
            }
            $fs.Close()
            Remove-Item -Path $destZip -Force
            Write-Host '🧹 Original ZIP deleted after split.'
        }

        Write-Host '🎉 All done!'
    } -zipPath '%ZIP_PATH%' -outDir '%OUTPUT_DIR%' -chunkMB %MAX_CHUNK_MB%"

pause
