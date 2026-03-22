# Ω7 Judicial Accountability Brain — OMEGA-INFINITY Reference
> Module 7 of 12 · Cognitive Litigation Kernel v4.0
> Case: Pigors v Watson · 14th Circuit · Muskegon County

## Purpose

Centralize all judicial accountability intelligence — violation tracking, bias documentation, disqualification grounds, JTC complaint preparation, and the three-court judicial cartel analysis — into a single brain that feeds Modules M2 (Contradiction Engine), M4 (Filing Factory), M5 (Strategic Command), and M6 (Domain Specialists — Judicial submodule).

---

## 1. Judge Jenny L. McNeill — Violation Profile

### 1.1 Overview

**Presiding Judge:** Hon. Jenny L. McNeill
**Court:** 14th Circuit Court, Family Division, Muskegon County
**Case Numbers:** 2024-001507-DC, 2023-5907-PP

**Total documented violations:** `SELECT COUNT(*) FROM judicial_violations;` (current: query live — do NOT hardcode)

### 1.2 Violation Type Distribution

```sql
SELECT violation_type, COUNT(*) as cnt,
       ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM judicial_violations), 1) as pct
FROM judicial_violations
GROUP BY violation_type
ORDER BY cnt DESC;
```

**Known violation types and their significance:**

| Type | Description | Legal Basis |
|------|-------------|-------------|
| `ex_parte` | Ex parte communications or orders without proper notice | MCR 3.207(B), Canon 3(B)(7) |
| `bias` | Demonstrated prejudice or appearance of partiality | MCR 2.003(C)(1), Canon 3(B)(5) |
| `unclassified` | Violations pending categorization | — |
| `improper_procedure` | Failure to follow mandated court procedures | Various MCR |
| `canon_violation` | Direct violation of Michigan Code of Judicial Conduct | Canons 1-7 |
| `denial_of_hearing` | Denied right to be heard or present evidence | MCR 2.517(A), 14th Amendment |
| `due_process` | Constitutional due process deprivation | US Const. Amend. XIV; MI Const. Art. 1, §17 |

### 1.3 Violation Schema

```sql
PRAGMA table_info(judicial_violations);
-- id (INTEGER), violation_type (TEXT), description (TEXT), date_occurred (TEXT),
-- mcr_rule (TEXT), canon (TEXT), source_file (TEXT), source_quote (TEXT),
-- severity (INTEGER), lane (TEXT), created_at (TIMESTAMP)
```

**Critical columns:**

- `mcr_rule` — Michigan Court Rule violated (e.g., "MCR 2.003(C)")
- `canon` — Judicial Canon violated (e.g., "Canon 3")
- `severity` — Integer severity score (higher = more egregious)
- `lane` — Which case lane the violation applies to
- `source_quote` — Verbatim evidence text supporting the violation

### 1.4 MCR Rule Violation Distribution

```sql
SELECT mcr_rule, COUNT(*) as cnt
FROM judicial_violations
WHERE mcr_rule IS NOT NULL AND mcr_rule != ''
GROUP BY mcr_rule
ORDER BY cnt DESC
LIMIT 15;
```

**Top MCR violations (query for live counts):**

| MCR Rule | Subject |
|----------|---------|
| MCR 2.003(C) | Disqualification — grounds for removal |
| MCR 3.207(B) | Ex parte, temporary, and protective orders |
| MCR 3.207 | General ex parte order provisions |
| MCR 2.003 | General disqualification provisions |
| MCR 1.109 | Court records and document requirements |
| MCR 2.003(D) | Disqualification — procedure |
| MCR 2.517(A) | Findings of fact / conclusions of law |
| MCR 3.207(C) | Temporary order limitations |
| MCR 2.602(B) | Entry of judgments and orders |
| MCR 3.705 | Summary disposition |

### 1.5 Canon Violation Distribution

```sql
SELECT canon, COUNT(*) as cnt
FROM judicial_violations
WHERE canon IS NOT NULL AND canon != ''
GROUP BY canon
ORDER BY cnt DESC;
```

---

## 2. Michigan Code of Judicial Conduct — All 7 Canons

### 2.1 Canon Reference Table

```sql
SELECT canon_number, title, violation_type
FROM michigan_judicial_canons
ORDER BY canon_number;
```

