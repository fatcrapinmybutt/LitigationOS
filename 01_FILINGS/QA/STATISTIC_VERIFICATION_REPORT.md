# STATISTIC VERIFICATION REPORT — FINAL

**Generated:** 2026-03-23 09:11:55
**Database:** `litigation_context.db`
**Files Scanned:** 968
**Statistical Claims Found:** 1634
**Files With Critical Issues:** 75

> **Methodology:** This report extracts numerical claims from filing .md files,
> matches them against the correct database tables (verified via deep query analysis),
> and classifies each as FABRICATED, INFLATED, CORRECT, UNDERSTATED, or DURATION.
> Duration claims (days in jail, days without contact) are NOT compared to table
> row counts — they require date-based verification.

## Summary

| Status | Count | Action |
|--------|-------|--------|
| ❌ **FABRICATION** | **0** | **REMOVE before filing** |
| ❌ **INFLATED** (claimed > DB actual) | **104** | **CORRECT to DB value** |
| ⚠️ UNDERSTATED (claimed < DB actual) | 176 | Consider updating |
| 🕐 DURATION (date-based, not counts) | 124 | Verify via timeline dates |
| ❓ Unmatched (manual review needed) | 1016 | Review in context |

## 🚨 INFLATED STATISTICS (104)

**These numbers EXCEED the actual database counts. Must be corrected.**

### Evidence Quotes (Alienation)
- **Correct Query:** `SELECT COUNT(*) FROM alienation_timeline`
- **Correct Table:** `alienation_timeline`
- **Notes:** alienation_timeline=2,404; evidence_quotes with alienation category=917. 6,339 is inflated by 2-3x.

| File | Line | Claimed |
|------|------|---------|
| `MOTION_PARENTAL_ALIENATION_INTERFERENCE.md` | 217 | 63 documented events |
| `MOTION_PARENTAL_ALIENATION_INTERFERENCE.md` | 956 | 6,339 evidence quotes |
| `CIVIL_COMPLAINT_WATSON_FAMILY.md` | 228 | 39 documented instances |
| `COMPLAINT_JUDICIAL_TENURE_COMMISSION.md` | 240 | 9 ex parte communications |
| `JUDICIAL_BIAS_CHRONOLOGY_BRIEF.md` | 116 | 063 judicial violations |
| `01_14TH_CIRCUIT__CIVIL_COMPLAINT_WATSON_FAMILY.md` | 240 | 39 documented instances |
| `01_14TH_CIRCUIT__MOTION_CONTEMPT_SHOW_CAUSE.md` | 797 | 39 consecutive days of denied parenting |
| `19_CUSTODY_JOURNAL.md` | 4487 | 9.8% of |
| `CIVIL_COMPLAINT_WATSON_1.md` | 448 | 9 documented violations |
| `CIVIL_COMPLAINT_WATSON_FAMILY_1.md` | 228 | 39 documented instances |
| `CIVIL_COMPLAINT_WATSON_FAMILY_2.md` | 240 | 39 documented instances |
| `CUSTODY_CASE_TIMELINE.md` | 347 | 6% of |
| `journal_md_1.md` | 4535 | 9.8% of |
| `MCNEILL_EXTRACTION_SUMMARY.md` | 24 | 6 documented violations |
| `MCNEILL_EXTRACTION_SUMMARY.md` | 43 | 6 violations |
| `MCNEILL_JUDICIAL_DOSSIER.md` | 316 | 33 violations |
| `MCNEILL_JUDICIAL_DOSSIER.md` | 398 | 9 violations |
| `MCNEILL_JUDICIAL_DOSSIER.md` | 400 | 6 violations |
| `MOTION_CONTEMPT_SHOW_CAUSE_1.md` | 797 | 39 consecutive days of denied parenting |
| `MOTION_CONTEMPT_SHOW_CAUSE_2.md` | 797 | 39 consecutive days of denied parenting |

### Evidence Quotes/Entries
- **Correct Query:** `SELECT COUNT(*) FROM evidence_quotes`
- **Correct Table:** `evidence_quotes`
- **Notes:** Correct count is 92,246. The 308,704 likely conflated file_inventory (230K) or external_drive_files (363K) with evidence_quotes.

| File | Line | Claimed |
|------|------|---------|
| `MSC_PROPOSED_ORDERS_FLEET.md` | 4 | 308,704 evidence quotes |
| `MSC_PROPOSED_ORDERS_FLEET.md` | 381 | 308,704 entries |
| `04_STATEMENT_OF_FACTS_EXPANDED.md` | 259 | 308,704 entries |
| `06_FILING_READINESS_SCORE.md` | 46 | 308,704 evidence quotes |
| `COA_366810_APPELLANTS_BRIEF.md` | 407 | 30% of |
| `COA_366810_APPELLANTS_BRIEF.md` | 506 | 87 violations |
| `COA_366810_APPELLANTS_BRIEF_1.md` | 409 | 30% of |
| `COA_366810_APPELLANTS_BRIEF_1.md` | 512 | 87 violations |
| `COA_366810_APPELLANTS_BRIEF_PACKAGE.md` | 544 | 87 violations |
| `COA_366810_APPELLANTS_BRIEF_PACKAGE_1.md` | 544 | 87 violations |
| `COA_BRIEF_366810_FINAL.md` | 724 | 308,704 entries |
| `05_MSC_ORIGINAL_ACTION.md` | 635 | 308,704 evidence quotes |
| `06_JTC_COMPLAINT.md` | 351 | 4 violation |
| `07_CUSTODY_MODIFICATION.md` | 218 | 30% of |
| `09_COA_BRIEF_ON_APPEAL.md` | 248 | 4 violation |
| `09_COA_BRIEF_ON_APPEAL.md` | 502 | 4 violations |
| `05_EMERGENCY_APPLICATION_EVIDENCE.md` | 382 | 8 violations |
| `10_READINESS_SCORES.md` | 125 | 308,704 evidence quotes |
| `ENHANCED_MISCONDUCT_BRIEF.md` | 68 | 7 documented instances |
| `EVIDENCE_MINING_CYCLE6.md` | 59 | 7 documented instances |
| `COMPLAINT_JUDICIAL_TENURE_COMMISSION.md` | 479 | 8 Documented Violations |
| `03_JTC__ENHANCED_MISCONDUCT_BRIEF.md` | 68 | 7 documented instances |
| `ENHANCED_MISCONDUCT_BRIEF_2.md` | 68 | 7 documented instances |
| `JTC_SUPPLEMENTAL_BRIEF_V4_2.md` | 205 | 87 violations |
| `02_BRIEF_IN_SUPPORT.md` | 172 | 308,704 evidence quotes |
| `02_STATEMENT_OF_FACTS_2.md` | 363 | 30 documented instances |
| `14_MCNEILL_JOURNAL.md` | 48 | 30 violations |
| `19_CUSTODY_JOURNAL.md` | 4489 | 4 documented instances |
| `LANE_A_CUSTODY_MOTION_CHANGE_OF_VENUE.md` | 181 | 87 documented instances |
| `LANE_A_CUSTODY_TORT_COMPLAINT_WATSON_FAMILY.md` | 124 | 30% of |
| `MCNEILL_JUDICIAL_DOSSIER.md` | 399 | 8 violations |
| `MCNEILL_JUDICIAL_DOSSIER.md` | 404 | 4 violations |
| `MOTION_CHANGE_OF_VENUE_3.md` | 183 | 87 documented instances |
| `MOTION_FOR_DISQUALIFICATION_v2.md` | 159 | 8 ex parte order |
| `TORT_COMPLAINT_WATSON_FAMILY_1.md` | 124 | 30% of |
| `watson_damages_schedule.md` | 74 | 70% of |
| `watson_damages_schedule.md` | 123 | 8% of |
| `03_AFFIDAVIT_PIGORS.md` | 251 | 308,704 evidence quotes |

