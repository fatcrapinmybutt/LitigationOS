# CROSS-REFERENCE MATRIX -- ALL FILING STACKS

**Generated:** 2026-03-04 22:17
**Agent:** Agent-148 (LitigationOS)
**Case:** Pigors v. Watson, 14th Circuit No. 2024-001507-DC

---

## 1. FILING STACK INVENTORY

| Stack ID | Label | Court | Case No. | Type |
|----------|-------|-------|----------|------|
| 01_COA_366810 | COA Appeal No. 366810 | Michigan Court of Appeals | 366810 | STATE_APPELLATE |
| 02_TRIAL_14TH | 14th Circuit Court Motions | 14th Circuit Court, Muskegon County | 2024-001507-DC | STATE_TRIAL |
| 03_FEDERAL_1983 | 42 USC 1983 Federal Civil Rights | U.S. District Court, W.D. Michigan | TBD | FEDERAL |
| 04_JTC_MCNEILL | JTC Complaint - Judge McNeill | Judicial Tenure Commission | TBD | ADMINISTRATIVE |
| 04_MSC_ORIGINAL_ACTION | MSC Original Action / Application | Michigan Supreme Court | TBD | STATE_SUPREME |
| 05_BAR_BARNES | Attorney Discipline - Barnes/Berry | Attorney Grievance Commission | N/A | ADMINISTRATIVE |
| 06_EMERGENCY | Emergency Filings Package | 14th Circuit Court / Multiple | 2024-001507-DC | EMERGENCY |

## 2. FILING SEQUENCE & DEPENDENCIES

| Priority | Package | Filing Title | Target Court | Depends On |
|----------|---------|--------------|--------------|------------|
| 1 | PKG05_COA_APPELLANT_BRIEF | Appellant's Brief — Michigan Court of Appeals | Michigan Court of Appeals | None |
| 2 | PKG01_EMERGENCY_PARENTING_TIME | Emergency Motion to Restore Parenting Time | 14th Circuit Court | None |
| 3 | PKG06_JTC_COMPLAINT | Formal Complaint Against Hon. Jenny L. McNeill | Judicial Tenure Commission | PKG05 |
| 4 | PKG03_DISQUALIFY_MCNEILL | Motion to Disqualify Hon. Jenny L. McNeill | 14th Circuit Court | PKG06 |
| 5 | PKG04_VOID_EX_PARTE_ORDERS | Motion to Void Ex Parte Orders | 14th Circuit Court | PKG03 |
| 6 | PKG02_VACATE_PPO | Motion to Vacate Personal Protection Order | 14th Circuit Court | PKG04 |
| 7 | PKG10_FEDERAL_1983 | 42 U.S.C. § 1983 Civil Rights Complaint | U.S. District Court, Western District of Michigan | PKG05 |
| 8 | PKG07_MSC_APPLICATION | Application for Leave to Appeal | Michigan Supreme Court | PKG05 |
| 9 | PKG08_CONTEMPT_MOTION | Motion for Contempt / Enforcement | 14th Circuit Court | PKG03 |
| 10 | PKG11_SPOLIATION_NOTICE | Notice of Spoliation / Evidence Preservation | 14th Circuit Court | None |
| 11 | PKG12_FOC_OBJECTION | Objection to Friend of the Court Recommendation | 14th Circuit Court | None |
| 12 | PKG09_HOUSING_COMPLAINT | Housing Discrimination Complaint | Michigan Department of Civil Rights / HUD | None |

### Dependency Chain (Visual)

