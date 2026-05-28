# DESIGN SYSTEM: LITIGATIONOS

**DOCUMENT ID:** DESIGN_SYSTEM_LITIGATIONOS_V1.0.0
**VERSION:** 1.0.0
**LAST UPDATED:** 2026-05-28
**CLASSIFICATION:** PRIVILEGED AND CONFIDENTIAL - ATTORNEY WORK PRODUCT

This document establishes the design system and standards for LitigationOS.

## CORE PRINCIPLES

1. **Formality**: ALL references use complete, formal names
2. **Isolation**: Each track contains ONLY intelligence relevant to its defined entities
3. **Documentation**: Every cross-reference, contradiction, and citation is explicitly documented
4. **Persistence**: System state maintains across all chats and sessions
5. **Court Readiness**: All outputs meet immediate filing standards for Michigan courts

## DIRECTORY STRUCTURE

LitigationOS/
├── TRACK_DEFINITIONS.json
├── DESIGN_SYSTEM.md
├── CROSS_REFERENCE_LOG.json
├── FILE_INDEX.md
├── master_control.py
├── SCRIPTS/
│   ├── run_all_planes.py
│   ├── extract_plane_0.py
│   ├── extract_plane_1_pincites.py
│   ├── extract_plane_2_classification.py
│   └── ...
└── TRACK1_HOUSING_LANDLORD_TENANT/
    ├── DOCUMENTS/
    ├── COURT_FORMS/
    └── ANALYSIS/

## FILE NAMING CONVENTIONS

- Master Documents: [TOPIC]_MASTER.[ext]
- Legal Documents: LEGAL_[TOPIC].json
- Evidence Files: EVIDENCE_[CATEGORY].json
- Analysis Files: [TOPIC]_ANALYSIS.[ext]

## PROHIBITED TERMS

NEVER use: MEEK, manbearpig, informal abbreviations, nicknames, slang

ALWAYS use: Full formal track names, complete entity names, full case numbers

## VALIDATION PROTOCOLS

- All facts verified against source documents
- All citations accurate and complete (Bluebook format)
- Track isolation maintained
- Cross-references documented
- Formal names used

## SECURITY

- System accessible only to Andrew P.
- All files marked PRIVILEGED AND CONFIDENTIAL
- Attorney-work product classification