### Findings Count
- **Correct Query:** `SELECT COUNT(*) FROM judicial_violations WHERE LOWER(description) LIKE '%finding%'`
- **Correct Table:** `judicial_violations`
- **Notes:** DB has 456 findings. Claimed 519 (13% inflation).

| File | Line | Claimed |
|------|------|---------|
| `MSC_PROPOSED_ORDERS_FLEET.md` | 148 | 5 ex parte orders |
| `AFFIDAVIT_PIGORS_MSC.md` | 58 | 519 total findings |
| `CONVERGENCE_BRIEF_CROSS_LANE.md` | 297 | 5 violations |
| `05_EMERGENCY_APPLICATION_EVIDENCE.md` | 381 | 5 ex parte orders |
| `42_EMERGENCY_JOURNAL.md` | 2190 | 5 ex parte orders |
| `complaint_1983_v2.md` | 276 | 5 ex parte orders |
| `EVIDENCE_APPENDIX_1983.md` | 102 | 5 ex parte orders |
| `FEDERAL_1983_COMPLAINT_FINAL.md` | 172 | 5 ex parte orders |
| `01_FEDERAL_1983_COMPLAINT.md` | 205 | 5 ex parte orders |
| `AFFIDAVIT_PIGORS_14TH_CIRCUIT.md` | 581 | 5 ex parte orders |
| `ENHANCED_ALIENATION_BRIEF.md` | 45 | 519 total findings |
| `MOTION_APPOINT_GAL.md` | 94 | 519 total findings |
| `MOTION_EMERGENCY_CUSTODY.md` | 92 | 519 total findings |
| `MOTION_EMERGENCY_CUSTODY.md` | 189 | 519 documented instances |
| `AFFIDAVIT_PIGORS_JTC.md` | 46 | 519 total findings |
| `ENHANCED_MISCONDUCT_BRIEF.md` | 220 | 5 ex parte orders |
| `FORMAL_COMPLAINT_JUDGE_MCNEILL.md` | 204 | 5 ex parte orders |
| `EVIDENCE_MINING_CYCLE3.md` | 165 | 519 total findings |
| `EVIDENCE_MINING_CYCLE3.md` | 482 | 5 ex parte orders |
| `COMPLAINT_JUDICIAL_TENURE_COMMISSION.md` | 467 | 19 Documented Violations |
| `03_JTC__ENHANCED_MISCONDUCT_BRIEF.md` | 222 | 5 ex parte orders |
| `10_JTC_COMPLAINT_EVIDENCE.md` | 477 | 5 ex parte orders |
| `ENHANCED_MISCONDUCT_BRIEF_2.md` | 222 | 5 ex parte orders |
| `01_14TH_CIRCUIT__AFFIDAVIT_PIGORS_14TH_CIRCUIT.md` | 661 | 5 ex parte orders |
| `01_14TH_CIRCUIT__MOTION_EMERGENCY_CUSTODY.md` | 92 | 519 total findings |
| `01_14TH_CIRCUIT__MOTION_EMERGENCY_CUSTODY.md` | 225 | 519 documented instances |
| `03_JTC__FORMAL_COMPLAINT_JUDGE_MCNEILL.md` | 229 | 5 ex parte orders |
| `14_MCNEILL_JOURNAL.md` | 49 | 5 ex parte orders |
| `AFFIDAVIT_PIGORS_14TH_CIRCUIT_1.md` | 661 | 5 ex parte orders |
| `AFFIDAVIT_PIGORS_14TH_CIRCUIT_2.md` | 661 | 5 ex parte orders |
| `exhibit_list_3.md` | 57 | 5 ex parte orders |
| `FORMAL_COMPLAINT_JUDGE_MCNEILL_1.md` | 229 | 5 ex parte orders |
| `journal_md.md` | 4811 | 19.2% of |
| `MCNEILL_JUDICIAL_DOSSIER.md` | 391 | 51 violations |
| `MCNEILL_JUDICIAL_DOSSIER.md` | 401 | 5 violations |
| `MCNEILL_JUDICIAL_DOSSIER.md` | 1703 | 5 ex parte orders |
| `MEEK2_CUSTODY_PT.md` | 243 | 5 ex parte orders |
| `MEEK2_CUSTODY_PT_CLEAN.md` | 243 | 5 ex parte orders |
| `MEEK2_CUSTODY_PT_CLEAN_DELTA2.md` | 243 | 5 ex parte orders |
| `MOTION_EMERGENCY_CUSTODY_1.md` | 92 | 519 total findings |
| `MOTION_EMERGENCY_CUSTODY_1.md` | 225 | 519 documented instances |
| `MOTION_EMERGENCY_CUSTODY_2.md` | 92 | 519 total findings |
| `MOTION_EMERGENCY_CUSTODY_2.md` | 225 | 519 documented instances |
| `PKG07_MSC_APPLICATION_FINALIZED.md` | 431 | 5% of |
| `watson_damages_schedule.md` | 139 | 5% of |
| `watson_expanded_complaint.md` | 514 | 5 ex parte orders |

## ⚠️ UNDERSTATED STATISTICS (176)

**These numbers are BELOW actual DB counts. Not wrong, but could be updated.**

### Ex Parte Communications
- **Correct Query:** `SELECT COUNT(*) FROM judicial_violations WHERE LOWER(violation_type) LIKE '%ex parte%' OR LOWER(description) LIKE '%ex parte%'`
- **Notes:** DB has 3,366 ex parte judicial violations + 6,375 evidence_quotes. 226 is severely understated.

