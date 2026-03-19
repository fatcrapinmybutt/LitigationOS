
# ==========================================================
# 📎 FRED-AI v3.1 – PDF Exhibit Cover Page Generator
# Description: Generates PDF cover pages with exhibit labels and titles
# Requirements: Word installed, uses Word COM for PDF export
# Author: AJP Legal Systems / ChatGPT-AI Legal Automation
# ==========================================================

$exhibitRoot = "F:\FRED\Evidence\Exhibits"
$coverDir = Join-Path $exhibitRoot "Covers"
if (-not (Test-Path $coverDir)) {
    New-Item -ItemType Directory -Path $coverDir | Out-Null
}

# Start Word COM object
$word = New-Object -ComObject Word.Application
$word.Visible = $false

# Generate cover pages for each exhibit
$exhibits = Get-ChildItem -Path $exhibitRoot -File -Include *.pdf -ErrorAction SilentlyContinue | Where-Object { $_.Name -match "^Exhibit_[A-Z]\.pdf$" }

foreach ($file in $exhibits) {
    $label = $file.BaseName
    $title = $label -replace "_", " "
    $doc = $word.Documents.Add()
    $range = $doc.Range()
    $range.Font.Size = 28
    $range.Font.Bold = $true
    $range.ParagraphFormat.Alignment = 1  # Center
    $range.Text = "$title`r`n(FRED Legal Exhibit)"

    $pdfPath = Join-Path $coverDir "$label-Cover.pdf"
    $doc.ExportAsFixedFormat($pdfPath, 17)  # 17 = wdExportFormatPDF
    $doc.Close($false)
    Write-Host "🧾 Created cover: $pdfPath"
}

$word.Quit()
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($word) | Out-Null

Write-Host "`n✅ PDF exhibit cover pages generated successfully."
