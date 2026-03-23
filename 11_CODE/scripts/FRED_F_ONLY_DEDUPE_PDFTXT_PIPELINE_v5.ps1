<#
FRED_F_ONLY_DEDUPE_PDFTXT_PIPELINE_v5.ps1

v5 upgrades (over v4)
1) Resume ledger (restart-safe, incremental):
   - Skips re-fingerprinting unchanged files using a stable key:
     (FullPathLower, Size, LastWriteTimeUtcTicks)
   - Stores per-file fingerprint in: F:\INGEST\ledger\fp_index.jsonl (append-only)
   - Maintains a compact "latest view" cache: F:\INGEST\ledger\fp_index_latest.json (rewritten safely)

2) Canonical keeper index (content pointer map):
   - For each confirmed duplicate set, writes a canonical mapping record:
     Fingerprint -> KeeperPath + DuplicatePaths moved
   - Stored as JSONL: F:\INGEST\ledger\canon_index.jsonl

3) Safer move semantics:
   - Confirms exact equality via byte-by-byte compare prior to moving.
   - Preserves relative path under F:\DUPLICATES\F\...

4) PDF extraction is unchanged in concept but now:
   - Writes a pointer in canon_index linking extracted JSON to the source PDF.
   - Skips PDFs already extracted by doc_id.

Still true
- No SHA-256.
- Default scope: F:\ only.
- Default action: MOVE duplicates into F:\DUPLICATES (keeper stays put).
- Excludes: F:\DUPLICATES, F:\TEXT_INGESTION, F:\INGEST (configurable).
- Supports -WhatIf.

Run
  pwsh -ExecutionPolicy Bypass -File .\FRED_F_ONLY_DEDUPE_PDFTXT_PIPELINE_v5.ps1 -Mode DEDUPE -WhatIf
  pwsh -ExecutionPolicy Bypass -File .\FRED_F_ONLY_DEDUPE_PDFTXT_PIPELINE_v5.ps1 -Mode DEDUPE
  pwsh -ExecutionPolicy Bypass -File .\FRED_F_ONLY_DEDUPE_PDFTXT_PIPELINE_v5.ps1 -Mode DEDUPE -Threads 8
  pwsh -ExecutionPolicy Bypass -File .\FRED_F_ONLY_DEDUPE_PDFTXT_PIPELINE_v5.ps1 -Mode PDFTXT
  pwsh -ExecutionPolicy Bypass -File .\FRED_F_ONLY_DEDUPE_PDFTXT_PIPELINE_v5.ps1 -Mode BOTH

#>

