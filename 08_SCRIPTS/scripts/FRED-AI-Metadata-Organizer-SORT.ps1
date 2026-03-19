
# ==========================================================
# 🧠 FRED-AI v4.1 – Metadata-Aware File Organizer (Simplified)
# Description: Analyzes and organizes DOCX, TXT, and PDF files by contents
# Moves files based on keyword matches into categorized folders
# Author: AJP Legal Systems / ChatGPT-AI Legal Automation
# ==========================================================

$Root = "F:\FRED"
$Source = "$Root\Organized"
$Log = "$Root\Logs\metadata_organizer.log"
$NeedsReview = "$Root\Needs_Review"
$DryRun = $false  # Set to $true to simulate only

# === Classification Keywords ===
$ContentMap = @{
    "Evidence\Police_Reports"     = @("officer", "responded", "report #", "incident", "dispatcher", "call log")
    "Evidence\Medical_Records"    = @("pediatric", "immunization", "health record", "visit summary", "diagnosis")
    "Evidence\Declarations"       = @("i declare under", "unsworn declaration", "affidavit", "testify")
    "Evidence\Exhibits"           = @("exhibit", "attached hereto", "marked as exhibit")
    "Documents\Final"             = @("signed this", "final judgment", "court order")
    "Evidence\Transcripts"        = @("court reporter", "transcription", "testimony")
}

# === Initialize Log ===
if (-not (Test-Path $Log)) {
    New-Item -Path $Log -ItemType File -Force | Out-Null
} else {
    Clear-Content -Path $Log
}

# === Helper: extract text from DOCX ===
function Get-DocxText {
    param([string]$filePath)
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

# === Helper: extract text from supported file types ===
function Get-FileText {
    param([string]$filePath)
    $ext = [System.IO.Path]::GetExtension($filePath).ToLower()
    if ($ext -eq ".txt") {
        return Get-Content -Path $filePath -Raw -ErrorAction SilentlyContinue
    } elseif ($ext -eq ".docx") {
        return Get-DocxText -filePath $filePath
    } elseif ($ext -eq ".pdf") {
        return ""  # Placeholder for future PDF OCR integration
    } else {
        return ""
    }
}

# === Scan for Files ===
$files = Get-ChildItem "$Source\*" -Recurse -File | Where-Object {
    $_.Extension -in ".docx", ".txt", ".pdf"
}

foreach ($file in $files) {
    $content = Get-FileText -filePath $file.FullName
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

                Add-Content -Path $Log -Value "Moved: $($file.FullName) → $newFilePath"
                Write-Host "✅ Moved: $($file.Name) → $destKey"
                $matched = $true
                break
            }
        }
        if ($matched) { break }
    }

    if (-not $matched) {
        if (-not (Test-Path $NeedsReview)) {
            New-Item -Path $NeedsReview -ItemType Directory | Out-Null
        }

        $fallback = Join-Path $NeedsReview $file.Name
        if (-not $DryRun) {
            Move-Item -Path $file.FullName -Destination $fallback -Force
        }

        Add-Content -Path $Log -Value "Unmatched: $($file.FullName) → $fallback"
        Write-Host "⚠️ Unmatched: $($file.Name) → Needs_Review"
    }
}

Write-Host ""
Write-Host "✅ Metadata-based organization complete. Review $Log for details."