| File | Line | Claimed |
|------|------|---------|
| `COA_366810_APPELLANTS_BRIEF.md` | 45 | 226 ex parte communication |
| `COA_366810_APPELLANTS_BRIEF.md` | 65 | 226 EX PARTE COMMUNICATIONS |
| `COA_366810_APPELLANTS_BRIEF.md` | 487 | 226 EX PARTE COMMUNICATION |
| `COA_366810_APPELLANTS_BRIEF.md` | 508 | 226 Ex Parte Communication |
| `COA_366810_APPELLANTS_BRIEF_1.md` | 45 | 226 ex parte communication |
| `COA_366810_APPELLANTS_BRIEF_1.md` | 65 | 226 EX PARTE COMMUNICATIONS |
| `COA_366810_APPELLANTS_BRIEF_1.md` | 493 | 226 EX PARTE COMMUNICATION |
| `COA_366810_APPELLANTS_BRIEF_1.md` | 514 | 226 Ex Parte Communication |
| `COA_366810_APPELLANTS_BRIEF_PACKAGE.md` | 82 | 226 ex parte communication |
| `COA_366810_APPELLANTS_BRIEF_PACKAGE.md` | 105 | 226 EX PARTE COMMUNICATIONS |
| `COA_366810_APPELLANTS_BRIEF_PACKAGE.md` | 525 | 226 EX PARTE COMMUNICATION |
| `COA_366810_APPELLANTS_BRIEF_PACKAGE.md` | 546 | 226 Ex Parte Communication |
| `COA_366810_APPELLANTS_BRIEF_PACKAGE_1.md` | 82 | 226 ex parte communication |
| `COA_366810_APPELLANTS_BRIEF_PACKAGE_1.md` | 105 | 226 EX PARTE COMMUNICATIONS |
| `COA_366810_APPELLANTS_BRIEF_PACKAGE_1.md` | 525 | 226 EX PARTE COMMUNICATION |
| `COA_366810_APPELLANTS_BRIEF_PACKAGE_1.md` | 546 | 226 Ex Parte Communication |
| `JTC_SUPPLEMENTAL_BRIEF_V4_1.md` | 285 | 226 violations |
| `JTC_SUPPLEMENTAL_BRIEF_V4_2.md` | 318 | 226 violations |
| `JUDICIAL_BIAS_CHRONOLOGY_BRIEF.md` | 361 | 22% of |
| `LANE_A_CUSTODY_MOTION_CHANGE_OF_VENUE.md` | 32 | 226 ex parte communication |
| `LANE_A_CUSTODY_MOTION_CHANGE_OF_VENUE.md` | 135 | 226 documented instances |
| `MOTION_CHANGE_OF_VENUE_3.md` | 32 | 226 ex parte communication |
| `MOTION_CHANGE_OF_VENUE_3.md` | 137 | 226 documented instances |

### Ex Parte Orders
- **Correct Query:** `SELECT COUNT(*) FROM docket_events WHERE LOWER(description) LIKE '%ex parte%'`
- **Notes:** docket_events has 181 ex parte entries. 52 is understated.

| File | Line | Claimed |
|------|------|---------|
| `COA_SUPPLEMENTAL_BRIEF.md` | 164 | 52 EX PARTE ORDERS |
| `COA_SUPPLEMENTAL_BRIEF.md` | 204 | 52 ex parte orders |
| `AFFIDAVIT_PIGORS_MSC.md` | 108 | 52 Ex Parte Orders |
| `APPLICATION_LEAVE_TO_APPEAL_2.md` | 336 | 52 Ex Parte Orders |
| `COA_BRIEF_DRAFT.md` | 112 | 52 ex parte orders |
| `COA_BRIEF_FINAL.md` | 112 | 52 ex parte orders |
| `MOTION_IMMEDIATE_CONSIDERATION.md` | 229 | 52 ex parte orders |
| `MOTION_IMMEDIATE_CONSIDERATION_2.md` | 229 | 52 ex parte orders |
| `PETITION_SUPERINTENDING_CONTROL.md` | 516 | 52 Ex Parte Orders |
| `PETITION_SUPERINTENDING_CONTROL.md` | 732 | 52 ex parte orders |
| `01_EMERGENCY_MOTION_RESTORE_PARENTING_TIME.md` | 55 | 52 ex parte order |
| `02_MOTION_TERMINATE_PPO.md` | 77 | 52 ex parte order |
| `03_MOTION_CONTEMPT_SHOW_CAUSE.md` | 53 | 52 ex parte order |
| `04_MOTION_DISQUALIFY_JUDGE.md` | 43 | 52 ex parte order |
| `05_MOTION_VACATE_EX_PARTE_ORDERS.md` | 46 | 52 ex parte order |
| `06_MOTION_CHANGE_OF_VENUE.md` | 38 | 52 ex parte order |
| `07_AFFIDAVIT_ANDREW_PIGORS.md` | 48 | 52 ex parte order |
| `10_READINESS_SCORES.md` | 93 | 52 ex parte order |
| `A_EMERGENCY_MOTION_RESTORE_PARENTING_TIME.md` | 100 | 52 ex parte orders |
| `C_BRIEF_IN_SUPPORT.md` | 107 | 52 ex parte orders |
| `05_USDC__FEDERAL_1983_COMPLAINT.md` | 351 | 52 Ex Parte Orders |
| `FEDERAL_1983_COMPLAINT.md` | 323 | 52 Ex Parte Orders |
| `FEDERAL_1983_COMPLAINT_2.md` | 351 | 52 Ex Parte Orders |
| `FEDERAL_1983_COMPLAINT_2_2.md` | 339 | 52 Ex Parte Orders |
| `FEDERAL_1983_COMPLAINT_3.md` | 323 | 52 Ex Parte Orders |
| `AFFIDAVIT_PIGORS_14TH_CIRCUIT.md` | 584 | 52 ex parte orders |
| `EMERGENCY_MOTION_RESTORE_PARENTING_TIME.md` | 452 | 52 ex parte orders |
| `MOTION_CHANGE_OF_VENUE.md` | 237 | 52 Ex Parte Orders |
| `MOTION_SET_ASIDE_DEFAULT.md` | 108 | 52 ex parte orders |
| `APPLICATION_LEAVE_TO_APPEAL.md` | 338 | 52 Ex Parte Orders |
| `01_14TH_CIRCUIT__AFFIDAVIT_PIGORS_14TH_CIRCUIT.md` | 664 | 52 ex parte orders |
| `01_14TH_CIRCUIT__MOTION_CHANGE_OF_VENUE.md` | 239 | 52 Ex Parte Orders |
| `AFFIDAVIT_PIGORS_14TH_CIRCUIT_1.md` | 664 | 52 ex parte orders |
| `AFFIDAVIT_PIGORS_14TH_CIRCUIT_2.md` | 664 | 52 ex parte orders |
| `EXHIBIT_LIST.md` | 30 | 52 ex parte orders |
| `FILING_CHECKLIST.md` | 34 | 52 ex parte orders |
| `journal_md_1.md` | 1358 | 52 Ex Parte Orders |
| `MOTION_CHANGE_OF_VENUE_2.md` | 239 | 52 Ex Parte Orders |
| `MOTION_CHANGE_OF_VENUE_2_2.md` | 239 | 52 Ex Parte Orders |
| `PROPOSED_ORDER_3.md` | 44 | 52 ex parte orders |

