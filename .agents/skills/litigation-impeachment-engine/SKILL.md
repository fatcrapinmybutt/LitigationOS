---
name: litigation-impeachment-engine
description: >-
  Use when detecting contradictions in testimony or documents, preparing prior inconsistent statement packages, or analyzing transcripts for impeachment under MRE 613.
metadata:
  category: discipline
  author: andrew-pigors
  version: "1.0.0"
  triggers: impeachment, contradiction, transcript, prior statement, MRE 613
---

# litigation-impeachment-engine

## Metadata

```yaml
name: litigation-impeachment-engine
version: 2.0.0
category: discipline
tier: 2
description: >
  Use when detecting contradictions in testimony or documents, preparing prior
  inconsistent statement packages, analyzing transcripts for impeachment
  opportunities, and applying MRE 613/801(d)(1) in Michigan 14th Judicial
  Circuit (Muskegon County) litigation.
triggers:
  - impeachment
  - contradiction
  - prior inconsistent statement
  - transcript analysis
  - witness credibility
  - MRE 613
  - cross-examination
  - deposition
```

## Purpose

This skill systematically identifies contradictions across all witness statements,
depositions, affidavits, court filings, and public records in the Pigors v Watson
litigation. It produces court-ready impeachment packages compliant with Michigan
Rules of Evidence, particularly MRE 613 (prior inconsistent statements) and
MRE 801(d)(1) (prior statements by witness).

## Case Context

| Lane | Key Witnesses | Document Sources |
|------|---------------|------------------|
| A (Custody) | Watson, FOC workers, therapists, teachers | Custody filings, FOC reports, depositions |
| B (Housing) | Shady Oaks reps, inspectors, tenants | Inspection reports, communications, complaints |
| C (Convergence) | County officials, judges, administrators | Public records, hearing transcripts, filings |

## Decision Tree

```
INPUT: Witness name + document collection + target claims
  │
  ├─ Phase 1: STATEMENT HARVESTING
  │   ├─ Collect all statements by target witness
  │   │   ├─ Sworn testimony (depositions, hearings)
  │   │   ├─ Written filings (affidavits, declarations)
  │   │   ├─ Informal statements (emails, texts, reports)
  │   │   └─ Public statements (social media, interviews)
  │   │
  │   ├─ Normalize statements into atoms
  │   │   ├─ Extract claim + date + source + context
  │   │   ├─ Categorize: factual / opinion / legal conclusion
  │   │   └─ Tag reliability: sworn / unsworn / informal
  │   │
  │   └─ Build statement timeline (chronological)
  │
  ├─ Phase 2: CONTRADICTION DETECTION
  │   ├─ Intra-witness comparison
  │   │   ├─ Same witness, different statements → conflict?
  │   │   ├─ Same topic, different dates → evolution or contradiction?
  │   │   └─ Same facts, different framing → material inconsistency?
  │   │
  │   ├─ Cross-witness comparison
  │   │   ├─ Witness A vs. Witness B on same event
  │   │   ├─ Witness vs. documentary evidence
  │   │   └─ Witness vs. physical evidence
  │   │
  │   ├─ Contradiction classification
  │   │   ├─ DIRECT: Flat contradiction (said X, then said not-X)
  │   │   ├─ MATERIAL OMISSION: Critical fact present then absent
  │   │   ├─ TEMPORAL: Timeline inconsistency
  │   │   ├─ DEGREE: Magnitude shift (minor → major or reverse)
  │   │   └─ CONTEXTUAL: Contradicted by surrounding facts
  │   │
  │   └─ Score each contradiction
  │       ├─ Materiality (0–10): How important to case outcome?
  │       ├─ Clarity (0–10): How clear is the contradiction?
  │       └─ Provability (0–10): How easily demonstrated in court?
  │
  ├─ Phase 3: IMPEACHMENT PACKAGE ASSEMBLY
  │   ├─ For each viable contradiction (composite score ≥ 15):
  │   │   ├─ Statement A: Full text + source citation + page/line
  │   │   ├─ Statement B: Full text + source citation + page/line
  │   │   ├─ Contradiction analysis: Why these conflict
  │   │   ├─ MRE foundation: Which rule applies
  │   │   ├─ Examination script: Question sequence for cross
  │   │   └─ Exhibit preparation: Documents to present
  │   │
  │   ├─ MRE 613 compliance check
  │   │   ├─ (a) Examining witness: Contents disclosed, opportunity to explain
  │   │   ├─ (b) Extrinsic evidence: Foundation laid, witness given chance to deny
  │   │   └─ Timing: Contradiction raised before witness excused
  │   │
  │   └─ MRE 801(d)(1) analysis
  │       ├─ (A) Prior inconsistent: Given under oath at proceeding?
  │       ├─ (B) Consistent statement: Rebutting fabrication charge?
  │       └─ (C) Identification: Prior identification of person?
  │
  └─ Phase 4: OUTPUT GENERATION
      ├─ Contradiction matrix (all detected contradictions)
      ├─ Ranked impeachment targets
      ├─ Cross-examination scripts
      ├─ Exhibit packages (ready for court marking)
      └─ Foundation checklists per MRE
```

