<#
.SYNOPSIS
    MBP LitigationOS 2026 v1.0 - Master Launcher
.DESCRIPTION
    Comprehensive launcher for the LitigationOS platform.
    Supports: start, desktop, web, pipeline, train, evolve, analyze, status, help
    All components are 100% local. Zero network calls.
.EXAMPLE
    .\START.ps1 start       # Full system launch (backend + Electron)
    .\START.ps1 status      # Show system health dashboard
    .\START.ps1 analyze     # Run forensic + timeline analysis
    .\START.ps1 evolve 5    # Run 5 self-evolution cycles
#>

param(
    [Parameter(Position = 0)]
    [string]$Command = "help",

    [Parameter(Position = 1)]
    [string]$Arg1 = ""
)

# ==================================================================
# Configuration
# ==================================================================
$ErrorActionPreference = "Continue"
$Root       = $PSScriptRoot
$DB         = Join-Path $Root "litigation_context.db"
$Model      = "$Root\00_SYSTEM\local_model"
$ModelData  = "$Model\model_data"
$Desktop    = "$Root\08_APPS\desktop"
$Backend    = "$Desktop\backend"
$Electron   = "$Desktop\electron-app"
$Web        = "$Root\08_APPS\web"
$Pipeline   = "$Root\00_SYSTEM\pipeline"
$Analysis   = "$Root\00_SYSTEM\analysis"
$Config     = "$Root\litigationos.config.json"

# ==================================================================
# Helper: Banner
# ==================================================================
function Show-Banner {
    Write-Host ""
    Write-Host "+----------------------------------------------------------+" -ForegroundColor Cyan
    Write-Host "|    MBP LitigationOS 2026 v1.0 - Master Launcher         |" -ForegroundColor Cyan
    Write-Host "|    Pigors v. Watson | Michigan Family Law                |" -ForegroundColor Cyan
    Write-Host "|    100% Local | Zero Network | Cannot Fail               |" -ForegroundColor Cyan
    Write-Host "+----------------------------------------------------------+" -ForegroundColor Cyan
    Write-Host ""
}

# ==================================================================
# Helper: Formatted output
# ==================================================================
function Write-OK   { param([string]$Msg) Write-Host "  [OK]   $Msg" -ForegroundColor Green }
function Write-Warn { param([string]$Msg) Write-Host "  [WARN] $Msg" -ForegroundColor Yellow }
function Write-Fail { param([string]$Msg) Write-Host "  [FAIL] $Msg" -ForegroundColor Red }
function Write-Info { param([string]$Msg) Write-Host "  [INFO] $Msg" -ForegroundColor Cyan }
function Write-Step { param([string]$Msg) Write-Host "`n-- $Msg --" -ForegroundColor Yellow }