```
TIER 1 (IMMEDIATE):
  PKG11_SPOLIATION_NOTICE --> [No dependencies]
  PKG01_EMERGENCY_PARENTING_TIME --> [No dependencies]
  PKG05_COA_APPELLANT_BRIEF --> [No dependencies]

TIER 2 (AFTER COA BRIEF FILED):
  PKG05 --> PKG06_JTC_COMPLAINT
  PKG06 --> PKG03_DISQUALIFY_MCNEILL
  PKG03 --> PKG04_VOID_EX_PARTE_ORDERS
  PKG04 --> PKG02_VACATE_PPO

TIER 3 (CONTINGENT):
  PKG05 --> PKG10_FEDERAL_1983 (if COA denies)
  PKG05 --> PKG07_MSC_APPLICATION (if COA denies)

TIER 4 (SUPPLEMENTAL):
  PKG03 --> PKG08_CONTEMPT_MOTION
  PKG12_FOC_OBJECTION --> [Conditional]
  PKG09_HOUSING_COMPLAINT --> [Independent track]
```

## 3. FILING-TO-FILING CROSS-REFERENCE MATRIX

| Stack | 01_COA | 02_TRI | 03_FED | 04_JTC | 04_MSC | 05_BAR | 06_EME |
|-------|------|------|------|------|------|------|------|
| **01_COA** | -- | X | X | X | X | X | X |
| **02_TRI** | X | -- | X | X | X | X | X |
| **03_FED** | X | X | -- | X | X | X | X |
| **04_JTC** | X | X | X | -- | X | X | X |
| **04_MSC** | X | X | X | X | -- | X | X |
| **05_BAR** | X | X | X | X | X | -- | X |
| **06_EME** | X | X | X | X | X | X | -- |

## 4. CROSS-REFERENCE RELATIONSHIP DETAILS

### COA Appeal No. 366810 <--> 14th Circuit Court Motions

- **Relationship:** COA reviews trial court orders; trial motions create record for appeal
- **Shared Exhibits:** Exhibit A (AppClose Communication Record — Complete, Bates: PIGORS-0001); Exhibit B (AppClose Psychological Analysis, Bates: PIGORS-0002); Exhibit G (Albert Watson Premeditation Statement, Bates: PIGORS-0007); Exhibit I (Police Investigation Reports (9) — Zero Findings, Bates: PIGORS-0009); Exhibit K (Incarceration Records — 59+ Days, Bates: PIGORS-0011); Exhibit N (Damages Itemization Schedule, Bates: PIGORS-0014); Exhibit Q (Rebuttal Matrix — Adversary Assertions, Bates: PIGORS-0017); Exhibit R (Master Prosecution Timeline, Bates: PIGORS-0018); Exhibit S (AppClose Violation Record — 44 Incidents, Bates: PIGORS-0019); Exhibit T (Emily Watson Employment — Kent County Prosecutor, Bates: PIGORS-0020); Exhibit U (Parental Alienation Assessment, Bates: PIGORS-0021)

### COA Appeal No. 366810 <--> 42 USC 1983 Federal Civil Rights

