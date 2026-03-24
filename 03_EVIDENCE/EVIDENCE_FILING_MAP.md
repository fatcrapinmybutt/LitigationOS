# Evidence-to-Filing Mapping — Pigors v. Watson (LitigationOS)

> **All data from `litigation_context.db` tables: `filing_readiness`, `claims`, `filing_packages`, `evidence_exhibits`, `exhibit_index`.**
> No fabricated entries. Statistics are DB-verified.

---

## Filing Packages Overview

Source: `SELECT * FROM filing_readiness ORDER BY filing_id`

| Filing ID | Vehicle Name | Lane | Case Number | Readiness | Exhibit Count | Status |
|-----------|-------------|------|-------------|----------:|-------------:|--------|
| F1 | Emergency TRO / Custody Motion | A | 2024-001507-DC | 75% | 12 | ingested |
| F2 | Shady Oaks Housing Complaint | B | 2025-002760-CZ | 75% | 11 | ingested |
| F3 | Motion to Disqualify Judge McNeill (MCR 2.003) | A | 2024-001507-DC | 75% | 13 | ingested |
| F4 | Federal §1983 Civil Rights Complaint | A | NEW | 75% | 12 | ingested |
| F5 | Michigan Supreme Court Original Action | F | NEW | 75% | 12 | ingested |
| F6 | Judicial Tenure Commission Complaint | E | NEW | 75% | 11 | ingested |
| F7 | Motion for Custody Modification | A | 2024-001507-DC | 75% | 13 | ingested |
| F8 | Motion to Terminate PPO | D | 2023-5907-PP | 75% | 12 | ingested |
| F9 | Court of Appeals Brief on Appeal | F | COA-366810 | 75% | 11 | ingested |
| F10 | Court of Appeals Emergency Motion | F | COA-366810 | 75% | 11 | ingested |

---

## Evidence → Filing Map

### F1: Emergency TRO / Custody Motion (Lane A)

| Evidence Item | Source Table | Lane | Exhibit Category | Bates Range | Status |
|---------------|-------------|------|-----------------|-------------|--------|
| Ex parte order 8/8/25 (parenting time suspension) | evidence_quotes | A | Court Orders | PIGORS-F01-0001+ | ✅ Indexed |
| AppClose interference logs (305+ incidents) | evidence_exhibits (EX-APPCLOSE-305) | A | Communication Records | PIGORS-F01-0486+ | ✅ Indexed |
| HealthWest Evaluation H0002 (favorable) | evidence_exhibits (H0002) | A | Medical/Evaluation | PIGORS-F01-2037+ | ✅ Indexed |
| Albert+Emily kitchen recording transcript | evidence_exhibits (EX-ALBERT-AUDIO) | A | Audio/Transcript | — | ⚠️ Need exhibit # |
| Parenting time denial calendar | GENERATED_EXHIBITS (U-007) | A | Timeline | — | ✅ Generated |
| Show cause history | GENERATED_EXHIBITS (U-005) | A | Procedural History | — | ✅ Generated |
| Interference incident log | GENERATED_EXHIBITS (U-001) | A | Pattern Evidence | — | ✅ Generated |

**Claims supported:** A-EMRG-CUST (5,730 items), A-PT-ENFORCE (1,149 items)

**Exhibit binder structure (from exhibit_index):**
- Exhibit A: Judicial Conduct — 485 items (PIGORS-F01-0001 to 0485)
- Exhibit B: Custody/Alienation — 584 items (PIGORS-F01-0486 to 1069)
- Exhibit C: Credibility/Impeachment — 807 items (PIGORS-F01-1070 to 1876)
- Exhibit D: Financial — 160 items (PIGORS-F01-1877 to 2036)
- Exhibit E: Medical/Welfare — 84 items (PIGORS-F01-2037 to 2120)
- Exhibit F: Citations/Authority — 146 items (PIGORS-F01-2121 to 2266)
- Exhibit G: General Evidence — 106 items (PIGORS-F01-2267 to 2372)

---

### F2: Shady Oaks Housing Complaint (Lane B)

| Evidence Item | Source Table | Lane | Exhibit Category | Status |
|---------------|-------------|------|-----------------|--------|
| Lease/rental agreements | evidence_quotes | B | Property Records | ⚠️ Need originals |
| Property condition documentation | evidence_quotes | B | Photos/Condition | ⚠️ Need current photos |
| Utility shutoff records | evidence_quotes | B | Utility Records | ⚠️ Need provider records |
| Title/deed records | evidence_quotes | B | Public Records | ⚠️ Need certified copies |
| Payment ledgers | evidence_quotes | B | Financial | ⚠️ Need verification |
| Sewage/habitability evidence | evidence_quotes | B | Code Violations | ⚠️ Need inspection reports |

**Claims supported:** B-CONSTR-FRAUD (20,597), B-LEASE-FRAUD (20,590), B-RETALIATION (7,110), B-HABITABILITY (6,927), B-PROPERTY-DEST (6,934), B-UTILITY (6,927)

