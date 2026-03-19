use it, fix this script, and improve it. <#
LitigationPipeline.ps1
All-in-one autonomous pipeline:

1. Ensures rclone + NSSM and (re)installs rclone mount services
2. Organizes files across mounted drives
3. Indexes files to JSON
4. Pipelines summaries to GPT (cloud) or local LLM (offline)

## USAGE EXAMPLES

# Normal (cloud GPT if OPENAI\_API\_KEY is set)

powershell -ExecutionPolicy Bypass -File .\LitigationPipeline.ps1

# Force offline local LLM (e.g., LM Studio/Ollama)

powershell -ExecutionPolicy Bypass -File .\LitigationPipeline.ps1 -Offline

# Dry-run (no changes)

powershell -ExecutionPolicy Bypass -File .\LitigationPipeline.ps1 -DryRun

# Use custom config JSON (merges/overrides defaults)

powershell -ExecutionPolicy Bypass -File .\LitigationPipeline.ps1 -ConfigFile "C:\path\pipeline.config.json"
\#>

\[CmdletBinding()]
param(
\[switch]\$DryRun,
\[switch]\$Offline,
\[string]\$ConfigFile = "",
\[string]\$OpenAIModel = "gpt-4o-mini",
\[string]\$OpenAIEndpoint = "[https://api.openai.com/v1/chat/completions](https://api.openai.com/v1/chat/completions)",
\[string]\$LocalLLMEndpoint = "[http://localhost:1234/v1/chat/completions](http://localhost:1234/v1/chat/completions)", # LM Studio-compatible; set to Ollama if needed
\[string]\$LitigationOSWebhook = "" # Optional webhook to notify your Litigation OS
)

Set-StrictMode -Version Latest
\$ErrorActionPreference = 'Stop'

# ------------------------------

# Admin Elevation

# ------------------------------

