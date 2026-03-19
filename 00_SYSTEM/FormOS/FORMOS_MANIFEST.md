# FormOS / LitigationOS Package Manifest

**Generated:** 2026-02-28 12:35:22  
**Packages Processed:** 8  
**Total Files Extracted:** 123  
**Total Size:** 224,262,009 bytes (213.87 MB)  

---

## 1. LitigationOS_FormOS_Harvest_and_StackFactory_SUPERPIN_20260228.zip

| Field | Value |
|-------|-------|
| **Source** | `C:\Users\andre\Downloads\LitigationOS_FormOS_Harvest_and_StackFactory_SUPERPIN_20260228.zip` |
| **Extracted To** | `C:\Users\andre\LitigationOS\00_SYSTEM\FormOS\StackFactory` |
| **File Count** | 8 |
| **Total Size** | 23,445 bytes (22.9 KB) |
| **Contents** | 4 document, 2 json, 1 other, 1 python |

**Description:** FormOS StackFactory harvester and form assembly pipeline. Provides automated form stacking and batch processing for Michigan court filings.

**LitigationOS Integration:** Integrates with `00_SYSTEM/FormOS/` form generation and filing pipeline. Used by `filing_package`, `convert_filing`, and `filing_validate` JSON-RPC methods.

### Extracted Files

| File | Size | Type |
|------|------|------|
| `COPILOT_SUPERPIN_FORM_OS.md` | 3,622 bytes | document |
| `README.md` | 1,139 bytes | document |
| `config/form_os_config.example.json` | 353 bytes | json |
| `docs/FOLDER_PLANES.md` | 892 bytes | document |
| `docs/LEGAL_NOTE.md` | 338 bytes | document |
| `manifest.json` | 1,225 bytes | json |
| `tooling/form_os_orchestrator.py` | 13,389 bytes | python |
| `tooling/schema.sql` | 2,487 bytes | other |

---

## 2. LitigationOS_FormOS_Upgrade_v2plus_20260228.zip

| Field | Value |
|-------|-------|
| **Source** | `C:\Users\andre\Downloads\LitigationOS_FormOS_Upgrade_v2plus_20260228.zip` |
| **Extracted To** | `C:\Users\andre\LitigationOS\00_SYSTEM\FormOS\v2plus` |
| **File Count** | 12 |
| **Total Size** | 55,697 bytes (54.39 KB) |
| **Contents** | 5 python, 3 document, 2 json, 1 config, 1 other |

**Description:** FormOS v2+ upgrade package with enhanced form templates, validation rules, and Michigan court compliance checks.

**LitigationOS Integration:** Integrates with `00_SYSTEM/FormOS/` form generation and filing pipeline. Used by `filing_package`, `convert_filing`, and `filing_validate` JSON-RPC methods.

### Extracted Files

| File | Size | Type |
|------|------|------|
| `README.md` | 2,749 bytes | document |
| `config/formos_config.example.json` | 511 bytes | json |
| `docs/AUDIT_NOTES.md` | 1,060 bytes | document |
| `docs/FOLDER_PLANES_v2.md` | 985 bytes | document |
| `manifest.json` | 2,003 bytes | json |
| `rules/mi_rulebank.yaml` | 1,420 bytes | config |
| `tooling/build_cyclepack.py` | 2,100 bytes | python |
| `tooling/export_neo4j_from_formos_db.py` | 2,981 bytes | python |
| `tooling/formos_cli.py` | 31,604 bytes | python |
| `tooling/mifile_lint.py` | 4,620 bytes | python |
| `tooling/pdf_fieldmap_extract.py` | 2,605 bytes | python |
| `tooling/schema_v2.sql` | 3,059 bytes | other |

---

## 3. LitigationOS_FormOS_Upgrade_v2_20260228.zip

| Field | Value |
|-------|-------|
| **Source** | `C:\Users\andre\Downloads\LitigationOS_FormOS_Upgrade_v2_20260228.zip` |
| **Extracted To** | `C:\Users\andre\LitigationOS\00_SYSTEM\FormOS\v2` |
| **File Count** | 8 |
| **Total Size** | 42,318 bytes (41.33 KB) |
| **Contents** | 3 document, 2 json, 1 config, 1 other, 1 python |

