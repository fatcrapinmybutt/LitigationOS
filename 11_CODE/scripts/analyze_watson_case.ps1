# Watson v. Pigors - Comprehensive AI Analysis Workflow
# Uses all AI agents for complete case analysis

$ErrorActionPreference = "Continue"

Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host " Watson v. Pigors - AI Agent Comprehensive Analysis" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Import AI Agent Bridge
Import-Module ".\AgentBridge.psm1" -Force

# Configure paths
$evidenceBase = "C:\Users\andre\Desktop\ALL_PC_EVIDENCE_EXTRACTED"
$outputBase = "C:\Users\andre\Desktop\WATSON_AI_ANALYSIS_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
New-Item -ItemType Directory -Path $outputBase -Force | Out-Null

Write-Host "[CONFIG] Evidence Base: $evidenceBase" -ForegroundColor Yellow
Write-Host "[CONFIG] Output Directory: $outputBase" -ForegroundColor Yellow
Write-Host ""

# Stage 1: Evidence Extraction from All Documents
Write-Host "[STAGE 1/5] Evidence Extraction Analysis" -ForegroundColor Cyan
Write-Host "─────────────────────────────────────────" -ForegroundColor Gray

$evidenceOutput = Join-Path $outputBase "01_EVIDENCE"
Start-BatchAnalysis -FolderPath $evidenceBase `
                    -AgentType evidence `
                    -OutputPath $evidenceOutput `
                    -FilePattern "*.txt"

Write-Host "[✓] Evidence extraction complete" -ForegroundColor Green
Write-Host ""

# Stage 2: Judicial Misconduct Analysis
Write-Host "[STAGE 2/5] Judicial Misconduct Analysis" -ForegroundColor Cyan
Write-Host "─────────────────────────────────────────" -ForegroundColor Gray

$judgeOrders = Get-ChildItem "$evidenceBase\*judge*" -Filter "*.txt" -File -Recurse -ErrorAction SilentlyContinue

if ($judgeOrders) {
    $judicialOutput = Join-Path $outputBase "02_JUDICIAL_MISCONDUCT"
    New-Item -ItemType Directory -Path $judicialOutput -Force | Out-Null
    
    foreach ($order in $judgeOrders | Select-Object -First 20) {
        Write-Host "  Analyzing: $($order.Name)" -ForegroundColor Gray
        
        $result = Invoke-JudicialAnalyst -OrderPath $order.FullName `
                                        -CaseType "Custody/PPO" `
                                        -JudgeName "Watson" `
                                        -Date "2024"
        
        if ($result) {
            $outputFile = Join-Path $judicialOutput "$($order.BaseName)_analysis.json"
            $result | ConvertTo-Json -Depth 10 | Out-File $outputFile -Encoding UTF8
        }
    }
    
    Write-Host "[✓] Judicial analysis complete: $($judgeOrders.Count) orders" -ForegroundColor Green
} else {
    Write-Host "[SKIP] No judge orders found" -ForegroundColor Yellow
}
Write-Host ""

# Stage 3: Procedural Compliance Check
Write-Host "[STAGE 3/5] Procedural Compliance Verification" -ForegroundColor Cyan
Write-Host "──────────────────────────────────────────────" -ForegroundColor Gray

$filings = Get-ChildItem "$evidenceBase\*motion*","$evidenceBase\*brief*" -Filter "*.txt" -File -ErrorAction SilentlyContinue

if ($filings) {
    $proceduralOutput = Join-Path $outputBase "03_PROCEDURAL"
    New-Item -ItemType Directory -Path $proceduralOutput -Force | Out-Null
    
    foreach ($filing in $filings | Select-Object -First 10) {
        Write-Host "  Checking: $($filing.Name)" -ForegroundColor Gray
        
        $result = Invoke-ProceduralCheck -DocumentPath $filing.FullName `
                                        -DocumentType "Motion/Brief" `
                                        -Court "Circuit Court"
        
        if ($result) {
            $outputFile = Join-Path $proceduralOutput "$($filing.BaseName)_compliance.txt"
            $result | Out-File $outputFile -Encoding UTF8
        }
    }
    
    Write-Host "[✓] Procedural check complete" -ForegroundColor Green
} else {
    Write-Host "[SKIP] No filings found" -ForegroundColor Yellow
}
Write-Host ""

