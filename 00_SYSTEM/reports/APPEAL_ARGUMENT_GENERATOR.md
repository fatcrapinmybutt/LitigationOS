# Appeal Argument Generator — Tool #243

**Case:** COA 366810 (Pigors v Watson)
**Court:** Michigan Court of Appeals
**Generated:** 2026-03-19 09:43:06
**Database:** litigation_context.db

---

## Data Sources

| Table | Query | Results |
|-------|-------|---------|
| judicial_violations | WHERE judge_name LIKE '%mcneill%' | 1127 |
| authority_chains | SELECT * (all chains) | 28 |
| docket_events | SELECT * ORDER BY event_date_iso | 221 |
| evidence_quotes | LIKE search per argument keywords | 662 per argument (capped at 200) |

---

# ARG-1: Due Process Violations

## Issue

Whether the trial court violated Plaintiff-Appellant's procedural due process rights under the Fourteenth Amendment and Const 1963, art 1, § 17 by entering ex parte orders without notice or opportunity to be heard.

## Standard of Review

Constitutional questions are reviewed de novo. Const 1963, art 1, § 17; US Const, Am XIV. Due process violations are questions of law reviewed without deference. In re Rood, 483 Mich 73, 91 (2009).

## Rule

### Controlling Authorities

1. US Const, Am XIV (Due Process Clause)
2. Const 1963, art 1, § 17 (Michigan Due Process)
3. Mathews v Eldridge, 424 US 319 (1976) (three-factor balancing test)
4. In re Rood, 483 Mich 73, 91 (2009) (de novo review of constitutional questions)
5. MCR 3.207(B) (ex parte orders in domestic relations)
6. Troxel v Granville, 530 US 57 (2000) (parental rights as fundamental liberty interest)

### Authority Chains from Database (7 chains)

- **MCR 2.003(C)** [COMPLETE]: ex parte communication
- **MCL 600.2950** [COMPLETE]: due process violation
- **42 USC 1983** [COMPLETE]: 14th Amendment due process
- **MCR 9.104-9.121** [COMPLETE]: ex parte contact
- **42 USC § 1983; Flagg Bros. v. Brooks, 436 US 149 (1978); Monroe v. Pape, 365 US 167 (1961)** [COMPLETE]: Deprivation of rights under color of law
- **In re Dettmer, 260 Mich App 356 (2004)** [COMPLETE]: 567-day denial of parenting time constitutes constructive restraint
- **Troxel v Granville, 530 US 57 (2000)** [COMPLETE]: Suspension of all parenting time without evidentiary hearing violates substantive due process

## Application

**Judicial violations found:** 400 (severity: {'medium': 73, 'low': 7, 'high': 99, 'critical': 221})

### Key Violations

**JV-014f622f4185** — MRE 613(b) — Prior inconsistent statement [financial] [MEDIUM]

> notice. Based  on a motion  by either  party  or a recommendation  following  a review  by the friend  of the court,  the amount abated  may  be later  corrected  based  on the parties'  incomes  or ability

*Evidence:* MRE 613(b) — Prior inconsistent statement [financial]

**JV-01fab6258d2e** — MCR 3.210(C) [MEDIUM]

> Post-judgment hearings must be noticed and allow time to respond unless waived.

*Evidence:* MCR 3.210(C)

**JV-04a61100a989** — MRE 613(b) — Prior inconsistent statement [hearing] [MEDIUM]

> notice,  or that  notice  itself  will  precipitate  adverse  action"). (Michigan  Courts) o   Despite  my  timely  objection  and  repeated  requests  for  a prompt evidentiary  hearing,  the  suspension

*Evidence:* MRE 613(b) — Prior inconsistent statement [hearing]

**JV-07f5624cbf5c** — MRE 613(b) — Prior inconsistent statement [hearing] [MEDIUM]

> hearings  where  Judge  McNeill  muted my  microplione,  cut  me  off  mid-objection,  or instructed  me  not  to file  further materials  becarise  she would  not  look  at them. As a self-represented  liti

