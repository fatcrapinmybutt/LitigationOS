<# 
GEMINI + MCP Judicial Fleet (MI) — NO-BLOCKERS EDITION
- Monolithic PowerShell 7 script to bootstrap MCP + run a large drafting fleet.
- Always produces deliverables. If required fields are not present in the corpus, the drafts
  explicitly state "UNKNOWN (not found in current corpus)" and include a Verification Addendum.

FREE: Uses your existing free Gemini CLI access + open-source MCP servers via npx.

PHASE 1 DELIVERABLES (Court-Document Drafts):
  A) Michigan Court of Appeals — Original Action / Superintending Control:
     - Complaint for Superintending Control
     - Brief in Support
     - Appendix/Attachment Index
     - Service Plan + (optional) Proof template
  B) Michigan Supreme Court — Application for Leave to Appeal (MCR 7.305):
     - Application for Leave to Appeal (draft)
     - Supporting Brief (draft)
  C) Michigan Judicial Tenure Commission:
     - Request-for-Investigation (RFI) narrative pack + exhibit list

PHASE 2 (High-delta deep scan):
  - High-signal scan of C:\Users\andre\Documents (overrideable)
  - Extract top candidates, mine record defects/contradictions, and upgrade Phase 1 drafts

OUTPUTS:
  <Root>\tooling\gemini_judicial\outputs\<stamp>\PHASE1\DOC_*.md
  <Root>\tooling\gemini_judicial\outputs\<stamp>\PHASE2\...

RUN EXAMPLES:
  # Config only (MCP + agents + authority snapshot)
  .\THIS.ps1 -Phase config

  # Phase 1 (point to a case folder: your curated case corpus)
  .\THIS.ps1 -Phase phase1 -Phase1Target "C:\path\to\case_folder"

  # Phase 2 (deep scan Documents)
  .\THIS.ps1 -Phase phase2

  # Both
  .\THIS.ps1 -Phase both -Phase1Target "C:\path\to\case_folder"

NOTES:
- The script writes Gemini MCP config to: %USERPROFILE%\.gemini\settings.json
- The script writes VS Code MCP config to: <Root>\.vscode\mcp.json
- Authority snapshot is fetched from official Michigan Courts / JTC pages into AUTH_SNAPSHOT.
- "Judicial grade" here means: traditional structure, rule-anchored sections, evidence-cited facts,
  and clean appellate framing. No invented facts; inferences are labeled.

#>

