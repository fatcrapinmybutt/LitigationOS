$outputDir = "C:\users\andre\LITIGATIONOS_MASTER\OMNI_HARVEST_20260216_0357\07_EXTRACTIONS\TIER2_EVIDENCE\TEXTMASTER"

# Get all TXT files
$files = Get-ChildItem -Path $outputDir -Filter "*.txt" | Sort-Object Name
Write-Host "Processing $($files.Count) files..."

# Initialize collections
$fileIndex = @()
$citations = @()
$facts = @()
$legalTheories = @()

$fileNum = 0
foreach ($file in $files) {
    $fileNum++
    if ($fileNum % 50 -eq 0) { Write-Host "Processed $fileNum files..." }
    
    try {
        $content = Get-Content $file.FullName -Raw -ErrorAction SilentlyContinue
        if (-not $content) { continue }
        
        $wordCount = ($content -split '\s+').Count
        $lineCount = ($content -split "`n").Count
        
        # Index entry
        $fileIndex += [PSCustomObject]@{
            FileName = $file.Name
            FilePath = $file.FullName
            SizeBytes = $file.Length
            WordCount = $wordCount
            LineCount = $lineCount
            LastModified = $file.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss")
        }
        
        # Extract MCR/MCL citations (Michigan Compiled Laws)
        $mcrPattern = 'MCR\s+\d+\.\d+(?:\.\d+)?'
        $mclPattern = 'MCL\s+\d+\.\d+(?:\.\d+)?[a-z]?'
        
        $mcrMatches = [regex]::Matches($content, $mcrPattern, 'IgnoreCase')
        $mclMatches = [regex]::Matches($content, $mclPattern, 'IgnoreCase')
        
        foreach ($match in $mcrMatches) {
            $context = ""
            $pos = $match.Index
            $start = [Math]::Max(0, $pos - 100)
            $length = [Math]::Min(200, $content.Length - $start)
            if ($start + $length -le $content.Length) {
                $context = $content.Substring($start, $length) -replace '\s+', ' '
            }
            
            $citations += [PSCustomObject]@{
                SourceFile = $file.Name
                CitationType = "MCR"
                Citation = $match.Value
                Context = $context.Trim()
            }
        }
        
        foreach ($match in $mclMatches) {
            $context = ""
            $pos = $match.Index
            $start = [Math]::Max(0, $pos - 100)
            $length = [Math]::Min(200, $content.Length - $start)
            if ($start + $length -le $content.Length) {
                $context = $content.Substring($start, $length) -replace '\s+', ' '
            }
            
            $citations += [PSCustomObject]@{
                SourceFile = $file.Name
                CitationType = "MCL"
                Citation = $match.Value
                Context = $context.Trim()
            }
        }
        
        # Extract case law citations
        $casePattern = '\b[A-Z][a-z]+\s+v\.?\s+[A-Z][a-z]+(?:,\s+\d+\s+\w+\s+\d+)?'
        $caseMatches = [regex]::Matches($content, $casePattern)
        
        foreach ($match in $caseMatches) {
            $context = ""
            $pos = $match.Index
            $start = [Math]::Max(0, $pos - 100)
            $length = [Math]::Min(200, $content.Length - $start)
            if ($start + $length -le $content.Length) {
                $context = $content.Substring($start, $length) -replace '\s+', ' '
            }
            
            $citations += [PSCustomObject]@{
                SourceFile = $file.Name
                CitationType = "CaseLaw"
                Citation = $match.Value
                Context = $context.Trim()
            }
        }
        
        # Extract fact statements (sentences with evidentiary keywords)
        $factKeywords = @('on or about', 'dated', 'signed', 'executed', 'witness', 'exhibit', 'attached', 'document', 'evidence', 'plaintiff', 'defendant', 'respondent', 'petitioner')
        $sentences = $content -split '[\.\!\?]\s+'
        
        foreach ($sentence in $sentences) {
            $sentence = $sentence.Trim()
            if ($sentence.Length -gt 20 -and $sentence.Length -lt 500) {
                foreach ($keyword in $factKeywords) {
                    if ($sentence -match $keyword) {
                        $facts += [PSCustomObject]@{
                            SourceFile = $file.Name
                            FactStatement = $sentence.Substring(0, [Math]::Min(300, $sentence.Length))
                            Keyword = $keyword
                        }
                        break
                    }
                }
            }
        }
        
        # Extract legal theories/arguments
        $theoryKeywords = @('therefore', 'accordingly', 'pursuant to', 'court should', 'court must', 'entitled to', 'violation of', 'breach of', 'claim', 'cause of action', 'relief', 'damages', 'injunction', 'summary judgment', 'motion to', 'prayer for relief')
        
        foreach ($sentence in $sentences) {
            $sentence = $sentence.Trim()
            if ($sentence.Length -gt 30 -and $sentence.Length -lt 600) {
                foreach ($keyword in $theoryKeywords) {
                    if ($sentence -match $keyword) {
                        $legalTheories += [PSCustomObject]@{
                            SourceFile = $file.Name
                            Theory = $sentence.Substring(0, [Math]::Min(400, $sentence.Length))
                            Keyword = $keyword
                        }
                        break
                    }
                }
            }
        }
        
    } catch {
        Write-Host "Error processing $($file.Name): $_"
    }
}