### Interference/Denial Incidents
- **Correct Query:** `SELECT COUNT(*) FROM alienation_timeline`
- **Notes:** alienation_timeline has 2,404 entries. evidence_quotes with interference=590. 305 is understated.

| File | Line | Claimed |
|------|------|---------|
| `01_AGC_COMPLAINT_BERRY.md` | 156 | 305 documented incidents |
| `01_EMERGENCY_PT_MOTION.md` | 186 | 305 documented incidents |
| `01_EMERGENCY_PT_MOTION.md` | 347 | 305 Documented Incidents |
| `03_CONTEMPT_MOTION.md` | 128 | 305 documented incidents |
| `COA_366810_APPELLANTS_BRIEF_FINAL.md` | 347 | 305 separate incidents |
| `COA_366810_APPELLANTS_BRIEF_FINAL.md` | 407 | 305 documented incidents |
| `COA_366810_APPELLANTS_BRIEF_FINAL.md` | 766 | 305 documented violations |
| `COA_366810_APPELLANTS_BRIEF_FINAL.md` | 782 | 305 violations |
| `CONVERGENCE_BRIEF_CROSS_LANE.md` | 374 | 305 documented incidents |
| `MASTER_AFFIDAVIT_EMILY_WATSON_FAMILY.md` | 179 | 305 documented incidents |
| `01_COMPLAINT_DECLARATORY.md` | 169 | 305 documented instances |
| `02_BRIEF_IN_SUPPORT.md` | 103 | 305 documented instances |
| `01_APPLICATION_EMERGENCY_RELIEF.md` | 109 | 305 separate incidents |
| `02_BRIEF_IN_SUPPORT.md` | 104 | 305 separate incidents |
| `03_AFFIDAVIT_EMERGENCY.md` | 96 | 305 separate incidents |
| `03_AFFIDAVIT_EMERGENCY.md` | 108 | 305 documented incidents |
| `02_BRIEF_IN_SUPPORT.md` | 211 | 305 documented violations |
| `02_BRIEF_IN_SUPPORT.md` | 291 | 305 documented incidents |
| `04_PROPOSED_ORDER.md` | 53 | 305 documented incidents |
| `01_APPLICATION_WRIT_MANDAMUS.md` | 145 | 305 separate incidents |
| `02_BRIEF_IN_SUPPORT.md` | 450 | 305 violations |
| `01_PETITION_SUPERINTENDING_CONTROL.md` | 139 | 305 documented violations |
| `01_PETITION_SUPERINTENDING_CONTROL.md` | 163 | 305 violations |
| `03_AFFIDAVIT_PIGORS.md` | 125 | 305 documented violations |
| `03_AFFIDAVIT_PIGORS.md` | 127 | 305 violations |
| `04_PROPOSED_ORDER.md` | 58 | 305 documented violations |
| `04_PROPOSED_ORDER_SHOW_CAUSE.md` | 62 | 305 documented incidents |
| `01_MOTION_Emergency_Parenting_Time.md` | 240 | 305 documented incidents |
| `01_VERIFIED_COMPLAINT.md` | 141 | 305 separate incidents |
| `01_VERIFIED_COMPLAINT.md` | 621 | 305 documented incidents |
| `03_AFFIDAVIT_PIGORS.md` | 76 | 305 separate incidents |

### Judicial Violations
- **Correct Query:** `SELECT COUNT(*) FROM judicial_violations`
- **Notes:** DB has 5,063 judicial violations. 1,127 is UNDERSTATED, not inflated. v2 erroneously compared to case_timeline.