*Evidence:* MRE 613(b) — Prior inconsistent statement [hearing]

**JV-09e28dd2ab10** — MRE 613(b) — Prior inconsistent statement [hearing] [MEDIUM]

> Hearing.   Hearing Comments: If you  require  special  accommodations  to use  the  court  because  of a disability  or if you  require  a foreign  languageinterpreter  to help you  fully  participate  in co

*Evidence:* MRE 613(b) — Prior inconsistent statement [hearing]

**JV-0c38a7d5256c** — MCL 600.2950/2950a; MCR 3.207(B) [MEDIUM]

> Intentional use of PPO + contempt hearings to disrupt ECE

*Evidence:* MCL 600.2950/2950a; MCR 3.207(B)

**JV-0def9b508db5** — MCR 2.107; MCR 2.612(C) [MEDIUM]

> Possibly “Notice of Appearance” or similar if required by local court.

*Evidence:* MCR 2.107; MCR 2.612(C)

### Supporting Evidence (15 items)

| Ref | Doc ID | Page | Source | Snippet |
|-----|--------|------|--------|---------|
| EQ-1 | 2 | 1 | PDF_COURT_DOC | HEARING  11/26/2025 EMILY  A. WATSON, Defendant Defendant  requested,  and  the  |
| EQ-2 | 2 | 1 | PDF_COURT_DOC | hearing  was adjourned  for  Plaintiff  to obtain  a mental  health  assessment. |
| EQ-3 | 2 | 1 | PDF_COURT_DOC | hearing  and subpoenaed  the   which  occurred  on 1 1/26/25. Law If a  parentin |
| EQ-4 | 3 | 1 | PDF_COURT_DOC | notice  when  parenting  time  wifl not occur. (i) Any  other  reasonable  condi |
| EQ-5 | 4 | 1 | PDF_COURT_DOC | Defendant.  The  Court  ordered  that  once  he provided  the  assessment  as re |
| EQ-6 | 4 | 1 | PDF_COURT_DOC | hearing  would  be set. The Court  received  the  2nd Assessment  on 9/12/25.  A |
| EQ-7 | 4 | 1 | PDF_COURT_DOC | hearing  and  subpoenaed  the  two health  west  staff  for  the next  hearing,  |
| EQ-8 | 4 | 1 | PDF_COURT_DOC | hearing  on the Father's  7'h  PPO  violation  occurred.  He pled  guilty and re |
| EQ-9 | 5 | 1 | PDF_COURT_DOC | the Court.  He is to inform  the  assessor  of  ALL  the information that was pr |
| EQ-10 | 5 | 1 | PDF_COURT_DOC | hearing  on 8/22/25. On 9/22/2025,  the  Court  asked  the Plaintiff  to undergo |

### Relevant Procedural Events

- **2023-11-01** — PPO Issued — Domestic (order)
- **2023-11-17** — c. I am the defendanUrespondent. d. Please note my contact information for any related correspondence or additional instructions: @ Email: andrewjpigo (hearing)
- **2023-11-17** — c. I am the deTendant/respondent. d. Please note my contact information for any related correspondence or additional instructions: * Email: andrewjpig (hearing)
- **2023-12-04** — Judge: JENNY L MCNEILL 58235 Bar no. [a1. Thisorderisenteredafterhearing. THE COURT FINDS: 2. A motion was filed to E]a. modifythepersonalprot (hearing)
- **2024-01-04** — AMAYASHOI  UCCVPFK Muskegon  County REGISTER OF ACTIONS REL2 10 6 9/11/25 11:00:54 Pg:  2 Caseload Dsp:  OEP Crt : C 14 Case:  2023 61  Jur:  MCNEILL  (hearing)
- **2024-01-07** — PPO Violation Hearing — Show Cause (hearing)
- **2024-03-22** — Motion for Hearing on PPO Granted (motion)
- **2024-04-11** — HEARING  INFORMATION** SET NEXT DATE:  PPOH 04/11/2024  10:00 AM MCNEILL  COURTROOM:  CCG IN PERSON ROOM G 03/29/2024  D 001  RNU PROO (hearing)
- **2024-04-11** — HEARING GRANTED SET  NEXT  DATE:  PPOH 04/11/2024  10:00  AM MCNEILL  COURTROOM:  CCG IN  PERSON COURTROOM G,  4TH  FLOOR 04/09/2024 (hearing)
- **2024-04-11** — NOTICE  TO APPEAR NOTICE  TO APPEAR (notice)

