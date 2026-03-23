<# 
Drive Integrity Toolkit — SAFE MODE — v2
Read-only scan & reporting across multiple drives.
No repairs are performed.

Usage:
  powershell -ExecutionPolicy Bypass -File .\drive_integrity_safe.ps1 -Drives F,H,I,J

Outputs:
  .\logs\<RUN_ID>\ (report.md, summary.json, summary.csv, per-drive logs)

#>

[CmdletBinding()]
param(
  [Parameter(Mandatory=$false)]
  [string[]]$Drives = @('F','H','I','J'),

  [Parameter(Mandatory=$false)]
  [string]$LogRoot = $(Join-Path -Path $PSScriptRoot -ChildPath 'logs')
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Test-IsAdmin {
  try {
    $currentIdentity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentIdentity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
  } catch { return $false }
}

function New-RunId { return (Get-Date -Format "yyyyMMdd_HHmmss") + "_" + ([Guid]::NewGuid().ToString("N").Substring(0,8)) }

function Ensure-Dir([string]$Path) { if (-not (Test-Path -LiteralPath $Path)) { New-Item -ItemType Directory -Path $Path | Out-Null } }

function Write-Text([string]$Path, [string]$Text) { $Text | Out-File -FilePath $Path -Encoding UTF8 }

function Invoke-CmdCapture {
  param(
    [Parameter(Mandatory=$true)][string]$CommandLine,
    [Parameter(Mandatory=$true)][string]$OutFile
  )
  $pinfo = New-Object System.Diagnostics.ProcessStartInfo
  $pinfo.FileName = "cmd.exe"
  $pinfo.Arguments = "/c " + $CommandLine
  $pinfo.RedirectStandardOutput = $true
  $pinfo.RedirectStandardError  = $true
  $pinfo.UseShellExecute = $false
  $pinfo.CreateNoWindow = $true

  $proc = New-Object System.Diagnostics.Process
  $proc.StartInfo = $pinfo
  $null = $proc.Start()
  $stdout = $proc.StandardOutput.ReadToEnd()
  $stderr = $proc.StandardError.ReadToEnd()
  $proc.WaitForExit()
  $exitCode = $proc.ExitCode

  $content = @()
  $content += "=== COMMAND ==="
  $content += $CommandLine
  $content += ""
  if ($stdout) { $content += "=== STDOUT ==="; $content += $stdout.TrimEnd(); $content += "" }
  if ($stderr) { $content += "=== STDERR ==="; $content += $stderr.TrimEnd(); $content += "" }
  $content += "=== EXITCODE ==="
  $content += "$exitCode"
  Write-Text -Path $OutFile -Text ($content -join "`r`n")

  return [pscustomobject]@{ ExitCode=$exitCode; StdOut=$stdout; StdErr=$stderr }
}

function Get-VolumeInfo([string]$DriveLetter) {
  try { return Get-Volume -DriveLetter $DriveLetter -ErrorAction Stop } catch { return $null }
}

function Get-DiskMap([string]$DriveLetter) {
  # Maps a drive letter to underlying disk + partition.
  try {
    $p = Get-Partition -DriveLetter $DriveLetter -ErrorAction Stop
    $d = Get-Disk -Number $p.DiskNumber -ErrorAction Stop
    return [pscustomobject]@{
      DiskNumber = $d.Number
      DiskFriendlyName = $d.FriendlyName
      DiskSerialNumber = $d.SerialNumber
      DiskUniqueId = $d.UniqueId
      PartitionNumber = $p.PartitionNumber
    }
  } catch { return $null }
}

function Get-StorageHealth([int]$DiskNumber) {
  # Best-effort health counters; may not exist on some systems/controllers.
  try {
    $c = Get-StorageReliabilityCounter -DiskNumber $DiskNumber -ErrorAction Stop
    return $c
  } catch {
    return $null
  }
}

function Detect-IssuesFromText([string]$text) {
  $t = ($text ?? "").ToLowerInvariant()
  $issues = New-Object System.Collections.Generic.List[string]
  if ($t -match "windows has scanned the file system and found no problems") { return $issues } # empty
  if ($t -match "found no problems") { return $issues } # common wording
  if ($t -match "has made corrections" -or $t -match "correcting errors") { $issues.Add("Corrections mentioned (unexpected in SAFE MODE) — review log; CHKDSK may have run in repair context via OS policy.") }
  if ($t -match "errors found" -or $t -match "corrupt" -or $t -match "failed" -or $t -match "unrecoverable") { $issues.Add("Errors/corruption indicators present in output.") }
  if ($t -match "bad sectors" -or $t -match "bad clusters") { $issues.Add("Bad sectors/clusters reported — treat disk as suspect; prioritize backup/imaging.") }
  return $issues
}

if (-not (Test-IsAdmin)) {
  throw "This script must be run as Administrator (for fsutil and some storage health queries)."
}

$runId = New-RunId
Ensure-Dir $LogRoot
$runDir = Join-Path $LogRoot $runId
Ensure-Dir $runDir

$summary = @()
$repairPlanLines = New-Object System.Collections.Generic.List[string]
$repairPlanLines.Add("=== REPAIR PLAN (NOT EXECUTED) ===")
$repairPlanLines.Add("This file is generated only when SAFE MODE detects probable issues.")
$repairPlanLines.Add("SAFE MODE never performs repairs. If you proceed, back up first.")
$repairPlanLines.Add("")
$anyIssues = $false

foreach ($d in $Drives) {
  $drive = $d.Trim().TrimEnd(':').ToUpperInvariant()
  if (-not $drive) { continue }

  $vol = Get-VolumeInfo -DriveLetter $drive
  if ($null -eq $vol) {
    $summary += [pscustomobject]@{
      Drive="$drive`:"; Exists=$false; FileSystem=""; Label=""; SizeGB=""; FreeGB="";
      DiskNumber=""; DiskFriendlyName=""; Status="SKIPPED"; DirtyBit=""; Issues="Drive not found."
    }
    continue
  }

  $fs = ($vol.FileSystem ?? "").ToUpperInvariant()
  $diskMap = Get-DiskMap -DriveLetter $drive
  $diskNum = $null
  if ($diskMap) { $diskNum = $diskMap.DiskNumber }

  $health = $null
  if ($diskNum -ne $null) { $health = Get-StorageHealth -DiskNumber $diskNum }

  # Dirty bit (NTFS only)
  $dirtyOut = ""
  $dirtyBit = ""
  try {
    if ($fs -eq "NTFS") {
      $dirtyRes = Invoke-CmdCapture -CommandLine ("fsutil dirty query {0}:" -f $drive) -OutFile (Join-Path $runDir ("{0}_dirty.txt" -f $drive))
      $dirtyOut = ($dirtyRes.StdOut + "`n" + $dirtyRes.StdErr)
      if ($dirtyOut -match "is dirty") { $dirtyBit = "DIRTY" } else { $dirtyBit = "CLEAN/UNKNOWN" }
    } else {
      $dirtyBit = "N/A"
    }
  } catch {
    $dirtyBit = "UNKNOWN"
  }

  # CHKDSK read-only
  $chkdskLog = Join-Path $runDir ("{0}_chkdsk.txt" -f $drive)
  $cmdLine = ""
  if ($fs -eq "NTFS") { $cmdLine = "chkdsk {0}: /scan" -f $drive }
  else { $cmdLine = "chkdsk {0}:" -f $drive } # basic check for exFAT/FAT

  $chk = Invoke-CmdCapture -CommandLine $cmdLine -OutFile $chkdskLog
  $issues = Detect-IssuesFromText ($chk.StdOut + "`n" + $chk.StdErr)

  $issueText = ""
  if ($issues.Count -gt 0) { 
    $issueText = ($issues -join " | ")
    $anyIssues = $true
    $repairPlanLines.Add(("Drive {0}: detected issues; suggested next steps:" -f "$drive`:"))
    $repairPlanLines.Add(("  1) Backup/imaging recommended first (copy-only to a different physical disk)."))
    $repairPlanLines.Add(("  2) Then run: chkdsk {0}: /f" -f $drive))
    $repairPlanLines.Add(("  3) If recurring or bad sectors suspected: chkdsk {0}: /r (slow)" -f $drive))
    $repairPlanLines.Add("")
  }

  # Prepare summary row
  $row = [ordered]@{
    Drive = "$drive`:"
    Exists = $true
    FileSystem = $vol.FileSystem
    Label = $vol.FileSystemLabel
    SizeGB = [Math]::Round(($vol.Size/1GB), 2)
    FreeGB = [Math]::Round(($vol.SizeRemaining/1GB), 2)
    DiskNumber = if ($diskMap) { $diskMap.DiskNumber } else { "" }
    DiskFriendlyName = if ($diskMap) { $diskMap.DiskFriendlyName } else { "" }
    DiskSerialNumber = if ($diskMap) { $diskMap.DiskSerialNumber } else { "" }
    DirtyBit = $dirtyBit
    ChkdskCommand = $cmdLine
    ChkdskLog = $chkdskLog
    Issues = $issueText
  }

  # Attach health counters in a compact way (optional)
  if ($health) {
    $row["ReadErrorsTotal"] = $health.ReadErrorsTotal
    $row["WriteErrorsTotal"] = $health.WriteErrorsTotal
    $row["Temperature"] = $health.Temperature
    $row["Wear"] = $health.Wear
    $row["PowerOnHours"] = $health.PowerOnHours
  }

  $summary += New-Object psobject -Property $row
}

# Write summary files
$summaryJson = Join-Path $runDir "summary.json"
$summaryCsv  = Join-Path $runDir "summary.csv"
$reportMd    = Join-Path $runDir "report.md"

$summary | ConvertTo-Json -Depth 6 | Out-File -FilePath $summaryJson -Encoding UTF8
$summary | Export-Csv -NoTypeInformation -Path $summaryCsv -Encoding UTF8

# Markdown report
$md = New-Object System.Collections.Generic.List[string]
$md.Add("# Drive Integrity SAFE MODE Report")
$md.Add("")
$md.Add("RunId: **$runId**")
$md.Add("Timestamp: **" + (Get-Date).ToString("yyyy-MM-dd HH:mm:ss") + "**")
$md.Add("Drives: **" + ($Drives -join ", ") + "**")
$md.Add("")
$md.Add("## Summary")
$md.Add("")
foreach ($r in $summary) {
  $status = "OK"
  if ($r.Issues -and $r.Issues.Trim().Length -gt 0) { $status = "ISSUES" }
  if (-not $r.Exists) { $status = "MISSING" }
  $md.Add("- **$($r.Drive)** — FS=$($r.FileSystem) Label='$($r.Label)' SizeGB=$($r.SizeGB) FreeGB=$($r.FreeGB) DirtyBit=$($r.DirtyBit) Status=**$status**")
  if ($status -eq "ISSUES") { $md.Add("  - Issues: $($r.Issues)") }
  if ($r.ChkdskLog) { $md.Add("  - Chkdsk log: $($r.ChkdskLog)") }
}
$md.Add("")
$md.Add("## Artifacts")
$md.Add("")
$md.Add("- Summary JSON: `summary.json`")
$md.Add("- Summary CSV: `summary.csv`")
$md.Add("- Per-drive CHKDSK logs: `*_chkdsk.txt`")
$md.Add("")

if ($anyIssues) {
  $repairPlanPath = Join-Path $runDir "REPAIR_PLAN.txt"
  ($repairPlanLines -join "`r`n") | Out-File -FilePath $repairPlanPath -Encoding UTF8
  $md.Add("## Repair Plan Generated")
  $md.Add("")
  $md.Add("SAFE MODE detected probable issues. A suggested repair plan was generated (not executed):")
  $md.Add("")
  $md.Add("- `REPAIR_PLAN.txt`")
  $md.Add("")
} else {
  $md.Add("## Repair Plan")
  $md.Add("")
  $md.Add("No common issue markers detected in output. Review raw logs if you suspect problems.")
  $md.Add("")
}

($md -join "`r`n") | Out-File -FilePath $reportMd -Encoding UTF8

Write-Output ""
Write-Output "SAFE MODE scan complete."
Write-Output "Logs / report folder:"
Write-Output "  $runDir"
Write-Output "Report:"
Write-Output "  $reportMd"
