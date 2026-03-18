---
name: litigation-jury-instruction-engine
description: >-
  Use when researching Michigan Standard Jury Instructions (M Civ JI),
  drafting custom jury instructions, preparing objections to proposed
  instructions, creating verdict forms, preserving instructional error
  for appeal, or analyzing jury instruction issues under MCR 2.512(A)
  and MCR 2.516.
metadata:
  category: trial
  author: andrew-pigors
  version: "1.0.0"
  triggers: >-
    jury instructions, M Civ JI, jury charge, verdict form, MCR 2.512,
    MCR 2.516, instructional error, special verdict, general verdict,
    jury request, standard instruction, custom instruction, objection
    to instruction, trial instructions
---

# litigation-jury-instruction-engine

> **Tier:** 2 — Trial Specialist
> **Category:** trial
> **Version:** 1.0.0
> **Lane:** A (Custody) / B (Housing) / D (PPO) — any jury-eligible lane

## Description

Jury instruction research and drafting specialist for Michigan civil
litigation. Researches Michigan Standard Jury Instructions (M Civ JI),
drafts custom instructions when standard instructions are inadequate,
prepares objections to opposing party's proposed instructions, creates
verdict forms (general and special), and preserves instructional errors
for appellate review. Ensures all instructions comply with MCR 2.512(A)
and MCR 2.516.

**Case Context:**

| Field | Value |
|-------|-------|
| Plaintiff | Andrew James Pigors (Pro Se) |
| Defendant | Emily A. Watson |
| Child | L.D.W. per MCR 8.119(H) — MALE |
| Judge | Hon. Jenny L. McNeill — 14th Circuit Court |
| Case Nos. | 2024-001507-DC, 2025-002760-CZ |
| Lanes | A (Custody), B (Housing) |

## Triggers

- User preparing for trial and needs jury instructions
- User needs to research M Civ JI chapters
- User drafting custom jury instruction for novel issue
- User objecting to opposing party's proposed instructions
- User preparing verdict forms
- User preserving instructional error for appeal

## Michigan Rules — Jury Instructions

### MCR 2.512 — Instructions to Jury

**(A) Request for Instructions:**
- Any party may file written requests for jury instructions
- Requests must be filed at the close of evidence or earlier if ordered
- Each instruction shall be on a separate sheet
- Instructions shall be numbered and identify the party requesting them

**(B) Objections:**
- Objections to instructions must be made before instructions are given
- Must state the matter objected to and the grounds for objection
- Failure to object waives the right to appellate review (absent manifest injustice)

**(C) Court's Duty:**
- Court must instruct the jury on applicable law
- Court must give M Civ JI when they are applicable, accurate, and pertinent
- Court may give additional instructions not covered by M Civ JI

### MCR 2.516 — Jury Verdicts

**(A) Return of Verdict:**
- Verdicts must be unanimous unless parties stipulate otherwise
- Verdict must be returned in open court

**(B) Special Verdicts:**
- Court may require a special verdict (specific factual findings)
- Court may use general verdict with interrogatories

**(C) Polling the Jury:**
- Either party may request the jury be polled
- Each juror asked individually whether the verdict is their verdict

## M Civ JI — Standard Instruction Chapters

### Key Chapters for Family Law / Civil Litigation

| Chapter | Subject | When to Use |
|---------|---------|-------------|
| Ch. 1 | Preliminary instructions | Every trial |
| Ch. 2 | Burden of proof | Every trial |
| Ch. 3 | Damages — General | Damage claims |
| Ch. 4 | Damages — Personal injury | If applicable |
| Ch. 10 | Negligence | Housing claims (Lane B) |
| Ch. 12 | Intentional torts | If applicable |
| Ch. 14 | Contract | Housing/lease claims |
| Ch. 15 | Fraud | If applicable |
| Ch. 50 | Civil rights | Federal § 1983 claims |
| Ch. 107 | Credibility of witnesses | Every trial |
| Ch. 108 | Cautionary instructions | As needed |

### Instruction Request Format

```
PLAINTIFF'S REQUESTED JURY INSTRUCTION NO. [N]

M Civ JI [X.XX] — [Title]

[Full text of instruction]

Legal Basis: [MCR/MCL/case law supporting the instruction]
```

## Patterns

### Pattern 1: Standard Instruction Selection

**Context:** Trial preparation requires identifying applicable M Civ JI.

**Steps:**
1. List all claims and defenses at issue
2. Map each claim/defense to applicable M Civ JI chapters
3. Draft instruction request for each applicable M Civ JI
4. Identify gaps where custom instructions are needed
5. File complete set per MCR 2.512(A)

**Michigan basis:** MCR 2.512(A), MCR 2.512(C)

```python
from legal_ai.jury_instruction_engine import JuryInstructionEngine

jie = JuryInstructionEngine()
instructions = jie.select_standard_instructions(
    claims=["breach of contract", "negligence"],
    defenses=["comparative fault"],
)
request_set = jie.format_instruction_requests(instructions)
```

### Pattern 2: Custom Instruction Drafting

**Context:** No standard M Civ JI covers the legal issue.

**Steps:**
1. Research applicable statutory and case law
2. Draft proposed instruction in plain language
3. Include legal authority supporting each element
4. Contrast with any standard instruction that partially applies
5. File with citation to authority per MCR 2.512(A)

**Michigan basis:** MCR 2.512(C), *People v Stephan*, 241 Mich App 482 (2000)

### Pattern 3: Objection and Preservation

**Context:** Opposing party proposes an instruction that misstates the law.

**Steps:**
1. Review opposing party's proposed instructions
2. Identify legal errors, omissions, or misleading language
3. Prepare written objection stating specific grounds
4. Propose corrected alternative instruction
5. Make objection on the record before instructions given (MCR 2.512(B))
6. If overruled, ensure the objection is in the record for appeal