## Conclusion

The trial court's actions constitute reversible error requiring vacatur and remand. DB evidence: 400 judicial violations found (query: judicial_violations WHERE judge_name LIKE '%mcneill%' filtered by [due process, ex parte, notice...]), 200 supporting evidence quotes (query: evidence_quotes WHERE quote_text LIKE '%keyword%'), 7 authority chains (query: authority_chains filtered by argument keywords).

---

# ARG-2: Abuse of Discretion in Custody Determination

## Issue

Whether the trial court abused its discretion by restricting Plaintiff-Appellant's parenting time without adequate evidentiary basis and without proper consideration of the best-interest factors under MCL 722.23.

## Standard of Review

Custody decisions are reviewed for abuse of discretion. MCL 722.28. The trial court's findings of fact are reviewed for clear error. A finding is clearly erroneous if, after review of the entire record, the appellate court is left with the definite and firm conviction that a mistake was made. Pierron v Pierron, 486 Mich 81, 85 (2010).

## Rule

### Controlling Authorities

1. MCL 722.23 (Best Interest Factors)
2. MCL 722.27 (Court authority to modify custody)
3. MCL 722.27a (Parenting time)
4. MCL 722.28 (Appellate review standard)
5. Pierron v Pierron, 486 Mich 81 (2010) (clear error review of findings)
6. Vodvarka v Grasmeyer, 259 Mich App 499 (2003) (proper cause/change of circumstances)
7. Shade v Wright, 291 Mich App 17 (2010) (parenting time modification standard)

### Authority Chains from Database (3 chains)

- **MCR 3.206(A)** [COMPLETE]: best interest of child
- **In re Dettmer, 260 Mich App 356 (2004)** [COMPLETE]: 567-day denial of parenting time constitutes constructive restraint
- **Troxel v Granville, 530 US 57 (2000)** [COMPLETE]: Suspension of all parenting time without evidentiary hearing violates substantive due process

## Application

**Judicial violations found:** 335 (severity: {'medium': 117, 'low': 5, 'high': 74, 'critical': 139})

### Key Violations

**JV-00784fbb7588** — MCR / Canon — PROCEDURAL_MISCONDUCT [MEDIUM]

> Andrew requested make-up time for the parenting days Emily withheld, but she refused without explanation.

*Evidence:* MCR / Canon — PROCEDURAL_MISCONDUCT

**JV-0195e2fc64ba** — MCR / Canon — PROCEDURAL_MISCONDUCT [MEDIUM]

> The dates and instances contained in this affidavit are extracted from the AppClose co-parenting application,parenting time journals, police reports, and photographic evidence.

*Evidence:* MCR / Canon — PROCEDURAL_MISCONDUCT

**JV-01fa1732330f** — MRE 613(b) — Prior inconsistent statement [child_welfare] [MEDIUM]

> best interest  of  the child  to c}iange  parenting  time  (F 5. of  form) Plaintiff  requested  the Court  to Order  parenting  time  be changed  (G 6. of  form). Attached  to the Motion  was 16 additional  pages

*Evidence:* MRE 613(b) — Prior inconsistent statement [child_welfare]

**JV-036917e8de0f** — MCR / Canon — PROCEDURAL_MISCONDUCT [MEDIUM]

> Emily’s inability to provide a stable, consistent, and parent-centered home environment for Lincoln reinforces that her custody arrangement is not in Lincoln’s best interests. Instead, Lincoln appears to have a stronger reliance on his grandparents r

*Evidence:* MCR / Canon — PROCEDURAL_MISCONDUCT

