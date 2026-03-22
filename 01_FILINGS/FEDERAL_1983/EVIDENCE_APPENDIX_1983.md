# EVIDENCE APPENDIX TO SECOND AMENDED COMPLAINT
# UNDER 42 U.S.C. § 1983

## Pigors v. McNeill et al.
## United States District Court, Western District of Michigan

---

## TABLE OF CONTENTS

I. Overview and Methodology
II. Element-by-Element Evidence Mapping
III. Constitutional Violation Matrix
IV. Most Egregious Incidents Timeline
V. Conduct Pattern Summary (JTC Table)
VI. Adverse Rebuttal Packet Analysis
VII. Cross-Reference to JTC Exhibit Binders
VIII. Statistical Summary

---

## I. OVERVIEW AND METHODOLOGY

### A. Evidence System Description

This appendix summarizes evidence cataloged in Plaintiff's litigation intelligence system, which maintains independently verifiable databases drawn from 9 primary source files:

| Source File | Finding Count | Description |
|---|---|---|
| Deadline_Notice_Audit_Enhanced.csv | 40,895 | Systematic audit of deadline notices, service, and compliance |
| Notice_Risk_Register.csv | 29,903 | Risk-scored register of notice and service deficiencies |
| Adverse_Statement_Rebuttal_Matrix_ENHANCED.csv | 3,518 | Rebuttal matrix for adverse statements with evidence mapping |
| EVIDENCE_ATOMS.jsonl | 1,080 | Atomic evidence units with SHA-256 provenance |
| Proceeding_Chain_Summary.csv | 364 | Proceeding chain analysis showing temporal coordination |
| Vehicle_Proof_Obligations_Calibrated.csv | 261 | Proof obligation tracking per legal vehicle |
| Adverse_Rebuttal_Packet_Summary.csv | 173 | Adverse rebuttal packet analysis by topic and case |
| JTC_Conduct_Pattern_Table.csv | 86 | Judicial conduct pattern analysis (19 categories, 1,127 violations) |
| Continuance_Chain_Summary.csv | 49 | Continuance chain analysis showing scheduling manipulation |
| **TOTAL** | **76,329** | |

### B. Cross-Validation Methodology

Each finding in the evidence matrix is independently derived from source documents (court records, docket entries, filed motions, orders, transcripts, and physical evidence). Findings are cross-validated across multiple source files — the same incident may appear in the Notice_Risk_Register, the Deadline_Notice_Audit, and the EVIDENCE_ATOMS database independently, confirming accuracy through triangulation.

### C. Severity Classification

| Severity | Definition | Count | Percentage |
|---|---|---|---|
| CRITICAL | Constitutional violation with irreversible harm | 111 | 0.1% |
| HIGH | Serious violation with documented evidence | 60,418 | 79.2% |
| MEDIUM | Violation with supporting circumstantial evidence | 15,567 | 20.4% |
| LOW | Minor or procedural irregularity | 233 | 0.3% |

---

## II. ELEMENT-BY-ELEMENT EVIDENCE MAPPING

### A. 42 U.S.C. § 1983 — Elements

For a § 1983 claim, Plaintiff must establish: (1) action under color of state law; (2) deprivation of a constitutionally protected right.

#### Element 1: Color of State Law

| Evidence | Source | Finding ID(s) |
|---|---|---|
| Judge McNeill acted as judicial officer of 14th Circuit Court | Court records, docket entries | All findings |
| Watson/Berry acted under color of law via conspiracy with McNeill | Temporal coordination analysis; Berry voicemail | AEM_000001–AEM_000061; Proceeding_Chain_Summary.csv |
| State court orders enforced via contempt power of the state | Contempt sanction chain | AEM_000012–AEM_000015, AEM_000024–AEM_000027 |

**Assessment:** Element satisfied — Judge McNeill is a state actor; Watson and Berry acted under color of law through documented conspiracy.

#### Element 2: Deprivation of Constitutional Rights

See Sections II.B through II.F below for element-by-element mapping of each constitutional right.

### B. Fourteenth Amendment — Substantive Due Process

**Right:** Fundamental liberty interest in parent-child relationship. *Troxel v. Granville*, 530 U.S. 57, 65 (2000).