**Description:** FormOS v2 base upgrade package with core form templates and filing infrastructure for Michigan courts.

**LitigationOS Integration:** Integrates with `00_SYSTEM/FormOS/` form generation and filing pipeline. Used by `filing_package`, `convert_filing`, and `filing_validate` JSON-RPC methods.

### Extracted Files

| File | Size | Type |
|------|------|------|
| `README.md` | 2,485 bytes | document |
| `config/formos_config.example.json` | 511 bytes | json |
| `docs/AUDIT_NOTES.md` | 1,060 bytes | document |
| `docs/FOLDER_PLANES_v2.md` | 985 bytes | document |
| `manifest.json` | 1,194 bytes | json |
| `rules/mi_rulebank.yaml` | 1,420 bytes | config |
| `tooling/formos_cli.py` | 31,604 bytes | python |
| `tooling/schema_v2.sql` | 3,059 bytes | other |

---

## 4. MI_LitigationOS_ClerkStacks_Pack_20260228.zip

| Field | Value |
|-------|-------|
| **Source** | `C:\Users\andre\Downloads\MI_LitigationOS_ClerkStacks_Pack_20260228.zip` |
| **Extracted To** | `C:\Users\andre\LitigationOS\00_SYSTEM\FormOS\ClerkStacks` |
| **File Count** | 11 |
| **Total Size** | 39,098 bytes (38.18 KB) |
| **Contents** | 3 json, 3 xml, 2 document, 2 config, 1 python |

**Description:** Michigan court clerk filing stack templates. Pre-configured packages for common Michigan court clerk operations and filing requirements.

**LitigationOS Integration:** Integrates with `00_SYSTEM/FormOS/` form generation and filing pipeline. Used by `filing_package`, `convert_filing`, and `filing_validate` JSON-RPC methods.

### Extracted Files

| File | Size | Type |
|------|------|------|
| `MI_LitigationOS_ClerkStacks_Pack_20260228/README.md` | 1,802 bytes | document |
| `MI_LitigationOS_ClerkStacks_Pack_20260228/lint/mcr_timing_rules.yaml` | 782 bytes | config |
| `MI_LitigationOS_ClerkStacks_Pack_20260228/lint/mifile_lint_rules.yaml` | 1,964 bytes | config |
| `MI_LitigationOS_ClerkStacks_Pack_20260228/manifests/examples/manifest_example_foc65.json` | 3,681 bytes | json |
| `MI_LitigationOS_ClerkStacks_Pack_20260228/report/MI_ClerkStacks_Report_v2026-02-28.md` | 8,478 bytes | document |
| `MI_LitigationOS_ClerkStacks_Pack_20260228/schemas/litigationos.mi_manifest.schema.json` | 6,595 bytes | json |
| `MI_LitigationOS_ClerkStacks_Pack_20260228/schemas/litigationos.mi_motion_min.schema.json` | 3,074 bytes | json |
| `MI_LitigationOS_ClerkStacks_Pack_20260228/templates/akn/foc65_motion_parenting_time.xml` | 3,041 bytes | xml |
| `MI_LitigationOS_ClerkStacks_Pack_20260228/templates/akn/foc87_motion_custody.xml` | 2,255 bytes | xml |
| `MI_LitigationOS_ClerkStacks_Pack_20260228/templates/akn/mcr2003_motion_disqualify.xml` | 2,290 bytes | xml |
| `MI_LitigationOS_ClerkStacks_Pack_20260228/tooling/build_clerkstack_bundle.py` | 5,136 bytes | python |

---

## 5. MI_AkomaNtoso_FormFactory_DeepResearch_Pack_20260228.zip

| Field | Value |
|-------|-------|
| **Source** | `C:\Users\andre\Downloads\MI_AkomaNtoso_FormFactory_DeepResearch_Pack_20260228.zip` |
| **Extracted To** | `C:\Users\andre\LitigationOS\00_SYSTEM\FormOS\AkomaNtoso` |
| **File Count** | 9 |
| **Total Size** | 26,878 bytes (26.25 KB) |
| **Contents** | 3 document, 3 json, 2 xml, 1 config |

**Description:** Akoma Ntoso XML-based legal document standards. Deep research pack for structured legal document interchange format used in legislative/judicial systems.