Write-Host "Generating output files..."

# Export TEXTMASTER_INDEX.csv
$indexPath = Join-Path $outputDir "TEXTMASTER_INDEX.csv"
$fileIndex | Export-Csv -Path $indexPath -NoTypeInformation -Encoding UTF8
Write-Host "Created: TEXTMASTER_INDEX.csv ($($fileIndex.Count) files)"

# Export CITATIONS_EXTRACTED.csv
$citationsPath = Join-Path $outputDir "CITATIONS_EXTRACTED.csv"
$citations | Export-Csv -Path $citationsPath -NoTypeInformation -Encoding UTF8
Write-Host "Created: CITATIONS_EXTRACTED.csv ($($citations.Count) citations)"

# Export FACTS_EXTRACTED.csv
$factsPath = Join-Path $outputDir "FACTS_EXTRACTED.csv"
$facts | Select-Object -First 5000 | Export-Csv -Path $factsPath -NoTypeInformation -Encoding UTF8
Write-Host "Created: FACTS_EXTRACTED.csv ($($facts.Count) facts, saved top 5000)"

# Generate LEGAL_THEORIES_INDEX.md
$theoriesPath = Join-Path $outputDir "LEGAL_THEORIES_INDEX.md"
$theoriesMd = @"
# LEGAL THEORIES INDEX
**Generated:** $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
**Source:** TEXTMASTER Archive Analysis
**Total Arguments Identified:** $($legalTheories.Count)

---

## SUMMARY OF LEGAL ARGUMENTS

"@

$theoriesByFile = $legalTheories | Group-Object SourceFile | Sort-Object Count -Descending | Select-Object -First 50

foreach ($group in $theoriesByFile) {
    $theoriesMd += "`n### $($group.Name)`n"
    $theoriesMd += "**Argument Count:** $($group.Count)`n`n"
    
    foreach ($theory in ($group.Group | Select-Object -First 10)) {
        $theoriesMd += "- $($theory.Theory)`n"
    }
    $theoriesMd += "`n"
}

$theoriesMd | Out-File -FilePath $theoriesPath -Encoding UTF8
Write-Host "Created: LEGAL_THEORIES_INDEX.md"

# Generate TEXTMASTER_ANALYSIS.md
$analysisPath = Join-Path $outputDir "TEXTMASTER_ANALYSIS.md"

$totalSize = ($fileIndex | Measure-Object -Property SizeBytes -Sum).Sum
$totalWords = ($fileIndex | Measure-Object -Property WordCount -Sum).Sum
$uniqueMCR = ($citations | Where-Object CitationType -eq 'MCR' | Select-Object -Property Citation -Unique).Count
$uniqueMCL = ($citations | Where-Object CitationType -eq 'MCL' | Select-Object -Property Citation -Unique).Count
$uniqueCases = ($citations | Where-Object CitationType -eq 'CaseLaw' | Select-Object -Property Citation -Unique).Count

$analysisMd = @"
# TEXTMASTER ANALYSIS REPORT
**Analysis Date:** $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
**Archive:** TEXTMASTER.zip (2.80 MB)

---

## EXECUTIVE SUMMARY

This analysis represents a comprehensive extraction and parsing of the TEXTMASTER archive, containing pre-analyzed legal research materials for the Pigors v. Watson litigation.

### ARCHIVE STATISTICS
- **Total Files:** $($fileIndex.Count)
- **Total Size:** $([Math]::Round($totalSize/1MB, 2)) MB
- **Total Words:** $($totalWords.ToString('N0'))
- **Average Words per File:** $([Math]::Round($totalWords/$fileIndex.Count, 0))

---

## DOCUMENT CATEGORIES

### Exhibit Binder Files
Files from the MSC/JTC Exhibits Binder (v5):
- Pattern: 2025-10-29_Pigors_v_Watson_MSC-JTC_Exhibits_Binder_v5__p####.txt
- Count: $(($fileIndex | Where-Object {$_.FileName -like '*MSC-JTC_Exhibits_Binder*'}).Count)

### JTC Binder Files  
Files from the JTC MSC Binder:
- Pattern: JTC_MSC_Binder_v5_2025-10-29_19-13-34__p####.txt
- Count: $(($fileIndex | Where-Object {$_.FileName -like 'JTC_MSC_Binder*'}).Count)