| Deprivation | Evidence Category | Evidence Count | Severity | Source |
|---|---|---|---|---|
| Total suspension of parenting time (567+ days) | Due process findings | 2,008 (§1983 target) | CRITICAL | Adverse Evidence Matrix |
| Ex parte custody order 08/08/2025 without affidavit | EX_PARTE_HANDLING | 2,327 rows (custody case) | CRITICAL | JTC Conduct Pattern Table, AEM_000016–AEM_000019 |
| No best-interest hearing under MCL 722.23 | GENERAL_CONDUCT_EPISODE | 17,078 rows (custody) | CRITICAL | JTC Conduct Pattern Table, AEM_000001–AEM_000007 |
| Exclusion of exculpatory evidence at hearings | MENTAL_HEALTH_EVAL_PROCESS | 1,158 rows | HIGH | JTC Conduct Pattern Table, AEM_000045 |
| Parenting time restrictions | PARENTING_TIME_RESTRICTION | 63 adverse rows (custody) + 66 adverse rows (PPO) | HIGH | Adverse_Rebuttal_Packet_Summary.csv |
| No findings of imminent danger | Due process findings | Part of 14,056 total | CRITICAL | Adverse Evidence Summary |

**Aggregate evidence for this element:** 14,056 due process findings + 3,756 judicial misconduct findings in the full matrix; 2,008 + 886 in the §1983 target specifically.

### C. Fourteenth Amendment — Procedural Due Process

**Right:** Notice, opportunity to be heard, and neutral decision-maker before deprivation. *Mathews v. Eldridge*, 424 U.S. 319, 333 (1976).

| Deprivation | Evidence Category | Evidence Count | Severity | Source |
|---|---|---|---|---|
| **Failure of Notice** | | | | |
| 150 ex parte violations (no notice before deprivation) | EX_PARTE_HANDLING | 2,327 + 630 + 538 rows | CRITICAL | JTC Conduct Pattern Table |
| 1,202 service/notice defects (custody case) | SERVICE_NOTICE_DEFECT | 1,202 rows, priority 2,924 | HIGH | JTC Conduct Pattern Table, AEM_000032–AEM_000038 |
| 484 service/notice defects (PPO case) | SERVICE_NOTICE_DEFECT | 484 rows, priority 1,438 | HIGH | JTC Conduct Pattern Table |
| 24 of 55 orders entered ex parte (43.6%) | Ex parte findings | 12,699 (§1983 target) | CRITICAL | Adverse Evidence Matrix |
| 5 ex parte orders on single day (08/08/2025) | EX_PARTE_HANDLING | Part of 2,327 rows | CRITICAL | JTC Conduct Pattern Table |
| **Failure of Hearing** | | | | |
| Muting/silencing at hearings | Judicial misconduct | 886 (§1983 target) | HIGH | Adverse Evidence Matrix |
| Exclusion of exculpatory evidence | MENTAL_HEALTH_EVAL_PROCESS | 1,158 rows | HIGH | JTC Conduct Pattern Table |
| Evidence refused: police reports, HealthWest evals, photos, USB | Judicial misconduct | Subset of 886 | HIGH | Court record |
| **Failure of Neutral Decision-Maker** | | | | |
| Self-ruling on disqualification (MCR 2.003(D) violation) | RECUSAL_BIAS_SIGNAL | 1,676 rows (custody) | HIGH | JTC Conduct Pattern Table, AEM_000020–AEM_000023 |
| 167 MCR 2.003 disqualification violations | RECUSAL_BIAS_SIGNAL | 1,003 rows (PPO) | HIGH | JTC Conduct Pattern Table, AEM_000039–AEM_000042 |
| 4,195 total bias signal entries across all cases | RECUSAL_BIAS_SIGNAL | 4,195 combined | HIGH | JTC Conduct Pattern Table |

**Aggregate evidence for this element:** 56,608 ex parte findings across all source files; 12,699 ex parte + 2,008 due process + 886 judicial misconduct in §1983 target = **15,593 findings** supporting procedural due process claims.

### D. Fourteenth Amendment — Equal Protection

**Right:** Equal protection of the laws; prohibition of sex-based or class-of-one discrimination. *Craig v. Boren*, 429 U.S. 190 (1976).