| Canon | Title | Key Provision | Relevance to McNeill |
|-------|-------|---------------|---------------------|
| **Canon 1** | A Judge Should Uphold the Integrity and Independence of the Judiciary | Maintain public confidence | Berry-McNeill undisclosed relationship undermines independence |
| **Canon 2** | A Judge Should Avoid Impropriety and the Appearance of Impropriety | Appearance standard (objective) | Spousal family connection to Emily's partner creates appearance of bias |
| **Canon 3** | A Judge Should Perform the Duties of Office Impartially and Diligently | Hear both sides; no ex parte; diligence | Ex parte orders; denial of hearings; unequal treatment — MOST VIOLATED |
| **Canon 4** | A Judge May Engage in Extra-Judicial Activities | Limits on outside activities | If McNeill's former firm connections influence decisions |
| **Canon 5** | A Judge Should Regulate Extra-Judicial Activities to Minimize Conflict | Minimize conflicts of interest | Ladas, Hoopes & McNeill firm history creates ongoing conflict |
| **Canon 6** | Compensation and Expense Reimbursement | Financial disclosures | If undisclosed financial relationships exist |
| **Canon 7** | A Judge Should Refrain from Political Activity | Limits on political conduct | Not primary, but judicial election context matters |

### 2.2 Canon 3 Deep Dive (Most Violated)

Canon 3 is the primary accountability weapon. Key subsections:

| Subsection | Provision | McNeill Violation Pattern |
|-----------|-----------|--------------------------|
| 3(A)(1) | Hear and decide matters unless disqualified | Failed to recuse despite Berry conflict |
| 3(A)(4) | Be patient, dignified, courteous | Hostile record practices toward Andrew |
| 3(B)(2) | Maintain order and decorum | Unequal enforcement of courtroom rules |
| 3(B)(5) | Perform duties without bias/prejudice | Systematic bias favoring Emily |
| 3(B)(7) | No ex parte communications | Ex parte orders dominate violation count |
| 3(B)(8) | Dispose of matters promptly/efficiently | Delayed rulings on Andrew's filings; rapid action on Emily's |
| 3(C)(1) | Disqualification required | Berry-McNeill conflict triggers mandatory disqualification |

**Query Canon 3 violations specifically:**

```sql
SELECT id, description, date_occurred, mcr_rule, severity, source_quote
FROM judicial_violations
WHERE canon = 'Canon 3' OR canon LIKE '%Canon%3%' OR canon LIKE '%Canon\n3%'
ORDER BY date_occurred ASC;
```

---

## 3. Three-Court Judicial Cartel

### 3.1 The Ladas, Hoopes & McNeill Connection

All three judges share professional origin at the same law firm:

**Ladas, Hoopes & McNeill**
435 Whitehall Road, Muskegon, MI

```
┌─────────────────────────────────────────────────────────┐
│              LADAS, HOOPES & McNEILL                    │
│              435 Whitehall Rd, Muskegon                 │
│                                                         │
│  Former Partners:                                       │
│  ├── Jenny L. McNeill ──→ 14th Circuit (Family Div.)   │
│  ├── Kenneth Hoopes ───→ 14th Circuit (Chief Judge)    │
│  └── Maria Ladas-Hoopes → 60th District               │
│                                                         │
│  Also: Kenneth Hoopes ← married to → Maria Ladas-Hoopes│
└─────────────────────────────────────────────────────────┘
```

### 3.2 Judicial Actor Profiles

| Judge | Court | Position | Connection |
|-------|-------|----------|------------|
| **Hon. Jenny L. McNeill** | 14th Circuit, Family Division | Presiding judge in Pigors v Watson | Former law partner of Kenneth Hoopes |
| **Hon. Kenneth Hoopes** | 14th Circuit | Chief Judge | McNeill's former partner; wife is Maria Ladas-Hoopes; reviews disqualification motions against McNeill |
| **Hon. Maria Ladas-Hoopes** | 60th District | District judge | Kenneth's wife; firm namesake; 60th District handles related proceedings |
| **Hon. Raymond J. Kostrzewa Jr.** | 60th District | Criminal judge | Presiding over case 2025-25245676SM (criminal case against Andrew) |

### 3.3 Structural Conflict Analysis

The cartel structure creates these specific conflicts:

**Conflict 1: McNeill ↔ Berry family**
```
Ronald Berry (Emily's partner)
  ↓ family relationship
Cavan Berry (Judge McNeill's husband)
  ↓ married to
Hon. Jenny L. McNeill (presiding judge)
```

