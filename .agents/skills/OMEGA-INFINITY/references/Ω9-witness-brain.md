# Ω9 Witness Intelligence Brain — OMEGA-INFINITY Reference
> Module 9 of 12 · Cognitive Litigation Kernel v4.0
> Case: Pigors v Watson · 14th Circuit · Muskegon County

## Purpose

Govern all witness intelligence operations: identification, categorization, preparation, examination planning, evidence linkage, and subpoena tracking across all six case lanes.

---

## 1. Known Witness Registry

### 1.1 Primary Parties

| ID | Name | Role | Category | Lanes | Filing Refs | Subpoena | Notes |
|----|------|------|----------|-------|-------------|----------|-------|
| W1 | **Andrew James Pigors** | Plaintiff | Fact witness | A,B,C,D,E,F | All (F1-F10) | N/A — party | 1977 Whitehall Road, Lot 17, North Muskegon, MI 49445. Primary affiant for all filings. Personal knowledge of custody interference, housing lockout, judicial misconduct, and parenting time denial. |
| W2 | **Emily A. Watson** | Defendant | Hostile witness | A,D | F1,F3,F7,F8 | N/A — party | 2160 Garland Drive, Norton Shores, MI 49441. Expected testimony on custody interference, parenting time denial, PPO allegations. Relevance score: 10.0. |
| W3 | **Ronald Berry** | Non-attorney | Fact witness | A,D,E | F7,F8 | Required | Emily's boyfriend/domestic partner. NON-ATTORNEY — no bar number. Never was Emily's attorney. Do NOT reference as "Esq." or counsel. Witness to intimidation, household conditions, interactions with L.D.W. Relevance score: 7.0. |
| W4 | **Pamela Rusco** | FOC Caseworker | Fact witness | A | F3,F7 | Via FOC office | 990 Terrace St, Muskegon, MI 49442. Testimony on custody evaluation, parenting time recommendations, FOC report findings. Relevance score: 8.5. |
| W5 | **Hon. Jenny L. McNeill** | Presiding Judge | Reference only | E | F6 | N/A — judicial immunity | 14th Circuit Court, Family Division. Cannot be deposed on judicial decision-making. Included for JTC complaint (F6) and disqualification motion (F3) reference only. Relevance score: 9.0. |

### 1.2 Identified Witnesses (Identity TBD — Verify Before Filing)

| ID | Name/Role | Category | Lane | Subpoena | Evidence Matches | Notes |
|----|-----------|----------|------|----------|-----------------|-------|
| W6 | **Jennifer Barnes (P55406)** | Fact witness | A | Required — former counsel | F3 refs | Emily's former attorney. WITHDREW from representation. Attorney-client privilege may limit scope. |
| W7 | **Albert** | Fact witness | A,D | Required | Kitchen recording evidence | Witness to kitchen recording incident. First name only — verify full identity before subpoena. |
| W8 | **HealthWest Custody Evaluator** | Expert witness | A | TBD | 36 evidence items (HealthWest, evaluator, psychological) | Custody evaluation findings. Specific individual TBD. |
| W9 | **Pediatrician / Medical Provider** | Expert witness | A | TBD | 55 evidence items (pediatrician, doctor, medical) | L.D.W.'s health records and well-being observations. Specific individual TBD. |
| W10 | **School Personnel** | Fact witness | A | TBD | 17 evidence items (school, teacher, IEP, education) | L.D.W.'s attendance, performance, observed behavior. |
| W11 | **Shady Oaks Management** | Fact witness | B | TBD | 486 evidence items (Shady Oaks, management, landlord, property) | Property conditions, lease terms, code violations. |
| W12 | **Code Enforcement Officer** | Fact witness | B | TBD | 1 evidence item (code enforcement, inspector) | Housing code violations, inspection results. |
| W13 | **Law Enforcement Officer(s)** | Fact witness | D | TBD | 160 evidence items (officer, police, body cam, deputy) | Incident response, body cam footage, police reports. |
| W14 | **AppClose Records Custodian** | Records custodian | D | TBD | 95 evidence items (AppClose, OurFamilyWizard) | Authentication of co-parenting app communications. |
| W15 | **Court Reporter** | Records custodian | E | TBD | 204 evidence items (court reporter, transcript, stenograph) | Authentication of hearing transcripts and court records. |
| W16 | **Court Clerk / Records Custodian** | Records custodian | F | TBD | 89 evidence items (clerk, record, certified) | Authentication of lower court record for appellate review. |
| W17 | **Attorney/Litigant (Bias Pattern)** | Fact witness | E | TBD | 596 evidence items (attorney, counsel, litigant, bias) | Observations of judicial bias patterns in McNeill courtroom. |
| W18 | **CPS Investigator(s)** | Fact witness | A | TBD | Search evidence_quotes for CPS terms | CPS investigation findings. Do NOT fabricate investigation count — query DB. |
| W19 | **Police Officers (Body Cam)** | Fact witness | D | TBD | Cross-ref with W13 | Body cam footage from specific incidents. Criminal case records. |

