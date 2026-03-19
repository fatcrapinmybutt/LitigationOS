# FRED-COMPLIANT TIMELINE + OCR EXTRACTOR v1.2
# Adds JSON + CSV export for ingestion by FRED_LITIGATION_OS

$sourcePath = "F:\LLC_Litigation_Archive"
$timelineTxt = Join-Path $sourcePath "FRED_Timeline_Output.txt"
$timelineJson = Join-Path $sourcePath "FRED_Timeline_Output.json"
$timelineCsv = Join-Path $sourcePath "FRED_Timeline_Output.csv"
$timelineData = @()

# ✅ Ensure base folder exists
if (!(Test-Path $sourcePath)) {
    New-Item -ItemType Directory -Path $sourcePath | Out-Null
}

# TIMESTAMP PATTERNS
$timestampPatterns = @(
    "\b(?:\d{1,2}[-/ ])?(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[-/ ]\d{2,4}\b",
    "\b\d{1,2}/\d{1,2}/\d{2,4}\b",
    "\b\d{4}-\d{2}-\d{2}\b"
)

function Extract-TextFromPDF {
    param([string]$pdfPath)
    try {
        $tempImg = "$env:TEMP\ocr_page.png"
        $tempTxt = "$env:TEMP\ocr_output.txt"
        & magick -density 300 "$pdfPath[0]" -quality 100 $tempImg
        & tesseract $tempImg $tempTxt -l eng
        return Get-Content "$tempTxt.txt" -Raw
    } catch {
        Write-Warning "OCR failed on $pdfPath"
        return ""
    }
}

function Extract-TimelineFromText {
    param([string]$text, [string]$origin)
    foreach ($pattern in $timestampPatterns) {
        $matches = [regex]::Matches($text, $pattern)
        foreach ($match in $matches) {
            $entry = [PSCustomObject]@{
                Date = $match.Value
                Source = $origin
            }
            $global:timelineData += $entry
        }
    }
}

$files = Get-ChildItem -Path $sourcePath -Recurse -Include *.pdf, *.txt, *.docx -File
foreach ($file in $files) {
    $text = ""
    if ($file.Extension -eq ".pdf") {
        $text = Extract-TextFromPDF -pdfPath $file.FullName
    } elseif ($file.Extension -eq ".txt") {
        $text = Get-Content $file.FullName -Raw
    } elseif ($file.Extension -eq ".docx") {
        try {
            $doc = [System.IO.Packaging.Package]::Open($file.FullName)
            $reader = New-Object System.IO.StreamReader($doc.GetRelationshipsByType("http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument").TargetUri.OriginalString)
            $text = $reader.ReadToEnd()
            $reader.Close()
        } catch {
            Write-Warning "DOCX read failed on $($file.FullName)"
        }
    }

    Extract-TimelineFromText -text $text -origin $file.FullName
}

# Export timeline in TXT, JSON, and CSV formats
$timelineData | Sort-Object Date | ForEach-Object { "$($_.Date)`tFROM: $($_.Source)" } | Out-File -FilePath $timelineTxt -Encoding UTF8 -Force
$timelineData | Sort-Object Date | ConvertTo-Json -Depth 3 | Out-File -FilePath $timelineJson -Encoding UTF8 -Force
$timelineData | Sort-Object Date | Export-Csv -Path $timelineCsv -NoTypeInformation -Encoding UTF8

Write-Host "`n✅ Timeline exported to:`n- $timelineTxt`n- $timelineJson`n- $timelineCsv"
