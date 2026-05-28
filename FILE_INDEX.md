# FILE INDEX: LITIGATIONOS

**DOCUMENT ID:** FILE_INDEX_LITIGATIONOS_V1.0.0
**VERSION:** 1.0.0
**LAST UPDATED:** 2026-05-28
**CLASSIFICATION:** PRIVILEGED AND CONFIDENTIAL

## OVERVIEW

Complete index of all files in the LitigationOS system.

## SYSTEM-LEVEL FILES

- TRACK_DEFINITIONS.json: Master track definitions
- DESIGN_SYSTEM.md: Design system documentation
- CROSS_REFERENCE_LOG.json: All cross-track references
- FILE_INDEX.md: This file
- master_control.py: Master orchestration script

## TRACK-SPECIFIC FILES

### TRACK 1: HOUSING_LANDLORD_TENANT
- TENANT_FILE.json
- EVIDENCE_INVENTORY.json
- LEGAL_AUTHORITIES.json

### TRACK 2: CUSTODY_PARENTING_TIME
- LEGAL_ENCYCLOPEDIA.json
- RECURSIVE_BIBLE.md
- ENCYCLOPEDIA_MASTER.md
- BRAIN_30_EVIDENCE.json
- BRAIN_39_PATTERNS.json

### TRACK 3: PPO_CONTEMPT_PROCESS_ABUSE
- POLICE_REPORTS_MAPPED.json
- WEAPON_CHAINS.json
- WEAPONIZABLE_TIMELINE.json

### TRACK 4: JUDICIAL_CONDUCT
- JUDICIAL_MISCONDUCT_EVIDENCE.json
- JTC_COMPLAINT_DRAFT.md

### TRACK 5: WATSONS_LAWSUIT (AIR-GAPPED)
### TRACK 6: SYSTEMIC_LAWSUIT (AIR-GAPPED)

## SCRIPTS

- run_all_planes.py: Master workflow
- extract_plane_0.py: Raw extraction
- extract_plane_1_pincites.py: Pincite mining
- extract_plane_2_classification.py: Classification