**LitigationOS Integration:** Integrates with `00_SYSTEM/FormOS/` form generation and filing pipeline. Used by `filing_package`, `convert_filing`, and `filing_validate` JSON-RPC methods.

### Extracted Files

| File | Size | Type |
|------|------|------|
| `MI_COMPOSITION_REQUIREMENTS_RULEBANK.md` | 1,948 bytes | document |
| `MI_COMPOSITION_REQUIREMENTS_RULEBANK.yaml` | 2,514 bytes | config |
| `README.md` | 1,893 bytes | document |
| `SUPERPIN_AKN_MI_ALL_FORMS.md` | 6,339 bytes | document |
| `manifest.json` | 1,477 bytes | json |
| `schemas/form_profile.schema.json` | 1,503 bytes | json |
| `seeds/akn_templates/COA_appellant_brief_seed.xml` | 2,301 bytes | xml |
| `seeds/akn_templates/FOC65_motion_parenting_time_seed.xml` | 3,239 bytes | xml |
| `seeds/form_profiles_seed.jsonl` | 5,664 bytes | json |

---

## 6. 20260224_MEEK234_HIGHSIGNAL_DB_CATALOGUE_DELTA9999_PLUS.zip

| Field | Value |
|-------|-------|
| **Source** | `C:\Users\andre\Downloads\20260224_MEEK234_HIGHSIGNAL_DB_CATALOGUE_DELTA9999_PLUS.zip` |
| **Extracted To** | `C:\Users\andre\LitigationOS\00_SYSTEM\MEEK234\HIGHSIGNAL` |
| **File Count** | 20 |
| **Total Size** | 152,100,581 bytes (148535.72 KB) |
| **Contents** | 14 data, 4 document, 1 json, 1 database |

**Description:** MEEK234 high-signal database catalogue delta. Contains curated high-relevance evidence entries, DB catalogue updates, and signal-filtered litigation intelligence.

**LitigationOS Integration:** Feeds into `00_SYSTEM/MEEK234/` intelligence pipeline. Supports `evidence_quotes`, `contradiction_map`, and `impeachment_items` DB tables.

### Extracted Files

| File | Size | Type |
|------|------|------|
| `AUTHORITY_CATALOGUE_OFFICIAL_LINKS.csv` | 2,146 bytes | data |
| `CHRONO_HEATMAP_MONTH_LANE.csv` | 2,978 bytes | data |
| `HIGHSIGNAL_QUOTES_TOP500.csv` | 2,117,734 bytes | data |
| `HIGHSIGNAL_QUOTES_UNIFIED_DEDUP.csv` | 31,122,020 bytes | data |
| `HIGHSIGNAL_QUOTES_UNIFIED_RAW.csv` | 68,112,439 bytes | data |
| `HYPERPIN_PROMPT_MEEK234_DB_CATALOGUE_DELTA9999.txt` | 1,285 bytes | document |
| `LANE_TOPIC_COUNTS.csv` | 1,320 bytes | data |
| `MANIFEST.json` | 2,751 bytes | json |
| `MCNEILL_RUSCO_MARTINI_USB_HEALTHWEST_FOCUSED_TOP300.csv` | 1,288,128 bytes | data |
| `MEEK234_HIGHSIGNAL_DATABASE_CATALOGUE.md` | 61,281 bytes | document |
| `MEEK234_HIGHSIGNAL_DB.sqlite` | 41,979,904 bytes | database |
| `MEEK2_HIGHSIGNAL_TOP500.csv` | 2,162,293 bytes | data |
| `MEEK3_HIGHSIGNAL_TOP500.csv` | 1,927,147 bytes | data |
| `MEEK4_HIGHSIGNAL_TOP500.csv` | 1,570,236 bytes | data |
| `MEMO_ANCHOR_INDEX_MCNEILL_USB_RUSCO_MARTINI.csv` | 87,146 bytes | data |
| `README_START_HERE.txt` | 291 bytes | document |
| `RUNLOG.txt` | 181 bytes | document |
| `SOURCE_HEATMAP_COUNTS.csv` | 29,908 bytes | data |
| `SOURCE_INVENTORY_EXTRACTION_STATUS.csv` | 66,828 bytes | data |
| `TOPIC_CATALOGUE_INDEX.csv` | 1,564,565 bytes | data |

