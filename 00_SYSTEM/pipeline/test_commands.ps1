Set-Location 'C:\Users\andre\scans\tooling\'
Write-Host "Working directory: $(Get-Location)"
Write-Host ""

Write-Host "=== COMMAND 1: python -c `"print('hello')`" ===" -ForegroundColor Green
try {
    $output = & python -c "print('hello')" 2>&1
    Write-Host "OUTPUT: $output"
    Write-Host "EXIT CODE: $LASTEXITCODE"
} catch {
    Write-Host "ERROR: $_"
}
Write-Host ""

Write-Host "=== COMMAND 2: config import ===" -ForegroundColor Green
try {
    $output = & python -c "import sys; sys.path.insert(0,'.'); import config; print('config OK')" 2>&1
    Write-Host "OUTPUT: $output"
    Write-Host "EXIT CODE: $LASTEXITCODE"
} catch {
    Write-Host "ERROR: $_"
}
Write-Host ""

Write-Host "=== COMMAND 3: safety import ===" -ForegroundColor Green
try {
    $output = & python -c "import sys; sys.path.insert(0,'.'); import safety; print('safety OK')" 2>&1
    Write-Host "OUTPUT: $output"
    Write-Host "EXIT CODE: $LASTEXITCODE"
} catch {
    Write-Host "ERROR: $_"
}
Write-Host ""

Write-Host "=== COMMAND 4: run_omega_pipeline import ===" -ForegroundColor Green
try {
    $output = & python -c "import sys; sys.path.insert(0,'.'); import run_omega_pipeline; print('orchestrator OK')" 2>&1
    Write-Host "OUTPUT: $output"
    Write-Host "EXIT CODE: $LASTEXITCODE"
} catch {
    Write-Host "ERROR: $_"
}
Write-Host ""

Write-Host "=== COMMAND 5: python run_omega_pipeline.py --list-phases ===" -ForegroundColor Green
try {
    $output = & python run_omega_pipeline.py --list-phases 2>&1
    Write-Host "OUTPUT:"
    Write-Host $output
    Write-Host "EXIT CODE: $LASTEXITCODE"
} catch {
    Write-Host "ERROR: $_"
}
Write-Host ""

Write-Host "=== COMMAND 6: python run_omega_pipeline.py --dry-run --create-snapshot (30s timeout) ===" -ForegroundColor Green
try {
    $proc = Start-Process -FilePath python -ArgumentList 'run_omega_pipeline.py', '--dry-run', '--create-snapshot' -NoNewWindow -PassThru
    $procId = $proc.Id
    Write-Host "Process started with ID: $procId"
    
    $exited = $proc.WaitForExit(30000)
    if ($exited) {
        Write-Host "Process completed. Exit code: $($proc.ExitCode)"
    } else {
        Write-Host "Process TIMEOUT after 30 seconds"
        Write-Host "Terminating process ID: $procId"
        $proc.Kill()
    }
} catch {
    Write-Host "ERROR: $_"
}