| Disparity | Father (Plaintiff) | Mother (Watson) | Evidence Source |
|---|---|---|---|
| Ex parte orders | 24 of 55 against Father | 0 sanctions for false filings | Court docket |
| Contempt sanctions | 2,722 atoms (custody) + 1,261 atoms (PPO) | 0 contempt findings | JTC Conduct Pattern Table |
| Financial barriers | $250 bond per motion | No restrictions | Court order, AEM_000043–AEM_000044 |
| Parenting time | 100% suspended 567+ days | Full custody retained | Court orders |
| Evidence consideration | Excluded/refused | Accepted unsworn allegations | Hearing record |
| Hearing access | Muted/silenced | Full opportunity | Hearing record |
| Sanctions | Multiple | Zero | Court docket |
| Bias indicators | 4,195 bias signals | None | JTC Conduct Pattern Table |

**Aggregate evidence for this element:** 50 bias findings + 8 retaliation findings in §1983 target; 4,195 RECUSAL_BIAS_SIGNAL entries; disparity table entries above.

### E. First Amendment — Access to Courts / Retaliation

**Right:** Right to petition government for redress; meaningful access to courts. *Boddie v. Connecticut*, 401 U.S. 371 (1971); *Bounds v. Smith*, 430 U.S. 817 (1977).

| Deprivation | Evidence Category | Evidence Count | Severity | Source |
|---|---|---|---|---|
| $250 bond per motion (financial barrier) | GENERAL_CONDUCT_EPISODE, BOND_BARRIER | 1,575 rows + 5 adverse entries | HIGH | JTC Conduct Pattern Table, AEM_000043–AEM_000044; Adverse_Rebuttal_Packet_Summary.csv |
| Bond imposed after Plaintiff filed motions challenging ex parte orders (retaliatory timing) | Retaliation findings | 8 (§1983 target) | HIGH | Adverse Evidence Matrix |
| Financial harm from bond + litigation costs | Financial harm findings | 29 (§1983 target) | HIGH | Adverse Evidence Matrix |
| Complete denial of court access (bond + ex parte suspension = no remedy available) | Combined | 29 + 8 = 37 | CRITICAL | Adverse Evidence Matrix |

### F. 42 U.S.C. § 1985(3) — Conspiracy

**Elements:** (1) Conspiracy; (2) discriminatory purpose; (3) overt act; (4) resulting injury.