---

### F3: Motion to Disqualify Judge McNeill — MCR 2.003 (Lane A/E)

| Evidence Item | Source Table | Lane | Exhibit Category | Status |
|---------------|-------------|------|-----------------|--------|
| Ex parte orders entered without notice | judicial_violations (3,697 ex_parte) | E | Due Process | ✅ Documented |
| Bias pattern analysis | judicial_violations (1,076 bias) | E | Judicial Conduct | ✅ Documented |
| Hostile record practices | evidence_quotes (14,484 items) | E | Record Practices | ✅ Documented |
| HealthWest evaluation exclusion | evidence_exhibits (H0002) | A/E | Excluded Evidence | ✅ Indexed |
| Denial of hearing instances | judicial_violations (19 denial_of_hearing) | E | Procedural Violations | ✅ Documented |
| Canon violations | judicial_violations (29 canon_violation) | E | Ethical Violations | ⚠️ Need specific citations |
| Judicial conduct analysis | GENERATED_EXHIBITS (U-015) | E | Analysis | ✅ Generated |
| Ex parte order log | GENERATED_EXHIBITS (U-013) | E | Timeline | ✅ Generated |

**Claims supported:** E-DISQUALIFY (11,800), E-EX-PARTE (11,807), E-HOSTILE-RECORD (14,484)

**Exhibit binder structure:**
- Exhibit A: Constitutional/Due Process — 165 items
- Exhibit B: Judicial Conduct — 126 items
- Exhibit C: Custody/Alienation — 318 items
- Exhibit D: Credibility/Impeachment — 781 items
- Exhibit E: Timeline/Witness — 185 items
- Exhibit F: Citations/Authority — 248 items

---

### F4: Federal §1983 Civil Rights Complaint (Lane A)

| Evidence Item | Source Table | Lane | Exhibit Category | Status |
|---------------|-------------|------|-----------------|--------|
| Due process violations | evidence_quotes | A/E | Constitutional | ✅ Documented |
| Equal protection violations | claims (FED-EQUAL-PROT, 15,195) | A | Constitutional | ✅ Documented |
| Fourth Amendment seizure | claims (FED-4A-SEIZURE, 12,166) | A | Constitutional | ✅ Documented |
| First Amendment retaliation | claims (FED-1A-RETAL, 7,063) | A | Constitutional | ✅ Documented |
| Pattern of constitutional violations | evidence_quotes | A/E | Pattern Evidence | ✅ Documented |
| Ella Randall Report NS2505044 | evidence_exhibits | D/E | **SMOKING GUN** | ✅ Located |

**Claims supported:** FED-1983 (24,478), FED-EQUAL-PROT (15,195), FED-4A-SEIZURE (12,166), FED-DUE-PROCESS (6,071), FED-1A-RETAL (7,063)

---

### F5: Michigan Supreme Court Original Action (Lane F)

| Evidence Item | Source Table | Lane | Exhibit Category | Status |
|---------------|-------------|------|-----------------|--------|
| Lower court record compilation | multiple | A/D/E | Full Record | ⚠️ Need certified copies |
| Constitutional violations | evidence_quotes | E/F | Constitutional | ✅ Documented |
| Superintending control basis | claims (F-SUPER-CTRL, 17,866) | F | Jurisdictional | ✅ Documented |
| Extraordinary circumstances | evidence_quotes | A/E/F | Emergency | ✅ Documented |

**Claims supported:** F-MSC-ORIG (17,866), F-SUPER-CTRL (17,866), F-MSC-BYPASS (15,183)

---

### F6: Judicial Tenure Commission Complaint (Lane E)

| Evidence Item | Source Table | Lane | Exhibit Category | Status |
|---------------|-------------|------|-----------------|--------|
| Judicial violations database | judicial_violations (5,063 total) | E | Full Violation Log | ✅ Documented |
| Ex parte communications | judicial_violations (3,697 ex_parte) | E | Ex Parte Log | ✅ Documented |
| Bias incidents | judicial_violations (1,076 bias) | E | Bias Evidence | ✅ Documented |
| Canon violations | judicial_violations (29 canon_violation) | E | Ethics | ⚠️ Need specifics |
| Improper procedures | judicial_violations (37 improper_procedure) | E | Procedural | ✅ Documented |

**Claims supported:** E-JTC (4,339)

---

### F7: Motion for Custody Modification (Lane A)