---

## 2. Witness Categorization Framework

### 2.1 Category Definitions

| Category | Definition | MRE Foundation | Examination Approach |
|----------|-----------|----------------|---------------------|
| **Fact Witness** | Personal knowledge of relevant events (MRE 602) | MRE 601 (competency), MRE 602 (personal knowledge) | Open-ended direct; leading on cross |
| **Expert Witness** | Specialized knowledge assists trier of fact (MRE 702) | MRE 702-706 (expert testimony) | Establish qualifications → opinions → basis |
| **Hostile Witness** | Adverse party or witness showing hostility | MRE 611(c) (leading questions on direct) | Leading questions permitted on direct |
| **Character Witness** | Testifies to reputation or opinion of character | MRE 404, 405, 608 | Limited to reputation/opinion; no specific acts on direct |
| **Records Custodian** | Authenticates business/public records | MRE 803(6)-(8), MRE 902 | Foundation: regular course of business, made at/near time |

### 2.2 Current Witness Categories

```
FACT WITNESSES:    Andrew Pigors, Pamela Rusco, Jennifer Barnes, Ronald Berry,
                   Albert, School Personnel, Shady Oaks Mgmt, Code Enforcement,
                   Law Enforcement, CPS Investigators, Bias Pattern witnesses
EXPERT WITNESSES:  HealthWest Evaluator, Pediatrician/Medical
HOSTILE WITNESSES: Emily A. Watson
CUSTODIANS:        AppClose Records, Court Reporter, Court Clerk
REFERENCE ONLY:    Hon. Jenny L. McNeill (judicial immunity)
```

---

## 3. Deposition Preparation Protocol

### 3.1 Pre-Deposition Checklist

1. **Verify witness identity.** Query `witness_list` for current name, contact_info, availability.
2. **Pull all related evidence.** Query `evidence_quotes` filtered by witness name mentions:
   ```sql
   SELECT id, quote_text, source_file, category, lane, relevance_score
   FROM evidence_quotes
   WHERE quote_text LIKE '%[witness_name]%'
   ORDER BY relevance_score DESC;
   ```
3. **Review filing references.** Join `witness_list.filing_ids` to `filing_packages` for context.
4. **Identify contradictions.** Search for inconsistencies between witness statements and record.
5. **Prepare exhibit binder.** Tag exhibits per witness from `evidence_quotes` + `filing_documents`.
6. **Draft examination outline.** Use templates from Section 4 below.
7. **Subpoena status.** Verify `subpoena_needed` flag and track service.

### 3.2 Deposition Notice Requirements (MCR 2.306)

| Element | Requirement |
|---------|-------------|
| Notice | Reasonable written notice to every party (MCR 2.306(B)) |
| Location | Within 50 miles of deponent's residence/business, or as court orders |
| Duration | 7-hour day limit (MCR 2.306(A)(2)) |
| Recording | Stenographic by default; may request audio/video with notice |
| Documents | Use MCR 2.306(B)(5) for document production at deposition |
| Non-party | Subpoena required (MCR 2.305) |

### 3.3 Hostile Witness Protocol (Emily A. Watson)

- Designate hostile under MRE 611(c) at start of direct examination.
- Leading questions permitted on direct once hostile designation granted.
- Prepare impeachment materials from `evidence_quotes` WHERE lane IN ('A','D').
- Focus areas: parenting time denial, PPO allegations, custody interference, communications about L.D.W.
- Cross-reference AppClose/OurFamilyWizard records for contradictions.

---

## 4. Witness Examination Templates

### 4.1 Direct Examination Template