## Mode Switches

### Mode 1: FULL SCAN
Scans entire document collection for all contradictions by all witnesses.
Most comprehensive but most time-intensive.

### Mode 2: TARGETED WITNESS
Focuses on a single witness across all document sources.
Use when preparing for specific deposition or cross-examination.

### Mode 3: TARGETED TOPIC
Scans all witnesses on a specific factual issue.
Use when a particular claim is central to a motion.

### Mode 4: TRANSCRIPT ATTACK
Deep analysis of a single transcript for internal contradictions,
evasions, non-responsive answers, and impeachable moments.

### Mode 5: PACKAGE ASSEMBLY
Generates court-ready impeachment package from previously identified
contradictions. Formats for exhibit marking and presentation.

## Output Contract

```yaml
output:
  contradiction_matrix:
    type: table
    columns:
      - id: string (C001, C002, ...)
      - witness: string
      - topic: string
      - statement_a: {text, source, date, page_line}
      - statement_b: {text, source, date, page_line}
      - type: DIRECT | MATERIAL_OMISSION | TEMPORAL | DEGREE | CONTEXTUAL
      - materiality: integer (0–10)
      - clarity: integer (0–10)
      - provability: integer (0–10)
      - composite_score: integer (0–30)
      - lane: A | B | C

  impeachment_package:
    type: document_set
    per_contradiction:
      - setup_questions: list[string]     # Lock witness into position
      - confront_questions: list[string]  # Present contradiction
      - exhibit_reference: string         # Marked exhibit ID
      - foundation_checklist: list[{step, mre_rule, status}]
      - anticipated_explanation: string   # What witness might say
      - rebuttal_to_explanation: string   # Counter to excuse

  cross_examination_script:
    type: document
    format: Q&A with annotations
    includes:
      - witness_name
      - topic_headers
      - question_sequence (numbered)
      - expected_answers
      - impeachment_triggers (flagged questions)
      - exhibit_cues

  transcript_analysis:
    type: report
    sections:
      - evasive_answers: list[{page_line, question, answer, analysis}]
      - non_responsive: list[{page_line, question, answer}]
      - internal_contradictions: list[{stmt_1, stmt_2, analysis}]
      - admissions: list[{page_line, admission_text, significance}]
      - credibility_score: float (0.0–1.0)
```

## MRE 613 — Prior Inconsistent Statements (Detailed)

### Foundation Requirements
1. **Disclose contents**: Witness must be told substance of prior statement
2. **Identify circumstances**: When, where, and to whom statement was made
3. **Opportunity to explain**: Witness must be given chance to explain or deny
4. **Extrinsic evidence**: If witness denies, extrinsic proof admissible
5. **Timing**: Must occur while witness is still subject to recall

### Cross-Examination Pattern (MRE 613)
```
Step 1: COMMIT — Lock witness into current testimony
  Q: "You testified today that [current claim], correct?"

Step 2: CREDIT — Establish reliability of prior statement
  Q: "You previously gave a sworn statement on [date], correct?"
  Q: "You understood the importance of telling the truth?"
  Q: "You signed that statement under oath?"

Step 3: CONFRONT — Present the contradiction
  Q: "I'm showing you Exhibit [X], your sworn statement of [date]."
  Q: "Please read the highlighted portion on page [X], line [Y]."
  Q: "In that statement, you said [prior inconsistent claim], correct?"

Step 4: CONTRAST — Highlight the inconsistency
  Q: "So on [prior date], you said [A], but today you say [B]?"
```

## MRE 801(d)(1) — Substantive Use

### When Prior Statement Is NOT Hearsay
- **(A)** Prior inconsistent statement given under oath at a trial,
  hearing, other proceeding, or deposition → admissible substantively
