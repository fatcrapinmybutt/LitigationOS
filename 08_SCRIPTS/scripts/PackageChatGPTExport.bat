@echo off
setlocal enabledelayedexpansion

:: === CONFIGURATION ===
set "ZIP_PATH=F:\EXPORTED CHAT GPT.zip"
set "OUTPUT_DIR=F:\ChatGPT_Packaged"
set "MAX_CHUNK_MB=30"

:: === PRE-CHECK ===
if not exist "%ZIP_PATH%" (
    echo ❌ File not found at: %ZIP_PATH%
    pause
    exit /b
)

if not exist "%OUTPUT_DIR%" (
    echo 📁 Creating output directory: %OUTPUT_DIR%
    mkdir "%OUTPUT_DIR%"
)

:: === EXECUTE POWERFUL SPLITTING SCRIPT ===
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
"& {
    param($zipPath, $outDir, $chunkMB)

    $chunkSize = $chunkMB * 1MB
    $timestamp = (Get-Date -Format 'yyyyMMdd_HHmmss')
    $baseName = 'ChatGPT_Export_' + $timestamp
    $destZip = Join-Path $outDir ($baseName + '.zip')

    Copy-Item -Path $zipPath -Destination $destZip -Force
    Write-Host '📦 Copied ZIP to:' $destZip

    $buffer = New-Object byte[] $chunkSize
    $i = 0
    $fs = [System.IO.File]::OpenRead($destZip)

    while (($read = $fs.Read($buffer, 0, $chunkSize)) -gt 0) {
        $partName = ('{0}.part{1:D3}' -f $baseName, $i)
        $partPath = Join-Path $outDir $partName
        [System.IO.File]::WriteAllBytes($partPath, $buffer[0..($read-1)])
        Write-Host ('➡️ Created part file: ' + $partPath)

        $zipName = ('Part_{0:D3}.zip' -f $i)
        $zipPath = Join-Path $outDir $zipName
        Compress-Archive -Path $partPath -DestinationPath $zipPath -Force
        Write-Host ('🗜️  Zipped to: ' + $zipPath)

        Remove-Item $partPath -Force
        $i++
    }

    $fs.Close()
    Remove-Item $destZip -Force
    Write-Host '🧹 Original ZIP removed after split.'
    Write-Host '✅ All chunks created and zipped into: ' + $outDir
} -zipPath '%ZIP_PATH%' -outDir '%OUTPUT_DIR%' -chunkMB %MAX_CHUNK_MB%"

pause