- MCR 2.003(C)(1)(b): Judge must disqualify when spouse's relationship to a party or party's representative creates appearance of partiality.
- This is a MANDATORY disqualification ground — not discretionary.

**Conflict 2: McNeill ↔ Hoopes (disqualification review)**
```
McNeill (subject of disqualification motion)
  ↓ former law partner
Kenneth Hoopes (Chief Judge — reviews disqualification motions)
```

- If Andrew files MCR 2.003 against McNeill, Hoopes (her former partner) decides the motion.
- This creates a structural impossibility of impartial review within the 14th Circuit.
- Solution: MCR 2.003(D)(3)(a) — request Chief Judge of another circuit to decide, or appeal directly.

**Conflict 3: Cross-court coordination**
```
14th Circuit (McNeill + Hoopes) ←→ 60th District (Ladas-Hoopes + Kostrzewa)
```

- Criminal case 2025-25245676SM in 60th District may be influenced by 14th Circuit communications.
- Maria Ladas-Hoopes' presence in 60th District connects both courts through the Hoopes marriage.

---

## 4. MCR 2.003 Disqualification Framework

### 4.1 Mandatory vs. Discretionary Disqualification

| Type | MCR Provision | Standard | Applies to McNeill? |
|------|--------------|----------|-------------------|
| **Mandatory** | MCR 2.003(C)(1) | Judge SHALL disqualify if: personal bias, personal knowledge, prior involvement, spouse/family connection | YES — Berry-McNeill spousal family connection |
| **Discretionary** | MCR 2.003(C)(2) | Judge MAY disqualify if: would not feel able to be impartial | Supplement to mandatory |

### 4.2 MCR 2.003(C)(1) — Mandatory Grounds

```
(a) Personal bias or prejudice concerning a party or attorney
(b) Personal knowledge of disputed evidentiary facts
(c) Prior representation or material witness role
(d) Judge or spouse has financial interest
(e) Judge or spouse related to party within third degree
```

**Ground (a) — personal bias:** Documented via `judicial_violations WHERE violation_type = 'bias'`

**Ground (b) — personal knowledge:** Berry family relationship provides personal knowledge channel

**Ground (e) — spousal relationship:** Cavan Berry → Ronald Berry → Emily Watson chain

### 4.3 MCR 2.003(D) — Procedure

| Step | MCR | Action |
|------|-----|--------|
| 1 | 2.003(D)(1) | File motion with affidavit of specific facts showing bias |
| 2 | 2.003(D)(2) | Motion heard by challenged judge first |
| 3 | 2.003(D)(3)(a) | If denied, Chief Judge of the circuit decides |
| 4 | 2.003(D)(3)(b) | If Chief Judge is also conflicted → Chief Judge of another circuit |
| 5 | — | Appeal to Court of Appeals if all circuit options fail |

**CRITICAL:** Kenneth Hoopes IS the Chief Judge of 14th Circuit AND McNeill's former law partner. Step 3 is structurally compromised. Proceed directly to Step 4 (another circuit's Chief Judge) or appellate review.

### 4.4 Disqualification Motion Query Pack

```sql
-- All bias violations for disqualification affidavit
SELECT id, violation_type, description, date_occurred, mcr_rule, canon,
       source_file, source_quote, severity
FROM judicial_violations
WHERE violation_type = 'bias' AND severity >= 5
ORDER BY date_occurred ASC;

-- All ex parte violations (pattern evidence)
SELECT id, description, date_occurred, mcr_rule, source_quote
FROM judicial_violations
WHERE violation_type = 'ex_parte'
  AND date_occurred IS NOT NULL
ORDER BY date_occurred ASC;

-- Bias chronology for narrative spine
SELECT date, event_description, canon_violated, mcr_violation,
       severity, filing_relevance, source_quote
FROM judicial_bias_chronology
WHERE severity >= 7
ORDER BY date ASC;
```

---

## 5. JTC Complaint Framework

### 5.1 Michigan Court Rules — Judicial Tenure Commission