- **Relationship:** Federal 1983 claim references same constitutional violations; serves as Plan B if COA denies
- **Shared Exhibits:** Exhibit A (AppClose Communication Record — Complete, Bates: PIGORS-0001); Exhibit C (Drug Screen Results — NEGATIVE, Bates: PIGORS-0003); Exhibit D (HealthWest Evaluation #1 — ALL ZEROS, Bates: PIGORS-0004); Exhibit E (HealthWest Evaluation #2 — "Rule Out" After Judge Letter, Bates: PIGORS-0005); Exhibit F (Judge McNeill Communication to HealthWest Evaluator, Bates: PIGORS-0006); Exhibit G (Albert Watson Premeditation Statement, Bates: PIGORS-0007); Exhibit I (Police Investigation Reports (9) — Zero Findings, Bates: PIGORS-0009); Exhibit K (Incarceration Records — 59+ Days, Bates: PIGORS-0011); Exhibit N (Damages Itemization Schedule, Bates: PIGORS-0014); Exhibit O (Constitutional Violation Map, Bates: PIGORS-0015); Exhibit Q (Rebuttal Matrix — Adversary Assertions, Bates: PIGORS-0017); Exhibit R (Master Prosecution Timeline, Bates: PIGORS-0018)

### COA Appeal No. 366810 <--> JTC Complaint - Judge McNeill

- **Relationship:** JTC complaint uses same judicial misconduct evidence as COA brief; COA filing provides protection from retaliation
- **Shared Exhibits:** Exhibit A (AppClose Communication Record — Complete, Bates: PIGORS-0001); Exhibit E (HealthWest Evaluation #2 — "Rule Out" After Judge Letter, Bates: PIGORS-0005); Exhibit F (Judge McNeill Communication to HealthWest Evaluator, Bates: PIGORS-0006); Exhibit J (Ex Parte Order Statistical Analysis, Bates: PIGORS-0010); Exhibit N (Damages Itemization Schedule, Bates: PIGORS-0014); Exhibit P (Judicial Canon Violation Matrix, Bates: PIGORS-0016); Exhibit Q (Rebuttal Matrix — Adversary Assertions, Bates: PIGORS-0017); Exhibit R (Master Prosecution Timeline, Bates: PIGORS-0018)

### COA Appeal No. 366810 <--> MSC Original Action / Application

- **Relationship:** MSC application follows COA denial; same constitutional arguments elevated
- **Shared Exhibits:** Exhibit A (AppClose Communication Record — Complete, Bates: PIGORS-0001); Exhibit J (Ex Parte Order Statistical Analysis, Bates: PIGORS-0010); Exhibit N (Damages Itemization Schedule, Bates: PIGORS-0014); Exhibit P (Judicial Canon Violation Matrix, Bates: PIGORS-0016); Exhibit Q (Rebuttal Matrix — Adversary Assertions, Bates: PIGORS-0017); Exhibit R (Master Prosecution Timeline, Bates: PIGORS-0018)

### COA Appeal No. 366810 <--> Attorney Discipline - Barnes/Berry

- **Relationship:** Attorney misconduct evidence supports ineffective assistance arguments in COA brief
- **Shared Exhibits:** Exhibit A (AppClose Communication Record — Complete, Bates: PIGORS-0001); Exhibit N (Damages Itemization Schedule, Bates: PIGORS-0014); Exhibit Q (Rebuttal Matrix — Adversary Assertions, Bates: PIGORS-0017); Exhibit R (Master Prosecution Timeline, Bates: PIGORS-0018)

### COA Appeal No. 366810 <--> Emergency Filings Package

- **Relationship:** Emergency filings create urgency record supporting COA emergency application
- **Shared Exhibits:** Exhibit A (AppClose Communication Record — Complete, Bates: PIGORS-0001); Exhibit N (Damages Itemization Schedule, Bates: PIGORS-0014); Exhibit Q (Rebuttal Matrix — Adversary Assertions, Bates: PIGORS-0017); Exhibit R (Master Prosecution Timeline, Bates: PIGORS-0018)

### 14th Circuit Court Motions <--> 42 USC 1983 Federal Civil Rights

- **Relationship:** Trial court denials establish exhaustion for federal claim; same due process violations
- **Shared Exhibits:** Exhibit A (AppClose Communication Record — Complete, Bates: PIGORS-0001); Exhibit G (Albert Watson Premeditation Statement, Bates: PIGORS-0007); Exhibit I (Police Investigation Reports (9) — Zero Findings, Bates: PIGORS-0009); Exhibit K (Incarceration Records — 59+ Days, Bates: PIGORS-0011); Exhibit L (Employment Termination Records — 3 Job Losses, Bates: PIGORS-0012); Exhibit M (Housing Loss Documentation, Bates: PIGORS-0013); Exhibit N (Damages Itemization Schedule, Bates: PIGORS-0014); Exhibit Q (Rebuttal Matrix — Adversary Assertions, Bates: PIGORS-0017); Exhibit R (Master Prosecution Timeline, Bates: PIGORS-0018)

### 14th Circuit Court Motions <--> JTC Complaint - Judge McNeill

- **Relationship:** Trial court rulings document judicial misconduct for JTC; disqualification motion parallels JTC complaint
- **Shared Exhibits:** Exhibit A (AppClose Communication Record — Complete, Bates: PIGORS-0001); Exhibit N (Damages Itemization Schedule, Bates: PIGORS-0014); Exhibit Q (Rebuttal Matrix — Adversary Assertions, Bates: PIGORS-0017); Exhibit R (Master Prosecution Timeline, Bates: PIGORS-0018)

### 14th Circuit Court Motions <--> MSC Original Action / Application

- **Relationship:** Trial court orders subject to MSC superintending control
- **Shared Exhibits:** Exhibit A (AppClose Communication Record — Complete, Bates: PIGORS-0001); Exhibit N (Damages Itemization Schedule, Bates: PIGORS-0014); Exhibit Q (Rebuttal Matrix — Adversary Assertions, Bates: PIGORS-0017); Exhibit R (Master Prosecution Timeline, Bates: PIGORS-0018)

### 14th Circuit Court Motions <--> Attorney Discipline - Barnes/Berry

- **Relationship:** Barnes FOC conduct documented in trial proceedings; trial record supports bar complaint
- **Shared Exhibits:** Exhibit A (AppClose Communication Record — Complete, Bates: PIGORS-0001); Exhibit N (Damages Itemization Schedule, Bates: PIGORS-0014); Exhibit Q (Rebuttal Matrix — Adversary Assertions, Bates: PIGORS-0017); Exhibit R (Master Prosecution Timeline, Bates: PIGORS-0018)

### 14th Circuit Court Motions <--> Emergency Filings Package

- **Relationship:** Emergency motions filed in trial court; emergency record supports appellate emergency applications
- **Shared Exhibits:** Exhibit A (AppClose Communication Record — Complete, Bates: PIGORS-0001); Exhibit N (Damages Itemization Schedule, Bates: PIGORS-0014); Exhibit Q (Rebuttal Matrix — Adversary Assertions, Bates: PIGORS-0017); Exhibit R (Master Prosecution Timeline, Bates: PIGORS-0018)

### 42 USC 1983 Federal Civil Rights <--> JTC Complaint - Judge McNeill

- **Relationship:** Federal complaint names McNeill individually; JTC complaint provides corroborating pattern evidence
- **Shared Exhibits:** Exhibit A (AppClose Communication Record — Complete, Bates: PIGORS-0001); Exhibit E (HealthWest Evaluation #2 — "Rule Out" After Judge Letter, Bates: PIGORS-0005); Exhibit F (Judge McNeill Communication to HealthWest Evaluator, Bates: PIGORS-0006); Exhibit N (Damages Itemization Schedule, Bates: PIGORS-0014); Exhibit Q (Rebuttal Matrix — Adversary Assertions, Bates: PIGORS-0017); Exhibit R (Master Prosecution Timeline, Bates: PIGORS-0018)

### 42 USC 1983 Federal Civil Rights <--> MSC Original Action / Application

- **Relationship:** Federal and MSC actions create parallel pressure; same constitutional framework
- **Shared Exhibits:** Exhibit A (AppClose Communication Record — Complete, Bates: PIGORS-0001); Exhibit N (Damages Itemization Schedule, Bates: PIGORS-0014); Exhibit Q (Rebuttal Matrix — Adversary Assertions, Bates: PIGORS-0017); Exhibit R (Master Prosecution Timeline, Bates: PIGORS-0018)

### 42 USC 1983 Federal Civil Rights <--> Attorney Discipline - Barnes/Berry

- **Relationship:** Attorney misconduct may support conspiracy claims under 42 USC 1985
- **Shared Exhibits:** Exhibit A (AppClose Communication Record — Complete, Bates: PIGORS-0001); Exhibit N (Damages Itemization Schedule, Bates: PIGORS-0014); Exhibit Q (Rebuttal Matrix — Adversary Assertions, Bates: PIGORS-0017); Exhibit R (Master Prosecution Timeline, Bates: PIGORS-0018)

### 42 USC 1983 Federal Civil Rights <--> Emergency Filings Package

- **Relationship:** Emergency separation duration (571+ days) establishes constitutional injury for 1983 damages
- **Shared Exhibits:** Exhibit A (AppClose Communication Record — Complete, Bates: PIGORS-0001); Exhibit N (Damages Itemization Schedule, Bates: PIGORS-0014); Exhibit Q (Rebuttal Matrix — Adversary Assertions, Bates: PIGORS-0017); Exhibit R (Master Prosecution Timeline, Bates: PIGORS-0018)

### JTC Complaint - Judge McNeill <--> MSC Original Action / Application

- **Relationship:** JTC and MSC complaints address same judicial conduct from different remedial angles
- **Shared Exhibits:** Exhibit A (AppClose Communication Record — Complete, Bates: PIGORS-0001); Exhibit J (Ex Parte Order Statistical Analysis, Bates: PIGORS-0010); Exhibit N (Damages Itemization Schedule, Bates: PIGORS-0014); Exhibit P (Judicial Canon Violation Matrix, Bates: PIGORS-0016); Exhibit Q (Rebuttal Matrix — Adversary Assertions, Bates: PIGORS-0017); Exhibit R (Master Prosecution Timeline, Bates: PIGORS-0018)

### JTC Complaint - Judge McNeill <--> Attorney Discipline - Barnes/Berry

- **Relationship:** Coordinated misconduct between judge and attorneys documented in both complaints
- **Shared Exhibits:** Exhibit A (AppClose Communication Record — Complete, Bates: PIGORS-0001); Exhibit N (Damages Itemization Schedule, Bates: PIGORS-0014); Exhibit Q (Rebuttal Matrix — Adversary Assertions, Bates: PIGORS-0017); Exhibit R (Master Prosecution Timeline, Bates: PIGORS-0018)

### JTC Complaint - Judge McNeill <--> Emergency Filings Package

- **Relationship:** Emergency filings document ongoing harm from judicial misconduct
- **Shared Exhibits:** Exhibit A (AppClose Communication Record — Complete, Bates: PIGORS-0001); Exhibit N (Damages Itemization Schedule, Bates: PIGORS-0014); Exhibit Q (Rebuttal Matrix — Adversary Assertions, Bates: PIGORS-0017); Exhibit R (Master Prosecution Timeline, Bates: PIGORS-0018)

### MSC Original Action / Application <--> Attorney Discipline - Barnes/Berry

- **Relationship:** MSC may consider systemic attorney misconduct as factor in supervisory jurisdiction
- **Shared Exhibits:** Exhibit A (AppClose Communication Record — Complete, Bates: PIGORS-0001); Exhibit N (Damages Itemization Schedule, Bates: PIGORS-0014); Exhibit Q (Rebuttal Matrix — Adversary Assertions, Bates: PIGORS-0017); Exhibit R (Master Prosecution Timeline, Bates: PIGORS-0018)

### MSC Original Action / Application <--> Emergency Filings Package

- **Relationship:** Emergency circumstances support MSC original jurisdiction under MCR 7.304
- **Shared Exhibits:** Exhibit A (AppClose Communication Record — Complete, Bates: PIGORS-0001); Exhibit N (Damages Itemization Schedule, Bates: PIGORS-0014); Exhibit Q (Rebuttal Matrix — Adversary Assertions, Bates: PIGORS-0017); Exhibit R (Master Prosecution Timeline, Bates: PIGORS-0018)

### Attorney Discipline - Barnes/Berry <--> Emergency Filings Package

- **Relationship:** Attorney failures contributed to emergency circumstances
- **Shared Exhibits:** Exhibit A (AppClose Communication Record — Complete, Bates: PIGORS-0001); Exhibit N (Damages Itemization Schedule, Bates: PIGORS-0014); Exhibit Q (Rebuttal Matrix — Adversary Assertions, Bates: PIGORS-0017); Exhibit R (Master Prosecution Timeline, Bates: PIGORS-0018)

## 5. SHARED EXHIBIT MAP

| Exhibit | Bates | Title | Stacks Using |
|---------|-------|-------|-------------|
| Exhibit A | PIGORS-0001 | AppClose Communication Record — Complete | 01_COA_366810, 02_TRIAL_14TH, 03_FEDERAL_1983, 04_JTC_MCNEILL, 04_MSC_ORIGINAL_ACTION, 05_BAR_BARNES, 06_EMERGENCY |
| Exhibit B | PIGORS-0002 | AppClose Psychological Analysis | 01_COA_366810, 02_TRIAL_14TH |
| Exhibit C | PIGORS-0003 | Drug Screen Results — NEGATIVE | 01_COA_366810, 03_FEDERAL_1983 |
| Exhibit D | PIGORS-0004 | HealthWest Evaluation #1 — ALL ZEROS | 01_COA_366810, 03_FEDERAL_1983 |
| Exhibit E | PIGORS-0005 | HealthWest Evaluation #2 — "Rule Out" After Judge Letter | 01_COA_366810, 03_FEDERAL_1983, 04_JTC_MCNEILL |
| Exhibit F | PIGORS-0006 | Judge McNeill Communication to HealthWest Evaluator | 01_COA_366810, 03_FEDERAL_1983, 04_JTC_MCNEILL |
| Exhibit G | PIGORS-0007 | Albert Watson Premeditation Statement | 01_COA_366810, 03_FEDERAL_1983, 02_TRIAL_14TH |
| Exhibit H | PIGORS-0008 | Lori Watson Illegal Recording — MCL 750.539c | 01_COA_366810 |
| Exhibit I | PIGORS-0009 | Police Investigation Reports (9) — Zero Findings | 01_COA_366810, 03_FEDERAL_1983, 02_TRIAL_14TH |
| Exhibit J | PIGORS-0010 | Ex Parte Order Statistical Analysis | 01_COA_366810, 04_JTC_MCNEILL, 04_MSC_ORIGINAL_ACTION |
| Exhibit K | PIGORS-0011 | Incarceration Records — 59+ Days | 01_COA_366810, 03_FEDERAL_1983, 02_TRIAL_14TH |
| Exhibit L | PIGORS-0012 | Employment Termination Records — 3 Job Losses | 03_FEDERAL_1983, 02_TRIAL_14TH |
| Exhibit M | PIGORS-0013 | Housing Loss Documentation | 03_FEDERAL_1983, 02_TRIAL_14TH |
| Exhibit N | PIGORS-0014 | Damages Itemization Schedule | 01_COA_366810, 02_TRIAL_14TH, 03_FEDERAL_1983, 04_JTC_MCNEILL, 04_MSC_ORIGINAL_ACTION, 05_BAR_BARNES, 06_EMERGENCY |
| Exhibit O | PIGORS-0015 | Constitutional Violation Map | 01_COA_366810, 03_FEDERAL_1983 |
| Exhibit P | PIGORS-0016 | Judicial Canon Violation Matrix | 01_COA_366810, 04_JTC_MCNEILL, 04_MSC_ORIGINAL_ACTION |
| Exhibit Q | PIGORS-0017 | Rebuttal Matrix — Adversary Assertions | 01_COA_366810, 02_TRIAL_14TH, 03_FEDERAL_1983, 04_JTC_MCNEILL, 04_MSC_ORIGINAL_ACTION, 05_BAR_BARNES, 06_EMERGENCY |
| Exhibit R | PIGORS-0018 | Master Prosecution Timeline | 01_COA_366810, 02_TRIAL_14TH, 03_FEDERAL_1983, 04_JTC_MCNEILL, 04_MSC_ORIGINAL_ACTION, 05_BAR_BARNES, 06_EMERGENCY |
| Exhibit S | PIGORS-0019 | AppClose Violation Record — 44 Incidents | 01_COA_366810, 02_TRIAL_14TH |
| Exhibit T | PIGORS-0020 | Emily Watson Employment — Kent County Prosecutor | 01_COA_366810, 02_TRIAL_14TH |
| Exhibit U | PIGORS-0021 | Parental Alienation Assessment | 01_COA_366810, 02_TRIAL_14TH |

## 6. LEGAL THEORY CROSS-REFERENCE


---
*Cross-Reference Matrix generated 2026-03-04 22:17 by Agent-148*
