# Extraction Patterns — litigation-evidence-harvester

## Evidence Atom Extraction Patterns

This reference defines the patterns used to extract discrete evidence atoms
from documents in the Pigors v Watson evidence collection. Each pattern
identifies a specific type of evidentiary information and defines how to
extract, structure, and score it.

---

## Atom Types

| Atom Type | Code | Description |
|-----------|------|-------------|
| Factual Assertion | FACT | A specific claim about what happened |
| Admission | ADM | Statement against declarant's interest |
| Contradiction | CONTRA | Statement conflicting with other evidence |
| Timeline Event | TIME | Date-stamped factual occurrence |
| Financial Data | FIN | Monetary amounts, transactions, accounts |
| Relationship | REL | Connection between persons or entities |
| Legal Conclusion | LEGAL | Statement about legal rights/obligations |
| Condition Report | COND | Description of physical conditions |

---

## Pattern EP-001: Factual Assertion Extraction

### Trigger
Any sentence or paragraph that asserts a specific fact about events,
conditions, actions, or states relevant to the case.

### Extraction Template
```yaml
atom_id: ATM-[auto]
atom_type: FACT
text: "[Exact text of the assertion]"
source:
  document: "[File path]"
  page: [N]
  line_start: [N]
  line_end: [N]
who: "[Person making/about whom assertion is made]"
what: "[Action or state described]"
when: "[Date/time if specified]"
where: "[Location if specified]"
lane: [A | B | C | MULTI]
relevance_score: [0-100]
```

### Scoring Rules for FACT Atoms
| Factor | Points | Criteria |
|--------|--------|----------|
| Direct case relevance | 0–40 | Does this fact go to an element of a claim or defense? |
| Source reliability | 0–20 | Sworn > Unsworn > Informal |
| Corroboration potential | 0–15 | Can this be independently verified? |
| Uniqueness | 0–10 | Is this fact available only from this source? |
| Impeachment value | 0–15 | Does this contradict opposing party's position? |

---

## Pattern EP-002: Admission Extraction

### Trigger
Statement by a party (or their agent/representative) that is adverse
to their position in the litigation.

### Michigan Rule: MRE 801(d)(2)
Admissions by a party-opponent are excluded from the hearsay rule
and admissible for all purposes.

### Sub-Types
| Sub-Type | MRE Rule | Example |
|----------|----------|---------|
| Direct admission | 801(d)(2)(A) | Watson: "I didn't check on the kids that night" |
| Adoptive admission | 801(d)(2)(B) | Watson nods when told "you left them alone" |
| Authorized admission | 801(d)(2)(C) | Shady Oaks spokesperson: "We knew about the mold" |
| Agent admission | 801(d)(2)(D) | Shady Oaks maintenance worker: "We don't fix those" |

### Extraction Template
```yaml
atom_id: ATM-[auto]
atom_type: ADM
text: "[Exact text of admission]"
declarant: "[Who made the statement]"
declarant_role: "[Party | Agent | Employee | Representative]"
adverse_to: "[Which party's interest this hurts]"
mre_rule: "[801(d)(2)(A) through (D)]"
source:
  document: "[File path]"
  page: [N]
  line_start: [N]
  line_end: [N]
context: "[Circumstances of the statement]"
sworn: [true | false]
lane: [A | B | C | MULTI]
relevance_score: [0-100]
```

---

## Pattern EP-003: Contradiction Extraction

### Trigger
A statement that conflicts with another statement by the same person
or with documentary/physical evidence.

### Extraction Template
```yaml
atom_id: ATM-[auto]
atom_type: CONTRA
statement_1:
  text: "[First statement]"
  source: "[Document]"
  date: "[Date]"
  page_line: "[P/L]"
statement_2:
  text: "[Conflicting statement]"
  source: "[Document]"
  date: "[Date]"
  page_line: "[P/L]"
witness: "[Who made contradictory statements]"
contradiction_type: [DIRECT | OMISSION | TEMPORAL | DEGREE | CONTEXTUAL]
lane: [A | B | C | MULTI]
relevance_score: [0-100]
```

*Note*: Contradictions are forwarded to litigation-impeachment-engine for
detailed analysis and impeachment package assembly.

---

## Pattern EP-004: Timeline Event Extraction

### Trigger
Any reference to a specific date, time, or temporal sequence relevant to
the case facts.