| File | Line | Claimed |
|------|------|---------|
| `01_Emergency_Application_for_Leave_to_Appeal.md` | 43 | 127 judicial violations |
| `07_USDC_Section_1983_Complaint.md` | 164 | 127 Documented Violations |
| `07_USDC_Section_1983_Complaint.md` | 428 | 127 documented violations |
| `07_USDC_Section_1983_Complaint.md` | 543 | 127 total violations |
| `Response_to_Motion_to_Dismiss.md` | 49 | 127 documented violations |
| `PKG10_FEDERAL_1983_FINALIZED.md` | 272 | 127 documented instances |
| `PKG10_FEDERAL_1983_FINALIZED.md` | 335 | 127 distinct violations |
| `PKG10_FEDERAL_1983_FINALIZED.md` | 370 | 127 documented violations |
| `PKG10_FEDERAL_1983_FINALIZED.md` | 418 | 127 violations |
| `MOTION_DISQUALIFICATION_MCNEILL.md` | 111 | 127 documented instances |
| `MSC_PROPOSED_ORDERS_FLEET.md` | 4 | 127 judicial violations |
| `MSC_PROPOSED_ORDERS_FLEET.md` | 50 | 1,127 entries |
| `AFFIDAVIT_PIGORS_COA_2.md` | 92 | 127 judicial violations |
| `BRIEF_IN_SUPPORT_EMERGENCY_MOTION_COA.md` | 125 | 127 judicial violations |
| `MOTION_IMMEDIATE_CONSIDERATION_COA.md` | 52 | 127 judicial violations |
| `AFFIDAVIT_IN_SUPPORT.md` | 123 | 127 documented violations |
| `EMERGENCY_MOTION_FOR_STAY.md` | 83 | 127 judicial violations |
| `05_MSC_ORIGINAL_ACTION.md` | 296 | 127 judicial violations |
| `05_MSC_ORIGINAL_ACTION.md` | 683 | 127 violations |
| `05_MSC_ORIGINAL_ACTION.md` | 1036 | 127 documented violations |
| `BRIEF_IN_SUPPORT.md` | 212 | 127 violations |
| `BRIEF_IN_SUPPORT.md` | 221 | 127 documented violations |
| `CONSOLIDATED_EXHIBIT_INDEX.md` | 169 | 127 documented violations |
| `CONSOLIDATED_EXHIBIT_INDEX.md` | 254 | 127 Violations |
| `MOTION_FOR_DISQUALIFICATION.md` | 87 | 27 documented instances |
| `05_EMERGENCY_APPLICATION_EVIDENCE.md` | 129 | 127 documented violations |
| `05_EMERGENCY_APPLICATION_EVIDENCE.md` | 178 | 127 judicial violations |
| `05_EMERGENCY_APPLICATION_EVIDENCE.md` | 295 | 127 violations |
| `05_EMERGENCY_APPLICATION_EVIDENCE.md` | 390 | 127 total violations |
| `MSC_EMERGENCY_APPLICATION_FINAL.md` | 83 | 127 judicial violations |
| `MSC_EMERGENCY_APPLICATION_FINAL.md` | 203 | 127 documented violations |
| `MSC_EMERGENCY_APPLICATION_FINAL.md` | 252 | 127 Violations |
| `brief_in_support_1983_v2.md` | 60 | 127 documented violations |
| `brief_in_support_1983_v2.md` | 88 | 27 documented incidents |
| `brief_in_support_1983_v2.md` | 108 | 127 violations |
| `BRIEF_IN_SUPPORT_IFP.md` | 60 | 127 documented violations |
| `complaint_1983_v2.md` | 236 | 127 violations |
| `complaint_1983_v2.md` | 384 | 127 documented violations |
| `complaint_1983_v2.md` | 503 | 127 judicial violations |
| `EVIDENCE_APPENDIX_1983.md` | 37 | 127 violations |
| `FEDERAL_1983_COMPLAINT_1.md` | 121 | 127 judicial violations |
| `JS_44_CIVIL_COVER_SHEET.md` | 102 | 127 documented violations |
| `01_FEDERAL_1983_COMPLAINT.md` | 290 | 127 documented violations |
| `02_BRIEF_IN_SUPPORT.md` | 157 | 127 violations |
| `02_BRIEF_IN_SUPPORT.md` | 193 | 127 documented violations |
| `02_BRIEF_IN_SUPPORT.md` | 235 | 127 judicial violations |
| `04_EXHIBIT_INDEX.md` | 110 | 127 violations |
| `FILING_CHECKLISTS.md` | 26 | 127 violations |
| `ENHANCED_ALIENATION_BRIEF.md` | 381 | 27 violations |
| `MOTION_CONTEMPT_SHOW_CAUSE.md` | 55 | 27 documented instances |
| `01_JTC_REQUEST_FOR_INVESTIGATION.md` | 47 | 27 documented instances |
| `01_JTC_REQUEST_FOR_INVESTIGATION.md` | 107 | 127 violations |
| `10_JTC_COMPLAINT_EVIDENCE.md` | 55 | 127 documented violations |
| `10_JTC_COMPLAINT_EVIDENCE.md` | 71 | 127 judicial violations |
| `10_JTC_COMPLAINT_EVIDENCE.md` | 472 | 127 violations |
| `COVER_LETTER_JTC.md` | 69 | 127 violations |
| `EXHIBIT_PACKAGE_INDEX.md` | 88 | 127 violations |
| `JTC_COMPLAINT.md` | 128 | 127 violations |
| `STATISTICAL_ANALYSIS.md` | 189 | 127 violations |
| `WITNESS_LIST.md` | 68 | 127 documented violations |
| `01_PETITION_SUPERINTENDING_CONTROL.md` | 253 | 127 judicial violations |
| `01_14TH_CIRCUIT__MOTION_CONTEMPT_SHOW_CAUSE.md` | 55 | 27 documented instances |
| `19_CUSTODY_JOURNAL.md` | 19252 | 12 VIOLATION |
| `DISQUAL_PROCEDURE_SPINE.md` | 98 | 127 judicial violations |
| `DISQUAL_PROCEDURE_SPINE.md` | 155 | 127 violations |
| `FILING_CHECKLIST.md` | 35 | 127 violations |
| `MCNEILL_BENCHBOOK_DEVIATION_REPORT.md` | 42 | 127 documented violations |
| `MCNEILL_JUDICIAL_DOSSIER.md` | 4 | 127 documented violations |
| `MCNEILL_JUDICIAL_DOSSIER.md` | 394 | 27 violations |
| `MCNEILL_JUDICIAL_DOSSIER.md` | 397 | 11 violations |
| `MCNEILL_JUDICIAL_DOSSIER.md` | 3649 | 127 violations |
| `MOTION_CONTEMPT_SHOW_CAUSE_1.md` | 55 | 27 documented instances |
| `MOTION_CONTEMPT_SHOW_CAUSE_2.md` | 55 | 27 documented instances |
| `MOTION_DISQUALIFICATION.md` | 95 | 127 violations |
| `MOTION_DISQUALIFICATION_MCNEILL.md` | 193 | 127 judicial violations |
| `MOTION_DISQUALIFICATION_MCNEILL.md` | 205 | 127 violations |
| `MOTION_DISQUALIFICATION_MCNEILL.md` | 213 | 127 documented violations |
| `PKG03_DISQUALIFY_MCNEILL_FINALIZED.md` | 234 | 127 judicial violations |
| `PKG03_DISQUALIFY_MCNEILL_FINALIZED.md` | 411 | 127 documented violations |
| `PKG03_DISQUALIFY_MCNEILL_FINALIZED.md` | 785 | 127 violations |
| `PKG07_MSC_APPLICATION_FINALIZED.md` | 418 | 127 documented violations |
| `watson_damages_schedule.md` | 107 | 12% of |

## 🕐 DURATION CLAIMS (124)

**These are time periods (days in jail, days without contact), NOT event counts.**
**They should be verified by computing date differences from timeline events,**
**NOT by comparing to table row counts.**

### Denied Parenting Duration
- **Verification Method:** N/A — compute from denial start date
- **Notes:** Duration of denied parenting time. Timeline shows March 26-May 5, 2024 as one period. 200 days may measure a later continuous denial period.

