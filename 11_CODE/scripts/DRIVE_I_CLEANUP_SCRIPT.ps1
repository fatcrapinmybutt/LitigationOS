# ============================================================================
# DRIVE I: (FRED) CLEANUP SCRIPT — Generated 2025-07-17
# ============================================================================
# REVIEW EVERY SECTION BEFORE UNCOMMENTING AND RUNNING!
# All destructive commands are commented out with -WhatIf safety.
# Run from an ELEVATED (Administrator) PowerShell for full access.
#
# CURRENT STATE:
#   Volume:  FRED (I:)
#   Total:   465.74 GB
#   Used:    454.75 GB (97.6%)
#   Free:    10.99 GB  ← CRITICALLY LOW
#
# SPACE ACCOUNTING:
#   fred/                           266.53 GB (visible content)
#   Root-level files                  5.52 GB
#   Recycle Bin                       0.35 GB
#   .omni_cache                       0.02 GB
#   Other visible dirs                0.10 GB
#   ─────────────────────────────────────────
#   Accounted:                     ~272.52 GB
#   Unaccounted (VSS/shadow):     ~182.23 GB  ← Likely Volume Shadow Copies
#
# TOP SPACE CONSUMERS IN fred/:
#   Organized_Litigation_Supreme     82.30 GB  (249,572 files)
#   Archives                         70.86 GB  (225 files — mostly ZIPs)
#   GitRepo                          43.71 GB  (175,927 files)
#   GOOGLE DOWNLOADS                 20.19 GB  (555 files — includes LLM models)
#   Videos                           17.05 GB  (264 files)
#   GitHub                            9.76 GB  (57,249 files)
#   Photos                            5.15 GB  (8,154 files)
#
# CLEANUP TARGETS IDENTIFIED:
#   1. _Duplicates folder            22.81 GB  (109,381 files) — BIGGEST QUICK WIN
#   2. Recycle Bin                    0.35 GB   (1,539 files)   — SAFE
#   3. Temp/cache/bak/log files      1.41 GB   (249 files)     — MOSTLY SAFE
#   4. Volume Shadow Copies        ~182 GB      — REQUIRES ADMIN
#   5. LLM model files              17.93 GB   (in GOOGLE DOWNLOADS)
#   6. ISO files                      5.42 GB   (1 file)
#   7. Large ZIP archives           106.99 GB   (1,071 files)  — REVIEW NEEDED
# ============================================================================

$ErrorActionPreference = "SilentlyContinue"

function Write-Phase($title) {
    Write-Host "`n" -NoNewline
    Write-Host ("=" * 70) -ForegroundColor Cyan
    Write-Host "  $title" -ForegroundColor Cyan
    Write-Host ("=" * 70) -ForegroundColor Cyan
}

# ─────────────────────────────────────────────────────────────────────────────
# PHASE 0: PRE-FLIGHT CHECK
# ─────────────────────────────────────────────────────────────────────────────
Write-Phase "PHASE 0: Pre-Flight Check"

if (-not (Test-Path "I:\")) {
    Write-Host "ERROR: Drive I: is not accessible. Aborting." -ForegroundColor Red
    exit 1
}

$drive = Get-PSDrive I
$freeBefore = [math]::Round($drive.Free/1GB, 2)
Write-Host "Drive I: (FRED) accessible"
Write-Host "Free space before cleanup: $freeBefore GB" -ForegroundColor Yellow

# ─────────────────────────────────────────────────────────────────────────────
# PHASE 1: EMPTY RECYCLE BIN — ~0.35 GB (SAFE)
# ─────────────────────────────────────────────────────────────────────────────
Write-Phase "PHASE 1: Empty Recycle Bin (~0.35 GB)"
Write-Host "1,539 files in Recycle Bin on I:"

# UNCOMMENT TO EXECUTE:
# Clear-RecycleBin -DriveLetter I -Force -ErrorAction SilentlyContinue
# Write-Host "Recycle Bin emptied." -ForegroundColor Green

# ─────────────────────────────────────────────────────────────────────────────
# PHASE 2: REMOVE TEMP/CACHE/BAK FILES — ~1.41 GB (MOSTLY SAFE)
# ─────────────────────────────────────────────────────────────────────────────
Write-Phase "PHASE 2: Temp/Cache/Bak/Log Files (~1.41 GB)"

# DRY RUN — shows what would be deleted:
$tempFiles = Get-ChildItem "I:\" -Recurse -File | Where-Object {
    $_.Extension -in '.tmp', '.bak', '.cache'
}
Write-Host "Found $($tempFiles.Count) temp/bak/cache files"
$tempFiles | Select-Object @{N='SizeMB';E={[math]::Round($_.Length/1MB,2)}}, FullName |
    Sort-Object SizeMB -Descending | Select-Object -First 10 | Format-Table -AutoSize