| MCR | Subject | Application |
|-----|---------|-------------|
| MCR 9.200 | Organization and authority of JTC | Establishes JTC jurisdiction over judicial misconduct |
| MCR 9.201 | Definitions | Defines misconduct, incapacity, grounds for discipline |
| MCR 9.202 | Complaint procedures | How to file; investigation process; formal proceedings |
| MCR 9.203 | Preliminary investigation | JTC investigates after complaint receipt |
| MCR 9.204 | Formal complaint | JTC files formal complaint after investigation |
| MCR 9.205 | Hearing | Master/panel hearing on formal complaint |
| MCR 9.206 | Discipline | Sanctions: censure, suspension, removal |

### 5.2 JTC Complaint Elements

A JTC complaint requires:

1. **Specific facts** — dates, descriptions, evidence citations
2. **Canon violations** — which Canons were violated and how
3. **Pattern evidence** — not isolated incidents but systematic conduct
4. **Impact documentation** — harm to litigant, harm to public confidence
5. **Exhaustion** — show that judicial remedies (disqualification, appeal) were pursued

### 5.3 Building the JTC Complaint from DB

**Step 1: Extract violation inventory**
```sql
SELECT violation_type, canon, mcr_rule, COUNT(*) as cnt
FROM judicial_violations
WHERE canon IS NOT NULL OR mcr_rule IS NOT NULL
GROUP BY violation_type, canon, mcr_rule
ORDER BY cnt DESC;
```

**Step 2: Build chronological narrative**
```sql
SELECT date, event_description, canon_violated, mcr_violation, severity,
       source_quote, filing_relevance
FROM judicial_bias_chronology
ORDER BY date ASC;
```

**Step 3: Extract high-severity incidents**
```sql
SELECT id, violation_type, description, date_occurred, canon, mcr_rule,
       source_file, source_quote, severity
FROM judicial_violations
WHERE severity >= 7
ORDER BY severity DESC, date_occurred ASC;
```

**Step 4: Compile canon-by-canon analysis**
```sql
SELECT jv.canon, jv.violation_type, COUNT(*) as violations,
       mc.title as canon_title
FROM judicial_violations jv
LEFT JOIN michigan_judicial_canons mc ON jv.canon = mc.canon_number
WHERE jv.canon IS NOT NULL AND jv.canon != ''
GROUP BY jv.canon, jv.violation_type
ORDER BY jv.canon, violations DESC;
```

---

## 6. Bias Documentation

### 6.1 Hostile Record Practices

Evidence of McNeill creating a hostile record against Andrew:

```sql
SELECT id, quote_text, source_file, category
FROM evidence_quotes
WHERE category IN ('judicial', 'judicial_violation', 'due_process')
  AND (quote_text LIKE '%record%' OR quote_text LIKE '%hostile%'
       OR quote_text LIKE '%denied%' OR quote_text LIKE '%struck%')
ORDER BY id;
```

**Patterns to document:**

| Practice | Description | MCR/Canon |
|----------|-------------|-----------|
| Striking pleadings | Removing Andrew's filings from record without cause | MCR 2.517(A), Canon 3(A)(1) |
| Excluding evidence | Refusing to consider Andrew's evidence while accepting Emily's | Canon 3(B)(5) |
| Interrupted testimony | Cutting off Andrew's presentation mid-hearing | Canon 3(A)(4) |
| Denied motions without hearing | Ruling on motions without oral argument when rules require it | MCR 2.119 |
| Ex parte communications | Communicating with Emily/Barnes without Andrew present | Canon 3(B)(7) |
| Unequal time | Granting Emily more hearing time, argument time | Canon 3(B)(5) |

### 6.2 Unequal Evidentiary Treatment

```sql
-- Compare filing events by party
SELECT filed_by, event_type, COUNT(*) as filings
FROM docket_events
WHERE filed_by IS NOT NULL
GROUP BY filed_by, event_type
ORDER BY filed_by, filings DESC;
```

### 6.3 Ex Parte Contamination

The dominant violation type. Query the full ex parte record:

```sql
SELECT id, description, date_occurred, mcr_rule, severity, source_quote
FROM judicial_violations
WHERE violation_type = 'ex_parte'
ORDER BY date_occurred ASC;
```

**Pattern analysis:**

```sql
-- Ex parte violations by month
SELECT strftime('%Y-%m', date_occurred) as month, COUNT(*) as violations
FROM judicial_violations
WHERE violation_type = 'ex_parte' AND date_occurred IS NOT NULL
GROUP BY month
ORDER BY month ASC;
```

