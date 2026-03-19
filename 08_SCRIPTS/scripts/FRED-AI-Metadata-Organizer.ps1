
# ==========================================================
# 🧠 FRED-AI v4.0 – Metadata-Aware Legal File Organizer
# Description: Scans file content (PDF, DOCX, TXT) to classify by legal category
# Requirements: Word COM, PDF text extractor installed (optional)
# Author: AJP Legal Systems / ChatGPT-AI Legal Automation
# ==========================================================

$Root = "F:\FRED"
$Source = "$Root\Organized"
$Log = "$Root\Logs\metadata_organizer.log"
$NeedsReview = "$Root\Needs_Review"
$DryRun = $false  # Set to $true to simulate

# Category keyword mapping (content-based)
$ContentMap = @{
    "Evidence\Police_Reports" = @("officer", "responded", "report #", "incident", "dispatcher", "call log")
    "Evidence\Medical_Records" = @("pediatric", "immunization", "health record", "visit summary", "diagnosis")
    "Evidence\Declarations" = @("i declare under", "unsworn declaration", "affidavit", "testify")
    "Evidence\Exhibits" = @("exhibit", "attached hereto", "marked as exhibit")
    "Documents\Final" = @("signed this", "final judgment", "court order")
    "Evidence\Transcripts" = @("court reporter", "transcription", "testimony")
}

# Create log
if (-not (Test-Path $Log)) {
    New-Item -Path $Log -ItemType File -Force | Out-Null
}

# Helper: extract text from DOCX
function Get-DocxText($filePath) {
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    try {
        $doc = $word.Documents.Open($filePath, $false, $true)
        $text = $doc.Content.Text
        $doc.Close($false)
        return $text
    } catch {
        return ""
    } finally {
        $word.Quit()
        [System.Runtime.Interopservices.Marshal]::ReleaseComObject($word) | Out-Null
    }
}

# Helper: extract text from TXT or PDF (optional external tool for PDF)
function Get-FileText($filePath) {
    $ext = [System.IO.Path]::GetExtension($filePath).ToLower()
    if ($ext -eq ".txt") {
        return Get-Content -Path $filePath -Raw -ErrorAction SilentlyContinue
    } elseif ($ext -eq ".docx") {
        return Get-DocxText $filePath
    } elseif ($ext -eq ".pdf") {
        return ""  # Placeholder for future PDF extractor integration
    } else {
        return ""
    }
}

# Process files
$files = Get-ChildItem -Path $Source -Recurse -File -Include *.docx, *.txt, *.pdf

foreach ($file in $files) {
    $content = Get-FileText $file.FullName
    $matched = $false

    foreach ($destKey in $ContentMap.Keys) {
        foreach ($keyword in $ContentMap[$destKey]) {
            if ($content -like "*$keyword*") {
                $targetPath = Join-Path -Path $Root -ChildPath $destKey
                if (-not (Test-Path $targetPath)) {
                    New-Item -Path $targetPath -ItemType Directory -Force | Out-Null
                }

                $newFilePath = Join-Path -Path $targetPath -ChildPath $file.Name
                if (-not $DryRun) {
                    Move-Item -Path $file.FullName -Destination $newFilePath -Force
                }

                Add-Content -Path $Log -Value "Moved by metadata: $($file.FullName) → $newFilePath"
                Write-Host "📂 Moved: $($file.Name) → $destKey"
                $matched = $true
                break
            }
        }
        if ($matched) { break }
    }

    if (-not $matched) {
        $fallback = $NeedsReview
        if (-not (Test-Path $fallback)) {
            New-Item -Path $fallback -ItemType Directory | Out-Null
        }

        $dest = Join-Path $fallback $file.Name
        if (-not $DryRun) {
            Move-Item $file.FullName $dest -Force
        }

        Add-Content -Path $Log -Value "Unmatched content: $($file.FullName) → $dest"
        Write-Host "⚠️ Unmatched: $($file.Name) → Needs_Review"
    }
}

Write-Host "`n✅ Metadata-based file organization complete. See log for details."
