# Step 1: Delete files and directories
Write-Host "=== STEP 1: Deleting files and directories ===" -ForegroundColor Cyan
$items_to_delete = @("test_commands.bat", "test_commands.ps1", "__pycache__")
foreach ($item in $items_to_delete) {
    if (Test-Path $item) {
        if (Test-Path $item -PathType Container) {
            Remove-Item $item -Recurse -Force
            Write-Host "✓ Deleted directory: $item" -ForegroundColor Green
        } else {
            Remove-Item $item -Force
            Write-Host "✓ Deleted file: $item" -ForegroundColor Green
        }
    } else {
        Write-Host "✗ Not found: $item" -ForegroundColor Yellow
    }
}

# Step 2: Find all .py files
Write-Host "`n=== STEP 2: Finding all .py files ===" -ForegroundColor Cyan
$py_files = Get-ChildItem -Path . -Filter "*.py" -File | Sort-Object Name
Write-Host "Found $($py_files.Count) Python files:"
$py_files | ForEach-Object { Write-Host "  $($_.Name)" }

# Step 3: Syntax checking all .py files
Write-Host "`n=== STEP 3: Syntax checking all .py files ===" -ForegroundColor Cyan
$syntax_errors = @()
foreach ($file in $py_files) {
    $file_short = $file.Name
    $full_path = $file.FullName
    python -c "import py_compile; py_compile.compile(r'$full_path', doraise=True)" 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ $file_short" -ForegroundColor Green
    } else {
        Write-Host "✗ $file_short - Exit code: $LASTEXITCODE" -ForegroundColor Red
        $syntax_errors += $file_short
    }
}

if ($syntax_errors.Count -gt 0) {
    Write-Host "`n⚠ SYNTAX ERRORS FOUND in: $($syntax_errors -join ', ')" -ForegroundColor Red
} else {
    Write-Host "`n✓ All .py files passed syntax check" -ForegroundColor Green
}

# Step 4: Verifying phase1_inventory.py
Write-Host "`n=== STEP 4: Verifying phase1_inventory.py ===" -ForegroundColor Cyan
$output = python -c "import sys; sys.path.insert(0,r'C:\Users\andre\scans\tooling'); import phase1_inventory; print('phase1 OK')" 2>&1
Write-Host $output
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ phase1_inventory.py verified" -ForegroundColor Green
} else {
    Write-Host "✗ phase1_inventory.py import failed - Exit code: $LASTEXITCODE" -ForegroundColor Red
}

Write-Host "`n=== COMPLETE ===" -ForegroundColor Cyan
