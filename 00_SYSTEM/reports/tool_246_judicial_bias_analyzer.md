# ⚖️ JUDICIAL BIAS PATTERN ANALYZER
**Generated:** 2026-03-19 09:41
**Case:** Pigors v. Watson | 14th Circuit Court
**Subject:** Hon. Jenny L. McNeill
**Legal Standard:** *Crampton v Dept of State*, 395 Mich 347 (1975)
**Total Documented Violations:** 1,127
**Bias Composite Score:** 21/60 (35.0%)

## CRAMPTON OBJECTIVE BIAS TEST
> *Crampton v Dept of State*, 395 Mich 347 (1975): A judge should be disqualified
> when a reasonable person, knowing all the circumstances, would have a legitimate
> basis to question the judge's impartiality. This is an **objective** test — actual
> bias need not be proven; the **appearance** of bias suffices.

### Bias Indicators
| # | Indicator | Score | Finding | Traceable Query |
|---|-----------|-------|---------|-----------------|
| 1 | Ruling Asymmetry | ░░░░░░░░░░ 0/10 | 2 rulings favoring Emily vs 0 favoring Andrew (2.0% vs 0.0%) | `SELECT * FROM docket_events — analyzed 100 rulings` |
| 2 | Procedural Shortcuts | ██████████ 10/10 | 31 orders issued without hearing or notice (violates MCR 2.119 right to respond) | `SELECT * FROM docket_events WHERE title/summary contains 'without hearing/ex par` |
| 3 | Canon Violation Volume | ██████████ 10/10 | 1,127 documented violations — 620 critical/high severity | `SELECT COUNT(*) FROM judicial_violations — 1,127 rows` |
| 4 | FOC Communication Pattern | █░░░░░░░░░ 1/10 | 1 references to FOC/Rusco communications in evidence | `SELECT * FROM evidence_quotes WHERE quote_text LIKE '%rusco%' OR '%foc%'` |
| 5 | Appearance of Impropriety (Canon 2) | ░░░░░░░░░░ 0/10 | 0 Canon 2 violations — directly relevant to Crampton appearance test | `SELECT * FROM judicial_violations WHERE canon_number LIKE '2%'` |
| 6 | Impartiality Violations (Canon 3) | ░░░░░░░░░░ 0/10 | 0 Canon 3 violations — failure to perform duties impartially | `SELECT * FROM judicial_violations WHERE canon_number LIKE '3%'` |

**COMPOSITE SCORE: 21/60 (35.0%)**

> ⚠️ **FINDING:** Significant indicators present. Consider supplementing record
> before filing disqualification motion under MCR 2.003.

## RULING PATTERN ANALYSIS
**Total Rulings Analyzed:** 100
**Query:** `SELECT * FROM docket_events` — filtered for orders/rulings

| Direction | Count | Percentage |
|-----------|-------|------------|
| Favoring Emily Watson | 2 | 2.0% |
| Favoring Andrew Pigors | 0 | 0.0% |
| Neutral/Procedural | 98 | 98.0% |