```
PHASE 1 — FOUNDATION (all witnesses)
Q: State your full name for the record.
Q: What is your current address/place of employment?
Q: How do you know the parties in this case?
Q: Describe your involvement in the events at issue.

PHASE 2 — PERSONAL KNOWLEDGE (MRE 602)
Q: Were you personally present when [event]?
Q: What did you see/hear/observe?
Q: When did this occur? [pin to specific date]

PHASE 3 — NARRATIVE (fact-specific)
Q: Describe [event] in your own words.
Q: What happened next?
Q: Who else was present?

PHASE 4 — EXHIBIT AUTHENTICATION (MRE 901)
Q: I'm showing you what has been marked Exhibit [N]. Do you recognize it?
Q: What is it?
Q: Is this a fair and accurate representation of [subject]?

PHASE 5 — IMPACT/HARM
Q: How did [event] affect [L.D.W. / plaintiff / subject]?
Q: Are you aware of any continuing effects?
```

### 4.2 Cross-Examination Template

```
PHASE 1 — BIAS/MOTIVE (MRE 607, 616)
Q: You have a close relationship with [party], correct?
Q: You would benefit if [party] prevails in this case, correct?

PHASE 2 — PRIOR INCONSISTENT STATEMENTS (MRE 613)
Q: You previously stated [quote from evidence_quotes], correct?
Q: That's different from your testimony today, isn't it?
Q: [Extrinsic evidence if denied — MRE 613(b)]

PHASE 3 — LIMITING KNOWLEDGE
Q: You weren't present for [event], were you?
Q: You have no personal knowledge of [fact], correct?
Q: You're relying on what someone told you, correct? [hearsay objection setup]

PHASE 4 — IMPEACHMENT (MRE 608, 609)
Q: Have you ever been convicted of a crime? [MRE 609 — 10-year limit]
Q: Have you made false statements under oath before? [MRE 608(b)]
```

### 4.3 Redirect Examination Template

```
PHASE 1 — REHABILITATE
Q: You were asked about [cross topic]. Let me ask you...
Q: What was the full context of [statement challenged on cross]?

PHASE 2 — CLARIFY
Q: When you said [X on cross], did you mean [clarification]?

PHASE 3 — BOLSTER (if opened on cross)
Q: [Only if character attacked on cross — MRE 608(a)(2)]
```

---

## 5. Michigan Rules of Evidence — Witness Testimony

### 5.1 Competency and Foundation (MRE 601-615)

| Rule | Subject | Application |
|------|---------|-------------|
| MRE 601 | General competency | Every person competent unless rules provide otherwise |
| MRE 602 | Personal knowledge | Foundation required — witness must have perceived the matter |
| MRE 607 | Impeachment | Any party may attack credibility of any witness |
| MRE 608 | Character for truthfulness | Opinion/reputation evidence; specific instances on cross only |
| MRE 609 | Impeachment by conviction | Crimes of dishonesty ≤10 years; other crimes if probative > prejudice |
| MRE 611 | Mode and order | Court controls; leading on cross, hostile witness, child |
| MRE 612 | Writing to refresh memory | Adverse party entitled to inspect writing used to refresh |
| MRE 613 | Prior inconsistent statements | Must give opportunity to explain (613(b) for extrinsic) |
| MRE 614 | Court-called witnesses | Court may call/interrogate; parties may cross |
| MRE 615 | Witness exclusion | Court shall exclude witnesses on request (party exemption) |

### 5.2 Hearsay Rules (MRE 801-807)

| Rule | Subject | Witness Impact |
|------|---------|----------------|
| MRE 801(d)(1) | Prior statements of witness | Inconsistent under oath = not hearsay |
| MRE 801(d)(2) | Admissions by party-opponent | Emily's own statements = not hearsay |
| MRE 803(1) | Present sense impression | Narration during/immediately after event |
| MRE 803(2) | Excited utterance | Under stress of startling event |
| MRE 803(4) | Medical diagnosis | Statements for medical treatment/diagnosis |
| MRE 803(6) | Business records | Foundation via custodian — AppClose, medical, school |
| MRE 803(8) | Public records | Government records — CPS, police, FOC |
| MRE 804(b)(1) | Former testimony | If witness unavailable and prior testimony under oath |
| MRE 807 | Residual exception | Trustworthiness + notice + interests of justice |

---

## 6. Evidence Linkage per Witness

### 6.1 Query Pattern — Witness-to-Evidence

```sql
-- Find all evidence mentioning a specific witness
SELECT eq.id, eq.quote_text, eq.source_file, eq.category,
       eq.lane, eq.relevance_score, eq.filing_refs
FROM evidence_quotes eq
WHERE eq.quote_text LIKE '%Watson%'
  AND eq.lane IN ('A', 'D')
ORDER BY eq.relevance_score DESC
LIMIT 50;
```

