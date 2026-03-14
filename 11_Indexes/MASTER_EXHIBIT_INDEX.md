# MASTER EXHIBIT INDEX — PIGORS v. WATSON LITIGATION
## All Clerk-Ready Filings — Unified Cross-Reference

**Generated:** 2026-03-15
**Case Numbers:** 2024-001507-DC | 2023-5907-PP | COA 366810
**Pro Se Plaintiff:** Andrew James Pigors

---

## CRITICAL NOTE: EXHIBIT LETTER COLLISION MAP

Different filings assign DIFFERENT letters to the SAME or DIFFERENT documents.
This index uses a **Unified ID** (U-001 through U-999) as the master key.
Each filing's local exhibit letter is mapped below.

### Legend

| Column | Meaning |
|--------|---------|
| **UID** | Unified exhibit ID (stable across all filings) |
| **F1** | 01_EMERGENCY_PT_MOTION.md letter |
| **F2** | 02_DISQUALIFICATION_MOTION.md letter |
| **F3** | 03_CONTEMPT_MOTION.md letter |
| **F5** | MOTION_DISQUALIFICATION_MCNEILL.md letter |
| **F6** | MOTION_DISSOLVE_PPO.md letter |
| **Status** | ✅ FILE EXISTS | ⚠️ PARTIAL | ❌ MISSING |

---

## SECTION 1: UNIFIED EXHIBIT TABLE