# ==================================================================
# Helper: Check database health
# ==================================================================
function Test-Database {
    if (-not (Test-Path $DB)) {
        Write-Fail "Database not found at $DB"
        Write-Warn "Run:  .\START.ps1 pipeline"
        return $false
    }
    $dbSize = [math]::Round((Get-Item $DB).Length / 1MB, 1)
    Write-OK "Database: $DB (${dbSize} MB)"
    try {
        $stats = python -c "
import sqlite3, json
c = sqlite3.connect(r'$DB', timeout=10)
c.execute('PRAGMA journal_mode=WAL')
tables = c.execute(`"SELECT COUNT(*) FROM sqlite_master WHERE type='table'`").fetchone()[0]
rows = 0
for t in c.execute(`"SELECT name FROM sqlite_master WHERE type='table'`").fetchall():
    try: rows += c.execute(f'SELECT COUNT(*) FROM [{t[0]}]').fetchone()[0]
    except: pass
print(json.dumps({'tables': tables, 'rows': rows}))
c.close()
" 2>$null
        if ($stats) {
            $info = $stats | ConvertFrom-Json
            Write-OK "Tables: $($info.tables) | Rows: $($info.rows.ToString('N0'))"
        }
    } catch {
        Write-Warn "DB stats query failed (non-fatal)"
    }
    return $true
}

# ==================================================================
# Helper: Check model health
# ==================================================================
function Test-Model {
    $manifestPath = "$ModelData\manifest.json"
    if (-not (Test-Path $manifestPath)) {
        Write-Warn "Model not trained yet. Run:  .\START.ps1 train"
        return $false
    }
    try {
        $manifest = Get-Content $manifestPath -Raw | ConvertFrom-Json
        Write-OK "Model: $($manifest.model_name)"
        Write-OK "Corpus: $($manifest.corpus_size) docs | Vocab: $($manifest.vocab_size) terms"
        Write-OK "Trained: $($manifest.trained_at)"
    } catch {
        Write-Warn "Could not read model manifest"
        return $false
    }
    return $true
}

# ==================================================================
# Helper: Check if a TCP port is in use
# ==================================================================
function Test-Port {
    param([int]$Port)
    $conn = $null
    try {
        $conn = New-Object System.Net.Sockets.TcpClient
        $conn.Connect("127.0.0.1", $Port)
        return $true
    } catch {
        return $false
    } finally {
        if ($null -ne $conn) {
            try {
                $conn.Close()
            } catch {
                # Suppress cleanup errors
            }
        }
    }
}

# ==================================================================
# Command: status
# ==================================================================
function Show-Status {
    Show-Banner
    Write-Host "  SYSTEM HEALTH DASHBOARD" -ForegroundColor White
    Write-Host "  ========================" -ForegroundColor White

    Write-Step "Database"
    Test-Database | Out-Null

    Write-Step "MLLM Model"
    Test-Model | Out-Null
    if (Test-Path "$Model\inference_engine.py") {
        try {
            $env:LITIGATION_DB_PATH = $DB
            $statusOut = python "$Model\inference_engine.py" --status 2>&1
            if ($LASTEXITCODE -eq 0 -and $statusOut) {
                $statusOut -split "`n" | ForEach-Object { Write-Info $_.Trim() }
            }
        } catch { }
    }

    Write-Step "Applications"
    if (Test-Port 3001) {
        Write-OK "Desktop backend RUNNING on http://localhost:3001"
    } else {
        Write-Info "Desktop backend not running (port 3001 free)"
    }
    if (Test-Port 3000) {
        Write-OK "Web app RUNNING on http://localhost:3000"
    } else {
        Write-Info "Web app not running (port 3000 free)"
    }

    Write-Step "Evolution Cycles"
    $cycleDir = "$Root\00_SYSTEM\cyclepacks"
    if (Test-Path $cycleDir) {
        $cycles = (Get-ChildItem $cycleDir -Directory).Count
        Write-OK "$cycles cycle packs recorded"
        $latest = Get-ChildItem $cycleDir -Directory | Sort-Object Name -Descending | Select-Object -First 1
        if ($latest) { Write-Info "Latest: $($latest.Name)" }
    } else {
        Write-Info "No cycle packs found"
    }

    Write-Step "Pipeline"
    if (Test-Path "$Pipeline\pipeline.db") {
        $pipeSize = [math]::Round((Get-Item "$Pipeline\pipeline.db").Length / 1KB, 1)
        Write-OK "Pipeline DB: ${pipeSize} KB"
    }
    Write-OK "Phases available: 16 (phase1 -> phase16)"

    Write-Step "Directory Summary"
    $dirs = @(
        @("00_SYSTEM",           "Pipeline, AI model, scripts"),
        @("01_CASE_FILES",       "Primary case documents"),
        @("02_EVIDENCE",         "Exhibits, photos, records"),
        @("03_LEGAL_AUTHORITIES","Authority master DB, citations"),
        @("04_COURT_FILINGS",    "Court-ready filings"),
        @("05_ANALYSIS",         "Case analysis, strategy"),
        @("07_COURT_DOCUMENTS",  "Orders, transcripts, docket"),
        @("08_APPS",             "Desktop, Web, Mobile, Enterprise")
    )
    foreach ($d in $dirs) {
        $path = "$Root\$($d[0])"
        if (Test-Path $path) {
            $count = (Get-ChildItem $path -Recurse -File -ErrorAction SilentlyContinue).Count
            Write-OK "$($d[0].PadRight(22)) $($d[1].PadRight(35)) ($count files)"
        }
    }

    Write-Host ""
    Write-Host "  Run '.\START.ps1 help' for available commands." -ForegroundColor DarkGray
    Write-Host ""
}

# ==================================================================
# Command: start  (full system launch)
# ==================================================================
function Start-FullSystem {
    Show-Banner

    # 1. Database
    Write-Step "1/4  Database Check"
    if (-not (Test-Database)) { return }

    # 2. Model
    Write-Step "2/4  MLLM Model Check"
    $env:LITIGATION_DB_PATH = $DB
    $manifestPath = "$ModelData\manifest.json"
    if (-not (Test-Path $manifestPath)) {
        Write-Info "Training MLLM model (first run, ~60 seconds)..."
        python "$Model\train_model.py"
        if ($LASTEXITCODE -ne 0) {
            Write-Warn "Training failed - system will use DB-only fallback"
        } else {
            Write-OK "Model trained successfully"
        }
    } else {
        Test-Model | Out-Null
    }

    # 3. Desktop Backend
    Write-Step "3/4  Desktop Backend (Express :3001)"
    $env:NODE_ENV = "production"
    $env:PORT = "3001"
    if (Test-Port 3001) {
        Write-OK "Backend already running on port 3001"
    } elseif (Test-Path "$Backend\src\server.js") {
        Push-Location $Backend
        try {
            Start-Process -NoNewWindow -FilePath "node" -ArgumentList "src/server.js" -PassThru | Out-Null
            Start-Sleep -Seconds 3
            if (Test-Port 3001) {
                Write-OK "Backend started on http://localhost:3001"
            } else {
                Write-Warn "Backend may still be starting..."
            }
        } catch {
            Write-Fail "Could not start backend: $_"
        } finally {
            Pop-Location
        }
    } else {
        Write-Fail "Backend not found at $Backend\src\server.js"
    }

    # 4. Electron App
    Write-Step "4/4  Electron Desktop App"
    if (Test-Path "$Electron\main.js") {
        Push-Location $Electron
        $npxPath = Get-Command npx -ErrorAction SilentlyContinue
        if ($npxPath) {
            Start-Process -NoNewWindow -FilePath "npx" -ArgumentList "electron","." -PassThru | Out-Null
            Write-OK "Electron app launching..."
        } else {
            Write-Warn "npx not found - install with: npm install -g electron"
        }
        Pop-Location
    } else {
        Write-Warn "Electron entry not found at $Electron\main.js"
    }

    # Summary
    Write-Host ""
    Write-Host "+----------------------------------------------------------+" -ForegroundColor Green
    Write-Host "|    LitigationOS is RUNNING                               |" -ForegroundColor Green
    Write-Host "|    Backend:  http://localhost:3001                        |" -ForegroundColor Green
    Write-Host "|    AI:       MLLM (local, zero-network)                  |" -ForegroundColor Green
    Write-Host "|    DB:       litigation_context.db                        |" -ForegroundColor Green
    Write-Host "+----------------------------------------------------------+" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Quick test:" -ForegroundColor Cyan
    Write-Host "    python $Model\inference_engine.py `"MCR 2.003 disqualification`"" -ForegroundColor White
    Write-Host "    curl http://localhost:3001/api/litigation/stats" -ForegroundColor White
    Write-Host ""
}

# ==================================================================
# Command: desktop
# ==================================================================
function Start-Desktop {
    Show-Banner
    Write-Step "Starting Desktop App"
    $env:LITIGATION_DB_PATH = $DB
    $env:NODE_ENV = "production"
    $env:PORT = "3001"

    if (-not (Test-Port 3001)) {
        if (Test-Path "$Backend\src\server.js") {
            Write-Info "Starting backend on port 3001..."
            Push-Location $Backend
            Start-Process -NoNewWindow -FilePath "node" -ArgumentList "src/server.js" -PassThru | Out-Null
            Pop-Location
            Start-Sleep -Seconds 2
        }
    } else {
        Write-OK "Backend already running on port 3001"
    }

    if (Test-Path "$Electron\main.js") {
        Push-Location $Electron
        $npxPath = Get-Command npx -ErrorAction SilentlyContinue
        if ($npxPath) {
            Start-Process -NoNewWindow -FilePath "npx" -ArgumentList "electron","." -PassThru | Out-Null
            Write-OK "Electron desktop app starting..."
        } else {
            Write-Fail "npx not found. Run: npm install -g electron"
        }
        Pop-Location
    } else {
        Write-Fail "Electron entry not found at $Electron\main.js"
    }
}

# ==================================================================
# Command: web
# ==================================================================
function Start-Web {
    Show-Banner
    Write-Step "Starting Web App (Next.js)"

    if (-not (Test-Path "$Web\package.json")) {
        Write-Fail "Web app not found at $Web"
        return
    }

    if (-not (Test-Port 3000)) {
            npm install --silent 2>"npm-install-errors.log"
            if ($LASTEXITCODE -ne 0) {
                Write-Info "npm install reported errors. See npm-install-errors.log for details."
            }
    }

    Push-Location $Web
    try {
        if (-not (Test-Path "$Web\node_modules")) {
            Write-Info "Installing dependencies (first run)..."
            npm install --silent 2>$null
        }
        Start-Process -NoNewWindow -FilePath "npm" -ArgumentList "run","dev" -PassThru | Out-Null
        Write-OK "Web app starting at http://localhost:3000"
    } catch {
        Write-Fail "Could not start web app: $_"
    }
    Pop-Location
}

# ==================================================================
# Command: pipeline
# ==================================================================
function Start-Pipeline {
    Show-Banner
    Write-Step "Running Omega Pipeline (16 phases)"

    if (-not (Test-Path "$Pipeline\run_omega_pipeline.py")) {
        Write-Fail "Pipeline runner not found at $Pipeline\run_omega_pipeline.py"
        return
    }

    $env:LITIGATION_DB_PATH = $DB
    Push-Location $Pipeline
    try {
        Write-Info "Launching pipeline - this may take several minutes..."
        python run_omega_pipeline.py
        if ($LASTEXITCODE -eq 0) {
            Write-OK "Pipeline completed successfully"
        } else {
            Write-Warn "Pipeline exited with code $LASTEXITCODE"
        }
    } catch {
        Write-Fail "Pipeline error: $_"
    }
    Pop-Location
}

# ==================================================================
# Command: train
# ==================================================================
function Start-Train {
    Show-Banner
    Write-Step "Training MLLM (Michigan Legal Language Model)"

    if (-not (Test-Path "$Model\train_model.py")) {
        Write-Fail "Training script not found at $Model\train_model.py"
        return
    }

    $env:LITIGATION_DB_PATH = $DB
    Push-Location $Model
    try {
        Write-Info "Training in progress (~60 seconds)..."
        python train_model.py
        if ($LASTEXITCODE -eq 0) {
            Write-OK "Model training complete"
            Test-Model | Out-Null
        } else {
            Write-Fail "Training failed with exit code $LASTEXITCODE"
        }
    } catch {
        Write-Fail "Training error: $_"
    }
    Pop-Location
}

# ==================================================================
# Command: evolve
# ==================================================================
function Start-Evolve {
    param([int]$Cycles = 10)
    Show-Banner
    Write-Step "Self-Evolution: $Cycles cycles"

    if (-not (Test-Path "$Model\self_evolve.py")) {
        Write-Fail "Self-evolution script not found at $Model\self_evolve.py"
        return
    }

    $env:LITIGATION_DB_PATH = $DB
    Push-Location $Model
    try {
        Write-Info "Running $Cycles evolution cycles..."
        python self_evolve.py --cycles $Cycles
        if ($LASTEXITCODE -eq 0) {
            Write-OK "Evolution complete ($Cycles cycles)"
        } else {
            Write-Warn "Evolution exited with code $LASTEXITCODE"
        }
    } catch {
        Write-Fail "Evolution error: $_"
    }
    Pop-Location
}

# ==================================================================
# Command: analyze
# ==================================================================
function Start-Analyze {
    Show-Banner
    Write-Step "Running Analysis Suite"
    $env:LITIGATION_DB_PATH = $DB

    $scripts = @(
        @("$Analysis\forensic_judicial_analysis.py", "Forensic Judicial Analysis"),
        @("$Analysis\master_timeline.py",            "Master Timeline Builder")
    )

    foreach ($s in $scripts) {
        $scriptPath = $s[0]
        $label      = $s[1]
        if (Test-Path $scriptPath) {
            Write-Info "Running: $label"
            Push-Location (Split-Path $scriptPath)
            try {
                python (Split-Path $scriptPath -Leaf)
                if ($LASTEXITCODE -eq 0) {
                    Write-OK "$label - done"
                } else {
                    Write-Warn "$label - exited with code $LASTEXITCODE"
                }
            } catch {
                Write-Fail "$label - error: $_"
            }
            Pop-Location
        } else {
            Write-Warn "$label - script not found at $scriptPath"
        }
    }

    Write-Host ""
    Write-OK "Analysis suite complete. Results in: $Root\05_ANALYSIS"
}

# ==================================================================
# Command: help
# ==================================================================
function Show-Help {
    Show-Banner
    Write-Host "  USAGE:  .\START.ps1 <command> [args]" -ForegroundColor White
    Write-Host ""
    Write-Host "  COMMANDS:" -ForegroundColor Yellow
    Write-Host "    start          Full system launch (DB + Model + Backend + Electron)" -ForegroundColor White
    Write-Host "    status         System health dashboard (DB, model, apps, cycles)" -ForegroundColor White
    Write-Host "    desktop        Start desktop app (backend + Electron)" -ForegroundColor White
    Write-Host "    web            Start web app (Next.js on :3000)" -ForegroundColor White
    Write-Host "    pipeline       Run the 16-phase Omega pipeline" -ForegroundColor White
    Write-Host "    train          Train / retrain the MLLM model" -ForegroundColor White
    Write-Host "    evolve [N]     Run N self-evolution cycles (default: 10)" -ForegroundColor White
    Write-Host "    analyze        Run forensic + timeline analysis suite" -ForegroundColor White
    Write-Host "    help           Show this help message" -ForegroundColor White
    Write-Host ""
    Write-Host "  EXAMPLES:" -ForegroundColor Yellow
    Write-Host "    .\START.ps1 start          # Launch everything" -ForegroundColor DarkGray
    Write-Host "    .\START.ps1 status         # Quick health check" -ForegroundColor DarkGray
    Write-Host "    .\START.ps1 evolve 5       # 5 evolution cycles" -ForegroundColor DarkGray
    Write-Host "    .\START.ps1 train          # Retrain MLLM" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "  QUICK TEST:" -ForegroundColor Yellow
    Write-Host "    python $Model\inference_engine.py `"MCR 2.003 disqualification`"" -ForegroundColor DarkGray
    Write-Host "    curl http://localhost:3001/api/litigation/stats" -ForegroundColor DarkGray
    Write-Host ""
}

# ==================================================================
# Main: Route command
# ==================================================================
switch ($Command.ToLower()) {
    "start"    { Start-FullSystem }
    "status"   { Show-Status }
    "desktop"  { Start-Desktop }
    "web"      { Start-Web }
    "pipeline" { Start-Pipeline }
    "train"    { Start-Train }
    "evolve"   {
        $cycles = if ($Arg1 -match '^\d+$') { [int]$Arg1 } else { 10 }
        Start-Evolve -Cycles $cycles
    }
    "analyze"  { Start-Analyze }
    "help"     { Show-Help }
    default    {
        Write-Host ""
        Write-Host "  Unknown command: '$Command'" -ForegroundColor Red
        Write-Host "  Run '.\START.ps1 help' for available commands." -ForegroundColor Yellow
        Write-Host ""
        exit 1
    }
}
