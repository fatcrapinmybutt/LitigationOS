# Classification Rules — litigation-evidence-harvester

## Evidence Classification Rule Set

This reference defines the classification rules for categorizing evidence
across all three lanes of Pigors v Watson litigation. Rules are applied
in priority order — first matching rule wins.

---

## Classification Levels

| Level | Definition | Action |
|-------|-----------|--------|
| HIGH | Directly supports or undermines a claim, defense, or credibility | Immediate atom extraction + exhibit preparation |
| MED | Provides context, corroboration, or pattern evidence | Atom extraction + index |
| LOW | Tangentially related, may support secondary arguments | Index only |
| SKIP | Not relevant to any active case lane | Log + skip |

---

## Priority 1: Lane A Classification Rules (Custody/Watson)

### HIGH Classification — Lane A

| Rule ID | Trigger | Rationale |
|---------|---------|-----------|
| A-H-001 | Document contains sworn testimony by Watson | Party admissions / impeachment |
| A-H-002 | Document is a court order in Case 2024-001507-DC or 2023-5907-PP | Active case record |
| A-H-003 | Document contains FOC recommendation or report | Key decision input for McNeill |
| A-H-004 | Document shows violation of existing court order | Contempt evidence |
| A-H-005 | Document relates to child welfare or safety | Best interest factors (MCL 722.23) |
| A-H-006 | Document shows parental fitness/unfitness evidence | Custody modification basis |
| A-H-007 | Document shows alienation behavior by either parent | Factor (j) analysis |
| A-H-008 | Communication between parties about custody/children | Direct party evidence |
| A-H-009 | Document contradicts Watson's sworn statements | Impeachment material |
| A-H-010 | Mental health evaluation or treatment records (with consent/order) | Factor (g) — mental health |

### MED Classification — Lane A

| Rule ID | Trigger | Rationale |
|---------|---------|-----------|
| A-M-001 | School records referencing either parent | Factor (d) — home/school environment |
| A-M-002 | Medical records of child (with consent/order) | Factor (c) — physical needs |
| A-M-003 | Communications with third parties about custody | Context / pattern |
| A-M-004 | Prior court filings not in active case | Background / history |
| A-M-005 | Employment records of either parent | Factor (c) — financial capacity |

### LOW Classification — Lane A

| Rule ID | Trigger | Rationale |
|---------|---------|-----------|
| A-L-001 | General background on parties | Context only |
| A-L-002 | Social media posts not directly case-related | Potential future relevance |
| A-L-003 | Receipts / financial records not custody-related | Peripheral |

---

## Priority 2: Lane B Classification Rules (Housing/Shady Oaks)

### HIGH Classification — Lane B

| Rule ID | Trigger | Rationale |
|---------|---------|-----------|
| B-H-001 | Inspection report showing habitability defects | MCL 554.139 evidence |
| B-H-002 | Photos of housing conditions (mold, structural, plumbing) | Direct evidence of conditions |
| B-H-003 | Written notice to Shady Oaks of defects | Notice requirement proof |
| B-H-004 | Shady Oaks response (or non-response) to complaints | Knowledge/inaction evidence |
| B-H-005 | Lease agreement and amendments | Contractual obligations |
| B-H-006 | Shady Oaks corporate communications re: conditions | Corporate knowledge |
| B-H-007 | Alden Global communications re: Shady Oaks | Parent company liability |
| B-H-008 | Health impact documentation from housing conditions | Damages evidence |
| B-H-009 | Government code enforcement records | Official documentation |
| B-H-010 | Rent payment records | Tenancy proof + damages calculation |

### MED Classification — Lane B

| Rule ID | Trigger | Rationale |
|---------|---------|-----------|
| B-M-001 | Other tenant complaints about same property | Pattern evidence |
| B-M-002 | Shady Oaks marketing/advertising materials | Consumer protection claims |
| B-M-003 | Repair records / maintenance logs | Repair history |
| B-M-004 | Insurance documents related to property | Corporate structure |
| B-M-005 | Michigan LARA filings for Shady Oaks / Alden Global | Entity registration |

### LOW Classification — Lane B

| Rule ID | Trigger | Rationale |
|---------|---------|-----------|
| B-L-001 | General manufactured housing industry information | Background |
| B-L-002 | News articles about Shady Oaks or Alden Global | Public record |
| B-L-003 | Similar cases in other jurisdictions | Persuasive authority only |

---

## Priority 3: Lane C Classification Rules (Convergence/County)

### HIGH Classification — Lane C

| Rule ID | Trigger | Rationale |
|---------|---------|-----------|
| C-H-001 | Evidence of judicial misconduct | JTC complaint / recusal basis |
| C-H-002 | Evidence linking Lane A and Lane B (same actors, same patterns) | Convergence proof |
| C-H-003 | Government official actions violating constitutional rights | § 1983 elements |
| C-H-004 | Records showing pattern of similar violations by same officials | Pattern evidence |
| C-H-005 | Internal government communications re: case parties | Knowledge / intent |
| C-H-006 | FOC administrative records showing systemic issues | Institutional misconduct |

### MED Classification — Lane C

| Rule ID | Trigger | Rationale |
|---------|---------|-----------|
| C-M-001 | Public records from Muskegon County offices | Government documentation |
| C-M-002 | Other litigant complaints about same officials | Pattern corroboration |
| C-M-003 | Media coverage of judicial or official conduct | Public record |

---

## Cross-Lane (MULTI) Classification Rules

| Rule ID | Trigger | Classification |
|---------|---------|---------------|
| X-001 | Document relevant to both custody and housing | MULTI (A+B) |
| X-002 | Document showing connection between housing conditions and child welfare | MULTI (A+B) — HIGH |
| X-003 | Document showing government involvement in both custody and housing | MULTI (A+B+C) |
| X-004 | Evidence of coordinated action by opposing parties across lanes | MULTI — HIGH |

---

## SKIP Classification Rules

| Rule ID | Trigger | Action |
|---------|---------|--------|
| S-001 | System-generated file (log, temp, cache, thumbs.db) | SKIP + log |
| S-002 | Duplicate of already-classified document (same hash) | SKIP + link to original |
| S-003 | Corrupted file (unreadable after all handler attempts) | SKIP + error log |
| S-004 | File from unrelated matter with no connection to any lane | SKIP + log |
| S-005 | Software installation files, drivers, system files | SKIP |

---

## Classification Override Protocol

Automated classification may be overridden by manual review when:

1. **Case theory changes**: A document previously classified LOW becomes HIGH under new theory
2. **New connection discovered**: Document links to newly identified witness or entity
3. **Opposing filing references document**: Anything referenced by opposition becomes HIGH
4. **Cross-lane link found**: Document connects multiple lanes → upgrade to MULTI

### Override Record
```
Override ID: OR-[XXX]
Document ID: [DOC-XXXXXX]
Original classification: [HIGH | MED | LOW | SKIP]
New classification: [HIGH | MED | LOW | SKIP]
Reason: [Specific reason for override]
Date: [YYYY-MM-DD]
Reviewer: [Name]
```