### 6.4 Due Process Violations (14th Amendment)

Due process requires notice and opportunity to be heard before deprivation of liberty or parental rights.

```sql
SELECT id, description, date_occurred, mcr_rule, severity
FROM judicial_violations
WHERE violation_type = 'due_process'
ORDER BY date_occurred ASC;
```

**Constitutional framework:**

- US Constitution, 14th Amendment: "nor shall any State deprive any person of life, liberty, or property, without due process of law"
- MI Constitution, Art. 1, §17: "No person shall... be deprived of life, liberty or property, without due process of law"
- Parental rights are a fundamental liberty interest: *Troxel v. Granville*, 530 U.S. 57 (2000)
- Ex parte orders depriving parenting time without hearing violate procedural due process

---

## 7. Judicial Audit System

### 7.1 Per-Filing Audit Results

```sql
PRAGMA table_info(judicial_audit);
-- filing_id, check_id, check_name, block, result, score, details, audit_date
```

**Audit query:**

```sql
SELECT filing_id, check_name, result, score, details
FROM judicial_audit
WHERE result != 'PASS'
ORDER BY filing_id, score ASC;
```

### 7.2 Audit Aggregation

```sql
SELECT filing_id, COUNT(*) as total_checks,
       SUM(CASE WHEN result = 'PASS' THEN 1 ELSE 0 END) as passed,
       SUM(CASE WHEN result != 'PASS' THEN 1 ELSE 0 END) as failed,
       ROUND(AVG(score), 1) as avg_score
FROM judicial_audit
GROUP BY filing_id
ORDER BY avg_score ASC;
```

---

## 8. Authority Chain Analysis

### 8.1 Authority Chains v2

The `authority_chains_v2` table maps citation relationships for judicial accountability:

```sql
PRAGMA table_info(authority_chains_v2);
-- id, primary_citation, supporting_citation, relationship, source_document,
-- source_type, lane, paragraph_context, created_at
```

**Query chain density for judicial filings:**

```sql
SELECT primary_citation, COUNT(*) as supporting_count
FROM authority_chains_v2
WHERE lane = 'E'
GROUP BY primary_citation
ORDER BY supporting_count DESC
LIMIT 20;
```

### 8.2 Authority Chain Audit (Per-Filing Completeness)

```sql
SELECT filing_id, filing_name, total_arguments, complete_chains,
       incomplete_chains, avg_chain_score, total_canons,
       total_rules, critical_gaps
FROM authority_chain_summary
ORDER BY avg_chain_score ASC;
```

### 8.3 Canon-Specific Authority Chains

```sql
SELECT primary_citation, supporting_citation, relationship, paragraph_context
FROM authority_chains_v2
WHERE primary_citation LIKE '%Canon%' OR supporting_citation LIKE '%Canon%'
ORDER BY primary_citation;
```

### 8.4 Master Citations for Judicial Accountability

```sql
SELECT citation, authority_type, lane, frequency, context
FROM master_citations
WHERE lane = 'E'
  OR citation LIKE '%Canon%'
  OR citation LIKE '%MCR 2.003%'
  OR citation LIKE '%MCR 9.2%'
ORDER BY frequency DESC
LIMIT 30;
```

---

## 9. Key DB Queries — Ready to Run

### Query 1: Judicial Violation Summary Dashboard

```sql
SELECT
  (SELECT COUNT(*) FROM judicial_violations) as total_violations,
  (SELECT COUNT(*) FROM judicial_violations WHERE violation_type = 'ex_parte') as ex_parte,
  (SELECT COUNT(*) FROM judicial_violations WHERE violation_type = 'bias') as bias,
  (SELECT COUNT(*) FROM judicial_violations WHERE severity >= 7) as high_severity,
  (SELECT COUNT(*) FROM judicial_bias_chronology) as bias_timeline_events,
  (SELECT COUNT(DISTINCT canon) FROM judicial_violations WHERE canon IS NOT NULL AND canon != '') as canons_violated,
  (SELECT COUNT(DISTINCT mcr_rule) FROM judicial_violations WHERE mcr_rule IS NOT NULL AND mcr_rule != '') as mcr_rules_violated;
```

### Query 2: Disqualification Evidence Pack

