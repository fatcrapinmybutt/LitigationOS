# MASTER FILING MANIFEST — LitigationOS

> **Pigors v. Watson / Multi-Lane Litigation Complex**
> **Generated:** 2026-03-11
> **Maintainer:** Andrew Pigors (Pro Se)
> **System:** LitigationOS Event Horizon Δ∞

---

## Overview

This manifest maps every active filing lane to its documents, current status, file locations, and next actions. It serves as the single source of truth for all litigation deliverables across 8 case lanes.

**Status Key:**
| Status | Meaning |
|--------|---------|
| ✅ READY | Complete, court-ready, filed or ready to file |
| 📝 DRAFT | Written but needs review/revision |
| 🔨 CREATING | Actively being drafted |
| 📋 PLANNED | Scoped but not yet started |
| ❌ NEEDED | Required but not yet created |
| 🚫 BLOCKED | Cannot proceed — dependency or information gap |
| 📄 TEMPLATE | Reusable template created |

---

## Lane A — Custody (14th Circuit, Muskegon County)

**Case:** 2024-001507-DC — *Pigors v. Watson*
**Court:** 14th Circuit Court, Muskegon County
**Judge:** Hon. Annette Smedley (recusal pending via MCR 2.003)
**MEEK Signal:** MEEK2

| # | Document | Status | Path | Est. Pages | Blockers |
|---|----------|--------|------|-----------|----------|
| A-1 | Emergency Motion to Restore Parenting Time | 🔨 CREATING | `01_FILINGS\EMERGENCY\` | 15-20 | None — active drafting |
| A-2 | Motion for Contempt / Show Cause | 🔨 CREATING | `01_FILINGS\EMERGENCY\` | 10-15 | Needs finalized exhibit list |
| A-3 | Motion to Modify Custody | 📋 PLANNED | — | 20-30 | Depends on A-1 outcome |
| A-4 | Motion for Sanctions | 📋 PLANNED | — | 8-12 | Depends on A-2 |
| A-5 | FOC 65 (Uniform Child Custody Order) | ❌ NEEDED | — | 4 | Court form — obtain from SCAO |
| A-6 | FOC 66 (Order Regarding Parenting Time) | ❌ NEEDED | — | 4 | Court form — obtain from SCAO |
| A-7 | MC 280 (Proof of Service) | 📄 TEMPLATE | `01_FILINGS\TEMPLATES\MC280_PROOF_OF_SERVICE.md` | 2 | Template ready, fill per filing |
| A-8 | MC 97 (Fee Waiver Application) | 📄 TEMPLATE | `01_FILINGS\TEMPLATES\MC97_FEE_WAIVER_APPLICATION.md` | 3 | Template ready, fill per filing |
| A-9 | Motion to Vacate Prior Orders | 📝 DRAFT | `01_FILINGS\MOTION_TO_VACATE\` | 10-15 | 5 files (affidavit, brief, exhibits, checklist) |
| A-10 | Emergency Filing Package (full bundle) | 📝 DRAFT | `01_FILINGS\EMERGENCY\` | 100+ | 163 .md files, needs consolidation |

**Lane A Next Steps:**
1. Finalize Emergency Motion to Restore Parenting Time (A-1)
2. Complete exhibit index for Motion for Contempt (A-2)
3. Obtain FOC 65 and FOC 66 forms from SCAO website
4. Run pre-filing QA on complete package before submission

---

## Lane B — Housing (14th Circuit, Muskegon County)

**Case:** 2025-002760-CZ — *Pigors v. Shady Oaks et al.*
**Court:** 14th Circuit Court, Muskegon County
**MEEK Signal:** MEEK1

| # | Document | Status | Path | Est. Pages | Blockers |
|---|----------|--------|------|-----------|----------|
| B-1 | 22-Count Complaint | ✅ READY | `01_FILINGS\SHADY_OAKS_CIRCUIT\` | 30+ | 6 files: complaint, brief, exhibits, checklist |
| B-2 | Master Housing Affidavit | ✅ READY | `01_FILINGS\MASTER_AFFIDAVITS\09_AFFIDAVIT_ANDREW_PIGORS.md` | 15-20 | Complete |
| B-3 | Brief in Support | ✅ READY | `01_FILINGS\SHADY_OAKS_CIRCUIT\BRIEF_IN_SUPPORT.md` | 20 | Filed |
| B-4 | TRO Application | ✅ READY | `01_FILINGS\MASTER_AFFIDAVITS\05_TRO_APPLICATION.md` | 10 | Complete |
| B-5 | Exhibit Index | ✅ READY | `01_FILINGS\SHADY_OAKS_CIRCUIT\EXHIBIT_INDEX.md` | 5 | Complete |
| B-6 | Summons Package | ✅ READY | `01_FILINGS\MASTER_AFFIDAVITS\06_SUMMONS_PACKAGE.md` | 3 | Complete |
| B-7 | Amended Complaint Cover | ✅ READY | `01_FILINGS\MASTER_AFFIDAVITS\01_AMENDED_COMPLAINT_COVER.md` | 2 | Complete |
| B-8 | Damages Calculation | ✅ READY | `01_FILINGS\MASTER_AFFIDAVITS\03_DAMAGES_CALCULATION_FINAL.md` | 8 | Complete |
| B-9 | Corporate Disclosure | ✅ READY | `01_FILINGS\MASTER_AFFIDAVITS\04_CORPORATE_DISCLOSURE_ENHANCED.md` | 3 | Complete |
| B-10 | Filing Checklist | ✅ READY | `01_FILINGS\SHADY_OAKS_CIRCUIT\FILING_CHECKLIST.md` | 2 | Complete |
| B-11 | Motion for Disqualification | ✅ READY | `01_FILINGS\SHADY_OAKS_CIRCUIT\MOTION_FOR_DISQUALIFICATION.md` | 10 | Complete |
| B-12 | Affidavit of Bias | ✅ READY | `01_FILINGS\SHADY_OAKS_CIRCUIT\AFFIDAVIT_OF_BIAS.md` | 8 | Complete |
| B-13 | Statistical Analysis Exhibit | ✅ READY | `01_FILINGS\SHADY_OAKS_CIRCUIT\STATISTICAL_ANALYSIS_EXHIBIT.md` | 5 | Complete |

**Lane B Status:** ✅ **SUBSTANTIALLY COMPLETE** — Full complaint package ready with 13 documents.

---

## Lane C — Convergence (Cross-Lane)

**Purpose:** Cross-lane analysis, shared evidence, and convergence filings.
**MEEK Signal:** N/A (multi-lane)

| # | Document | Status | Path | Est. Pages | Blockers |
|---|----------|--------|------|-----------|----------|
| C-1 | Cross-Filing Consistency Report | 📝 DRAFT | `01_FILINGS\CROSS_FILING_CONSISTENCY_REPORT.md` | 10 | Needs update with latest filings |
| C-2 | Convergence Filing Stack | 📝 DRAFT | `01_FILINGS\CONVERGENCE\` | Variable | Cross-lane materials |

---

## Lane D — PPO (14th Circuit, Muskegon County)

**Case:** 2023-5907-PP — *Watson v. Pigors (PPO)*
**Court:** 14th Circuit Court, Muskegon County
**MEEK Signal:** MEEK3

| # | Document | Status | Path | Est. Pages | Blockers |
|---|----------|--------|------|-----------|----------|
| D-1 | Motion to Terminate PPO (CC 377) | ✅ READY | `01_FILINGS\EMERGENCY\02_MOTION_TERMINATE_PPO.md` | 12-15 | Complete — exists in EMERGENCY folder |
| D-2 | Response to PPO (CC 380) | ❌ NEEDED | — | 8-10 | Court form CC 380 needed |

**Lane D Next Steps:**
1. Obtain CC 380 form from SCAO
2. Draft Response to PPO using existing evidence from Lane A
3. Coordinate with Lane A emergency filings for simultaneous submission

---

## Lane E — JTC Judicial Misconduct

**Target:** Hon. Annette Smedley (McNeill)
**Body:** Judicial Tenure Commission (JTC)
**MEEK Signal:** MEEK4

| # | Document | Status | Path | Est. Pages | Blockers |
|---|----------|--------|------|-----------|----------|
| E-1 | JTC Complaint (v6 — latest) | ✅ READY | `04_JTC_MCNEILL\` | 50+ | Multiple versions; v6 is current |
| E-2 | JTC Request for Investigation | ✅ READY | `01_FILINGS\JTC\` | 10-15 | 6 files: request, narrative, analysis |
| E-3 | JTC Exhibit Binder (v5) | ✅ READY | `04_JTC_MCNEILL\` | 500+ | Comprehensive exhibit package |
| E-4 | JTC Enhanced Filing Stack | ✅ READY | `01_FILINGS\JTC_MCNEILL\` | 1,057 files | Enhanced with citations, journals |
| E-5 | JTC APEX Filing Stack | 📝 DRAFT | `04_JTC_MCNEILL\APEX_FILING_STACK\` | Variable | Production-quality stack |
| E-6 | JTC Production Output | 📝 DRAFT | `04_JTC_MCNEILL\PRODUCTION_OUTPUT\` | Variable | Final production files |

**Lane E Status:** ✅ **SUBSTANTIALLY COMPLETE** — Massive evidence collection (1,057+ files). Focus on final production packaging.

---

## Lane F — COA Appellate (Michigan Court of Appeals)

**Case:** 366810
**Court:** Michigan Court of Appeals
**MEEK Signal:** MEEK5

| # | Document | Status | Path | Est. Pages | Blockers |
|---|----------|--------|------|-----------|----------|
| F-1 | COA Brief (finalized) | ✅ READY | `01_COA_366810\COA_BRIEF_366810_FINAL.pdf` | 50+ | PDF finalized |
| F-2 | COA Filing Stack (294 files) | ✅ READY | `01_FILINGS\COA_366810\` | 294 files | Comprehensive appellate package |
| F-3 | COA Docket Statement | ❌ NEEDED | — | 3-5 | Required for appeal initiation |
| F-4 | COA Emergency Stay Application | 📝 DRAFT | `01_FILINGS\COA_EMERGENCY_STAY\` | 15-20 | If needed |
| F-5 | COA APEX Filing Stack | 📝 DRAFT | `01_COA_366810\APEX_FILING_STACK\` | Variable | Production stack |
| F-6 | COA Draft Stack v2 | 📝 DRAFT | `01_FILINGS\COA_DRAFT_STACK_v2026-02-14_01\` | Variable | Updated draft |

**Lane F Next Steps:**
1. Create COA Docket Statement (F-3) — required form
2. Review Emergency Stay Application if custody situation escalates
3. Finalize APEX stack for production submission

---

## Lane G — Federal §1983 (W.D. Michigan)

**Case:** To be assigned — *Pigors v. [Defendants]*
**Court:** U.S. District Court, Western District of Michigan
**Basis:** 42 U.S.C. § 1983 — Civil Rights Violation

| # | Document | Status | Path | Est. Pages | Blockers |
|---|----------|--------|------|-----------|----------|
| G-1 | §1983 Complaint | ✅ READY | `03_FEDERAL_1983\` | 40+ | Drafts + production output |
| G-2 | Federal Filing Stack (181 files) | ✅ READY | `01_FILINGS\FEDERAL_1983\` | 181 files | Comprehensive package |
| G-3 | Consolidated Federal Complaint | ✅ READY | `01_FILINGS\FEDERAL_1983_CONSOLIDATED\` | 7 files | Consolidated version |
| G-4 | WDMI Full Stack | 📝 DRAFT | `03_FEDERAL_1983\WDMI_FULL_STACK\` | Variable | Western District package |
| G-5 | Federal APEX Stack | 📝 DRAFT | `03_FEDERAL_1983\APEX_FILING_STACK\` | Variable | Production stack |

**Lane G Status:** ✅ **SUBSTANTIALLY COMPLETE** — 181+ files across multiple stacks.

---

## Lane H — AGC (Attorney Grievance Commission)

**Target:** Attorney Berry (Barnes)
**Body:** Attorney Grievance Commission / State Bar of Michigan

| # | Document | Status | Path | Est. Pages | Blockers |
|---|----------|--------|------|-----------|----------|
| H-1 | Bar Complaint | ✅ READY | `05_BAR_BARNES\` | 30+ | Multiple versions in APEX + PRODUCTION |
| H-2 | Bar APEX Filing Stack | 📝 DRAFT | `05_BAR_BARNES\APEX_FILING_STACK\` | Variable | Production stack |
| H-3 | Bar Production Output | 📝 DRAFT | `05_BAR_BARNES\PRODUCTION_OUTPUT\` | Variable | Final production |

---

## Lane I — Disqualification (MCR 2.003)

**Basis:** MCR 2.003 — Disqualification of Judge
**Target:** Hon. Annette Smedley

| # | Document | Status | Path | Est. Pages | Blockers |
|---|----------|--------|------|-----------|----------|
| I-1 | Motion for Disqualification | ✅ READY | `01_FILINGS\DISQUALIFICATION\` | 15-20 | 6 files: motion, brief, affidavit, exhibits |
| I-2 | Affidavit of Bias | ✅ READY | `01_FILINGS\DISQUALIFICATION\AFFIDAVIT_OF_BIAS.md` | 8 | Included in package |
| I-3 | Statistical Analysis Exhibit | ✅ READY | `01_FILINGS\DISQUALIFICATION\STATISTICAL_ANALYSIS_EXHIBIT.md` | 5 | Included in package |

**Lane I Status:** ✅ **READY** — Complete disqualification package with supporting exhibits.

---

## Lane J — MSC (Michigan Supreme Court)

**Body:** Michigan Supreme Court

| # | Document | Status | Path | Est. Pages | Blockers |
|---|----------|--------|------|-----------|----------|
| J-1 | MSC Action Package | 📝 DRAFT | `01_FILINGS\MSC_ACTION\` | 36 files | Action package in progress |
| J-2 | MSC Filing Directory | ❌ NEEDED | `01_FILINGS\MSC\` | — | Empty directory — no filings yet |

---

## Cross-Lane Templates & Shared Documents

These documents are reusable across multiple filing lanes.

| # | Document | Type | Path | Used By |
|---|----------|------|------|---------|
| X-1 | MC 280 Proof of Service | 📄 TEMPLATE | `01_FILINGS\TEMPLATES\MC280_PROOF_OF_SERVICE.md` | All Lanes |
| X-2 | MC 97 Fee Waiver Application | 📄 TEMPLATE | `01_FILINGS\TEMPLATES\MC97_FEE_WAIVER_APPLICATION.md` | All Lanes |
| X-3 | Master Emily Watson Affidavit | ✅ READY | `01_FILINGS\MASTER_AFFIDAVITS\` | Lanes A, D, E |
| X-4 | Master Housing Affidavit | ✅ READY | `01_FILINGS\MASTER_AFFIDAVITS\09_AFFIDAVIT_ANDREW_PIGORS.md` | Lane B |
| X-5 | Master Exhibit Index | ✅ READY | `01_FILINGS\MASTER_AFFIDAVITS\02_EXHIBIT_INDEX_MASTER.md` | All Lanes |
| X-6 | Filing Checklist Template | ✅ READY | `01_FILINGS\MASTER_AFFIDAVITS\07_FILING_CHECKLIST.md` | All Lanes |
| X-7 | Andrew Pigors Action Checklist | 📝 DRAFT | `01_FILINGS\00_ANDREW_ACTION_CHECKLIST.md` | All Lanes |
| X-8 | QA Report (Final) | ✅ READY | `01_FILINGS\QA_REPORT_FINAL.md` | All Lanes |

---

## Evidence Base — NoReply Court Exports

7 court record PDFs exported from MiFile on 2024-10-26. **All are scanned images requiring OCR.**

| File | Size | Pages | Extracted Text | Type |
|------|------|-------|---------------|------|
| `NoReply_20241026_110612.pdf` | 6.42 MB | 61 | 1,316 chars | 🖼️ Scanned |
| `NoReply_20241026_110712.pdf` | 9.68 MB | 77 | 1,668 chars | 🖼️ Scanned |
| `NoReply_20241026_111342.pdf` | 1.58 MB | 13 | 260 chars | 🖼️ Scanned |
| `NoReply_20241026_111519.pdf` | 4.96 MB | 40 | 854 chars | 🖼️ Scanned |
| `NoReply_20241026_111809.pdf` | 16.17 MB | 64 | 1,382 chars | 🖼️ Scanned |
| `NoReply_20241026_112302.pdf` | 5.09 MB | 16 | 326 chars | 🖼️ Scanned |
| `NoReply_20241026_112736.pdf` | 4.36 MB | 100 | 2,174 chars | 🖼️ Scanned |

**Location:** `03_EVIDENCE\NoReply_Exports\`
**Extracted Text:** `temp\noreply_text\` (one .txt per PDF)
**Extraction Report:** `temp\noreply_text\NOREPLY_EXTRACTION_REPORT.md`

⚠️ **OCR Required:** All 371 pages are image-only scans. Run Tesseract OCR pipeline to extract full text content. These documents likely contain court orders, custody rulings, PPO records, and filed motions critical to Lanes A, D, and E.

---

## Filing Readiness Dashboard

| Lane | Label | Ready | Draft | Needed | Blocked | Overall |
|------|-------|-------|-------|--------|---------|---------|
| **A** | Custody | 2 | 2 | 2 | 0 | 🔨 IN PROGRESS |
| **B** | Housing | 13 | 0 | 0 | 0 | ✅ READY |
| **C** | Convergence | 0 | 2 | 0 | 0 | 📝 DRAFT |
| **D** | PPO | 1 | 0 | 1 | 0 | 🔨 IN PROGRESS |
| **E** | JTC | 4 | 2 | 0 | 0 | ✅ SUBSTANTIALLY READY |
| **F** | COA 366810 | 2 | 3 | 1 | 0 | 📝 MOSTLY READY |
| **G** | Federal §1983 | 3 | 2 | 0 | 0 | ✅ SUBSTANTIALLY READY |
| **H** | AGC / Bar | 1 | 2 | 0 | 0 | ✅ SUBSTANTIALLY READY |
| **I** | Disqualification | 3 | 0 | 0 | 0 | ✅ READY |
| **J** | MSC | 0 | 1 | 1 | 0 | 📋 EARLY STAGE |

**Totals:** 29 READY · 14 DRAFT · 5 NEEDED · 0 BLOCKED

---

## Priority Actions

### Immediate (This Week)
1. **Lane A:** Finalize Emergency Motion to Restore Parenting Time
2. **Lane A:** Complete Motion for Contempt exhibit package
3. **Lane D:** Obtain CC 380 form, draft Response to PPO
4. **OCR:** Run Tesseract on 7 NoReply PDFs (371 pages) for evidence extraction

### Short-Term (Next 2 Weeks)
5. **Lane F:** Create COA Docket Statement
6. **Lane A:** Obtain FOC 65 and FOC 66 forms
7. **Lane A:** File MC 97 Fee Waiver if needed
8. **Cross-Lane:** Run pre-filing QA sweep on all READY packages

### Medium-Term (30 Days)
9. **Lane A:** Motion to Modify Custody (after emergency motions resolved)
10. **Lane G:** File federal §1983 complaint
11. **Lane E:** Submit JTC complaint package
12. **Lane H:** Submit bar complaint to AGC

---

## Manifest Metadata

- **Total Documents Tracked:** 48+ primary filings
- **Total Files in System:** 1,750+ across all filing directories
- **Lanes Active:** 10 (A through J)
- **Court Systems:** 14th Circuit (Muskegon), Michigan COA, Michigan Supreme Court, W.D. Michigan Federal, JTC, AGC
- **Last Updated:** 2026-03-11
- **Source of Truth:** This manifest + `litigation_context.db`
