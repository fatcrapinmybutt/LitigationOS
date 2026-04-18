# MASTER DRIVE ORGANIZATION PLAN
## LitigationOS — 6-Drive Taxonomy & Canonical Structure
### Generated: 2026-03-09 | APEX MANBEARPIG

---

## CURRENT STATE (from 6-drive forensic scan)

| Drive | Files | Size | Current Use | Health |
|-------|-------|------|-------------|--------|
| C:\ | 466K | 102.6 GB | Primary — OS + LitigationOS + case files | ⚠️ CLUTTERED |
| D:\ | 132K | 12.3 GB | Mixed — old backups, misc files | ⚠️ DISORGANIZED |
| F:\ | 83K | 9.4 GB | Mixed — code, documents, archives | ⚠️ DISORGANIZED |
| G:\ | 21K | 4.95 GB | Small — misc files | 🟡 MODERATE |
| H:\ | 37K | 4.97 GB | Partially organized (119K files reorganized) | 🟢 IMPROVING |
| I:\ | 752K | 348 GB | Massive — backup, dedup archive, slow USB | ⚠️ ARCHIVE DRIVE |

**Total: ~1.49M files, ~483 GB**

---

## TARGET STATE — DRIVE PURPOSE TAXONOMY

### C:\ — PRIMARY WORKSPACE (Active Files Only)
```
C:\Users\andre\LitigationOS\           ← System root (canonical)
  00_SYSTEM\                            ← Pipeline, engines, tools, config
  01_CASE_DATA\                         ← Active case data by lane
  01_FILINGS\                           ← Active filing drafts
  02_Court_Forms\                       ← Michigan court forms (SCAO)
  05_ANALYSIS\                          ← Analysis outputs
  10_Exhibits\                          ← Active exhibit files
  11_CODE\                              ← Product app source
  temp\                                 ← Session temp files (cleaned weekly)
  
C:\Users\andre\Desktop\
  COURT_FILING_PACKETS\                 ← 12 packets + supplementals (FILING READY)
  LitigationOS_FINAL_BACKUP_20260309\   ← Local backup copy
```
**Rule: C:\ holds ONLY active, current-version files. All archives → I:\**

### D:\ — SECONDARY WORKSPACE (Overflow + Staging)
```
D:\LitigationOS_Staging\               ← Files being processed/classified
D:\LitigationOS_Code\                  ← Code backups, dev environment
D:\LitigationOS_Imports\               ← Incoming files before classification
```
**Rule: D:\ is a staging area. Files move to C:\ (active) or I:\ (archive) within 7 days.**

### F:\ — TOOLS & REFERENCE
```
F:\LitigationOS_Tools\                 ← Software, utilities, installers
F:\LitigationOS_Reference\             ← Legal reference materials, statutes
F:\LitigationOS_Templates\             ← Form templates, document templates
```
**Rule: F:\ holds static reference material. Rarely changes.**

### G:\ — EVIDENCE VAULT (Small, Fast)
```
G:\Evidence_Vault\
  Lane_A_Custody\                       ← Custody evidence (photos, docs)
  Lane_B_Housing\                       ← Housing evidence (photos, EGLE)
  Lane_D_PPO\                           ← PPO evidence
  Lane_E_Misconduct\                    ← Judicial misconduct evidence
  Originals\                            ← SHA-256 verified originals (read-only)
```
**Rule: G:\ holds ORIGINAL evidence. Never modified. Write-protected after verification.**

### H:\ — WORKING DOCUMENTS
```
H:\Legal_Documents\                     ← Court filings, motions, briefs
H:\Transcripts\                         ← Hearing transcripts
H:\Correspondence\                      ← Attorney/court correspondence
H:\Financial_Records\                   ← Support, fees, employment
```
**Rule: H:\ holds organized legal documents. Already partially reorganized (119K files).**

### I:\ — ARCHIVE & BACKUP (Slow USB — Bulk Storage)
```
I:\APEX_MANBEARPIG_INJECT\             ← Session backups, filing packet copies
I:\DEDUP_ARCHIVE\                       ← 36,860 deduplicated files (preserved)
I:\DEDUP_GLOBAL\                        ← Future global dedup target
I:\LitigationOS_Archive\               ← Version history, old drafts
I:\LitigationOS_Backups\               ← Timestamped full backups
I:\Raw_Imports\                         ← Original unprocessed imports
```
**Rule: I:\ is write-many, read-rarely. Archive and backup ONLY. Slow USB = not for daily use.**

---

## MIGRATION PLAN (5 phases)

### Phase 1: CLASSIFY (no file moves)
- Run classifier on ALL files across all drives
- Assign each file a category: active, archive, evidence, reference, tool, junk, duplicate
- Output: `master_file_classification.csv`
- **Duration: ~2-4 hours (automated)**

### Phase 2: SAFE COPY (non-destructive)
- COPY (not move) classified files to target locations
- Verify SHA-256 of copy matches source
- Log every operation to `migration_log.csv`
- **Duration: ~8-12 hours (I:\ drive is slow)**

### Phase 3: VERIFY INTEGRITY
- SHA-256 spot-check 10% of copied files
- Verify all DB references still resolve
- Verify all filing packets intact
- Run pipeline validation
- **Duration: ~1-2 hours**

### Phase 4: ANDREW APPROVAL
- Present before/after file counts per drive
- Show any files that couldn't be classified
- Get explicit approval before removing source copies
- **This step is MANUAL — requires Andrew's review**

### Phase 5: CLEANUP SOURCE (after approval only)
- Move source copies to I:\DEDUP_ARCHIVE (NOT delete)
- Update all config/code references to new paths
- Final verification pass
- Generate DRIVE_ORGANIZATION_REPORT.md
- **Duration: ~4-8 hours**

---

## NAMING CONVENTIONS

| Pattern | Example | Rule |
|---------|---------|------|
| Case files | `2024-001507-DC_Motion_Disqualify_v3.md` | CaseNum_DocType_Version |
| Evidence | `EX_A001_Watson_Text_20240315.png` | EX_BatesNum_Subject_Date |
| Filings | `FILING_01_DISQUALIFICATION_MCR2003.md` | FILING_Num_Name |
| Backups | `BACKUP_20260309_COURT_PACKETS.zip` | BACKUP_Date_Description |
| Analysis | `ANALYSIS_Impeachment_Watson_v2.md` | ANALYSIS_Subject_Version |

---

## FILE FINDABILITY TARGET

**Goal: Any file findable in <10 seconds**

1. **By name:** Consistent naming = search by filename works
2. **By content:** FTS5 search in litigation_context.db covers all ingested text
3. **By category:** Drive taxonomy = know which drive to look on
4. **By case:** Lane structure = filter by case number
5. **By date:** ISO date prefixes enable chronological sorting

---

## RISK MITIGATION

| Risk | Mitigation |
|------|-----------|
| File loss during migration | SHA-256 verify + copy-then-verify (never move-first) |
| Broken DB references | Update all path columns in DB after migration |
| Long path failures | Enable Windows LongPathsEnabled registry key first |
| I:\ drive too slow | Run I:\ operations overnight; don't block on them |
| Accidental deletion | NO DELETIONS EVER — moves to I:\DEDUP_ARCHIVE only |
| Andrew's custom organization | Present plan for approval before Phase 2 |

---

*Andrew: Review this plan and approve/modify before execution. No files will be moved without your explicit go-ahead.*