### 6.2 High-Value Evidence by Witness

| Witness | Evidence Source | Lane | Relevance | Evidence Type |
|---------|---------------|------|-----------|---------------|
| Emily A. Watson | AppClose messages, court filings, police reports | A,D | 10.0 | Admissions, inconsistent statements |
| Pamela Rusco | FOC reports, custody evaluation | A | 8.5 | Official records |
| Ronald Berry | Kitchen recording, household observations | A,D | 7.0 | Direct observation |
| Albert | Kitchen recording incident | A,D | 7.0+ | Eyewitness testimony |
| Law Enforcement | Body cam footage, police reports | D | 8.0 | Official records, recordings |
| HealthWest Evaluator | Custody evaluation report | A | 7.2 | Expert opinion |
| Shady Oaks Mgmt | Lease, property records, correspondence | B | 8.0 | Business records |

### 6.3 Evidence Count by Witness Category

```sql
-- Count evidence items per witness search term
SELECT 'Watson' AS witness, COUNT(*) AS hits FROM evidence_quotes WHERE quote_text LIKE '%Watson%'
UNION ALL
SELECT 'Rusco', COUNT(*) FROM evidence_quotes WHERE quote_text LIKE '%Rusco%'
UNION ALL
SELECT 'Berry', COUNT(*) FROM evidence_quotes WHERE quote_text LIKE '%Berry%'
UNION ALL
SELECT 'Shady Oaks', COUNT(*) FROM evidence_quotes WHERE quote_text LIKE '%Shady Oaks%'
UNION ALL
SELECT 'police', COUNT(*) FROM evidence_quotes WHERE quote_text LIKE '%police%' OR quote_text LIKE '%officer%'
ORDER BY hits DESC;
```

---

## 7. Subpoena Tracking Protocol

### 7.1 Subpoena Status Dashboard

```sql
SELECT id, name, role, lane, subpoena_needed, availability, notes
FROM witness_list
WHERE subpoena_needed = 1
ORDER BY relevance_score DESC;
```

### 7.2 Subpoena Issuance Workflow

| Step | Action | Form | Rule |
|------|--------|------|------|
| 1 | Draft subpoena | MC 11 (Subpoena) | MCR 2.506 |
| 2 | Issue from court clerk | — | MCR 2.506(A) |
| 3 | Serve personally | MC 12 (Proof of Service) | MCR 2.105 |
| 4 | Witness fee + mileage | Statutory fee | MCL 600.2552 |
| 5 | Track in `witness_list.subpoena_needed` | — | Update DB |
| 6 | File proof of service | MC 12 | MCR 2.104 |

### 7.3 Subpoena Duces Tecum (Documents)

For records custodians (W14-W16), use subpoena duces tecum to compel document production:

```
REQUIRED ELEMENTS:
- Specific documents described with reasonable particularity
- Time, date, location for production
- Witness fee tendered at service
- Filed proof of service (MC 12)
```

### 7.4 Priority Subpoena Queue

| Priority | Witness | Reason | Deadline Sensitivity |
|----------|---------|--------|---------------------|
| 1 | AppClose Records Custodian | Authenticate co-parenting communications | Pre-trial |
| 2 | Law Enforcement Officer(s) | Body cam footage, incident reports | Discovery deadline |
| 3 | Pamela Rusco (FOC) | FOC report, custody evaluation | Custody modification hearing |
| 4 | Court Reporter | Transcript authentication for appeal | COA brief deadline |
| 5 | HealthWest Evaluator | Custody evaluation report authentication | Custody modification |

---

## 8. Witness-Related DB Tables

### 8.1 Primary Table: `witness_list`

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Auto-increment witness ID |
| name | TEXT NOT NULL | Witness name |
| role | TEXT | fact, expert, hostile, custodian, character |
| lane | TEXT | Case lane assignment (A-F) |
| filing_ids | TEXT | Comma-separated filing references |
| relevance_score | REAL | 0.0-10.0 relevance rating |
| contact_info | TEXT | Address, phone, or office |
| testimony_summary | TEXT | Expected testimony narrative |
| depo_questions | TEXT | JSON array of deposition questions |
| subpoena_needed | INTEGER | 0=no, 1=yes |
| availability | TEXT | Service/availability notes |
| notes | TEXT | Additional notes and warnings |
| created_at | TEXT | Timestamp |