### Print Order Master Files
Comprehensive print order documents:
- Pattern: JTC_Print_Order_Master_2025-10-29_with_bookmarks_footer_toc__p####.txt
- Count: $(($fileIndex | Where-Object {$_.FileName -like 'JTC_Print_Order_Master*'}).Count)

### Discovery Documents
Numbered discovery files:
- Pattern: D######.txt
- Count: $(($fileIndex | Where-Object {$_.FileName -like 'D0*'}).Count)

---

## LEGAL CONTENT ANALYSIS

### Citations Extracted
- **Michigan Court Rules (MCR):** $uniqueMCR unique citations
- **Michigan Compiled Laws (MCL):** $uniqueMCL unique citations
- **Case Law References:** $uniqueCases unique cases
- **Total Citations:** $($citations.Count)

### Most Cited Statutes
"@

$topMCR = $citations | Where-Object CitationType -eq 'MCR' | Group-Object Citation | Sort-Object Count -Descending | Select-Object -First 10
if ($topMCR) {
    $analysisMd += "`n#### Top MCR Citations`n"
    foreach ($cit in $topMCR) {
        $analysisMd += "- **$($cit.Name)** - Referenced $($cit.Count) times`n"
    }
}

$topMCL = $citations | Where-Object CitationType -eq 'MCL' | Group-Object Citation | Sort-Object Count -Descending | Select-Object -First 10
if ($topMCL) {
    $analysisMd += "`n#### Top MCL Citations`n"
    foreach ($cit in $topMCL) {
        $analysisMd += "- **$($cit.Name)** - Referenced $($cit.Count) times`n"
    }
}

$analysisMd += @"

### Fact Statements
- **Total Extracted:** $($facts.Count)
- **Saved to CSV:** $(if ($facts.Count -gt 5000) { "5000 (top)" } else { $facts.Count })

### Legal Arguments/Theories
- **Total Identified:** $($legalTheories.Count)
- **Files with Arguments:** $(($legalTheories | Select-Object -Property SourceFile -Unique).Count)

---

## CONTENT QUALITY INDICATORS

### File Size Distribution
- **Smallest File:** $(($fileIndex | Sort-Object SizeBytes | Select-Object -First 1).FileName) - $(($fileIndex | Sort-Object SizeBytes | Select-Object -First 1).SizeBytes) bytes
- **Largest File:** $(($fileIndex | Sort-Object SizeBytes -Descending | Select-Object -First 1).FileName) - $([Math]::Round((($fileIndex | Sort-Object SizeBytes -Descending | Select-Object -First 1).SizeBytes)/1KB, 1)) KB
- **Median Size:** $([Math]::Round((($fileIndex | Sort-Object SizeBytes)[[Math]::Floor($fileIndex.Count/2)].SizeBytes)/1KB, 1)) KB

### Word Count Distribution  
- **Minimum Words:** $(($fileIndex | Sort-Object WordCount | Select-Object -First 1).WordCount)
- **Maximum Words:** $(($fileIndex | Sort-Object WordCount -Descending | Select-Object -First 1).WordCount)
- **Median Words:** $(($fileIndex | Sort-Object WordCount)[[Math]::Floor($fileIndex.Count/2)].WordCount)

---

## USAGE RECOMMENDATIONS

### High-Value Content
1. **Citation Database:** Use CITATIONS_EXTRACTED.csv to build argument foundations
2. **Fact Matrix:** Cross-reference FACTS_EXTRACTED.csv with timeline documents
3. **Theory Development:** Review LEGAL_THEORIES_INDEX.md for argument strategies

### Next Steps
- Cross-reference citations with Michigan case law database
- Map fact statements to specific claims/defenses
- Integrate legal theories into brief templates
- Correlate with other TIER2_EVIDENCE materials

---

## DELIVERABLES CREATED

1. **TEXTMASTER_INDEX.csv** - Complete file catalog
2. **CITATIONS_EXTRACTED.csv** - All statutory and case citations
3. **FACTS_EXTRACTED.csv** - Evidentiary fact statements
4. **LEGAL_THEORIES_INDEX.md** - Categorized legal arguments
5. **TEXTMASTER_ANALYSIS.md** - This comprehensive report

---

*Analysis completed using automated legal content extraction algorithms.*
*Review all extracted content for accuracy before use in litigation.*
"@

$analysisMd | Out-File -FilePath $analysisPath -Encoding UTF8
Write-Host "Created: TEXTMASTER_ANALYSIS.md"

Write-Host "`n=== ANALYSIS COMPLETE ==="
Write-Host "All deliverables created in: $outputDir"
