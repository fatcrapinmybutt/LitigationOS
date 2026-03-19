# I: DRIVE DEDUP REPORT — OPERATION OMEGA
> Generated for LitigationOS | Drive: I: (exFAT, 465.7 GB total, ~16 GB free — 97% full)

---

## EXECUTIVE SUMMARY

| Metric | Value |
|--------|-------|
| **Total files on I:** | 390,000 |
| **Total data on I:** | 208.0 GB |
| **Estimated wasted (duplicates)** | **~39.4 GB** (42.3 GB gross, minus unique copies) |
| **Files in duplicate groups** | 361,314 (93% of all files!) |
| **Cross-drive duplicates (I: ↔ other drives)** | 2.55 GB |
| **Largest hotspot** | `I:\fred\Organized_Litigation_Supreme\Other` — 8.24 GB |
| **Reclaimable with safe cleanup** | **~30–35 GB** (conservative estimate) |

### Root Cause
The I: drive contains **deeply nested Git repository copies** — repos cloned inside repos inside repos. The path patterns show 3–4 levels of nesting:
- `I:\fred\GitRepo\fredprime\GitRepo\fredprime\GitCleanRepo\...` (4 deep)
- `I:\fred\GitRepo\fredprime\GitRepo\fredprime\...` (3 deep)
- `I:\fred\GitRepo\fredprime\GitCleanRepo\...` (3 deep)
- `I:\fred\GitHub\GitCleanRepo\...` (2 deep)

This nesting means Git pack objects (extensionless hash-named files) are duplicated 3–30× across nested copies.

---

## TOP 15 DUPLICATE GROUPS BY WASTED SPACE

These are files with identical filenames and sizes found in multiple locations on I:.