| File | Line | Claimed |
|------|------|---------|
| `MASTER_AFFIDAVIT_OF_FACTS.md` | 246 | 20% of |
| `01_AGC_COMPLAINT_BERRY.md` | 70 | 200 consecutive days of denied parenting |
| `MOTION_PARENTAL_ALIENATION_INTERFERENCE.md` | 858 | 20 documented events |
| `COA_366810_APPELLANTS_BRIEF.md` | 459 | 329 consecutive days of denied parenting |
| `COA_366810_APPELLANTS_BRIEF_1.md` | 463 | 329 consecutive days of denied parenting |
| `COA_366810_APPELLANTS_BRIEF_PACKAGE.md` | 499 | 329 consecutive days of denied parenting |
| `COA_366810_APPELLANTS_BRIEF_PACKAGE_1.md` | 499 | 329 consecutive days of denied parenting |
| `05_EMERGENCY_APPLICATION_EVIDENCE.md` | 146 | 20 violations |
| `EVIDENCE_INDEX.md` | 124 | 200 documented violations |
| `complaint_1983_v2.md` | 29 | 329 documented findings |
| `complaint_1983_v2.md` | 180 | 329 Total Findings |
| `CIVIL_COMPLAINT_WATSON_FAMILY.md` | 229 | 29 documented instances |
| `ENHANCED_ALIENATION_BRIEF.md` | 158 | 29 documented instances |
| `COMPLAINT_JUDICIAL_TENURE_COMMISSION.md` | 456 | 29 Documented Violations |
| `B_msc_brief_in_support_v2.md` | 319 | 20.9% of |
| `01_14TH_CIRCUIT__CIVIL_COMPLAINT_WATSON_FAMILY.md` | 241 | 29 documented instances |
| `02_STATEMENT_OF_FACTS_2.md` | 369 | 29 documented instances |
| `CIVIL_COMPLAINT_WATSON_FAMILY_1.md` | 229 | 29 documented instances |
| `CIVIL_COMPLAINT_WATSON_FAMILY_2.md` | 241 | 29 documented instances |
| `FILING_CHECKLIST.md` | 36 | 20 violations |
| `MCNEILL_JUDICIAL_DOSSIER.md` | 333 | 32 violations |
| `01_VERIFIED_COMPLAINT.md` | 366 | 200 consecutive days of denied parenting |

### Incarceration Duration
- **Verification Method:** N/A — verify via jail entry/release dates in case_timeline
- **Notes:** This is a duration claim (days in jail), not a count. Verify by computing date difference between jail entry and release.

