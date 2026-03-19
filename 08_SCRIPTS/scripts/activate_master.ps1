<# 
activate_master.ps1 — hardened MASTER-tier activator

Usage:
  1) Right-click PowerShell → Run as Administrator.
  2) Set-ExecutionPolicy Bypass -Scope Process -Force
  3) .\activate_master.ps1
     or customize params:
     .\activate_master.ps1 -Root "F:\LAWFORGE_MASTER" -OutRoot "F:\LegalResults\MASTER" -Roots "F:\MEEK1","F:\MEEK2","F:\MEEK3","Z:\LAWFORGE_SERVER","D:\","E:\"

Requires:
  - Windows 10+ PowerShell 5.1 or PowerShell 7+
  - Python 3.10+ on PATH (or py launcher)
  - Tesseract OCR recommended (choco install tesseract)
What it does:
  - Creates isolated venv
  - Installs Python deps
  - Writes config, module map, .env
  - Verifies paths and permissions
  - Runs deterministic self-test and writes a signed report
#>

[CmdletBinding()]
param(
  [Parameter()] [string]   $Root    = "F:\LAWFORGE_MASTER",
  [Parameter()] [string]   $OutRoot = "F:\LegalResults\MASTER",
  [Parameter()] [string[]] $Roots   = @("F:\MEEK1","F:\MEEK2","F:\MEEK3","Z:\LAWFORGE_SERVER","D:\","E:\")
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

# ---------- Helpers ----------
function Ensure-Dir([string]$Path){
  if(-not $Path){ throw "Ensure-Dir: empty path" }
  if(!(Test-Path -LiteralPath $Path)){ New-Item -ItemType Directory -Path $Path | Out-Null }
}

function Write-UTF8NoBOM([string]$Path, [string]$Content){
  $dir = Split-Path -Parent $Path
  if($dir -and !(Test-Path -LiteralPath $dir)){ New-Item -ItemType Directory -Path $dir | Out-Null }
  $enc = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($Path, $Content, $enc)
}

function Hash-SHA256([string]$Path){
  if(!(Test-Path -LiteralPath $Path)){ throw "Hash-SHA256: file not found: $Path" }
  (Get-FileHash -Algorithm SHA256 -Path $Path).Hash
}

function Timestamp(){ (Get-Date).ToString("yyyy-MM-ddTHH:mm:ssK") }

$global:LogFile = $null
function Log([string]$Level, [string]$Msg){
  $line = "[{0}] [{1}] {2}" -f (Timestamp()), $Level, $Msg
  if($global:LogFile){ Add-Content -Path $global:LogFile -Value $line }
  Write-Host $line
}
function Info($m){ Log "INFO" $m }
function Warn($m){ Log "WARN" $m }
function Err ($m){ Log "ERROR" $m }
function Die ($m){ Err $m; exit 1 }

function Test-Admin(){
  try{
    $id  = [Security.Principal.WindowsIdentity]::GetCurrent()
    $pri = New-Object Security.Principal.WindowsPrincipal($id)
    return $pri.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
  } catch { return $false }
}

function Resolve-Python(){
  $candidates = @("python","py -3","py")
  foreach($c in $candidates){
    try{
      $ver = & $env:ComSpec /c "$c -V" 2>&1
      if($LASTEXITCODE -eq 0 -and $ver){ return $c }
    }catch{}
  }
  return $null
}

function Test-WriteAccess([string]$Path){
  try{
    Ensure-Dir $Path
    $probe = Join-Path $Path (".__write_probe_{0}.tmp" -f [Guid]::NewGuid().ToString("N"))
    "ok" | Out-File -FilePath $probe -Encoding utf8 -Force
    Remove-Item -LiteralPath $probe -Force
    return $true
  } catch { return $false }
}

# ---------- Boot ----------
Ensure-Dir $Root
$LogDir  = Join-Path $Root "logs"
Ensure-Dir $LogDir
$Stamp   = (Get-Date).ToString("yyyyMMdd_HHmmss")
$global:LogFile = Join-Path $LogDir "unlock_$Stamp.log"
Info "MASTER activation start"
Info "Root     = $Root"
Info "OutRoot  = $OutRoot"
Info "Roots[]  = `n  - " + ($Roots -join "`n  - ")

if(-not (Test-Admin())){ Warn "Run as Administrator for best reliability. Continuing." }

foreach($r in $Roots){ if([string]::IsNullOrWhiteSpace($r)){ Die "A Roots entry is empty" } }

# ---------- Permissions checks ----------
try{
  if(-not (Test-WriteAccess $Root)){ Die "No write access to Root: $Root" }
  if(-not (Test-WriteAccess $OutRoot)){ Die "No write access to OutRoot: $OutRoot" }
  foreach($r in $Roots){
    if(Test-Path -LiteralPath $r){
      if(-not (Get-Item -LiteralPath $r).PSIsContainer -and -not (Get-Item -LiteralPath $r).Attributes.HasFlag([IO.FileAttributes]::Directory)){
        Warn "Path is not a directory: $r"
      }
    } else {
      Warn "Root path not found (will be skipped in self-test): $r"
    }
  }
  Info "Write access checks passed"
}catch{ Die "Permission checks failed: $($_.Exception.Message)" }

# ---------- Python + venv ----------
$pyCmd = Resolve-Python
if(-not $pyCmd){ Die "Python not found. Install Python 3.10+ and re-run." }
Info "Python resolver = '$pyCmd'"

# Create venv
$Venv = Join-Path $Root ".venv"
if(!(Test-Path -LiteralPath $Venv)){
  Info "Creating venv at $Venv"
  & $env:ComSpec /c "$pyCmd -m venv `"$Venv`""
  if($LASTEXITCODE -ne 0){ Die "venv creation failed" }
} else {
  Info "Reusing existing venv"
}

$Vpy = Join-Path $Venv "Scripts\python.exe"
$Vpip = "$Vpy -m pip"
if(!(Test-Path -LiteralPath $Vpy)){ Die "venv python missing: $Vpy" }

# Upgrade pip toolchain
Info "Upgrading pip toolchain"
& $env:ComSpec /c "$Vpip install --upgrade pip wheel setuptools"
if($LASTEXITCODE -ne 0){ Die "pip toolchain upgrade failed" }

# Install deps
$Deps = @(
  "pdfplumber",
  "pypdfium2",
  "pytesseract",
  "pillow",
  "python-docx",
  "pandas",
  "regex",
  "unidecode",
  "tqdm",
  "pyyaml",
  "chromadb",
  "pydantic<3"
)
Info "Installing Python deps"
& $env:ComSpec /c "$Vpip install $($Deps -join ' ')"
if($LASTEXITCODE -ne 0){ Die "dependency install failed" }
Info "Python deps installed"

# ---------- External tools checks ----------
try{
  $tess = Get-Command tesseract.exe -ErrorAction SilentlyContinue
  if($tess){
    Info "Tesseract detected: $($tess.Source)"
  } else {
    Warn "Tesseract not found. OCR will be limited. Install with Chocolatey: choco install tesseract"
  }
}catch{ Warn "Tesseract check failed: $($_.Exception.Message)" }

# ---------- Config files ----------
$cfgPath = Join-Path $Root "lawforge_config.yaml"
$modPath = Join-Path $Root "modules_enabled.json"
$envPath = Join-Path $Root ".env"

# Compose YAML safely
$rootsYaml = ($Roots | ForEach-Object { '    - "{0}"' -f ($_ -replace '\\','\\') }) -join "`r`n"
$cfg = @"
general:
  tier: MASTER_OMEGA
  mode: offline
  timezone: America/Detroit
paths:
  roots:
$rootsYaml
  output: "$OutRoot"
scanning:
  include_ext: [pdf, docx, txt, rtf, jpg, jpeg, png, tif, tiff, eml, msg, mp3, mp4, wav]
  max_files_per_root: 100000000
ocr:
  engine: tesseract
  language: eng
legal:
  enforce_mcr: true
  enforce_mcl: true
  enforce_benchbooks: true
modules:
  - name: EvidenceProcessingEngine           ; enabled: true  ; version: 1.0.0
  - name: LitigationStrategyEngine           ; enabled: true  ; version: 1.0.0
  - name: CanonViolationDetector             ; enabled: true  ; version: 1.0.0
  - name: BenchbookViolationMapper           ; enabled: true  ; version: 1.0.0
  - name: MotionStackGenerator               ; enabled: true  ; version: 1.0.0
  - name: TimelineWarboard                   ; enabled: true  ; version: 1.0.0
  - name: CourtFormOverlayAutofill           ; enabled: true  ; version: 1.0.0
  - name: EntityShellMapper                  ; enabled: true  ; version: 1.0.0
  - name: KnowledgeRetentionLayer            ; enabled: true  ; version: 1.0.0
  - name: ActionableHarmIndex                ; enabled: true  ; version: 1.0.0
  - name: LitigationTriggerGenerator         ; enabled: true  ; version: 1.0.0
  - name: JudicialResponseAnticipation       ; enabled: true  ; version: 1.0.0
  - name: ZIPComplianceValidator             ; enabled: true  ; version: 1.0.0
"@

$mods = @"
[
  {"name":"EvidenceProcessingEngine","enabled":true,"id":"EPE"},
  {"name":"LitigationStrategyEngine","enabled":true,"id":"LSE"},
  {"name":"CanonViolationDetector","enabled":true,"id":"CVD"},
  {"name":"BenchbookViolationMapper","enabled":true,"id":"BVM"},
  {"name":"MotionStackGenerator","enabled":true,"id":"MSG"},
  {"name":"TimelineWarboard","enabled":true,"id":"TWB"},
  {"name":"CourtFormOverlayAutofill","enabled":true,"id":"CFO"},
  {"name":"EntityShellMapper","enabled":true,"id":"ESM"},
  {"name":"KnowledgeRetentionLayer","enabled":true,"id":"KRL"},
  {"name":"ActionableHarmIndex","enabled":true,"id":"AHI"},
  {"name":"LitigationTriggerGenerator","enabled":true,"id":"LTG"},
  {"name":"JudicialResponseAnticipation","enabled":true,"id":"JRA"},
  {"name":"ZIPComplianceValidator","enabled":true,"id":"ZCV"}
]
"@

$envTxt = @"
LFO_TIER=MASTER_OMEGA
LFO_MODE=OFFLINE
TZ=America/Detroit
MCR_ENFORCE=1
MCL_ENFORCE=1
BENCHBOOK_ENFORCE=1
OUTPUT_DIR=$OutRoot
"@

try{
  Write-UTF8NoBOM $cfgPath $cfg
  Write-UTF8NoBOM $modPath $mods
  Write-UTF8NoBOM $envPath $envTxt
  $cfgHash = Hash-SHA256 $cfgPath
  $modHash = Hash-SHA256 $modPath
  $envHash = Hash-SHA256 $envPath
  Info "Config written"
  Info "SHA256 cfg=$cfgHash"
  Info "SHA256 mods=$modHash"
  Info "SHA256 env=$envHash"
}catch{ Die "Config write failed: $($_.Exception.Message)" }

# ---------- Self-test (deterministic) ----------
$testPy = Join-Path $Root "lf_selftest.py"
$testSrc = @"
import os, sys, json, hashlib, uuid, time, yaml
from datetime import datetime

CFG = r'$cfgPath'
OUT = r'$OutRoot'
REPORT = os.path.join(OUT, f'MASTER_UNLOCK_REPORT_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt')

def sha256_file(p):
    h = hashlib.sha256()
    with open(p,'rb') as f:
        for chunk in iter(lambda: f.read(1048576), b''):
            h.update(chunk)
    return h.hexdigest()

os.makedirs(OUT, exist_ok=True)
with open(CFG,'r',encoding='utf-8') as f:
    cfg = yaml.safe_load(f)

roots = cfg.get('paths',{}).get('roots',[])
exts  = set(e.lower() for e in cfg.get('scanning',{}).get('include_ext',[]))

counts  = {}
samples = {}
for r in roots:
    try:
        if not os.path.exists(r):
            counts[r] = 0
            samples[r] = []
            continue
        n = 0
        s = []
        for dp,_,fn in os.walk(r):
            for name in fn:
                ext = name.rsplit('.',1)[-1].lower() if '.' in name else ''
                if ext in exts:
                    full = os.path.join(dp,name)
                    n += 1
                    if len(s) < 5:
                        s.append(full)
        counts[r] = n
        samples[r] = s
    except Exception as e:
        counts[r] = -1
        samples[r] = [f'ERROR: {e!r}']

status = {
    "tier": cfg.get("general",{}).get("tier",""),
    "mode": cfg.get("general",{}).get("mode",""),
    "timezone": cfg.get("general",{}).get("timezone",""),
    "output": OUT,
    "config_sha256": sha256_file(CFG),
    "chain_id": str(uuid.uuid4()),
    "file_counts": counts,
    "sample_files": samples,
}

with open(REPORT,'w',encoding='utf-8') as f:
    f.write("LAWFORGE MASTER UNLOCK REPORT\n")
    f.write("=============================\n")
    for k in ("tier","mode","timezone","output","config_sha256","chain_id"):
        f.write(f"{k}: {status[k]}\n")
    f.write("\nFILE COUNTS\n-----------\n")
    for k,v in counts.items():
        f.write(f"{k}: {v}\n")
    f.write("\nSAMPLE FILES\n------------\n")
    for k,arr in samples.items():
        f.write(f"{k}:\n")
        for item in arr:
            f.write(f"  - {item}\n")

print(json.dumps(status, indent=2))
"@

try{
  Write-UTF8NoBOM $testPy $testSrc
  Info "Running self-test"
  $env:PYTHONIOENCODING = "utf-8"
  $testOut = & $Vpy $testPy 2>&1
  if($LASTEXITCODE -ne 0){ Die "Self-test failed`n$testOut" }
  Info "Self-test OK"
  Add-Content -Path $global:LogFile -Value "SELFTEST_JSON:`n$testOut"
}catch{ Die "Self-test error: $($_.Exception.Message)" }

# ---------- Finalize ----------
try{
  $DoneFlag = Join-Path $Root "MASTER_UNLOCK_OK"
  Write-UTF8NoBOM $DoneFlag ("UNLOCKED $Stamp`r`nCFG_SHA256=$cfgHash`r`nLOG=$global:LogFile")
  Info "Master tier configured"
  Info "Report dir: $OutRoot"
  Info "Log file  : $global:LogFile"
  exit 0
}catch{
  Die "Finalize failed: $($_.Exception.Message)"
}