| Evidence Item | Source Table | Lane | Exhibit Category | Status |
|---------------|-------------|------|-----------------|--------|
| Albert+Emily kitchen VIDEO | evidence_exhibits (EX-ALBERT-VIDEO) | A | **KEY — Audio/Video** | ✅ Located at I:\02_EVIDENCE\...\Albertemily.mp4 (1.35 GB) |
| Albert+Emily kitchen AUDIO | evidence_exhibits (EX-ALBERT-AUDIO) | A | **KEY — Audio** | ✅ Located at I:\04_MEDIA\...\Albert.mp3 (14.86 MB) |
| Albert+Emily transcript | evidence_exhibits | A | Transcript | ✅ Located |
| Change of circumstances evidence | evidence_quotes | A | Best Interest Factors | ✅ Documented |
| Parenting time interference log | evidence_quotes | A | Pattern Evidence | ✅ Documented |
| Child welfare concerns for L.D.W. | claims (A-CHILD-WELF, 1,770) | A | Child Welfare | ⚠️ Need corroboration |
| MRE 901 analysis | GENERATED_EXHIBITS (U022) | A | Authentication | ✅ Generated |

**Claims supported:** A-CUST-MOD (6,233), A-CHILD-WELF (1,770), A-FALSE-ALLEG (2,488)

---

### F8: Motion to Terminate PPO (Lane D)

| Evidence Item | Source Table | Lane | Exhibit Category | Status |
|---------------|-------------|------|-----------------|--------|
| False allegations evidence | claims (D-FALSE-ALLEG-PPO, 5,063) | D | Impeachment | ✅ Documented |
| PPO weaponization pattern | claims (D-PPO-WEAPON, 4,008) | D | Pattern Evidence | ✅ Documented |
| Albert+Emily recording (threats) | evidence_exhibits | A/D | **KEY — Impeachment** | ✅ Located |
| MCL 750.539 analysis | GENERATED_EXHIBITS (U021) | D | Legal Analysis | ✅ Generated |
| Police report contradictions | evidence_quotes | D | Impeachment | ⚠️ Need compilation |

**Claims supported:** D-PPO-TERM (3,979), D-FALSE-ALLEG-PPO (5,063), D-PPO-WEAPON (4,008)

---

### F9: Court of Appeals Brief on Appeal (Lane F)

| Evidence Item | Source Table | Lane | Exhibit Category | Status |
|---------------|-------------|------|-----------------|--------|
| Appellate record | multiple | All | Complete Record | ⚠️ Need compilation |
| Issues for appeal | claims (F-COA-APPEAL, 17,875) | F | Legal Arguments | ✅ Documented |
| Lower court error analysis | judicial_violations | E | Error Log | ✅ Documented |
| Constitutional issues | evidence_quotes | A/E/F | Constitutional | ✅ Documented |

**Claims supported:** F-COA-APPEAL (17,875)

---

### F10: Court of Appeals Emergency Motion (Lane F)

| Evidence Item | Source Table | Lane | Exhibit Category | Status |
|---------------|-------------|------|-----------------|--------|
| Emergency circumstances | evidence_quotes | A/F | Emergency | ✅ Documented |
| Irreparable harm to L.D.W. | claims (F-EMRG-STAY, 8,774) | F | Child Welfare | ✅ Documented |
| Stay pending appeal basis | evidence_quotes | F | Legal | ✅ Documented |

**Claims supported:** F-EMRG-STAY (8,774)

---

## Critical Evidence Items Referenced Across Multiple Filings

| Evidence Item | Filings | Lanes | Authentication |
|---------------|---------|-------|---------------|
| **Albert+Emily Kitchen VIDEO** (Albertemily.mp4, 1.35 GB) | F1, F3, F7, F8 | A, D, E | MRE 901(a) — ⚠️ need foundation |
| **Albert+Emily Kitchen AUDIO** (Albert.mp3, 14.86 MB) | F1, F3, F7, F8 | A, D, E | MRE 901(a) — ⚠️ need foundation |
| **NS2505044 Ella Randall Report** | F3, F4, F5, F6 | D, E | Official record — ✅ |
| **HealthWest Evaluation H0002** | F1, F3, F7 | A, E | Official record — ⚠️ need certified copy |
| **AppClose Logs (305+ incidents)** | F1, F7, F8 | A | Business records MRE 803(6) — ⚠️ need certification |
| **Ex parte order 8/8/25** | F1, F3, F5, F9, F10 | A, E, F | Court record — ✅ self-authenticating |

---

## Evidence Readiness Summary

| Filing | Total Evidence Items | Exhibits Indexed | Authentication Ready | Overall Readiness |
|--------|--------------------:|----------------:|:-------------------:|:-----------------:|
| F1 | 6,879+ | 2,372 | Partial | 75% |
| F2 | 69,085+ | — | Partial | 75% |
| F3 | 38,091+ | 1,823 | Partial | 75% |
| F4 | 64,973+ | — | Partial | 75% |
| F5 | 50,915+ | — | Partial | 75% |
| F6 | 5,063+ | — | Partial | 75% |
| F7 | 10,491+ | — | Partial | 75% |
| F8 | 13,050+ | — | Partial | 75% |
| F9 | 17,875+ | — | Partial | 75% |
| F10 | 8,774+ | — | Partial | 75% |

> **Note:** Readiness scores from `filing_readiness` table. All filings at "ingested" status with 75% readiness. Key blockers: exhibit authentication, authority chain verification, and final QA pass.