| File | Line | Claimed |
|------|------|---------|
| `MASTER_AFFIDAVIT_OF_FACTS.md` | 226 | 59 days of incarceration |
| `COA_SUPPLEMENTAL_BRIEF.md` | 200 | incarcerated for 59 days |
| `COA_SUPPLEMENTAL_BRIEF.md` | 349 | 59 days of incarceration |
| `COA_SUPPLEMENTAL_BRIEF.md` | 532 | 59 days incarceration |
| `JTC_SUPPLEMENTAL_COMPLAINT.md` | 47 | incarcerated for 59 days |
| `JTC_SUPPLEMENTAL_COMPLAINT.md` | 275 | 59 days incarceration |
| `JTC_SUPPLEMENTAL_COMPLAINT.md` | 310 | 59 days of incarceration |
| `MOTION_FOR_DISQUALIFICATION.md` | 99 | incarcerated for 59 days |
| `01_EMERGENCY_PT_MOTION.md` | 154 | 59 days of incarceration |
| `02_DISQUALIFICATION_MOTION.md` | 45 | 59 days of incarceration |
| `AFFIDAVIT_OF_DISQUALIFICATION.md` | 110 | 59 days of incarceration |
| `COA_BRIEF_366810_APEX.md` | 175 | jailed for 59 days |
| `COA_BRIEF_366810_APEX.md` | 263 | 59 DAYS OF INCARCERATION |
| `CONVERGENCE_BRIEF_CROSS_LANE.md` | 213 | jailed for 59 days |
| `CONVERGENCE_BRIEF_CROSS_LANE.md` | 269 | 59 days of incarceration |
| `03_DISQUALIFICATION_MCR2003.md` | 120 | 59 days of incarceration |
| `03_DISQUALIFICATION_MCR2003.md` | 170 | 45 days of incarceration |
| `04_FEDERAL_1983_COMPLAINT.md` | 49 | 59 days of incarceration |
| `04_FEDERAL_1983_COMPLAINT.md` | 157 | 45 Days Incarceration |
| `04_FEDERAL_1983_COMPLAINT.md` | 163 | 45 days of incarceration |
| `04_FEDERAL_1983_COMPLAINT.md` | 375 | jailed for 59 days |
| `05_MSC_ORIGINAL_ACTION.md` | 796 | jailed for 59 days |
| `05_MSC_ORIGINAL_ACTION.md` | 862 | 59 Days of Incarceration |
| `05_MSC_ORIGINAL_ACTION.md` | 1042 | 59 days of incarceration |
| `06_JTC_COMPLAINT.md` | 54 | incarcerated for 59 days |
| `06_JTC_COMPLAINT.md` | 304 | 45 days incarceration |
| `07_CUSTODY_MODIFICATION.md` | 312 | 59 days of incarceration |
| `08_PPO_TERMINATION.md` | 125 | 59 days of incarceration |
| `08_PPO_TERMINATION.md` | 253 | 59 days incarceration |
| `09_COA_BRIEF_ON_APPEAL.md` | 460 | 45 days of incarceration |
| `01_MOTION_TO_DISQUALIFY.md` | 128 | 59 days of incarceration |
| `01_MOTION_TO_DISQUALIFY.md` | 634 | 59 days incarceration |
| `01_MOTION_TO_DISQUALIFY.md` | 709 | jailed for 59 days |
| `02_AFFIDAVIT_IN_SUPPORT.md` | 330 | 59 days of incarceration |
| `03_PROPOSED_ORDER.md` | 54 | 59 days of incarceration |
| `05_EXHIBIT_INDEX.md` | 175 | 59 days of incarceration |
| `01_MOTION_TERMINATE_PPO.md` | 128 | 59 days of incarceration |
| `01_MOTION_TERMINATE_PPO.md` | 267 | 59 days incarceration |
| `AFFIDAVIT_OF_BIAS.md` | 187 | 59 days of incarceration |
| `AFFIDAVIT_OF_BIAS.md` | 187 | jailed for 59 days |
| `BRIEF_IN_SUPPORT.md` | 118 | 59 days of incarceration |
| `MOTION_DISQUALIFY_MCNEILL_v2.md` | 45 | 59 days of incarceration |
| `MOTION_FOR_DISQUALIFICATION.md` | 65 | 59 days of incarceration |
| `MOTION_FOR_DISQUALIFICATION.md` | 65 | jailed for 59 days |
| `AMENDED_1983_BERRY_CONSPIRACY.md` | 179 | 45 Days Incarceration |
| `AMENDED_1983_BERRY_CONSPIRACY.md` | 185 | 45 days of incarceration |
| `AMENDED_1983_BERRY_CONSPIRACY.md` | 211 | incarcerated for 59 days |
| `05_USDC__FEDERAL_1983_COMPLAINT.md` | 646 | 45 days of incarceration |
| `COMPLAINT_42USC1983.md` | 127 | 45 Days Incarceration |
| `COMPLAINT_42USC1983.md` | 133 | 45 days of incarceration |
| `COMPLAINT_42USC1983.md` | 149 | 59 days of incarceration |
| `COMPLAINT_42USC1983.md` | 333 | incarcerated for 59 days |
| `FEDERAL_1983_COMPLAINT_2.md` | 646 | 45 days of incarceration |
| `FEDERAL_1983_COMPLAINT_2_2.md` | 634 | 45 days of incarceration |
| `SUPPLEMENT_DOCTRINAL_DEFENSE.md` | 73 | 59 days of incarceration |
| `SUPPLEMENT_DOCTRINAL_DEFENSE.md` | 117 | 45 days of incarceration |
| `01_FEDERAL_1983_COMPLAINT.md` | 113 | incarcerated for 59 days |
| `01_FEDERAL_1983_COMPLAINT.md` | 131 | 59 days of incarceration |
| `01_FEDERAL_1983_COMPLAINT.md` | 310 | 59 days incarceration |
| `02_BRIEF_IN_SUPPORT.md` | 179 | 59 days of incarceration |
| `02_BRIEF_IN_SUPPORT.md` | 227 | 59 days incarceration |
| `04_EXHIBIT_INDEX.md` | 34 | 59 days incarceration |
| `06_IFP_APPLICATION.md` | 128 | incarcerated for 59 days |
| `COA_FEE_WAIVER_366810.md` | 121 | incarcerated for 59 days |
| `FEDERAL_IFP_APPLICATION_WDMI.md` | 175 | incarcerated for 59 days |
| `MSC_FEE_WAIVER.md` | 95 | jailed for 59 days |
| `MSC_FEE_WAIVER.md` | 144 | incarcerated for 59 days |
| `COMPLAINT_JUDICIAL_TENURE_COMMISSION.md` | 198 | incarcerated for 59 days |
| `COMPLAINT_JUDICIAL_TENURE_COMMISSION.md` | 546 | 59 days incarceration |
| `COMPLAINT_JUDICIAL_TENURE_COMMISSION.md` | 567 | 59 days of incarceration |
| `MASTER_AFFIDAVIT_EMILY_WATSON_FAMILY.md` | 163 | 59 days jailing |
| `MASTER_AFFIDAVIT_EMILY_WATSON_FAMILY.md` | 179 | 59 days of imprisonment |
| `MSC_BYPASS_APPLICATION.md` | 327 | 59 days of incarceration |
| `MSC_BYPASS_APPLICATION.md` | 339 | 59 days incarceration |
| `BRIEF_IN_SUPPORT.md` | 168 | jailed for 59 days |
| `BRIEF_IN_SUPPORT.md` | 407 | Jailed for 59 days |
| `BRIEF_IN_SUPPORT.md` | 460 | incarcerated for 59 days |
| `COMPLAINT_FOR_SUPERINTENDING_CONTROL.md` | 584 | 59 days of incarceration |
| `COMPLAINT_FOR_SUPERINTENDING_CONTROL.md` | 663 | incarcerated for 59 days |
| `EXHIBIT_INDEX.md` | 76 | 45 days incarceration |
| `PROPOSED_ORDER.md` | 81 | incarcerated for 59 days |
| `PROPOSED_ORDER.md` | 119 | 59 days of incarceration |
| `02_BRIEF_IN_SUPPORT.md` | 329 | jailed for 59 days |
| `02_BRIEF_IN_SUPPORT.md` | 395 | 59 Days of Incarceration |
| `03_AFFIDAVIT_OF_ANDREW_PIGORS.md` | 121 | jailed for 59 days |
| `05_PROPOSED_ORDER.md` | 56 | 59 days of incarceration |
| `08_COVER_LETTER.md` | 59 | 59 days of incarceration |
| `MOTION_TERMINATE_MODIFY_PPO.md` | 111 | 59 days of incarceration |
| `MOTION_TERMINATE_MODIFY_PPO.md` | 418 | 59 days incarceration |
| `MOTION_TERMINATE_MODIFY_PPO.md` | 529 | 45 days incarceration |
| `03_JTC__FORMAL_COMPLAINT_JUDGE_MCNEILL.md` | 335 | 45 days of incarceration |
| `FORMAL_COMPLAINT_JUDGE_MCNEILL.md` | 335 | 45 days of incarceration |
| `FORMAL_COMPLAINT_JUDGE_MCNEILL_1.md` | 335 | 45 days of incarceration |
| `LANE_A_CUSTODY_TORT_COMPLAINT_WATSON_FAMILY.md` | 88 | 45 days of incarceration |
| `TORT_COMPLAINT_WATSON_FAMILY_1.md` | 88 | 45 days of incarceration |
| `TORT_COMPLAINT_WATSON_FAMILY_1.md` | 88 | 45 Days Incarceration |
| `TORT_COMPLAINT_WATSON_FAMILY_1.md` | 615 | 45 days incarceration |
| `watson_expanded_complaint.md` | 376 | incarcerated for 45 days |
| `OMNIBUS_MOTION_TO_VACATE.md` | 413 | 59 days of incarceration |
| `OMNIBUS_MOTION_TO_VACATE.md` | 516 | 59 days incarceration |
| `03_AFFIDAVIT_PIGORS.md` | 128 | 59 days of incarceration |
| `04_EXHIBIT_INDEX.md` | 76 | 59 days jailing |

## Database Reference Counts (Authoritative)

**Use these values when correcting filings.**

### Core Tables

| Table | Rows | Use For |
|-------|------|---------|
| `evidence_quotes` | **92,246** | Evidence/quote counts |
| `judicial_violations` | **5,063** | Judicial violation counts |
| `docket_events` | **683** | Docket/hearing/filing events |
| `case_timeline` | **1,472** | Timeline events |
| `narrative_context` | **9,110** | Narrative entries |
| `critical_facts` | **3,048** | Critical fact counts |
| `claims` | **35** | Legal claim counts |
| `deadlines` | **13** | Filing deadlines |
| `documents` | **6,386** | Document inventory |
| `alienation_timeline` | **2,404** | Alienation/interference events |
| `judicial_bias_chronology` | **1,940** | Bias incident counts |
| `impeachment_matrix` | **1,436** | Impeachment entries |
| `false_allegations` | **7** | False allegation counts |

### Specialized Counts

| Query | Count | Verified |
|-------|-------|----------|
| alienation evidence_quotes | **917** | ✅ |
| contempt docket_events | **31** | ✅ |
| denial case_timeline | **40** | ✅ |
| ex_parte docket_events | **181** | ✅ |
| ex_parte evidence_quotes | **6,375** | ✅ |
| ex_parte violations | **3,366** | ✅ |
| findings judicial_violations | **456** | ✅ |
| interference case_timeline | **6** | ✅ |
| parenting_time case_timeline | **227** | ✅ |

### Common Claim → Correct Value Mapping

