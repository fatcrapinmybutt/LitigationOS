# LitigationOS Agent PowerShell Profile v2.0
# Dot-source this: . C:\Users\andre\LitigationOS\00_SYSTEM\tools\agent_profile.ps1
#
# Provides: sspy, srun, senv, sshadow, spy (Python safety)
#           schain (command chaining), spreflight (session cleanup)

$env:PYTHONUTF8 = "1"
$env:PYTHONDONTWRITEBYTECODE = "1"

$script:SAFE_SHELL = "C:\Users\andre\LitigationOS\00_SYSTEM\tools\safe_shell.py"
$script:LITIGOS_ROOT = "C:\Users\andre\LitigationOS"

# ─── Python Safety Commands ─────────────────────────────────────────

# Safe syntax check — AST parse, no imports, avoids shadow modules
function sspy {
    param([Parameter(ValueFromRemainingArguments=$true)]$files)
    python $script:SAFE_SHELL check @files
}

# Safe run — executes script from its own directory, not repo root
function srun {
    param([Parameter(ValueFromRemainingArguments=$true)]$args_)
    python $script:SAFE_SHELL run @args_
}

# Environment health check
function senv {
    python $script:SAFE_SHELL env-check
}

# Shadow module audit
function sshadow {
    python $script:SAFE_SHELL shadow-audit
}

# Safe inline Python execution (writes to temp file, never python -c)
function spy {
    param([string]$code)
    $hash = [System.BitConverter]::ToString(
        [System.Security.Cryptography.MD5]::Create().ComputeHash(
            [System.Text.Encoding]::UTF8.GetBytes($code)
        )
    ).Replace("-","").Substring(0,8).ToLower()
    $tmp = "$script:LITIGOS_ROOT\00_SYSTEM\tools\_tmp_$hash.py"
    @"
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
$code
"@ | Out-File -Encoding utf8 $tmp
    python $tmp
    Remove-Item $tmp -ErrorAction SilentlyContinue
}

# ─── Shell Hygiene Commands ──────────────────────────────────────────

# Chain multiple commands in one shell to reduce session count
# Usage: schain "cd project" "npm run build" "npm test"
function schain {
    param([Parameter(ValueFromRemainingArguments=$true)][string[]]$commands)
    $joined = $commands -join " && "
    Write-Host "[schain] $joined" -ForegroundColor Cyan
    Invoke-Expression $joined
}

# Pre-flight cleanup: kill orphan Python processes older than 5 min + temp file sweep
function spreflight {
    Write-Host "[preflight] Checking for orphan processes..." -ForegroundColor Yellow
    $cutoff = (Get-Date).AddMinutes(-5)
    $orphans = Get-Process -Name python -ErrorAction SilentlyContinue |
        Where-Object { $_.StartTime -lt $cutoff -and $_.MainWindowHandle -eq 0 }
    if ($orphans) {
        Write-Host "[preflight] Found $($orphans.Count) orphan Python processes" -ForegroundColor Red
        $orphans | ForEach-Object {
            Write-Host "  PID $($_.Id) started $($_.StartTime) — $($_.Path)" -ForegroundColor DarkYellow
        }
        Write-Host "[preflight] Use: Stop-Process -Id <PID> to kill specific ones" -ForegroundColor Yellow
    } else {
        Write-Host "[preflight] No orphan processes found ✅" -ForegroundColor Green
    }

    # Check temp files
    $tmpFiles = Get-ChildItem "$script:LITIGOS_ROOT\00_SYSTEM\tools\_tmp_*.py" -ErrorAction SilentlyContinue
    if ($tmpFiles) {
        Write-Host "[preflight] Cleaning $($tmpFiles.Count) temp files..." -ForegroundColor Yellow
        $tmpFiles | Remove-Item -Force
        Write-Host "[preflight] Temp files cleaned ✅" -ForegroundColor Green
    }

    Write-Host "[preflight] Ready ✅" -ForegroundColor Green
}

# ─── Shell Session Budget Monitor ────────────────────────────────────

# Shell budget check — warns if approaching the 3-shell limit
# Usage: sbudget (call before creating new async shells)
function sbudget {
    Write-Host "[shell-budget] ⚠ REMINDER: Max 3 concurrent async shells" -ForegroundColor Yellow
    Write-Host "  Before creating a new shell:" -ForegroundColor DarkGray
    Write-Host "    1. Call list_powershell to count active sessions" -ForegroundColor DarkGray
    Write-Host "    2. Stop completed shells with stop_powershell" -ForegroundColor DarkGray
    Write-Host "    3. Chain related commands with && in one shell" -ForegroundColor DarkGray
    Write-Host "    4. Always use named shellIds (build, test, lint)" -ForegroundColor DarkGray
    Write-Host "  Recovery (Invalid shell ID):" -ForegroundColor DarkGray
    Write-Host "    list_powershell → stop ALL → wait 5s → retry" -ForegroundColor DarkGray
}

Write-Host "LitigationOS agent profile v3.0 loaded" -ForegroundColor Green
Write-Host "  Python: sspy, srun, senv, sshadow, spy" -ForegroundColor DarkGray
Write-Host "  Shell:  schain, spreflight, sbudget" -ForegroundColor DarkGray
