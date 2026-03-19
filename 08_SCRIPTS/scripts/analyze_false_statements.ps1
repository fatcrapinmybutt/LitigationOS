# FALSE STATEMENTS ANALYZER - Uses Ollama Mistral
# Analyzes evidence for lies, false statements, and unsupported claims

param(
    [int]$BatchSize = 5,
    [string]$OutputPath = "C:\Users\andre\Desktop\FULL_PC_JUDICIAL_ANALYSIS_REPORTS\03_FALSE_STATEMENTS_COMPREHENSIVE.md"
)

$ErrorActionPreference = "Continue"

# Load document queue
$queueFile = "C:\Users\andre\Desktop\doc_queue.json"
$documents = Get-Content $queueFile | ConvertFrom-Json

Write-Host "=== FALSE STATEMENTS ANALYSIS ===" -ForegroundColor Cyan
Write-Host "Total Documents: $($documents.Count)" -ForegroundColor Yellow
Write-Host "Using Model: Ollama Mistral" -ForegroundColor Yellow

# Analysis prompt template
$analysisPrompt = @"
You are a legal evidence analyzer. Analyze the following document for:

1. FALSE STATEMENTS: Factual assertions that are demonstrably untrue
2. LIES: Intentional misrepresentations or deceptions
3. UNSUPPORTED CLAIMS: Assertions made without evidence
4. NEGATIVE CONNOTATIONS: Prejudicial language, bias, character attacks
5. INCONSISTENCIES: Internal contradictions
6. MATERIAL OMISSIONS: Important facts that appear to be withheld

For each finding, provide:
- EXACT QUOTE from the document
- TYPE (false_statement/lie/unsupported_claim/bias/inconsistency/omission)
- EXPLANATION of why this is problematic
- LEGAL SIGNIFICANCE (if applicable)
- CONFIDENCE (high/medium/low)

Document content:
{CONTENT}

Respond ONLY in this JSON format:
{
  "findings": [
    {
      "quote": "exact text from document",
      "type": "false_statement",
      "explanation": "why this is false/problematic",
      "legal_significance": "potential perjury, fraud, etc.",
      "confidence": "high"
    }
  ]
}
"@

# Results storage
$allFindings = @()
$processed = 0
$failed = 0