- **(B)** Consistent statement offered to rebut charge of recent
  fabrication, improper influence, or motive → admissible
- **(C)** Statement of identification made after perceiving the person
  → admissible

### Strategic Implications
| Scenario | MRE Rule | Use | Admissibility |
|----------|----------|-----|---------------|
| Deposition contradicts trial testimony | 801(d)(1)(A) | Substantive | Full |
| Hearing testimony contradicts affidavit | 613 + 801(d)(1)(A) | Substantive if sworn | Full |
| Email contradicts testimony | 613 | Impeachment only | Limited |
| Text message contradicts testimony | 613 | Impeachment only | Limited |

## Contradiction Scoring Guide

| Score Range | Label | Action |
|-------------|-------|--------|
| 25–30 | DEVASTATING | Lead impeachment — case-changing |
| 20–24 | STRONG | Major impeachment — high impact |
| 15–19 | VIABLE | Solid impeachment — include in package |
| 10–14 | MARGINAL | Use only if needed for cumulative effect |
| 0–9 | WEAK | Do not use — may backfire |

## Integration Points

- **litigation-filing-architect**: Receives impeachment exhibits for filing packages
- **litigation-red-team**: Tests impeachment strategy for counter-attack vulnerabilities
- **litigation-judicial-analyst**: Provides transcript data for judicial impeachment
- **litigation-evidence-harvester**: Supplies source documents for statement harvesting

## Usage Examples

```
# Full scan for all contradictions
invoke litigation-impeachment-engine --mode full --sources ./evidence/

# Target specific witness
invoke litigation-impeachment-engine --mode witness --target "Watson" --sources ./depositions/

# Analyze specific transcript
invoke litigation-impeachment-engine --mode transcript --file hearing_2025-01-15.md

# Build impeachment package for top contradictions
invoke litigation-impeachment-engine --mode package --contradictions C001,C003,C007
```

## Related Skills

