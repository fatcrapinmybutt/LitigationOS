# FRED-PRIME OS EXE BUILDER
Write-Host "🔧 Starting FRED-PRIME .exe Build Process..." -ForegroundColor Cyan

# Ensure pyinstaller is installed
Write-Host "🧪 Checking for PyInstaller..." -ForegroundColor Yellow
pip show pyinstaller > $null
if ($LASTEXITCODE -ne 0) {
    Write-Host "📦 Installing PyInstaller..." -ForegroundColor Yellow
    pip install pyinstaller
}

# Set paths
$script = "F:\FRED-PRIME\fred_os_organizer.py"
$dist = "F:\FRED-PRIME\dist"
$output = "F:\FRED-PRIME\FRED_OS_ASSEMBLER.exe"

# Build with PyInstaller
Write-Host "⚙️ Compiling with PyInstaller..." -ForegroundColor Yellow
pyinstaller --onefile --distpath "$dist" --workpath "$env:TEMP\build" --specpath "$env:TEMP\spec" "$script"

# Rename and move .exe
if (Test-Path "$dist\fred_os_organizer.exe") {
    Rename-Item -Path "$dist\fred_os_organizer.exe" -NewName "FRED_OS_ASSEMBLER.exe"
    Move-Item -Path "$dist\FRED_OS_ASSEMBLER.exe" -Destination "F:\FRED-PRIME\FRED_OS_ASSEMBLER.exe" -Force
    Write-Host "✅ Build complete: FRED_OS_ASSEMBLER.exe is ready." -ForegroundColor Green
} else {
    Write-Host "❌ Build failed. fred_os_organizer.exe not found." -ForegroundColor Red
}