# Stage 4: Best Interests Analysis (Custody)
Write-Host "[STAGE 4/5] Best Interests Analysis (MCL 722.23)" -ForegroundColor Cyan
Write-Host "─────────────────────────────────────────────────" -ForegroundColor Gray

$custodyEvidence = Get-ChildItem "$evidenceBase\*custody*" -Filter "*.txt" -File -Recurse -ErrorAction SilentlyContinue

if ($custodyEvidence) {
    $harmOutput = Join-Path $outputBase "04_BEST_INTERESTS"
    New-Item -ItemType Directory -Path $harmOutput -Force | Out-Null
    
    # Combine custody evidence
    $combinedEvidence = ""
    foreach ($doc in $custodyEvidence | Select-Object -First 10) {
        $content = Get-Content $doc.FullName -Raw -ErrorAction SilentlyContinue
        $combinedEvidence += "`n`n=== $($doc.Name) ===`n$content"
    }
    
    $tempEvidenceFile = Join-Path $harmOutput "combined_custody_evidence.txt"
    $combinedEvidence | Out-File $tempEvidenceFile -Encoding UTF8
    
    Write-Host "  Analyzing combined custody evidence..." -ForegroundColor Gray
    
    $result = Invoke-BestInterestsAnalysis -EvidencePath $tempEvidenceFile `
                                          -ChildrenInfo "Children from Watson case" `
                                          -PartiesInfo "Watson v. Pigors"
    
    if ($result) {
        $outputFile = Join-Path $harmOutput "best_interests_analysis.json"
        $result | ConvertTo-Json -Depth 10 | Out-File $outputFile -Encoding UTF8
    }
    
    Write-Host "[✓] Best interests analysis complete" -ForegroundColor Green
} else {
    Write-Host "[SKIP] No custody evidence found" -ForegroundColor Yellow
}
Write-Host ""

# Stage 5: Quality Validation
Write-Host "[STAGE 5/5] Quality Validation" -ForegroundColor Cyan
Write-Host "───────────────────────────────" -ForegroundColor Gray

$briefs = Get-ChildItem "$evidenceBase\*brief*","$evidenceBase\*appellate*" -Filter "*.txt" -File -ErrorAction SilentlyContinue

if ($briefs) {
    $qualityOutput = Join-Path $outputBase "05_QUALITY"
    New-Item -ItemType Directory -Path $qualityOutput -Force | Out-Null
    
    foreach ($brief in $briefs | Select-Object -First 5) {
        Write-Host "  Validating: $($brief.Name)" -ForegroundColor Gray
        
        $result = Invoke-QualityValidator -DocumentPath $brief.FullName `
                                         -DocumentType "Appellate Brief"
        
        if ($result) {
            $outputFile = Join-Path $qualityOutput "$($brief.BaseName)_quality.txt"
            $result | Out-File $outputFile -Encoding UTF8
        }
    }
    
    Write-Host "[✓] Quality validation complete" -ForegroundColor Green
} else {
    Write-Host "[SKIP] No briefs found" -ForegroundColor Yellow
}
Write-Host ""

# Generate Summary Report
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host " COMPREHENSIVE ANALYSIS COMPLETE" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "All analysis results saved to:" -ForegroundColor Green
Write-Host "  $outputBase" -ForegroundColor White
Write-Host ""
Write-Host "Folders created:" -ForegroundColor Yellow
Write-Host "  01_EVIDENCE           - Evidence extraction results" -ForegroundColor Gray
Write-Host "  02_JUDICIAL_MISCONDUCT - Judicial bias/violation analysis" -ForegroundColor Gray
Write-Host "  03_PROCEDURAL         - MCR compliance checks" -ForegroundColor Gray
Write-Host "  04_BEST_INTERESTS     - MCL 722.23 factor analysis" -ForegroundColor Gray
Write-Host "  05_QUALITY            - Document quality assessments" -ForegroundColor Gray
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "  1. Review analysis results in each folder" -ForegroundColor Gray
Write-Host "  2. Generate comprehensive report from findings" -ForegroundColor Gray
Write-Host "  3. Use findings to enhance legal filings" -ForegroundColor Gray
Write-Host "  4. Export metrics for performance analysis" -ForegroundColor Gray
Write-Host ""