- [litigation-red-team](skill://litigation-red-team) — Stress-tests filings via adversarial review
- [litigation-evidence-harvester](skill://litigation-evidence-harvester) — Extracts and classifies case evidence

---

## Live Database Statistics (litigation_context.db)

| Table | Row Count | Description |
|-------|-----------|-------------|
| `impeachment_items` | 15,171 | Impeachment-ready inconsistencies across all witnesses |
| `contradiction_map` | 10,558 | Detected contradictions with severity scoring |
| `evidence_quotes` | 308,636 | Source evidence passages for statement harvesting |
| `pages` | 472,211 | Raw page text for deep statement mining |
| `master_citations` | 3,600,000+ | Citation corpus for authority backing |

### Key Queries
```sql
-- Top impeachment targets by composite score
SELECT speaker, statement, contradicting_text, legal_hook,
       (materiality + clarity + provability) as composite
FROM impeachment_items
ORDER BY composite DESC LIMIT 20;

-- All contradictions for a specific witness
SELECT source_a_text, source_b_text, contradiction_type, severity
FROM contradiction_map
WHERE speaker = 'Watson'
ORDER BY severity DESC;

-- Sworn vs. unsworn contradictions (MRE 801(d)(1)(A) substantive use)
SELECT * FROM impeachment_items
WHERE legal_hook LIKE '%sworn%' OR legal_hook LIKE '%deposition%'
ORDER BY (materiality + clarity + provability) DESC;
```

---

## MRE 613 — Prior Inconsistent Statements (Extended)

### Foundation Checklist (Must Complete Before Confrontation)
1. ✅ **Commit**: Lock witness into current testimony on the specific point
2. ✅ **Identify prior statement**: Specify date, place, circumstances, and to whom
3. ✅ **Disclose contents**: Tell witness the substance of the prior statement
4. ✅ **Opportunity to explain or deny**: Witness must be given chance to respond
5. ✅ **Extrinsic evidence ready**: If witness denies, have the document marked as exhibit
6. ✅ **Witness still subject to recall**: Complete before witness is excused

### MRE 613(a) — Examining the Witness
The witness need not be shown the prior statement before questioning about it, but on request the statement must be shown to opposing counsel. The key: you can confront with the SUBSTANCE without showing the document first.

### MRE 613(b) — Extrinsic Evidence of Prior Inconsistent Statement
Extrinsic evidence of a prior inconsistent statement is admissible IF:
1. The witness is given opportunity to explain or deny, AND
2. The opposite party is given opportunity to interrogate the witness
Exception: Admissions by a party-opponent (MRE 801(d)(2)) need NO foundation.

---

## MRE 608 — Character Evidence for Truthfulness

### MRE 608(a) — Opinion and Reputation Evidence
- A witness's credibility may be attacked by opinion or reputation evidence of **untruthfulness**
- After credibility is attacked, it may be supported by opinion or reputation evidence of **truthfulness**
- Character for truthfulness is ONLY admissible after an attack on credibility

### MRE 608(b) — Specific Instances of Conduct
- On cross-examination, the court MAY allow inquiry into specific instances of conduct probative of truthfulness
- **Cannot prove by extrinsic evidence** — limited to cross-examination
- Must be in good faith (must have factual basis for the question)
- Court has discretion under MRE 403 to limit

### Strategic Application
| Witness | Character Attack | Basis | MRE Rule |
|---------|-----------------|-------|----------|
| Watson | Pattern of false statements to court | Multiple documented contradictions | 608(b) |
| Watson | Reputation for dishonesty | FOC reports, third-party statements | 608(a) |
| FOC Worker | Bias in reporting | Selective omission pattern | 608(b) |

---

## MRE 609 — Impeachment by Evidence of Conviction

### MRE 609(a) — General Rule
Evidence of a conviction is admissible for impeachment IF:
1. Crime punishable by imprisonment > 1 year, AND
2. Court determines probative value outweighs prejudicial effect (MRE 403 balancing)

### MRE 609(a)(2) — Dishonesty or False Statement
Evidence of conviction of a crime involving dishonesty or false statement is admissible WITHOUT balancing — automatic admission regardless of prejudice.

### MRE 609(c) — Time Limit
Convictions > 10 years old are presumptively inadmissible unless:
- Probative value substantially outweighs prejudicial effect, AND
- Proponent gives advance written notice

### MRE 609(d) — Juvenile Adjudications
Generally NOT admissible, except in criminal cases where necessary for fair determination.

### Application Checklist
- [ ] Check criminal history for all witnesses
- [ ] Identify crimes of dishonesty (fraud, perjury, forgery, embezzlement)
- [ ] Verify convictions are within 10-year window
- [ ] Prepare MRE 403 balancing argument for non-dishonesty crimes
- [ ] Draft motion in limine if needed to resolve admissibility pretrial

---

## Cross-Examination Script Generation Pattern

### Script Structure (Per Impeachment Target)
```
CROSS-EXAMINATION SCRIPT: [Witness Name]
Topic: [Subject Matter]
Impeachment Items: [C-XXXXX, C-XXXXX]
Estimated Duration: [X] minutes

SECTION 1: ESTABLISH BASELINE (2-3 questions)
  Purpose: Lock witness into current position
  Q1: [Question that commits witness to current testimony]
  Expected A: [Yes/specific answer]
  If unexpected: [Redirect strategy]

SECTION 2: CREDIT THE PRIOR STATEMENT (3-4 questions)
  Purpose: Establish reliability of the prior document
  Q2: You gave a statement on [date], correct?
  Q3: You understood the importance of being truthful?
  Q4: [If sworn] You were under oath at that time?
  Expected A: Yes to all

SECTION 3: CONFRONT WITH CONTRADICTION (2-3 questions)
  Purpose: Present the inconsistency
  Q5: I'm showing you what's been marked Exhibit [X].
  Q6: Please read the highlighted portion. [Wait]
  Q7: In that [document], you stated [prior statement], correct?
  Expected A: Reluctant admission or attempted explanation

SECTION 4: HIGHLIGHT CONTRAST (1-2 questions)
  Purpose: Make the contradiction explicit for the record
  Q8: So on [date 1] you said [A], but today you say [B]. Which is true?
  Anticipated objection: [Type] — Response: [Argument for admissibility]

SECTION 5: CLOSE THE DOOR (1-2 questions)
  Purpose: Prevent rehabilitation
  Q9: There's no way to reconcile those two statements, is there?
  Q10: [If witness offers excuse] But nothing about [excuse] changes what
       you wrote under oath on [date], does it?

EXHIBIT CUES:
  - Exhibit [X]: [Description] — present at Q5
  - Exhibit [Y]: [Description] — reserve for rebuttal if needed
```

---

## Impeachment Hierarchy

Use the highest-value impeachment material first. Hierarchy in descending order of impact:

| Rank | Type | MRE Authority | Impact Level | Description |
|------|------|---------------|-------------|-------------|
| 1 | **Prior sworn testimony** contradicting current testimony | MRE 801(d)(1)(A) | DEVASTATING | Substantive evidence + impeachment. Deposition or hearing testimony under oath. |
| 2 | **Sworn affidavit/declaration** contradicting current testimony | MRE 613 + 801(d)(1)(A) | DEVASTATING | Written statement under oath contradicts trial testimony. |
| 3 | **Documented admission against interest** | MRE 801(d)(2) | STRONG | Party's own statement (email, text, recording) contradicting their position. No foundation needed. |
| 4 | **Official record contradicting testimony** | MRE 803(8), 901(b)(7) | STRONG | Government or business record that disproves witness claim. Self-authenticating. |
| 5 | **Third-party witness contradicting testimony** | MRE 613(b) | VIABLE | Another witness's account contradicts the target witness. |
| 6 | **Documentary contradiction** (unsworn) | MRE 613 | VIABLE | Emails, texts, letters that contradict — impeachment only, not substantive. |
| 7 | **Pattern of dishonesty** | MRE 608(b) | MODERATE | Multiple instances of false statements showing character for untruthfulness. |
| 8 | **Conviction for dishonesty crime** | MRE 609(a)(2) | MODERATE | Automatic admission; no balancing needed. |
| 9 | **Bias, interest, or motive** | MRE 616 (implied) | MODERATE | Financial interest, relationship, grudge affecting testimony. |
| 10 | **Sensory/capacity deficiencies** | Common law | MARGINAL | Witness couldn't have seen/heard/known what they claim. |

---

## Witness Preparation Module Integration

The impeachment engine feeds directly into witness preparation:

### For Cross-Examination (Opposing Witnesses)
1. Query `impeachment_items` for all items by target witness
2. Rank by composite score (materiality × clarity × provability)
3. Select top 5-10 items per witness
4. Generate cross-examination scripts using template above
5. Assemble exhibit packages (marked and ready)
6. Red-team the scripts for counter-attack vulnerabilities

### For Direct Examination (Friendly Witnesses)
1. Query `impeachment_items` to identify what opposing counsel may use
2. Identify vulnerable statements by friendly witnesses
3. Prepare "inoculation" questions for direct examination
4. Draft redirect examination scripts for anticipated cross attacks

### Database Queries for Witness Prep
```sql
-- Get all impeachment material for a specific witness
SELECT i.speaker, i.statement, i.contradicting_text, i.legal_hook,
       (i.materiality + i.clarity + i.provability) as composite
FROM impeachment_items i
WHERE i.speaker = 'Watson'
ORDER BY composite DESC;

-- Find statements by witness that are vulnerable to impeachment
SELECT eq.quote_text, eq.speaker, eq.legal_significance, eq.source_file
FROM evidence_quotes eq
WHERE eq.speaker = 'Pigors'
  AND EXISTS (
    SELECT 1 FROM contradiction_map cm
    WHERE cm.source_a_text LIKE '%' || substr(eq.quote_text, 1, 50) || '%'
  );

-- Cross-lane impeachment opportunities
SELECT cm.*, cm.contradiction_type, cm.severity
FROM contradiction_map cm
WHERE cm.severity >= 7
ORDER BY cm.severity DESC, cm.contradiction_type;
```


---

## 🔬 Pass 1: Data Intelligence Layer
*Enhanced: 2026-03-12 | Source: mega_file_harvest (53,625 files)*

### Live Database Arsenal
| Table | Records | Intelligence Value |
|-------|--------:|-------------------|
| `mega_file_harvest` | 53,625 | Complete file index with citations and metadata |
| `evidence_quotes` | 308,704 | Extracted evidence passages with legal significance |
| `contradiction_map` | 10,672 | Detected contradictions across all documents |
| `impeachment_items` | 15,171 | Impeachment-ready witness inconsistencies |
| `judicial_violations` | 1,127 | Documented judicial conduct violations |
| `pages` | 472,482 | Raw page text from ingested documents |
| `master_citations` | 3,684,757 | Extracted citations across all sources |
| `claims` | 653 | Active claims matrix with status tracking |
| `vehicles` | 6 | Filing vehicles with readiness scores |
| `authority_chains` | 28 | Authority chains with completeness scoring |
| `filing_readiness` | 24 | Per-vehicle filing readiness assessment |

### Governing Authority (Verified)
**MRE:** MRE 607, MRE 608, MRE 609, MRE 613, MRE 801(d)(1)
**Binding Cases:**
- *People v Layher, 464 Mich 756*
- *People v Smith, 456 Mich 543*

### Case Lane Intelligence
| Lane | Files Indexed | Case | Court |
|------|-------------:|------|-------|
| A | 3,502 | 2024-001507-DC | 14th Circuit, Muskegon County |
| B | 3,531 | 2025-002760-CZ | 14th Circuit, Muskegon County |
| C | 279 | USDC filing pending | U.S. District Court, W.D. Michigan |
| D | 6,462 | 2023-5907-PP | 14th Circuit |
| E | 9,945 | JTC Complaint - McNeill | Judicial Tenure Commission |

### Harvest-Discovered Citations (New)
| MCR Citation | Files Found | Status |
|-------------|----------:|--------|
| MCR 2.003 | 1980 | 🆕 Verify & integrate |
| MCR 2.119 | 1635 | 🆕 Verify & integrate |
| MCR 2.107 | 1369 | 🆕 Verify & integrate |
| MCR 3.207 | 1302 | 🆕 Verify & integrate |
| MCR 3.207(B) | 933 | 🆕 Verify & integrate |
| MCR 2.003(C)(1) | 882 | 🆕 Verify & integrate |
| MCR 2.105 | 871 | 🆕 Verify & integrate |
| MCR 2.313 | 868 | 🆕 Verify & integrate |
| MCR 3.203 | 850 | 🆕 Verify & integrate |
| MCR 1.109 | 795 | 🆕 Verify & integrate |

### FTS5 Query Templates
```sql
-- Search evidence for this skill's domain
SELECT * FROM pages_fts WHERE pages_fts MATCH 'custody AND best AND interest';
SELECT * FROM evidence_quotes WHERE legal_significance LIKE '%722.23%';
SELECT * FROM pages_fts WHERE pages_fts MATCH 'habitability OR housing OR landlord';
SELECT * FROM pages_fts WHERE pages_fts MATCH 'protection AND order';
SELECT * FROM pages_fts WHERE pages_fts MATCH 'judicial AND misconduct OR bias';
```

## 🔗 Pass 2: Cross-Skill Integration Matrix
*Enhanced: 2026-03-12 | 71 skills in fleet*

### Direct Integration Points
| Skill | Relationship | Data Flow |
|-------|-------------|-----------|
| `litigation-analysis-engine` | Integration | Bidirectional data exchange |
| `litigation-authority-validator` | Integration | Receives citations → validates authority chains |
| `litigation-filing-architect` | Integration | Provides readiness scores → filing decisions |
| `litigation-red-team` | Integration | Receives outputs → adversarial stress testing |

### Cross-Lane Evidence Routing
| Source Lane | Target Lane | Connection Pattern |
|-----------|------------|-------------------|
| A (Custody (Pigors v Watson)) | F | Trial errors → appellate issues |
| A (Custody (Pigors v Watson)) | E | Biased rulings → JTC complaint evidence |
| B (Housing (Shady Oaks)) | A | Unsafe housing → best-interest factor (d) |
| D (PPO (Protection Orders)) | A | PPO proceedings → false allegation pattern (factor j) |
| D (PPO (Protection Orders)) | E | Improper PPO issuance → judicial bias pattern |
| A (Custody (Pigors v Watson)) | C | Due process violations → §1983 claims |
| E (Judicial Misconduct (JTC)) | F | Misconduct findings → appellate arguments |

### OMEGA Pipeline Phase Mapping
```
This skill operates across these pipeline phases:
  Ω-3 Evidence Harvest → Ω-5 Claim Mapping → Ω-6 Contradiction Detection
  Ω-9 Gap Analysis → Ω-11 Risk Assessment → Ω-12 Filing Readiness
```

## ⚡ Pass 3: Elite Combat Refinement
*Enhanced: 2026-03-12 | EGCP-scored | Adversarial-hardened*

### EGCP Filing Thresholds
| Filing Type | Min EGCP | Lane | Authority |
|------------|--------:|------|-----------|
| Custody Modification | 65/100 | A,B,C,D,E | Verified |
| Emergency Custody | 55/100 | A,B,C,D,E | Verified |
| PPO Modification/Termination | 60/100 | A,B,C,D,E | Verified |
| Summary Disposition (C10) | 75/100 | A,B,C,D,E | Verified |
| Summary Disposition (C8) | 70/100 | A,B,C,D,E | Verified |
| Contempt | 70/100 | A,B,C,D,E | Verified |
| Judicial Disqualification | 75/100 | A,B,C,D,E | Verified |
| Default Judgment | 60/100 | A,B,C,D,E | Verified |
| TRO Application | 60/100 | A,B,C,D,E | Verified |
| Federal §1983 Complaint | 70/100 | A,B,C,D,E | Verified |
| JTC Formal Complaint | 75/100 | A,B,C,D,E | Verified |

### Adversarial Defense Matrix
| Attack Vector | Defense | Skill Response |
|-------------|---------|---------------|
| Opposing motion to strike evidence | Pre-authenticate under MRE 901-903 | Run litigation-evidence-authentication |
| Challenge to standing | Verify party status and injury-in-fact | Document concrete harm with citations |
| Laches/statute of limitations | Verify timeliness under MCL/MCR | Check deadline_sentinel calculations |
| Hearsay objection | Map to MRE 801-807 exceptions | Pre-classify all evidence by exception |
| Judicial discretion argument | Identify abuse-of-discretion factors | Score against published standards |
| Mootness challenge | Show continuing controversy or capable-of-repetition | Document ongoing harm pattern |

### Quality Gates (Pre-Output Checklist)
```
□ All citations verified against authority_chains table
□ No hallucinated case names or statute numbers
□ Cross-lane contamination check passed (MEEK signal verified)
□ EGCP score meets filing threshold for target vehicle
□ Pinpoint citations include page + paragraph references
□ Opposing argument anticipated and addressed
□ Party names verified: Andrew J. Pigors, Emily A. Watson, L.D.W.
□ Judge name verified: Hon. Jenny L. McNeill (NOT McNeil)
□ Case numbers verified with leading zeros: 2024-001507-DC
□ No fabricated evidence (CPS = 1 call, NOT 9 investigations)
```

### Case-Specific Intelligence

**Lane A: Custody (Pigors v Watson)**
- Case: 2024-001507-DC
- Court: 14th Circuit, Muskegon County
- Judge: Hon. Jenny L. McNeill
- Key Statutes: MCL 722.23, MCL 722.27, MCL 722.28
- Key Rules: MCR 3.206-3.215
- Critical Evidence: 329+ days separation, 44% ex parte rate, Factor (j) alienation

**Lane B: Housing (Shady Oaks)**
- Case: 2025-002760-CZ
- Court: 14th Circuit, Muskegon County
- Judge: TBD
- Key Statutes: MCL 554.139, MCL 125.534-540, MCL 600.2918
- Key Rules: MCR 2.116, MCR 2.603
- Critical Evidence: 6GB evidence, HOA complaints, LARA registrations, FOIA personnel

**Lane C: Federal Civil Rights (§1983)**
- Case: USDC filing pending
- Court: U.S. District Court, W.D. Michigan
- Judge: TBD
- Key Statutes: 42 USC § 1983, 42 USC § 1985, 42 USC § 1988
- Key Rules: FRCP 8, FRCP 12, FRCP 56
- Critical Evidence: Color of law violations, Monell policy, pattern evidence across lanes

**Lane D: PPO (Protection Orders)**
- Case: 2023-5907-PP
- Court: 14th Circuit
- Judge: Hon. Jenny L. McNeill
- Key Statutes: MCL 600.2950, MCL 750.411h
- Key Rules: MCR 3.705-3.708
- Critical Evidence: False PPO allegations pattern, zero CPS findings after 1 investigation

**Lane E: Judicial Misconduct (JTC)**
- Case: JTC Complaint - McNeill
- Court: Judicial Tenure Commission
- Judge: Target: Hon. Jenny L. McNeill
- Key Statutes: Const 1963 art 6 § 30, MCR 9.104-9.205
- Key Rules: MCR 2.003, Code of Judicial Conduct
- Critical Evidence: 1,127 violations, 44% ex parte rate, muting father 7x in hearing

### Self-Evolution Protocol
```
After each use of this skill:
1. Log output quality score (1-10) to session SQL
2. Record any missing citations or evidence gaps discovered
3. Update lane-specific intelligence if new orders/events occurred
4. Cross-reference findings with contradiction_map for consistency
5. Feed results to litigation-red-team for adversarial validation
```
