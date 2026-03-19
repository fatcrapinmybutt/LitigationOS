
# ================================================
# 🧠 FRED-AI v2.0 – Full Infrastructure Upgrade
# Location: F:\FRED
# Author: AJP Legal Systems / ChatGPT-AI Legal Automation
# ================================================

$root = "F:\FRED"

# === 1. Primary Structure ===
$baseFolders = @(
    "$root",
    "$root\Evidence\By_Case",
    "$root\Evidence\By_Type",
    "$root\Evidence\By_Party",
    "$root\Evidence\Exhibits",
    "$root\Evidence\FOIA_Responses",
    "$root\Evidence\Sanctions_Proof",
    "$root\Evidence\Video_Evidence",
    "$root\Evidence\Audio_Evidence",
    "$root\Evidence\!_Master_Index",
    "$root\Organized",
    "$root\Organized\Court_Submission_Ready",
    "$root\Documents\Drafts",
    "$root\Documents\Final",
    "$root\Logs",
    "$root\Scripts",
    "$root\Scripts\Templates",
    "$root\Backups",
    "$root\Opposing_Counsel\Emily_Watson",
    "$root\Opposing_Counsel\Shady_Oaks_Legal",
    "$root\Tactical_Modules\Custody_Modification",
    "$root\Tactical_Modules\PPO_Termination",
    "$root\Tactical_Modules\Contempt_Filing",
    "$root\Needs_Review"
)

# === 2. Evidence Matrix Subfolders ===
$matrix = @{
    "Evidence\By_Case" = @("Custody_23-123456-CZ", "Housing_25186592GC", "PPO_2024-00999-PP")
    "Evidence\By_Type" = @("Orders", "Motions", "Affidavits", "Exhibits", "Police_Reports", "Transcripts", "Medical_Records", "Declarations")
    "Evidence\By_Party" = @("Emily_Watson", "Cody_Watson", "Lori_Watson", "Ron_Berry", "Shady_Oaks_MHP_LLC")
    "Evidence\Exhibits" = @("Exhibit_Y_AppClose_Matrix", "Exhibit_S_False_Allegations", "Exhibit_G_Witness_Statements", "Exhibit_D_Medical_Neglect")
}

# === 3. Create All Folders ===
Write-Host "`n📁 Creating folder structure..."
foreach ($folder in $baseFolders) {
    if (-not (Test-Path $folder)) {
        New-Item -ItemType Directory -Path $folder | Out-Null
    }
}

Write-Host "`n🧠 Building Evidence Matrix folders..."
foreach ($category in $matrix.Keys) {
    foreach ($subfolder in $matrix[$category]) {
        $path = Join-Path "$root\$category" $subfolder
        if (-not (Test-Path $path)) {
            New-Item -Path $path -ItemType Directory | Out-Null
        }
    }
}

# === 4. Detect and Move Large/Unknown Files ===
Write-Host "`n⚠️ Scanning for large/unlabeled files outside FRED..."
$allFiles = Get-ChildItem -Path "F:\" -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $_.FullName -notlike "$root*" }

foreach ($file in $allFiles) {
    $ext = $file.Extension.ToLower()
    $isLarge = $file.Length -gt 300MB
    $isUnknown = ($ext -eq "") -or ($ext -eq ".bin") -or ($ext -eq ".dat")
    if ($isLarge -or $isUnknown) {
        $dest = Join-Path "$root\Needs_Review" $file.Name
        Move-Item -Path $file.FullName -Destination $dest -Force -ErrorAction SilentlyContinue
        Write-Host "→ Moved to Needs_Review: $($file.Name)"
    }
}

# === 5. Remove Empty Non-FRED Folders ===
Write-Host "`n🧹 Removing empty folders (outside of FRED)..."
Get-ChildItem -Path "F:\" -Recurse -Directory |
    Where-Object { ($_.FullName -notlike "$root*") -and ((Get-ChildItem -Path $_.FullName -Recurse -Force -ErrorAction SilentlyContinue).Count -eq 0) } |
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "`n✅ FRED-AI v2.0 – Expanded structure complete. You're ready to dominate court filings."
