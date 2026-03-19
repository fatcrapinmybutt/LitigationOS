# COMMAND: BUILD-LAWSUIT

## GUIDED LAWSUIT CONSTRUCTION — FACTS TO FILING

This command walks through the complete lawsuit construction process step by step. Each step has defined inputs, outputs, and validation gates.

---

## QUICK START BY CASE LANE

### LANE A — CUSTODY / PARENTAL RIGHTS
```
build-lawsuit --lane A --court "14th Circuit Family Division"
```
**Primary Claims:** Parental rights deprivation, due process violation, custody interference
**Key Statutes:** MCL 722.21+ (Child Custody Act), 42 USC 1983, Troxel v Granville (530 US 57)
**Special Considerations:**
- UCCJEA jurisdiction analysis required (MCL 722.1101+)
- Best interest factors (MCL 722.23) — know them, plead around them
- Emergency custody motions may be needed (MCL 722.27b)
- Parental presumption is a fundamental liberty interest — strict scrutiny applies

### LANE B — HOUSING / HABITABILITY
```
build-lawsuit --lane B --court "14th Circuit Civil Division"
```
**Primary Claims:** Breach of habitability (MCL 554.139), wrongful eviction, MCPA violations, Truth in Renting
**Key Statutes:** MCL 554.139, MCL 554.601+, MCL 445.901+, MCL 554.631+, MCL 600.5714+
**Special Considerations:**
- Document ALL habitability defects with photos, dates, and repair requests
- Rent escrow may be available (MCL 125.530)
- Retaliatory eviction defense (MCL 600.5720)
- Security deposit violations = automatic double damages (MCL 554.613)
- Lead paint disclosure required (42 USC 4852d)

### LANE C — CONVERGENCE / CIVIL RIGHTS
```
build-lawsuit --lane C --court "USDC Western District MI"
```
**Primary Claims:** 42 USC 1983, conspiracy (42 USC 1985/1986), Fair Housing Act, ELCRA
**Key Statutes:** 42 USC 1983, 1985(3), 1986, 42 USC 3601+, MCL 37.2501+
**Special Considerations:**
- Color of state law required for § 1983 — establish state action
- Monell liability requires policy, custom, or failure to train
- Qualified immunity is an affirmative defense — plead clearly to limit its reach
- Attorney fee shifting available under 42 USC 1988
- File in federal court for federal claims; supplemental jurisdiction for state claims (28 USC 1367)

---

## STEP-BY-STEP CONSTRUCTION

### STEP 1: FACT COMPILATION
**Command:** `build-lawsuit --step facts`

**Actions:**
1. Compile ALL known facts chronologically
2. For each fact, record: date, participants, location, documents, witnesses
3. Build a master timeline
4. Identify all potential defendants
5. Identify all potential witnesses
6. Catalog all documentary evidence

**Output:** `fact_compilation.json`
```json
{
  "facts": [
    {
      "id": "F001",
      "date": "2024-XX-XX",
      "description": "...",
      "participants": ["..."],
      "location": "...",
      "documents": ["D001", "D002"],
      "witnesses": ["W001"]
    }
  ],
  "defendants": [...],
  "witnesses": [...],
  "documents": [...]
}
```

**Validation Gate:** Every significant event has a date, description, and at least one evidence item.

### STEP 2: CLAIM IDENTIFICATION
**Command:** `build-lawsuit --step claims`

**Actions:**
1. Run fact pattern against cause of action catalog (references/causes/)
2. For each potential claim:
   - Identify the legal theory
   - Check statute of limitations (USE EXACT DATES)
   - Confirm jurisdiction and venue
   - Assess viability (can you prove every element?)
3. Score each claim: STRONG / MODERATE / WEAK / NON-VIABLE
4. Identify which defendants each claim applies to

**Output:** `claims_analysis.json`
```json
{
  "claims": [
    {
      "id": "C001",
      "cause_of_action": "Fraud",
      "defendants": ["D001", "D002"],
      "elements_count": 6,
      "sol_expiry": "2027-XX-XX",
      "sol_status": "SAFE",
      "strength": "STRONG",
      "lane": "B",
      "key_facts": ["F003", "F007", "F012"]
    }
  ]
}
```

**Validation Gate:** Every claim has SOL confirmed. No non-viable claims carried forward.

### STEP 3: ELEMENT MAPPING
**Command:** `build-lawsuit --step elements`

**Actions:**
1. For each viable claim, list ALL required elements
2. Map each element to specific facts and evidence
3. Identify gaps (elements without sufficient evidence)
4. Develop gap-filling strategy (discovery, subpoenas, FOIA)
5. Assess burden of proof posture per element

**Output:** `element_map.json` (see references/lifecycle/elements-mapping.md)

**Validation Gate:** No claim has a fatal element gap. Each element has at least one evidence item.

### STEP 4: COMPLAINT DRAFTING
**Command:** `build-lawsuit --step draft`

**Actions:**
1. Select complaint template (references/forms/complaint-templates.md)
2. Draft caption (MCR 2.113 compliant)
3. Draft jurisdictional allegations
4. Draft venue allegations
5. Draft party identification paragraphs
6. Draft factual allegations — numbered paragraphs, chronological or thematic
7. Draft each count:
   - Title: "COUNT [N] — [CAUSE OF ACTION]"
   - "Plaintiff incorporates paragraphs [X] through [Y] as if fully set forth herein."
   - Element-specific allegations
   - Damages allegations
8. Draft prayer for relief (specific and general)
9. Add jury demand
10. Prepare verification (if verified complaint)
11. Prepare exhibit list