| UID | Description | F1 | F2 | F3 | F5 | F6 | Status | File Location |
|-----|-------------|----|----|----|----|----|----|---------------|
| U-001 | **Interference Incident Log (305+ incidents)** | A | — | D | — | — | ❌ MISSING | Generate from `litigation_context.db → evidence_quotes WHERE category='interference'` |
| U-002 | **NSPD Report NS2505044 (Albert Watson Statement)** | B | F | A | — | — | ✅ EXISTS | `03_EVIDENCE\Police_Reports\NSPD\` (26 PDFs) + `10_Exhibits\AudioVideo\nspd police reports.zip` |
| U-003 | **PPO 2023-05907-PP Docket ("NOT SERVED" Status)** | C | H | H | — | — | ⚠️ PARTIAL | `10_Exhibits\Images\docket screenshot.jpg` (one image only) |
| U-004 | **Negative Poisoning Test Result** | D | — | B | — | — | ❌ MISSING | Andrew must provide original lab report |
| U-005 | **Show Cause History Summary (7 Proceedings)** | E | G | F | — | — | ❌ MISSING | Generate from `litigation_context.db → docket_events WHERE event_type LIKE '%show_cause%'` |
| U-006 | **Employment Loss Documentation (2 Jobs, 2 Homes)** | F | I | G | — | — | ❌ MISSING | Andrew must provide pay stubs, termination letters, eviction notices |
| U-007 | **Parenting Time Denial Calendar (229+ Days)** | G | J | C | — | — | ❌ MISSING | Generate from `litigation_context.db → docket_events WHERE event_type='parenting_time'` |
| U-008 | **USB Recording Chain of Custody** | H | — | I | AG | — | ❌ MISSING | Andrew must provide chain-of-custody documentation |
| U-009 | **HealthWest Evaluation #1 (ALL ZEROS — Clearing Father)** | I | — | J | I | — | ✅ EXISTS | `I:\!!!TEXT!!!\Exhibit_M_HealthWest_v10.pdf` (3 MB) — ALSO: `03_EVIDENCE\EXHIBITS\` older version `healthwest08052025.pdf` per CSV |
| U-010 | **HealthWest Evaluation — Parental Alienation Documented** | J | — | K | J | — | ⚠️ PARTIAL | Part of same HealthWest report; specific pages TBD |
| U-011 | **Second Evaluation Routed to Secretary (Not Clerk)** | K | — | — | K | — | ❌ MISSING | Andrew must provide proof of routing (email, delivery receipt) |
| U-012 | **Transcript — "Ghost Evaluation" / "I Had My Staff Listen"** | L | — | L | L | C | ❌ MISSING | Must obtain certified transcript from court reporter |
| U-013 | **Ex Parte Order Log (24/55 = 44%)** | M | — | — | P | — | ❌ MISSING | Generate from `litigation_context.db → docket_events WHERE event_type='ex_parte_order'` |
| U-014 | **Affidavit of Bias (MCR 2.003(D)(1))** | — | A | — | — | — | ✅ EXISTS | `01_FILINGS\CLERK_READY\AFFIDAVIT_OF_DISQUALIFICATION.md` |
| U-015 | **Statistical Analysis of Judicial Conduct** | — | B | — | — | — | ❌ MISSING | Generate from `litigation_context.db → judicial_violations` aggregate query |
| U-016 | **Hearing Transcript — Muting Incidents (3 Occasions)** | — | C | — | — | — | ❌ MISSING | Must obtain certified transcript |
| U-017 | **Order Imposing $250 Filing Bond** | — | D | — | S | — | ❌ MISSING | Must obtain certified copy from court clerk |
| U-018 | **Hearing Transcript — AI Research Disparagement** | — | E | — | — | — | ❌ MISSING | Must obtain certified transcript |
| U-019 | **August 8, 2025 Five Ex Parte Orders** | — | — | — | Q | — | ❌ MISSING | Must obtain certified copies from court clerk |
| U-020 | **Transcript Excerpt — USB Review Admission** | — | — | — | R | — | ❌ MISSING | Must obtain certified transcript |
| U-021 | **MCL 750.539 Felony Wiretapping Analysis** | — | — | — | AH | — | ❌ MISSING | Generate legal analysis document |
| U-022 | **MRE 901 Authentication Failure Analysis** | — | — | — | AI | — | ❌ MISSING | Generate legal analysis document |
| U-023 | **Court Orders Referencing Undisclosed 2nd HealthWest Eval** | — | — | — | AK | — | ❌ MISSING | Must obtain certified copies from court clerk |
| U-024 | **Final Judgment of Custody/PT (July 17, 2024)** | — | — | E | — | — | ❌ MISSING | Must obtain certified copy from court clerk |
| U-025 | **Hearing Transcript, October 30, 2024** | — | — | — | — | C | ✅ EXISTS | `Exhibit_Index.csv → Ex. B: Pigors Transcript. Partial Excerpts Only 10.30.24.pdf` (334 KB) |
| U-026 | **Lori Watson Ultimatum Text Message (03/25/2024)** | — | — | — | — | — | ✅ EXISTS | `Exhibit_Index.csv → Ex. E: LoriUltimatum1_20250107182654.png` (395 KB) |
| U-027 | **Outlook Printouts Image Stack** | — | — | — | — | — | ✅ EXISTS | `Exhibit_Index.csv → Ex. H: file-8BZuukf7YyxMWPQQo78UrZ.jpg` (292 KB) |

---

## SECTION 2: EXISTING EXHIBIT FILES ON DISK

### 2A. 03_EVIDENCE\EXHIBITS\ (Shady Oaks / Housing Lane B — 43 files)

| File | Description | Lane |
|------|-------------|------|
| Exhibit_A_LARA_Dissolution.pdf | LARA Dissolution of Shady Oaks LLC | B |
| Exhibit_B_Lease_Agreement.pdf | Lease Agreement | B |
| Exhibit_B_Court_Filings_Post_Dissolution.pdf | Post-dissolution court filings | B |
| Exhibit_C_Email_Exchange.pdf | Email exchange evidence | B |
| Exhibit_C_Lease_Under_Duress.pdf | Lease under duress | B |
| Exhibit_D_EGLE_Report.pdf | EGLE environmental report | B |
| Exhibit_D_Ledger_and_Communications.pdf | Ledger and communications | B |
| Exhibit_E1_LARA_Certification.pdf | LARA certification (7.5 MB) | B |
| Exhibit_E_Sewage_Water_Photos.pdf | Sewage/water photos | B |
| Exhibit_F_Utility_Billing.pdf | Utility billing records | B |
| Exhibit_G_CT_Corp_Mismatch.pdf | CT Corp registered agent mismatch | B |
| Exhibit_H_Tenant_Advocacy_Flyer.pdf | Tenant advocacy flyer | B |
| Exhibit_I_July_Receipts_Combo.pdf | July receipts | B |
| Exhibit_J_Custody_Order.pdf | Custody order | A/B |
| Exhibit_AA_Damages_Matrix.pdf | Economic damages matrix | B |

> **⚠️ WARNING:** These are LANE B (Shady Oaks housing) exhibits. They use the SAME letters (A-J) as the custody filings but refer to COMPLETELY DIFFERENT documents. Do NOT confuse them.

### 2B. 10_Exhibits\ (Custody Lane A — Mixed)

| File | Description | Lane |
|------|-------------|------|
| `AudioVideo\nspd police reports.zip` | NSPD police reports archive (16.9 MB) | A |
| `Images\docket screenshot.jpg` | Docket screenshot (80 KB) | A |
| `PDFs\` | (empty) | — |

### 2C. 03_EVIDENCE\Police_Reports\NSPD\ (26 individual PDFs)

All NSPD police report pages, extracted and ready for filing.

### 2D. I:\!!!TEXT!!!\ (Backup — Key Files)

| File | Description |
|------|-------------|
| Exhibit_M_HealthWest_v10.pdf | HealthWest evaluation (3 MB) — PRIMARY COPY |
| exhibitMhealthwest.pdf | HealthWest full version (5.7 MB) |
| SCANNEDMergeddocketsnotices_*.pdf | Merged docket/notices (2.7 MB) |
| healthwest_0001.pdf through healthwest_0082.pdf | 82 scanned pages |

### 2E. 11_Indexes\Exhibit_Index.csv (Prior Index — 6 Exhibits Catalogued)

| CSV ID | File | SHA256 (prefix) |
|--------|------|-----------------|
| Ex. A | healthwest08052025.pdf | 321657cf |
| Ex. B | Pigors Transcript...10.30.24.pdf | 9d94cc18 |
| Ex. C | docket screenshot.jpg | 9caeb09d |
| Ex. E | LoriUltimatum1_20250107182654.png | e9784a26 |
| Ex. G | nspd police reports.zip | f9be6eb5 |
| Ex. H | file-8BZuukf7YyxMWPQQo78UrZ.jpg | a513056d |

---

## SECTION 3: GAP ANALYSIS — WHAT'S MISSING

### Tier 1: CAN GENERATE FROM DATABASE (no human input needed)

| UID | Document | Generation Method |
|-----|----------|-------------------|
| U-001 | Interference Incident Log | `SELECT * FROM evidence_quotes WHERE category LIKE '%interference%' ORDER BY date` |
| U-005 | Show Cause History Summary | `SELECT * FROM docket_events WHERE event_type LIKE '%show_cause%' OR event_type LIKE '%contempt%'` |
| U-007 | Parenting Time Denial Calendar | `SELECT * FROM docket_events WHERE event_type='parenting_time'` + compute day counts |
| U-013 | Ex Parte Order Log | `SELECT * FROM docket_events WHERE event_type='ex_parte_order'` + statistics |
| U-015 | Statistical Analysis of Judicial Conduct | `SELECT severity, COUNT(*) FROM judicial_violations GROUP BY severity` |
| U-021 | MCL 750.539 Analysis | Legal analysis document — can draft from statute text |
| U-022 | MRE 901 Authentication Analysis | Legal analysis document — can draft from rule text |

### Tier 2: MUST OBTAIN FROM COURT CLERK ($1.25/page certified)

| UID | Document | Source |
|-----|----------|--------|
| U-012 | Transcript — "Ghost Evaluation" | Court reporter (date TBD) |
| U-016 | Transcript — Muting incidents | Court reporter (Nov 15, 2024 hearing) |
| U-017 | Filing Bond Order (May 16, 2025) | 14th Circuit Court Clerk |
| U-018 | Transcript — AI disparagement | Court reporter (date TBD) |
| U-019 | Five Ex Parte Orders (Aug 8, 2025) | 14th Circuit Court Clerk |
| U-020 | Transcript — USB admission | Court reporter (date TBD) |
| U-023 | Orders referencing 2nd HealthWest eval | 14th Circuit Court Clerk |
| U-024 | Custody Judgment (July 17, 2024) | 14th Circuit Court Clerk |

### Tier 3: MUST BE PROVIDED BY ANDREW

| UID | Document | Notes |
|-----|----------|-------|
| U-004 | Negative Poisoning Test Result | Original lab report from testing facility |
| U-006 | Employment Loss Documentation | Pay stubs, termination letters, lease terminations |
| U-008 | USB Recording Chain of Custody | Documentation of who had the USB and when |
| U-011 | Proof of Secretary Routing | Email/receipt showing eval went to judge's secretary |

---

## SECTION 4: FILING-SPECIFIC EXHIBIT CHECKLISTS

### ✅ Disqualification Package (F2 + F5 + Affidavit)
**Due: March 15, 2026**

| F2 Letter | F5 Letter | UID | Document | Status |
|-----------|-----------|-----|----------|--------|
| A | — | U-014 | Affidavit of Bias | ✅ CREATED |
| B | — | U-015 | Statistical Analysis | ❌ Generate |
| C | — | U-016 | Transcript — Muting | ❌ Court clerk |
| D | S | U-017 | Filing Bond Order | ❌ Court clerk |
| E | — | U-018 | Transcript — AI | ❌ Court clerk |
| F | — | U-002 | NSPD Report | ✅ EXISTS |
| G | — | U-005 | Show Cause Summary | ❌ Generate |
| H | — | U-003 | PPO Docket | ⚠️ PARTIAL |
| I | — | U-006 | Employment Loss | ❌ Andrew |
| J | — | U-007 | PT Denial Calendar | ❌ Generate |
| — | P | U-013 | Ex Parte Order Log | ❌ Generate |
| — | Q | U-019 | Aug 8 Ex Parte Orders | ❌ Court clerk |
| — | R | U-020 | Transcript — USB | ❌ Court clerk |
| — | I | U-009 | HealthWest Eval #1 | ✅ EXISTS |
| — | J | U-010 | HealthWest — Alienation | ⚠️ PARTIAL |
| — | K | U-011 | Secretary Routing | ❌ Andrew |
| — | L | U-012 | Transcript — Ghost | ❌ Court clerk |
| — | AG | U-008 | USB Chain of Custody | ❌ Andrew |
| — | AH | U-021 | MCL 750.539 Analysis | ❌ Generate |
| — | AI | U-022 | MRE 901 Analysis | ❌ Generate |
| — | AK | U-023 | Orders re: 2nd Eval | ❌ Court clerk |

**Score: 4/21 ready (19%), 5 generatable, 7 need court clerk, 3 need Andrew**

### ✅ Emergency PT Motion (F1)

| F1 Letter | UID | Status |
|-----------|-----|--------|
| A | U-001 | ❌ Generate |
| B | U-002 | ✅ EXISTS |
| C | U-003 | ⚠️ PARTIAL |
| D | U-004 | ❌ Andrew |
| E | U-005 | ❌ Generate |
| F | U-006 | ❌ Andrew |
| G | U-007 | ❌ Generate |
| H | U-008 | ❌ Andrew |
| I | U-009 | ✅ EXISTS |
| J | U-010 | ⚠️ PARTIAL |
| K | U-011 | ❌ Andrew |
| L | U-012 | ❌ Court clerk |
| M | U-013 | ❌ Generate |

**Score: 2/13 ready (15%), 4 generatable, 1 court clerk, 4 need Andrew**

### ✅ Contempt Motion (F3)

| F3 Letter | UID | Status |
|-----------|-----|--------|
| A | U-002 | ✅ EXISTS |
| B | U-004 | ❌ Andrew |
| C | U-007 | ❌ Generate |
| D | U-001 | ❌ Generate |
| E | U-024 | ❌ Court clerk |
| F | U-005 | ❌ Generate |
| G | U-006 | ❌ Andrew |
| H | U-003 | ⚠️ PARTIAL |
| I | U-008 | ❌ Andrew |
| J | U-009 | ✅ EXISTS |
| K | U-010 | ⚠️ PARTIAL |
| L | U-012 | ❌ Court clerk |

**Score: 2/12 ready (17%), 3 generatable, 2 court clerk, 3 need Andrew**

---

## SECTION 5: IMMEDIATE ACTION ITEMS

### 🔴 AUTOMATED (Copilot can generate now)
1. Interference Incident Log (U-001)
2. Show Cause History Summary (U-005)
3. Parenting Time Denial Calendar (U-007)
4. Ex Parte Order Log with statistics (U-013)
5. Statistical Analysis of Judicial Conduct (U-015)
6. MCL 750.539 Analysis (U-021)
7. MRE 901 Authentication Analysis (U-022)

### 🟡 ANDREW ACTION REQUIRED
8. Provide poisoning test result (U-004)
9. Provide employment loss documentation (U-006)
10. Provide USB chain of custody (U-008)
11. Provide secretary routing proof (U-011)

### 🔵 COURT CLERK REQUESTS ($1.25/page)
12. Request certified transcripts (U-012, U-016, U-018, U-020) — multiple hearing dates
13. Request certified orders (U-017, U-019, U-023, U-024) — specific order dates
14. **Pro tip:** File MC 20 Fee Waiver to avoid transcript/certification costs

---

*This index supersedes all prior exhibit references. When filing, use this index to map unified IDs back to each filing's local exhibit letter.*