---

## 7. 20260224_MEEK234_QUOTELOCK_REBUTTAL_OBJECTION_GRAFT_DELTA9999_CONTINUATION.zip

| Field | Value |
|-------|-------|
| **Source** | `C:\Users\andre\Downloads\20260224_MEEK234_QUOTELOCK_REBUTTAL_OBJECTION_GRAFT_DELTA9999_CONTINUATION.zip` |
| **Extracted To** | `C:\Users\andre\LitigationOS\00_SYSTEM\MEEK234\QUOTELOCK` |
| **File Count** | 18 |
| **Total Size** | 71,453,172 bytes (69778.49 KB) |
| **Contents** | 12 document, 5 data, 1 json |

**Description:** MEEK234 QuoteLock rebuttal/objection graft continuation. Contains locked evidence quotes, rebuttal frameworks, and objection templates for litigation use.

**LitigationOS Integration:** Feeds into `00_SYSTEM/MEEK234/` intelligence pipeline. Supports `evidence_quotes`, `contradiction_map`, and `impeachment_items` DB tables.

### Extracted Files

| File | Size | Type |
|------|------|------|
| `AUTHORITY_WEB_CITATION_GRAFT.md` | 1,088 bytes | document |
| `CHRONO_NEGATIVE_LINES_INDEX.csv` | 8,014,768 bytes | data |
| `MANIFEST.json` | 9,508 bytes | json |
| `MEEK234_FILING_GRAFT_SHELLS_QUOTELOCK.md` | 1,960 bytes | document |
| `MEEK2_FINAL_EXHIBIT_GRADE_DROPINS.md` | 232,905 bytes | document |
| `MEEK2_PRIMARY_SOURCE_DROPINS.md` | 142,534 bytes | document |
| `MEEK3_FINAL_EXHIBIT_GRADE_DROPINS.md` | 225,940 bytes | document |
| `MEEK3_PRIMARY_SOURCE_DROPINS.md` | 145,366 bytes | document |
| `MEEK4_FINAL_EXHIBIT_GRADE_DROPINS.md` | 322,706 bytes | document |
| `MEEK4_PRIMARY_SOURCE_DROPINS.md` | 218,751 bytes | document |
| `MEEK4_RUSCO_MARTINI_USB_MCNEILL_QUOTELOCK_CURATED.md` | 426,432 bytes | document |
| `PRIMARY_ONLY_MEEK234_ALL_CASESPECIFIC_FULLQUOTE_GRAFT.md` | 2,988,550 bytes | document |
| `PRIMARY_ONLY_MEEK4_CURATED_MCNEILL_RUSCO_MARTINI_USB.md` | 339,447 bytes | document |
| `PRIMARY_ONLY_QUOTELOCK_MATRIX_ALL.csv` | 4,479,976 bytes | data |
| `PRIMARY_ONLY_QUOTELOCK_MATRIX_CASESPECIFIC.csv` | 3,440,830 bytes | data |
| `QUOTELOCK_REBUTTAL_OBJECTION_MATRIX_ALL.csv` | 25,781,596 bytes | data |
| `QUOTELOCK_REBUTTAL_OBJECTION_MATRIX_CASESPECIFIC.csv` | 24,674,477 bytes | data |
| `RUNLOG.txt` | 6,338 bytes | document |

---

## 8. buncha txt documents newnewnew.zip

| Field | Value |
|-------|-------|
| **Source** | `C:\Users\andre\Downloads\buncha txt documents newnewnew.zip` |
| **Extracted To** | `C:\Users\andre\LitigationOS\03_EVIDENCE\FROM_DOWNLOADS\buncha_txt` |
| **File Count** | 37 |
| **Total Size** | 520,820 bytes (508.61 KB) |
| **Contents** | 37 document |

**Description:** Collection of text documents from downloads. Raw evidence/reference materials to be catalogued and integrated into the evidence pipeline.

**LitigationOS Integration:** Raw evidence intake for `03_EVIDENCE/`. Candidates for ingestion via `scan_ingest` and `classify_doc` methods into `evidence_quotes` and `documents` tables.

