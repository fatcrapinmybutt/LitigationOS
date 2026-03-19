# FRED-COMPLIANT TIMELINE + OCR EXTRACTOR v1.0
# Adds timeline generation and per-file OCR capability
# Requires: Windows PowerShell, Windows 10+, Tesseract OCR (installed & in PATH)

$sourcePath = "F:\LLC_Litigation_Archive"
$timelinePath = Join-Path $sourcePath "FRED_Timeline_Output.txt"
$timelineData = @()
Add-Type -AssemblyName System.Windows.Forms

# TIMESTAMP REGEXES – EXTENDABLE
$timestampPatterns = @(
    "\b(?:\d{1,2}[-/ ])?(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[-/ ]\d{2,4}\b",
    "\b\d{1,2}/\d{1,2}/\d{2,4}\b",
    "\b\d{4}-\d{2}-\d{2}\b"
)

function Extract-TextFromPDF {
    param([string]$pdfPath)
    try {
        # Extract text using Tesseract via OCR fallback
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
            $line = "$($match.Value)`tFROM: $origin"
            $timelineData += $line
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

# Final writeout
$timelineData | Sort-Object | Out-File -FilePath $timelinePath -Encoding UTF8 -Force
Write-Host "`n✅ Timeline extracted to: $timelinePath"