**Output:** Complete complaint draft in filing-ready format

**Validation Gate:**
- [ ] MCR 2.111 format compliance
- [ ] MCR 2.112 special pleading compliance (fraud, conditions precedent)
- [ ] MCR 2.113 caption compliance
- [ ] Every element of every count is pled
- [ ] Jury demand included
- [ ] Verification language correct
- [ ] All citations verified

### STEP 5: FORM PREPARATION
**Command:** `build-lawsuit --step forms`

**Actions:**
1. Complete MC 01 Summons (one per defendant)
2. Complete civil case cover sheet
3. Complete MC 20 fee waiver (if applicable)
4. Prepare MC 12 proof of service forms
5. Prepare case information sheet
6. Assemble exhibit package
7. Make correct number of copies (original + 1 per party + 1 for plaintiff)

**Output:** Complete filing package

**Validation Gate:** All forms completed and signed. Correct number of copies prepared.

### STEP 6: FILE
**Command:** `build-lawsuit --step file`

**Actions:**
1. Deliver filing package to clerk of court
2. Pay filing fee or submit MC 20 fee waiver
3. Obtain case number
4. Obtain stamped copies
5. Record filing date
6. Calculate service deadline (91 days from filing — MCR 2.102(D))
7. Calendar all deadlines

**Output:** Case number, filed-stamped copies, deadline calendar

**Validation Gate:** Case number obtained. Clerk accepted all documents.

### STEP 7: SERVE
**Command:** `build-lawsuit --step serve`

**Actions:**
1. Determine service method for each defendant (references/forms/service-matrix.md)
2. Arrange service (process server, registered mail, or as required)
3. Execute service on ALL defendants
4. Obtain proof of service for each defendant
5. File MC 12 proof of service with court
6. Calendar answer deadlines:
   - Personal service: 21 days (MCR 2.108(A)(1))
   - Registered mail: 28 days (MCR 2.108(A)(2))
   - Substituted service: 28 days

**Output:** Proof of service filed, answer deadlines calendared

**Validation Gate:** All defendants served within 91 days. All proofs of service filed.

---

## MULTI-DEFENDANT COMPLAINT GUIDANCE

### STRUCTURING COUNTS AGAINST MULTIPLE DEFENDANTS
When suing multiple defendants on overlapping claims:

1. **Joint Counts:** Where defendants acted together (conspiracy, joint tortfeasors), plead a single count naming all participating defendants.
2. **Individual Counts:** Where claims are defendant-specific, plead separate counts per defendant.
3. **Alternative Pleading:** MCR 2.111(A)(2) permits pleading in the alternative. "Defendant A is liable for X, or in the alternative, Defendant B is liable for X."

### CROSS-REFERENCING ALLEGATIONS
- Number ALL paragraphs sequentially across the entire complaint
- Each count incorporates prior paragraphs by reference
- Add count-specific allegations with new paragraph numbers continuing the sequence

### CAPTION FORMAT FOR MULTIPLE DEFENDANTS
```
ANDREW PIGORS,                   )
    Plaintiff,                   )
                                 )   Case No. _______________
v.                               )
                                 )   Hon. ____________________
[DEFENDANT 1 FULL LEGAL NAME],  )
[DEFENDANT 2 FULL LEGAL NAME],  )
[DEFENDANT 3 FULL LEGAL NAME],  )
    jointly and severally,       )
    Defendants.                  )
_________________________________)
```

---

## AMENDED COMPLAINT PROCEDURES

### WHEN TO AMEND (MCR 2.118)
- **Before responsive pleading:** Amend as of right (MCR 2.118(A)(1))
- **After responsive pleading:** By leave of court or written consent of adverse party (MCR 2.118(A)(2))
- **During/after trial:** By leave of court to conform to evidence (MCR 2.118(C))

### RELATION BACK (MCR 2.118(D))
An amendment relates back to the original filing date when:
- The claim arises from the same conduct, transaction, or occurrence as the original
- The party to be added received notice within the service period
- The party knew or should have known the action would have been brought against them

### FORMAT REQUIREMENTS
- Title: "FIRST AMENDED VERIFIED COMPLAINT"
- Clearly mark changes (new paragraphs, modified paragraphs)
- Refile all counts — an amended complaint supersedes the original entirely
- Serve the amended complaint on all parties per MCR 2.107
- File a new cover sheet if case type or parties change

### STRATEGIC CONSIDERATIONS
- Amending signals to the court that the original was imperfect — use sparingly
- If SOL is expiring on new claims, file the amendment BEFORE expiry
- Adding new defendants after SOL requires relation-back analysis
- Keep a clean "tracked changes" version for your records

---

## VALIDATION CHECKLIST — FINAL REVIEW BEFORE FILING

```
[ ] All defendants named with correct legal names
[ ] Jurisdiction properly pled
[ ] Venue properly pled and correct
[ ] All factual allegations in numbered paragraphs
[ ] Every element of every cause of action is pled
[ ] Fraud claims pled with particularity (MCR 2.112(B)(1))
[ ] Conditions precedent specifically alleged (MCR 2.112(B)(2))
[ ] Prayer for relief includes specific and general damages
[ ] Jury demand included (MCR 2.508(B))
[ ] Verification language correct and complaint sworn
[ ] All exhibits referenced, indexed, and attached
[ ] Summons prepared for each defendant
[ ] Filing fee calculated or MC 20 fee waiver completed
[ ] Correct number of copies prepared
[ ] Proof of service forms ready (MC 12)
[ ] Service plan for each defendant documented
[ ] SOL confirmed unexpired for every claim
[ ] MCR 2.114 signature requirements met
```