### Extracted Files

| File | Size | Type |
|------|------|------|
| `# GPT Execution Agent – Master Inst.txt` | 8,049 bytes | document |
| `# Litigation OS – Custody  Best-Int.txt` | 4,156 bytes | document |
| `#2 reassignment of JUDGE.txt` | 15,491 bytes | document |
| `2. JTC FORMAL COMPLAINT (READY TO F.txt` | 5,448 bytes | document |
| `25255226txt.txt` | 0 bytes | document |
| `4. PPO Trial-Court Packet (No Custo.txt` | 6,693 bytes | document |
| `ADDENDUM REQUEST FOR APPOINTMENT OF.txt` | 30,256 bytes | document |
| `APPELLANT’S MOTION FOR IMMEDIATE CONSIDERATION.txt` | 14,295 bytes | document |
| `ARGUMENT.txt` | 9,746 bytes | document |
| `ARGUMENT2.txt` | 56,371 bytes | document |
| `All set. Your one-bundle pack (orch.txt` | 1,573 bytes | document |
| `Alright, here’s how we handle this.txt` | 28,835 bytes | document |
| `Below are the two things you asked.txt` | 22,643 bytes | document |
| `Brief on appeal RECUSAL.txt` | 18,789 bytes | document |
| `COA BRIEF add to JTC MSC petitions.txt` | 13,039 bytes | document |
| `DISMISS SHOWCAUSE #7.txt` | 11,629 bytes | document |
| `FLITIGATION_OS_vNextplaybooksHousin.txt` | 8,096 bytes | document |
| `Here’s how I’d deploy that argument.txt` | 32,470 bytes | document |
| `Motion for Immediate Consideration.txt` | 358 bytes | document |
| `PETITION FOR SUPERINTENDING CONTROL.txt` | 14,318 bytes | document |
| `PLAINTIFF APPELLANTS BRIEF ON APPEAL.txt` | 24,973 bytes | document |
| `PLAINTIFF_RESPONDENT’S MOTION TO CONSOLIDATE_ COORDINATE,.txt` | 3,376 bytes | document |
| `PLAINTIFF–APPELLANT’S BRIEF ON APPEAL.txt` | 9,562 bytes | document |
| `PPO CUSTODY CONSOLIDATION.txt` | 3,093 bytes | document |
| `PPO SHOW CAUSE #7 draft.txt` | 6,274 bytes | document |
| `SAFE HARBOR MOTION PROPOSED ORDER.txt` | 2,599 bytes | document |
| `THEME  DOCUMENT  SOURCE  DATE D.txt` | 2,376 bytes | document |
| `THIS ALL WORKED.txt` | 23,630 bytes | document |
| `There is also the recording of her.txt` | 1,814 bytes | document |
| `To combine your Litigation OS autom.txt` | 3,183 bytes | document |
| `Untitled.txt` | 0 bytes | document |
| `VERIFIED JUDICIAL MISCONDUCT COMPLAINT2.txt` | 2,405 bytes | document |
| `VERIFIED JUDICIAL MISCONDUCT COMPLAINT3.txt` | 23,266 bytes | document |
| `You are a Michigan litigation mainf.txt` | 3,223 bytes | document |
| `jtccoa.txt` | 39,208 bytes | document |
| `jtccoa1.txt` | 35,155 bytes | document |
| `jtccoa2.txt` | 34,428 bytes | document |

---

## LitigationOS Infrastructure Map

```
00_SYSTEM/
  FormOS/
    StackFactory/    <- Package #1: Harvest + StackFactory SUPERPIN
    v2plus/          <- Package #2: FormOS v2+ Upgrade
    v2/              <- Package #3: FormOS v2 Base
    ClerkStacks/     <- Package #4: MI Clerk Stacks
    AkomaNtoso/      <- Package #5: Akoma Ntoso Deep Research
    FORMOS_MANIFEST.md  <- This file
  MEEK234/
    HIGHSIGNAL/      <- Package #6: DB Catalogue Delta
    QUOTELOCK/       <- Package #7: Rebuttal/Objection Graft
03_EVIDENCE/
  FROM_DOWNLOADS/
    buncha_txt/      <- Package #8: Text Documents
```
