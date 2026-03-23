# P1 Verification Script
# Wrapper for the Python test
Write-Host "Running P1 Sandbox Verification..."
$pythonPath = "python" # Assume python is in path
$testScript = "$PSScriptRoot\..\tests\test_p1.py"

# Execute
& $pythonPath $testScript
if ($LASTEXITCODE -eq 0) {
    Write-Host "P1 VERIFIED"
    exit 0
} else {
    Write-Host "P1 FAILED"
    exit 1
}