# UNCOMMENT TO EXECUTE (with -WhatIf safety first):
# $tempFiles | Remove-Item -WhatIf
# After verifying -WhatIf output, remove -WhatIf:
# $tempFiles | Remove-Item -Force

# NOTE: .log files excluded — they may contain litigation-relevant audit trails.
# To include .log files, add '.log' to the extension list above and review first.

# ─────────────────────────────────────────────────────────────────────────────
# PHASE 3: CLEAN .omni_cache — ~0.02 GB (SAFE)
# ─────────────────────────────────────────────────────────────────────────────
Write-Phase "PHASE 3: Clean .omni_cache (~0.02 GB)"

# UNCOMMENT TO EXECUTE:
# Remove-Item "I:\.omni_cache" -Recurse -Force -ErrorAction SilentlyContinue
# Write-Host ".omni_cache removed." -ForegroundColor Green

# ─────────────────────────────────────────────────────────────────────────────
# PHASE 4: ARCHIVE THEN REMOVE _Duplicates — 22.81 GB (REVIEW FIRST!)
# ─────────────────────────────────────────────────────────────────────────────
Write-Phase "PHASE 4: _Duplicates Folder (22.81 GB / 109,381 files)"
Write-Host "Location: I:\fred\Organized_Litigation_Supreme\_Duplicates"
Write-Host ""
Write-Host "WARNING: These are identified duplicates from a prior sort operation." -ForegroundColor Yellow
Write-Host "Before deleting, verify originals still exist elsewhere." -ForegroundColor Yellow

# STEP A: Generate a manifest of what's in _Duplicates (run this first!)
# $dupPath = "I:\fred\Organized_Litigation_Supreme\_Duplicates"
# $manifest = Get-ChildItem $dupPath -Recurse -File | Select-Object Name, Length, FullName
# $manifest | Export-Csv "I:\fred\_Duplicates_MANIFEST.csv" -NoTypeInformation
# Write-Host "Manifest saved to I:\fred\_Duplicates_MANIFEST.csv" -ForegroundColor Green

# STEP B: After reviewing manifest, rename folder to mark for deletion
# $archiveDate = Get-Date -Format "yyyy-MM-dd"
# Rename-Item $dupPath "${dupPath}_REVIEWED_${archiveDate}"

# STEP C: After confirming originals are safe, delete
# Remove-Item "${dupPath}_REVIEWED_${archiveDate}" -Recurse -Force
# Write-Host "_Duplicates removed. Freed ~22.81 GB" -ForegroundColor Green

# ─────────────────────────────────────────────────────────────────────────────
# PHASE 5: LLM MODEL FILES — ~17.93 GB (REVIEW — may be needed)
# ─────────────────────────────────────────────────────────────────────────────
Write-Phase "PHASE 5: LLM Model Files in GOOGLE DOWNLOADS (~17.93 GB)"
Write-Host "These are large AI model files. Delete only if not needed."
Write-Host ""

$modelFiles = @(
    "I:\fred\GOOGLE DOWNLOADS\Mistral-7B-Instruct-v0.3.Q5_K_M.gguf",  # 4.9 GB
    "I:\fred\GOOGLE DOWNLOADS\model-00001-of-00003.safetensors",         # 4.7 GB
    "I:\fred\GOOGLE DOWNLOADS\model-00003-of-00003.safetensors",         # 4.3 GB
    "I:\fred\GOOGLE DOWNLOADS\Mistral-7B-Instruct-v0.3.Q4_K_S.gguf"    # 3.9 GB
)

foreach ($f in $modelFiles) {
    if (Test-Path $f) {
        $size = [math]::Round((Get-Item $f).Length/1GB, 2)
        Write-Host "  $size GB — $(Split-Path $f -Leaf)"
    }
}

# UNCOMMENT TO EXECUTE (if models are not in active use):
# foreach ($f in $modelFiles) { Remove-Item $f -Force -ErrorAction SilentlyContinue }
# Write-Host "Model files removed." -ForegroundColor Green

# ─────────────────────────────────────────────────────────────────────────────
# PHASE 6: ISO FILES — ~5.42 GB
# ─────────────────────────────────────────────────────────────────────────────
Write-Phase "PHASE 6: ISO Files (~5.42 GB)"

Get-ChildItem "I:\" -Recurse -File -Filter "*.iso" | ForEach-Object {
    Write-Host "  $([math]::Round($_.Length/1GB, 2)) GB — $($_.FullName)"
}

# UNCOMMENT TO EXECUTE:
# Get-ChildItem "I:\" -Recurse -File -Filter "*.iso" | Remove-Item -Force
# Write-Host "ISO files removed." -ForegroundColor Green

