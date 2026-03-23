# ALLSCANNED Evidence Analysis Script
# Extracts text from PDFs and analyzes with Ollama mistral

param(
    [int]$SamplesPerCategory = 8
)

# Define sampling strategy for each category
$samplingStrategy = @{
    'judge_orders' = @{
        Folders = @('04_2sided_judge_orders')
        Priority = 'HIGH'
        Samples = 10
    }
    'ex_parte' = @{
        Folders = @('01_5th_exparte_suspension', '10_exparte_scanned_mine')
        Priority = 'HIGH'
        Samples = 10
    }
    'custody' = @{
        Folders = @('05_court_docs_ppo_cust', '06_custody_scanned2')
        Priority = 'HIGH'
        Samples = 8
    }
    'transcripts' = @{
        Folders = @('15_transcripts_ppo_oct2024')
        Priority = 'HIGH'
        Samples = 10
    }
    'jtc' = @{
        Folders = @('13_jtc')
        Priority = 'MEDIUM'
        Samples = 8
    }
    'dockets' = @{
        Folders = @('08_dockets_notices_proofs')
        Priority = 'MEDIUM'
        Samples = 6
    }
    'healthwest' = @{
        Folders = @('11_healthwest_1st', '12_healthwest_2nd')
        Priority = 'MEDIUM'
        Samples = 8
    }
}

$baseDir = "C:\Users\andre\Desktop\ALLSCANNED_ANALYSIS\EXTRACTED"
$outputDir = "C:\Users\andre\Desktop\ALLSCANNED_ANALYSIS\REPORTS"
$extractedTextDir = "$outputDir\extracted_texts"

# Create output directories
New-Item -ItemType Directory -Force -Path $extractedTextDir | Out-Null

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "ALLSCANNED EVIDENCE EXTRACTION & ANALYSIS" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Function to extract text from PDF using COM
function Extract-PDFTextCOM {
    param([string]$PdfPath)
    
    try {
        # Try using Word COM automation
        $word = New-Object -ComObject Word.Application
        $word.Visible = $false
        $doc = $word.Documents.Open($PdfPath)
        $text = $doc.Content.Text
        $doc.Close()
        $word.Quit()
        [System.Runtime.Interopservices.Marshal]::ReleaseComObject($word) | Out-Null
        return $text
    }
    catch {
        return $null
    }
}

# Function to extract text from PDF using basic method
function Extract-PDFText {
    param([string]$PdfPath)
    
    Write-Host "  Extracting: $([System.IO.Path]::GetFileName($PdfPath))" -ForegroundColor Gray
    
    # Try COM method first
    $text = Extract-PDFTextCOM -PdfPath $PdfPath
    
    if ($text) {
        return $text
    }
    
    # Fallback: Return file metadata and note
    $file = Get-Item $PdfPath
    return @"
[PDF FILE: $($file.Name)]
Size: $([math]::Round($file.Length/1KB, 2)) KB
Created: $($file.CreationTime)
Modified: $($file.LastWriteTime)

[NOTE: Text extraction requires external tool. Manual review recommended.]
"@
}

# Sample and extract from each category
$allExtracts = @{}
$totalExtracted = 0

foreach ($category in $samplingStrategy.Keys | Sort-Object) {
    $config = $samplingStrategy[$category]
    Write-Host "`n--- Processing Category: $category ($($config.Priority) priority) ---" -ForegroundColor Yellow
    
    $categoryExtracts = @()
    $sampledFiles = @()
    
    foreach ($folder in $config.Folders) {
        $folderPath = Join-Path $baseDir $folder
        if (Test-Path $folderPath) {
            $files = Get-ChildItem $folderPath -File -Filter "*.pdf" -Recurse
            $sampleCount = [math]::Min($config.Samples, $files.Count)
            
            # Sample files evenly
            $step = [math]::Max(1, [math]::Floor($files.Count / $sampleCount))
            for ($i = 0; $i -lt $files.Count -and $sampledFiles.Count -lt $config.Samples; $i += $step) {
                $sampledFiles += $files[$i]
            }
        }
    }
    
    Write-Host "  Found $($sampledFiles.Count) files to sample" -ForegroundColor Cyan
    
    foreach ($file in $sampledFiles) {
        $text = Extract-PDFText -PdfPath $file.FullName
        
        if ($text -and $text.Length -gt 50) {
            $extractData = @{
                File = $file.Name
                Category = $category
                Folder = $file.Directory.Name
                Size = $file.Length
                Text = $text
                TextLength = $text.Length
            }
            $categoryExtracts += $extractData
            $totalExtracted++
            
            # Save individual extract
            $safeFileName = $file.BaseName -replace '[^\w\-]', '_'
            $extractFile = Join-Path $extractedTextDir "$category`_$safeFileName.txt"
            $text | Out-File -FilePath $extractFile -Encoding UTF8
        }
    }
    
    $allExtracts[$category] = $categoryExtracts
    Write-Host "  Extracted $($categoryExtracts.Count) documents from $category" -ForegroundColor Green
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "EXTRACTION SUMMARY" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Total documents extracted: $totalExtracted" -ForegroundColor Green
Write-Host "Categories processed: $($allExtracts.Keys.Count)" -ForegroundColor Green
Write-Host "`nExtracted text files saved to: $extractedTextDir" -ForegroundColor Yellow

# Save extraction summary
$summary = @{
    Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    TotalExtracted = $totalExtracted
    CategoriesProcessed = $allExtracts.Keys.Count
    ExtractionsByCategory = @{}
}

foreach ($cat in $allExtracts.Keys) {
    $summary.ExtractionsByCategory[$cat] = @{
        Count = $allExtracts[$cat].Count
        TotalTextLength = ($allExtracts[$cat] | Measure-Object -Property TextLength -Sum).Sum
        Files = $allExtracts[$cat] | ForEach-Object { $_.File }
    }
}

$summaryJson = $summary | ConvertTo-Json -Depth 10
$summaryJson | Out-File -FilePath "$outputDir\extraction_summary.json" -Encoding UTF8

Write-Host "`nExtraction summary saved: $outputDir\extraction_summary.json" -ForegroundColor Green
Write-Host "`nReady for Ollama mistral analysis..." -ForegroundColor Cyan