### Procedural Shortcuts — Orders Without Hearing (31)
| Date | Description |
|------|-------------|
| 2024-07-01 | Ex Parte Custody Order Entered |
| 2024-04-11 | PPO Amended — Ex Parte Order |
| 2024-04-29 | PIGORS v WATSON Fn,E # 2024-001507-DC Recommendation dated 6/5/24 PAGE 2 5. On April 29, 2024 an Ex Parte Order for Custody, Parenting Time and Child  |
| 2024-04-29 | IT IS FURTHER ORDERED that parties participated in a Facilitative Information Gathering Conference which resulted in a temporary Order titled Ex Parte |
| 2024-07-17 | STATE  OF  MICHIGAN IN THE CIRCUIT COURT FOR THE COUNTY OF MUSKEG-ON ANDREW PIGORS, Plaintiff, File No: 2024-001507-DC Hon. Jenny L. McNeill VS. CUSTO |
| 2025-04-25 | FILED 4/25/2025 14th  CIRCUIT  COURT MUSKEGON  COUNTY ST ATE OF MICHIGAN IN THE 14TH CIRCUIT COURT FOR TIIE COUNTY OF MUSKEGON - FAMILY DIVISION Case  |
| 2025-08-06 | hearing. Appendix E - Ex Parte and Post-Ex Parte Orders in August-October 2025 The ex parte order suspending all parenting time (ente |
| 2025-08-06 | Ex Parte Paretxting-Time Suspension and Lack of Notice (August 2025) 4. August 6, 2025 - Ex parte order suspending all parenting time. o |
| 2025-08-06 | ex parte order suspending all parenting time (entered 011 or about August 6, 2025). Subsequent orders continuing the suspension (around |
| 2025-08-07 | 2025 - Ex Parte Order Pattern (CRITICAL) |
| 2025-08-08 | ex parte motion was filed. On or about August 8, 2025, the ex parte order took effect, and my parenting time has been functionally sus |
| 2025-08-08 | ex parte motion or order before an August 8, 2025 exchange. I arrived expecting my regular parenting time, and only discovered after t |
| 2025-08-08 | :ECEIa7ED  ri/t'/2025 FILED  8/8/2025 14th  CIRCUIT  COURT MUSKEGON  COUNTY STATE OF MICHIGAN IN THE1 4TH CIRCUIT COURT IN THE COUNTY OF MUSKEGON FAMI |
| 2025-08-08 | 2025 - Ex Parte Order Pattern (CRITICAL) |
| 2025-08-08 | 1. Ex Parte Order Pattern ⚠️ CRITICAL |
| 2025-08-08 | Ambush at Parenting Time Exchange — No Notice of Ex Parte |
| 2025-08-22 | 2025 - Ex Parte Order Pattern (CRITICAL) |
| 2025-08-22 | Interim Hearing on Ex Parte Order |
| 2025-08-30 | 2025 - Ex Parte Order Pattern (CRITICAL) |
| 2025-09-04 | STATE  OF  M CHIGAN IN THE CIRCUIT COURT FOR THE COUNTY OF MUSKEGON ANDREW J. PIGORS, Plaintiff CASE 2024-001507-DC HON. JENNY L. MCNEILL VS. ORDER RE |

## CANON VIOLATION BREAKDOWN
**Total Violations:** 1,127
**Query:** `SELECT * FROM judicial_violations` — 1,127 rows

| Canon | Description | Count | Critical | High | Medium | Low |
|-------|-------------|-------|----------|------|--------|-----|
| MCR 2.003 (Disqualification) | Canon MCR 2.003 (Disqualification) | 167 | 70 | 73 | 24 | 0 |
| MCR / Canon — PROCEDURAL_MISCONDUCT | Canon MCR / Canon — PROCEDURAL_MISCONDUCT | 161 | 59 | 6 | 96 | 0 |
| MCR / Canon — EX_PARTE_VIOLATION | Canon MCR / Canon — EX_PARTE_VIOLATION | 150 | 126 | 16 | 8 | 0 |
| MCL 600.2950/2950a; MCR 3.207(B) | Canon MCL 600.2950/2950a; MCR 3.207(B) | 126 | 7 | 16 | 103 | 0 |
| MCR 2.107; MCR 2.612(C) | Canon MCR 2.107; MCR 2.612(C) | 105 | 12 | 9 | 84 | 0 |
| MCL 600.2950/2950a; Canons 2/3; MCR 3.207(B) | Canon MCL 600.2950/2950a; Canons 2/3; MCR 3.207(B) | 62 | 9 | 2 | 51 | 0 |
| MRE 613(b) — Prior inconsistent statement [hearing] | Canon MRE 613(b) — Prior inconsistent statement [h | 51 | 15 | 3 | 33 | 0 |
| MCR / Canon — CREDIBILITY_FAILURE | Canon MCR / Canon — CREDIBILITY_FAILURE | 51 | 17 | 3 | 31 | 0 |
| MCR 3.207 | Canon MCR 3.207 | 35 | 5 | 30 | 0 | 0 |
| MCR / Canon — PPO_WEAPONIZATION | Canon MCR / Canon — PPO_WEAPONIZATION | 27 | 9 | 3 | 15 | 0 |
| MRE 613(b) — Prior inconsistent statement [ex_parte] | Canon MRE 613(b) — Prior inconsistent statement [e | 14 | 11 | 3 | 0 | 0 |
| Canon 2 (Impropriety/Appearance) | Canon Canon 2 (Impropriety/Appearance) | 14 | 2 | 11 | 1 | 0 |
| MRE 613(b) — Prior inconsistent statement [child_welfare] | Canon MRE 613(b) — Prior inconsistent statement [c | 11 | 0 | 0 | 6 | 5 |
| Canon 3 (Impartiality/Diligence) | Canon Canon 3 (Impartiality/Diligence) | 9 | 1 | 7 | 1 | 0 |
| MRE 613(b) — Prior inconsistent statement [child_welfare, hearing] | Canon MRE 613(b) — Prior inconsistent statement [c | 8 | 4 | 0 | 4 | 0 |

### Severity Distribution
| Severity | Count | Percentage |
|----------|-------|------------|
| Critical | 377 | 33.5% |
| High | 243 | 21.6% |
| Medium | 484 | 42.9% |
| Low | 23 | 2.0% |

### Sample Canon Violations

#### Canon MCR 2.003 (Disqualification): Canon MCR 2.003 (Disqualification)
- ,
 and  the Court  signed  an ex parte  order  suspending
 the  Plaintiff's
parenting  time.  An evidentiary
 hearing  was held on Septemb
- ,  Judge  McNeill
 signed  an ex parte  "emergency"
order  suspending
 all of  my  parenting
 time  with  my  three-year-old
 son,
Lincoln
- suspended.
3. 
Off-record,
 ex parte  handling
 of  evidence
 (USB  recording
 and  mental-health
evaluation).
o  
A USB  recording
 sub

#### Canon MCR / Canon — PROCEDURAL_MISCONDUCT: Canon MCR / Canon — PROCEDURAL_MISCONDUCT
- Emily Watson has deliberately violated Factor J and has shown no effort to encourage or foster a strong father-child relationship, warranting significant reconsideration of her custody arrangement.
- Refusing all make-up parenting time despite multiple requests.
- Citation: Parenting Time Observations, December 2024​

#### Canon MCR / Canon — EX_PARTE_VIOLATION: Canon MCR / Canon — EX_PARTE_VIOLATION
- **Event:** Emily Watson filed 32 objections against the Ex Parte Custody Order, making false claims about Plaintiff’s living conditions, finances, and parenting ability.
- EX PARTE MOTION  TO SUSPEND  PLAINTIFF'S
 PARENTING  TIME
NOW  COMES  Defendant,
 EmilyWatson,
 files  the  Emergency
 Ex Parte  Motion  to Suspend
Parenting
 Time,  station  as follows:
q, 
TheDefend
- ex parte  order  will automatically
 become  a temporary
 order  if you  do not  file a written
objection
 or motion  to modify  or rescind  the  ex parte  order  and  a request  for  a hearing.
EVen 

#### Canon MCL 600.2950/2950a; MCR 3.207(B): Canon MCL 600.2950/2950a; MCR 3.207(B)
- Financial documents (pay stubs, employment letters, etc.) to support your improved financial condition.
- If the court reopens the case, request an interim order for custody and child support until the final resolution, showing the necessity for immediate relief.
- This supports your request for a modification of custody orders based on a material change in circumstances (new financial situation, new evidence).

#### Canon MCR 2.107; MCR 2.612(C): Canon MCR 2.107; MCR 2.612(C)
- being homeless and couch surfing
Monitoring her with a webcam
throwing her off of a table
show cause #! alleged text from a random number, an Obama meme about orgies.
October 2023, I caught Emily send
- Demonstrate that reopening the case and reassessing custody would serve the best interests of Lincoln. Use this law to highlight the statutory factors the court must consider.Vodvarka v. Grasmeyer, 25
- Proof of Service: Documentation showing the other party was served with the motion.

## FOC/RUSCO COMMUNICATION PATTERN (1 references)
Evidence of potentially improper communications with FOC Pamela Rusco.

| # | Date | Speaker | Quote |
|---|------|---------|-------|
| 1 |  | COURT | Ex Parte Communications)
7. 
Order
 to obtain
 HealthWest
 evaluation,
 followed
 by  chambers-only
instructions.
o  
Af |

## McNEILL REFERENCES IN EVIDENCE (125 found)
**Query:** `SELECT * FROM evidence_quotes WHERE quote_text LIKE '%McNeill%'`

| # | Date | Speaker | Category | Quote |
|---|------|---------|----------|-------|
| 1 |  | COURT | JUDGE_ORDER | dismissed.
Dated: s/ri/;,s
N. 
ray L. MCNEILL
IRCU  
COURT  JUDGE
-2- |
| 2 | 11/26/25 | COURT | TRANSCRIPT | Judge:
 
JENNY
 L-  
MCNEILL
(231  ) 724-6251
Date:  
FRDAY
 DECEMBER
 12,
 
2025
TO:
ANDREW
 JAMES
 
PIGORS
1977
 
WHIT |
| 3 |  | COURT | TRANSCRIPT | hearing,  Judge  McNeill
 ordered  me to obtain  a
psychological
 assessment  from  HealtliWest.
o  
The  judge's
 secre |
| 4 |  | COURT | TRANSCRIPT | hearings
 where  Judge  McNeill
 muted
my  microplione,
 cut  me  off  mid-objection,
 or instructed
 me  not  to file   |
| 5 | 1/7/2025 |  | TRANSCRIPT | hearing'  1/7/2025
L]PACCCodeMCL600.2950a
 
[]pqcccooeucteoo.zgsom
i)uBge'JE!JhJYL.MCNEILL
 
P-58235
Bar  no
i  Order  e |
| 6 | 5/16/2025 |  | TRANSCRIPT | hearing'  5/16/2025
.liidge'
JENNY
 L MCNEILL
Z PACC  Code  MCL  600.2950m
P58235
Bar no.
3.0rder
 entered
 afterviolati |
| 7 | 10/18/2025 | COURT | TRANSCRIPT | hearing:  10/18/2025
.ludge.' JENNY L. MCNEILL
P-58235
Bar  no.
1. Order  entered  after  show-cause
 hearing  requested |
| 8 | 2/28/2025 |  | TRANSCRIPT | hearing'  2/28/2025
.1,,,.lge. Jenny L McNeill
t OrderenteredafterviolationhearingpursuanttoMCR3.708(H),heldasaresultof
 |
| 9 | 10/30/2024 | COURT | TRANSCRIPT | hearing'  10/30/2024
.ludge.' JENNY L. MCNEILL
P-58235
Bar nO.
1. Order  entered  after  show-cause
 hearing  requested
 |
| 10 | 6/12/2025 |  | TRANSCRIPT | hearing'  6/12/2025
.liidge'
JENNY  L MCNEILL
P58235
Bar no.
hL"",;4:ymz-r'
1.Order
 entered  after  violation  hearing  |
| 11 |  | COURT | TRANSCRIPT | Judge:
JENNY  L. MCNEILL
P-58235
Bar  no.
€  1. Thisorderisenteredafterhearing.
THECOURTFINDS:
2. A T':i;;t!On  %'ifaS ' |
| 12 |  | COURT | TRANSCRIPT | Judge:
Respondent's name, address, and telephone no.
ANDREW
 PIGORS
1977  WmTEHALL
 RD TRLR  17
MUSKEGON
 MI  49445
JENN |
| 13 |  | COURT | TRANSCRIPT | hearing.
THE  COURTFINDS:
Judge:
Respondent's name, address, and telephone no.
ANDREW
 PIGORS
1977  WmTEHALL
 RD TRLR  1 |
| 14 | 12/4/2023 | COURT | TRANSCRIPT | Judge:  JENNY L MCNEILL
58235
Bar  no.
[a1. Thisorderisenteredafterhearing.
THE  COURT  FINDS:
2. A motion  was  filed   |
| 15 | 12/4/2024 | COURT | TRANSCRIPT | Judge:  JENNY L MCNEILL
€ 1. Thisorderisenteredafterhearing.
THE  COURT  FINDS:
2. A motion  was  filed  to
[]a.  modify |
| 16 |  |  | JUDGE_ORDER | hearing:  4/1 1/2024 
,ludge'  JENNY L. MCNEILL  
P-58235
Bar no
1. Order  entered  after  show-cause
 hearing  requeste |
| 17 | 2/28/2025 |  | TRANSCRIPT | hearing'  2/28/2025
€ 
PACC  Code  MCL  600.2950a
.ludge'  Jenny L McNeill
€ 
PACC  Code  MCL  600.2950m
P-58235
Bar no. |
| 18 | 4/22/2025 | COURT | JUDGE_ORDER | hearing'
 4/22/2025
,ludge'  JENY  !-  MCNEILL
P-58235
Bar no
1. Order  entered
 after  show-cause
 hearing  requested
  |
| 19 | 04/11/2024 | COURT | TRANSCRIPT | HEARING
 
INFORMATION**
SET 
NEXT 
DATE:  
PPOH 
04/11/2024
 
10:00
 AM 
MCNEILL  
COURTROOM:
 
CCG
IN  PERSON
 ROOM  G
 |
| 20 | 04/11/2024 | COURT | TRANSCRIPT | HEARING
 GRANTED
SET  
NEXT  
DATE:
 
PPOH 
04/11/2024
 
10:00
 
AM 
MCNEILL  
COURTROOM:
 
CCG
IN  
PERSON
 COURTROOM
  |

## JUDICIAL STANDARDS COMPARISON
### Michigan Code of Judicial Conduct
| Standard | Expectation | Documented Reality |
|----------|-------------|-------------------|
| Canon 1 — Independence | Uphold integrity | 0 violations |
| Canon 2 — No Impropriety | Avoid appearance of bias | 0 violations |
| Canon 3 — Impartial Duties | Fair hearing, diligent | 0 violations |
| MCR 2.003 — Disqualification | Recuse when biased | 31 shortcuts documented |
| Due Process — 14th Amendment | Notice + opportunity to be heard | 31 orders without hearing |

## DATABASE QUERIES USED (Traceable)
```sql
-- Judicial violations count and breakdown
SELECT COUNT(*) FROM judicial_violations;
SELECT canon_number, COUNT(*) FROM judicial_violations GROUP BY canon_number;

-- Docket events ruling analysis
SELECT * FROM docket_events; -- Filtered for orders/rulings/judgments

-- McNeill evidence references
SELECT quote_text, speaker, evidence_category, date_ref FROM evidence_quotes
WHERE quote_text LIKE '%McNeill%';

-- FOC/Rusco communication search
SELECT * FROM evidence_quotes WHERE quote_text LIKE '%rusco%' OR '%foc%';
```

---
*Tool #246 — Judicial Bias Pattern Analyzer | LitigationOS*
*1,127 violations analyzed — Crampton composite: 35.0%*
*Legal standard: Crampton v Dept of State, 395 Mich 347 (1975)*