**JV-0383154fd78a** — MCR / Canon — PROCEDURAL_MISCONDUCT [MEDIUM]

> Denying parenting time on holidays, birthdays, and without justification.

*Evidence:* MCR / Canon — PROCEDURAL_MISCONDUCT

**JV-0459c4edf2bc** — MRE 613(b) — Prior inconsistent statement [ppo] [MEDIUM]

> dismissed. IT IS FURTHER  ORDERED  that  this Judgment  of Custody,  Parenting  Time,  and Chi!d Support  is the initial  Order  regarding  custody  and parenting  time,  issued  by this Court. IT !S FURTHER  OR

*Evidence:* MRE 613(b) — Prior inconsistent statement [ppo]

**JV-0571e0e93543** — MCL 600.2950/2950a; Canons 2/3; MCR 3.207(B) [MEDIUM]

> Motion to Revoke Child Support Arrears and Modify Custody and Parenting Time

*Evidence:* MCL 600.2950/2950a; Canons 2/3; MCR 3.207(B)

### Supporting Evidence (15 items)

| Ref | Doc ID | Page | Source | Snippet |
|-----|--------|------|--------|---------|
| EQ-1 | 2 | 1 | PDF_COURT_DOC | HEARING  11/26/2025 EMILY  A. WATSON, Defendant Defendant  requested,  and  the  |
| EQ-4 | 3 | 1 | PDF_COURT_DOC | notice  when  parenting  time  wifl not occur. (i) Any  other  reasonable  condi |
| EQ-10 | 5 | 1 | PDF_COURT_DOC | hearing  on 8/22/25. On 9/22/2025,  the  Court  asked  the Plaintiff  to undergo |
| EQ-14 | 6 | 1 | PDF_COURT_DOC | hearing  he was  given  a suspended  sentence because  he said  he understood  w |
| EQ-18 | 10 | 1 | PDF_COURT_DOC | best interests  of  the child  standard  under  MCL  722.23.   This  request  is |
| EQ-34 | 29 | 1 | PDF_COURT_DOC | HEARING EMILY  WATSON, Defendant. Andrew  Pigors Self-Represented  Litigant Jenn |
| EQ-35 | 29 | 1 | PDF_COURT_DOC | hearing  was  held;  and  the  Court  rendered  an oral  opinion.  The  Defendan |
| EQ-36 | 29 | 1 | PDF_COURT_DOC | best interest  factors;  the Plaintiff  filed  an objection,  but  failed  to fo |
| EQ-37 | 31 | 1 | PDF_COURT_DOC | HEARING  11/26/2025 EMILY  A. WATSON, Defendant Defendant  requested,  and the C |
| EQ-39 | 31 | 1 | PDF_COURT_DOC | hearing  and subpoenaed  the two health  west  staff  for the next hearing,  whi |

### Relevant Procedural Events

- **2023-12-04** — 2023 (filing)
- **2024-04-05** — IT IS ORDERED that Plaintiff filed a Complaint for Custody, Parenting Time and Child ori April 5, 2024. Pigors v ll'atsnn Page l of 14 Judgment (order)
- **2024-04-11** — Custody Complaint Filed by Watson (filing)
- **2024-04-12** — Denied.  Ordcr entered on April 12, 2024. April 11, 2024: Plaintiff filed a Motion regarding Custody. Plaintiff addressed the Best Interes (motion_filed)
- **2024-04-12** — Denied.  Order entered on April 12, 2024. April 11, 2024: Plaintiff filed a Motion regarding Custody. Plaintiff addresscd the Best Intere (order)
- **2024-04-29** — PIGORS v WATSON Fn,E # 2024-001507-DC Recommendation dated 6/5/24 PAGE 2 5. On April 29, 2024 an Ex Parte Order for Custody, Parenting Time and Child  (ex_parte_order)
- **2024-04-29** — IT IS FURTHER ORDERED that parties participated in a Facilitative Information Gathering Conference which resulted in a temporary Order titled Ex Parte (ex_parte_order)
- **2024-05-02** — g LDW During Parenting Time Misbehavior: March 26–May 2, 2024: Emily withheld LDW for over 37 days without a co (parenting_time)
- **2024-05-02** — urt-ordered parenting time, including: March 26 – May 2, 2024 (37 consecutive days) October 20 – November 12, 2 (order)
- **2024-05-02** — ing Parenting Time: Withheld LDW from March 26 to May 2, 2024, for 37 consecutive days without legal justificat (parenting_time)