[CmdletBinding()]
param(
  [Parameter(Mandatory=$false)]
  [ValidateSet("config","phase1","phase2","both")]
  [string]$Phase = "config",

  [Parameter(Mandatory=$false)]
  [string]$Root = "C:\Users\andre\Desktop\THE_LITIGATION_OPERATING_SYSTEM",

  [Parameter(Mandatory=$false)]
  [string]$Phase1Target = "",

  [Parameter(Mandatory=$false)]
  [string]$Phase2DocumentsRoot = "C:\Users\andre\Documents",

  [Parameter(Mandatory=$false)]
  [ValidateSet("off","auto","on")]
  [string]$OcrMode = "auto",

  [Parameter(Mandatory=$false)]
  [switch]$EnableWingetInstall,

  [Parameter(Mandatory=$false)]
  [switch]$DryRun,

  [Parameter(Mandatory=$false)]
  [int]$MaxAgents = 50
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ---------------------------
# Logging / helpers
# ---------------------------
function Write-Section([string]$Title) {
  Write-Host ""
  Write-Host ("=" * 92)
  Write-Host $Title
  Write-Host ("=" * 92)
}
function Write-Note([string]$Msg) { Write-Host ("[+] " + $Msg) }
function Write-Warn([string]$Msg) { Write-Warning $Msg }
function Write-Fail([string]$Msg) { throw $Msg }

function Cmd-Exists([string]$Name) {
  return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}
function Ensure-Dir([string]$Path) {
  if (-not (Test-Path -LiteralPath $Path)) {
    if ($DryRun) { Write-Note "DRY-RUN mkdir $Path"; return }
    New-Item -ItemType Directory -Path $Path -Force | Out-Null
  }
}
function Read-JsonFile([string]$Path) {
  if (-not (Test-Path -LiteralPath $Path)) { return $null }
  $raw = Get-Content -LiteralPath $Path -Raw -Encoding UTF8
  if ([string]::IsNullOrWhiteSpace($raw)) { return $null }
  return ($raw | ConvertFrom-Json -Depth 64)
}
function ConvertTo-Hashtable($obj) {
  if ($null -eq $obj) { return $null }
  if ($obj -is [System.Collections.IDictionary]) {
    $ht = [ordered]@{}
    foreach ($k in $obj.Keys) { $ht[$k] = ConvertTo-Hashtable $obj[$k] }
    return $ht
  }
  if ($obj -is [System.Collections.IEnumerable] -and -not ($obj -is [string])) {
    $arr = @()
    foreach ($item in $obj) { $arr += (ConvertTo-Hashtable $item) }
    return $arr
  }
  if ($obj -is [pscustomobject]) {
    $ht = [ordered]@{}
    foreach ($p in $obj.PSObject.Properties) { $ht[$p.Name] = ConvertTo-Hashtable $p.Value }
    return $ht
  }
  return $obj
}
function Write-JsonFile([string]$Path, $Obj) {
  $dir = Split-Path -Parent $Path
  Ensure-Dir $dir
  $json = ($Obj | ConvertTo-Json -Depth 64)
  if ($DryRun) { Write-Note "DRY-RUN write $Path"; return }
  $json | Set-Content -LiteralPath $Path -Encoding UTF8
}
function Write-TextFile([string]$Path, [string]$Text) {
  $dir = Split-Path -Parent $Path
  Ensure-Dir $dir
  if ($DryRun) { Write-Note "DRY-RUN write $Path"; return }
  $Text | Set-Content -LiteralPath $Path -Encoding UTF8
}
function Try-WingetInstall([string]$Id, [string]$Display) {
  if (-not $EnableWingetInstall) { return }
  if (-not (Cmd-Exists "winget")) {
    Write-Warn "winget not found; cannot auto-install $Display."
    return
  }
  Write-Note "winget installing: $Display ($Id)"
  if ($DryRun) { return }
  try {
    winget install --id $Id --source winget --accept-package-agreements --accept-source-agreements | Out-Host
  } catch {
    Write-Warn "winget install failed for $Display. Install manually if needed."
  }
}

# ---------------------------
# MCP config writers
# ---------------------------
function Ensure-GeminiMcpConfig([string]$RootPath, [string]$DocsRoot, [string]$CaseRoot) {
  $GeminiDir = Join-Path $env:USERPROFILE ".gemini"
  $GeminiSettings = Join-Path $GeminiDir "settings.json"
  Ensure-Dir $GeminiDir

  $existing = Read-JsonFile $GeminiSettings
  $existing = ConvertTo-Hashtable $existing
  if ($null -eq $existing) { $existing = [ordered]@{} }
  if (-not $existing.Contains("mcpServers")) { $existing["mcpServers"] = [ordered]@{} }

  # Filesystem scopes (use in prompts)
  $existing["mcpServers"]["fs_root"] = [ordered]@{ command="npx"; args=@("-y","@modelcontextprotocol/server-filesystem",$RootPath) }
  $existing["mcpServers"]["fs_docs"] = [ordered]@{ command="npx"; args=@("-y","@modelcontextprotocol/server-filesystem",$DocsRoot) }
  if (-not [string]::IsNullOrWhiteSpace($CaseRoot)) {
    $existing["mcpServers"]["fs_case"] = [ordered]@{ command="npx"; args=@("-y","@modelcontextprotocol/server-filesystem",$CaseRoot) }
  } else {
    $existing["mcpServers"]["fs_case"] = [ordered]@{ command="npx"; args=@("-y","@modelcontextprotocol/server-filesystem",$DocsRoot) }
  }

  # Search + fetch + memory + git
  $existing["mcpServers"]["ripgrep"] = [ordered]@{ command="npx"; args=@("-y","mcp-ripgrep@latest") }
  $existing["mcpServers"]["fetch"]   = [ordered]@{ command="npx"; args=@("-y","@modelcontextprotocol/server-fetch") }
  $existing["mcpServers"]["git"]     = [ordered]@{ command="npx"; args=@("-y","@modelcontextprotocol/server-git",$RootPath) }
  $existing["mcpServers"]["memory"]  = [ordered]@{ command="npx"; args=@("-y","@modelcontextprotocol/server-memory") }

  Write-JsonFile $GeminiSettings $existing
  Write-Note "Gemini MCP config written: $GeminiSettings"
}

function Ensure-VSCodeMcpConfig([string]$RootPath) {
  $VsCodeMcp = Join-Path $RootPath ".vscode\mcp.json"
  Ensure-Dir (Split-Path -Parent $VsCodeMcp)

  $vsc = Read-JsonFile $VsCodeMcp
  $vsc = ConvertTo-Hashtable $vsc
  if ($null -eq $vsc) { $vsc = [ordered]@{} }
  if (-not $vsc.Contains("servers")) { $vsc["servers"] = [ordered]@{} }

  $vsc["servers"]["filesystem"] = [ordered]@{ command="npx"; args=@("-y","@modelcontextprotocol/server-filesystem",'${workspaceFolder}') }
  $vsc["servers"]["ripgrep"]    = [ordered]@{ command="npx"; args=@("-y","mcp-ripgrep@latest") }
  $vsc["servers"]["fetch"]      = [ordered]@{ command="npx"; args=@("-y","@modelcontextprotocol/server-fetch") }
  $vsc["servers"]["git"]        = [ordered]@{ command="npx"; args=@("-y","@modelcontextprotocol/server-git",'${workspaceFolder}') }
  $vsc["servers"]["memory"]     = [ordered]@{ command="npx"; args=@("-y","@modelcontextprotocol/server-memory") }

  Write-JsonFile $VsCodeMcp $vsc
  Write-Note "VS Code MCP config written: $VsCodeMcp"
}

# ---------------------------
# Authority Snapshot Harvester (official sources only)
# ---------------------------
function Ensure-AuthoritySnapshot([string]$AuthDir) {
  Ensure-Dir $AuthDir
  $manifest = Join-Path $AuthDir "AUTH_SNAPSHOT_MANIFEST.json"

  $targets = @(
    # MCR (Chapter 7) official responsive HTML index (zip-hosted viewer)
    @{ id="MCR_CH7_HTML"; url="https://www.courts.michigan.gov/siteassets/rules-instructions-administrative-orders/michigan-court-rules/court-rules-book-ch-7-responsive-html5.zip/index.html"; file="MCR_Chapter7_index.html" },

    # COA guide to original actions (official)
    @{ id="COA_ORIGINAL_ACTIONS_GUIDE_PDF"; url="https://www.courts.michigan.gov/4a90e2/siteassets/publications/manuals/coa/guide-to-original-actions.pdf"; file="COA_Guide_to_Original_Actions.pdf" },

    # MSC case processing guide (official)
    @{ id="MSC_CASE_PROCESSING_PDF"; url="https://www.courts.michigan.gov/4af555/siteassets/forms/msc/other-msc-forms-and-guides/msc-case-processing.pdf"; file="MSC_Case_Processing.pdf" },

    # JTC RFI form and how-to
    @{ id="JTC_RFI_FORM_PDF"; url="https://cms4files.revize.com/mjtc/file_a_grievance/docs/RFI%20Form%208.8.2023.pdf"; file="JTC_Request_for_Investigation_Form.pdf" },
    @{ id="JTC_HOW_TO_FILE"; url="https://jtc.courts.mi.gov/file_a_grievance/how_to_file_a_grievance.php"; file="JTC_How_To_File.html" }
  )

  $dl = @()
  foreach ($t in $targets) {
    $out = Join-Path $AuthDir $t.file
    $dl += [ordered]@{ id=$t.id; url=$t.url; file=$t.file }

    if (Test-Path -LiteralPath $out) { continue }
    Write-Note "AUTH fetch: $($t.id)"
    if ($DryRun) { continue }
    try {
      Invoke-WebRequest -Uri $t.url -OutFile $out -UseBasicParsing | Out-Null
    } catch {
      Write-Warn "Failed to fetch $($t.id): $($_.Exception.Message)"
    }
  }

  $meta = [ordered]@{
    generated_utc = (Get-Date).ToUniversalTime().ToString("s") + "Z"
    items = $dl
  }
  Write-JsonFile $manifest $meta
  Write-Note "Authority snapshot manifest: $manifest"
}

# ---------------------------
# Extraction: build an extracted-text mirror (offline)
# ---------------------------
function Ensure-ExtractedTextMirror([string]$TargetRoot, [string]$OutDir, [string]$OcrMode) {
  if ([string]::IsNullOrWhiteSpace($TargetRoot)) { Write-Fail "Extract requested but TargetRoot empty." }
  if (-not (Test-Path -LiteralPath $TargetRoot)) { Write-Fail "TargetRoot not found: $TargetRoot" }

  Ensure-Dir $OutDir
  $errLog = Join-Path $OutDir "_EXTRACT_ERRORS.txt"

  $hasPdftotext = Cmd-Exists "pdftotext"
  $hasOcrmypdf  = Cmd-Exists "ocrmypdf"
  $doOcr = ($OcrMode -ne "off") -and $hasOcrmypdf
  if ($OcrMode -eq "on" -and -not $hasOcrmypdf) { Write-Fail "OCR mode=on but ocrmypdf not found on PATH." }

  function Log-Err([string]$msg) {
    $line = ("[{0}] {1}" -f (Get-Date -Format "s"), $msg)
    if ($DryRun) { Write-Note "DRY-RUN logerr $msg"; return }
    Add-Content -LiteralPath $errLog -Value $line -Encoding UTF8
  }

  function Extract-Docx([string]$src, [string]$dst) {
    try {
      $word = New-Object -ComObject Word.Application
      $word.Visible = $false
      $doc = $word.Documents.Open($src, $false, $true)
      $text = $doc.Content.Text
      $doc.Close($false) | Out-Null
      $word.Quit() | Out-Null
      if ($DryRun) { Write-Note "DRY-RUN docx->txt $src"; return }
      $text | Set-Content -LiteralPath $dst -Encoding UTF8
    } catch {
      Log-Err "DOCX extract failed: $src :: $($_.Exception.Message)"
      try { if ($doc) { $doc.Close($false) | Out-Null } } catch {}
      try { if ($word) { $word.Quit() | Out-Null } } catch {}
    }
  }

  Write-Section "Extracted Text Mirror"
  Write-Note "TargetRoot: $TargetRoot"
  Write-Note "OutDir   : $OutDir"
  Write-Note ("pdftotext: " + ($hasPdftotext ? "YES" : "NO"))
  Write-Note ("ocrmypdf : " + ($hasOcrmypdf  ? "YES" : "NO"))
  Write-Note ("OCR mode : " + $OcrMode + ($doOcr ? " (enabled)" : " (disabled)"))

  $files = Get-ChildItem -LiteralPath $TargetRoot -Recurse -File -ErrorAction SilentlyContinue |
           Where-Object { $_.Extension.ToLowerInvariant() -in @(".pdf",".docx",".txt") }

  foreach ($f in $files) {
    $rel = $f.FullName.Substring($TargetRoot.Length).TrimStart("\","/")
    $dst = Join-Path $OutDir ($rel + ".txt")
    Ensure-Dir (Split-Path -Parent $dst)

    try {
      if ($f.Extension -ieq ".txt") {
        if ($DryRun) { Write-Note "DRY-RUN copy txt $rel"; continue }
        Get-Content -LiteralPath $f.FullName -Raw -Encoding UTF8 -ErrorAction SilentlyContinue |
          Set-Content -LiteralPath $dst -Encoding UTF8
      }
      elseif ($f.Extension -ieq ".docx") {
        Extract-Docx $f.FullName $dst
      }
      elseif ($f.Extension -ieq ".pdf") {
        if (-not $hasPdftotext) {
          Log-Err "Skipping PDF (pdftotext missing): $($f.FullName)"
          continue
        }
        $pdfForText = $f.FullName
        if ($doOcr) {
          $ocrOut = Join-Path $OutDir ("_OCR_PDF\" + $rel)
          $ocrOut = [System.IO.Path]::ChangeExtension($ocrOut, ".ocr.pdf")
          Ensure-Dir (Split-Path -Parent $ocrOut)
          if (-not (Test-Path -LiteralPath $ocrOut) -or ((Get-Item $ocrOut).LastWriteTimeUtc -lt $f.LastWriteTimeUtc)) {
            if ($DryRun) { Write-Note "DRY-RUN OCR $rel"; }
            else {
              $cp = & ocrmypdf --skip-text --deskew --rotate-pages --quiet $f.FullName $ocrOut 2>&1
              if ($LASTEXITCODE -ne 0) {
                Log-Err "ocrmypdf failed: $($f.FullName) :: $cp"
                $pdfForText = $f.FullName
              } else {
                $pdfForText = $ocrOut
              }
            }
          } else {
            $pdfForText = $ocrOut
          }
        }
        if ($DryRun) { Write-Note "DRY-RUN pdftotext $rel"; continue }
        $cp2 = & pdftotext -layout $pdfForText $dst 2>&1
        if ($LASTEXITCODE -ne 0) {
          Log-Err "pdftotext failed: $($f.FullName) :: $cp2"
          continue
        }
      }
    } catch {
      Log-Err "Extract failed: $($f.FullName) :: $($_.Exception.Message)"
      continue
    }
  }

  Write-Note "Extracted text mirror complete. Errors (if any): $errLog"
}

# ---------------------------
# High-signal file ranking for Phase 2
# ---------------------------
function Build-HighSignalCandidateList([string]$DocsRoot, [string]$OutJson) {
  if (-not (Test-Path -LiteralPath $DocsRoot)) { Write-Fail "DocumentsRoot not found: $DocsRoot" }

  $keywords = @(
    "Muskegon","McNeill","Jenny","PPO","personal protection","show cause","contempt",
    "parenting time","FOC","Friend of the Court","custody","ex parte","order","judgment",
    "HealthWest","Hackley","superintending","Court of Appeals","Supreme Court","JTC","Judicial Tenure",
    "service","proof of service","hearing","transcript","register of actions","ROA"
  )

  $extOk = @(".pdf",".docx",".txt")
  $files = Get-ChildItem -LiteralPath $DocsRoot -Recurse -File -ErrorAction SilentlyContinue |
           Where-Object { $extOk -contains $_.Extension.ToLowerInvariant() }

  $rows = @()
  foreach ($f in $files) {
    $score = 0
    $name = $f.Name.ToLowerInvariant()
    foreach ($k in $keywords) {
      $kl = $k.ToLowerInvariant()
      if ($name -like ("*" + $kl + "*")) { $score += 6 }
    }

    # recency boost (last 180 days)
    $ageDays = ([datetime]::UtcNow - $f.LastWriteTimeUtc).TotalDays
    if ($ageDays -lt 30) { $score += 6 }
    elseif ($ageDays -lt 90) { $score += 3 }
    elseif ($ageDays -lt 180) { $score += 1 }

    $mb = $f.Length / 1MB
    if ($mb -gt 200) { $score -= 10 }

    $rows += [ordered]@{
      path = $f.FullName
      ext  = $f.Extension.ToLowerInvariant()
      size_mb = [math]::Round($mb,2)
      last_write_utc = $f.LastWriteTimeUtc.ToString("s") + "Z"
      name_score = $score
    }
  }

  # content hits for .txt (fast lane)
  $hasRg = Cmd-Exists "rg"
  if ($hasRg -and -not $DryRun) {
    $top = $rows | Sort-Object -Property name_score -Descending | Select-Object -First 800
    foreach ($r in $top) { $r["content_hits"] = 0 }
    $rgPatterns = @("McNeill","PPO","show cause","contempt","parenting time","HealthWest","ex parte","superintending","Judicial Tenure","JTC","Court of Appeals","Supreme Court","ROA","Register of Actions")
    foreach ($r in $top) {
      try {
        if ($r.ext -eq ".txt") {
          $hits = 0
          foreach ($p in $rgPatterns) {
            $out = & rg -n --no-heading --fixed-strings $p $r.path 2>$null
            if ($LASTEXITCODE -eq 0) { $hits += ($out | Measure-Object).Count }
          }
          $r["content_hits"] = $hits
        }
      } catch {}
    }

    $hitMap = @{}
    foreach ($r in $top) { $hitMap[$r.path] = $r.content_hits }
    foreach ($r in $rows) { if ($hitMap.ContainsKey($r.path)) { $r["content_hits"] = $hitMap[$r.path] } else { $r["content_hits"] = 0 } }
  } else {
    foreach ($r in $rows) { $r["content_hits"] = 0 }
  }

  foreach ($r in $rows) { $r["score_total"] = $r.name_score + [int]$r.content_hits }

  $out = [ordered]@{
    generated_utc = (Get-Date).ToUniversalTime().ToString("s") + "Z"
    docs_root = $DocsRoot
    count = $rows.Count
    candidates = ($rows | Sort-Object -Property score_total -Descending)
  }

  Write-JsonFile $OutJson $out
  Write-Note "High-signal candidate list: $OutJson"
}

# ---------------------------
# Deterministic meta extraction (no LLM) — returns UNKNOWN when not found
# ---------------------------
function Build-CaseMetaJson([string]$ExtractedDir, [string]$OutJson) {
  if (-not (Test-Path -LiteralPath $ExtractedDir)) { Write-Fail "ExtractedDir not found: $ExtractedDir" }

  $caseNumPatterns = @(
    '(?i)\b\d{4}-\d{6,}-[A-Z]{2}\b',
    '(?i)\b\d{4}-\d{6,}-[A-Z]{2}-[A-Z]{2}\b',
    '(?i)\b\d{2}-\d{6,}-[A-Z]{2}-[A-Z]{2}\b'
  )

  $hits = [ordered]@{
    discovered_case_numbers = @()
    discovered_judges = @()
    discovered_counties = @()
    discovered_courts = @()
  }

  $txts = Get-ChildItem -LiteralPath $ExtractedDir -Recurse -File -ErrorAction SilentlyContinue |
          Where-Object { $_.Name.ToLowerInvariant().EndsWith(".txt") } |
          Select-Object -First 3000

  foreach ($t in $txts) {
    $raw = ""
    try { $raw = Get-Content -LiteralPath $t.FullName -Raw -Encoding UTF8 -ErrorAction SilentlyContinue } catch { continue }
    if ([string]::IsNullOrWhiteSpace($raw)) { continue }

    foreach ($p in $caseNumPatterns) {
      $m = [regex]::Matches($raw, $p)
      foreach ($mm in $m) {
        $cn = $mm.Value.Trim()
        if ($cn -and -not ($hits.discovered_case_numbers -contains $cn)) { $hits.discovered_case_numbers += $cn }
      }
    }

    if ($raw -match '(?i)\bHon\.?\s+Jenny\s+L\.?\s+McNeill\b' -or $raw -match '(?i)\bJudge\s+Jenny\s+L\.?\s+McNeill\b') {
      if (-not ($hits.discovered_judges -contains "Hon. Jenny L. McNeill")) { $hits.discovered_judges += "Hon. Jenny L. McNeill" }
    }

    if ($raw -match '(?i)\bMuskegon\b') { if (-not ($hits.discovered_counties -contains "Muskegon")) { $hits.discovered_counties += "Muskegon" } }
    if ($raw -match '(?i)\b14th\s+Circuit\b') { if (-not ($hits.discovered_courts -contains "14th Circuit Court")) { $hits.discovered_courts += "14th Circuit Court" } }
    if ($raw -match '(?i)\b60th\s+District\b') { if (-not ($hits.discovered_courts -contains "60th District Court")) { $hits.discovered_courts += "60th District Court" } }
    if ($raw -match '(?i)\bMichigan\s+Court\s+of\s+Appeals\b') { if (-not ($hits.discovered_courts -contains "Michigan Court of Appeals")) { $hits.discovered_courts += "Michigan Court of Appeals" } }
    if ($raw -match '(?i)\bMichigan\s+Supreme\s+Court\b') { if (-not ($hits.discovered_courts -contains "Michigan Supreme Court")) { $hits.discovered_courts += "Michigan Supreme Court" } }
  }

  # Provide top-level defaults for drafts
  $meta = [ordered]@{
    generated_utc = (Get-Date).ToUniversalTime().ToString("s") + "Z"
    extracted_dir = $ExtractedDir
    hits = $hits
    draft_defaults = [ordered]@{
      petitioner_name = "Andrew J. Pigors"
      petitioner_email = "andrewjpigors@gmail.com"
      petitioner_phone = "231-260-1936"
      petitioner_address = "UNKNOWN (not found in current corpus)"
      respondent_name = "UNKNOWN (not found in current corpus)"
      respondent_address = "UNKNOWN (not found in current corpus)"
      trial_court_case_number = ($hits.discovered_case_numbers | Select-Object -First 1) ?? "UNKNOWN (not found in current corpus)"
      county = ($hits.discovered_counties | Select-Object -First 1) ?? "UNKNOWN (not found in current corpus)"
      judge = ($hits.discovered_judges | Select-Object -First 1) ?? "UNKNOWN (not found in current corpus)"
    }
  }

  Write-JsonFile $OutJson $meta
  Write-Note "Case meta JSON: $OutJson"
}

# ---------------------------
# Gemini runner
# ---------------------------
function Invoke-GeminiPrompt([string]$PromptText, [string]$OutPath) {
  if (-not (Cmd-Exists "gemini")) { Write-Fail "gemini CLI not found on PATH." }
  Ensure-Dir (Split-Path -Parent $OutPath)
  if ($DryRun) { Write-Note "DRY-RUN gemini -> $OutPath"; return }

  try {
    & gemini -p $PromptText | Out-File -FilePath $OutPath -Encoding UTF8
  } catch {
    $err = "gemini failed: $($_.Exception.Message)"
    Write-Warn $err
    $err | Out-File -FilePath $OutPath -Encoding UTF8
  }
}

# ---------------------------
# Agent fleet writer (<= 50)
# ---------------------------
function Ensure-AgentFleet([string]$AgentsDir, [int]$MaxAgents) {
  Ensure-Dir $AgentsDir

  $SYSTEM = @'
# SYSTEM: Judicial-Grade Michigan Document Intelligence (NO-BLOCKERS)
You are an agentic legal-document intelligence system for Michigan practice (trial, COA, MSC, JTC).

Non-negotiables:
- Do NOT invent facts, quotes, dates, case numbers, or authority.
- You ARE allowed and encouraged to infer and explore — label it.
- You MUST always produce a deliverable draft (no "BLOCKERS only" outputs).
- When a required field is not found in the corpus, you must:
  1) Write it as: "UNKNOWN (not found in current corpus)"
  2) Add a "Verification Addendum" listing the exact evidence needed to confirm it.

Epistemic Labels (MANDATORY):
- FACT: directly supported by a local-corpus citation (file path + snippet)
- INFERENCE: derived from FACT(s); explain link; cite upstream FACT(s)
- HYPOTHESIS: plausible; propose verification method (search query + target file types)
- ACTION: concrete step (tool + expected result)

Court-Document drafting rules:
- Use traditional Michigan filing structure and headings.
- Anchor procedural requirements to AUTH_SNAPSHOT sources or official Michigan Courts/JTC pages.
- All factual assertions must either be FACT-cited or explicitly labeled as INFERENCE/HYPOTHESIS.
- Never use bracket placeholders like [____]. Use explicit UNKNOWN text instead.

Deliverables:
PHASE 1:
- COA Original Action (Complaint + Brief)
- MSC Leave to Appeal (Application + Supporting Brief)
- JTC RFI narrative pack
PHASE 2:
- High-delta upgrades + record defect mining from Documents scan.
'@

  Write-TextFile (Join-Path $AgentsDir "00_SYSTEM.md") $SYSTEM

  $core = @(
    @{ name="01_CORPUS_MAP.md"; body=@'
# 01_CORPUS_MAP — Inventory + High-Signal Map
- Inventory major docs (orders, motions, transcripts, emails, police reports).
- Identify top 25 documents by leverage with citations.
Output: CORPUS_MAP.
'@},
    @{ name="02_CAPTION_EXTRACT.md"; body=@'
# 02_CAPTION_EXTRACT — Caption + Parties + Addresses
Goal: Find exact caption blocks and party IDs.
If missing, set UNKNOWN and list what would confirm.
Output: CAPTION_FIELDS + Verification Addendum.
'@},
    @{ name="03_ORDER_INDEX.md"; body=@'
# 03_ORDER_INDEX — Operating Orders + Dates + Directives
Extract each operative order: date, judge, directives, reasoning hooks, service clues.
Output: ORDER_INDEX + defects/anomalies.
'@},
    @{ name="04_ROA_DOCKET_AGENT.md"; body=@'
# 04_ROA_DOCKET_AGENT — Docket/ROA Reconstruction
Reconstruct a docket-like list from corpus evidence.
Output: ROA_TABLE + gaps.
'@},
    @{ name="05_AUTHORITY_PIN_AGENT.md"; body=@'
# 05_AUTHORITY_PIN_AGENT — Authority Pinpoints (AUTH_SNAPSHOT)
Extract requirements for:
- COA original action (superintending control)
- MSC leave (MCR 7.305)
- JTC RFI
Output: AUTHORITY_TRIPLES with pinpoint references to AUTH_SNAPSHOT files.
'@},
    @{ name="06_FACT_PACK_AGENT.md"; body=@'
# 06_FACT_PACK_AGENT — Facts / Inferences / Hypotheses
Output:
- FACT_PACK (numbered; each has citation)
- INFERENCE_PACK (numbered; cites upstream facts)
- HYPOTHESIS_PACK (numbered; includes verification plan)
'@},
    @{ name="07_CONTRADICTION_AGENT.md"; body=@'
# 07_CONTRADICTION_AGENT — Contradictions + Record Defects
Output:
- CONTRADICTION_GRID (claim vs counter-evidence)
- RECORD_DEFECTS (notice/service, ex parte issues, transcript gaps)
'@},
    @{ name="08_COA_COMPLAINT_DRAFTER.md"; body=@'
# 08_COA_COMPLAINT_DRAFTER — Complaint for Superintending Control (COA)
Draft the complaint in traditional format.
Rules:
- Missing caption fields => use UNKNOWN (not found in current corpus) + Verification Addendum.
- Facts must be FACT-cited or labeled inference.
Deliverable: DOC_COA_COMPLAINT_SUPERINTENDING_CONTROL.md
'@},
    @{ name="09_COA_BRIEF_DRAFTER.md"; body=@'
# 09_COA_BRIEF_DRAFTER — Brief in Support (COA Original Action)
Draft the supporting brief per AUTH_SNAPSHOT.
Include:
- Questions presented
- Jurisdiction/standard
- Argument with citations
- Relief
Include Verification Addendum for any UNKNOWN.
'@},
    @{ name="10_MSC_APP_DRAFTER.md"; body=@'
# 10_MSC_APP_DRAFTER — Application for Leave to Appeal (MSC)
Draft per MCR 7.305 (pinpoint via AUTH_SNAPSHOT).
Use UNKNOWN as needed + Verification Addendum.
'@},
    @{ name="11_MSC_BRIEF_DRAFTER.md"; body=@'
# 11_MSC_BRIEF_DRAFTER — Supporting Brief (MSC)
Draft supporting brief with citations and strong issue framing.
Use UNKNOWN as needed + Verification Addendum.
'@},
    @{ name="12_JTC_RFI_DRAFTER.md"; body=@'
# 12_JTC_RFI_DRAFTER — JTC Request for Investigation Narrative Pack
Draft:
- Narrative + numbered counts
- Exhibit list with pointers
Use UNKNOWN as needed + Verification Addendum.
'@},
    @{ name="13_SERVICE_AGENT.md"; body=@'
# 13_SERVICE_AGENT — Service Plan (COA/MSC)
Output:
- Service plan (who/what/how)
- Proof of service template (addresses UNKNOWN if not found)
Use official rule guidance from AUTH_SNAPSHOT.
'@},
    @{ name="14_APPENDIX_BUILDER.md"; body=@'
# 14_APPENDIX_BUILDER — Appendix/Attachment Index
Output:
- Appendix index for COA/MSC
- Exhibit list alignment
- Missing critical attachments (Verification Addendum)
'@},
    @{ name="15_STYLE_QA_AGENT.md"; body=@'
# 15_STYLE_QA_AGENT — Judicial-Grade Tightening + Compliance QA
- Improve diction and structure.
- Flag unsupported statements and relabel as INFERENCE/HYPOTHESIS or remove.
Output revised docs + QA report.
'@},
    @{ name="16_PHASE2_DEEP_SCAN_PLANNER.md"; body=@'
# 16_PHASE2_DEEP_SCAN_PLANNER — High-Delta Scan Strategy
From candidate list, pick top targets and what to mine.
Output PHASE2_PLAN.
'@},
    @{ name="17_PHASE2_RECORD_DEFECTS.md"; body=@'
# 17_PHASE2_RECORD_DEFECTS — Deep Record-Defect Mining
Extract advanced record defects from top candidates.
Output RECORD_DEFECTS_DEEP.
'@},
    @{ name="18_PHASE2_ARGUMENT_UPGRADES.md"; body=@'
# 18_PHASE2_ARGUMENT_UPGRADES — Draft Upgrades
Produce 10 best upgrades, each with citations.
Output UPGRADE_PLAN + patched sections.
'@},
    @{ name="19_PHASE2_REDTTEAM.md"; body=@'
# 19_PHASE2_REDTTEAM — Skeptic Simulation
Attack the drafts; propose preemptions with citations.
Output REDTEAM + FIXES.
'@},
    @{ name="20_PACKAGER_AGENT.md"; body=@'
# 20_PACKAGER_AGENT — Manifest + Readiness Gradient
Produce MANIFEST.md where each file is tagged:
- READY_TO_FILE (rare; requires confirmed caption fields)
- DRAFT_STRONG (usable; some UNKNOWNs remain)
- DRAFT_WEAK (needs more evidence)
No blockers-only outputs.
'@}
  )

  foreach ($a in $core) { Write-TextFile (Join-Path $AgentsDir $a.name) $a.body }

  # Micro agents for extra horsepower up to MaxAgents (high-signal only)
  $micro = @(
    "TRANSCRIPT_HUNTER","ORDER_SIGNATURE_MINER","SERVICE_PROOF_MINER","EX_PARTE_FINDER","TIMELINE_FORENSICS",
    "CONTEMPT_LANE","PPO_LANE","PARENTING_TIME_LANE","BIAS_LANE","CANON_LANE","DUE_PROCESS_LANE",
    "SANCTIONS_LANE","HEALTH_EVAL_LANE","POLICE_REPORT_LANE","INCOME_CONTRADICTIONS","HEARSAY_FILTER",
    "STANDARD_OF_REVIEW","RELIEF_PRECISION","JURISDICTION_CHECK","EXHIBIT_POWER_RANK","QUOTE_EXTRACTOR"
  )

  $i = 21
  foreach ($t in $micro) {
    if ($i -gt $MaxAgents) { break }
    $name = ("{0:D2}_{1}.md" -f $i, $t)
    $body = @"
# $name — Micro Agent: $t
Goal: Find only high-delta material for lane: $t.
Output must be short, ranked, and citation-dense.
If evidence is thin, produce a Verification Addendum (what to locate).
"@
    Write-TextFile (Join-Path $AgentsDir $name) $body
    $i++
  }

  Write-Note "Agent fleet written: $AgentsDir (<= $MaxAgents agents)"
}

# ---------------------------
# Phase runners
# ---------------------------
function Run-Phase1([string]$RootPath, [string]$CaseTarget, [string]$AuthDir, [string]$OutDir, [string]$OcrMode) {
  if ([string]::IsNullOrWhiteSpace($CaseTarget)) { Write-Fail "Phase1 requires -Phase1Target <folder>." }
  if (-not (Test-Path -LiteralPath $CaseTarget)) { Write-Fail "Phase1Target not found: $CaseTarget" }

  Ensure-Dir $OutDir

  $Extracted = Join-Path $OutDir "_EXTRACTED_TEXT"
  Ensure-ExtractedTextMirror -TargetRoot $CaseTarget -OutDir $Extracted -OcrMode $OcrMode

  $CaseMeta = Join-Path $OutDir "CASE_META.json"
  Build-CaseMetaJson -ExtractedDir $Extracted -OutJson $CaseMeta

  $AgentsDir = Join-Path $RootPath "tooling\gemini_judicial\agents"
  $System = Get-Content -LiteralPath (Join-Path $AgentsDir "00_SYSTEM.md") -Raw -Encoding UTF8

  $steps = @(
    @{ id="01_CORPUS_MAP";        agent="01_CORPUS_MAP.md";         out="01_CORPUS_MAP.md" },
    @{ id="02_CAPTION_EXTRACT";   agent="02_CAPTION_EXTRACT.md";    out="02_CAPTION_EXTRACT.md" },
    @{ id="03_ORDER_INDEX";       agent="03_ORDER_INDEX.md";        out="03_ORDER_INDEX.md" },
    @{ id="04_ROA_DOCKET";        agent="04_ROA_DOCKET_AGENT.md";   out="04_ROA_DOCKET.md" },
    @{ id="05_AUTHORITY_TRIPLES"; agent="05_AUTHORITY_PIN_AGENT.md";out="05_AUTHORITY_TRIPLES.md" },
    @{ id="06_FACT_PACK";         agent="06_FACT_PACK_AGENT.md";    out="06_FACT_PACK.md" },
    @{ id="07_CONTRADICTIONS";    agent="07_CONTRADICTION_AGENT.md";out="07_CONTRADICTIONS.md" },
    @{ id="08_COA_COMPLAINT";     agent="08_COA_COMPLAINT_DRAFTER.md"; out="DOC_COA_COMPLAINT_SUPERINTENDING_CONTROL.md" },
    @{ id="09_COA_BRIEF";         agent="09_COA_BRIEF_DRAFTER.md";  out="DOC_COA_BRIEF_SUPERINTENDING_CONTROL.md" },
    @{ id="10_MSC_APP";           agent="10_MSC_APP_DRAFTER.md";    out="DOC_MSC_APPLICATION_LEAVE_TO_APPEAL.md" },
    @{ id="11_MSC_BRIEF";         agent="11_MSC_BRIEF_DRAFTER.md";  out="DOC_MSC_SUPPORTING_BRIEF.md" },
    @{ id="12_JTC_RFI";           agent="12_JTC_RFI_DRAFTER.md";    out="DOC_JTC_REQUEST_FOR_INVESTIGATION_PACK.md" },
    @{ id="13_SERVICE";           agent="13_SERVICE_AGENT.md";      out="13_SERVICE_PLAN.md" },
    @{ id="14_APPENDIX";          agent="14_APPENDIX_BUILDER.md";   out="14_APPENDIX_INDEX.md" },
    @{ id="15_STYLE_QA";          agent="15_STYLE_QA_AGENT.md";     out="15_QA_AND_REVISIONS.md" },
    @{ id="20_MANIFEST";          agent="20_PACKAGER_AGENT.md";     out="MANIFEST.md" }
  )

  $contextFiles = @("CASE_META.json")

  foreach ($s in $steps) {
    $agentPath = Join-Path $AgentsDir $s.agent
    if (-not (Test-Path -LiteralPath $agentPath)) { Write-Fail "Missing agent file: $agentPath" }
    $agentPrompt = Get-Content -LiteralPath $agentPath -Raw -Encoding UTF8

    $ctx = ""
    foreach ($cf in $contextFiles) {
      $p = Join-Path $OutDir $cf
      if (Test-Path -LiteralPath $p) {
        $txt = Get-Content -LiteralPath $p -Raw -Encoding UTF8
        $ctx += "`n`n## CONTEXT FILE: $cf`n" + $txt
      }
    }

    $prompt = @"
$System

# MCP TOOL SCOPES
- Prefer fs_case for case corpus.
- Prefer ripgrep for locating key strings fast.
- Use AUTH_SNAPSHOT for procedural requirements and pinpoints.
- Use fetch ONLY for official Michigan Courts / JTC pages if AUTH_SNAPSHOT is insufficient.

# PATHS
CaseTarget: $CaseTarget
PhaseOutputDir: $OutDir
ExtractedTextDir: $Extracted
AuthoritySnapshotDir: $AuthDir

# AGENT TASK
$agentPrompt

# AVAILABLE CONTEXT (prior steps)
$ctx
"@

    $outPath = Join-Path $OutDir $s.out
    Write-Note "PHASE1 RUN $($s.id) -> $($s.out)"
    Invoke-GeminiPrompt -PromptText $prompt -OutPath $outPath

    if (-not ($contextFiles -contains $s.out)) { $contextFiles += $s.out }
  }
}

function Run-Phase2([string]$RootPath, [string]$DocsRoot, [string]$AuthDir, [string]$OutDir, [string]$OcrMode) {
  if (-not (Test-Path -LiteralPath $DocsRoot)) { Write-Fail "Phase2DocumentsRoot not found: $DocsRoot" }
  Ensure-Dir $OutDir

  $Candidates = Join-Path $OutDir "PHASE2_CANDIDATES.json"
  Build-HighSignalCandidateList -DocsRoot $DocsRoot -OutJson $Candidates

  $staging = Join-Path $OutDir "_STAGING_TOP_FILES"
  Ensure-Dir $staging

  if (-not $DryRun) {
    $candObj = ConvertTo-Hashtable (Read-JsonFile $Candidates)
    $top = @($candObj.candidates | Select-Object -First 250)
    foreach ($c in $top) {
      try {
        $src = $c.path
        $dst = Join-Path $staging ([System.IO.Path]::GetFileName($src))
        if (-not (Test-Path -LiteralPath $dst)) {
          Copy-Item -LiteralPath $src -Destination $dst -Force -ErrorAction SilentlyContinue
        }
      } catch {}
    }
  }

  $Extracted = Join-Path $OutDir "_EXTRACTED_TEXT"
  Ensure-ExtractedTextMirror -TargetRoot $staging -OutDir $Extracted -OcrMode $OcrMode

  $Meta = Join-Path $OutDir "PHASE2_META.json"
  Build-CaseMetaJson -ExtractedDir $Extracted -OutJson $Meta

  $AgentsDir = Join-Path $RootPath "tooling\gemini_judicial\agents"
  $System = Get-Content -LiteralPath (Join-Path $AgentsDir "00_SYSTEM.md") -Raw -Encoding UTF8

  $steps = @(
    @{ id="16_PHASE2_PLAN";       agent="16_PHASE2_DEEP_SCAN_PLANNER.md"; out="16_PHASE2_PLAN.md" },
    @{ id="17_RECORD_DEFECTS";    agent="17_PHASE2_RECORD_DEFECTS.md";    out="17_RECORD_DEFECTS_DEEP.md" },
    @{ id="18_ARGUMENT_UPGRADES"; agent="18_PHASE2_ARGUMENT_UPGRADES.md"; out="18_ARGUMENT_UPGRADES.md" },
    @{ id="19_REDTEAM";           agent="19_PHASE2_REDTTEAM.md";          out="19_REDTEAM.md" },
    @{ id="20_MANIFEST";          agent="20_PACKAGER_AGENT.md";           out="MANIFEST_PHASE2.md" }
  )

  $contextFiles = @("PHASE2_CANDIDATES.json","PHASE2_META.json")

  foreach ($s in $steps) {
    $agentPath = Join-Path $AgentsDir $s.agent
    if (-not (Test-Path -LiteralPath $agentPath)) { Write-Fail "Missing agent file: $agentPath" }
    $agentPrompt = Get-Content -LiteralPath $agentPath -Raw -Encoding UTF8

    $ctx = ""
    foreach ($cf in $contextFiles) {
      $p = Join-Path $OutDir $cf
      if (Test-Path -LiteralPath $p) {
        $txt = Get-Content -LiteralPath $p -Raw -Encoding UTF8
        $ctx += "`n`n## CONTEXT FILE: $cf`n" + $txt
      }
    }

    $prompt = @"
$System

# MCP TOOL SCOPES
- Prefer fs_docs for Documents corpus.
- Use ripgrep to locate targets, then read exact files for citations.
- Use AUTH_SNAPSHOT for procedural pinpoints.

# PATHS
DocumentsRoot: $DocsRoot
Phase2OutputDir: $OutDir
StagingTopFilesDir: $staging
ExtractedTextDir: $Extracted
AuthoritySnapshotDir: $AuthDir

# AGENT TASK
$agentPrompt

# AVAILABLE CONTEXT
$ctx
"@

    $outPath = Join-Path $OutDir $s.out
    Write-Note "PHASE2 RUN $($s.id) -> $($s.out)"
    Invoke-GeminiPrompt -PromptText $prompt -OutPath $outPath

    if (-not ($contextFiles -contains $s.out)) { $contextFiles += $s.out }
  }
}

# ---------------------------
# Main
# ---------------------------
Write-Section "Gemini + MCP Judicial Fleet (MI) — NO-BLOCKERS"

try { $Root = (Resolve-Path -LiteralPath $Root).Path } catch {}
Ensure-Dir $Root
Write-Note "Root: $Root"
Write-Note "Phase: $Phase"
Write-Note "DryRun: $DryRun"
Write-Note "MaxAgents: $MaxAgents"

Write-Section "Dependencies (optional auto-install)"
if (-not (Cmd-Exists "node")) { Try-WingetInstall "OpenJS.NodeJS.LTS" "Node.js LTS" }
if (-not (Cmd-Exists "git"))  { Try-WingetInstall "Git.Git" "Git" }
if (-not (Cmd-Exists "rg"))   { Try-WingetInstall "BurntSushi.ripgrep.MSVC" "ripgrep" }

if (-not (Cmd-Exists "npx")) { Write-Warn "npx not found. Install Node.js LTS to run MCP servers." } else { Write-Note "npx OK" }
if (-not (Cmd-Exists "rg"))  { Write-Warn "rg not found. Install ripgrep for best Phase2 scoring." } else { Write-Note "rg OK" }
if (-not (Cmd-Exists "gemini")) { Write-Warn "gemini CLI not found. Install/login first; configs will still be written." } else { Write-Note "gemini OK" }

Write-Section "Write MCP Configs + Agent Fleet + Authority Snapshot"
$AuthDir = Join-Path $Root "tooling\gemini_judicial\AUTH_SNAPSHOT"
$AgentsDir = Join-Path $Root "tooling\gemini_judicial\agents"
Ensure-AgentFleet -AgentsDir $AgentsDir -MaxAgents $MaxAgents
Ensure-AuthoritySnapshot -AuthDir $AuthDir
Ensure-GeminiMcpConfig -RootPath $Root -DocsRoot $Phase2DocumentsRoot -CaseRoot $Phase1Target
Ensure-VSCodeMcpConfig -RootPath $Root

# Output base
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$OutBase = Join-Path $Root ("tooling\gemini_judicial\outputs\" + $stamp)
Ensure-Dir $OutBase

if ($Phase -eq "config") {
  Write-Section "CONFIG COMPLETE"
  Write-Note "Next: run -Phase phase1 -Phase1Target <case folder> to generate MI court drafts."
  Write-Note "Or run -Phase phase2 to deep scan Documents."
  exit 0
}

if ($Phase -eq "phase1" -or $Phase -eq "both") {
  $p1 = Join-Path $OutBase "PHASE1"
  Ensure-Dir $p1
  Write-Section "RUN PHASE 1 — Court Documents (COA/MSC/JTC)"
  Run-Phase1 -RootPath $Root -CaseTarget $Phase1Target -AuthDir $AuthDir -OutDir $p1 -OcrMode $OcrMode
}

if ($Phase -eq "phase2" -or $Phase -eq "both") {
  $p2 = Join-Path $OutBase "PHASE2"
  Ensure-Dir $p2
  Write-Section "RUN PHASE 2 — High-Delta Deep Scan (Documents)"
  Run-Phase2 -RootPath $Root -DocsRoot $Phase2DocumentsRoot -AuthDir $AuthDir -OutDir $p2 -OcrMode $OcrMode
}

Write-Section "DONE"
Write-Note "Outputs: $OutBase"
Write-Note "Phase1 drafts: $OutBase\PHASE1\DOC_*"
Write-Note "Phase2 upgrades: $OutBase\PHASE2\"
