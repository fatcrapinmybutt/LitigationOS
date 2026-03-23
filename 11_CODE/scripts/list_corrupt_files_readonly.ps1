<#
Drive Integrity Toolkit — LIST-ONLY MODE — v3

GOAL
  Produce a list of *suspect/unreadable* files on one or more drives WITHOUT attempting any repair.
  This script does NOT delete, move, or modify user files.

IMPORTANT REALITY CHECK
  - Windows/NTFS can record corruption in internal metadata (e.g., $corrupt). Enumerating that log is read-only,
    but populating it requires a scan (e.g., chkdsk /scan or Repair-Volume -Scan) which may write metadata.
  - A "read test" detects unreadable files (I/O errors) but cannot detect silent corruption where reads succeed.

USAGE (Administrator recommended)
  powershell -ExecutionPolicy Bypass -File .\list_corrupt_files_readonly.ps1 -Drives F,H,I,J

OUTPUT
  One CSV file (default: Desktop\corrupt_files_<RUNID>.csv). No per-drive log folders are created.

#>

[CmdletBinding()]
param(
  [Parameter(Mandatory=$false)]
  [string[]]$Drives = @('F','H','I','J'),

  [Parameter(Mandatory=$false)]
  [ValidateSet('Auto','ReadTest','NtfsCorruptLog')]
  [string]$Technique = 'Auto',

  [Parameter(Mandatory=$false)]
  [string]$OutputFile = '',

  [Parameter(Mandatory=$false)]
  [switch]$SkipReadTest,

  [Parameter(Mandatory=$false)]
  [switch]$SkipNtfsCorruptLog,

  [Parameter(Mandatory=$false)]
  [int]$ReadChunkMB = 4,

  [Parameter(Mandatory=$false)]
  [switch]$FailFast,

  [Parameter(Mandatory=$false)]
  [string[]]$ExcludePathContains = @(),

  [Parameter(Mandatory=$false)]
  [int64]$MaxBytesPerFile = 0,

  [Parameter(Mandatory=$false)]
  [int]$MaxFilesPerDrive = 0
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

function New-RunId { return (Get-Date -Format "yyyyMMdd_HHmmss") + "_" + ([Guid]::NewGuid().ToString('N').Substring(0,8)) }

function Normalize-Drive([string]$d) {
  $x = ($d ?? '').Trim().TrimEnd(':').ToUpperInvariant()
  if ($x.Length -ne 1) { return '' }
  if ($x -notmatch '^[A-Z]$') { return '' }
  return $x
}

function Should-ExcludePath([string]$path, [string[]]$rules) {
  if (-not $rules -or $rules.Count -eq 0) { return $false }
  foreach ($r in $rules) {
    if (-not $r) { continue }
    if ($path -like "*$r*") { return $true }
  }
  return $false
}

function Invoke-Cmd {
  param([Parameter(Mandatory=$true)][string]$CommandLine)
  $pinfo = New-Object System.Diagnostics.ProcessStartInfo
  $pinfo.FileName = 'cmd.exe'
  $pinfo.Arguments = '/c ' + $CommandLine
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
  return [pscustomobject]@{ ExitCode=$proc.ExitCode; StdOut=$stdout; StdErr=$stderr }
}

function Try-GetVolume([string]$drive) {
  try { return Get-Volume -DriveLetter $drive -ErrorAction Stop } catch { return $null }
}

function Get-FilesRecursive([string]$root, [int]$maxFiles) {
  # Robust directory walk; skips directories it cannot enter.
  $results = New-Object System.Collections.Generic.List[string]
  $stack = New-Object System.Collections.Generic.Stack[string]
  $stack.Push($root)

  while ($stack.Count -gt 0) {
    $dir = $stack.Pop()

    # Enumerate files
    try {
      foreach ($f in [System.IO.Directory]::EnumerateFiles($dir)) {
        $results.Add($f)
        if ($maxFiles -gt 0 -and $results.Count -ge $maxFiles) { return $results }
      }
    } catch {
      # swallow
    }

    # Enumerate subdirectories
    try {
      foreach ($sd in [System.IO.Directory]::EnumerateDirectories($dir)) {
        $stack.Push($sd)
      }
    } catch {
      # swallow
    }
  }

  return $results
}

function ReadTest-File([string]$path, [int]$chunkMB, [int64]$maxBytes) {
  $bufSize = [Math]::Max(1024*1024, $chunkMB * 1024 * 1024)
  $buffer = New-Object byte[] $bufSize

  $fs = $null
  try {
    $fs = New-Object System.IO.FileStream(
      $path,
      [System.IO.FileMode]::Open,
      [System.IO.FileAccess]::Read,
      [System.IO.FileShare]::ReadWrite,
      $bufSize,
      [System.IO.FileOptions]::SequentialScan
    )

    $total = 0L
    while ($true) {
      $toRead = $buffer.Length
      if ($maxBytes -gt 0) {
        $remaining = $maxBytes - $total
        if ($remaining -le 0) { break }
        if ($remaining -lt $toRead) { $toRead = [int]$remaining }
      }

      $n = $fs.Read($buffer, 0, $toRead)
      if ($n -le 0) { break }
      $total += $n
    }

    return [pscustomobject]@{ Ok=$true; BytesRead=$total; ErrorType=''; ErrorMessage='' }
  } catch {
    $ex = $_.Exception
    return [pscustomobject]@{ Ok=$false; BytesRead=0; ErrorType=$ex.GetType().FullName; ErrorMessage=$ex.Message }
  } finally {
    if ($fs) { try { $fs.Dispose() } catch {} }
  }
}

function Parse-FsutilRepairEnumerate([string]$text) {
  # Returns file reference numbers (as strings, like 0x0000000000000000)
  $ids = New-Object System.Collections.Generic.List[string]
  $lines = ($text ?? '').Split([Environment]::NewLine)
  foreach ($ln in $lines) {
    $m = [Regex]::Match($ln, '0x[0-9a-fA-F]+')
    if ($m.Success) { $ids.Add($m.Value.ToLowerInvariant()) }
  }
  return $ids
}

function Query-PathByFileId([string]$drive, [string]$fileIdHex) {
  # fsutil file queryfilenamebyid <volume>: <fileid>
  $res = Invoke-Cmd -CommandLine ("fsutil file queryfilenamebyid {0}: {1}" -f $drive, $fileIdHex)
  $out = (($res.StdOut ?? '') + "\n" + ($res.StdErr ?? '')).Trim()
  if ($res.ExitCode -ne 0 -or -not $out) { return '' }

  # Output is usually a full path like: \\?\Volume{GUID}\path\file
  # or a path rooted to the volume. We'll return the first non-empty line.
  foreach ($ln in $out.Split([Environment]::NewLine)) {
    $t = $ln.Trim()
    if ($t) { return $t }
  }
  return ''
}

$runId = New-RunId
if (-not $OutputFile) {
  $desktop = [Environment]::GetFolderPath('Desktop')
  if (-not $desktop) { $desktop = $env:USERPROFILE }
  $OutputFile = Join-Path $desktop ("corrupt_files_{0}.csv" -f $runId)
}

$wantNtfs = ($Technique -eq 'Auto' -or $Technique -eq 'NtfsCorruptLog') -and (-not $SkipNtfsCorruptLog)
$wantRead = ($Technique -eq 'Auto' -or $Technique -eq 'ReadTest') -and (-not $SkipReadTest)

$results = New-Object System.Collections.Generic.List[object]
$admin = Test-IsAdmin

foreach ($d in $Drives) {
  $drive = Normalize-Drive $d
  if (-not $drive) { continue }

  $vol = Try-GetVolume $drive
  if ($null -eq $vol) {
    $results.Add([pscustomobject]@{
      Drive="$drive`:"; FullPath=''; FindingSource='SCRIPT'; Category='DriveMissing'; Details='Drive not found / no drive letter mounted.'; FileId=''
    })
    if ($FailFast) { break }
    continue
  }

  $fs = ($vol.FileSystem ?? '').ToUpperInvariant()

  # A) NTFS $corrupt / $verify enumeration (read-only, but requires admin)
  if ($wantNtfs -and $fs -eq 'NTFS') {
    if (-not $admin) {
      $results.Add([pscustomobject]@{
        Drive="$drive`:"; FullPath=''; FindingSource='NTFS'; Category='AdminRequired'; Details='Not running as Administrator; skipping fsutil repair enumerate.'; FileId=''
      })
    } else {
      foreach ($stream in @('$corrupt','$verify')) {
        try {
          $enum = Invoke-Cmd -CommandLine ("fsutil repair enumerate {0}: {1}" -f $drive, $stream)
          $ids = Parse-FsutilRepairEnumerate (($enum.StdOut ?? '') + "\n" + ($enum.StdErr ?? ''))
          foreach ($id in $ids) {
            $pathGuess = ''
            try { $pathGuess = Query-PathByFileId -drive $drive -fileIdHex $id } catch { $pathGuess = '' }
            $results.Add([pscustomobject]@{
              Drive="$drive`:"; FullPath=$pathGuess; FindingSource="NTFS_{0}" -f $stream; Category='CorruptionLogged'; Details='Entry present in NTFS corruption log stream.'; FileId=$id
            })
          }
        } catch {
          $results.Add([pscustomobject]@{
            Drive="$drive`:"; FullPath=''; FindingSource="NTFS_{0}" -f $stream; Category='EnumerateFailed'; Details=$_.Exception.Message; FileId=''
          })
        }
      }
    }
  }

  # B) Read test (detects unreadable files / IO errors)
  if ($wantRead) {
    $root = "$drive`:\\"
    $files = Get-FilesRecursive -root $root -maxFiles $MaxFilesPerDrive

    foreach ($path in $files) {
      if (Should-ExcludePath -path $path -rules $ExcludePathContains) { continue }

      $rt = ReadTest-File -path $path -chunkMB $ReadChunkMB -maxBytes $MaxBytesPerFile
      if (-not $rt.Ok) {
        $results.Add([pscustomobject]@{
          Drive="$drive`:"; FullPath=$path; FindingSource='READ_TEST'; Category='Unreadable'; Details=("{0}: {1}" -f $rt.ErrorType, $rt.ErrorMessage); FileId=''
        })
        if ($FailFast) { break }
      }
    }
  }
}

# De-dup rows (same drive+path+source+category)
$dedup = @{}
$final = New-Object System.Collections.Generic.List[object]
foreach ($r in $results) {
  $k = "{0}|{1}|{2}|{3}|{4}" -f ($r.Drive ?? ''), ($r.FullPath ?? ''), ($r.FindingSource ?? ''), ($r.Category ?? ''), ($r.FileId ?? '')
  if (-not $dedup.ContainsKey($k)) { $dedup[$k] = $true; $final.Add($r) }
}

# Write exactly ONE output file
$final | Export-Csv -NoTypeInformation -Encoding UTF8 -Path $OutputFile

# Minimal console summary
$grouped = $final | Group-Object Category | Sort-Object Count -Descending
Write-Host "\nWROTE: $OutputFile" -ForegroundColor Green
Write-Host "Findings summary:" -ForegroundColor Cyan
foreach ($g in $grouped) {
  Write-Host ("  {0,-20} {1,6}" -f $g.Name, $g.Count)
}