## Conclusion

The trial court's actions constitute reversible error requiring vacatur and remand. DB evidence: 335 judicial violations found (query: judicial_violations WHERE judge_name LIKE '%mcneill%' filtered by [custody, parenting, best interest...]), 200 supporting evidence quotes (query: evidence_quotes WHERE quote_text LIKE '%keyword%'), 3 authority chains (query: authority_chains filtered by argument keywords).

---

# ARG-3: Ex Parte Communications

## Issue

Whether the trial court engaged in improper ex parte communications with Defendant's counsel, the FOC, or other parties in violation of MCR 2.003 and the Michigan Code of Judicial Conduct.

## Standard of Review

Judicial disqualification is reviewed for abuse of discretion. MCR 2.003(D). However, actual bias is reviewed de novo as a constitutional question. Armstrong v Ypsilanti Charter Twp, 248 Mich App 573, 597 (2001).

## Rule

### Controlling Authorities

1. MCR 2.003(C) (Grounds for disqualification)
2. MCJC Canon 2 (Impropriety and appearance of impropriety)
3. MCJC Canon 3(A)(4) (Prohibition on ex parte communications)
4. Armstrong v Ypsilanti Charter Twp, 248 Mich App 573 (2001)
5. Cain v Dep't of Corrections, 451 Mich 470 (1996) (due process requires impartial tribunal)
6. In re MKK, 286 Mich App 546 (2009) (ex parte communications as basis for disqualification)

### Authority Chains from Database (8 chains)

- **MCR 2.003(C)** [COMPLETE]: personal bias/prejudice
- **MCR 2.003(C)** [COMPLETE]: ex parte communication
- **MCR 2.003(C)** [COMPLETE]: personal knowledge of disputed facts
- **MCR 2.003(C)** [COMPLETE]: appearance of impropriety
- **MCR 9.104-9.121** [COMPLETE]: ex parte contact
- **MCR 2.003(C)(1); Cain v. Dept of Corrections, 451 Mich 470 (1996)** [COMPLETE]: Prejudice to administration of justice
- **MCR 2.003(C)(1); Cain v. Dept of Corrections, 451 Mich 470 (1996)** [COMPLETE]: Prejudice to substantial rights
- **In re Dettmer, 260 Mich App 356 (2004)** [COMPLETE]: 567-day denial of parenting time constitutes constructive restraint

## Application

**Judicial violations found:** 681 (severity: {'medium': 205, 'low': 4, 'high': 163, 'critical': 309})

### Key Violations

**JV-00784fbb7588** — MCR / Canon — PROCEDURAL_MISCONDUCT [MEDIUM]

> Andrew requested make-up time for the parenting days Emily withheld, but she refused without explanation.

*Evidence:* MCR / Canon — PROCEDURAL_MISCONDUCT

**JV-01542861827f** — MCR / Canon — PROCEDURAL_MISCONDUCT [MEDIUM]

> Exposing Lincoln to unstable situations, including medical neglect and unexplained injuries.

*Evidence:* MCR / Canon — PROCEDURAL_MISCONDUCT

**JV-0195e2fc64ba** — MCR / Canon — PROCEDURAL_MISCONDUCT [MEDIUM]

> The dates and instances contained in this affidavit are extracted from the AppClose co-parenting application,parenting time journals, police reports, and photographic evidence.

*Evidence:* MCR / Canon — PROCEDURAL_MISCONDUCT

**JV-0368cb779314** — MCR / Canon — PPO_WEAPONIZATION [MEDIUM]

> She failed to properly serve the PPO extension, violating legal procedures.

*Evidence:* MCR / Canon — PPO_WEAPONIZATION