| If Filing Says | Correct Value | Source Table | Correct Query |
|---------------|---------------|-------------|---------------|
| 308,704 evidence | **92,246** | `evidence_quotes` | `SELECT COUNT(*) FROM evidence_quotes` |
| X judicial violations | **5,063** | `judicial_violations` | `SELECT COUNT(*) FROM judicial_violations` |
| X ex parte communications | **3,366** | `judicial_violations` | `...WHERE LOWER(violation_type) LIKE '%ex parte%'` |
| X alienation events | **2,404** | `alienation_timeline` | `SELECT COUNT(*) FROM alienation_timeline` |
| X interference incidents | **2,404** | `alienation_timeline` | `SELECT COUNT(*) FROM alienation_timeline` |
| X documented facts | **3,048** | `critical_facts` | `SELECT COUNT(*) FROM critical_facts` |
| X bias incidents | **1,940** | `judicial_bias_chronology` | `SELECT COUNT(*) FROM judicial_bias_chronology` |
| X impeachment entries | **1,436** | `impeachment_matrix` | `SELECT COUNT(*) FROM impeachment_matrix` |
| X false allegations | **7** | `false_allegations` | `SELECT COUNT(*) FROM false_allegations` |
| X docket events | **683** | `docket_events` | `SELECT COUNT(*) FROM docket_events` |

### Files Requiring Correction (75)

- `01_14TH_CIRCUIT__AFFIDAVIT_PIGORS_14TH_CIRCUIT.md`
- `01_14TH_CIRCUIT__CIVIL_COMPLAINT_WATSON_FAMILY.md`
- `01_14TH_CIRCUIT__MOTION_CONTEMPT_SHOW_CAUSE.md`
- `01_14TH_CIRCUIT__MOTION_EMERGENCY_CUSTODY.md`
- `01_FEDERAL_1983_COMPLAINT.md`
- `02_BRIEF_IN_SUPPORT.md`
- `02_STATEMENT_OF_FACTS_2.md`
- `03_AFFIDAVIT_PIGORS.md`
- `03_JTC__ENHANCED_MISCONDUCT_BRIEF.md`
- `03_JTC__FORMAL_COMPLAINT_JUDGE_MCNEILL.md`
- `04_STATEMENT_OF_FACTS_EXPANDED.md`
- `05_EMERGENCY_APPLICATION_EVIDENCE.md`
- `05_MSC_ORIGINAL_ACTION.md`
- `06_FILING_READINESS_SCORE.md`
- `06_JTC_COMPLAINT.md`
- `07_CUSTODY_MODIFICATION.md`
- `09_COA_BRIEF_ON_APPEAL.md`
- `10_JTC_COMPLAINT_EVIDENCE.md`
- `10_READINESS_SCORES.md`
- `14_MCNEILL_JOURNAL.md`
- `19_CUSTODY_JOURNAL.md`
- `42_EMERGENCY_JOURNAL.md`
- `AFFIDAVIT_PIGORS_14TH_CIRCUIT.md`
- `AFFIDAVIT_PIGORS_14TH_CIRCUIT_1.md`
- `AFFIDAVIT_PIGORS_14TH_CIRCUIT_2.md`
- `AFFIDAVIT_PIGORS_JTC.md`
- `AFFIDAVIT_PIGORS_MSC.md`
- `CIVIL_COMPLAINT_WATSON_1.md`
- `CIVIL_COMPLAINT_WATSON_FAMILY.md`
- `CIVIL_COMPLAINT_WATSON_FAMILY_1.md`
- `CIVIL_COMPLAINT_WATSON_FAMILY_2.md`
- `COA_366810_APPELLANTS_BRIEF.md`
- `COA_366810_APPELLANTS_BRIEF_1.md`
- `COA_366810_APPELLANTS_BRIEF_PACKAGE.md`
- `COA_366810_APPELLANTS_BRIEF_PACKAGE_1.md`
- `COA_BRIEF_366810_FINAL.md`
- `COMPLAINT_JUDICIAL_TENURE_COMMISSION.md`
- `CONVERGENCE_BRIEF_CROSS_LANE.md`
- `CUSTODY_CASE_TIMELINE.md`
- `ENHANCED_ALIENATION_BRIEF.md`
- `ENHANCED_MISCONDUCT_BRIEF.md`
- `ENHANCED_MISCONDUCT_BRIEF_2.md`
- `EVIDENCE_APPENDIX_1983.md`
- `EVIDENCE_MINING_CYCLE3.md`
- `EVIDENCE_MINING_CYCLE6.md`
- `FEDERAL_1983_COMPLAINT_FINAL.md`
- `FORMAL_COMPLAINT_JUDGE_MCNEILL.md`
- `FORMAL_COMPLAINT_JUDGE_MCNEILL_1.md`
- `JTC_SUPPLEMENTAL_BRIEF_V4_2.md`
- `JUDICIAL_BIAS_CHRONOLOGY_BRIEF.md`
- `LANE_A_CUSTODY_MOTION_CHANGE_OF_VENUE.md`
- `LANE_A_CUSTODY_TORT_COMPLAINT_WATSON_FAMILY.md`
- `MCNEILL_EXTRACTION_SUMMARY.md`
- `MCNEILL_JUDICIAL_DOSSIER.md`
- `MEEK2_CUSTODY_PT.md`
- `MEEK2_CUSTODY_PT_CLEAN.md`
- `MEEK2_CUSTODY_PT_CLEAN_DELTA2.md`
- `MOTION_APPOINT_GAL.md`
- `MOTION_CHANGE_OF_VENUE_3.md`
- `MOTION_CONTEMPT_SHOW_CAUSE_1.md`
- `MOTION_CONTEMPT_SHOW_CAUSE_2.md`
- `MOTION_EMERGENCY_CUSTODY.md`
- `MOTION_EMERGENCY_CUSTODY_1.md`
- `MOTION_EMERGENCY_CUSTODY_2.md`
- `MOTION_FOR_DISQUALIFICATION_v2.md`
- `MOTION_PARENTAL_ALIENATION_INTERFERENCE.md`
- `MSC_PROPOSED_ORDERS_FLEET.md`
- `PKG07_MSC_APPLICATION_FINALIZED.md`
- `TORT_COMPLAINT_WATSON_FAMILY_1.md`
- `complaint_1983_v2.md`
- `exhibit_list_3.md`
- `journal_md.md`
- `journal_md_1.md`
- `watson_damages_schedule.md`
- `watson_expanded_complaint.md`

---
*Report generated by LitigationOS Statistic Verification Engine v3.0 (final)*
*Deep verification: each claim category verified with correct table and query.*
*Duration claims separated from count claims to eliminate false positives.*