# Process documents in batches
for ($i = 0; $i -lt $documents.Count; $i++) {
    $doc = $documents[$i]
    $processed++
    
    Write-Host "`n[$processed/$($documents.Count)] Processing: $($doc.Category)" -ForegroundColor Cyan
    Write-Host "  File: $([System.IO.Path]::GetFileName($doc.FilePath))" -ForegroundColor Gray
    
    try {
        # Extract text from PDF
        $content = ""
        $ext = [System.IO.Path]::GetExtension($doc.FilePath).ToLower()
        
        if ($ext -eq ".pdf") {
            # Try to extract text using Python if available
            $pythonCmd = @"
import sys
try:
    import PyPDF2
    with open(r'$($doc.FilePath)', 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        text = ''
        for page in reader.pages[:5]:  # First 5 pages
            text += page.extract_text()
        print(text[:4000])  # First 4000 chars
except Exception as e:
    print('ERROR: ' + str(e))
"@
            $content = python -c $pythonCmd 2>$null
            
            if ($content -match "ERROR" -or [string]::IsNullOrWhiteSpace($content)) {
                # Fallback: Read as text
                $content = Get-Content $doc.FilePath -Raw -ErrorAction SilentlyContinue | Select-Object -First 4000
            }
        } elseif ($ext -in @(".txt", ".eml", ".msg")) {
            $content = Get-Content $doc.FilePath -Raw -ErrorAction SilentlyContinue | Select-Object -First 4000
        }
        
        if ([string]::IsNullOrWhiteSpace($content)) {
            Write-Host "  [SKIP] No extractable text" -ForegroundColor Yellow
            continue
        }
        
        # Truncate if too long
        $content = $content.Substring(0, [Math]::Min($content.Length, 4000))
        
        # Build prompt
        $prompt = $analysisPrompt -replace '\{CONTENT\}', $content
        
        # Call Ollama Mistral
        Write-Host "  [ANALYZE] Sending to Ollama..." -ForegroundColor Gray
        
        $requestBody = @{
            model = "mistral:latest"
            prompt = $prompt
            stream = $false
            options = @{
                temperature = 0.1
                num_predict = 2000
            }
        } | ConvertTo-Json -Depth 10
        
        $response = Invoke-RestMethod -Uri "http://localhost:11434/api/generate" -Method Post -Body $requestBody -ContentType "application/json" -TimeoutSec 120
        
        $aiResponse = $response.response
        
        # Parse JSON response
        try {
            # Extract JSON from response
            if ($aiResponse -match '\{[\s\S]*"findings"[\s\S]*\}') {
                $jsonMatch = $matches[0]
                $result = $jsonMatch | ConvertFrom-Json
                
                if ($result.findings -and $result.findings.Count -gt 0) {
                    Write-Host "  [FOUND] $($result.findings.Count) findings!" -ForegroundColor Green
                    
                    foreach ($finding in $result.findings) {
                        $allFindings += [PSCustomObject]@{
                            Category = $doc.Category
                            FilePath = $doc.FilePath
                            FileName = [System.IO.Path]::GetFileName($doc.FilePath)
                            Quote = $finding.quote
                            Type = $finding.type
                            Explanation = $finding.explanation
                            LegalSignificance = $finding.legal_significance
                            Confidence = $finding.confidence
                            Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
                        }
                    }
                } else {
                    Write-Host "  [CLEAN] No findings" -ForegroundColor Green
                }
            } else {
                Write-Host "  [WARN] Could not parse AI response" -ForegroundColor Yellow
            }
        } catch {
            Write-Host "  [ERROR] JSON parse failed: $($_.Exception.Message)" -ForegroundColor Red
        }
        
    } catch {
        $failed++
        Write-Host "  [ERROR] $($_.Exception.Message)" -ForegroundColor Red
    }
    
    # Progress update every 10 documents
    if ($processed % 10 -eq 0) {
        Write-Host "`nPROGRESS: $processed/$($documents.Count) processed, $($allFindings.Count) findings, $failed errors" -ForegroundColor Magenta
        
        # Save intermediate results
        if ($allFindings.Count -gt 0) {
            $allFindings | Export-Csv -Path "C:\Users\andre\Desktop\findings_intermediate.csv" -NoTypeInformation -Force
        }
    }
    
    # Small delay to avoid overwhelming Ollama
    Start-Sleep -Milliseconds 500
}

Write-Host "`n=== ANALYSIS COMPLETE ===" -ForegroundColor Cyan
Write-Host "Total Processed: $processed" -ForegroundColor Yellow
Write-Host "Total Findings: $($allFindings.Count)" -ForegroundColor Yellow
Write-Host "Failed: $failed" -ForegroundColor Yellow

# Save final results
if ($allFindings.Count -gt 0) {
    $allFindings | Export-Csv -Path "C:\Users\andre\Desktop\findings_complete.csv" -NoTypeInformation -Force
    Write-Host "`nResults saved to: C:\Users\andre\Desktop\findings_complete.csv" -ForegroundColor Green
}

# Generate comprehensive report
Write-Host "`nGenerating comprehensive report..." -ForegroundColor Cyan

$report = @"
# COMPREHENSIVE FALSE STATEMENTS ANALYSIS
## Evidence Base Analysis - Judicial Case

**Analysis Date:** $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
**Documents Analyzed:** $processed
**Total Findings:** $($allFindings.Count)
**Model Used:** Ollama Mistral
**Evidence Location:** C:\Users\andre\Desktop\ALL_PC_EVIDENCE_EXTRACTED\

---

## EXECUTIVE SUMMARY

This analysis examined $processed documents across 8 categories of evidence, identifying false statements, lies, unsupported claims, and prejudicial language that may constitute:
- **Perjury** (false statements under oath)
- **Fraud** (intentional misrepresentations)
- **Contempt** (violations of court orders)
- **Bad Faith** (malicious or vexatious conduct)

### Key Statistics:
- **False Statements:** $($allFindings | Where-Object {$_.Type -eq 'false_statement'} | Measure-Object | Select-Object -ExpandProperty Count)
- **Lies/Misrepresentations:** $($allFindings | Where-Object {$_.Type -eq 'lie'} | Measure-Object | Select-Object -ExpandProperty Count)
- **Unsupported Claims:** $($allFindings | Where-Object {$_.Type -eq 'unsupported_claim'} | Measure-Object | Select-Object -ExpandProperty Count)
- **Bias/Prejudicial Language:** $($allFindings | Where-Object {$_.Type -eq 'bias'} | Measure-Object | Select-Object -ExpandProperty Count)
- **Inconsistencies:** $($allFindings | Where-Object {$_.Type -eq 'inconsistency'} | Measure-Object | Select-Object -ExpandProperty Count)
- **Material Omissions:** $($allFindings | Where-Object {$_.Type -eq 'omission'} | Measure-Object | Select-Object -ExpandProperty Count)

---

## FINDINGS BY CATEGORY

"@

# Group findings by category
$byCategory = $allFindings | Group-Object -Property Category

foreach ($catGroup in $byCategory | Sort-Object Name) {
    $report += @"

### $($catGroup.Name) ($($catGroup.Count) findings)

"@
    
    $findings = $catGroup.Group | Sort-Object -Property Confidence -Descending
    
    foreach ($finding in $findings) {
        $report += @"

#### Finding: $($finding.Type.ToUpper())
- **File:** $($finding.FileName)
- **Confidence:** $($finding.Confidence)
- **Quote:** "$($finding.Quote)"
- **Explanation:** $($finding.Explanation)
- **Legal Significance:** $($finding.LegalSignificance)

---

"@
    }
}

# Findings by type
$report += @"

## FINDINGS BY TYPE

"@

$byType = $allFindings | Group-Object -Property Type

foreach ($typeGroup in $byType | Sort-Object Count -Descending) {
    $report += @"

### $($typeGroup.Name.ToUpper()) ($($typeGroup.Count) instances)

"@
    
    $findings = $typeGroup.Group | Select-Object -First 10 | Sort-Object -Property Confidence -Descending
    
    foreach ($finding in $findings) {
        $report += @"

**[$($finding.Category)] $($finding.FileName)**
- Quote: "$($finding.Quote)"
- Explanation: $($finding.Explanation)
- Legal Significance: $($finding.LegalSignificance)

"@
    }
}

# High confidence findings
$highConfidence = $allFindings | Where-Object {$_.Confidence -eq 'high'} | Sort-Object -Property Category

if ($highConfidence.Count -gt 0) {
    $report += @"

## HIGH CONFIDENCE FINDINGS ($($highConfidence.Count) instances)

These findings have the strongest evidentiary support and legal significance:

"@
    
    foreach ($finding in $highConfidence) {
        $report += @"

### [$($finding.Category)] $($finding.FileName)
- **Type:** $($finding.Type)
- **Quote:** "$($finding.Quote)"
- **Explanation:** $($finding.Explanation)
- **Legal Significance:** $($finding.LegalSignificance)

---

"@
    }
}

# Legal implications
$report += @"

## LEGAL IMPLICATIONS AND RECOMMENDED ACTIONS

### Potential Claims Arising from False Statements:

1. **Perjury (MCL 750.422 - 750.425)**
   - False statements made under oath
   - Criminal penalties: Felony, up to 15 years imprisonment

2. **Fraud (MCL 750.218)**
   - Intentional misrepresentations to gain advantage
   - Criminal penalties: Felony, imprisonment and fines

3. **Contempt of Court (MCR 3.606)**
   - Violations of court orders
   - Sanctions: Fines, attorney fees, modification of orders

4. **Bad Faith Litigation**
   - Vexatious proceedings
   - Sanctions under MCR 2.114, MCR 2.625(A)(2)

### Recommended Filings:

"@

# Add specific recommendations based on findings
if (($allFindings | Where-Object {$_.Type -eq 'false_statement'} | Measure-Object).Count -gt 0) {
    $report += @"

- **Motion for Sanctions** - False statements in pleadings (MCR 2.114(E))
- **Motion to Show Cause** - False testimony or affidavits
- **Criminal Referral** - If perjury is substantiated

"@
}

if (($allFindings | Where-Object {$_.Type -eq 'unsupported_claim'} | Measure-Object).Count -gt 0) {
    $report += @"

- **Motion to Strike** - Unsupported allegations from pleadings
- **Motion for Summary Disposition** - Claims lacking factual support (MCR 2.116(C)(10))

"@
}

$report += @"

## METHODOLOGY

This analysis employed:
1. **Document Sampling Strategy:**
   - Court Documents: 50 sampled
   - Judicial Orders: 30 sampled
   - Ex Parte Documents: 50 sampled
   - PPO Documents: 50 sampled
   - Custody Materials: ALL (65 documents)
   - Medical/Psychological: ALL (62 documents)
   - JTC Documents: 30 sampled
   - Communications: 50 sampled

2. **AI Analysis:**
   - Model: Ollama Mistral (local, private)
   - Analysis criteria: False statements, lies, unsupported claims, bias, inconsistencies, omissions
   - Confidence scoring: High/Medium/Low

3. **Legal Framework:**
   - Michigan Court Rules
   - Michigan Compiled Laws
   - Case law on perjury, fraud, and sanctions

---

## APPENDIX: DETAILED FINDINGS

Complete CSV dataset available at: C:\Users\andre\Desktop\findings_complete.csv

### Total Documents by Category:
"@

foreach ($catGroup in $byCategory | Sort-Object Name) {
    $report += "- $($catGroup.Name): $($catGroup.Count) findings`n"
}

$report += @"

---

**Report Generated:** $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
**Total Analysis Time:** $(($processed * 5) / 60) minutes (estimated)
**Evidence Base:** ALL_PC_EVIDENCE_EXTRACTED (8,768 PDFs, 870 emails, ~51 GB)

"@

# Save report
$report | Out-File -FilePath $OutputPath -Encoding UTF8 -Force

Write-Host "`nCOMPREHENSIVE REPORT SAVED TO:" -ForegroundColor Green
Write-Host $OutputPath -ForegroundColor Yellow

# Display summary
Write-Host "`n=== SUMMARY ===" -ForegroundColor Cyan
Write-Host "Documents Processed: $processed" -ForegroundColor White
Write-Host "Total Findings: $($allFindings.Count)" -ForegroundColor White
Write-Host "High Confidence: $(($allFindings | Where-Object {$_.Confidence -eq 'high'} | Measure-Object).Count)" -ForegroundColor White
Write-Host "Failed: $failed" -ForegroundColor White

Write-Host "`nAnalysis complete! Review the comprehensive report for all findings." -ForegroundColor Green