### 8.2 Supporting Tables

| Table | Relevance | Join Pattern |
|-------|-----------|-------------|
| `evidence_quotes` | Quote text mentioning witnesses | `WHERE quote_text LIKE '%[name]%'` |
| `filing_packages` | Filings where witness testimony is relevant | `WHERE filing_id IN (witness.filing_ids)` |
| `filing_documents` | Specific documents referencing witnesses | `WHERE content LIKE '%[name]%'` |
| `narrative_context` | Narrative blocks about witness events | `WHERE content LIKE '%[name]%'` |

### 8.3 Gap: Missing Tables

The following witness-related tables do NOT currently exist in `litigation_context.db`. Document as acquisition tasks:

| Missing Table | Purpose | Recommended Schema |
|---------------|---------|-------------------|
| `witness_testimony_log` | Track actual deposition/trial testimony | witness_id, hearing_date, testimony_text, exhibit_refs |
| `subpoena_tracking` | Track subpoena issuance and service | witness_id, subpoena_type, issued_date, served_date, proof_filed |
| `witness_credibility_matrix` | Score witness credibility factors | witness_id, bias_score, consistency_score, impeachment_risk |
| `witness_exhibit_map` | Map witnesses to specific exhibits | witness_id, exhibit_id, exhibit_type, authentication_status |

---

## Key DB Queries

```sql
-- Q1: All witnesses requiring subpoenas, ordered by relevance
SELECT name, role, lane, relevance_score, availability
FROM witness_list
WHERE subpoena_needed = 1
ORDER BY relevance_score DESC;

-- Q2: Evidence count per witness
SELECT wl.name, wl.role, wl.lane,
       (SELECT COUNT(*) FROM evidence_quotes eq
        WHERE eq.quote_text LIKE '%' || wl.name || '%') AS evidence_hits
FROM witness_list wl
ORDER BY evidence_hits DESC;

-- Q3: Witnesses per filing package
SELECT fp.filing_id, fp.title, wl.name, wl.role
FROM filing_packages fp
JOIN witness_list wl ON (',' || wl.filing_ids || ',') LIKE ('%,' || fp.filing_id || ',%')
ORDER BY fp.filing_id, wl.relevance_score DESC;

-- Q4: High-relevance hostile witness evidence
SELECT eq.id, eq.quote_text, eq.source_file, eq.relevance_score
FROM evidence_quotes eq
WHERE eq.quote_text LIKE '%Watson%'
  AND eq.relevance_score >= 7.0
ORDER BY eq.relevance_score DESC
LIMIT 25;

-- Q5: Witness coverage gap analysis
SELECT wl.name, wl.lane, wl.subpoena_needed, wl.availability,
       CASE WHEN wl.contact_info = '' THEN 'MISSING CONTACT' ELSE 'OK' END AS contact_status
FROM witness_list wl
WHERE wl.availability LIKE '%TBD%' OR wl.contact_info = '';
```

---

## Cross-Wiring Points

| Target Brain | Connection | Data Flow |
|-------------|-----------|-----------|
| **Ω10 Filing Brain** | Witness → filing_ids linkage | Each filing package references witnesses; witnesses drive affidavit content |
| **Ω11 Agent Brain** | `subpoena-engine` agent | Automates subpoena drafting; `evidence-warfare-commander` drives impeachment prep |
| **Ω12 Context Brain** | Witness data persists in `litigation_context.db` | Session continuity preserves witness intelligence across sessions |
| **Ω1 Evidence Brain** | `evidence_quotes` cross-reference | Every witness links to supporting evidence via text search |
| **Ω2 Timeline Brain** | Witness events map to chronology | Testimony pins to dated events for timeline construction |
| **Ω4 Authority Brain** | MRE rules govern testimony | Admissibility analysis depends on witness category and evidence type |

---

## Anti-Hallucination Rules

- **NEVER fabricate witness names.** If identity unknown, use role descriptor + "[VERIFY IDENTITY]".
- **NEVER fabricate evidence counts.** Run the SQL query and cite the result.
- **NEVER assign a bar number to Ronald Berry** — he is a NON-ATTORNEY.
- **NEVER use the child's full name** — L.D.W. initials only per MCR 8.119(H).
- **NEVER fabricate CPS investigation counts** — query DB for actual data.
- **NEVER claim Judge McNeill can be deposed** — judicial immunity limits apply.