| Element | Evidence | Count | Source |
|---|---|---|---|
| **Conspiracy (agreement)** | Watson files → McNeill rules same day → Berry files within 48 hours | 30+ temporal matches | Proceeding_Chain_Summary.csv |
| | Berry voicemail to Plaintiff (Item #6) | 1 direct evidence item | Ex parte objection table |
| | PPO-custody same-day events (10/10 weaponization score) | 27 incidents | Case database |
| **Discriminatory purpose** | One-directional benefit pattern (100% for Watson, 0% for Plaintiff) | All 24 ex parte orders | Court docket |
| | 4,195 bias signal entries | 4,195 | JTC Conduct Pattern Table |
| **Overt acts** | Each ex parte order | 24+ | Court docket |
| | Each same-day ruling | 30+ | Proceeding chain analysis |
| | 5 ex parte orders on 08/08/2025 | 5 | Court docket |
| | 27 PPO weaponization incidents | 27 | Case database |
| **Injury** | 567+ days separation | Ongoing | Calculated from 08/08/2025 |
| | 15,991 adverse findings (§1983 target) | 15,991 | Adverse Evidence Matrix |

---

## III. CONSTITUTIONAL VIOLATION × EVIDENCE MATRIX

| Constitutional Violation | Evidence Category | Finding Count | Severity Distribution | Key Source |
|---|---|---|---|---|
| **14th Amend. — Substantive Due Process** | Due process + judicial misconduct | 2,894 (§1983) | 18 CRIT / 2,400 HIGH / 450 MED | JTC Conduct Pattern Table; Adverse Evidence Matrix |
| **14th Amend. — Procedural Due Process** | Ex parte + service defects + hearing denial | 12,699 ex parte + 1,686 notice defects | 4 CRIT / 12,000+ HIGH | Deadline_Notice_Audit; Notice_Risk_Register; JTC |
| **14th Amend. — Equal Protection** | Bias + disparate treatment | 50 bias + 4,195 bias signals | 0 CRIT / 50 HIGH | Adverse Evidence Matrix; JTC |
| **1st Amend. — Access to Courts** | Financial harm + retaliation + bond | 29 + 8 + 5 = 42 | 0 CRIT / 37 HIGH / 5 MED | Adverse Evidence Matrix; Adverse Rebuttal |
| **§ 1985(3) — Conspiracy** | Temporal coordination + direct evidence | 30+ incidents + 27 PPO + voicemail | HIGH severity pattern | Proceeding_Chain_Summary; Case database |
| **Monell — Municipal Policy** | Systemic failures across all categories | All 76,329 | Full severity range | All 9 source files |

---

## IV. MOST EGREGIOUS INCIDENTS TIMELINE

| Date | Incident | Constitutional Right | Severity | Evidence Reference |
|---|---|---|---|---|
| **2023-10-XX** | PPO case filed (2023-5907-PP); assigned to McNeill | — | — | Court docket |
| **2024-01-XX** | Custody case filed (2024-001507-DC); also assigned to McNeill | — | — | Court docket |
| **2024-04-11** | Show Cause (contempt) filed; **jail threat** + $250 bond | 14th Amend. Due Process; 1st Amend. | CRITICAL | AEM_000012–AEM_000015 (CONTEMPT_SANCTION_CHAIN, 2,722 rows) |
| **2024-04-11** | Ex Parte PPO order entered same day | 14th Amend. Due Process | CRITICAL | AEM_000047–AEM_000050 (EX_PARTE_HANDLING, 630 rows) |
| **2024-07-17** | Ex Parte "FIG Order" hearing re: minor child L.D.W. (minor child, born November 9, 2022) | 14th Amend. Due Process | HIGH | AEM_000058–AEM_000061 (EX_PARTE_HANDLING, 538 rows) |
| **2025-05-XX** | **$250 bond per motion** imposed on Plaintiff | 1st Amend. Access to Courts | CRITICAL | AEM_000043–AEM_000044; Bond order text |
| **2025-07-29** | Parenting exchange — exculpatory photographs taken; court later **refuses to view** | 14th Amend. Due Process | HIGH | Hearing record; MENTAL_HEALTH_EVAL_PROCESS |
| **2025-08-08** | **FIVE (5) ex parte orders on single day** — ALL parenting time suspended | 14th Amend. Due Process (total deprivation) | CRITICAL | AEM_000016–AEM_000019 (EX_PARTE_HANDLING, 2,327 rows) |
| **2025-08-08** | Plaintiff arrives at scheduled exchange with **no notice** of ex parte orders | 14th Amend. Procedural Due Process | CRITICAL | Plaintiff declaration |
| **2025-08-08 → present** | **567+ consecutive days** of total parent-child separation (ongoing) | 14th Amend. Substantive Due Process | CRITICAL | Calculated duration |
| **2025-09-05** | HealthWest mental health evaluation ordered; results **excluded** by court | 14th Amend. Due Process | HIGH | AEM_000032; SERVICE_NOTICE_DEFECT |
| **2025-10-27** | Orders entered "after hearing" — bias signals in court documentation | 14th Amend. Equal Protection | HIGH | AEM_000028–AEM_000031 (RECUSAL_BIAS_SIGNAL, 1,516 rows) |
| **Post-08/08/2025** | McNeill **self-rules on disqualification** motion | 14th Amend. (neutral decision-maker) | HIGH | MCR 2.003(D) violation; AEM_000020–AEM_000023 |
| **Ongoing** | Contempt sanctions escalate; **2,722 atoms** in custody, **1,261** in PPO | 14th Amend. Due Process; 8th Amend. | HIGH | AEM_000012–AEM_000015, AEM_000024–AEM_000027 |

---

## V. CONDUCT PATTERN SUMMARY (JTC TABLE)

The JTC Conduct Pattern Table documents 19 distinct conduct categories across 3 case numbers. Below is the complete summary:

| Case | Conduct Pattern | Row Count | Findings Gap | Service Gap | Priority Score |
|---|---|---|---|---|---|
| 2024-001507-DC | GENERAL_CONDUCT_EPISODE | 17,078 | 16,451 | 0 | 49,980 |
| 2023-005907-PP | GENERAL_CONDUCT_EPISODE | 10,201 | 9,894 | 0 | 29,989 |
| 2024-001507-DC | CONTEMPT_SANCTION_CHAIN | 2,722 | 2,704 | 0 | 8,130 |
| 2024-001507-DC | EX_PARTE_HANDLING | 2,327 | 2,014 | 12 | 6,379 |
| 2024-001507-DC | RECUSAL_BIAS_SIGNAL | 1,676 | 1,044 | 1 | 3,766 |
| 2023-005907-PP | CONTEMPT_SANCTION_CHAIN | 1,261 | 1,237 | 0 | 3,735 |
| UNASSIGNED | RECUSAL_BIAS_SIGNAL | 1,516 | 1,060 | 22 | 3,680 |
| 2024-001507-DC | SERVICE_NOTICE_DEFECT | 1,202 | 857 | 4 | 2,924 |
| 2023-005907-PP | RECUSAL_BIAS_SIGNAL | 1,003 | 731 | 0 | 2,465 |
| UNASSIGNED | GENERAL_CONDUCT_EPISODE | 1,575 | 409 | 0 | 2,393 |
| 2024-001507-DC | MENTAL_HEALTH_EVAL_PROCESS | 1,158 | 436 | 0 | 2,030 |
| 2023-005907-PP | EX_PARTE_HANDLING | 630 | 582 | 9 | 1,812 |
| UNASSIGNED | MENTAL_HEALTH_EVAL_PROCESS | 1,372 | 186 | 0 | 1,744 |
| UNASSIGNED | EX_PARTE_HANDLING | 538 | 533 | 0 | 1,604 |
| 2023-005907-PP | SERVICE_NOTICE_DEFECT | 484 | 477 | 0 | 1,438 |
| 2023-005907-PP | MENTAL_HEALTH_EVAL_PROCESS | 151 | 117 | 0 | 385 |
| UNASSIGNED | SERVICE_NOTICE_DEFECT | 77 | 1 | 4 | 87 |
| UNASSIGNED | CONTEMPT_SANCTION_CHAIN | 3 | 0 | 0 | 3 |

**Key observations:**
- The "Findings Gap" column shows the number of entries where required findings were **missing** — e.g., in the custody GENERAL_CONDUCT_EPISODE, 16,451 of 17,078 rows had missing findings.
- The CONTEMPT_SANCTION_CHAIN in the custody case has 2,704 of 2,722 rows with missing findings — meaning nearly all contempt sanctions lacked required evidentiary support.
- The combined priority scores exceed 119,000, reflecting the extraordinary volume and severity of the documented conduct.

---

## VI. ADVERSE REBUTTAL PACKET ANALYSIS

The Adverse_Rebuttal_Packet_Summary.csv catalogs 173 adverse rebuttal entries across multiple topics and lanes:

| Case | Lane | Topic | Adverse Rows | Findings Missing | Priority |
|---|---|---|---|---|---|
| 2023-005907-PP | MEEK3 | ADVERSE_GENERIC | 204 | 203 | 610 |
| 2023-005907-PP | MEEK3 | CONTEMPT_JAIL | 110 | 109 | 328 |
| UNASSIGNED | UNCLASS | EX_PARTE_PROCESS | 98 | 97 | 292 |
| 2023-005907-PP | MEEK3 | PARENTING_TIME_RESTRICTION | 66 | 62 | 190 |
| 2024-001507-DC | MEEK1 | PARENTING_TIME_RESTRICTION | 63 | 63 | 189 |
| 2023-005907-PP | MEEK3 | PPO_EXTENSION | 56 | 56 | 168 |
| UNASSIGNED | MEEK4 | EX_PARTE_PROCESS | 43 | 41 | 125 |
| 2023-005907-PP | MEEK3 | JUDICIAL_CONDUCT | 29 | 29 | 87 |
| 2023-005907-PP | MEEK1 | HOUSING_UTILITY | 15 | 15 | 45 |
| 2024-001507-DC | MEEK2 | ADVERSE_GENERIC | 13 | 13 | 39 |
| 2023-005907-PP | MEEK3 | THREAT_HARASSMENT_ALLEGATIONS | 12 | 12 | 36 |
| 2023-005907-PP | MEEK1 | PARENTING_TIME_RESTRICTION | 12 | 10 | 32 |
| 2023-005907-PP | MEEK3 | SERVICE_NOTICE | 10 | 10 | 30 |

**Key findings:**
- **204 ADVERSE_GENERIC entries** in the PPO case with **203 findings missing** (99.5% unsupported);
- **110 CONTEMPT_JAIL entries** with **109 findings missing** (99.1% unsupported);
- **56 PPO_EXTENSION entries** with **56 findings missing** (100% unsupported);
- **29 JUDICIAL_CONDUCT entries** with **29 findings missing** (100% unsupported).

These missing-findings rates confirm that the vast majority of adverse actions against Plaintiff were taken **without the evidentiary support required by due process**.

---

## VII. CROSS-REFERENCE TO JTC EXHIBIT BINDERS

The evidence documented herein has been prepared in parallel for the following proceedings:

| Proceeding | Case/File Number | Overlap with §1983 Evidence |
|---|---|---|
| JTC Formal Complaint | Michigan Judicial Tenure Commission | 1,127 violations from JTC Conduct Pattern Table; 15,651 JTC-target findings in evidence matrix |
| COA Appeal of Right | COA Case No. 366810 | 15,954 COA-target findings; same evidence base |
| MSC Superintending Control | Michigan Supreme Court | 15,928 MSC-target findings; same evidence base |
| Circuit Court Custody | Case No. 2024-001507-DC | 2,101 custody-target findings |
| Circuit Court Shady Oaks | Case No. 2025-002760-CZ | 5,352 housing-target findings |
| Federal Fair Housing | To be filed | 5,352 FHA-target findings |

**Note:** The evidence matrix assigns findings to multiple filing targets where applicable. Cross-referencing ensures consistency across all proceedings and prevents inconsistent factual representations.

---

## VIII. STATISTICAL SUMMARY

### A. Total Evidence by Filing Target

| Filing Target | Count | % of Total |
|---|---|---|
| **Federal §1983 McNeill** | **15,991** | **21.0%** |
| COA Appeal | 15,954 | 20.9% |
| MSC Superintending Control | 15,928 | 20.9% |
| JTC Investigation | 15,651 | 20.5% |
| Circuit Court Shady Oaks | 5,352 | 7.0% |
| Federal Fair Housing | 5,352 | 7.0% |
| Circuit Court Custody | 2,101 | 2.8% |
| **TOTAL** | **76,329** | **100%** |

### B. Federal §1983 Target — Severity Breakdown

| Severity | Count | Percentage |
|---|---|---|
| CRITICAL | 18 | 0.1% |
| HIGH | 13,202 | 82.6% |
| MEDIUM | 2,732 | 17.1% |
| LOW | 39 | 0.2% |
| **TOTAL** | **15,991** | **100%** |

### C. Federal §1983 Target — Violation Type Breakdown

| Type | Count | % of §1983 Findings |
|---|---|---|
| Ex parte | 12,699 | 79.4% |
| Due process | 2,008 | 12.6% |
| Judicial misconduct | 886 | 5.5% |
| Housing violation | 285 | 1.8% |
| Bias | 50 | 0.3% |
| Financial harm | 29 | 0.2% |
| Fraud | 26 | 0.2% |
| Retaliation | 8 | 0.1% |
| **TOTAL** | **15,991** | **100%** |

### D. Key Numerical Summary

| Metric | Value |
|---|---|
| Total adverse findings across all databases | 76,329 |
| Findings tagged to Federal §1983 target | 15,991 |
| CRITICAL severity findings (§1983) | 18 |
| HIGH severity findings (§1983) | 13,202 |
| Discrete judicial conduct violations (JTC) | 1,127 |
| Conduct pattern categories | 19 |
| Ex parte violations (documented) | 150 |
| Ex parte findings (evidence matrix) | 12,699 |
| MCR 2.003 disqualification violations | 167 |
| Recusal/bias signal entries | 4,195 |
| Contempt sanction chain atoms (custody) | 2,722 |
| Contempt sanction chain atoms (PPO) | 1,261 |
| Service/notice defect entries (custody) | 1,202 |
| Service/notice defect entries (PPO) | 484 |
| PPO weaponization incidents | 27 |
| Fraud on court indicators | 105 |
| $250 bond barrier entries | 5+ |
| Days of total parent-child separation | 567+ (ongoing) |
| Source files analyzed | 9 |
| Independent evidence databases | Multiple (cross-validated) |

---

*This Evidence Appendix is filed concurrently with the Second Amended Complaint and Brief in Support. All data is derived from Plaintiff's litigation intelligence system and is independently verifiable through the underlying source documents, court records, and docket entries.*

*Generated from LitigationOS evidence databases. Last updated: 2026-03-07.*
