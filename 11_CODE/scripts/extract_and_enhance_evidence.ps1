# Legal Filing Enhancement with ALLSCANNED Evidence
# This script extracts evidence from ALLSCANNED folders and enhances legal filings

$ErrorActionPreference = "Continue"

# Define paths
$allscannedPath = "C:\Users\andre\Desktop\ALLSCANNED_EXTRACTED"
$outputPath = "C:\Users\andre\Desktop\LEGAL_ANALYSIS_OUTPUT\01_ENHANCED_FILINGS"
$tempPath = "$allscannedPath\TEMP_EXTRACTED"

# Create temp directory
New-Item -ItemType Directory -Path $tempPath -Force | Out-Null

Write-Host "=== Legal Filing Enhancement with Evidence ===" -ForegroundColor Cyan
Write-Host ""

# Step 1: Extract key zip files
Write-Host "[1/4] Extracting evidence folders..." -ForegroundColor Yellow

$zipFiles = @{
    "SCANNED2sided judge orders scanned_0001.zip" = "04_JUDGE_ORDERS_2SIDED"
    "SCANNEDexpartescannedandmine_0008.zip" = "10_EXPARTE_SCANNED_AND_MINE"
    "SCANNED EXPARTE EMILY AND JUDGE DOCS.zip" = "02_EXPARTE_EMILY_JUDGE"
    "SCANNED 5th exparte suspension 18 pdfs.zip" = "01_5TH_EXPARTE_SUSPENSION"
    "SCANNEDtranscriptsppooct302024_0013.zip" = "15_TRANSCRIPTS_PPO_OCT302024"
}

foreach ($zip in $zipFiles.Keys) {
    $destName = $zipFiles[$zip]
    $destPath = Join-Path $tempPath $destName
    
    if (-not (Test-Path $destPath)) {
        Write-Host "  Extracting $destName..." -ForegroundColor Gray
        try {
            Expand-Archive -Path (Join-Path $allscannedPath $zip) -DestinationPath $destPath -Force
            Write-Host "    ✓ Extracted: $(((Get-ChildItem $destPath -File -Recurse).Count)) files" -ForegroundColor Green
        } catch {
            Write-Host "    ✗ Error: $_" -ForegroundColor Red
        }
    } else {
        Write-Host "  ✓ Already extracted: $destName" -ForegroundColor Green
    }
}

# Step 2: Scan for PDF and image files
Write-Host "`n[2/4] Scanning evidence files..." -ForegroundColor Yellow

$judgeOrders = Get-ChildItem -Path "$tempPath\04_JUDGE_ORDERS_2SIDED" -File -Recurse -ErrorAction SilentlyContinue | Select-Object -First 20
$exparteMotions = Get-ChildItem -Path "$tempPath\10_EXPARTE_SCANNED_AND_MINE","$tempPath\02_EXPARTE_EMILY_JUDGE","$tempPath\01_5TH_EXPARTE_SUSPENSION" -File -Recurse -ErrorAction SilentlyContinue | Select-Object -First 20
$transcripts = Get-ChildItem -Path "$tempPath\15_TRANSCRIPTS_PPO_OCT302024" -File -Recurse -ErrorAction SilentlyContinue

Write-Host "  Found:" -ForegroundColor Gray
Write-Host "    Judge Orders: $($judgeOrders.Count) files" -ForegroundColor White
Write-Host "    Ex Parte Motions: $($exparteMotions.Count) files" -ForegroundColor White
Write-Host "    Transcripts: $($transcripts.Count) files" -ForegroundColor White

# Step 3: Read existing filings
Write-Host "`n[3/4] Loading existing filings..." -ForegroundColor Yellow