[CmdletBinding(SupportsShouldProcess=$true)]
param(
  [ValidateSet("DEDUPE","PDFTXT","BOTH")]
  [string]$Mode = "DEDUPE",

  [string]$Root = "F:\",

  [string]$DuplicatesDir = "F:\DUPLICATES",
  [string]$TextIngestDir = "F:\TEXT_INGESTION",
  [string]$LedgerDir = "F:\INGEST\ledger",

  # Dedupe knobs
  [int]$HeadBytes = 65536,          # 64 KiB
  [int]$TailBytes = 65536,          # 64 KiB
  [int]$MinSizeBytes = 1,           # ignore empty by default
  [int]$Threads = 0,                # 0 = single-thread; >0 uses ForEach-Object -Parallel for fingerprinting
  [switch]$IncludeHiddenSystem,      # include hidden/system if set
  [string[]]$ExcludeDirs = @("F:\DUPLICATES","F:\TEXT_INGESTION","F:\INGEST"),

  # PDF extraction knobs
  [switch]$WriteTxt,                # also write .txt alongside .json
  [switch]$TryInstallPdfDeps,        # attempts venv+pip install pymupdf into F:\_py\venv_litos (best-effort)
  [string]$VenvDir = "F:\_py\venv_litos",
  [string]$PipCacheDir = "F:\_py\pip_cache",
  [string]$TmpDir = "F:\_py\tmp"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Ensure-Dir([string]$p){ if (-not (Test-Path -LiteralPath $p)) { New-Item -ItemType Directory -Path $p -Force | Out-Null } }
Ensure-Dir $LedgerDir
Ensure-Dir $DuplicatesDir
Ensure-Dir $TextIngestDir

function Normalize([string]$p){ return ([System.IO.Path]::GetFullPath($p)).TrimEnd('\') }

$RootN = Normalize $Root
if (-not (Test-Path -LiteralPath $RootN)) { throw "Root not found: $RootN" }

# Exclude roots
$ExcludeRoots = @()
foreach ($d in $ExcludeDirs){
  try { $ExcludeRoots += (Normalize $d) } catch { }
}

function Is-Excluded([string]$full){
  $f = Normalize $full
  foreach ($e in $ExcludeRoots){
    if ($f.StartsWith($e, [System.StringComparison]::OrdinalIgnoreCase)) { return $true }
  }
  return $false
}

$RunId = (Get-Date).ToString("yyyyMMdd_HHmmss")
$RunLog = Join-Path $LedgerDir ("run_{0}.log" -f $RunId)

# Ledgers (append-only)
$DupeLedger = Join-Path $LedgerDir ("dupes_{0}.jsonl" -f $RunId)
$PdfLedger  = Join-Path $LedgerDir ("pdf_{0}.jsonl" -f $RunId)
$FpIndex    = Join-Path $LedgerDir "fp_index.jsonl"
$FpLatest   = Join-Path $LedgerDir "fp_index_latest.json"
$CanonIndex = Join-Path $LedgerDir "canon_index.jsonl"

function Log([string]$m){
  $t = (Get-Date).ToString("s")
  "$t`t$m" | Out-File -FilePath $RunLog -Append -Encoding utf8
  Write-Host $m
}
function JLine([string]$path, [hashtable]$obj){
  ($obj | ConvertTo-Json -Depth 12 -Compress) | Out-File -FilePath $path -Append -Encoding utf8
}

# -------- Load latest FP cache (compact) --------
$FpCache = @{}  # key -> fp
if (Test-Path -LiteralPath $FpLatest){
  try {
    $raw = Get-Content -LiteralPath $FpLatest -Raw -Encoding utf8
    if ($raw -and $raw.Trim().Length -gt 0){
      $tmp = $raw | ConvertFrom-Json
      if ($tmp){
        foreach ($k in $tmp.PSObject.Properties.Name){
          $FpCache[$k] = $tmp.$k
        }
      }
    }
    Log "Loaded FP cache entries: $($FpCache.Count)"
  } catch {
    Log "Warning: failed to load fp_index_latest.json; will rebuild incrementally."
  }
}

function Save-FpCache {
  # atomic-ish write
  $tmp = $FpLatest + ".tmp"
  ($FpCache | ConvertTo-Json -Depth 6) | Out-File -FilePath $tmp -Encoding utf8
  Move-Item -LiteralPath $tmp -Destination $FpLatest -Force
}

# -------- CRC32 --------
function Get-Crc32Bytes([byte[]]$bytes){
  $crc = 0xFFFFFFFF
  foreach ($b in $bytes){
    $crc = $crc -bxor $b
    for ($i=0; $i -lt 8; $i++){
      if (($crc -band 1) -ne 0){ $crc = (0xEDB88320 -bxor ($crc -shr 1)) } else { $crc = ($crc -shr 1) }
    }
  }
  return ($crc -bxor 0xFFFFFFFF)
}

function Read-HeadTail([string]$path, [int]$headN, [int]$tailN){
  $fs = [System.IO.File]::Open($path, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite)
  try {
    $len = $fs.Length
    $head = New-Object byte[] ([Math]::Min($headN, $len))
    [void]$fs.Read($head, 0, $head.Length)
    $tailLen = [Math]::Min($tailN, $len)
    $tail = New-Object byte[] $tailLen
    if ($tailLen -gt 0){
      $fs.Seek(-$tailLen, [System.IO.SeekOrigin]::End) | Out-Null
      [void]$fs.Read($tail, 0, $tail.Length)
    }
    return @{ Len = $len; Head = $head; Tail = $tail }
  } finally { $fs.Dispose() }
}

function Fingerprint([string]$path){
  $ht = Read-HeadTail $path $HeadBytes $TailBytes
  $h = Get-Crc32Bytes $ht.Head
  $t = Get-Crc32Bytes $ht.Tail
  return "{0:X8}-{1:X8}-{2}" -f $h, $t, $ht.Len
}

function FileKey([System.IO.FileInfo]$fi){
  # stable key for "unchanged enough" purposes
  # PathLower|Size|LastWriteTicks
  return ("{0}|{1}|{2}" -f $fi.FullName.ToLowerInvariant(), $fi.Length, $fi.LastWriteTimeUtc.Ticks)
}

function Get-FingerprintCached([System.IO.FileInfo]$fi){
  $k = FileKey $fi
  if ($FpCache.ContainsKey($k)) { return $FpCache[$k] }
  return $null
}

function Set-FingerprintCached([System.IO.FileInfo]$fi, [string]$fp){
  $k = FileKey $fi
  $FpCache[$k] = $fp
  # append audit record
  JLine $FpIndex @{ ts=(Get-Date).ToString("o"); kind="FP_SET"; key=$k; path=$fi.FullName; fp=$fp; size=$fi.Length; lwt_utc=$fi.LastWriteTimeUtc.ToString("o") }
}

function ByteEquals([string]$a, [string]$b){
  $fa = [System.IO.File]::Open($a, 'Open', 'Read', 'ReadWrite')
  $fb = [System.IO.File]::Open($b, 'Open', 'Read', 'ReadWrite')
  try {
    if ($fa.Length -ne $fb.Length) { return $false }
    $bufA = New-Object byte[] 1048576
    $bufB = New-Object byte[] 1048576
    while ($true){
      $ra = $fa.Read($bufA, 0, $bufA.Length)
      $rb = $fb.Read($bufB, 0, $bufB.Length)
      if ($ra -ne $rb) { return $false }
      if ($ra -eq 0) { break }
      for ($i=0; $i -lt $ra; $i++){
        if ($bufA[$i] -ne $bufB[$i]) { return $false }
      }
    }
    return $true
  } finally { $fa.Dispose(); $fb.Dispose() }
}

function PathDepth([string]$p){
  $norm = (Normalize $p)
  return ($norm -split '\\').Count
}

function Choose-Keeper([string[]]$paths){
  $best = $null
  foreach ($p in $paths){
    try {
      $fi = Get-Item -LiteralPath $p -Force
      $cand = [PSCustomObject]@{
        Path = $p
        Depth = PathDepth $p
        Len = ($p.Length)
        LWT = $fi.LastWriteTimeUtc
      }
      if ($null -eq $best){ $best = $cand; continue }
      if ($cand.Depth -lt $best.Depth){ $best = $cand; continue }
      if ($cand.Depth -eq $best.Depth){
        if ($cand.Len -lt $best.Len){ $best = $cand; continue }
        if ($cand.Len -eq $best.Len){
          if ($cand.LWT -lt $best.LWT){ $best = $cand; continue }
          if ($cand.LWT -eq $best.LWT){
            if ($cand.Path -lt $best.Path){ $best = $cand; continue }
          }
        }
      }
    } catch { continue }
  }
  return $best.Path
}

function Move-ToDuplicates([string]$src){
  $srcN = Normalize $src
  $rel = $srcN.Substring($RootN.Length).TrimStart('\')
  $targetBase = Join-Path $DuplicatesDir ("F\{0}" -f $rel)
  $targetDir = Split-Path -Parent $targetBase
  Ensure-Dir $targetDir

  $target = $targetBase
  $n = 1
  while (Test-Path -LiteralPath $target){
    $ext = [System.IO.Path]::GetExtension($targetBase)
    $noext = $targetBase.Substring(0, $targetBase.Length - $ext.Length)
    $target = ("{0}-dup-{1}{2}" -f $noext, $n, $ext)
    $n++
  }

  if ($PSCmdlet.ShouldProcess($src, "Move duplicate to $target")){
    Move-Item -LiteralPath $src -Destination $target -Force
  }
  return $target
}

function Get-AllFiles([string]$root){
  Log "Enumerating files under $root ..."
  $files = Get-ChildItem -LiteralPath $root -Recurse -File -Force -ErrorAction SilentlyContinue
  $out = New-Object System.Collections.Generic.List[System.IO.FileInfo]
  foreach ($f in $files){
    if (Is-Excluded $f.FullName) { continue }
    if ($f.Length -lt $MinSizeBytes) { continue }
    if (-not $IncludeHiddenSystem){
      $attr = $f.Attributes
      if (($attr -band [IO.FileAttributes]::Hidden) -ne 0) { continue }
      if (($attr -band [IO.FileAttributes]::System) -ne 0) { continue }
    }
    $out.Add($f) | Out-Null
  }
  Log ("Files considered: {0}" -f $out.Count)
  return $out
}

function Find-And-Move-Duplicates {
  $files = Get-AllFiles $RootN

  Log "Grouping by size ..."
  $bySize = @{}
  foreach ($f in $files){
    $k = [string]$f.Length
    if (-not $bySize.ContainsKey($k)) { $bySize[$k] = New-Object System.Collections.Generic.List[System.IO.FileInfo] }
    $bySize[$k].Add($f) | Out-Null
  }

  $sizeCandidates = @()
  foreach ($k in $bySize.Keys){
    if ($bySize[$k].Count -gt 1){ $sizeCandidates += ,@($bySize[$k]) }
  }
  Log ("Size candidate groups: {0}" -f $sizeCandidates.Count)

  # Build fingerprint groups with caching
  $fingerGroups = @{} # fp -> list[path]
  $todo = New-Object System.Collections.Generic.List[System.IO.FileInfo]
  foreach ($grp in $sizeCandidates){
    foreach ($fi in $grp){
      $fp = Get-FingerprintCached $fi
      if ($fp){
        if (-not $fingerGroups.ContainsKey($fp)) { $fingerGroups[$fp] = New-Object System.Collections.Generic.List[string] }
        $fingerGroups[$fp].Add($fi.FullName) | Out-Null
      } else {
        $todo.Add($fi) | Out-Null
      }
    }
  }
  Log ("Fingerprint cache hits: {0}" -f ($files.Count - $todo.Count))

  if ($todo.Count -gt 0){
    if ($Threads -gt 0){
      Log "Fingerprinting remaining files in parallel: $($todo.Count) (Threads=$Threads)"
      $results = $todo | ForEach-Object -Parallel {
        param($headBytes,$tailBytes)
        function Get-Crc32BytesLocal([byte[]]$bytes){
          $crc = 0xFFFFFFFF
          foreach ($b in $bytes){
            $crc = $crc -bxor $b
            for ($i=0; $i -lt 8; $i++){
              if (($crc -band 1) -ne 0){ $crc = (0xEDB88320 -bxor ($crc -shr 1)) } else { $crc = ($crc -shr 1) }
            }
          }
          return ($crc -bxor 0xFFFFFFFF)
        }
        function ReadHeadTailLocal([string]$path,[int]$headN,[int]$tailN){
          $fs = [System.IO.File]::Open($path, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite)
          try {
            $len = $fs.Length
            $head = New-Object byte[] ([Math]::Min($headN, $len))
            [void]$fs.Read($head, 0, $head.Length)
            $tailLen = [Math]::Min($tailN, $len)
            $tail = New-Object byte[] $tailLen
            if ($tailLen -gt 0){
              $fs.Seek(-$tailLen, [System.IO.SeekOrigin]::End) | Out-Null
              [void]$fs.Read($tail, 0, $tail.Length)
            }
            return @{ Len=$len; Head=$head; Tail=$tail }
          } finally { $fs.Dispose() }
        }
        try {
          $ht = ReadHeadTailLocal $_.FullName $headBytes $tailBytes
          $h = Get-Crc32BytesLocal $ht.Head
          $t = Get-Crc32BytesLocal $ht.Tail
          $fp = "{0:X8}-{1:X8}-{2}" -f $h, $t, $ht.Len
          [PSCustomObject]@{ Path=$_.FullName; FP=$fp; Size=$_.Length; LWT=$_.LastWriteTimeUtc.Ticks }
        } catch {
          [PSCustomObject]@{ Path=$_.FullName; FP=$null; Err="$_" }
        }
      } -ThrottleLimit $Threads -ArgumentList $HeadBytes,$TailBytes

      foreach ($r in $results){
        if (-not $r.FP) { continue }
        $fi = Get-Item -LiteralPath $r.Path -Force
        # update cache
        # reconstruct key same as FileKey
        $k = ("{0}|{1}|{2}" -f $fi.FullName.ToLowerInvariant(), $fi.Length, $fi.LastWriteTimeUtc.Ticks)
        $FpCache[$k] = $r.FP
        JLine $FpIndex @{ ts=(Get-Date).ToString("o"); kind="FP_SET"; key=$k; path=$fi.FullName; fp=$r.FP; size=$fi.Length; lwt_utc=$fi.LastWriteTimeUtc.ToString("o") }

        if (-not $fingerGroups.ContainsKey($r.FP)) { $fingerGroups[$r.FP] = New-Object System.Collections.Generic.List[string] }
        $fingerGroups[$r.FP].Add($r.Path) | Out-Null
      }
    } else {
      Log "Fingerprinting remaining files (single-thread): $($todo.Count)"
      foreach ($fi in $todo){
        try {
          $fp = Fingerprint $fi.FullName
          Set-FingerprintCached $fi $fp
          if (-not $fingerGroups.ContainsKey($fp)) { $fingerGroups[$fp] = New-Object System.Collections.Generic.List[string] }
          $fingerGroups[$fp].Add($fi.FullName) | Out-Null
        } catch {
          Log "ERROR fingerprinting $($fi.FullName) :: $_"
        }
      }
    }
    Save-FpCache
    Log "Saved FP cache entries: $($FpCache.Count)"
  }

  $dupeSets = @()
  foreach ($fp in $fingerGroups.Keys){
    if ($fingerGroups[$fp].Count -gt 1){
      $dupeSets += [PSCustomObject]@{ Fingerprint=$fp; Paths=$fingerGroups[$fp].ToArray() }
    }
  }
  Log ("Fingerprint candidate sets: {0}" -f $dupeSets.Count)

  $moved = 0
  foreach ($set in $dupeSets){
    $paths = $set.Paths
    $keeper = Choose-Keeper $paths
    if (-not $keeper) { continue }

    # Confirm exact duplicates by byte-compare against keeper
    $confirmed = New-Object System.Collections.Generic.List[string]
    $confirmed.Add($keeper) | Out-Null
    foreach ($p in $paths){
      if ($p -eq $keeper) { continue }
      try {
        if (ByteEquals $keeper $p){
          $confirmed.Add($p) | Out-Null
        } else {
          JLine $DupeLedger @{ run_id=$RunId; kind="FP_COLLISION"; fp=$set.Fingerprint; keeper=$keeper; other=$p; action="SKIP_NOT_EQUAL" }
        }
      } catch {
        JLine $DupeLedger @{ run_id=$RunId; kind="COMPARE_ERROR"; fp=$set.Fingerprint; keeper=$keeper; other=$p; error="$($_)" }
      }
    }
    if ($confirmed.Count -le 1){ continue }

    # Record canonical mapping for this content
    JLine $CanonIndex @{
      ts=(Get-Date).ToString("o"); kind="CANON_SET"; fp=$set.Fingerprint
      keeper=$keeper; confirmed_count=$confirmed.Count
    }

    foreach ($p in $confirmed){
      if ($p -eq $keeper) { continue }
      $obj = @{
        run_id=$RunId; kind="DUPLICATE_FILE"; fp=$set.Fingerprint
        keeper=$keeper; duplicate=$p
        keeper_depth=(PathDepth $keeper); dupe_depth=(PathDepth $p)
      }
      try {
        $dest = Move-ToDuplicates $p
        $obj["action"]="MOVED"; $obj["dest"]=$dest
        $moved++
        # append canonical move record
        JLine $CanonIndex @{ ts=(Get-Date).ToString("o"); kind="CANON_MOVE"; fp=$set.Fingerprint; keeper=$keeper; moved_from=$p; moved_to=$dest }
      } catch {
        $obj["action"]="MOVE_ERROR"; $obj["error"]="$($_)"
        JLine $CanonIndex @{ ts=(Get-Date).ToString("o"); kind="CANON_MOVE_ERROR"; fp=$set.Fingerprint; keeper=$keeper; moved_from=$p; error="$($_)" }
      }
      JLine $DupeLedger $obj
    }
  }

  Log ("Duplicates moved: {0}" -f $moved)
}

# -------- PDF text extraction (best-effort) --------
function Resolve-Python {
  $cmd = Get-Command python -ErrorAction SilentlyContinue
  if ($cmd) { return $cmd.Path }
  return $null
}

function Bootstrap-PdfDeps {
  Ensure-Dir (Split-Path -Parent $VenvDir)
  Ensure-Dir $PipCacheDir
  Ensure-Dir $TmpDir
  $env:TEMP = $TmpDir
  $env:TMP  = $TmpDir
  $env:PIP_CACHE_DIR = $PipCacheDir

  $py = Resolve-Python
  if (-not $py) { throw "Python not found on PATH." }

  $venvPy = Join-Path $VenvDir "Scripts\python.exe"
  if (-not (Test-Path -LiteralPath $venvPy)){
    Log "Creating venv at $VenvDir"
    & $py -m venv $VenvDir
  }
  if (-not (Test-Path -LiteralPath $venvPy)) { throw "venv creation failed at $VenvDir" }

  Log "Ensuring pip in venv"
  & $venvPy -m ensurepip --upgrade | Out-Null
  & $venvPy -m pip install --upgrade pip wheel setuptools --no-cache-dir | Out-Null
  & $venvPy -m pip install --no-cache-dir pymupdf orjson | Out-Null
  return $venvPy
}

function Write-ExtractorPy([string]$dest){
@"
import json, os, re, sys
from datetime import datetime

def safe_id(path: str) -> str:
  s = path.lower().replace(':','').replace('\\\\','/')
  s = re.sub(r'[^a-z0-9/_\\.-]+','_',s)
  return s.strip('_').replace('/','__')

def extract_pdf(pdf_path: str):
  try:
    import fitz
  except Exception as e:
    return {"ok": False, "error": f"pymupdf_missing:{e}"}
  try:
    doc = fitz.open(pdf_path)
    pages = []
    for i in range(doc.page_count):
      t = doc.load_page(i).get_text("text") or ""
      pages.append({"page": i+1, "text": t})
    meta = dict(doc.metadata or {})
    doc.close()
    return {"ok": True, "meta": meta, "pages": pages}
  except Exception as e:
    return {"ok": False, "error": str(e)}

def main():
  if len(sys.argv) < 5:
    print("usage: extractor.py <root> <outdir> <ledger_jsonl> <exclude_prefix_lower> [--txt]")
    sys.exit(2)
  root, outdir, ledger, excl = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
  write_txt = ("--txt" in sys.argv[5:])
  os.makedirs(outdir, exist_ok=True)
  os.makedirs(os.path.dirname(ledger), exist_ok=True)

  for dirpath, _, filenames in os.walk(root):
    if os.path.abspath(dirpath).lower().startswith(excl):
      continue
    for fn in filenames:
      if not fn.lower().endswith(".pdf"):
        continue
      p = os.path.join(dirpath, fn)
      did = safe_id(p)
      out_json = os.path.join(outdir, did + ".json")
      out_txt  = os.path.join(outdir, did + ".txt")
      if os.path.exists(out_json):
        rec = {"ts": datetime.utcnow().isoformat()+"Z","kind":"PDF_SKIP_EXISTS","pdf":p,"out_json":out_json}
        with open(ledger,'a',encoding='utf-8') as f: f.write(json.dumps(rec, ensure_ascii=False) + "\\n")
        continue
      res = extract_pdf(p)
      rec = {"ts": datetime.utcnow().isoformat()+"Z","kind":"PDF_EXTRACT","pdf":p,"out_json":out_json,"ok":res.get("ok",False)}
      if not res.get("ok",False):
        rec["error"]=res.get("error")
        with open(ledger,'a',encoding='utf-8') as f: f.write(json.dumps(rec, ensure_ascii=False) + "\\n")
        continue
      payload = {
        "doc_id": did,
        "source_path": p,
        "extracted_utc": datetime.utcnow().isoformat()+"Z",
        "meta": res.get("meta",{}),
        "pages": res.get("pages",[])
      }
      with open(out_json,'w',encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False)
      if write_txt:
        joined = "\\n\\n".join([pg.get("text","") for pg in payload["pages"]])
        with open(out_txt,'w',encoding='utf-8') as f:
          f.write(joined)
      with open(ledger,'a',encoding='utf-8') as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\\n")

if __name__ == "__main__":
  main()
"@ | Out-File -FilePath $dest -Encoding utf8
}

function Extract-PdfText {
  $py = Resolve-Python
  if (-not $py){
    Log "PDFTXT: SKIP (python not found)"
    return
  }

  $venvPy = Join-Path $VenvDir "Scripts\python.exe"
  $usePy = $py

  if ($TryInstallPdfDeps){
    try {
      $usePy = Bootstrap-PdfDeps
      Log "PDFTXT: using venv python: $usePy"
    } catch {
      Log "PDFTXT: bootstrap failed, falling back to system python: $py"
      $usePy = $py
    }
  } else {
    if (Test-Path -LiteralPath $venvPy) { $usePy = $venvPy }
  }

  $extractor = Join-Path $LedgerDir ("pdf_extractor_{0}.py" -f $RunId)
  Write-ExtractorPy $extractor

  $excl = (Normalize $DuplicatesDir).ToLowerInvariant()
  $args = @($extractor, $RootN, $TextIngestDir, $PdfLedger, $excl)
  if ($WriteTxt) { $args += "--txt" }

  Log "PDFTXT: running: $usePy $($args -join ' ')"
  try {
    & $usePy @args
    # link extracts into canon index
    JLine $CanonIndex @{ ts=(Get-Date).ToString("o"); kind="PDF_EXTRACT_RUN"; root=$RootN; outdir=$TextIngestDir; ledger=$PdfLedger; write_txt=[bool]$WriteTxt }
    Log "PDFTXT: done"
  } catch {
    Log "PDFTXT: ERROR $_"
  }
}

# -------- Main --------
Log "RUN $RunId start"
Log "Mode=$Mode Root=$RootN DuplicatesDir=$DuplicatesDir TextIngestDir=$TextIngestDir Threads=$Threads"

try {
  if ($Mode -eq "DEDUPE" -or $Mode -eq "BOTH"){
    Find-And-Move-Duplicates
  }
  if ($Mode -eq "PDFTXT" -or $Mode -eq "BOTH"){
    Extract-PdfText
  }
  Log "RUN $RunId done"
} catch {
  Log "FATAL: $($_)"
  throw
}