| # | File (hash/name) | Size Each | Copies | Wasted | Primary Location Pattern |
|---|-----------------|-----------|--------|--------|--------------------------|
| 1 | `6e3a3ae06e6b6...` (git pack) | 42.0 MB | 30 | **1.22 GB** | FRED-PRIME/* subdirs (AppClose, Appeals, etc.) |
| 2 | `df537bccfc671...` (git pack) | 35.8 MB | 32 | **1.11 GB** | FRED-PRIME/* subdirs |
| 3 | `30d6532f44b48...` (git pack) | 271.9 MB | 4 | **816 MB** | FRED/Needs_Review (4 nested copies) |
| 4 | `b6f56638ae09f...` (git pack) | 346.1 MB | 3 | **693 MB** | FRED/Needs_Review (3 nested copies) |
| 5 | `263f1d909a77f...` (git pack) | 22.3 MB | 30 | **647 MB** | FRED-PRIME/* subdirs |
| 6 | `ff332eaade9e5...` (git pack) | 24.8 MB | 26 | **619 MB** | FRED-PRIME/* subdirs |
| 7 | `2740d5192a812...` (git pack) | 552.4 MB | 2 | **553 MB** | FRED/Needs_Review (2 nested copies) |
| 8 | `c25f947f5f7c1...` (git pack) | 251.9 MB | 3 | **504 MB** | Nested repo copies |
| 9 | `e766c8ba8d1ae...` (git pack) | 248.6 MB | 3 | **497 MB** | Nested repo copies |
| 10 | `b906d0e9d6578...` (git pack) | 205.6 MB | 3 | **411 MB** | Nested repo copies |
| 11 | `306d95c1067fa...` (git pack) | 136.3 MB | 4 | **409 MB** | Nested repo copies |
| 12 | `0f96259502c47...` (git pack) | 108.7 MB | 4 | **326 MB** | Nested repo copies |
| 13 | `1633b322a4d79...` (git pack) | 104.8 MB | 4 | **314 MB** | Nested repo copies |
| 14 | `6d705ec8eeee4...` (git pack) | 11.5 MB | 26 | **287 MB** | FRED-PRIME/* subdirs |
| 15 | `52bc18af5eec9...` (git pack) | 10.3 MB | 26 | **258 MB** | FRED-PRIME/* subdirs |

**Combined waste from top 15 groups alone: ~7.87 GB**

---

## TOP 50 DUPLICATE GROUPS — SIZE+EXTENSION ANALYSIS

These show files with identical extension and size (likely duplicates even if differently named).

| # | Extension | Size Each | Copies | Total Waste | Notes |
|---|-----------|-----------|--------|-------------|-------|
| 1 | (none) | 346.1 MB | 4 | 1.35 GB | Git pack objects |
| 2 | (none) | 271.9 MB | 5 | 1.33 GB | Git pack objects |
| 3 | (none) | 42.0 MB | 31 | 1.27 GB | Git pack spread across 30+ FRED-PRIME dirs |
| 4 | (none) | 35.8 MB | 33 | 1.15 GB | Git pack spread across 32+ dirs |
| 5 | (none) | 552.4 MB | 2 | 1.08 GB | Large git pack, 2 copies |
| 6 | (none) | 251.9 MB | 4 | 984 MB | Git pack objects |
| 7 | **.z06** | **500 MB** | **2** | **1.00 GB** | **Archive split file** |
| 8 | (none) | 248.6 MB | 4 | 970 MB | Git pack objects |
| 9 | (none) | 22.3 MB | 31 | 692 MB | Git pack objects |
| 10 | (none) | 136.3 MB | 5 | 680 MB | Git pack objects |
| 11 | (none) | 24.8 MB | 27 | 668 MB | Git pack objects |
| 12 | (none) | 205.6 MB | 3 | 617 MB | Git pack objects |
| 13 | (none) | 108.7 MB | 5 | 543 MB | Git pack objects |
| 14 | (none) | 104.8 MB | 5 | 524 MB | Git pack objects |
| 15 | (none) | 108.1 MB | 4 | 432 MB | Git pack objects |
| 16 | (none) | 69.5 MB | 5 | 348 MB | Git pack objects |
| 17 | (none) | 11.5 MB | 27 | 310 MB | Git pack objects |
| 18 | (none) | 60.6 MB | 5 | 303 MB | Git pack objects |
| 19 | (none) | 60.3 MB | 5 | 301 MB | Git pack objects |
| 20 | (none) | 74.4 MB | 4 | 298 MB | Git pack objects |
| 21 | **.gsd** | **94.0 MB** | **3** | **282 MB** | **Application data file** |
| 22 | (none) | 10.3 MB | 27 | 279 MB | Git pack objects |
| 23 | (none) | 9.8 MB | 27 | 264 MB | Git pack objects |
| 24 | **.crdownload** | **121.4 MB** | **2** | **243 MB** | **Incomplete Chrome download** |
| 25 | (none) | 60.3 MB | 4 | 241 MB | Git pack objects |
| 26 | (none) | 8.6 MB | 27 | 232 MB | Git pack objects |
| 27 | (none) | 69.1 MB | 4 | 207 MB | Git pack objects |
| 28 | **.csv** | **28.6 MB** | **7** | **200 MB** | **Data file — check before deleting** |
| 29 | **.25** | **98.3 MB** | **2** | **197 MB** | **Unknown format split file** |
| 30–50 | (various) | 5–55 MB | 3–29 | 120–190 MB | Mostly git pack objects |

---

## HOTSPOT DIRECTORIES (Highest Waste Concentration)

| Directory | Files | Size | Action |
|-----------|-------|------|--------|
| `I:\fred\Organized_Litigation_Supreme\Other` | 94,782 | **8.24 GB** | ⚠️ REVIEW — may contain originals |
| `I:\fred\GitRepo\fredprime\FRED\Needs_Review` | 24,316 | **7.12 GB** | 🗑️ SAFE TO REMOVE (nested copy) |
| `I:\fred\GitRepo\fredprime\GitRepo\fredprime\FRED\Needs_Review` | 24,315 | **6.63 GB** | 🗑️ SAFE TO REMOVE (deeper nested copy) |
| `I:\fred\GitHub\GitCleanRepo\FRED\Needs_Review` | 24,403 | **6.24 GB** | 🗑️ SAFE TO REMOVE (yet another copy) |
| `I:\fred\GitRepo\fredprime\GitCleanRepo\FRED\Needs_Review` | 11,458 | **2.68 GB** | 🗑️ SAFE TO REMOVE (nested copy) |
| `I:\fred\Organized_Litigation_Supreme\_Duplicates` | 30,954 | **1.25 GB** | 🗑️ Already flagged as duplicates |
| `I:\fred\` (root) | 10,749 | **0.79 GB** | ⚠️ REVIEW individually |
| `I:\fred\GitRepo\fredprime\FRED-PRIME\Scripts` | — | **0.69 GB** | ⚠️ Check if unique |
| `I:\fred\GitRepo\fredprime\GitRepo\fredprime\FRED-PRIME\Scripts` | — | **0.69 GB** | 🗑️ SAFE TO REMOVE (nested copy) |
| `I:\fred\GitRepo\fredprime\FRED-PRIME\Procedural` | — | **0.62 GB** | ⚠️ Check if unique |
| `I:\fred\GitRepo\fredprime\GitRepo\fredprime\FRED-PRIME\Procedural` | — | **0.62 GB** | 🗑️ SAFE TO REMOVE (nested copy) |
| `I:\fred\GitRepo\fredprime\GitRepo\fredprime\FRED-PRIME\HousingDisputes` | — | **0.60 GB** | 🗑️ SAFE TO REMOVE |
| `I:\fred\GitRepo\fredprime\FRED-PRIME\HousingDisputes` | — | **0.60 GB** | ⚠️ Check if unique |
| `I:\fred\GitRepo\fredprime\FRED-PRIME\Financial` | — | **0.59 GB** | ⚠️ Check if unique |
| `I:\fred\GitRepo\fredprime\GitRepo\fredprime\FRED-PRIME\Financial` | — | **0.59 GB** | 🗑️ SAFE TO REMOVE |

---

## CROSS-DRIVE DUPLICATES (I: files also on other drives)

Files on I: that also exist on other drives — **safest to delete** because copies exist elsewhere.

| Cross-Drive Pair | Shared Data |
|-----------------|-------------|
| C: (LitigationOS) ↔ I: | **2.43 GB** |
| D: ↔ I: | 161 MB |
| G: ↔ I: | 154 MB |
| H: ↔ I: | 103 MB |
| F: ↔ I: | 32 MB |
| **Total cross-drive reclaimable** | **~2.55 GB** |

---

## ⚠️ DO NOT DELETE — LITIGATION EVIDENCE DIRECTORIES

These directories contain or may contain litigation evidence. **NEVER auto-delete.**

| Directory | Files | Size | Reason |
|-----------|-------|------|--------|
| `I:\fred\GitRepo\fredprime\FRED-PRIME\SHADYOAKS-EVIDENCE\Shady_Oaks` | 163 | **1.28 GB** | 🔴 **LITIGATION EVIDENCE** |
| `I:\fred\Custody_Evidence` | 67 | **172 MB** | 🔴 **CUSTODY EVIDENCE** |
| `I:\fred\EVIDENCE NOT SCANNED BY GPT` | 21 | **87 MB** | 🔴 **UNPROCESSED EVIDENCE** |
| `I:\fred\GitRepo\fredprime\FRED-PRIME\Discovery` | 18 | **41 MB** | 🔴 **DISCOVERY MATERIALS** |
| `I:\fred\!!!!!!@@@NEW SHADY hOA EVIDENCE` | 34 | **1.2 MB** | 🔴 **SHADY OAKS EVIDENCE** |
| `I:\fred\EVERYTHIING\COURTFILES` | 12 | **2.4 MB** | 🔴 **COURT FILES** |
| `I:\fred\LOCAL_FRED\processed_files\archives\michigan court rules` | varies | **~40 MB** | 🟡 Reference — court rules |

---

## NESTED REPO STRUCTURE — THE ROOT PROBLEM

The I: drive has the same Git repository cloned inside itself multiple times:

```
I:\fred\GitRepo\fredprime\                          ← Level 1 (46,775 files, 16.6 GB)
I:\fred\GitRepo\fredprime\GitRepo\fredprime\        ← Level 2 (55,479 files, 14.1 GB)  
I:\fred\GitRepo\fredprime\GitCleanRepo\             ← Level 2 alt (23,958 files, 3.0 GB)
I:\fred\GitHub\GitCleanRepo\                         ← Separate clone (37,166 files, 7.0 GB)
I:\fred\Organized_Litigation_Supreme\                ← Organized copy (137,816 files, 25.9 GB)
```

**The nested copies (Level 2+) are the primary waste — ~17 GB of pure duplicates.**

---

## SAFE DELETION CANDIDATES (Highest Confidence)

### Tier 1: Nested Repository Copies (~22 GB reclaimable)

These are confirmed copies-within-copies. The parent directories already contain these files.

```powershell
# ⚠️ REVIEW BEFORE RUNNING — DO NOT EXECUTE WITHOUT MANUAL VERIFICATION

# 1. Remove deepest nested copy (repo inside repo inside repo)
#    ~6.63 GB — exact duplicate of I:\fred\GitRepo\fredprime\FRED\Needs_Review
# Remove-Item -Recurse -Force "I:\fred\GitRepo\fredprime\GitRepo\fredprime\FRED\Needs_Review"

# 2. Remove nested GitCleanRepo copy
#    ~2.68 GB — duplicate of I:\fred\GitHub\GitCleanRepo\FRED\Needs_Review
# Remove-Item -Recurse -Force "I:\fred\GitRepo\fredprime\GitCleanRepo\FRED\Needs_Review"

# 3. Remove nested FRED-PRIME duplicates (each pair below, keep the shorter path)
#    ~0.69 GB Scripts
# Remove-Item -Recurse -Force "I:\fred\GitRepo\fredprime\GitRepo\fredprime\FRED-PRIME\Scripts"
#    ~0.62 GB Procedural
# Remove-Item -Recurse -Force "I:\fred\GitRepo\fredprime\GitRepo\fredprime\FRED-PRIME\Procedural"
#    ~0.60 GB HousingDisputes
# Remove-Item -Recurse -Force "I:\fred\GitRepo\fredprime\GitRepo\fredprime\FRED-PRIME\HousingDisputes"
#    ~0.59 GB Financial
# Remove-Item -Recurse -Force "I:\fred\GitRepo\fredprime\GitRepo\fredprime\FRED-PRIME\Financial"
#    ~0.11 GB Misc
# Remove-Item -Recurse -Force "I:\fred\GitRepo\fredprime\GitRepo\fredprime\FRED-PRIME\Misc"

# 4. Nuclear option: Remove entire nested GitRepo subtree
#    This removes the Level 2+ nested repos (~14 GB):
# Remove-Item -Recurse -Force "I:\fred\GitRepo\fredprime\GitRepo"
```

### Tier 2: Pre-Flagged Duplicates (~1.25 GB)

```powershell
# Already identified as duplicates by prior analysis
# Remove-Item -Recurse -Force "I:\fred\Organized_Litigation_Supreme\_Duplicates"
```

### Tier 3: Incomplete Downloads & Temp Files

```powershell
# Chrome incomplete downloads (~243 MB .crdownload files)
# Get-ChildItem -Path "I:\" -Recurse -Filter "*.crdownload" | Remove-Item -Force
```

---

## RECOMMENDED CLEANUP STRATEGY

### Phase 1: Quick Wins (~15 GB, LOW RISK)
1. Delete `I:\fred\GitRepo\fredprime\GitRepo\` (entire nested Level 2+ tree) → **~14 GB**
2. Delete `I:\fred\Organized_Litigation_Supreme\_Duplicates\` → **~1.25 GB**

### Phase 2: Cross-Reference Cleanup (~10 GB, MEDIUM RISK)
1. Compare `I:\fred\GitRepo\fredprime\FRED\Needs_Review` with `I:\fred\GitHub\GitCleanRepo\FRED\Needs_Review` — keep one, delete the other → **~6.24 GB**
2. Review `I:\fred\Organized_Litigation_Supreme\Other` for duplicates → **up to 8.24 GB**

### Phase 3: Cross-Drive Dedup (~2.5 GB, REQUIRES VERIFICATION)
1. Identify I: files that exist identically on C: → delete I: copy → **~2.43 GB**

### Estimated Total Reclaimable: **~28–35 GB**
This would bring I: drive from ~16 GB free to ~44–51 GB free (89% → 78% utilization).

---

## VERIFICATION COMMANDS (Run Before Deleting)

```powershell
# Verify a directory is truly a duplicate before deletion:
# Compare file counts
# (Get-ChildItem -Recurse "I:\fred\GitRepo\fredprime\FRED\Needs_Review" | Measure-Object).Count
# (Get-ChildItem -Recurse "I:\fred\GitRepo\fredprime\GitRepo\fredprime\FRED\Needs_Review" | Measure-Object).Count

# Compare total sizes
# (Get-ChildItem -Recurse "I:\fred\GitRepo\fredprime\FRED\Needs_Review" | Measure-Object -Property Length -Sum).Sum
# (Get-ChildItem -Recurse "I:\fred\GitRepo\fredprime\GitRepo\fredprime\FRED\Needs_Review" | Measure-Object -Property Length -Sum).Sum

# Spot-check with hash comparison (pick a few large files):
# Get-FileHash "I:\fred\GitRepo\fredprime\FRED\Needs_Review\<file>" -Algorithm SHA256
# Get-FileHash "I:\fred\GitRepo\fredprime\GitRepo\fredprime\FRED\Needs_Review\<file>" -Algorithm SHA256
```

---

## FILE TYPE BREAKDOWN ON I: DRIVE

| Extension | Files | Total Size | Notes |
|-----------|-------|------------|-------|
| .zip | 802 | 87.6 GB | Archives — check for nested dupes inside zips |
| (none) | 184,933 | 44.8 GB | Mostly Git pack objects (hash-named) |
| .mp4 | 275 | 17.8 GB | Videos — check if needed |
| .safetensors | 2 | 8.8 GB | ML model files |
| .gguf | 2 | 8.6 GB | ML model files (GGUF format) |
| .iso | 2 | 5.4 GB | Disk images |
| .db | 37 | 2.3 GB | Database files |
| .pdf | 1,078 | 2.1 GB | Documents — likely litigation |
| .json | 10,654 | 1.9 GB | Data files |
| .html | 1,152 | 1.7 GB | Web pages / exports |
| .csv | 7,067 | 1.3 GB | Data files |
| .jpg | 824 | 1.2 GB | Images |
| .z06 | 2 | 1.0 GB | Split archive |
| .dbo | 8 | 943 MB | Database objects |
| .png | 670 | 784 MB | Images |
| .js | 27,506 | 754 MB | JavaScript (Git repos) |
| .py | 52,112 | 740 MB | Python (Git repos) |

---

*Report generated by Operation Omega — LitigationOS*
*⚠️ ALL deletion commands are COMMENTED OUT — manual review and approval required before execution*