function Ensure-Admin {
\$current = \[Security.Principal.WindowsIdentity]::GetCurrent()
\$principal = New-Object Security.Principal.WindowsPrincipal(\$current)
if (-not \$principal.IsInRole(\[Security.Principal.WindowsBuiltinRole]::Administrator)) {
Write-Host "\[INFO] Elevating to Administrator..." -ForegroundColor Yellow
\$psi = New-Object System.Diagnostics.ProcessStartInfo "powershell"
\$argsList = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "`"$PSCommandPath`"")
if (\$DryRun) { \$argsList += "-DryRun" }
if (\$Offline) { \$argsList += "-Offline" }
if (\$ConfigFile) { \$argsList += @("-ConfigFile", "`"$ConfigFile`"") }
if (\$OpenAIModel) { \$argsList += @("-OpenAIModel", "`"$OpenAIModel`"") }
if (\$OpenAIEndpoint) { \$argsList += @("-OpenAIEndpoint", "`"$OpenAIEndpoint`"") }
if (\$LocalLLMEndpoint) { \$argsList += @("-LocalLLMEndpoint", "`"$LocalLLMEndpoint`"") }
if (\$LitigationOSWebhook) { \$argsList += @("-LitigationOSWebhook", "`"$LitigationOSWebhook`"") }
\$psi.Arguments = (\$argsList -join ' ')
\$psi.Verb = "runas"
\[System.Diagnostics.Process]::Start(\$psi) | Out-Null
exit
}
}
Ensure-Admin

# ------------------------------

# Logging

# ------------------------------

\$Global\:Config = \$null
\$Global\:LogDir  = "\$Env\:ProgramData\LitigationOS\logs"
\$Global\:LogFile = Join-Path \$Global\:LogDir ("pipeline\_" + (Get-Date -Format "yyyyMMdd\_HHmmss") + ".log")
New-Item -ItemType Directory -Path \$Global\:LogDir -Force | Out-Null

function Write-Log {
param(
\[ValidateSet('INFO','WARN','ERROR','SUCCESS')] \[string]\$Level = 'INFO',
\[Parameter(Mandatory)]\[string]\$Message
)
\$ts = (Get-Date).ToString('yyyy-MM-dd HH\:mm\:ss')
\$line = "\[\$ts]\[\$Level] \$Message"
\$color = switch (\$Level) {
'INFO'    { 'Gray' }
'WARN'    { 'Yellow' }
'ERROR'   { 'Red' }
'SUCCESS' { 'Green' }
}
Add-Content -Path \$Global\:LogFile -Value \$line
Write-Host \$line -ForegroundColor \$color
}

# ------------------------------

# Default Configuration

# ------------------------------

\$defaultConfig = @{
Rclone = @{
Exe     = "Z:\CENTRAL DASHBOARD\rclone.exe"
Dir     = "Z:\CENTRAL DASHBOARD"
Config  = "\$Env\:ProgramData\rclone\rclone.conf"
Version = "" # pin e.g. "v1.67.0" or leave empty for latest (used only if auto-installing)
}
NSSM = @{
Exe = "Z:\CENTRAL DASHBOARD\nssm.exe"
Dir = "Z:\CENTRAL DASHBOARD"
Url = "[https://nssm.cc/release/nssm-2.24.zip](https://nssm.cc/release/nssm-2.24.zip)"
}
Mounts = @(
@{ Service="rcloneGDriveF"; Remote="gdrive:"; Letter="F:"; RcPort=5572; Options="--vfs-cache-mode full --dir-cache-time 12h --poll-interval 15s --buffer-size 64M --volname GDrive" },
@{ Service="rcloneGDriveZ"; Remote="gdrive:"; Letter="Z:"; RcPort=5573; Options="--vfs-cache-mode full --dir-cache-time 12h --poll-interval 15s --buffer-size 64M --volname GDrive" },
@{ Service="rcloneGDriveE"; Remote="gdrive:"; Letter="E:"; RcPort=5574; Options="--vfs-cache-mode full --dir-cache-time 12h --poll-interval 15s --buffer-size 64M --volname GDrive" }
)
Organize = @{
Roots = @("F:", "Z:", "E:")
UnsortedFolder = "Unsorted"
Rules = @(
@{ Patterns=@("*.pdf");                           Target="Depositions\PDFs" },
@{ Patterns=@("*.doc","*.docx","*.rtf","*.txt");  Target="Documents" },
@{ Patterns=@("*.xlsx","*.csv");                  Target="Spreadsheets" },
@{ Patterns=@("*.mp4","*.mov","*.mkv");           Target="Media\Evidence" },
@{ Patterns=@("*.mp3","*.wav","*.m4a");           Target="Media\Audio" },
@{ Patterns=@("*.jpg","*.jpeg","*.png","*.tiff","*.bmp"); Target="Media\Images" }
)
}
Index = @{
Roots = @("F:", "Z:", "E:")
OutputDir = "\$Env\:ProgramData\LitigationOS\indexes"
ComputeHash = \$false
IncludeExtensions = @("pdf","doc","docx","rtf","txt","xlsx","csv","mp4","mov","mkv","mp3","wav","m4a","jpg","jpeg","png","tiff","bmp")
}
Pipeline = @{
SendTo = \$(if(\$Offline){ "LocalLLM" } else { "OpenAI" }) # OpenAI | LocalLLM | Webhook
CaseId = "default"
OutputDir = "\$Env\:ProgramData\LitigationOS\pipeline"
OpenAIModel = \$OpenAIModel
OpenAIEndpoint = \$OpenAIEndpoint
LocalLLMEndpoint = \$LocalLLMEndpoint
Webhook = \$LitigationOSWebhook
}
}

# Merge with external config if provided

function Merge-Hashtable(\$base, \$override) {
foreach (\$k in \$override.Keys) {
if (\$base.ContainsKey(\$k) -and \$base\[\$k] -is \[hashtable] -and \$override\[\$k] -is \[hashtable]) {
\$base\[\$k] = Merge-Hashtable \$base\[\$k] \$override\[\$k]
} else {
\$base\[\$k] = \$override\[\$k]
}
}
return \$base
}

\$Global\:Config = \$defaultConfig
if (\$ConfigFile -and (Test-Path \$ConfigFile)) {
Write-Log INFO "Loading config overrides from \$ConfigFile"
\$json = Get-Content \$ConfigFile -Raw | ConvertFrom-Json -AsHashtable
\$Global\:Config = Merge-Hashtable \$Global\:Config \$json
}

# Ensure dirs

New-Item -ItemType Directory -Path \$Global\:Config.Index.OutputDir -Force | Out-Null
New-Item -ItemType Directory -Path \$Global\:Config.Pipeline.OutputDir -Force | Out-Null
New-Item -ItemType Directory -Path (Split-Path \$Global\:Config.Rclone.Config -Parent) -Force | Out-Null

# ------------------------------

# Tools: Ensure NSSM & rclone (optional auto-install if paths missing)

# ------------------------------

function Get-OSBits { if (\[Environment]::Is64BitOperatingSystem) { "amd64" } else { "386" } }

function Ensure-NSSM {
\$exe = \$Global\:Config.NSSM.Exe
if (Test-Path \$exe) { Write-Log INFO "NSSM found at \$exe"; return }
if (\$DryRun) { Write-Log WARN "\[DRY-RUN] NSSM missing; would download & install."; return }
Write-Log INFO "Installing NSSM..."
\$dir = \$Global\:Config.NSSM.Dir
New-Item -ItemType Directory -Path \$dir -Force | Out-Null
\$zip = Join-Path \$env\:TEMP "nssm.zip"
Invoke-WebRequest -UseBasicParsing -Uri \$Global\:Config.NSSM.Url -OutFile \$zip
Expand-Archive -Path \$zip -DestinationPath \$dir -Force
\$sub = Get-ChildItem \$dir -Directory | Where-Object { $\_.Name -like "nssm-\*" } | Select-Object -First 1
\$bits = if (\[Environment]::Is64BitOperatingSystem) { "win64" } else { "win32" }
Copy-Item (Join-Path \$sub.FullName "\$bits\nssm.exe") \$exe -Force
Remove-Item \$zip -Force
Write-Log SUCCESS "NSSM installed to \$exe"
}

function Ensure-Rclone {
\$exe = \$Global\:Config.Rclone.Exe
if (Test-Path \$exe) { Write-Log INFO "rclone found at \$exe"; return }
if (\$DryRun) { Write-Log WARN "\[DRY-RUN] rclone missing; would download & install."; return }
Write-Log INFO "Installing rclone..."
\$dir = \$Global\:Config.Rclone.Dir
New-Item -ItemType Directory -Path \$dir -Force | Out-Null
\$bits = Get-OSBits
\$ver = \$Global\:Config.Rclone.Version
if (-not \$ver) {
\$latest = (Invoke-RestMethod "[https://downloads.rclone.org/").Links](https://downloads.rclone.org/%22%29.Links) |
Where-Object { \$*.href -match '^v\d+.\d+.\d+/\$' } |
Sort-Object href -Descending | Select-Object -First 1 -ExpandProperty href
\$ver = \$latest.TrimEnd('/')
}
\$zipUrl = "[https://downloads.rclone.org/\$ver/rclone-\$ver-windows-\$bits.zip](https://downloads.rclone.org/$ver/rclone-$ver-windows-$bits.zip)"
\$zip = Join-Path \$env\:TEMP "rclone.zip"
Invoke-WebRequest -UseBasicParsing -Uri \$zipUrl -OutFile \$zip
Expand-Archive -Path \$zip -DestinationPath \$dir -Force
\$sub = Get-ChildItem \$dir -Directory | Where-Object { \$*.Name -like "rclone-\*" } | Select-Object -First 1
Copy-Item (Join-Path \$sub.FullName "rclone.exe") \$exe -Force
Remove-Item \$zip -Force
Write-Log SUCCESS "rclone installed to \$exe"
}

# ------------------------------

# Service Setup with NSSM

# ------------------------------

function Remove-Service-IfExists(\[string]\$Name) {
\$svc = Get-Service -Name \$Name -ErrorAction SilentlyContinue
if (\$svc) {
Write-Log INFO "Stopping and removing service \$Name"
if (-not \$DryRun) {
Try { Stop-Service -Name \$Name -Force -ErrorAction SilentlyContinue; Start-Sleep -Seconds 2 } Catch {}
& \$Global\:Config.NSSM.Exe remove \$Name confirm | Out-Null
Start-Sleep -Seconds 1
} else {
Write-Log WARN "\[DRY-RUN] Would remove service \$Name"
}
}
}

function Install-Rclone-Service(\$m) {
\$svc = \$m.Service
\$remote = \$m.Remote
\$letter = \$m.Letter
\$rcPort = \$m.RcPort
\$opts = "\$(\$m.Options) --rc --rc-addr 127.0.0.1:\$rcPort --log-file `"$($Global:LogDir)\$svc.runtime.log`" --log-level INFO"

Write-Log INFO "Installing service \$svc for \$remote -> \$letter"
\$rcloneExe = \$Global\:Config.Rclone.Exe
\$rcloneConf = \$Global\:Config.Rclone.Config

if (-not \$DryRun) {
& \$Global\:Config.NSSM.Exe install \$svc \$rcloneExe | Out-Null
& \$Global\:Config.NSSM.Exe set \$svc AppDirectory \$Global\:Config.Rclone.Dir | Out-Null
& \$Global\:Config.NSSM.Exe set \$svc AppParameters "--config `"$rcloneConf`" mount \$remote \$letter \$opts" | Out-Null
& \$Global\:Config.NSSM.Exe set \$svc AppStdout (Join-Path \$Global\:LogDir "\$svc.out.log") | Out-Null
& \$Global\:Config.NSSM.Exe set \$svc AppStderr (Join-Path \$Global\:LogDir "\$svc.err.log") | Out-Null
& \$Global\:Config.NSSM.Exe set \$svc AppStopMethodSkip 6 | Out-Null
& \$Global\:Config.NSSM.Exe set \$svc AppRestartDelay 5000 | Out-Null
& \$Global\:Config.NSSM.Exe set \$svc Start SERVICE\_AUTO\_START | Out-Null
sc.exe config \$svc start= delayed-auto | Out-Null
Try { Start-Service -Name \$svc; Start-Sleep -Seconds 2 } Catch {}
} else {
Write-Log WARN "\[DRY-RUN] Would install and start service \$svc"
}

\$running = (Get-Service -Name \$svc -ErrorAction SilentlyContinue)
if (\$running -and \$running.Status -eq 'Running') {
Write-Log SUCCESS "Service \$svc is RUNNING"
} else {
if (\$DryRun) { Write-Log INFO "\[DRY-RUN] Skipping status check for \$svc" }
else { Write-Log WARN "Service \$svc not confirmed running (check logs)" }
}
}

function Setup-Rclone-Services {
Ensure-NSSM
Ensure-Rclone
foreach (\$m in \$Global\:Config.Mounts) {
Remove-Service-IfExists \$m.Service
Install-Rclone-Service \$m
}
}

# ------------------------------

# Organizer

# ------------------------------

function Organize-Drives {
\$roots = \$Global\:Config.Organize.Roots
\$unsorted = \$Global\:Config.Organize.UnsortedFolder
\$rules = \$Global\:Config.Organize.Rules

foreach (\$root in \$roots) {
if (-not (Test-Path \$root)) { Write-Log WARN "Root not found: \$root"; continue }
\$unsortedPath = Join-Path \$root \$unsorted
if (-not (Test-Path \$unsortedPath)) { Write-Log INFO "No Unsorted at \$unsortedPath (skip)"; continue }

```
Write-Log INFO "Organizing: $unsortedPath"
foreach ($rule in $rules) {
  $target = Join-Path $root $rule.Target
  if (-not (Test-Path $target)) { if (-not $DryRun) { New-Item -ItemType Directory -Path $target -Force | Out-Null } }
  foreach ($pattern in $rule.Patterns) {
    $files = Get-ChildItem -Path $unsortedPath -Recurse -File -Filter $pattern -ErrorAction SilentlyContinue
    foreach ($f in $files) {
      $dest = Join-Path $target $f.Name
      if ($DryRun) {
        Write-Log INFO "[DRY-RUN] Move `"$($f.FullName)`" -> `"$dest`""
      } else {
        Try {
          Move-Item -LiteralPath $f.FullName -Destination $dest -Force
          Write-Log SUCCESS "Moved: $($f.FullName) -> $dest"
        } Catch {
          Write-Log ERROR "Move failed: $($f.FullName) -> $dest :: $($_.Exception.Message)"
        }
      }
    }
  }
}
```

}
}

# ------------------------------

# Indexer

# ------------------------------

function Index-FilesToJson {
\$roots = \$Global\:Config.Index.Roots
\$outDir = \$Global\:Config.Index.OutputDir
\$computeHash = \[bool]\$Global\:Config.Index.ComputeHash
\$exts = \$Global\:Config.Index.IncludeExtensions
\$items = New-Object System.Collections.Generic.List\[object]

foreach (\$root in \$roots) {
if (-not (Test-Path \$root)) { Write-Log WARN "Index root not found: \$root"; continue }
Write-Log INFO "Indexing \$root"
\$files = Get-ChildItem -Path \$root -Recurse -File -ErrorAction SilentlyContinue | Where-Object {
\$e = $\_.Extension.TrimStart('.').ToLowerInvariant()
if (\$exts.Count -eq 0) { \$true } else { \$exts -contains \$e }
}
foreach (\$f in \$files) {
\$obj = \[ordered]@{
Path     = \$f.FullName
Name     = \$f.Name
Dir      = \$f.DirectoryName
Ext      = \$f.Extension.ToLower()
Size     = \$f.Length
Created  = \$f.CreationTimeUtc
Modified = \$f.LastWriteTimeUtc
}
if (\$computeHash) {
Try { \$obj.Hash = (Get-FileHash -Algorithm SHA256 -LiteralPath \$f.FullName).Hash } Catch { \$obj.Hash = \$null }
}
\$items.Add(\[PSCustomObject]\$obj) | Out-Null
}
}

\$now = Get-Date -Format "yyyyMMdd\_HHmmss"
\$indexPath = Join-Path \$outDir ("index\_" + \$Global\:Config.Pipeline.CaseId + "\_\$now\.json")
\$items | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 \$indexPath
Write-Log SUCCESS "Index written: \$indexPath"
return \$indexPath
}

# ------------------------------

# Pipeline to GPT / Local LLM / Webhook

# ------------------------------

function Build-Digest(\[string]\$IndexPath) {
\$arr = Get-Content \$IndexPath -Raw | ConvertFrom-Json
\$count = \$arr.Count
\$byExt = \$arr | Group-Object Ext | Sort-Object Count -Descending | Select-Object Name,Count
\$recent = \$arr | Sort-Object Modified -Descending | Select-Object -First 50 Path,Modified,Size
\$totalSize = (\$arr | Measure-Object -Property Size -Sum).Sum
return \[PSCustomObject]@{
CaseId     = \$Global\:Config.Pipeline.CaseId
Count      = \$count
TotalBytes = \$totalSize
ByExtension= \$byExt
Recent     = \$recent
IndexPath  = \$IndexPath
GeneratedAt= (Get-Date)
}
}

function Send-ToOpenAI(\[pscustomobject]\$Digest) {
\$apiKey = \$Env\:OPENAI\_API\_KEY
if (-not \$apiKey) { Write-Log ERROR "OPENAI\_API\_KEY not set."; return \$null }

\$body = @{
model = \$Global\:Config.Pipeline.OpenAIModel
messages = @(
@{ role="system"; content="You are Litigation OS's assistant. Produce concise, actionable summaries and file routing suggestions." }
@{ role="user"; content = "Here is a file inventory digest in JSON. Summarize key risks, missing docs, and next actions:\`n\$(\$Digest | ConvertTo-Json -Depth 6)" }
)
temperature = 0.2
} | ConvertTo-Json -Depth 6 -Compress

\$resp = Invoke-RestMethod -Uri \$Global\:Config.Pipeline.OpenAIEndpoint `    -Method POST`
-Headers @{ "Authorization" = "Bearer \$apiKey"; "Content-Type" = "application/json" } \`
-Body \$body

return \$resp.choices\[0].message.content
}

function Send-ToLocalLLM(\[pscustomobject]\$Digest) {
\$body = @{
model = "local-model"
messages = @(
@{ role="system"; content="You are Litigation OS's assistant. Produce concise, actionable summaries and file routing suggestions." }
@{ role="user"; content = "Here is a file inventory digest in JSON. Summarize key risks, missing docs, and next actions:\`n\$(\$Digest | ConvertTo-Json -Depth 6)" }
)
temperature = 0.2
} | ConvertTo-Json -Depth 6 -Compress

\$resp = Invoke-RestMethod -Uri \$Global\:Config.Pipeline.LocalLLMEndpoint `    -Method POST`
-Headers @{ "Content-Type" = "application/json" } \`
-Body \$body

return \$resp.choices\[0].message.content
}

function Send-ToWebhook(\[pscustomobject]\$Digest) {
if (-not \$Global\:Config.Pipeline.Webhook) { Write-Log WARN "Webhook URL not set; skipping."; return \$null }
\$payload = @{
caseId = \$Global\:Config.Pipeline.CaseId
digest = \$Digest
} | ConvertTo-Json -Depth 6
\$resp = Invoke-RestMethod -Uri \$Global\:Config.Pipeline.Webhook -Method POST -Headers @{ "Content-Type" = "application/json" } -Body \$payload
return (\$resp | ConvertTo-Json -Depth 6)
}

function Run-Pipeline(\[string]\$IndexPath) {
\$digest = Build-Digest -IndexPath \$IndexPath
\$outDir = \$Global\:Config.Pipeline.OutputDir
\$summaryPath = Join-Path \$outDir ("summary\_" + \$Global\:Config.Pipeline.CaseId + "\_" + (Get-Date -Format "yyyyMMdd\_HHmmss") + ".txt")

\$mode = \$Global\:Config.Pipeline.SendTo
\$text = \$null
switch (\$mode) {
"OpenAI"   { \$text = Send-ToOpenAI \$digest }
"LocalLLM" { \$text = Send-ToLocalLLM \$digest }
"Webhook"  { \$text = Send-ToWebhook \$digest }
default    { Write-Log WARN ("Unknown Pipeline.SendTo '{0}'" -f \$mode) }
}

if (\$text) {
Set-Content -Path \$summaryPath -Value \$text -Encoding UTF8
Write-Log SUCCESS "Pipeline summary written: \$summaryPath"
} else {
Write-Log WARN "No pipeline output generated."
}
}

# ------------------------------

# Orchestration

# ------------------------------

Write-Log INFO "==== Litigation Pipeline Start ===="
if (\$DryRun) { Write-Log WARN "DRY-RUN mode active (no changes will be made)" }
if (\$Offline) { Write-Log INFO "Offline mode: using Local LLM by default" }

# 1) Ensure services (rclone mounts via NSSM)

Setup-Rclone-Services

# 2) Organize files

Organize-Drives

# 3) Index files

\$indexPath = Index-FilesToJson

# 4) Pipeline summaries (GPT/local/webhook)

Run-Pipeline -IndexPath \$indexPath

Write-Log SUCCESS "==== Pipeline Complete ===="
Write-Host "`nLog file: $Global:LogFile`n" -ForegroundColor Cyan