**JV-036917e8de0f** — MCR / Canon — PROCEDURAL_MISCONDUCT [MEDIUM]

> Emily’s inability to provide a stable, consistent, and parent-centered home environment for Lincoln reinforces that her custody arrangement is not in Lincoln’s best interests. Instead, Lincoln appears to have a stronger reliance on his grandparents r

*Evidence:* MCR / Canon — PROCEDURAL_MISCONDUCT

**JV-0383154fd78a** — MCR / Canon — PROCEDURAL_MISCONDUCT [MEDIUM]

> Denying parenting time on holidays, birthdays, and without justification.

*Evidence:* MCR / Canon — PROCEDURAL_MISCONDUCT

**JV-0571e0e93543** — MCL 600.2950/2950a; Canons 2/3; MCR 3.207(B) [MEDIUM]

> Motion to Revoke Child Support Arrears and Modify Custody and Parenting Time

*Evidence:* MCL 600.2950/2950a; Canons 2/3; MCR 3.207(B)

### Supporting Evidence (15 items)

| Ref | Doc ID | Page | Source | Snippet |
|-----|--------|------|--------|---------|
| EQ-1 | 2 | 1 | PDF_COURT_DOC | HEARING  11/26/2025 EMILY  A. WATSON, Defendant Defendant  requested,  and  the  |
| EQ-37 | 31 | 1 | PDF_COURT_DOC | HEARING  11/26/2025 EMILY  A. WATSON, Defendant Defendant  requested,  and the C |
| EQ-53 | 36 | 1 | PDF_COURT_DOC | ex parte order suspending  his parenting  time  is denied.  The  Court  also  no |
| EQ-58 | 43 | 1 | PDF_COURT_DOC | hearing  on October  29, 2025. 2.   Lack  of  notice  and  ambush  at a schedule |
| EQ-62 | 45 | 1 | PDF_COURT_DOC | hearings  and jail  time,  which  in  him  caused  job  loss  and  housing  inst |
| EQ-64 | 45 | 1 | PDF_COURT_DOC | notice  of SuSpenSlOn. o   I was  not  served  with  the  ex parte  motion  or o |
| EQ-72 | 48 | 1 | PDF_COURT_DOC | hearing  (Counts  #5 and  #6). At  the February  28, 2025  PPO  violation  heari |
| EQ-74 | 50 | 1 | PDF_COURT_DOC | the court. 2.  Canon  2(A)  and  2(B)  -  Avoiding  impropriety  and  the  appea |
| EQ-75 | 50 | 1 | PDF_COURT_DOC | hearings. (Micl'iigan  Courts) o   MCR  3.207(B)(1)  and  (B)(5)-(6)  govern  ex |
| EQ-78 | 51 | 1 | PDF_COURT_DOC | hearing  occurred,  despite  my  objection  and  repeated  requests, and  withou |

### Relevant Procedural Events

- **2023-10-15** — My requests for communication were lawful and aligned with MCL 722.23(a), which recognizes the importance of maintaining love, affection, and emotiona (motion)
- **2024-04-11** — PPO Amended — Ex Parte Order (ex_parte_order)
- **2024-04-29** — PIGORS v WATSON Fn,E # 2024-001507-DC Recommendation dated 6/5/24 PAGE 2 5. On April 29, 2024 an Ex Parte Order for Custody, Parenting Time and Child  (ex_parte_order)
- **2024-04-29** — IT IS FURTHER ORDERED that parties participated in a Facilitative Information Gathering Conference which resulted in a temporary Order titled Ex Parte (ex_parte_order)
- **2024-07-01** — Ex Parte Custody Order Entered (order)
- **2024-07-17** — STATE  OF  MICHIGAN IN THE CIRCUIT COURT FOR THE COUNTY OF MUSKEG-ON ANDREW PIGORS, Plaintiff, File No: 2024-001507-DC Hon. Jenny L. McNeill VS. CUSTO (hearing)
- **2025-02-28** — hearing (Counts #5 and #6). At the February 28, 2025 PPO violation hearing, the record reflects side-channel communication minimizing the (hearing)
- **2025-02-28** — PPO Violation Hearing (Counts 5 & 6) (hearing)
- **2025-04-25** — FILED 4/25/2025 14th  CIRCUIT  COURT MUSKEGON  COUNTY ST ATE OF MICHIGAN IN THE 14TH CIRCUIT COURT FOR TIIE COUNTY OF MUSKEGON - FAMILY DIVISION Case  (ex_parte_order)
- **2025-05-16** — 5. Punitive structural barriers to access the court. o A May 16, 2025 order imposed a $250.00 filing bond in the custody case, that has functioned as  (evidentiary_hearing)

## Conclusion

The trial court's actions constitute reversible error requiring vacatur and remand. DB evidence: 681 judicial violations found (query: judicial_violations WHERE judge_name LIKE '%mcneill%' filtered by [ex parte, communication, off-record...]), 200 supporting evidence quotes (query: evidence_quotes WHERE quote_text LIKE '%keyword%'), 8 authority chains (query: authority_chains filtered by argument keywords).

---

# ARG-4: Failure to Make Required Findings Under MCL 722.27a

## Issue

Whether the trial court erred by restricting parenting time without making the specific findings required by MCL 722.27a(6), including findings that parenting time would endanger the child's physical, mental, or emotional health.

## Standard of Review

Failure to make required findings is a question of law reviewed de novo. The trial court's findings, where made, are reviewed for clear error. Lieberman v Orr, 319 Mich App 68, 78 (2017).

## Rule

### Controlling Authorities

1. MCL 722.27a(6) (Required findings for parenting time restriction)
2. MCL 722.27a(7) (Conditions on parenting time)
3. Lieberman v Orr, 319 Mich App 68 (2017) (required findings)
4. Shade v Wright, 291 Mich App 17 (2010) (parenting time standard)
5. Brown v Loveman, 260 Mich App 576 (2004) (necessity of findings on record)
6. Berger v Berger, 277 Mich App 700 (2008) (clear error in custody findings)

## Application

**Judicial violations found:** 249 (severity: {'medium': 67, 'low': 5, 'high': 63, 'critical': 114})

### Key Violations

**JV-00784fbb7588** — MCR / Canon — PROCEDURAL_MISCONDUCT [MEDIUM]

> Andrew requested make-up time for the parenting days Emily withheld, but she refused without explanation.

*Evidence:* MCR / Canon — PROCEDURAL_MISCONDUCT

**JV-0195e2fc64ba** — MCR / Canon — PROCEDURAL_MISCONDUCT [MEDIUM]

> The dates and instances contained in this affidavit are extracted from the AppClose co-parenting application,parenting time journals, police reports, and photographic evidence.

*Evidence:* MCR / Canon — PROCEDURAL_MISCONDUCT

**JV-01fa1732330f** — MRE 613(b) — Prior inconsistent statement [child_welfare] [MEDIUM]

> best interest  of  the child  to c}iange  parenting  time  (F 5. of  form) Plaintiff  requested  the Court  to Order  parenting  time  be changed  (G 6. of  form). Attached  to the Motion  was 16 additional  pages

*Evidence:* MRE 613(b) — Prior inconsistent statement [child_welfare]

**JV-036917e8de0f** — MCR / Canon — PROCEDURAL_MISCONDUCT [MEDIUM]

> Emily’s inability to provide a stable, consistent, and parent-centered home environment for Lincoln reinforces that her custody arrangement is not in Lincoln’s best interests. Instead, Lincoln appears to have a stronger reliance on his grandparents r

*Evidence:* MCR / Canon — PROCEDURAL_MISCONDUCT

**JV-0383154fd78a** — MCR / Canon — PROCEDURAL_MISCONDUCT [MEDIUM]

> Denying parenting time on holidays, birthdays, and without justification.

*Evidence:* MCR / Canon — PROCEDURAL_MISCONDUCT

**JV-0459c4edf2bc** — MRE 613(b) — Prior inconsistent statement [ppo] [MEDIUM]

> dismissed. IT IS FURTHER  ORDERED  that  this Judgment  of Custody,  Parenting  Time,  and Chi!d Support  is the initial  Order  regarding  custody  and parenting  time,  issued  by this Court. IT !S FURTHER  OR

*Evidence:* MRE 613(b) — Prior inconsistent statement [ppo]

**JV-0571e0e93543** — MCL 600.2950/2950a; Canons 2/3; MCR 3.207(B) [MEDIUM]

> Motion to Revoke Child Support Arrears and Modify Custody and Parenting Time

*Evidence:* MCL 600.2950/2950a; Canons 2/3; MCR 3.207(B)

### Supporting Evidence (15 items)

| Ref | Doc ID | Page | Source | Snippet |
|-----|--------|------|--------|---------|
| EQ-4 | 3 | 1 | PDF_COURT_DOC | notice  when  parenting  time  wifl not occur. (i) Any  other  reasonable  condi |
| EQ-40 | 31 | 1 | PDF_COURT_DOC | best interests  of the child. It is presumed  to be in the best interests of a c |
| EQ-41 | 32 | 1 | PDF_COURT_DOC | notice  when  parenting  time  will not occur. (i) Any  other  reasonable  condi |
| EQ-246 | 144 | 1 | PDF_COURT_DOC | notice  & approval  requirements;  travel  limits  if  needed. 4  Halloween2024  |
| EQ-247 | 144 | 1 | PDF_COURT_DOC | hearing;  require  specific  danger findings. 9 i Lincoln's 3rd birthday in 2025 |
| EQ-248 | 144 | 1 | PDF_COURT_DOC | hearing;  clear  tindings  on record. 12 i Misstatement that father "refused"  s |
| EQ-351 | 486 | 1 | PDF_COURT_DOC | ex parte suspension MCL 722.27a(3); holiday-priority  guidelines; MCR 3.207; MCR |
| EQ-352 | 486 | 1 | PDF_COURT_DOC | Ex parte suspension since -08/08/2025   i Ongoing suspension of all parenting ti |
| EQ-353 | 486 | 1 | PDF_COURT_DOC | ex parte-based shutdown  i MCL 722.27a(3); birthday/special-event guidelines  i  |
| EQ-575 | 657 | 83 | PDF_COURT_DOC | the PPO, endangering LDW during the incident. On October 20, 2024, her father, A |

### Relevant Procedural Events

- **2024-09-20** — hreatening behavior, including road harassment on September 20, 2024, violating the PPO and endangering LDW. III. APPL (ppo)
- **2024-10-20** — the PPO, endangering LDW during the incident. On October 20, 2024, her father, Albert Watson, forcibly removed LDW (ppo)
- **2025-01-15** — Motion for Parenting Time Filed by Father (motion_filed)
- **2025-02-14** — Motion Regarding Parenting Time Filed by Father (motion_filed)
- **2025-08-08** — Ex parte suspension since -08/08/2025  i Ongoing suspension of all parenting time (months-long shutdown) i MCL 722.27a(3); MCR 3.207; MCR 3.310(B); (parenting_time)

## Conclusion

The trial court's actions constitute reversible error requiring vacatur and remand. DB evidence: 249 judicial violations found (query: judicial_violations WHERE judge_name LIKE '%mcneill%' filtered by [finding, 722.27, parenting...]), 62 supporting evidence quotes (query: evidence_quotes WHERE quote_text LIKE '%keyword%'), 0 authority chains (query: authority_chains filtered by argument keywords).

---

## Traceable Queries

```sql
-- Violations: SELECT * FROM judicial_violations WHERE LOWER(judge_name) LIKE '%mcneill%' ORDER BY severity DESC
-- Authorities: SELECT * FROM authority_chains ORDER BY id
-- Procedural: SELECT * FROM docket_events ORDER BY event_date_iso
-- Evidence: SELECT * FROM evidence_quotes WHERE LOWER(quote_text) LIKE '%keyword%' LIMIT 200
```