**Michigan basis:** MCR 2.512(B), MCR 2.613, *Silberstein v Pro-Golf of America*, 278 Mich App 446 (2008)

### Pattern 4: Verdict Form Preparation

**Context:** Complex case requires special verdict or interrogatories.

**Steps:**
1. Identify each factual issue the jury must decide
2. Draft special verdict form with specific questions
3. Alternatively, prepare general verdict form with written interrogatories
4. Ensure verdict form covers all claims and defenses
5. File proposed verdict form with instruction requests

**Michigan basis:** MCR 2.516(B)

## Anti-Patterns

### Anti-Pattern 1: Late Filing of Instruction Requests

❌ Waiting until after evidence closes to begin drafting instructions.
**Why it fails:** MCR 2.512(A) requires filing at or before close of
evidence. Late requests may be rejected. Complex instructions need
research time.
**Fix:** Begin drafting instructions during trial preparation, not during
trial. File preliminary requests before trial with right to supplement.

### Anti-Pattern 2: Failing to Object on the Record

❌ Objecting to an instruction only in writing or only at sidebar.
**Why it fails:** MCR 2.512(B) requires objection before instructions are
given. Failure to object on the record waives appellate review.
**Fix:** Always state the objection clearly on the record, identifying
the specific instruction number and the legal ground for objection.

### Anti-Pattern 3: Ignoring Standard Instructions

❌ Proposing only custom instructions when M Civ JI applies.
**Why it fails:** MCR 2.512(C) requires the court to give applicable
M Civ JI. If you don't request them, the court may give an
instruction that's less favorable.
**Fix:** Always start with M Civ JI. Use custom instructions only to
fill gaps not covered by the standard set.

## Verdict Form Templates

### General Verdict Form

```
VERDICT FORM

We, the jury, find in favor of:
  [ ] Plaintiff, Andrew James Pigors
  [ ] Defendant, Emily A. Watson

If finding for Plaintiff, we assess damages at: $__________

Date: __________

Foreperson: ____________________
```

### Special Verdict Form (Contract Claim)

```
SPECIAL VERDICT FORM

1. Did Defendant breach the contract with Plaintiff?
   [ ] Yes  [ ] No

2. If yes, was the breach a proximate cause of damages to Plaintiff?
   [ ] Yes  [ ] No

3. If yes, what is the amount of Plaintiff's damages? $__________

Date: __________

Foreperson: ____________________
```

## Appellate Preservation Checklist

- [ ] All instruction requests filed per MCR 2.512(A)
- [ ] Each request on separate sheet, numbered, party identified
- [ ] Objections to opposing instructions made before jury charged
- [ ] Objections state specific grounds (MCR 2.512(B))
- [ ] Court's ruling on each objection noted in record
- [ ] Final instructions compared to requested instructions
- [ ] Any deviation from M Civ JI documented
- [ ] Verdict form preserved in record

## Integration Points

### Upstream Skills
- `litigation-case-strategy-architect` — Trial strategy informing instruction selection
- `litigation-evidence-harvester` — Evidence supporting each claim element
- `litigation-witness-preparation` — Witness testimony alignment with instructions

### Downstream Skills
- `litigation-appellate-strategist` — Instructional error as appellate issue
- `litigation-brief-writer` — Post-trial brief on instruction errors
- `litigation-record-builder` — Record preservation of instruction history


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

### Case Lane Intelligence
| Lane | Files Indexed | Case | Court |
|------|-------------:|------|-------|
| A | 3,502 | 2024-001507-DC | 14th Circuit, Muskegon County |
| B | 3,531 | 2025-002760-CZ | 14th Circuit, Muskegon County |
| D | 6,462 | 2023-5907-PP | 14th Circuit |
| F | 975 | COA 366810 | Michigan Court of Appeals / Supreme Court |

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
SELECT * FROM pages_fts WHERE pages_fts MATCH 'appeal AND error AND preserved';
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
| Custody Modification | 65/100 | A,B,D,F | Verified |
| Emergency Custody | 55/100 | A,B,D,F | Verified |
| PPO Modification/Termination | 60/100 | A,B,D,F | Verified |
| Summary Disposition (C10) | 75/100 | A,B,D,F | Verified |
| Summary Disposition (C8) | 70/100 | A,B,D,F | Verified |
| Contempt | 70/100 | A,B,D,F | Verified |
| Appeal Brief | 70/100 | A,B,D,F | Verified |
| Leave Application (MSC) | 80/100 | A,B,D,F | Verified |
| Default Judgment | 60/100 | A,B,D,F | Verified |
| TRO Application | 60/100 | A,B,D,F | Verified |

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

**Lane D: PPO (Protection Orders)**
- Case: 2023-5907-PP
- Court: 14th Circuit
- Judge: Hon. Jenny L. McNeill
- Key Statutes: MCL 600.2950, MCL 750.411h
- Key Rules: MCR 3.705-3.708
- Critical Evidence: False PPO allegations pattern, zero CPS findings after 1 investigation

**Lane F: Appellate (COA/MSC)**
- Case: COA 366810
- Court: Michigan Court of Appeals / Supreme Court
- Judge: Panel TBD
- Key Statutes: MCL 722.28, MCL 600.308
- Key Rules: MCR 7.203-7.305
- Critical Evidence: Preserved errors, constitutional violations, due process denial

### Self-Evolution Protocol
```
After each use of this skill:
1. Log output quality score (1-10) to session SQL
2. Record any missing citations or evidence gaps discovered
3. Update lane-specific intelligence if new orders/events occurred
4. Cross-reference findings with contradiction_map for consistency
5. Feed results to litigation-red-team for adversarial validation
```