### Extraction Template
```yaml
atom_id: ATM-[auto]
atom_type: TIME
event: "[Description of what happened]"
date: "[YYYY-MM-DD or range]"
time: "[HH:MM if known]"
precision: [EXACT | APPROXIMATE | RANGE]
source:
  document: "[File path]"
  page: [N]
  line_start: [N]
participants: ["[List of persons involved]"]
lane: [A | B | C | MULTI]
relevance_score: [0-100]
```

### Critical Timeline Events by Lane

**Lane A (Custody)**:
- Custody order dates and modifications
- Incidents affecting child welfare
- PPO filing and modification dates
- FOC recommendation dates
- Parenting time violations

**Lane B (Housing)**:
- Lease execution and renewal dates
- Condition first reported dates
- Repair request dates
- Inspection dates
- Code enforcement dates
- Move-in / move-out dates

**Lane C (Convergence)**:
- Judicial conduct incident dates
- Government action dates
- Cross-lane event connections

---

## Pattern EP-005: Financial Data Extraction

### Trigger
Any reference to monetary amounts, financial transactions, accounts,
or economic data relevant to damages or claims.

### Extraction Template
```yaml
atom_id: ATM-[auto]
atom_type: FIN
description: "[What the financial data represents]"
amount: [N.NN]
currency: "USD"
date: "[YYYY-MM-DD]"
parties: ["[Payor]", "[Payee]"]
transaction_type: "[Payment | Invoice | Fee | Damage | Rent | etc.]"
source:
  document: "[File path]"
  page: [N]
lane: [A | B | C | MULTI]
relevance_score: [0-100]
```

**Lane A Financial Targets**: Child support amounts, legal fees, income data
**Lane B Financial Targets**: Rent payments, repair costs, damage assessments,
  diminished property values, medical costs from housing conditions

---

## Pattern EP-006: Relationship Extraction

### Trigger
Any information establishing a connection between persons, entities,
or organizations relevant to the litigation.

### Extraction Template
```yaml
atom_id: ATM-[auto]
atom_type: REL
entity_a: "[Person or organization]"
entity_b: "[Person or organization]"
relationship: "[Type: employs, owns, controls, related_to, etc.]"
evidence: "[Text establishing the relationship]"
source:
  document: "[File path]"
  page: [N]
lane: [A | B | C | MULTI]
relevance_score: [0-100]
```

### Key Relationships to Extract
| Relationship | Why It Matters |
|-------------|----------------|
| Alden Global → Shady Oaks | Corporate control / veil piercing |
| Shady Oaks → Property managers | Agent liability |
| Watson → Third parties | Witness identification |
| County officials → Judicial officers | Convergence connections |
| FOC → Judicial officers | Institutional relationships |

---

## Pattern EP-007: Condition Report Extraction

### Trigger (Lane B Primary)
Any description of physical conditions at Shady Oaks properties,
including photographs, inspection reports, and tenant complaints.

### Extraction Template
```yaml
atom_id: ATM-[auto]
atom_type: COND
location: "[Specific unit/area]"
condition: "[Description of defect/condition]"
category: "[Mold | Structural | Plumbing | Electrical | HVAC | Pest | Safety]"
severity: "[CRITICAL | SERIOUS | MODERATE | MINOR]"
date_observed: "[YYYY-MM-DD]"
observer: "[Who documented this]"
photo_evidence: [true | false]
reported_to_landlord: [true | false | unknown]
date_reported: "[YYYY-MM-DD | null]"
landlord_response: "[Description | null]"
source:
  document: "[File path]"
  page: [N]
lane: B
relevance_score: [0-100]
```

### Condition Severity for MCL 554.139
| Severity | Definition | Legal Significance |
|----------|-----------|-------------------|
| CRITICAL | Immediate health/safety hazard | Grounds for rent abatement + injunction |
| SERIOUS | Significant habitability impairment | Grounds for damages + repair order |
| MODERATE | Reduced quality of living | Supports damages claim |
| MINOR | Cosmetic / convenience issue | Weak standing alone; pattern value |

---

## Batch Processing Configuration

### Recommended Processing Order
1. Court filings (known-relevant, establish baseline)
2. Communications (emails, texts — high impeachment value)
3. Photographs (visual evidence — Lane B priority)
4. Financial records (damages quantification)
5. Public records (authentication + context)
6. Remaining documents (classification determines priority)

### Performance Targets
| Metric | Target |
|--------|--------|
| Text documents | 1,000 files/hour |
| PDF (text) | 500 files/hour |
| PDF (OCR) | 100 files/hour |
| Images (OCR) | 200 files/hour |
| Emails | 800 files/hour |
| Total collection (427,956) | ~200 processing hours |