# ─────────────────────────────────────────────────────────────────────────────
# PHASE 7: VOLUME SHADOW COPIES — ~182 GB (REQUIRES ADMIN!)
# ─────────────────────────────────────────────────────────────────────────────
Write-Phase "PHASE 7: Volume Shadow Copies (~182 GB estimated — ADMIN REQUIRED)"
Write-Host "~182 GB is unaccounted for and likely consumed by VSS shadow copies."
Write-Host "This is the SINGLE BIGGEST cleanup opportunity on this drive."
Write-Host ""
Write-Host "Run the following from an ELEVATED PowerShell:" -ForegroundColor Yellow
Write-Host '  vssadmin list shadowstorage /for=I:'
Write-Host '  vssadmin list shadows /for=I:'
Write-Host ""
Write-Host "To delete all shadow copies (IRREVERSIBLE):" -ForegroundColor Red
Write-Host '  vssadmin delete shadows /for=I: /all'
Write-Host ""
Write-Host "To limit shadow storage to 10% of drive:" -ForegroundColor Yellow
Write-Host '  vssadmin resize shadowstorage /for=I: /on=I: /maxsize=10%'

# ─────────────────────────────────────────────────────────────────────────────
# PHASE 8: LARGE ZIP ARCHIVE REVIEW — 106.99 GB (REVIEW CAREFULLY)
# ─────────────────────────────────────────────────────────────────────────────
Write-Phase "PHASE 8: Large ZIP Archive Review (106.99 GB total)"
Write-Host "Top 10 largest ZIP files:" -ForegroundColor Yellow

Get-ChildItem "I:\" -Recurse -File -Filter "*.zip" |
    Sort-Object Length -Descending |
    Select-Object -First 10 |
    ForEach-Object {
        Write-Host "  $([math]::Round($_.Length/1GB, 2)) GB — $($_.FullName)"
    }

Write-Host ""
Write-Host "KEY OBSERVATIONS:" -ForegroundColor Yellow
Write-Host "  - Pictures.zip (19.8 GB) — likely extracted already to Photos/"
Write-Host "  - GUI_09769eb5.zip (15.5 GB) — inside Organized_Litigation_Supreme"
Write-Host "  - OneDrive_2_4-30-2025.zip (12.2 GB) — OneDrive backup"
Write-Host "  - takeout.zip (9.9 GB) — Google Takeout"
Write-Host "  - 11x drive-download ZIPs (~2 GB each) — Google Drive downloads"
Write-Host ""
Write-Host "If these have already been extracted, deleting the ZIPs saves ~70+ GB."

# ─────────────────────────────────────────────────────────────────────────────
# PHASE 9: GIT REPOSITORY CLEANUP — 43.71 GB
# ─────────────────────────────────────────────────────────────────────────────
Write-Phase "PHASE 9: GitRepo Directory (43.71 GB / 175,927 files)"
Write-Host "Location: I:\fred\GitRepo"
Write-Host "This is a massive directory. Check if it's a clone that exists elsewhere."
Write-Host ""

# List subdirectories:
# Get-ChildItem "I:\fred\GitRepo" -Directory | ForEach-Object {
#     $size = (Get-ChildItem $_.FullName -Recurse -File | Measure-Object Length -Sum).Sum
#     Write-Host "  $([math]::Round($size/1GB, 2)) GB — $($_.Name)"
# }

# Also check I:\fred\GitHub (9.76 GB) for overlap with GitRepo

# ─────────────────────────────────────────────────────────────────────────────
# PHASE 10: POST-CLEANUP VERIFICATION
# ─────────────────────────────────────────────────────────────────────────────
Write-Phase "PHASE 10: Post-Cleanup Verification"

$driveAfter = Get-PSDrive I
$freeAfter = [math]::Round($driveAfter.Free/1GB, 2)
$recovered = [math]::Round($freeAfter - $freeBefore, 2)

Write-Host "Free space before: $freeBefore GB"
Write-Host "Free space after:  $freeAfter GB"
Write-Host "Space recovered:   $recovered GB" -ForegroundColor Green

# ============================================================================
# CLEANUP POTENTIAL SUMMARY
# ============================================================================
Write-Phase "CLEANUP POTENTIAL SUMMARY"
Write-Host @"

  CATEGORY                          SIZE        RISK     ACTION
  ─────────────────────────────────────────────────────────────────
  Volume Shadow Copies (VSS)      ~182 GB      LOW*     Admin required
  _Duplicates folder               22.81 GB    LOW      Generate manifest first
  LLM model files                  17.93 GB    MED      Check if still needed
  ISO files                         5.42 GB    LOW      Likely not needed
  Temp/cache/bak files              1.41 GB    LOW      Safe to delete
  Recycle Bin                       0.35 GB    NONE     Safe to empty
  .omni_cache                       0.02 GB    NONE     Safe to delete
  ─────────────────────────────────────────────────────────────────
  TOTAL IMMEDIATE (safe)          ~230 GB      
  
  AFTER REVIEW:
  ZIP archives (if extracted)     ~70+ GB      MED      Verify contents first
  GitRepo (if backed up)           43.71 GB    HIGH     Verify before deleting
  
  * VSS risk is LOW if you don't need file version history on this drive.

"@