```sql
SELECT violation_type, description, date_occurred, mcr_rule, canon,
       source_file, source_quote, severity
FROM judicial_violations
WHERE mcr_rule LIKE '%2.003%' OR violation_type = 'bias'
ORDER BY severity DESC, date_occurred ASC;
```

### Query 3: JTC-Ready Violation Extract

```sql
SELECT jv.id, jv.violation_type, jv.description, jv.date_occurred,
       jv.canon, jv.mcr_rule, jv.severity, jv.source_quote,
       mc.title as canon_title
FROM judicial_violations jv
LEFT JOIN michigan_judicial_canons mc ON jv.canon = mc.canon_number
WHERE jv.severity >= 5
ORDER BY jv.date_occurred ASC;
```

### Query 4: Ex Parte Pattern Evidence

```sql
SELECT strftime('%Y-%m', date_occurred) as month,
       COUNT(*) as violations,
       GROUP_CONCAT(mcr_rule, '; ') as rules_violated
FROM judicial_violations
WHERE violation_type = 'ex_parte' AND date_occurred IS NOT NULL
GROUP BY month
ORDER BY month ASC;
```

### Query 5: Cross-Table Judicial Intelligence

```sql
SELECT 'judicial_violations' as source, violation_type as category, COUNT(*) as cnt
FROM judicial_violations GROUP BY violation_type
UNION ALL
SELECT 'judicial_bias_chronology', canon_violated, COUNT(*)
FROM judicial_bias_chronology WHERE canon_violated IS NOT NULL GROUP BY canon_violated
UNION ALL
SELECT 'evidence_quotes', category, COUNT(*)
FROM evidence_quotes WHERE category IN ('judicial', 'judicial_violation', 'due_process') GROUP BY category
ORDER BY source, cnt DESC;
```

---

## 10. Cross-Wiring Points

| Target Brain | Connection | Data Flow |
|-------------|------------|-----------|
| **Ω5-adversary-brain** | Berry-McNeill conflict chain | Ronald Berry → Cavan Berry → McNeill undisclosed relationship is both adversary intel AND judicial accountability evidence |
| **Ω6-timeline-brain** | Violations are dated events | `judicial_violations.date_occurred` and `judicial_bias_chronology.date` feed JUDGE_COURT_CONDUCT chronology view |
| **Ω8-financial-brain** | Judicial misconduct → §1983 damages | Each documented due process violation supports compensatory and punitive damages under 42 USC §1983 (subject to judicial immunity analysis) |
| **Ω3-authority-brain** | Authority chains validate accusations | `authority_chains_v2` WHERE lane = 'E' provides citation chains for every judicial misconduct claim |
| **Ω4-filing-brain** | Violations drive filing priorities | High-severity violations trigger: disqualification motion (immediate), JTC complaint (parallel), appellate brief (if denied) |
| **Ω1-evidence-brain** | Evidence proves violations | `evidence_quotes WHERE category IN ('judicial', 'judicial_violation')` supplies exhibit candidates for every violation |

---

## 11. Operational Directives

1. **Separate disqualification from JTC.** MCR 2.003 disqualification is a case-level remedy (remove judge). JTC complaint is a career-level remedy (discipline/remove from bench). Both require different evidence presentations.
2. **Document the Hoopes conflict explicitly.** Every disqualification filing must address that the Chief Judge (Hoopes) is McNeill's former law partner and therefore cannot impartially review the motion under MCR 2.003(D)(3)(a).
3. **Track severity scores.** High-severity violations (≥7) go in the disqualification affidavit. All violations (any severity) go in the JTC complaint pattern section.
4. **Ex parte is the lead violation.** It is the most numerous, most provable, and most constitutionally significant violation type. Lead every judicial accountability filing with ex parte evidence.
5. **Judicial immunity analysis is required** before citing judicial violations in any §1983 claim. Absolute immunity protects judicial acts performed in judicial capacity with jurisdiction. Focus on acts outside jurisdiction or non-judicial acts for §1983.
6. **The three-court cartel is pattern evidence** for JTC, not just McNeill-specific. The systemic nature of the conflict (former partners populating multiple courts) elevates this from individual bias to structural corruption.
7. **Never fabricate violation counts.** Always query live: `SELECT COUNT(*) FROM judicial_violations WHERE [condition]`.
8. **Bias chronology is the narrative spine** for JTC complaints. Use `judicial_bias_chronology` in date order to build the chronological narrative required by MCR 9.202.