$disqFile = Get-Item "$outputPath\2026-02-10_DISQ_v02_ENHANCED.txt" -ErrorAction SilentlyContinue
$jtcFile = Get-Item "$outputPath\2026-02-10_JTC_CITATIONS_ADDED.txt" -ErrorAction SilentlyContinue
$coaFile = Get-Item "$outputPath\2026-02-10_COA_APPENDIX_v02_ENHANCED.txt" -ErrorAction SilentlyContinue

if ($disqFile) { Write-Host "  ✓ DISQ filing loaded" -ForegroundColor Green } else { Write-Host "  ✗ DISQ filing not found" -ForegroundColor Red }
if ($jtcFile) { Write-Host "  ✓ JTC filing loaded" -ForegroundColor Green } else { Write-Host "  ✗ JTC filing not found" -ForegroundColor Red }
if ($coaFile) { Write-Host "  ✓ COA filing loaded" -ForegroundColor Green } else { Write-Host "  ✗ COA filing not found" -ForegroundColor Red }

# Step 4: Create exhibit lists
Write-Host "`n[4/4] Creating exhibit inventory..." -ForegroundColor Yellow

$exhibitList = @"
# EXHIBIT LIST FOR ENHANCED LEGAL FILINGS
Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

## DISQUALIFICATION MOTION (DISQ) - EXHIBIT INVENTORY

### Judge Order Evidence (04_JUDGE_ORDERS_2SIDED)
Total Files Scanned: $($judgeOrders.Count)

"@

$exhibitNum = 1
foreach ($file in $judgeOrders) {
    $exhibitList += "`n**Exhibit $exhibitNum**: $($file.Name)"
    $exhibitList += "`n  - File: $($file.FullName)"
    $exhibitList += "`n  - Size: $([math]::Round($file.Length/1KB,2)) KB"
    $exhibitList += "`n  - Modified: $($file.LastWriteTime)"
    $exhibitList += "`n"
    $exhibitNum++
}

$exhibitList += @"

## JUDICIAL TENURE COMMISSION COMPLAINT (JTC) - EXHIBIT INVENTORY

### Ex Parte Motion Evidence (Multiple Folders)
Total Files Scanned: $($exparteMotions.Count)

"@

$exhibitNum = 1
foreach ($file in $exparteMotions) {
    $exhibitList += "`n**Exhibit $exhibitNum**: $($file.Name)"
    $exhibitList += "`n  - File: $($file.FullName)"
    $exhibitList += "`n  - Size: $([math]::Round($file.Length/1KB,2)) KB"
    $exhibitList += "`n  - Modified: $($file.LastWriteTime)"
    $exhibitList += "`n"
    $exhibitNum++
}

$exhibitList += @"

## COURT OF APPEALS BRIEF (COA) - EXHIBIT INVENTORY

### PPO Transcript Evidence (15_TRANSCRIPTS_PPO_OCT302024)
Total Files Scanned: $($transcripts.Count)

"@

$exhibitNum = 1
foreach ($file in $transcripts) {
    $exhibitList += "`n**Exhibit $exhibitNum**: $($file.Name)"
    $exhibitList += "`n  - File: $($file.FullName)"
    $exhibitList += "`n  - Size: $([math]::Round($file.Length/1KB,2)) KB"
    $exhibitList += "`n  - Modified: $($file.LastWriteTime)"
    $exhibitList += "`n"
    $exhibitNum++
}

# Save exhibit list
$exhibitListPath = "$outputPath\2026-02-10_EXHIBIT_LISTS.md"
$exhibitList | Out-File -FilePath $exhibitListPath -Encoding UTF8
Write-Host "  ✓ Exhibit list created: $exhibitListPath" -ForegroundColor Green

Write-Host "`n=== Extraction Complete ===" -ForegroundColor Cyan
Write-Host "Next: Use Ollama mistral to analyze evidence and suggest insertions" -ForegroundColor White
Write-Host ""
Write-Host "Temp files location: $tempPath" -ForegroundColor Gray
Write-Host "Exhibit list: $exhibitListPath" -ForegroundColor Gray
