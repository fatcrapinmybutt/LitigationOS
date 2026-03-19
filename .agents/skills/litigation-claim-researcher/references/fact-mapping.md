# Fact-to-Element Mapping — Systematic Protocol

> Deep reference for Phase 4 element-by-element analysis
> Context: Pigors v Watson | Michigan | 14th Judicial Circuit

---

## 5-Step Mapping Protocol

### Step 1: List ALL Facts

Create a master fact inventory. Every fact gets a unique identifier.

| Fact ID | Date | Actor | Description | Source/Evidence |
|---------|------|-------|-------------|----------------|
| F-001 | 2024-01-15 | Defendant Watson | Represented property was in "move-in ready" condition | Text message (Exhibit A) |
| F-002 | 2024-01-20 | Plaintiff Pigors | Signed lease based on Watson's representations | Lease agreement (Exhibit B) |
| F-003 | 2024-02-01 | Plaintiff Pigors | Moved in and discovered [defect] | Photographs (Exhibit C) |
| ... | ... | ... | ... | ... |

**Rules for fact listing:**
- Include negative facts (things that DIDN'T happen but should have)
- Include omission facts (duties not performed, notices not given)
- Include background facts (relationships, capacities, regulatory status)
- Include timing facts (when notice was given, when deadlines expired)
- Include quantum facts (amounts paid, amounts owed, amounts lost)

### Step 2: For Each Fact, Identify Violated Rights

| Fact ID | Right Violated | Legal Basis |
|---------|---------------|-------------|
| F-001 | Right to truthful dealing | Common law fraud; MCPA 445.903(1)(s) |
| F-001 | Right to accurate property condition disclosure | MCL 554.139; silent fraud |
| F-003 | Right to habitable premises | MCL 554.139(1)(a) |
| F-003 | Right to code-compliant housing | Michigan Building Code; IPMC |

**Key principle:** A single fact can violate MULTIPLE rights simultaneously. Map every right, not just the most obvious one.

### Step 3: For Each Right, Identify Statutes and Common Law

| Right | Statutory Basis | Common Law Basis |
|-------|----------------|-----------------|
| Truthful dealing | MCPA MCL 445.903(1)(s) | Fraud, silent fraud |
| Habitable premises | MCL 554.139 | Implied warranty |
| Quiet enjoyment | (lease covenant) | Common law covenant |
| Deposit return | MCL 554.601 et seq. | N/A (purely statutory) |
| Non-retaliation | MCL 600.5720 | N/A (purely statutory) |
| Building code compliance | State Construction Code MCL 125.1501 | Negligence per se |

### Step 4: For Each Cause of Action, Check ALL Elements

**Element Mapping Template:**

```
═══════════════════════════════════════════════════════════
CLAIM: FRAUD
═══════════════════════════════════════════════════════════

ELEMENT 1: Material representation
  → Supporting Facts: F-001 (Watson stated property was "move-in ready")
  → Evidence: Text message dated 2024-01-15 (Exhibit A)
  → Strength: STRONG — direct quote from defendant
  → Counterargument: Watson may claim "move-in ready" is subjective/puffery
  → Rebuttal: Specific factual representation about condition, not opinion

ELEMENT 2: Falsity
  → Supporting Facts: F-003 (discovered [defect] on move-in)
  → Evidence: Photographs (Exhibit C), inspection report (Exhibit D)
  → Strength: STRONG — objective evidence contradicts representation
  → Counterargument: Watson may claim condition changed after statement
  → Rebuttal: Timeline shows condition existed before representation

ELEMENT 3: Knowledge of falsity / reckless disregard
  → Supporting Facts: [identify facts showing defendant knew]
  → Evidence: [prior inspection reports, prior complaints, prior notices]
  → Strength: [STRONG/ARGUABLE/WEAK]
  → Counterargument: Watson may claim no knowledge
  → Rebuttal: [constructive knowledge through ownership, duty to inspect]

ELEMENT 4: Intent that plaintiff would act on it
  → Supporting Facts: [representation made in context of lease negotiation]
  → Evidence: [timing of statement relative to signing]
  → Strength: [assess]
  → Counterargument: [casual conversation, not inducement]
  → Rebuttal: [made in direct response to inquiry about condition]

ELEMENT 5: Actual reliance
  → Supporting Facts: F-002 (signed lease after representation)
  → Evidence: Lease execution date after representation date
  → Strength: [assess — did plaintiff have independent knowledge?]
  → Counterargument: Plaintiff should have inspected independently
  → Rebuttal: Right to rely on landlord's representations; no duty to independently verify

ELEMENT 6: Resulting damages
  → Supporting Facts: [all harm facts]
  → Evidence: [receipts, invoices, medical records, testimony]
  → Strength: [assess]
  → Damages Calculation: $[amount] + consequentials

COVERAGE: [X/6 elements met] = [XX%]
OVERALL STRENGTH: [STRONG/ARGUABLE/WEAK]
═══════════════════════════════════════════════════════════
```

### Step 5: Score Coverage Percentage

| Score | Meaning | Action |
|-------|---------|--------|
| 100% | All elements strongly supported | File immediately — CRITICAL priority |
| 80-99% | Most elements strong, one or two arguable | File — HIGH priority |
| 60-79% | Majority of elements supported, some weak | File with caveats — MEDIUM priority |
| 40-59% | Half the elements supported | Investigate further before filing |
| 20-39% | Minority of elements supported | Defer — develop facts |
| 0-19% | Most elements not supported | Reject — state reason |

---

## Implied Fact Identification

Every explicit fact implies additional facts. The agent must identify these:

| Explicit Fact | Implied Facts |
|--------------|---------------|
| Lease agreement exists | Implied warranty of habitability (MCL 554.139), covenant of quiet enjoyment, security deposit obligations (if deposit paid), Truth in Renting compliance required |
| Defendant owns property | Duty to maintain (MCL 554.139(1)(b)), duty to comply with building code, premises liability duty to invitees, duty to disclose known defects |
| Plaintiff complained to code enforcement | Retaliatory action protection triggered (MCL 600.5720), 90-day presumption window activated |
| Defendant is a business entity | MCPA may apply (trade or commerce), entity records are discoverable, registered agent exists for service |
| Defendant has multiple properties | Pattern evidence admissible, other tenants are potential witnesses, business practices discoverable |

---

## Evidence Quality Assessment

For each piece of evidence supporting an element:

| Evidence Type | Reliability | Weight |
|--------------|------------|--------|
| Signed contract/document | Very High | Primary evidence |
| Written correspondence (email, text) | High | Direct evidence of statements/knowledge |
| Photographs with metadata | High | Objective condition evidence |
| Government inspection reports | High | Official record, admissible |
| Witness testimony (disinterested) | Medium-High | Credible if consistent |
| Witness testimony (interested party) | Medium | Credibility contested |
| Plaintiff's own testimony | Medium | Credible but self-interested |
| Circumstantial evidence | Medium-Low | Must build inference chain |
| Hearsay (without exception) | Low | Inadmissible without exception |

---

## Multi-Defendant Fact Mapping

When multiple defendants are involved, map each defendant's conduct separately:

```
DEFENDANT: Watson (Individual)
  Facts attributable: F-001, F-003, F-007, F-012
  Claims against: Fraud, IIED, negligence
  Personal participation: [describe]

DEFENDANT: Watson Properties LLC
  Facts attributable: F-002, F-004, F-008
  Claims against: Breach of contract, habitability, MCPA
  Entity liability: [describe]

SHARED LIABILITY:
  Civil conspiracy between Watson and Watson Properties LLC
  Facts: Coordinated conduct F-005, F-009
  Theory: Individual used entity to commit fraud, entity used individual as agent
```
