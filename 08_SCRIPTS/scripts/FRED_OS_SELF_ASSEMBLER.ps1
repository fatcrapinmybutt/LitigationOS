# FRED-PRIME SELF-ASSEMBLER (PowerShell Bootstrap)
Write-Host "🔧 FRED-PRIME SELF-ASSEMBLER BOOTING..." -ForegroundColor Cyan

$pythonScript = "F:/FRED-PRIME/fred_os_organizer.py"

if (Test-Path $pythonScript) {
    Write-Host "📦 Found organizer. Launching Python system organizer..." -ForegroundColor Yellow
    python $pythonScript
} else {
    Write-Host "❌ Python script not found: fred_os_organizer.py" -ForegroundColor Red
    Write-Host "Please ensure it's located at F:/FRED-PRIME/"
}